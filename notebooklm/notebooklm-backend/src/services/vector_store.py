import os
import logging
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

# Vector database and embedding imports
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logging.warning(f"Vector database libraries not available: {e}")

from fi_instrumentation import register, FITracer
from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

tracer = trace.get_tracer(__name__)


class VectorStore:
    """
    Service for managing document embeddings and semantic search using ChromaDB
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.embedding_model = None
        self.collections = {}
        
        # Initialize ChromaDB client
        self._initialize_client()
        
        # Initialize embedding model
        self._initialize_embedding_model()
    
    def _initialize_client(self):
        """Initialize ChromaDB client"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logging.info(f"ChromaDB client initialized with persistence at {self.persist_directory}")
            
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB client: {e}")
            # Fallback to in-memory client
            self.client = chromadb.Client()
            logging.warning("Using in-memory ChromaDB client as fallback")
    
    def _initialize_embedding_model(self):
        with tracer.start_as_current_span("initialize_embedding_model") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
            """Initialize sentence transformer model for embeddings"""
            try:
                # Use a lightweight but effective model
                model_name = "all-MiniLM-L6-v2"  # 384 dimensions, good balance of speed and quality
                
                # Set cache directory to avoid repeated downloads
                cache_dir = os.path.join(os.path.dirname(self.persist_directory), "model_cache")
                os.makedirs(cache_dir, exist_ok=True)
                

                # Initialize with cache directory
                self.embedding_model = SentenceTransformer(
                    model_name, 
                    cache_folder=cache_dir,
                    device='cpu'  # Explicitly use CPU to avoid GPU issues
                )
                span.set_attribute("output.value", json.dumps(model_name))
                logging.info(f"Embedding model '{model_name}' loaded successfully from cache: {cache_dir}")
                
            except Exception as e:
                logging.error(f"Failed to load embedding model: {e}")
                self.embedding_model = None
    
    def get_or_create_collection(self, notebook_id: str) -> chromadb.Collection:
        with tracer.start_as_current_span("get_or_create_collection") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
            """
            Get or create a collection for a specific notebook
            """
            collection_name = f"notebook_{notebook_id}"
            
            if collection_name in self.collections:
                return self.collections[collection_name]
            
            try:
                # Try to get existing collection
                collection = self.client.get_collection(name=collection_name)
                logging.info(f"Retrieved existing collection: {collection_name}")
                
            except Exception:
                # Create new collection if it doesn't exist
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"notebook_id": notebook_id, "created_at": datetime.now().isoformat()}
                )
                logging.info(f"Created new collection: {collection_name}")
            
            self.collections[collection_name] = collection
            span.set_attribute("output.value", json.dumps(collection))
            return collection
    
    def add_document_chunks(self, notebook_id: str, source_id: str, chunks: List[Dict]) -> bool:
        with tracer.start_as_current_span("add_document_chunks") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id, "source_id": source_id, "chunks": chunks}))
            """
            Add document chunks to the vector store
            
            Args:
                notebook_id: ID of the notebook
                source_id: ID of the source document
                chunks: List of text chunks with metadata
                
            Returns:
                bool: Success status
            """
            try:
                if not self.embedding_model:
                    raise Exception("Embedding model not available")
                
                collection = self.get_or_create_collection(notebook_id)
                
                # Prepare data for insertion
                texts = []
                metadatas = []
                ids = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{source_id}_chunk_{i}"
                    
                    texts.append(chunk['text'])
                    metadatas.append({
                        'source_id': source_id,
                        'chunk_index': i,
                        'start_word': chunk.get('start_word', 0),
                        'end_word': chunk.get('end_word', 0),
                        'word_count': chunk.get('word_count', 0),
                        'character_count': chunk.get('character_count', 0),
                        'created_at': datetime.now().isoformat()
                    })
                    ids.append(chunk_id)
                
                # Generate embeddings
                embeddings = self.embedding_model.encode(texts).tolist()
                
                # Add to collection
                collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logging.info(f"Added {len(chunks)} chunks for source {source_id} to collection {notebook_id}")
                span.set_attribute("output.value", json.dumps(True))
                return True
                
            except Exception as e:
                logging.error(f"Error adding document chunks: {e}")
                span.set_attribute("output.value", json.dumps(False))
                return False
    
    def search_similar_chunks(self, notebook_id: str, query: str, n_results: int = 10, 
                            source_ids: Optional[List[str]] = None) -> List[Dict]:
        with tracer.start_as_current_span("search_similar_chunks") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.RETRIEVER.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id, "query": query, "n_results": n_results, "source_ids": source_ids}))
            """
            Search for similar chunks in the vector store
            
            Args:
                notebook_id: ID of the notebook to search in
                query: Search query text
                n_results: Number of results to return
                source_ids: Optional list of source IDs to filter by
                
            Returns:
                List of similar chunks with metadata and scores
            """
            try:
                if not self.embedding_model:
                    raise Exception("Embedding model not available")
                
                collection = self.get_or_create_collection(notebook_id)
                
                # Generate query embedding
                query_embedding = self.embedding_model.encode([query]).tolist()[0]
                
                # Prepare where clause for filtering
                where_clause = None
                if source_ids:
                    where_clause = {"source_id": {"$in": source_ids}}
                
                # Search in collection
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_clause,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Format results
                formatted_results = []
                if results['documents'] and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        formatted_results.append({
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                            'distance': results['distances'][0][i]
                        })
                
                logging.info(f"Found {len(formatted_results)} similar chunks for query in notebook {notebook_id}")
                span.set_attribute("output.value", json.dumps(formatted_results))
                return formatted_results
                
            except Exception as e:
                logging.error(f"Error searching similar chunks: {e}")
                return []
    
    def delete_source_chunks(self, notebook_id: str, source_id: str) -> bool:
        with tracer.start_as_current_span("delete_source_chunks") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id, "source_id": source_id}))
            """
            Delete all chunks for a specific source
            
            Args:
                notebook_id: ID of the notebook
                source_id: ID of the source to delete
                
            Returns:
                bool: Success status
            """
            try:
                collection = self.get_or_create_collection(notebook_id)
                
                # Get all chunk IDs for this source
                results = collection.get(
                    where={"source_id": source_id},
                    include=['documents']
                )
                
                if results['ids']:
                    collection.delete(ids=results['ids'])
                    logging.info(f"Deleted {len(results['ids'])} chunks for source {source_id}")
                span.set_attribute("output.value", json.dumps(True))
                return True
                
            except Exception as e:
                logging.error(f"Error deleting source chunks: {e}")
                span.set_attribute("output.value", json.dumps(False))
                return False
    
    def delete_notebook_collection(self, notebook_id: str) -> bool:
        with tracer.start_as_current_span("delete_notebook_collection") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
            """
            Delete entire collection for a notebook
            
            Args:
                notebook_id: ID of the notebook
                
            Returns:
                bool: Success status
            """
            try:
                collection_name = f"notebook_{notebook_id}"
                
                # Remove from cache
                if collection_name in self.collections:
                    del self.collections[collection_name]
                
                # Delete from ChromaDB
                self.client.delete_collection(name=collection_name)
                
                logging.info(f"Deleted collection for notebook {notebook_id}")
                span.set_attribute("output.value", json.dumps(True))
                return True
                
            except Exception as e:
                logging.error(f"Error deleting notebook collection: {e}")
                span.set_attribute("output.value", json.dumps(False))
                return False
    
    def get_collection_stats(self, notebook_id: str) -> Dict:
        with tracer.start_as_current_span("get_collection_stats") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
            """
            Get statistics about a collection
            
            Args:
                notebook_id: ID of the notebook
                
            Returns:
                Dict with collection statistics
            """
            try:
                collection = self.get_or_create_collection(notebook_id)
                
                # Get collection count
                count = collection.count()
                
                # Get sample of documents to analyze
                sample_results = collection.peek(limit=100)
                
                # Analyze sources
                source_counts = {}
                if sample_results['metadatas']:
                    for metadata in sample_results['metadatas']:
                        source_id = metadata.get('source_id', 'unknown')
                        source_counts[source_id] = source_counts.get(source_id, 0) + 1
                
                span.set_attribute("output.value", json.dumps({
                    'total_chunks': count,
                    'sources_count': len(source_counts),
                    'source_distribution': source_counts,
                    'collection_name': f"notebook_{notebook_id}",
                    'embedding_dimension': 384  # MiniLM-L6-v2 dimension
                }))

                return {
                    'total_chunks': count,
                    'sources_count': len(source_counts),
                    'source_distribution': source_counts,
                    'collection_name': f"notebook_{notebook_id}",
                    'embedding_dimension': 384  # MiniLM-L6-v2 dimension
                }
                
            except Exception as e:
                logging.error(f"Error getting collection stats: {e}")
                return {}
    
    def hybrid_search(self, notebook_id: str, query: str, n_results: int = 10,
                     source_ids: Optional[List[str]] = None, 
                     keyword_weight: float = 0.3) -> List[Dict]:
        with tracer.start_as_current_span("hybrid_search") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.RETRIEVER.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id, "query": query, "n_results": n_results, "source_ids": source_ids, "keyword_weight": keyword_weight}))
            """
            Perform hybrid search combining semantic similarity and keyword matching
            
            Args:
                notebook_id: ID of the notebook to search in
                query: Search query text
                n_results: Number of results to return
                source_ids: Optional list of source IDs to filter by
                keyword_weight: Weight for keyword matching (0.0 to 1.0)
                
            Returns:
                List of results with combined scores
            """
            try:
                # Get semantic search results
                semantic_results = self.search_similar_chunks(
                    notebook_id, query, n_results * 2, source_ids
                )
                
                # Simple keyword matching for hybrid approach
                query_words = set(query.lower().split())
                
                # Calculate hybrid scores
                for result in semantic_results:
                    text_words = set(result['text'].lower().split())
                    keyword_overlap = len(query_words.intersection(text_words)) / len(query_words)
                    
                    # Combine semantic and keyword scores
                    semantic_score = result['similarity_score']
                    hybrid_score = (1 - keyword_weight) * semantic_score + keyword_weight * keyword_overlap
                    
                    result['hybrid_score'] = hybrid_score
                    result['keyword_score'] = keyword_overlap
                
                # Sort by hybrid score and return top results
                hybrid_results = sorted(semantic_results, key=lambda x: x['hybrid_score'], reverse=True)
                span.set_attribute("output.value", json.dumps(hybrid_results))
                return hybrid_results[:n_results]
                
            except Exception as e:
                logging.error(f"Error in hybrid search: {e}")
                return self.search_similar_chunks(notebook_id, query, n_results, source_ids)
    
    def update_chunk_metadata(self, notebook_id: str, chunk_id: str, metadata: Dict) -> bool:
        with tracer.start_as_current_span("update_chunk_metadata") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id, "chunk_id": chunk_id, "metadata": metadata}))
            """
            Update metadata for a specific chunk
            
            Args:
                notebook_id: ID of the notebook
                chunk_id: ID of the chunk
                metadata: New metadata to update
                
            Returns:
                bool: Success status
            """
            try:
                collection = self.get_or_create_collection(notebook_id)
                
                # Update metadata
                collection.update(
                    ids=[chunk_id],
                    metadatas=[metadata]
                )
                
                logging.info(f"Updated metadata for chunk {chunk_id}")
                span.set_attribute("output.value", json.dumps(True))
                return True
                
            except Exception as e:
                logging.error(f"Error updating chunk metadata: {e}")
                span.set_attribute("output.value", json.dumps(False))
                return False
    
    def get_health_status(self) -> Dict:
        with tracer.start_as_current_span("get_health_status") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            """
            Get health status of the vector store
            
            Returns:
                Dict with health information
            """
            try:
                # Test basic functionality
                test_collection = "health_check"
                
                # Try to create and delete a test collection
                try:
                    collection = self.client.create_collection(name=test_collection)
                    self.client.delete_collection(name=test_collection)
                    chromadb_status = "healthy"
                except Exception:
                    chromadb_status = "error"
                
                # Check embedding model
                embedding_status = "healthy" if self.embedding_model else "error"
                
                span.set_attribute("output.value", json.dumps({
                    'chromadb_status': chromadb_status,
                    'embedding_model_status': embedding_status,
                    'persist_directory': self.persist_directory,
                    'collections_count': len(self.collections),
                    'timestamp': datetime.now().isoformat()
                }))
                return {
                    'chromadb_status': chromadb_status,
                    'embedding_model_status': embedding_status,
                    'persist_directory': self.persist_directory,
                    'collections_count': len(self.collections),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

