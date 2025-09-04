from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple

import gradio as gr
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch

# ──────────────────────────────────────────────────────────────────────────────
# Boot / Config
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DB = os.getenv("MONGODB_DB", "ragdb")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "pdf_chunks")
MONGODB_ATLAS_INDEX = os.getenv("MONGODB_ATLAS_INDEX", "vector_index")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "6"))

ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "false").lower() == "true"

# ── Future AGI instrumentation ──────────────────────────────────
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType
trace_provider = register(project_type=ProjectType.OBSERVE, project_name="mongodb_project")
from traceai_langchain import LangChainInstrumentor
LangChainInstrumentor().instrument(tracer_provider=trace_provider)

# ──────────────────────────────────────────────────────────────────────────────
# Prompting
# ──────────────────────────────────────────────────────────────────────────────
SENTINEL = 'Not enough information in the uploaded documents.'

SYSTEM_PREAMBLE_STRICT = (
    "You are a precise PDF RAG assistant. Answer ONLY from the provided context. "
    f"If the answer isn't in the context, reply exactly: \"{SENTINEL}\" "
    "Do NOT use outside knowledge. Do NOT include a Sources or References section in your answer."
)

SYSTEM_PREAMBLE_FALLBACK = (
    "You are a precise PDF RAG assistant. Prefer answers grounded in the provided context. "
    "If the context is insufficient, you MAY use your general knowledge, but clearly prefix with: "
    "\"(Based on general knowledge, not found in the uploaded PDFs)\". "
    "Do NOT include a Sources or References section in your answer."
)

SYSTEM_PREAMBLE = SYSTEM_PREAMBLE_FALLBACK if ALLOW_FALLBACK else SYSTEM_PREAMBLE_STRICT

RAG_TEMPLATE = """{system_preamble}

Context (excerpts from the user's PDFs):
{context}

Question:
{question}

Answer (concise, based strictly on the context if possible):"""

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Globals
_client: MongoClient | None = None
_collection = None
_vectorstore: MongoDBAtlasVectorSearch | None = None
_retrieval_qa: RetrievalQA | None = None

# ──────────────────────────────────────────────────────────────────────────────
# Mongo / Atlas Vector Search
# ──────────────────────────────────────────────────────────────────────────────
def _connect_mongo():
    global _client, _collection
    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI missing in .env")
    try:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000, tls=True)
        _client.admin.command("ping")
    except OperationFailure as e:
        raise RuntimeError(
            "MongoDB auth failed. Check username/password (URL-encode special chars) "
            "and IP allowlist in Atlas. Original error: " + str(e)
        )
    _collection = _client[MONGODB_DB][MONGODB_COLLECTION]

def _ensure_collection_exists():
    _collection.insert_one({"__bootstrap__": True})
    _collection.delete_one({"__bootstrap__": True})

def _ensure_search_index(embedding_dimension: int):
    _ensure_collection_exists()
    # Try new schema
    try:
        _collection.database.command({
            "createSearchIndexes": _collection.name,
            "indexes": [{
                "name": MONGODB_ATLAS_INDEX,
                "definition": {
                    "mappings": {
                        "dynamic": False,
                        "fields": {
                            "embedding": {"type": "tor", "dimensions": int(embedding_dimension), "similarity": "cosine"},
                            "text": {"type": "string"},
                            "metadata": {"type": "document"},
                        }
                    }
                }
            }]
        })
        print("[atlas-index] Created using new 'mappings/knnVector' schema.")
        return
    except Exception as e:
        msg = str(e).lower()
        if "already exists" in msg or "exists" in msg:
            print(f"[atlas-index] {e}")
            return
        print(f"[atlas-index] New schema failed ({e}). Trying legacy schema...")

    # Legacy schema
    try:
        _collection.database.command({
            "createSearchIndexes": _collection.name,
            "indexes": [{
                "name": MONGODB_ATLAS_INDEX,
                "definition": {
                    "fields": [
                        {"type": "vector", "path": "embedding", "numDimensions": int(embedding_dimension), "similarity": "cosine"},
                        {"type": "string", "path": "text"},
                        {"type": "document", "path": "metadata"},
                    ]
                }
            }]
        })
        print("[atlas-index] Created using legacy 'fields/vector' schema.")
    except Exception as e2:
        raise RuntimeError(f"Failed to create Atlas Search index (both schemas). Last error: {e2}")

def _build_vectorstore(embeddings: OpenAIEmbeddings) -> MongoDBAtlasVectorSearch:
    return MongoDBAtlasVectorSearch(
        collection=_collection,
        embedding=embeddings,
        index_name=MONGODB_ATLAS_INDEX,
        text_key="text",
        embedding_key="embedding",
    )

# ──────────────────────────────────────────────────────────────────────────────
# RAG utilities
# ──────────────────────────────────────────────────────────────────────────────
def _make_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )

def _load_pdfs(paths: List[Path]) -> List[Document]:
    docs: List[Document] = []
    for p in paths:
        loader = PyPDFLoader(str(p))
        file_docs = loader.load()
        for d in file_docs:
            d.metadata["source"] = p.name
        docs.extend(file_docs)
    return docs

def _format_sources(docs: List[Document]) -> str:
    seen = set()
    lines = []
    for d in docs:
        src = d.metadata.get("source", "document.pdf")
        page = d.metadata.get("page", None)
        key = (src, page)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {src} (page {int(page) + 1})" if page is not None else f"- {src}")
    return "\n".join(lines) if lines else "- (no sources found)"

def _expand_query(q: str) -> str:
    ql = q.lower().strip()
    expansions = []
    if " rag" in f" {ql}" or ql == "rag":
        expansions.extend([
            "retrieval-augmented generation",
            "retrieval augmented generation",
            "RAG system",
        ])
    # add more acronym expansions if you like
    if not expansions:
        return q
    return q + " | " + " | ".join(expansions)

def _strip_model_sources(text: str) -> str:
    return re.sub(r"\n+(sources?|references?)\s*:.*$", "", text, flags=re.IGNORECASE | re.DOTALL)

def _build_chain() -> RetrievalQA:
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    prompt = PromptTemplate(
        template=RAG_TEMPLATE,
        input_variables=["context", "question"],
        partial_variables={"system_preamble": SYSTEM_PREAMBLE},
    )
    retriever = _vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
    return chain

def init_app():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing. Put it in .env")

    # Mongo + index
    global _vectorstore, _retrieval_qa
    _connect_mongo()
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)
    dim = len(embeddings.embed_query("dimension-probe"))
    _ensure_search_index(dim)
    _vectorstore = _build_vectorstore(embeddings)
    _retrieval_qa = _build_chain()

# ──────────────────────────────────────────────────────────────────────────────
# Gradio handlers
# ──────────────────────────────────────────────────────────────────────────────
def handle_ingest(files) -> str:
    if not files:
        return "No files selected."
    saved: List[Path] = []
    for f in files:
        src = Path(f.name)
        dst = DOCS_DIR / src.name
        shutil.copy(src, dst)
        saved.append(dst)

    docs = _load_pdfs(saved)
    chunks = _make_splitter().split_documents(docs)
    if not chunks:
        return "No text found in uploaded PDFs."
    _vectorstore.add_documents(chunks)
    return f"Ingested {len(saved)} file(s) → {len(chunks)} chunks."

def handle_reset() -> str:
    _collection.drop()
    _ensure_collection_exists()
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)
    dim = len(embeddings.embed_query("dimension-probe"))
    _ensure_search_index(dim)
    return "Collection dropped and search index re-initialized."

def handle_chat(user_msg: str, history: List[Tuple[str, str]]):
    if not user_msg.strip():
        return "Please enter a question.", history

    # Expand acronyms to improve recall, but keep the original question semantics.
    expanded = _expand_query(user_msg)

    # Ask the chain using the expanded query (improves retrieval), but the prompt itself
    # uses {question} which will be populated with the same string. That's acceptable for QA.
    res = _retrieval_qa.invoke({"query": expanded})

    answer_raw = res["result"]
    answer = _strip_model_sources(answer_raw).strip()
    src_docs = res.get("source_documents", [])

    # If the strict sentinel fired, don't show sources (to avoid the contradiction you saw).
    if not ALLOW_FALLBACK and answer == SENTINEL:
        pretty = answer
        history = history + [(user_msg, pretty)]
        return "", history

    sources = _format_sources(src_docs)
    pretty = f"{answer}\n\n---\n**Sources**\n{sources}"
    history = history + [(user_msg, pretty)]
    return "", history

# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────
def build_ui() -> gr.Blocks:
    with gr.Blocks(title="PDF RAG (LangChain + MongoDB Atlas)") as demo:
        gr.Markdown("# 📄 PDF RAG Chatbot\nUpload PDF(s) → Ingest → Ask grounded questions.")

        with gr.Tab("Ingest"):
            file_uploader = gr.File(label="Upload PDF files", file_types=[".pdf"], file_count="multiple")
            with gr.Row():
                ingest_btn = gr.Button("Ingest PDFs", variant="primary")
                reset_btn = gr.Button("Reset / Clear Collection")
            ingest_out = gr.Markdown()

        with gr.Tab("Chat"):
            chat = gr.Chatbot(height=420, label="Chat", type="tuples")
            with gr.Row():
                box = gr.Textbox(show_label=False, placeholder="Ask a question about your PDFs…", scale=8)
                send = gr.Button("Send", variant="primary", scale=1)
            gr.Examples(
                examples=[
                    "Define retrieval-augmented generation.",
                    "List key terms and their definitions.",
                    "Where does the paper define embeddings?",
                    "Summarize section 2.1 in 3 bullets."
                ],
                inputs=[box],
            )

        ingest_btn.click(handle_ingest, inputs=[file_uploader], outputs=[ingest_out])
        reset_btn.click(handle_reset, outputs=[ingest_out])
        send.click(handle_chat, inputs=[box, chat], outputs=[box, chat])
        box.submit(handle_chat, inputs=[box, chat], outputs=[box, chat])
    return demo

if __name__ == "__main__":
    init_app()
    ui = build_ui()
    ui.launch()
