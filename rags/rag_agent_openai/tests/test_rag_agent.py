"""
Test script for validating RAG agent functionality
"""

import sys
import os
import time
import uuid
from typing import List, Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from knowledge_base import KnowledgeBase
from rag_pipeline import RAGPipeline, ChatHistoryManager
from sample_data import SAMPLE_DATA, load_sample_data_to_knowledge_base
from mock_openai import mock_openai

# Use mock OpenAI for testing
import openai
openai.chat = mock_openai.chat

def test_knowledge_base():
    """Test knowledge base functionality"""
    print("\n=== Testing Knowledge Base ===")
    
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Clear existing data
    kb.clear()
    print(f"Cleared knowledge base. Document count: {kb.get_document_count()}")
    
    # Load sample data
    doc_ids = load_sample_data_to_knowledge_base(kb, SAMPLE_DATA)
    print(f"Added {len(doc_ids)} documents to knowledge base")
    
    # Test search functionality
    test_queries = [
        "What is machine learning?",
        "Explain RAG systems",
        "What are the effects of climate change?",
        "Tell me about ancient Egypt"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = kb.search(query, n_results=2)
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Title: {result['metadata'].get('title', 'Unknown')}")
            print(f"  Distance: {result['distance']}")
            print(f"  Content snippet: {result['content'][:100]}...")
    
    return kb

def test_rag_pipeline(kb: KnowledgeBase):
    """Test RAG pipeline functionality"""
    print("\n=== Testing RAG Pipeline ===")
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(knowledge_base=kb)
    
    # Test question breakdown
    complex_question = "What are the components of RAG systems and how do they compare to traditional deep learning approaches?"
    print(f"\nComplex question: {complex_question}")
    
    sub_questions = rag_pipeline.breakdown_question(complex_question)
    print(f"Breakdown into {len(sub_questions)} sub-questions:")
    for i, q in enumerate(sub_questions):
        print(f"  {i+1}. {q}")
    
    # Test context retrieval and reranking
    print("\nTesting context retrieval and reranking...")
    retrieved_contexts = rag_pipeline.retrieve_context(sub_questions)
    print(f"Retrieved {len(retrieved_contexts)} contexts")
    
    reranked_contexts = rag_pipeline.rerank_context(complex_question, retrieved_contexts)
    print(f"Reranked to {len(reranked_contexts)} contexts")
    
    for i, context in enumerate(reranked_contexts[:2]):  # Show top 2
        print(f"Context {i+1}:")
        print(f"  Title: {context['metadata'].get('title', 'Unknown')}")
        print(f"  Rerank score: {context.get('rerank_score', 'N/A')}")
    
    # Test answer generation
    print("\nTesting answer generation...")
    answer, used_contexts = rag_pipeline.process_query(complex_question)
    
    print(f"Generated answer ({len(answer)} chars):")
    print(f"{answer[:300]}...")
    print(f"Used {len(used_contexts)} contexts for generation")
    
    # Test follow-up question with chat history
    print("\nTesting follow-up question with chat history...")
    
    # Create chat history
    chat_history = [
        {"role": "user", "content": complex_question},
        {"role": "assistant", "content": answer}
    ]
    
    follow_up = "Can you explain more about the reranking process?"
    print(f"Follow-up question: {follow_up}")
    
    follow_up_answer, _ = rag_pipeline.process_query(follow_up, chat_history=chat_history)
    
    print(f"Follow-up answer ({len(follow_up_answer)} chars):")
    print(f"{follow_up_answer[:300]}...")
    
    return rag_pipeline

def test_chat_history_manager():
    """Test chat history manager functionality"""
    print("\n=== Testing Chat History Manager ===")
    
    # Initialize chat history manager
    chat_manager = ChatHistoryManager(max_history_length=5)
    
    # Create test session
    session_id = str(uuid.uuid4())
    print(f"Created test session: {session_id}")
    
    # Add messages
    test_conversation = [
        ("user", "What is machine learning?"),
        ("assistant", "Machine learning is a subset of AI..."),
        ("user", "How does it differ from deep learning?"),
        ("assistant", "Deep learning is a specialized form of machine learning..."),
        ("user", "Give me an example of a machine learning algorithm"),
        ("assistant", "Linear regression is a common machine learning algorithm...")
    ]
    
    for role, content in test_conversation:
        chat_manager.add_message(session_id, role, content)
    
    # Get history
    history = chat_manager.get_history(session_id)
    print(f"Added {len(history)} messages to history")
    
    # Print history
    print("\nChat history:")
    for i, msg in enumerate(history):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
    
    # Test history limit
    print("\nTesting history limit...")
    for i in range(10):
        chat_manager.add_message(session_id, "user", f"Test message {i}")
        chat_manager.add_message(session_id, "assistant", f"Test response {i}")
    
    history = chat_manager.get_history(session_id)
    print(f"History length after adding 10 more exchanges: {len(history)}")
    
    # Test clear history
    chat_manager.clear_history(session_id)
    history = chat_manager.get_history(session_id)
    print(f"History length after clearing: {len(history)}")
    
    return chat_manager

def main():
    """Main test function"""
    print("Starting RAG Agent Validation Tests")
    
    # Test knowledge base
    kb = test_knowledge_base()
    
    # Test RAG pipeline
    rag_pipeline = test_rag_pipeline(kb)
    
    # Test chat history manager
    chat_manager = test_chat_history_manager()
    
    print("\n=== All Tests Completed ===")
    print("RAG Agent validation successful!")

if __name__ == "__main__":
    main()
