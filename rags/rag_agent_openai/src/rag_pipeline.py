"""
RAG Pipeline Module for RAG Agent

This module implements the RAG pipeline components:
- Question breakdown
- Context retrieval
- Context reranking
- Answer generation
- Chat history management
"""

import re
from typing import List, Dict, Any, Optional, Tuple

import openai
from sentence_transformers import CrossEncoder

from knowledge_base import KnowledgeBase

class RAGPipeline:
    """
    RAG Pipeline class that handles question processing, context retrieval,
    reranking, and answer generation.
    """
    
    def __init__(
        self, 
        knowledge_base: KnowledgeBase,
        reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        openai_model: str = "gpt-4o",
        max_context_chunks: int = 5
    ):
        """
        Initialize the RAG Pipeline.
        
        Args:
            knowledge_base: KnowledgeBase instance
            reranker_model_name: Name of the cross-encoder model for reranking
            openai_model: OpenAI model to use for generation
            max_context_chunks: Maximum number of context chunks to include
        """
        self.knowledge_base = knowledge_base
        self.reranker_model_name = reranker_model_name
        self.openai_model = openai_model
        self.max_context_chunks = max_context_chunks
        
        # Initialize reranker model
        self.reranker = CrossEncoder(reranker_model_name)
    
    def breakdown_question(self, question: str) -> List[str]:
        """
        Break down a complex question into simpler sub-questions.
        
        Args:
            question: The original question
            
        Returns:
            List of sub-questions
        """
        # Use OpenAI to break down the question
        prompt = f"""
        Break down the following complex question into simpler, atomic sub-questions that would help answer the original question.
        If the question is already simple, return it as is.
        
        Original question: {question}
        
        Output format:
        - Sub-question 1
        - Sub-question 2
        ...
        
        Only output the sub-questions, nothing else.
        """
        
        response = openai.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that breaks down complex questions into simpler sub-questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        # Extract sub-questions from the response
        sub_questions_text = response.choices[0].message.content.strip()
        
        # Parse the sub-questions
        sub_questions = []
        for line in sub_questions_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                sub_questions.append(line[2:])
            elif line.startswith('* '):
                sub_questions.append(line[2:])
            elif re.match(r'^\d+\.', line):
                sub_questions.append(re.sub(r'^\d+\.\s*', '', line))
        
        # If no sub-questions were extracted, use the original question
        if not sub_questions:
            sub_questions = [question]
        
        return sub_questions
    
    def retrieve_context(
        self, 
        questions: List[str], 
        n_results_per_question: int = 3,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for each question.
        
        Args:
            questions: List of questions
            n_results_per_question: Number of results to retrieve per question
            filter_criteria: Optional filter criteria for metadata
            
        Returns:
            List of retrieved context documents
        """
        all_results = []
        
        for question in questions:
            results = self.knowledge_base.search(
                query=question,
                n_results=n_results_per_question,
                filter_criteria=filter_criteria
            )
            all_results.extend(results)
        
        # Remove duplicates based on document ID
        unique_results = {}
        for result in all_results:
            if result["id"] not in unique_results:
                unique_results[result["id"]] = result
        
        return list(unique_results.values())
    
    def rerank_context(
        self, 
        question: str, 
        contexts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank retrieved contexts based on relevance to the question.
        
        Args:
            question: Original question
            contexts: List of context documents
            
        Returns:
            Reranked list of context documents
        """
        if not contexts:
            return []
        
        # Prepare pairs for reranking
        pairs = [(question, context["content"]) for context in contexts]
        
        # Get scores from reranker
        scores = self.reranker.predict(pairs)
        
        # Add scores to contexts
        for i, context in enumerate(contexts):
            context["rerank_score"] = float(scores[i])
        
        # Sort by rerank score (descending)
        reranked_contexts = sorted(contexts, key=lambda x: x["rerank_score"], reverse=True)
        
        # Limit to max_context_chunks
        return reranked_contexts[:self.max_context_chunks]
    
    def generate_answer(
        self, 
        question: str, 
        contexts: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate an answer based on the question and retrieved contexts.
        
        Args:
            question: Original question
            contexts: Reranked context documents
            chat_history: Optional chat history for follow-up questions
            
        Returns:
            Generated answer
        """
        if not contexts:
            return "I don't have enough information to answer that question."
        
        # Prepare context text
        context_text = "\n\n".join([
            f"Source: {context['metadata'].get('title', 'Unknown')}\n{context['content']}"
            for context in contexts
        ])
        
        # Prepare system message with context
        system_message = f"""
        You are a helpful assistant that answers questions based on the provided context.
        Use only the information from the context to answer the question.
        If the context doesn't contain the answer, say "I don't have enough information to answer that question."
        Always cite your sources by mentioning the titles of the documents you used.
        
        Context:
        {context_text}
        """
        
        # Prepare messages including chat history if provided
        messages = [{"role": "system", "content": system_message}]
        
        if chat_history:
            for message in chat_history:
                messages.append({"role": message["role"], "content": message["content"]})
        
        messages.append({"role": "user", "content": question})
        
        # Generate answer
        response = openai.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def process_query(
        self, 
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a query through the full RAG pipeline.
        
        Args:
            question: User question
            chat_history: Optional chat history for follow-up questions
            filter_criteria: Optional filter criteria for metadata
            
        Returns:
            Tuple of (answer, used_contexts)
        """
        # Break down question
        sub_questions = self.breakdown_question(question)
        
        # Retrieve context for all sub-questions
        retrieved_contexts = self.retrieve_context(
            questions=sub_questions,
            filter_criteria=filter_criteria
        )
        
        # Rerank contexts
        reranked_contexts = self.rerank_context(question, retrieved_contexts)
        
        # Generate answer
        answer = self.generate_answer(question, reranked_contexts, chat_history)
        
        return answer, reranked_contexts

class ChatHistoryManager:
    """
    Chat History Manager for maintaining conversation context.
    """
    
    def __init__(self, max_history_length: int = 10):
        """
        Initialize the Chat History Manager.
        
        Args:
            max_history_length: Maximum number of messages to keep in history
        """
        self.max_history_length = max_history_length
        self.sessions = {}
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the chat history.
        
        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({"role": role, "content": content})
        
        # Trim history if it exceeds max length
        if len(self.sessions[session_id]) > self.max_history_length * 2:  # *2 because each exchange has 2 messages
            self.sessions[session_id] = self.sessions[session_id][-self.max_history_length * 2:]
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get the chat history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        return self.sessions.get(session_id, [])
    
    def clear_history(self, session_id: str) -> None:
        """
        Clear the chat history for a session.
        
        Args:
            session_id: Session identifier
        """
        self.sessions[session_id] = []
