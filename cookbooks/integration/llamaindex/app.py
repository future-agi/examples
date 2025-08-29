# ============================================================================
# IMPORTS
# ============================================================================
import os
import gradio as gr
from pathlib import Path
from typing import List, Any
from dotenv import load_dotenv

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings

load_dotenv()

# ============================================================================
# FUTUREAGI INSTRUMENTATION SETUP
# ============================================================================
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="llamaindex_project",
)

from traceai_llamaindex import LlamaIndexInstrumentor

LlamaIndexInstrumentor().instrument(tracer_provider=trace_provider)

# ============================================================================
# CONFIGURATION
# ============================================================================
STORAGE_PATH = Path("./vectorstore")
DOCUMENTS_PATH = Path("./documents")
DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)

DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")

INDEX: VectorStoreIndex | None = None

# ============================================================================
# INDEX MANAGEMENT
# ============================================================================
def _ensure_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY not set. Put it in .env or export it before running."
        )


def _configure_settings(temperature: float = 0.2):
    _ensure_api_key()
    Settings.llm = OpenAI(model=DEFAULT_LLM_MODEL, temperature=temperature)
    Settings.embed_model = OpenAIEmbedding(model=DEFAULT_EMBED_MODEL)


def initialize_index() -> VectorStoreIndex:
    _configure_settings(temperature=0.2)

    if not any(DOCUMENTS_PATH.iterdir()):
        (DOCUMENTS_PATH / "README.txt").write_text(
            "Add PDFs/TXT/DOCX/MD into ./documents and click 'Rebuild Index'.\n"
        )

    if not STORAGE_PATH.exists():
        docs = SimpleDirectoryReader(str(DOCUMENTS_PATH), recursive=True).load_data()
        index = VectorStoreIndex.from_documents(docs)
        index.storage_context.persist(persist_dir=str(STORAGE_PATH))
        return index

    storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_PATH))
    index = load_index_from_storage(storage_context)
    return index


def rebuild_index() -> str:
    global INDEX
    try:
        _configure_settings(temperature=0.2)
        if STORAGE_PATH.exists():
            for p in STORAGE_PATH.glob("**/*"):
                try:
                    p.unlink()
                except IsADirectoryError:
                    pass
            for p in sorted(STORAGE_PATH.glob("**/*"), reverse=True):
                if p.is_dir():
                    p.rmdir()
            if STORAGE_PATH.exists():
                STORAGE_PATH.rmdir()
        INDEX = None
        INDEX = initialize_index()
        return "Index rebuilt from ./documents and saved to ./vectorstore."
    except Exception as e:
        return f"Rebuild failed: {type(e).__name__}: {e}"

# ============================================================================
# CHAT ENGINE AND RESPONSES
# ============================================================================
def _history_to_memory(history: List, token_limit: int = 4000) -> ChatMemoryBuffer:
    mem = ChatMemoryBuffer.from_defaults(token_limit=token_limit)
    for msg in history:
        if isinstance(msg, tuple) and len(msg) >= 2:
            user_msg, bot_msg = msg[0], msg[1]
            if user_msg:
                mem.put(ChatMessage(role=MessageRole.USER, content=user_msg))
            if bot_msg:
                mem.put(ChatMessage(role=MessageRole.ASSISTANT, content=bot_msg))
    return mem


def respond(message: str, history: List[Any]) -> str:
    global INDEX
    try:
        if INDEX is None:
            INDEX = initialize_index()

        memory = _history_to_memory(history)
        engine = INDEX.as_chat_engine(
            chat_mode="condense_question",
            memory=memory,
            verbose=True,
        )
        response = engine.chat(message)

        sources_lines = []
        try:
            for sn in (response.source_nodes or [])[:3]:
                meta = sn.metadata or {}
                name = meta.get("file_name") or meta.get("filename") or meta.get("source") or sn.node_id[:8]
                score = getattr(sn, "score", None)
                page_num = meta.get("page_label") or meta.get("page") or meta.get("page_number")
                
                source_text = f"- {name}"
                if page_num is not None:
                    source_text += f" (page {page_num})"
                if score is not None:
                    source_text += f" (score={round(score, 3)})"
                
                sources_lines.append(source_text)
        except Exception as e:
            print(f"Error formatting sources: {str(e)}")
            pass

        if sources_lines:
            return f"{response.response}\n\n**Sources**\n" + "\n".join(sources_lines)
        else:
            return response.response

    except Exception as e:
        return f"[Error] {type(e).__name__}: {e}"

# ============================================================================
# FILE HANDLING
# ============================================================================
def save_uploaded(files) -> str:
    if not files:
        return "No files uploaded."
    saved = 0
    for f in files:
        try:
            dest = DOCUMENTS_PATH / Path(f.name).name
            with open(f.name, "rb") as src, open(dest, "wb") as out:
                out.write(src.read())
            saved += 1
        except Exception:
            pass
    return f"Uploaded {saved} file(s) to ./documents. Click 'Rebuild Index' to include them."

# ============================================================================
# UI CONFIGURATION
# ============================================================================
DESCRIPTION = """
Upload documents and chat with their content using AI.
"""

CSS = """
.container {border-radius: 10px; padding: 20px; margin-bottom: 10px}
.status-container {min-height: 30px; margin-top: 10px}
"""

def upload_and_process(files):
    upload_result = save_uploaded(files)
    if files and "Uploaded" in upload_result:
        index_result = rebuild_index()
        return "Documents uploaded successfully. Start chatting."
    return upload_result

# ============================================================================
# UI LAYOUT AND INITIALIZATION
# ============================================================================
with gr.Blocks(title="Document Chat Assistant", fill_height=True, css=CSS) as demo:
    gr.Markdown("#Document Chat Assistant")
    gr.Markdown(DESCRIPTION)
    
    with gr.Row():
        with gr.Column(scale=1, elem_classes="container"):
            files = gr.Files(label="Upload Documents (PDF, TXT, DOCX, MD)", file_count="multiple")
            upload_btn = gr.Button("Upload", variant="primary")
            status = gr.Markdown("", elem_classes="status-container")
        
        with gr.Column(scale=2, elem_classes="container"):
            chat = gr.ChatInterface(
                fn=respond,
                textbox=gr.Textbox(placeholder="Ask a question about your documents..."),
                examples=[
                    "Summarize the key points from the document.",
                    "What are the main concepts discussed in the document?",
                    "Extract the most important conclusions from the document.",
                    "Compare and contrast the main ideas in the document.",
                ],
            )

    upload_btn.click(upload_and_process, inputs=[files], outputs=[status])

# ============================================================================
# MAIN FUNCTION
# ============================================================================
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860, show_api=False)
