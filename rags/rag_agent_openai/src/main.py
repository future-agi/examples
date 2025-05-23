"""
Main Application Module for RAG Agent

This module integrates all components and provides the entry point for the application.
"""

import os
import argparse
from typing import Dict, Any

# Add dotenv for env loading
from dotenv import load_dotenv
load_dotenv()
# Add tracing and guardrails imports
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType
from fi.evals import ProtectClient, EvalClient
from opentelemetry import trace

from knowledge_base import KnowledgeBase
from rag_pipeline import RAGPipeline, ChatHistoryManager
from gradio_ui import GradioUI
from sample_data import SAMPLE_DATA, load_sample_data_to_knowledge_base

def parse_args() -> Dict[str, Any]:
    """
    Parse command line arguments.
    
    Returns:
        Dictionary of arguments
    """
    parser = argparse.ArgumentParser(description="RAG Agent with ChatGPT-like UI")
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=7860,
        help="Port to run the Gradio server on"
    )
    
    parser.add_argument(
        "--share", 
        action="store_true",
        help="Create a public link for sharing"
    )
    
    parser.add_argument(
        "--reset-db", 
        action="store_true",
        help="Reset the knowledge base and reload sample data"
    )
    
    return vars(parser.parse_args())

def initialize_components(reset_db: bool = False) -> tuple:
    """
    Initialize all components of the RAG agent.
    
    Args:
        reset_db: Whether to reset the knowledge base
        
    Returns:
        Tuple of (knowledge_base, rag_pipeline, chat_history_manager)
    """
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Reset knowledge base if requested
    if reset_db:
        kb.clear()
        print("Knowledge base cleared.")
    
    # Check if knowledge base is empty and load sample data if needed
    if kb.get_document_count() == 0:
        print("Knowledge base is empty. Loading sample data...")
        doc_ids = load_sample_data_to_knowledge_base(kb, SAMPLE_DATA)
        print(f"Added {len(doc_ids)} documents to knowledge base.")
    else:
        print(f"Knowledge base contains {kb.get_document_count()} documents.")
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(knowledge_base=kb)
    
    # Initialize chat history manager
    chat_history_manager = ChatHistoryManager()
    
    return kb, rag_pipeline, chat_history_manager

# Load environment variables from .env

# Initialize tracing
tracer_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="FUTURE_AGI",
)

tracer = trace.get_tracer(__name__)

from traceai_openai import OpenAIInstrumentor

OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

def main() -> None:
    """
    Main function to run the RAG agent.
    """

    # Set up protection rules (from sample.py)
    protect_rules = [
        {"metric": "Toxicity"},
        {"metric": "Prompt Injection"},
        {"metric": "Data Privacy"},
        {"metric": "Tone", "contains": ["Aggressive", "Threatening"]},
    ]

    # Parse arguments
    args = parse_args()

    # Initialize components
    kb, rag_pipeline, chat_history_manager = initialize_components(reset_db=args["reset_db"])

    # Set up FI evaluator and protector
    evaluator = EvalClient(
        fi_api_key=os.environ.get("FI_API_KEY"),
        fi_secret_key=os.environ.get("FI_SECRET_KEY"),
        fi_base_url=os.environ.get("FI_BASE_URL")
    )
    protector = ProtectClient(evaluator=evaluator)

    # Wrap the Gradio UI to add input/output protection and tracing
    class GuardedGradioUI(GradioUI):
        def _handle_query(self, query, chat_history, session_id):
            # Protect user input
            protection_result = protector.protect(
                inputs=query,
                protect_rules=protect_rules,
                reason=True,
                timeout=30000
            )
            if protection_result["status"] != "passed":
                blocked_reason = protection_result.get("reasons", "Blocked by guardrails.")
                print( "protection_result",protection_result)
                chat_history.append((query, f"Input was blocked. Reason: {blocked_reason}"))
                return "", chat_history, ""
            # Trace the answer generation
            with tracer.start_as_current_span("rag_pipeline.process_query"):
                answer, contexts = self.rag_pipeline.process_query(
                    question=query,
                    chat_history=self.chat_history_manager.get_history(session_id)
                )
            # Protect output
            output_protection = protector.protect(
                inputs=answer,
                protect_rules=protect_rules,
                reason=True,
                timeout=30000
            )
            if output_protection["status"] != "passed":
                print( "output_protection",output_protection)
                blocked_reason = output_protection.get("reasons", "Output blocked by guardrails.")
                chat_history.append((query, f"Output was blocked. Reason: {blocked_reason}"))
                return "", chat_history, ""
            self.chat_history_manager.add_message(session_id, "assistant", answer)
            chat_history.append((query, answer))
            sources_md = self._format_sources(contexts)
            return "", chat_history, sources_md

    # Create UI
    ui = GuardedGradioUI(
        knowledge_base=kb,
        rag_pipeline=rag_pipeline,
        chat_history_manager=chat_history_manager,
        title="RAG Knowledge Assistant",
        description="Ask questions about machine learning, deep learning, NLP, RAG systems, climate change, renewable energy, and history."
    )

    # Launch UI
    print(f"Launching Gradio UI on port {args['port']}...")
    ui.launch(share=args["share"], server_port=args["port"])

if __name__ == "__main__":
    main()
