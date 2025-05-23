"""
Interview Agent - Vector Storage Module
Handles storing and retrieving interview transcripts using ChromaDB
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions
from chromadb.errors import NotFoundError

class VectorStorageService:
    """Service for storing and retrieving interview transcripts using ChromaDB"""
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "interviews",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the vector storage service
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
            openai_api_key: OpenAI API key for embeddings (optional)
        """
        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Set up OpenAI API key for embeddings
        if openai_api_key:
            self.openai_api_key = openai_api_key
        elif os.environ.get("OPENAI_API_KEY"):
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        else:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name="text-embedding-3-small"
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except (ValueError, NotFoundError):
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
    
    def store_interview(self, 
                        transcript: str, 
                        summary: Dict[str, Any], 
                        metadata: Dict[str, Any]) -> str:
        """
        Store an interview transcript in the vector database
        
        Args:
            transcript: Full interview transcript text
            summary: Dictionary containing summary sections
            metadata: Dictionary containing interview metadata
            
        Returns:
            Interview ID
        """
        if not transcript or len(transcript.strip()) == 0:
            raise ValueError("Transcript cannot be empty")
        
        # Generate a unique ID for the interview
        interview_id = str(uuid.uuid4())
        
        # Prepare metadata
        full_metadata = {
            "interview_id": interview_id,
            "title": metadata.get("title", f"Interview {interview_id[:8]}"),
            "date_uploaded": metadata.get("date_uploaded", datetime.now().isoformat()),
            "audio_metadata": metadata.get("audio_metadata", {}),
            "summary_available": True
        }
        
        # Add custom metadata if provided
        if "custom_metadata" in metadata:
            full_metadata.update(metadata["custom_metadata"])
        
        # Store full interview document in a separate JSON file
        interview_doc = {
            "id": interview_id,
            "title": full_metadata["title"],
            "date_uploaded": full_metadata["date_uploaded"],
            "audio_metadata": full_metadata["audio_metadata"],
            "transcript": transcript,
            "summary": summary,
            "metadata": full_metadata
        }
        
        # Ensure interviews directory exists
        os.makedirs("./interviews", exist_ok=True)
        
        # Save full interview document
        with open(f"./interviews/{interview_id}.json", "w") as f:
            json.dump(interview_doc, f, indent=2)
        
        # Split transcript into chunks for vector storage
        chunks = self._chunk_transcript(transcript)
        
        # Prepare data for ChromaDB
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{interview_id}_{i}"
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk)
            
            # Metadata for this chunk
            chunk_metadata = {
                "interview_id": interview_id,
                "chunk_index": i,
                "chunk_count": len(chunks),
                "title": full_metadata["title"]
            }
            chunk_metadatas.append(chunk_metadata)
        
        # Add chunks to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            metadatas=chunk_metadatas
        )
        
        return interview_id
    
    def retrieve_interview(self, interview_id: str) -> Dict[str, Any]:
        """
        Retrieve a full interview document by ID
        
        Args:
            interview_id: ID of the interview to retrieve
            
        Returns:
            Interview document
        """
        # Check if interview exists
        interview_path = f"./interviews/{interview_id}.json"
        if not os.path.exists(interview_path):
            raise ValueError(f"Interview with ID {interview_id} not found")
        
        # Load interview document
        with open(interview_path, "r") as f:
            interview_doc = json.load(f)
        
        return interview_doc
    
    def list_interviews(self) -> List[Dict[str, Any]]:
        """
        List all stored interviews with basic metadata
        
        Returns:
            List of interview metadata
        """
        interviews = []
        
        # Check if interviews directory exists
        if not os.path.exists("./interviews"):
            return interviews
        
        # List all JSON files in interviews directory
        for filename in os.listdir("./interviews"):
            if filename.endswith(".json"):
                interview_path = f"./interviews/{filename}"
                
                try:
                    with open(interview_path, "r") as f:
                        interview_doc = json.load(f)
                    
                    # Extract basic metadata
                    interviews.append({
                        "id": interview_doc["id"],
                        "title": interview_doc["title"],
                        "date_uploaded": interview_doc["date_uploaded"],
                        "summary": interview_doc.get("summary", {}).get("executive_summary", "")
                    })
                except Exception as e:
                    print(f"Error loading interview {filename}: {str(e)}")
        
        # Sort by date uploaded (newest first)
        interviews.sort(key=lambda x: x["date_uploaded"], reverse=True)
        
        return interviews
    
    def search_interviews(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for interviews based on semantic similarity
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching interview chunks with metadata
        """
        if not query or len(query.strip()) == 0:
            raise ValueError("Search query cannot be empty")
        
        # Perform vector search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        # Process results
        search_results = []
        
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                chunk_id = results["ids"][0][i]
                chunk_text = results["documents"][0][i]
                chunk_metadata = results["metadatas"][0][i]
                
                search_results.append({
                    "chunk_id": chunk_id,
                    "interview_id": chunk_metadata["interview_id"],
                    "title": chunk_metadata["title"],
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
        
        return search_results
    
    def get_interview_context(self, query: str, interview_id: str, limit: int = 3) -> List[str]:
        """
        Get relevant context from a specific interview for a query
        
        Args:
            query: Query text
            interview_id: ID of the interview to search
            limit: Maximum number of chunks to return
            
        Returns:
            List of relevant text chunks
        """
        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")
        
        # Perform vector search with interview_id filter
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where={"interview_id": interview_id}
        )
        
        # Extract text chunks
        context_chunks = []
        
        if results["documents"] and len(results["documents"][0]) > 0:
            context_chunks = results["documents"][0]
        
        return context_chunks
    
    def get_multi_interview_context(self, query: str, interview_ids: List[str], limit_per_interview: int = 2) -> Dict[str, List[str]]:
        """
        Get relevant context from multiple interviews for a query
        
        Args:
            query: Query text
            interview_ids: List of interview IDs to search
            limit_per_interview: Maximum number of chunks per interview
            
        Returns:
            Dictionary mapping interview IDs to lists of relevant text chunks
        """
        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")
        
        if not interview_ids:
            raise ValueError("No interview IDs provided")
        
        # Get context for each interview
        context_by_interview = {}
        
        for interview_id in interview_ids:
            try:
                context_chunks = self.get_interview_context(query, interview_id, limit_per_interview)
                context_by_interview[interview_id] = context_chunks
            except Exception as e:
                print(f"Error getting context for interview {interview_id}: {str(e)}")
                context_by_interview[interview_id] = []
        
        return context_by_interview
    
    def delete_interview(self, interview_id: str) -> bool:
        """
        Delete an interview and its chunks from storage
        
        Args:
            interview_id: ID of the interview to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete chunks from ChromaDB
            self.collection.delete(where={"interview_id": interview_id})
            
            # Delete interview document
            interview_path = f"./interviews/{interview_id}.json"
            if os.path.exists(interview_path):
                os.remove(interview_path)
            
            return True
        except Exception as e:
            print(f"Error deleting interview {interview_id}: {str(e)}")
            return False
    
    def _chunk_transcript(self, transcript: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split transcript into overlapping chunks for vector storage
        
        Args:
            transcript: Full transcript text
            chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(transcript) <= chunk_size:
            return [transcript]
        
        # Split by paragraphs first
        paragraphs = transcript.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, start a new chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk)
                
                # Start new chunk with overlap from previous chunk
                words = current_chunk.split()
                overlap_word_count = min(len(words), overlap // 4)  # Approximate words in overlap
                overlap_text = " ".join(words[-overlap_word_count:]) if overlap_word_count > 0 else ""
                
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # If no chunks were created (rare case), split by fixed size with overlap
        if not chunks:
            chunks = []
            for i in range(0, len(transcript), chunk_size - overlap):
                chunk = transcript[i:i + chunk_size]
                chunks.append(chunk)
        
        return chunks

# Example usage
if __name__ == "__main__":
    import sys
    
    # Initialize service
    service = VectorStorageService()
    
    # Example: List all interviews
    interviews = service.list_interviews()
    print(f"Found {len(interviews)} interviews")
    
    for interview in interviews:
        print(f"ID: {interview['id']}, Title: {interview['title']}, Date: {interview['date_uploaded']}")
