import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


from eval_tags import list_of_eval_tags

llm = ChatOpenAI(model_name="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model = "text-embedding-3-large")

llm.invoke("Hi")

from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType, FiSpanKindValues , SpanAttributes
from traceai_langchain import LangChainInstrumentor
from opentelemetry import trace


trace_provider = register(
#   session_name="Rag-Agent",
  project_type=ProjectType.EXPERIMENT,
  project_name="Rag-Agent-text-splitter",
  eval_tags=list_of_eval_tags,
  project_version_name="RAG"
)

trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)
LangChainInstrumentor().instrument(tracer_provider=trace_provider)

import pandas as pd

dataset = pd.read_csv("Ragdata.csv")
pd.set_option('display.max_colwidth', None)
dataset.head(2)

def docs_to_serializable(docs):
    return [doc.page_content for doc in docs]


from langchain_experimental.text_splitter import SemanticChunker
from bs4 import BeautifulSoup as bs
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma

urls = ['https://en.wikipedia.org/wiki/Attention_Is_All_You_Need',
        'https://en.wikipedia.org/wiki/BERT_(language_model)',
        'https://en.wikipedia.org/wiki/Generative_pre-trained_transformer',
        'https://en.wikipedia.org/wiki/Large_language_model',
        'https://en.wikipedia.org/wiki/Reinforcement_learning',
        'https://en.wikipedia.org/wiki/Natural_language_processing',
        'https://en.wikipedia.org/wiki/GPT-4',
        'https://en.wikipedia.org/wiki/Transformers_(machine_learning)',
        'https://en.wikipedia.org/wiki/ChatGPT',
        'https://en.wikipedia.org/wiki/Vector_database'
        ]

docs = {}

def openai_llm(question, context):     
    formatted_prompt = f"Question: {question}\n\nContext: {context}"
    messages=[{'role': 'user', 'content': formatted_prompt}]     
    response = llm.invoke(messages)
    print(response)
    return response.content


def generate_sub_questions(question):
    """Generate sub-questions from a main question using the LLM."""
    with tracer.start_as_current_span(
        "Generate_SubQuestions",
        attributes={SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value}
    ) as span:
        span.set_attribute(SpanAttributes.RAW_INPUT,json.dumps (question))
        span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps (question))
        
        prompt = ("Break down this question into 2-3 sub-questions needed to answer it. "
                "Focus on specific topics and details and related subtopics.\n"
                f"Question: {question}\n"
                "Format: Bullet points with 'SUBQ:' prefix")
        
        span.set_attribute("formatted_prompt", prompt)
        
        messages = [{'role': 'user', 'content': prompt}]
        span.set_attribute("messages", json.dumps(messages))
        
        response = llm.invoke(messages)
        span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response.content))
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response.content))
        # Extract sub-questions from the response
        sub_qs = []
        for line in response.content.split("\n"):
            if "SUBQ:" in line:
                sub_qs.append(line.split("SUBQ:")[1].strip())
        
        # If no sub-questions were extracted or there was an error, return the original question
        if not sub_qs:
            sub_qs = [question]
        
        span.set_attribute("extracted_subquestions", json.dumps(sub_qs))
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(sub_qs))
        span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(sub_qs))
        return sub_qs


def rag_chain(question):
    with tracer.start_as_current_span(
        "RAG_Chain",
        attributes={SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value}
    ) as span:
        span.set_attribute(SpanAttributes.RAW_INPUT, json.dumps(question))
        span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(question))
        
        # Generate sub-questions from the original question
        sub_questions = generate_sub_questions(question)
        span.set_attribute("sub_questions", json.dumps(sub_questions))
        
        # Retrieve documents for each sub-question
        all_retrieved_docs = []
        for i, sub_q in enumerate(sub_questions):
            with tracer.start_as_current_span(
                f"Retrieval_SubQ_{i+1}",
                attributes={SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.RETRIEVER.value}
            ) as retrieval_span:
                retrieval_span.set_attribute(SpanAttributes.RAW_INPUT, json.dumps(sub_q))
                retrieval_span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(sub_q))
                retrieved_docs = retriever.invoke(sub_q)
                retrieval_span.set_attribute("num_docs_retrieved", len(retrieved_docs))
                retrieval_span.set_attribute("docs_content", json.dumps(docs_to_serializable(retrieved_docs)))
                all_retrieved_docs.extend(retrieved_docs)
        
        # Combine all contexts
        formatted_context = "\n\n".join(doc.page_content for doc in all_retrieved_docs)
        span.set_attribute("num_total_docs", len(all_retrieved_docs))
        span.set_attribute("context_length", len(formatted_context))
        
        # Get response from LLM
        response = openai_llm(question, formatted_context)
        span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response))
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response))
        return response

def get_important_facts(question):
    with tracer.start_as_current_span(
        "Important_Facts_Query",
        attributes={SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value}
    ) as span:
        span.set_attribute(SpanAttributes.RAW_INPUT, json.dumps(question))
        span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(question))
        response = rag_chain(question)
        span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response))
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response))
        return response

for i, url in enumerate(urls):
    loader = WebBaseLoader(url)
    doc = loader.load()
    docs[i] = doc

all_docs = [doc for doc_list in docs.values() for doc in doc_list]

semantic_chunker = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")

semantic_chunks = semantic_chunker.create_documents([d.page_content for d in all_docs])

vectorstore = Chroma.from_documents(documents=semantic_chunks, embedding=embeddings, persist_directory="chroma_db")

retriever = vectorstore.as_retriever()

import pandas as pd
import time

# Assuming your dataset is a pandas DataFrame with 'Query_Text' column
results = []

# Loop through each query with semantic chunk handling
for idx, question in enumerate(dataset['Query_Text']):
    with tracer.start_as_current_span(
        "RAG Chatbot",
        attributes={SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value}
    ) as span:
        try:
            span.set_attribute(SpanAttributes.RAW_INPUT, json.dumps(question))
            span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(question))
            
            # Generate sub-questions from the original question
            sub_questions = generate_sub_questions(question)
            span.set_attribute("sub_questions", json.dumps(sub_questions))
            
            # Retrieve documents for each sub-question
            all_retrieved_docs = []
            for i, sub_q in enumerate(sub_questions):
                with tracer.start_as_current_span(
                    f"Dataset_Retrieval_SubQ_{i+1}",
                    attributes={SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value}
                ) as retrieval_span:
                    
                    retrieval_span.set_attribute(SpanAttributes.RAW_INPUT, json.dumps(sub_q))
                    retrieval_span.set_attribute(SpanAttributes.INPUT_VALUE, json.dumps(sub_q))

                    retrieved_docs = retriever.invoke(sub_q)

                    retrieval_span.set_attribute("num_docs_retrieved", len(retrieved_docs))
                    retrieval_span.set_attribute("docs_content", json.dumps(docs_to_serializable(retrieved_docs)))
                    retrieval_span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(docs_to_serializable(retrieved_docs)))
                    retrieval_span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(docs_to_serializable(retrieved_docs)))
                    
                    all_retrieved_docs.extend(retrieved_docs)

            
            span.set_attribute("documents_retrieved", json.dumps(docs_to_serializable(all_retrieved_docs)))
            span.set_attribute("num_total_docs", len(all_retrieved_docs))

            # Format context with semantic chunk markers (keep for LLM input)
            formatted_context = "\n\n[SEMANTIC CHUNK]\n".join(
                [f"CHUNK {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(all_retrieved_docs)]
            )
            span.set_attribute("context_length", len(formatted_context))

            response = openai_llm(question, formatted_context)

            span.set_attribute(SpanAttributes.RAW_OUTPUT, json.dumps(response))
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response))
            # Store results with both formatted context and structured chunks
            results.append({
                "query_id": idx + 1,
                "question": question,
                "num_chunks": len(all_retrieved_docs),
                "context": formatted_context,  # Original string format
                "chunks_list": [doc.page_content for doc in all_retrieved_docs],  # List storage
                "response": response
            })

            # Add delay to avoid API overload
            time.sleep(1)  # Adjust based on API rate limits
            print(f"Processed query {idx+1}/{len(dataset)}")

        except Exception as e:
            print(f"Error processing query {idx+1}: {str(e)}")
            results.append({
                "query_id": idx + 1,
                "question": question,
                "num_chunks": 0,
                "context": "Error",
                "chunks_list": [],  # Empty list for error case
                "response": f"Error: {str(e)}"
            })

# Create DataFrame from results
results_df = pd.DataFrame(results)

# Improved analysis using list instead of string parsing
results_df['avg_chunk_length'] = results_df.apply(
    lambda row: sum(len(chunk.split()) for chunk in row['chunks_list'])/max(1, row['num_chunks'])
    if row['num_chunks'] > 0 else 0,
    axis=1
)

# Save to CSV (note: lists will be stored as strings in CSV)
results_df.to_csv('semantic_rag_evaluation.csv', index=False)


from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from typing import List, Dict

# New: Sub-question generation prompt
subq_prompt = PromptTemplate.from_template(
    "Break down this question into 2-3 sub-questions needed to answer it. "
    "Focus on specific topics and details and related subtopics.\n"
    "Question: {input}\n"
    "Format: Bullet points with 'SUBQ:' prefix"
)

# New: Sub-question parser (extract clean list from LLM output)
def parse_subqs(text: str) -> List[str]:

    content = text.content
    return [line.split("SUBQ:")[1].strip()
            for line in text.content.split("\n")
            if "SUBQ:" in line]

# New: Chain to generate and parse sub-questions
subq_chain = subq_prompt | llm | RunnableLambda(parse_subqs)

# Modified QA prompt to handle multiple contexts
qa_system_prompt = PromptTemplate.from_template(
    "Answer using ALL context below. Connect information between contexts.\n"
    "CONTEXTS:\n{contexts}\n\n"
    "Question: {input}\n"
    "Final Answer:"
)

# Revised chain with proper data flow
full_chain = (

    RunnablePassthrough.assign(
        subqs=lambda x: subq_chain.invoke(x["input"])
    )
    .assign(
        contexts=lambda x: "\n\n".join([
            doc.page_content
            for q in x["subqs"]
            for doc in retriever.invoke(q)
        ])
    )
    .assign(
        answer=qa_system_prompt | llm  # Now properly wrapped
    )
)
