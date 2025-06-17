"""
Gradio UI Module for RAG Agent

This module implements the ChatGPT-like Gradio UI with chat history.
"""

import os
import uuid
import time
from typing import List, Dict, Any, Tuple, Optional

import gradio as gr

from knowledge_base import KnowledgeBase
from rag_pipeline import RAGPipeline, ChatHistoryManager

# CSS for styling the UI to look like ChatGPT
CUSTOM_CSS = """
.gradio-container {
    max-width: 850px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}

.user-message {
    background-color: #f7f7f8;
}

.assistant-message {
    background-color: #ffffff;
    border: 1px solid #e5e5e5;
}

.message-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
}

.avatar {
    width: 30px;
    height: 30px;
    border-radius: 0.2rem;
    margin-right: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.user-avatar {
    background-color: #6e56cf;
    color: white;
}

.assistant-avatar {
    background-color: #19c37d;
    color: white;
}

.message-content {
    margin-left: 2.5rem;
    margin-top: 0.5rem;
}

.sources-section {
    margin-top: 1rem;
    padding-top: 0.5rem;
    border-top: 1px solid #e5e5e5;
    font-size: 0.9rem;
    color: #666;
}

.source-item {
    margin-bottom: 0.25rem;
}

.clear-button {
    margin-bottom: 1rem;
}

.footer {
    text-align: center;
    margin-top: 2rem;
    font-size: 0.8rem;
    color: #666;
}
"""

class GradioUI:
    """
    Gradio UI class for the RAG Agent.
    """
    
    def __init__(
        self, 
        knowledge_base: KnowledgeBase,
        rag_pipeline: RAGPipeline,
        chat_history_manager: ChatHistoryManager,
        title: str = "RAG Knowledge Assistant",
        description: str = "Ask questions about the internal knowledge base."
    ):
        """
        Initialize the Gradio UI.
        
        Args:
            knowledge_base: KnowledgeBase instance
            rag_pipeline: RAGPipeline instance
            chat_history_manager: ChatHistoryManager instance
            title: Title of the UI
            description: Description of the UI
        """
        self.knowledge_base = knowledge_base
        self.rag_pipeline = rag_pipeline
        self.chat_history_manager = chat_history_manager
        self.title = title
        self.description = description
        
        # Initialize the Gradio interface
        self.interface = self._create_interface()
    
    def _create_interface(self) -> gr.Blocks:
        """
        Create the Gradio interface.
        
        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(css=CUSTOM_CSS) as interface:
            gr.Markdown(f"# {self.title}")
            gr.Markdown(self.description)
            
            with gr.Row():
                with gr.Column():
                    # Session ID (hidden)
                    session_id = gr.State(value=str(uuid.uuid4()))
                    
                    # Chat history display
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=500,
                        avatar_images=("👤", "🤖")
                    )
                    
                    # User input
                    with gr.Row():
                        user_input = gr.Textbox(
                            placeholder="Ask a question...",
                            label="Your question",
                            scale=9
                        )
                        submit_btn = gr.Button("Send", scale=1)
                    
                    # Clear button
                    clear_btn = gr.Button("Clear Conversation", elem_classes=["clear-button"])
                    
                    # Sources display (initially empty)
                    sources_md = gr.Markdown(
                        label="Sources",
                        value="",
                        visible=True
                    )
            
            # Footer
            gr.Markdown(
                "This RAG agent uses a retrieval-augmented generation approach to answer questions based on an internal knowledge base.",
                elem_classes=["footer"]
            )
            
            # Event handlers
            submit_btn.click(
                fn=self._handle_query,
                inputs=[user_input, chatbot, session_id],
                outputs=[user_input, chatbot, sources_md]
            )
            
            user_input.submit(
                fn=self._handle_query,
                inputs=[user_input, chatbot, session_id],
                outputs=[user_input, chatbot, sources_md]
            )
            
            clear_btn.click(
                fn=self._clear_conversation,
                inputs=[session_id],
                outputs=[chatbot, sources_md]
            )
        
        return interface
    
    def _handle_query(
        self, 
        query: str, 
        chat_history: List[Tuple[str, str]],
        session_id: str
    ) -> Tuple[str, List[Tuple[str, str]], str]:
        """
        Handle a user query.
        
        Args:
            query: User query
            chat_history: Current chat history
            session_id: Session ID
            
        Returns:
            Tuple of (empty string, updated chat history, sources markdown)
        """
        if not query.strip():
            return "", chat_history, ""
        
        # Add user message to chat history manager
        self.chat_history_manager.add_message(session_id, "user", query)
        
        # Get chat history for context
        history_for_context = self.chat_history_manager.get_history(session_id)
        
        # Process query through RAG pipeline
        try:
            answer, contexts = self.rag_pipeline.process_query(
                question=query,
                chat_history=history_for_context
            )
            
            # Add assistant message to chat history manager
            self.chat_history_manager.add_message(session_id, "assistant", answer)
            
            # Update chat history for display
            chat_history.append((query, answer))
            
            # Format sources
            sources_md = self._format_sources(contexts)
            
            return "", chat_history, sources_md
        
        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            chat_history.append((query, error_message))
            return "", chat_history, ""
    
    def _clear_conversation(self, session_id: str) -> Tuple[List[Tuple[str, str]], str]:
        """
        Clear the conversation history.
        
        Args:
            session_id: Session ID
            
        Returns:
            Tuple of (empty chat history, empty sources markdown)
        """
        # Clear chat history in manager
        self.chat_history_manager.clear_history(session_id)
        
        # Return empty chat history and sources
        return [], ""
    
    def _format_sources(self, contexts: List[Dict[str, Any]]) -> str:
        """
        Format the sources from contexts.
        
        Args:
            contexts: List of context documents
            
        Returns:
            Markdown formatted sources
        """
        if not contexts:
            return ""
        
        sources_md = "### Sources\n\n"
        
        # Deduplicate sources by title
        seen_titles = set()
        unique_contexts = []
        
        for context in contexts:
            title = context["metadata"].get("title", "Unknown")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_contexts.append(context)
        
        # Format each source
        for i, context in enumerate(unique_contexts):
            title = context["metadata"].get("title", "Unknown")
            category = context["metadata"].get("category", "")
            
            sources_md += f"{i+1}. **{title}**"
            if category:
                sources_md += f" (Category: {category})"
            sources_md += "\n"
        
        return sources_md
    
    def launch(self, share: bool = False, server_port: int = 7860) -> None:
        """
        Launch the Gradio interface.
        
        Args:
            share: Whether to create a public link
            server_port: Port to run the server on
        """
        self.interface.launch(
            share=share,
            server_port=server_port,
            server_name="0.0.0.0"
        )

def create_ui() -> GradioUI:
    """
    Create and configure the Gradio UI with all components.
    
    Returns:
        Configured GradioUI instance
    """
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(knowledge_base=kb)
    
    # Initialize chat history manager
    chat_history_manager = ChatHistoryManager()
    
    # Create UI
    ui = GradioUI(
        knowledge_base=kb,
        rag_pipeline=rag_pipeline,
        chat_history_manager=chat_history_manager,
        title="RAG Knowledge Assistant",
        description="Ask questions about machine learning, deep learning, NLP, RAG systems, climate change, renewable energy, and history."
    )
    
    return ui

if __name__ == "__main__":
    # Create and launch UI
    ui = create_ui()
    ui.launch()
