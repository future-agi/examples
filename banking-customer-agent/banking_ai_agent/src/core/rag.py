"""
RAG (Retrieval-Augmented Generation) System - Banking Knowledge Base
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer

@dataclass
class RetrievalResult:
    """Result from RAG retrieval"""
    documents: List[Dict[str, Any]]
    sources: List[str]
    relevance_scores: List[float]
    total_documents: int
    query_embedding: Optional[List[float]] = None

class RAGSystem:
    """
    Advanced RAG system for banking knowledge retrieval and augmentation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('RAGSystem')
        
        # Configuration
        self.persist_directory = config.get('chroma_persist_directory', './data/chroma_db')
        self.collection_name = config.get('collection_name', 'banking_knowledge')
        self.embedding_model_name = config.get('embedding_model', 'text-embedding-ada-002')
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.max_retrieval_docs = config.get('max_retrieval_docs', 10)
        
        # Initialize components
        self._init_vector_database()
        self._init_embeddings()
        self._init_text_splitter()
        
        # Load banking knowledge base (will be called separately)
        self.knowledge_loaded = False
        
    def _init_vector_database(self):
        """Initialize ChromaDB vector database"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                self.logger.info(f"Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Banking knowledge base for AI agent"}
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"Error initializing vector database: {str(e)}")
            raise
    
    def _init_embeddings(self):
        """Initialize embedding models"""
        try:
            # OpenAI embeddings for primary use
            self.openai_embeddings = OpenAIEmbeddings(
                model=self.embedding_model_name,
                openai_api_key=self.config.get('openai_api_key')
            )
            
            # Fallback sentence transformer for offline use
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            self.logger.info("Embedding models initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def _init_text_splitter(self):
        """Initialize text splitter for document chunking"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def _load_banking_knowledge(self):
        """Load banking knowledge base into vector database"""
        try:
            # Check if knowledge base is already loaded
            collection_count = self.collection.count()
            if collection_count > 0:
                self.logger.info(f"Knowledge base already loaded with {collection_count} documents")
                return
            
            # Banking knowledge documents
            banking_documents = self._create_banking_knowledge_base()
            
            # Process and store documents
            await self._ingest_documents(banking_documents)
            
            self.logger.info(f"Banking knowledge base loaded with {len(banking_documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Error loading banking knowledge: {str(e)}")
    
    def _create_banking_knowledge_base(self) -> List[Document]:
        """Create comprehensive banking knowledge base"""
        documents = []
        
        # Account Management Knowledge
        account_docs = [
            Document(
                page_content="""
                Account Types and Features:
                
                Checking Accounts:
                - Primary transaction account for daily banking
                - Features: Debit card access, online banking, mobile deposits
                - Fees: Monthly maintenance, overdraft, ATM fees
                - Minimum balance requirements vary by account type
                
                Savings Accounts:
                - Interest-bearing accounts for saving money
                - Higher interest rates than checking accounts
                - Limited monthly transactions (Regulation D)
                - FDIC insured up to $250,000 per depositor
                
                Money Market Accounts:
                - Higher interest rates with higher minimum balances
                - Limited check-writing privileges
                - Tiered interest rates based on balance
                - FDIC insured protection
                """,
                metadata={"category": "account_management", "topic": "account_types"}
            ),
            Document(
                page_content="""
                Account Opening Process:
                
                Required Documentation:
                - Government-issued photo ID (driver's license, passport)
                - Social Security number or ITIN
                - Proof of address (utility bill, lease agreement)
                - Initial deposit amount
                
                KYC (Know Your Customer) Requirements:
                - Identity verification through multiple sources
                - Address verification
                - Background screening for risk assessment
                - Beneficial ownership identification for business accounts
                
                Account Setup Steps:
                1. Document collection and verification
                2. Credit and background checks
                3. Account type selection and features
                4. Initial deposit and funding
                5. Debit card and online banking setup
                """,
                metadata={"category": "account_management", "topic": "account_opening"}
            )
        ]
        
        # Transaction and Payment Knowledge
        transaction_docs = [
            Document(
                page_content="""
                Transaction Types and Processing:
                
                ACH Transfers:
                - Automated Clearing House electronic transfers
                - Processing time: 1-3 business days
                - Lower fees compared to wire transfers
                - Used for direct deposits, bill payments, recurring transfers
                
                Wire Transfers:
                - Real-time electronic fund transfers
                - Same-day processing for domestic wires
                - Higher fees but immediate settlement
                - Requires recipient bank routing and account information
                
                Mobile and Online Transfers:
                - Instant transfers between own accounts
                - External transfers to other banks (1-3 days)
                - Daily and monthly transfer limits apply
                - Enhanced security with multi-factor authentication
                """,
                metadata={"category": "transactions", "topic": "transfer_types"}
            ),
            Document(
                page_content="""
                Payment Processing and Security:
                
                Debit Card Transactions:
                - Real-time account debiting
                - PIN or signature verification
                - Daily spending and ATM withdrawal limits
                - Fraud monitoring and alerts
                
                Bill Pay Services:
                - Scheduled and recurring payments
                - Electronic or check payments to payees
                - Payment confirmation and tracking
                - Cut-off times for same-day processing
                
                Mobile Payment Integration:
                - Apple Pay, Google Pay, Samsung Pay support
                - Tokenization for enhanced security
                - Contactless payment capabilities
                - Transaction notifications and controls
                """,
                metadata={"category": "transactions", "topic": "payment_processing"}
            )
        ]
        
        # Lending and Credit Knowledge
        lending_docs = [
            Document(
                page_content="""
                Personal Loan Products:
                
                Unsecured Personal Loans:
                - No collateral required
                - Fixed interest rates and terms
                - Loan amounts: $1,000 to $100,000
                - Terms: 2-7 years typically
                - Credit score requirements: 600+ for approval
                
                Secured Personal Loans:
                - Collateral required (savings, CD, vehicle)
                - Lower interest rates than unsecured
                - Higher approval rates
                - Risk of collateral loss if defaulted
                
                Application Process:
                - Credit application and authorization
                - Income and employment verification
                - Debt-to-income ratio assessment
                - Credit history and score evaluation
                - Loan approval and funding timeline
                """,
                metadata={"category": "lending", "topic": "personal_loans"}
            ),
            Document(
                page_content="""
                Credit Card Products and Features:
                
                Credit Card Types:
                - Rewards cards (cash back, points, miles)
                - Low interest rate cards
                - Balance transfer cards
                - Secured credit cards for building credit
                - Business credit cards
                
                Credit Card Terms:
                - Annual Percentage Rate (APR)
                - Annual fees and other charges
                - Credit limits and utilization
                - Grace periods for purchases
                - Penalty rates and fees
                
                Credit Building:
                - Payment history (35% of credit score)
                - Credit utilization ratio (30% of score)
                - Length of credit history (15% of score)
                - Credit mix and new accounts
                - Responsible usage recommendations
                """,
                metadata={"category": "lending", "topic": "credit_cards"}
            )
        ]
        
        # Compliance and Security Knowledge
        compliance_docs = [
            Document(
                page_content="""
                Banking Regulations and Compliance:
                
                Bank Secrecy Act (BSA):
                - Currency Transaction Reports (CTR) for $10,000+ cash transactions
                - Suspicious Activity Reports (SAR) for unusual activities
                - Customer identification and verification requirements
                - Record keeping and reporting obligations
                
                Anti-Money Laundering (AML):
                - Customer due diligence procedures
                - Enhanced due diligence for high-risk customers
                - Ongoing monitoring of customer activities
                - Training and compliance program requirements
                
                Know Your Customer (KYC):
                - Identity verification at account opening
                - Beneficial ownership identification
                - Risk assessment and customer profiling
                - Ongoing customer information updates
                """,
                metadata={"category": "compliance", "topic": "regulations"}
            ),
            Document(
                page_content="""
                Fraud Prevention and Security:
                
                Fraud Detection Systems:
                - Real-time transaction monitoring
                - Machine learning algorithms for pattern recognition
                - Velocity checks and spending pattern analysis
                - Geographic and merchant category monitoring
                
                Customer Security Measures:
                - Multi-factor authentication
                - Account alerts and notifications
                - Secure login procedures
                - Regular password updates
                - Phishing and scam awareness
                
                Data Protection:
                - Encryption of sensitive data
                - Secure transmission protocols
                - Access controls and audit trails
                - GDPR and CCPA compliance measures
                - Incident response procedures
                """,
                metadata={"category": "security", "topic": "fraud_prevention"}
            )
        ]
        
        # Investment and Wealth Management Knowledge
        investment_docs = [
            Document(
                page_content="""
                Investment Products and Services:
                
                Certificates of Deposit (CDs):
                - Fixed-term deposits with guaranteed returns
                - Terms from 3 months to 5 years
                - Higher interest rates than savings accounts
                - Early withdrawal penalties apply
                - FDIC insured up to $250,000
                
                Investment Accounts:
                - Brokerage accounts for stocks, bonds, ETFs
                - Retirement accounts (IRA, 401k rollovers)
                - Mutual funds and managed portfolios
                - Investment advisory services
                - Risk tolerance assessment
                
                Wealth Management Services:
                - Financial planning and goal setting
                - Portfolio management and rebalancing
                - Tax-efficient investment strategies
                - Estate planning coordination
                - Regular portfolio reviews and adjustments
                """,
                metadata={"category": "investments", "topic": "products_services"}
            )
        ]
        
        # Customer Service Knowledge
        service_docs = [
            Document(
                page_content="""
                Customer Service Standards and Procedures:
                
                Service Excellence Principles:
                - Professional and courteous communication
                - Active listening and empathy
                - Timely response and resolution
                - Clear explanations of banking products
                - Proactive problem-solving approach
                
                Common Customer Issues:
                - Account access and login problems
                - Transaction disputes and errors
                - Fee inquiries and reversals
                - Card replacement and activation
                - Address and contact information updates
                
                Escalation Procedures:
                - Complex issues requiring specialist knowledge
                - Regulatory compliance concerns
                - Customer complaints and feedback
                - Technical system issues
                - Fraud and security incidents
                """,
                metadata={"category": "customer_service", "topic": "standards"}
            )
        ]
        
        # Combine all documents
        documents.extend(account_docs)
        documents.extend(transaction_docs)
        documents.extend(lending_docs)
        documents.extend(compliance_docs)
        documents.extend(investment_docs)
        documents.extend(service_docs)
        
        return documents
    
    async def _ingest_documents(self, documents: List[Document]):
        """Ingest documents into vector database"""
        try:
            # Split documents into chunks
            all_chunks = []
            for doc in documents:
                chunks = self.text_splitter.split_documents([doc])
                all_chunks.extend(chunks)
            
            # Generate embeddings and store in batches
            batch_size = 50
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                await self._store_document_batch(batch)
            
            self.logger.info(f"Ingested {len(all_chunks)} document chunks")
            
        except Exception as e:
            self.logger.error(f"Error ingesting documents: {str(e)}")
            raise
    
    async def _store_document_batch(self, documents: List[Document]):
        """Store a batch of documents in vector database"""
        try:
            # Prepare document data
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(texts)
            
            # Create unique IDs
            ids = [f"doc_{i}_{hash(text)}" for i, text in enumerate(texts)]
            
            # Store in ChromaDB
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
        except Exception as e:
            self.logger.error(f"Error storing document batch: {str(e)}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        try:
            # Try OpenAI embeddings first
            embeddings = await self.openai_embeddings.aembed_documents(texts)
            return embeddings
            
        except Exception as e:
            self.logger.warning(f"OpenAI embeddings failed, using fallback: {str(e)}")
            # Fallback to sentence transformer
            embeddings = self.sentence_transformer.encode(texts)
            return embeddings.tolist()
    
    async def retrieve_context(self, query: str, plan: Any = None) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query using RAG
        """
        try:
            self.logger.info(f"Retrieving context for query: {query[:100]}...")
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Determine number of documents to retrieve
            n_results = self.max_retrieval_docs
            if plan and hasattr(plan, 'complexity_score'):
                # Retrieve more documents for complex queries
                if plan.complexity_score > 7:
                    n_results = min(15, self.max_retrieval_docs * 2)
            
            # Query vector database
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process results
            documents = []
            sources = []
            relevance_scores = []
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to relevance score (lower distance = higher relevance)
                    relevance_score = max(0, 1 - distance)
                    
                    documents.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': relevance_score,
                        'rank': i + 1
                    })
                    
                    sources.append(f"{metadata.get('category', 'unknown')}:{metadata.get('topic', 'general')}")
                    relevance_scores.append(relevance_score)
            
            # Create retrieval result
            retrieval_result = RetrievalResult(
                documents=documents,
                sources=list(set(sources)),  # Remove duplicates
                relevance_scores=relevance_scores,
                total_documents=len(documents),
                query_embedding=query_embedding[0] if query_embedding else None
            )
            
            self.logger.info(f"Retrieved {len(documents)} relevant documents")
            
            return {
                'documents': documents,
                'sources': sources,
                'total_retrieved': len(documents),
                'avg_relevance': sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return {
                'documents': [],
                'sources': [],
                'total_retrieved': 0,
                'avg_relevance': 0,
                'error': str(e)
            }
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a new document to the knowledge base"""
        try:
            # Create document
            doc = Document(page_content=content, metadata=metadata)
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Store chunks
            await self._store_document_batch(chunks)
            
            doc_id = f"custom_{hash(content)}"
            self.logger.info(f"Added document {doc_id} with {len(chunks)} chunks")
            
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Error adding document: {str(e)}")
            raise
    
    async def search_similar(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents with optional category filtering"""
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Prepare where clause for category filtering
            where_clause = None
            if category:
                where_clause = {"category": category}
            
            # Query with filtering
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=limit,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process results
            similar_docs = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    similar_docs.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': max(0, 1 - distance)
                    })
            
            return similar_docs
            
        except Exception as e:
            self.logger.error(f"Error searching similar documents: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base collection"""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to understand categories
            sample_results = self.collection.get(limit=100, include=['metadatas'])
            categories = set()
            topics = set()
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if 'category' in metadata:
                        categories.add(metadata['category'])
                    if 'topic' in metadata:
                        topics.add(metadata['topic'])
            
            return {
                'total_documents': count,
                'categories': list(categories),
                'topics': list(topics),
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get RAG system status"""
        try:
            stats = self.get_collection_stats()
            
            return {
                "module": "rag",
                "status": "healthy",
                "knowledge_base": stats,
                "configuration": {
                    "embedding_model": self.embedding_model_name,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "max_retrieval_docs": self.max_retrieval_docs
                },
                "capabilities": [
                    "document_retrieval",
                    "semantic_search",
                    "context_augmentation",
                    "knowledge_base_management",
                    "similarity_matching"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting RAG status: {str(e)}")
            return {
                "module": "rag",
                "status": "error",
                "error": str(e)
            }

