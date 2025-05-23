"""
Interview Agent - Multi-Interview Analysis Module
Handles analysis and question answering across multiple interviews
"""

import os
from typing import Dict, Any, Optional, List

import openai

class MultiInterviewAnalysisService:
    """Service for analyzing and answering questions across multiple interviews"""
    
    def __init__(self, 
                 vector_storage_service,
                 api_key: Optional[str] = None, 
                 model: str = "gpt-4o"):
        """
        Initialize the multi-interview analysis service
        
        Args:
            vector_storage_service: Instance of VectorStorageService
            api_key: OpenAI API key (optional, will use environment variable if not provided)
            model: OpenAI model to use for analysis (default: gpt-4)
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
    
    def analyze_interviews(self, interview_ids: List[str], query: str) -> Dict[str, Any]:
        """
        Analyze multiple interviews based on a specific query
        
        Args:
            interview_ids: List of interview IDs to analyze
            query: Analysis query or topic
            
        Returns:
            Dictionary containing analysis results
        """
        if not interview_ids:
            raise ValueError("No interview IDs provided")
        
        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")
        
        # Get interview metadata
        interviews_metadata = []
        for interview_id in interview_ids:
            try:
                interview = self.vector_storage.retrieve_interview(interview_id)
                interviews_metadata.append({
                    "id": interview_id,
                    "title": interview.get("title", f"Interview {interview_id}"),
                    "date_uploaded": interview.get("date_uploaded", "Unknown date")
                })
            except Exception as e:
                print(f"Warning: Could not retrieve metadata for interview {interview_id}: {str(e)}")
                interviews_metadata.append({
                    "id": interview_id,
                    "title": f"Interview {interview_id}",
                    "date_uploaded": "Unknown date"
                })
        
        # Get relevant context from each interview
        context_by_interview = self.vector_storage.get_multi_interview_context(
            query, interview_ids, limit_per_interview=2
        )
        
        # Prepare context for the model
        context_sections = []
        
        for interview_id, context_chunks in context_by_interview.items():
            if not context_chunks:
                continue
                
            # Find interview metadata
            interview_meta = next((meta for meta in interviews_metadata if meta["id"] == interview_id), 
                                 {"id": interview_id, "title": f"Interview {interview_id}"})
            
            # Add context from this interview
            context_text = "\n\n".join(context_chunks)
            context_sections.append(
                f"--- From Interview: {interview_meta['title']} (ID: {interview_id}) ---\n\n{context_text}"
            )
        
        if not context_sections:
            return {
                "analysis": "No relevant information found in the selected interviews for this query.",
                "interviews": interviews_metadata,
                "query": query
            }
        
        # Combine all context
        combined_context = "\n\n".join(context_sections)
        
        # Prepare system prompt
        system_prompt = (
            "You are an AI assistant analyzing multiple interviews. "
            "You will be provided with context from several different interviews. "
            "Your task is to analyze the information across these interviews based on the user's query. "
            "Compare and contrast perspectives, identify common themes, note contradictions, "
            "and synthesize insights across the interviews. "
            "Base your analysis ONLY on the provided context. "
            "Cite specific interviews when referencing particular points."
        )
        
        # Prepare user prompt
        user_prompt = (
            f"Query: {query}\n\n"
            f"Context from {len(interviews_metadata)} interviews:\n\n{combined_context}\n\n"
            "Please provide a comprehensive analysis based on the above context from multiple interviews."
        )
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "analysis": analysis,
                "interviews": interviews_metadata,
                "query": query,
                "context_by_interview": {id: "\n\n".join(chunks) for id, chunks in context_by_interview.items() if chunks}
            }
            
        except Exception as e:
            raise ValueError(f"Error generating analysis: {str(e)}")
    
    def compare_interviews(self, interview_ids: List[str], aspects: List[str] = None) -> Dict[str, Any]:
        """
        Compare multiple interviews across specific aspects
        
        Args:
            interview_ids: List of interview IDs to compare
            aspects: Optional list of specific aspects to compare (e.g., ["main topic", "opinions", "background"])
            
        Returns:
            Dictionary containing comparison results
        """
        if not interview_ids or len(interview_ids) < 2:
            raise ValueError("At least two interview IDs must be provided for comparison")
        
        # Default aspects if none provided
        if not aspects:
            aspects = ["main topics", "key insights", "perspectives", "notable quotes", "context and background"]
        
        # Get interview summaries
        interviews_data = []
        
        for interview_id in interview_ids:
            try:
                interview = self.vector_storage.retrieve_interview(interview_id)
                
                # Get summary if available, otherwise use transcript excerpts
                if "summary" in interview and interview["summary"]:
                    summary = interview["summary"].get("full_summary", "")
                    if not summary:
                        # Try to construct from sections
                        sections = interview["summary"].get("sections", {})
                        summary = "\n\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in sections.items() if v])
                else:
                    # If no summary, get transcript excerpts
                    transcript = interview.get("transcript", "")
                    if transcript:
                        # Take beginning, middle and end excerpts
                        words = transcript.split()
                        if len(words) > 300:
                            beginning = " ".join(words[:100])
                            middle_start = max(0, len(words)//2 - 50)
                            middle = " ".join(words[middle_start:middle_start+100])
                            end = " ".join(words[-100:])
                            summary = f"Beginning excerpt: {beginning}\n\nMiddle excerpt: {middle}\n\nEnd excerpt: {end}"
                        else:
                            summary = transcript
                    else:
                        summary = "No transcript or summary available."
                
                interviews_data.append({
                    "id": interview_id,
                    "title": interview.get("title", f"Interview {interview_id}"),
                    "summary": summary
                })
                
            except Exception as e:
                print(f"Warning: Could not retrieve data for interview {interview_id}: {str(e)}")
                interviews_data.append({
                    "id": interview_id,
                    "title": f"Interview {interview_id}",
                    "summary": "Could not retrieve interview data."
                })
        
        # Prepare system prompt
        system_prompt = (
            "You are an AI assistant comparing multiple interviews. "
            f"You will analyze {len(interviews_data)} different interviews and compare them "
            f"across the following aspects: {', '.join(aspects)}. "
            "Create a structured comparison that highlights similarities and differences "
            "between the interviews for each aspect. "
            "Be specific and cite content from the interviews to support your analysis."
        )
        
        # Prepare user prompt with interview data
        interview_sections = []
        
        for i, interview in enumerate(interviews_data):
            interview_sections.append(
                f"Interview {i+1}: {interview['title']} (ID: {interview['id']})\n\n{interview['summary']}"
            )
        
        user_prompt = (
            f"Please compare the following {len(interviews_data)} interviews "
            f"across these aspects: {', '.join(aspects)}.\n\n"
            + "\n\n---\n\n".join(interview_sections)
        )
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            comparison = response.choices[0].message.content
            
            return {
                "comparison": comparison,
                "interviews": [{"id": i["id"], "title": i["title"]} for i in interviews_data],
                "aspects": aspects
            }
            
        except Exception as e:
            raise ValueError(f"Error generating comparison: {str(e)}")
    
    def identify_patterns(self, interview_ids: List[str], min_interviews: int = 2) -> Dict[str, Any]:
        """
        Identify patterns and common themes across multiple interviews
        
        Args:
            interview_ids: List of interview IDs to analyze
            min_interviews: Minimum number of interviews a pattern must appear in
            
        Returns:
            Dictionary containing pattern analysis results
        """
        if not interview_ids:
            raise ValueError("No interview IDs provided")
        
        if len(interview_ids) < min_interviews:
            raise ValueError(f"At least {min_interviews} interviews required for pattern analysis")
        
        # Get interview summaries
        interviews_data = []
        
        for interview_id in interview_ids:
            try:
                interview = self.vector_storage.retrieve_interview(interview_id)
                
                # Get summary if available
                if "summary" in interview and interview["summary"]:
                    # Prioritize key topics and insights sections
                    sections = interview["summary"].get("sections", {})
                    key_content = []
                    
                    if "key_topics" in sections and sections["key_topics"]:
                        key_content.append(f"Key Topics: {sections['key_topics']}")
                    
                    if "important_insights" in sections and sections["important_insights"]:
                        key_content.append(f"Important Insights: {sections['important_insights']}")
                    
                    if not key_content and "executive_summary" in sections and sections["executive_summary"]:
                        key_content.append(f"Executive Summary: {sections['executive_summary']}")
                    
                    summary = "\n\n".join(key_content) if key_content else interview["summary"].get("full_summary", "")
                else:
                    summary = "No summary available."
                
                interviews_data.append({
                    "id": interview_id,
                    "title": interview.get("title", f"Interview {interview_id}"),
                    "summary": summary
                })
                
            except Exception as e:
                print(f"Warning: Could not retrieve data for interview {interview_id}: {str(e)}")
        
        if not interviews_data:
            return {
                "patterns": "Could not retrieve data for any of the specified interviews.",
                "interviews": []
            }
        
        # Prepare system prompt
        system_prompt = (
            "You are an AI assistant analyzing patterns across multiple interviews. "
            f"You will analyze summaries from {len(interviews_data)} different interviews and identify: "
            "1. Common themes that appear across multiple interviews\n"
            "2. Recurring perspectives or opinions\n"
            "3. Contradictions or disagreements between interviews\n"
            "4. Unique insights that stand out\n"
            f"Focus on patterns that appear in at least {min_interviews} interviews. "
            "Be specific and cite which interviews contain each pattern."
        )
        
        # Prepare user prompt with interview data
        interview_sections = []
        
        for i, interview in enumerate(interviews_data):
            interview_sections.append(
                f"Interview {i+1}: {interview['title']} (ID: {interview['id']})\n\n{interview['summary']}"
            )
        
        user_prompt = (
            f"Please identify patterns across these {len(interviews_data)} interviews:\n\n"
            + "\n\n---\n\n".join(interview_sections)
        )
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            pattern_analysis = response.choices[0].message.content
            
            return {
                "patterns": pattern_analysis,
                "interviews": [{"id": i["id"], "title": i["title"]} for i in interviews_data],
                "min_interviews": min_interviews
            }
            
        except Exception as e:
            raise ValueError(f"Error identifying patterns: {str(e)}")

# Example usage
if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.vector_storage import VectorStorageService
    
    # Initialize services
    vector_storage = VectorStorageService()
    multi_analysis = MultiInterviewAnalysisService(vector_storage)
    
    # List available interviews
    interviews = vector_storage.list_interviews()
    
    if not interviews:
        print("No interviews found in storage.")
        sys.exit(1)
    
    print("Available interviews:")
    for i, interview in enumerate(interviews):
        print(f"{i+1}. {interview['title']} (ID: {interview['id']})")
    
    # Example: Compare first two interviews if available
    if len(interviews) >= 2:
        interview_ids = [interviews[0]['id'], interviews[1]['id']]
        
        try:
            result = multi_analysis.compare_interviews(interview_ids)
            
            print("\nComparison of interviews:")
            print(result["comparison"])
            
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
