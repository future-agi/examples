"""
Interview Agent - Question Answering Module
Handles question answering for single interviews using OpenAI's GPT models
"""

import os
from typing import Dict, Any, Optional, List

import openai

class QuestionAnsweringService:
    """Service for answering questions about interview transcripts using OpenAI's GPT models"""
    
    def __init__(self, 
                 vector_storage_service,
                 api_key: Optional[str] = None, 
                 model: str = "gpt-4o"):
        """
        Initialize the question answering service
        
        Args:
            vector_storage_service: Instance of VectorStorageService
            api_key: OpenAI API key (optional, will use environment variable if not provided)
            model: OpenAI model to use for question answering (default: gpt-4)
        """
        if api_key:
            openai.api_key = api_key
        elif os.environ.get("OPENAI_API_KEY"):
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        else:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI()
        self.model = model
        self.vector_storage = vector_storage_service
    
    def answer_question(self, interview_id: str, question: str) -> Dict[str, Any]:
        """
        Answer a question about a specific interview
        
        Args:
            interview_id: ID of the interview to query
            question: User's question
            
        Returns:
            Dictionary containing answer and context
        """
        if not question or len(question.strip()) == 0:
            raise ValueError("Question cannot be empty")
        
        # Retrieve interview metadata
        try:
            interview = self.vector_storage.retrieve_interview(interview_id)
            interview_title = interview.get("title", f"Interview {interview_id}")
        except Exception as e:
            raise ValueError(f"Error retrieving interview: {str(e)}")
        
        # Get relevant context from vector database
        try:
            context_chunks = self.vector_storage.get_interview_context(question, interview_id, limit=3)
            if not context_chunks:
                # If no specific context found, use summary as fallback
                if "summary" in interview and interview["summary"]:
                    summary_text = interview["summary"].get("full_summary", "")
                    if summary_text:
                        context_chunks = [summary_text]
        except Exception as e:
            raise ValueError(f"Error retrieving context: {str(e)}")
        
        if not context_chunks:
            return {
                "answer": "I couldn't find relevant information to answer this question in the interview.",
                "context": [],
                "interview_id": interview_id,
                "interview_title": interview_title
            }
        
        # Prepare context for the model
        context_text = "\n\n".join([f"Context {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Prepare system prompt
        system_prompt = (
            f"You are an AI assistant answering questions about an interview titled '{interview_title}'. "
            "You will be provided with context from the interview transcript. "
            "Answer the user's question based ONLY on the provided context. "
            "If the context doesn't contain the information needed to answer the question, "
            "say that you don't have enough information from the interview to answer. "
            "Do not make up or infer information that is not in the context. "
            "Cite specific parts of the context to support your answer when possible."
        )
        
        # Prepare user prompt
        user_prompt = f"Context from the interview:\n\n{context_text}\n\nQuestion: {question}"
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "context": context_chunks,
                "interview_id": interview_id,
                "interview_title": interview_title
            }
            
        except Exception as e:
            raise ValueError(f"Error generating answer: {str(e)}")
    
    def get_interview_insights(self, interview_id: str) -> Dict[str, Any]:
        """
        Generate insights about a specific interview
        
        Args:
            interview_id: ID of the interview
            
        Returns:
            Dictionary containing insights
        """
        try:
            # Retrieve interview
            interview = self.vector_storage.retrieve_interview(interview_id)
            interview_title = interview.get("title", f"Interview {interview_id}")
            
            # Get summary if available
            if "summary" in interview and interview["summary"]:
                summary = interview["summary"]
                
                # If we already have insights in the summary, return those
                if "important_insights" in summary and summary["important_insights"]:
                    return {
                        "insights": summary["important_insights"],
                        "interview_id": interview_id,
                        "interview_title": interview_title
                    }
            
            # If no summary or insights available, generate from transcript
            transcript = interview.get("transcript", "")
            if not transcript:
                return {
                    "insights": "No transcript available to generate insights.",
                    "interview_id": interview_id,
                    "interview_title": interview_title
                }
            
            # Prepare system prompt for insights generation
            system_prompt = (
                f"You are an AI assistant analyzing an interview titled '{interview_title}'. "
                "Generate key insights from the interview transcript provided. "
                "Focus on identifying patterns, notable statements, underlying themes, "
                "and significant revelations. Organize insights by topic and importance."
            )
            
            # If transcript is too long, use summary instead
            if len(transcript) > 12000:  # Approximate token limit
                if "summary" in interview and interview["summary"]:
                    summary_text = interview["summary"].get("full_summary", "")
                    if summary_text:
                        transcript = summary_text
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            insights = response.choices[0].message.content
            
            return {
                "insights": insights,
                "interview_id": interview_id,
                "interview_title": interview_title
            }
            
        except Exception as e:
            raise ValueError(f"Error generating insights: {str(e)}")

# Example usage
if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.vector_storage import VectorStorageService
    
    if len(sys.argv) < 3:
        print("Usage: python question_answering.py <interview_id> <question>")
        sys.exit(1)
    
    interview_id = sys.argv[1]
    question = sys.argv[2]
    
    # Initialize services
    vector_storage = VectorStorageService()
    qa_service = QuestionAnsweringService(vector_storage)
    
    try:
        # Answer question
        result = qa_service.answer_question(interview_id, question)
        
        # Print results
        print(f"\nQuestion: {question}")
        print(f"\nAnswer for interview '{result['interview_title']}':")
        print(result["answer"])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
