"""
Knowledge Management and RAG System for the Multi-Agent AI Trading System
"""
import asyncio
import json
import pickle
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
import numpy as np
from pathlib import Path
import sqlite3
import threading

from src.integrations.openai.client import OpenAIClient, ModelType
from src.utils.logging import get_component_logger

logger = get_component_logger("knowledge_base")


@dataclass
class KnowledgeDocument:
    """Knowledge document structure"""
    id: str
    title: str
    content: str
    document_type: str  # 'financial_report', 'research', 'news', 'regulation', 'strategy'
    source: str
    symbols: List[str]  # Related stock symbols
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeDocument':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class SearchResult:
    """Search result with relevance score"""
    document: KnowledgeDocument
    relevance_score: float
    matched_content: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "relevance_score": self.relevance_score,
            "matched_content": self.matched_content
        }


class EmbeddingManager:
    """Manages document embeddings using OpenAI"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.embedding_model = "text-embedding-3-small"
        self.embedding_cache = {}
        self.cache_lock = threading.Lock()
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        try:
            # Check cache first
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            with self.cache_lock:
                if text_hash in self.embedding_cache:
                    return self.embedding_cache[text_hash]
            
            # Get embedding from OpenAI
            response = await self.openai_client.create_embedding(
                input=text,
                model=self.embedding_model
            )
            
            if response and 'data' in response and response['data']:
                embedding = response['data'][0]['embedding']
                
                # Cache the embedding
                with self.cache_lock:
                    self.embedding_cache[text_hash] = embedding
                
                return embedding
            else:
                logger.error(f"Invalid embedding response: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        embeddings = []
        
        # Process in batches to avoid rate limits
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                embedding = await self.get_embedding(text)
                batch_embeddings.append(embedding)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0


class KnowledgeStorage:
    """SQLite-based knowledge storage"""
    
    def __init__(self, db_path: str = "data/knowledge.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    symbols TEXT,  -- JSON array
                    tags TEXT,     -- JSON array
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    embedding BLOB,  -- Pickled embedding
                    metadata TEXT    -- JSON metadata
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_type ON documents(document_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbols ON documents(symbols)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at)
            """)
            
            conn.commit()
    
    def store_document(self, document: KnowledgeDocument) -> bool:
        """Store a document in the knowledge base"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Serialize complex fields
                    symbols_json = json.dumps(document.symbols)
                    tags_json = json.dumps(document.tags)
                    metadata_json = json.dumps(document.metadata) if document.metadata else None
                    embedding_blob = pickle.dumps(document.embedding) if document.embedding else None
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO documents 
                        (id, title, content, document_type, source, symbols, tags, 
                         created_at, updated_at, embedding, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        document.id, document.title, document.content, document.document_type,
                        document.source, symbols_json, tags_json,
                        document.created_at.isoformat(), document.updated_at.isoformat(),
                        embedding_blob, metadata_json
                    ))
                    
                    conn.commit()
            
            logger.info(f"Stored document: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing document {document.id}: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve a document by ID"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT * FROM documents WHERE id = ?", (document_id,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        return self._row_to_document(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    def search_documents(self, query: str = None, document_type: str = None,
                        symbols: List[str] = None, tags: List[str] = None,
                        limit: int = 100) -> List[KnowledgeDocument]:
        """Search documents with filters"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    sql = "SELECT * FROM documents WHERE 1=1"
                    params = []
                    
                    if query:
                        sql += " AND (title LIKE ? OR content LIKE ?)"
                        params.extend([f"%{query}%", f"%{query}%"])
                    
                    if document_type:
                        sql += " AND document_type = ?"
                        params.append(document_type)
                    
                    if symbols:
                        for symbol in symbols:
                            sql += " AND symbols LIKE ?"
                            params.append(f"%{symbol}%")
                    
                    if tags:
                        for tag in tags:
                            sql += " AND tags LIKE ?"
                            params.append(f"%{tag}%")
                    
                    sql += " ORDER BY updated_at DESC LIMIT ?"
                    params.append(limit)
                    
                    cursor = conn.execute(sql, params)
                    rows = cursor.fetchall()
                    
                    return [self._row_to_document(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_all_documents(self) -> List[KnowledgeDocument]:
        """Get all documents"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT * FROM documents ORDER BY updated_at DESC")
                    rows = cursor.fetchall()
                    
                    return [self._row_to_document(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                    conn.commit()
            
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def _row_to_document(self, row) -> KnowledgeDocument:
        """Convert database row to KnowledgeDocument"""
        (id, title, content, document_type, source, symbols_json, tags_json,
         created_at, updated_at, embedding_blob, metadata_json) = row
        
        symbols = json.loads(symbols_json) if symbols_json else []
        tags = json.loads(tags_json) if tags_json else []
        metadata = json.loads(metadata_json) if metadata_json else None
        embedding = pickle.loads(embedding_blob) if embedding_blob else None
        
        return KnowledgeDocument(
            id=id,
            title=title,
            content=content,
            document_type=document_type,
            source=source,
            symbols=symbols,
            tags=tags,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
            embedding=embedding,
            metadata=metadata
        )


class RAGSystem:
    """Retrieval-Augmented Generation system"""
    
    def __init__(self, openai_client: OpenAIClient, storage: KnowledgeStorage):
        self.openai_client = openai_client
        self.storage = storage
        self.embedding_manager = EmbeddingManager(openai_client)
        
        # RAG configuration
        self.max_context_length = 8000  # Max tokens for context
        self.similarity_threshold = 0.7
        self.max_retrieved_docs = 5
        
    async def add_document(self, title: str, content: str, document_type: str,
                          source: str, symbols: List[str] = None, 
                          tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Add a document to the knowledge base"""
        try:
            # Generate document ID
            doc_id = hashlib.md5(f"{title}{source}".encode()).hexdigest()
            
            # Get embedding for content
            embedding = await self.embedding_manager.get_embedding(content)
            
            # Create document
            document = KnowledgeDocument(
                id=doc_id,
                title=title,
                content=content,
                document_type=document_type,
                source=source,
                symbols=symbols or [],
                tags=tags or [],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                embedding=embedding,
                metadata=metadata
            )
            
            # Store document
            success = self.storage.store_document(document)
            
            if success:
                logger.info(f"Added document to knowledge base: {title}")
                return doc_id
            else:
                logger.error(f"Failed to store document: {title}")
                return ""
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return ""
    
    async def search_similar_documents(self, query: str, symbols: List[str] = None,
                                     document_types: List[str] = None) -> List[SearchResult]:
        """Search for documents similar to the query"""
        try:
            # Get query embedding
            query_embedding = await self.embedding_manager.get_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to get query embedding")
                return []
            
            # Get candidate documents
            candidates = self.storage.search_documents(
                symbols=symbols,
                limit=100  # Get more candidates for similarity filtering
            )
            
            # Filter by document type if specified
            if document_types:
                candidates = [doc for doc in candidates if doc.document_type in document_types]
            
            # Calculate similarities
            search_results = []
            
            for doc in candidates:
                if not doc.embedding:
                    continue
                
                similarity = self.embedding_manager.calculate_similarity(
                    query_embedding, doc.embedding
                )
                
                if similarity >= self.similarity_threshold:
                    # Extract relevant content snippet
                    matched_content = self._extract_relevant_content(doc.content, query)
                    
                    search_results.append(SearchResult(
                        document=doc,
                        relevance_score=similarity,
                        matched_content=matched_content
                    ))
            
            # Sort by relevance score
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Return top results
            return search_results[:self.max_retrieved_docs]
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    async def generate_with_context(self, query: str, symbols: List[str] = None,
                                  document_types: List[str] = None) -> Dict[str, Any]:
        """Generate response using retrieved context"""
        try:
            # Retrieve relevant documents
            search_results = await self.search_similar_documents(
                query, symbols, document_types
            )
            
            if not search_results:
                # No relevant context found, generate without RAG
                response = await self.openai_client.create_chat_completion(
                    messages=[{"role": "user", "content": query}],
                    model=ModelType.GPT_4_TURBO
                )
                
                return {
                    "response": response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "sources": [],
                    "context_used": False
                }
            
            # Build context from retrieved documents
            context = self._build_context(search_results)
            
            # Create enhanced prompt
            enhanced_prompt = f"""Based on the following context information, please answer the question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, please indicate what additional information would be helpful."""
            
            # Generate response
            response = await self.openai_client.create_chat_completion(
                messages=[{"role": "user", "content": enhanced_prompt}],
                model=ModelType.GPT_4_TURBO
            )
            
            # Extract sources
            sources = [
                {
                    "title": result.document.title,
                    "source": result.document.source,
                    "relevance_score": result.relevance_score,
                    "document_type": result.document.document_type
                }
                for result in search_results
            ]
            
            return {
                "response": response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "sources": sources,
                "context_used": True,
                "retrieved_documents": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Error generating with context: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your request.",
                "sources": [],
                "context_used": False,
                "error": str(e)
            }
    
    def _extract_relevant_content(self, content: str, query: str, max_length: int = 500) -> str:
        """Extract relevant content snippet"""
        # Simple extraction - find sentences containing query terms
        query_terms = query.lower().split()
        sentences = content.split('.')
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(term in sentence_lower for term in query_terms):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            snippet = '. '.join(relevant_sentences[:3])  # Take first 3 relevant sentences
            if len(snippet) > max_length:
                snippet = snippet[:max_length] + "..."
            return snippet
        else:
            # Return first part of content if no specific match
            return content[:max_length] + "..." if len(content) > max_length else content
    
    def _build_context(self, search_results: List[SearchResult]) -> str:
        """Build context string from search results"""
        context_parts = []
        total_length = 0
        
        for result in search_results:
            doc = result.document
            
            # Create context entry
            context_entry = f"""
Document: {doc.title}
Source: {doc.source}
Type: {doc.document_type}
Content: {result.matched_content}
---
"""
            
            # Check if adding this would exceed context length
            if total_length + len(context_entry) > self.max_context_length:
                break
            
            context_parts.append(context_entry)
            total_length += len(context_entry)
        
        return '\n'.join(context_parts)
    
    async def update_document_embeddings(self):
        """Update embeddings for documents that don't have them"""
        try:
            documents = self.storage.get_all_documents()
            
            documents_to_update = [doc for doc in documents if not doc.embedding]
            
            if not documents_to_update:
                logger.info("All documents already have embeddings")
                return
            
            logger.info(f"Updating embeddings for {len(documents_to_update)} documents")
            
            for doc in documents_to_update:
                embedding = await self.embedding_manager.get_embedding(doc.content)
                
                if embedding:
                    doc.embedding = embedding
                    doc.updated_at = datetime.now(timezone.utc)
                    self.storage.store_document(doc)
                    
                    logger.info(f"Updated embedding for document: {doc.title}")
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
            
            logger.info("Finished updating document embeddings")
            
        except Exception as e:
            logger.error(f"Error updating document embeddings: {e}")


class KnowledgeManager:
    """Main knowledge management system"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.storage = KnowledgeStorage()
        self.rag_system = RAGSystem(openai_client, self.storage)
        
        logger.info("Knowledge Manager initialized")
    
    async def initialize_default_knowledge(self):
        """Initialize with default financial knowledge"""
        try:
            # Add some default financial knowledge documents
            default_docs = [
                {
                    "title": "Technical Analysis Fundamentals",
                    "content": """Technical analysis is the study of price movements and trading volume to predict future price movements. Key concepts include:

1. Support and Resistance Levels: Price levels where stocks tend to find buying (support) or selling (resistance) pressure.

2. Moving Averages: Trend-following indicators that smooth out price data. Common types include Simple Moving Average (SMA) and Exponential Moving Average (EMA).

3. Relative Strength Index (RSI): A momentum oscillator that measures the speed and magnitude of price changes, ranging from 0 to 100.

4. MACD (Moving Average Convergence Divergence): A trend-following momentum indicator that shows the relationship between two moving averages.

5. Volume Analysis: Trading volume often confirms price movements. High volume during price increases suggests strong buying interest.

6. Chart Patterns: Formations like head and shoulders, triangles, and flags that can indicate future price direction.""",
                    "document_type": "strategy",
                    "source": "Internal Knowledge Base",
                    "symbols": [],
                    "tags": ["technical_analysis", "indicators", "trading"]
                },
                {
                    "title": "Fundamental Analysis Principles",
                    "content": """Fundamental analysis evaluates a company's intrinsic value by examining financial statements, management quality, competitive position, and economic factors:

1. Financial Ratios:
   - P/E Ratio: Price-to-Earnings ratio indicates valuation relative to earnings
   - P/B Ratio: Price-to-Book ratio compares market value to book value
   - ROE: Return on Equity measures profitability relative to shareholder equity
   - Debt-to-Equity: Indicates financial leverage and risk

2. Income Statement Analysis:
   - Revenue growth trends
   - Profit margins (gross, operating, net)
   - Earnings per share (EPS) growth

3. Balance Sheet Analysis:
   - Asset quality and composition
   - Liability structure
   - Working capital management

4. Cash Flow Analysis:
   - Operating cash flow strength
   - Free cash flow generation
   - Capital allocation efficiency

5. Valuation Methods:
   - Discounted Cash Flow (DCF) modeling
   - Comparable company analysis
   - Asset-based valuation""",
                    "document_type": "strategy",
                    "source": "Internal Knowledge Base",
                    "symbols": [],
                    "tags": ["fundamental_analysis", "valuation", "financial_ratios"]
                },
                {
                    "title": "Risk Management Best Practices",
                    "content": """Effective risk management is crucial for long-term trading success:

1. Position Sizing:
   - Never risk more than 1-2% of portfolio on a single trade
   - Use Kelly Criterion for optimal position sizing
   - Consider volatility when determining position size

2. Diversification:
   - Spread risk across different assets, sectors, and strategies
   - Avoid concentration in correlated positions
   - Consider geographic and currency diversification

3. Stop-Loss Orders:
   - Set stop-losses before entering trades
   - Use technical levels for stop placement
   - Consider volatility-adjusted stops

4. Risk Metrics:
   - Value at Risk (VaR) for portfolio risk assessment
   - Maximum Drawdown monitoring
   - Sharpe Ratio for risk-adjusted returns
   - Beta for market risk exposure

5. Portfolio Management:
   - Regular rebalancing
   - Correlation monitoring
   - Stress testing under various scenarios
   - Liquidity risk assessment

6. Psychological Risk Management:
   - Avoid emotional decision making
   - Stick to predetermined rules
   - Regular performance review and adjustment""",
                    "document_type": "strategy",
                    "source": "Internal Knowledge Base",
                    "symbols": [],
                    "tags": ["risk_management", "portfolio", "position_sizing"]
                }
            ]
            
            for doc_data in default_docs:
                await self.rag_system.add_document(**doc_data)
            
            logger.info("Initialized default knowledge base")
            
        except Exception as e:
            logger.error(f"Error initializing default knowledge: {e}")
    
    async def add_document(self, **kwargs) -> str:
        """Add a document to the knowledge base"""
        return await self.rag_system.add_document(**kwargs)
    
    async def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Search the knowledge base"""
        return await self.rag_system.search_similar_documents(query, **kwargs)
    
    async def generate_with_context(self, query: str, **kwargs) -> Dict[str, Any]:
        """Generate response with retrieved context"""
        return await self.rag_system.generate_with_context(query, **kwargs)
    
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """Get a specific document"""
        return self.storage.get_document(document_id)
    
    def get_all_documents(self) -> List[KnowledgeDocument]:
        """Get all documents"""
        return self.storage.get_all_documents()
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        return self.storage.delete_document(document_id)
    
    async def update_embeddings(self):
        """Update embeddings for all documents"""
        await self.rag_system.update_document_embeddings()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        documents = self.storage.get_all_documents()
        
        doc_types = {}
        total_docs = len(documents)
        docs_with_embeddings = 0
        
        for doc in documents:
            doc_types[doc.document_type] = doc_types.get(doc.document_type, 0) + 1
            if doc.embedding:
                docs_with_embeddings += 1
        
        return {
            "total_documents": total_docs,
            "documents_with_embeddings": docs_with_embeddings,
            "document_types": doc_types,
            "embedding_coverage": docs_with_embeddings / total_docs if total_docs > 0 else 0
        }

