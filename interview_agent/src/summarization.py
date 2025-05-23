"""
Interview Agent - Summarization Module
Handles interview summarization using OpenAI's GPT models
"""

import os
from typing import Dict, Any, Optional, List

import openai

class SummarizationService:
    """Service for generating summaries of interview transcripts using OpenAI's GPT models"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the summarization service
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
            model: OpenAI model to use for summarization (default: gpt-4)
        """
        if api_key:
            openai.api_key = api_key
        elif os.environ.get("OPENAI_API_KEY"):
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        else:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI()
        self.model = model
    
    def generate_summary(self, transcript: str, detail_level: str = "medium") -> Dict[str, Any]:
        """
        Generate a summary of the interview transcript
        
        Args:
            transcript: Full interview transcript text
            detail_level: Level of detail for the summary (low, medium, high)
            
        Returns:
            Dictionary containing summary results
        """
        if not transcript or len(transcript.strip()) == 0:
            raise ValueError("Transcript cannot be empty")
        
        # Determine token count and chunk if necessary
        # Approximate token count (rough estimate: 1 token ≈ 4 chars)
        approx_tokens = len(transcript) // 4
        
        # If transcript is too long, chunk it
        if approx_tokens > 12000:  # Leave room for response
            return self._generate_summary_for_long_transcript(transcript, detail_level)
        
        # Prepare prompt based on detail level
        system_prompt = self._get_system_prompt(detail_level)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract and structure the summary
            summary_text = response.choices[0].message.content
            
            # Parse the structured summary
            sections = self._parse_summary_sections(summary_text)
            
            return {
                "full_summary": summary_text,
                "sections": sections
            }
            
        except Exception as e:
            raise ValueError(f"Error generating summary: {str(e)}")
    
    def _generate_summary_for_long_transcript(self, transcript: str, detail_level: str) -> Dict[str, Any]:
        """
        Generate summary for long transcripts by chunking and combining
        
        Args:
            transcript: Full interview transcript text
            detail_level: Level of detail for the summary
            
        Returns:
            Dictionary containing summary results
        """
        # Split transcript into chunks (by paragraphs or fixed length)
        chunks = self._split_transcript_into_chunks(transcript)
        
        # Generate summary for each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                # Prepare prompt for chunk summarization
                system_prompt = (
                    f"You are summarizing part {i+1} of {len(chunks)} of an interview transcript. "
                    "Extract key points, main topics, and important quotes from this section only."
                )
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chunk}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                chunk_summaries.append(response.choices[0].message.content)
                
            except Exception as e:
                chunk_summaries.append(f"Error summarizing chunk {i+1}: {str(e)}")
        
        # Combine chunk summaries into a final summary
        combined_summary = "\n\n".join(chunk_summaries)
        
        # Generate final consolidated summary
        system_prompt = self._get_system_prompt(detail_level)
        system_prompt += "\nYou are creating a final summary based on partial summaries of a long interview."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": combined_summary}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            summary_text = response.choices[0].message.content
            sections = self._parse_summary_sections(summary_text)
            
            return {
                "full_summary": summary_text,
                "sections": sections
            }
            
        except Exception as e:
            raise ValueError(f"Error generating final summary: {str(e)}")
    
    def _split_transcript_into_chunks(self, transcript: str) -> List[str]:
        """
        Split a long transcript into manageable chunks
        
        Args:
            transcript: Full interview transcript text
            
        Returns:
            List of transcript chunks
        """
        # Approximate tokens per chunk (8000 tokens ≈ 32000 chars)
        chunk_size = 32000
        
        # Split by paragraphs first
        paragraphs = transcript.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, start a new chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # If no chunks were created (rare case), split by fixed size
        if not chunks:
            return [transcript[i:i+chunk_size] for i in range(0, len(transcript), chunk_size)]
        
        return chunks
    
    def _get_system_prompt(self, detail_level: str) -> str:
        """
        Get the system prompt based on detail level
        
        Args:
            detail_level: Level of detail for the summary (low, medium, high)
            
        Returns:
            System prompt for the OpenAI API
        """
        base_prompt = (
            "You are an expert interview analyst. Your task is to create a comprehensive summary "
            "of the interview transcript provided. "
        )
        
        if detail_level == "low":
            base_prompt += (
                "Create a brief summary highlighting only the most important points and key takeaways. "
                "Keep the summary concise and focused on the main topics."
            )
        elif detail_level == "high":
            base_prompt += (
                "Create a detailed summary capturing all significant points, nuances, and context. "
                "Include important quotes, detailed explanations of topics discussed, and capture "
                "the flow of the conversation."
            )
        else:  # medium (default)
            base_prompt += (
                "Create a balanced summary that captures the main points, key insights, and important "
                "context. Include relevant quotes and provide enough detail to understand the core "
                "content of the interview."
            )
        
        base_prompt += (
            "\n\nStructure your summary with the following sections:\n"
            "1. Executive Summary: A brief overview of the entire interview\n"
            "2. Key Topics: List and brief explanation of main topics discussed\n"
            "3. Important Insights: Notable points, revelations, or opinions expressed\n"
            "4. Notable Quotes: Direct quotes that capture significant moments\n"
            "5. Context and Background: Relevant context provided in the interview\n"
            "6. Conclusion: Final thoughts and overall impression"
        )
        
        return base_prompt
    
    def _parse_summary_sections(self, summary_text: str) -> Dict[str, str]:
        """
        Parse the structured summary into sections
        
        Args:
            summary_text: Full summary text
            
        Returns:
            Dictionary of summary sections
        """
        sections = {
            "executive_summary": "",
            "key_topics": "",
            "important_insights": "",
            "notable_quotes": "",
            "context_and_background": "",
            "conclusion": ""
        }
        
        # Simple parsing based on section headers
        current_section = None
        lines = summary_text.split('\n')
        
        for line in lines:
            lower_line = line.lower()
            
            if "executive summary" in lower_line:
                current_section = "executive_summary"
                continue
            elif "key topics" in lower_line:
                current_section = "key_topics"
                continue
            elif "important insights" in lower_line:
                current_section = "important_insights"
                continue
            elif "notable quotes" in lower_line:
                current_section = "notable_quotes"
                continue
            elif "context and background" in lower_line:
                current_section = "context_and_background"
                continue
            elif "conclusion" in lower_line:
                current_section = "conclusion"
                continue
            
            if current_section and line.strip():
                sections[current_section] += line + "\n"
        
        # Clean up each section (remove trailing newlines)
        for section in sections:
            sections[section] = sections[section].strip()
        
        return sections

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python summarization.py <transcript_file_path> [detail_level]")
        sys.exit(1)
    
    transcript_path = sys.argv[1]
    detail_level = sys.argv[2] if len(sys.argv) > 2 else "medium"
    
    # Initialize service
    service = SummarizationService()
    
    try:
        # Read transcript file
        with open(transcript_path, 'r') as f:
            transcript = f.read()
        
        # Generate summary
        result = service.generate_summary(transcript, detail_level)
        
        # Print results
        print("\nSummary generated successfully!")
        print("\nExecutive Summary:")
        print(result["sections"]["executive_summary"])
        
        print("\nKey Topics:")
        print(result["sections"]["key_topics"])
        
        print("\nImportant Insights:")
        print(result["sections"]["important_insights"])
        
        print("\nNotable Quotes:")
        print(result["sections"]["notable_quotes"])
        
        print("\nContext and Background:")
        print(result["sections"]["context_and_background"])
        
        print("\nConclusion:")
        print(result["sections"]["conclusion"])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
