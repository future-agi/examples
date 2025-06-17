"""
Knowledge Base Module for RAG Agent

This module implements the internal knowledge database components:
- Document processing pipeline
- Embedding generation
- Vector storage and retrieval mechanisms
"""

import os
import uuid
from typing import List, Dict, Any, Optional, Union

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer

class KnowledgeBase:
    """
    Knowledge Base class that handles document processing, embedding generation,
    and vector storage/retrieval.
    """
    
    def __init__(
        self, 
        persist_directory: str = "../data/chroma_db",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize the Knowledge Base.
        
        Args:
            persist_directory: Directory to persist the vector database
            embedding_model_name: Name of the sentence-transformers model to use
            chunk_size: Size of text chunks for document splitting
            chunk_overlap: Overlap between chunks
        """
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
    
    def add_documents(
        self, 
        documents: List[Union[str, Dict[str, Any], Document]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Process and add documents to the knowledge base.
        
        Args:
            documents: List of documents to add (can be strings, dicts, or Document objects)
            metadatas: Optional list of metadata dicts for each document
            
        Returns:
            List of document IDs
        """
        # Convert all documents to Document objects if they aren't already
        doc_objects = []
        
        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                doc_objects.append(Document(page_content=doc, metadata=metadata))
            elif isinstance(doc, dict):
                content = doc.get("content", "") or doc.get("text", "") or doc.get("page_content", "")
                metadata = doc.get("metadata", {}) or metadatas[i] if metadatas and i < len(metadatas) else {}
                doc_objects.append(Document(page_content=content, metadata=metadata))
            elif isinstance(doc, Document):
                # If metadata is provided, update the document's metadata
                if metadatas and i < len(metadatas):
                    doc.metadata.update(metadatas[i])
                doc_objects.append(doc)
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(doc_objects)
        
        # Generate IDs, texts, and metadatas for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        texts = [chunk.page_content for chunk in chunks]
        chunk_metadatas = [chunk.metadata for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=chunk_metadatas
        )
        
        return ids
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Query string
            n_results: Number of results to return
            filter_criteria: Optional filter criteria for metadata
            
        Returns:
            List of dictionaries containing document content and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_criteria
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            })
        
        return formatted_results
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: ID of the document to delete
        """
        self.collection.delete(ids=[document_id])
    
    def clear(self) -> None:
        """
        Clear all documents from the knowledge base.
        """
        # Get all document IDs directly from the collection
        try:
            result = self.collection.get()
            if result and "ids" in result and result["ids"]:
                # Filter out any None values and ensure all IDs are strings
                valid_ids = [str(id_) for id_ in result["ids"] if id_ is not None]
                if valid_ids:
                    self.collection.delete(ids=valid_ids)
        except Exception as e:
            print(f"Error clearing knowledge base: {str(e)}")
            # If the collection is empty or doesn't exist yet, this is fine
    
    def get_document_count(self) -> int:
        """
        Get the number of documents in the knowledge base.
        
        Returns:
            Number of documents
        """
        return self.collection.count()
