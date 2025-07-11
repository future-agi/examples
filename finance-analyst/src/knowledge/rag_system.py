"""
RAG (Retrieval-Augmented Generation) System
Advanced knowledge retrieval and augmentation for trading insights
"""

import os
import json
import pickle
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeDocument:
    """Represents a knowledge document in the RAG system"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    embedding: Optional[np.ndarray] = None

class TradingKnowledgeBase:
    """
    Comprehensive trading knowledge base with RAG capabilities
    """
    
    def __init__(self, knowledge_dir: str = "data/knowledge"):
        """Initialize the knowledge base"""
        self.knowledge_dir = knowledge_dir
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.document_vectors = None
        self.is_indexed = False
        
        # Ensure knowledge directory exists
        os.makedirs(knowledge_dir, exist_ok=True)
        
        # Initialize with default trading knowledge
        self._initialize_default_knowledge()
        
        # Load existing knowledge if available
        self._load_knowledge_base()
    
    def _initialize_default_knowledge(self):
        """Initialize with comprehensive trading knowledge"""
        default_knowledge = [
            {
                "title": "Technical Analysis Fundamentals",
                "content": """
                Technical analysis is the study of price movements and trading volume to predict future price directions. 
                Key principles include:
                
                1. Price Action: The primary focus is on price movements, which reflect all available information
                2. Trend Analysis: Markets move in trends (uptrend, downtrend, sideways)
                3. Support and Resistance: Price levels where buying or selling pressure emerges
                4. Chart Patterns: Recurring formations that suggest future price movements
                5. Volume Confirmation: Trading volume should confirm price movements
                
                Common Technical Indicators:
                - Moving Averages (SMA, EMA): Trend following indicators
                - RSI (Relative Strength Index): Momentum oscillator (0-100 scale)
                - MACD: Moving Average Convergence Divergence for trend changes
                - Bollinger Bands: Volatility indicator with upper and lower bands
                - Stochastic Oscillator: Momentum indicator comparing closing price to price range
                
                Chart Patterns:
                - Head and Shoulders: Reversal pattern indicating trend change
                - Double Top/Bottom: Reversal patterns at key levels
                - Triangles: Continuation patterns (ascending, descending, symmetrical)
                - Flags and Pennants: Short-term continuation patterns
                - Cup and Handle: Bullish continuation pattern
                """,
                "category": "Technical Analysis",
                "tags": ["technical analysis", "indicators", "chart patterns", "trends"]
            },
            {
                "title": "Fundamental Analysis Deep Dive",
                "content": """
                Fundamental analysis evaluates a company's intrinsic value by examining financial statements, 
                business model, competitive position, and economic factors.
                
                Key Financial Metrics:
                
                Valuation Ratios:
                - P/E Ratio (Price-to-Earnings): Current price divided by earnings per share
                - PEG Ratio: P/E ratio divided by earnings growth rate
                - P/B Ratio (Price-to-Book): Market value divided by book value
                - P/S Ratio (Price-to-Sales): Market cap divided by revenue
                - EV/EBITDA: Enterprise value to earnings before interest, taxes, depreciation, amortization
                
                Profitability Metrics:
                - ROE (Return on Equity): Net income divided by shareholder equity
                - ROA (Return on Assets): Net income divided by total assets
                - Gross Margin: Gross profit divided by revenue
                - Operating Margin: Operating income divided by revenue
                - Net Margin: Net income divided by revenue
                
                Growth Metrics:
                - Revenue Growth: Year-over-year sales increase
                - Earnings Growth: Year-over-year profit increase
                - Free Cash Flow Growth: Operating cash flow minus capital expenditures
                
                Financial Health:
                - Debt-to-Equity Ratio: Total debt divided by shareholder equity
                - Current Ratio: Current assets divided by current liabilities
                - Quick Ratio: (Current assets - inventory) divided by current liabilities
                - Interest Coverage: EBIT divided by interest expense
                
                Qualitative Factors:
                - Management Quality: Track record, vision, execution capability
                - Competitive Advantage: Moats, barriers to entry, market position
                - Industry Trends: Growth prospects, disruption risks, regulatory environment
                - Economic Moats: Brand strength, network effects, cost advantages, switching costs
                """,
                "category": "Fundamental Analysis",
                "tags": ["fundamental analysis", "financial ratios", "valuation", "financial health"]
            },
            {
                "title": "Risk Management Strategies",
                "content": """
                Risk management is the cornerstone of successful investing and trading. It involves identifying, 
                assessing, and controlling potential losses while maximizing returns.
                
                Types of Investment Risk:
                
                1. Market Risk (Systematic Risk):
                - Cannot be diversified away
                - Affects entire market or asset class
                - Examples: Economic recession, interest rate changes, geopolitical events
                - Measured by Beta coefficient
                
                2. Company Risk (Unsystematic Risk):
                - Can be reduced through diversification
                - Specific to individual companies or sectors
                - Examples: Management changes, product failures, competitive threats
                
                3. Liquidity Risk:
                - Difficulty selling an investment quickly without significant price impact
                - More common in small-cap stocks, bonds, real estate
                
                4. Inflation Risk:
                - Purchasing power erosion over time
                - Particularly affects fixed-income investments
                
                Risk Management Techniques:
                
                1. Position Sizing:
                - Never risk more than 1-2% of portfolio on single trade
                - Use Kelly Criterion for optimal position sizing
                - Consider correlation between positions
                
                2. Diversification:
                - Spread investments across different assets, sectors, geographies
                - Correlation analysis to ensure true diversification
                - Rebalancing to maintain target allocations
                
                3. Stop Losses:
                - Predetermined exit points to limit losses
                - Types: Fixed percentage, technical levels, trailing stops
                - Discipline to execute without emotion
                
                4. Hedging:
                - Options strategies to protect positions
                - Inverse ETFs for market hedging
                - Currency hedging for international investments
                
                5. Asset Allocation:
                - Strategic allocation based on risk tolerance and time horizon
                - Tactical adjustments based on market conditions
                - Age-based allocation rules (100 - age = stock percentage)
                
                Portfolio Risk Metrics:
                - Sharpe Ratio: Risk-adjusted returns
                - Maximum Drawdown: Largest peak-to-trough decline
                - Value at Risk (VaR): Potential loss at given confidence level
                - Beta: Sensitivity to market movements
                - Standard Deviation: Volatility measure
                """,
                "category": "Risk Management",
                "tags": ["risk management", "diversification", "position sizing", "stop loss", "hedging"]
            },
            {
                "title": "Investment Strategies and Approaches",
                "content": """
                Different investment strategies suit different goals, risk tolerances, and market conditions.
                
                Long-term Investment Strategies:
                
                1. Buy and Hold:
                - Purchase quality investments and hold for years/decades
                - Benefits from compound growth and reduced transaction costs
                - Requires patience and conviction during market volatility
                - Best for: Retirement accounts, wealth building
                
                2. Value Investing:
                - Buy undervalued companies below intrinsic value
                - Focus on low P/E, P/B ratios, high dividend yields
                - Popularized by Benjamin Graham and Warren Buffett
                - Requires fundamental analysis and patience
                
                3. Growth Investing:
                - Invest in companies with above-average growth potential
                - Focus on revenue/earnings growth, expanding markets
                - Higher valuations justified by growth prospects
                - More volatile but higher return potential
                
                4. Dividend Investing:
                - Focus on companies with consistent dividend payments
                - Provides regular income and potential capital appreciation
                - Look for dividend growth, sustainable payout ratios
                - Good for income-focused investors
                
                5. Index Investing:
                - Passive investment in broad market indices
                - Low costs, instant diversification, market returns
                - Eliminates stock selection risk
                - Suitable for most individual investors
                
                Short-term Trading Strategies:
                
                1. Day Trading:
                - Buy and sell within same trading day
                - Requires significant time, capital, and skill
                - High risk, high potential reward
                - Focus on technical analysis and momentum
                
                2. Swing Trading:
                - Hold positions for days to weeks
                - Capture short-term price swings
                - Combines technical and fundamental analysis
                - Less time-intensive than day trading
                
                3. Momentum Trading:
                - Follow trends and price momentum
                - Buy strength, sell weakness
                - Use moving averages, breakouts, volume
                - Requires strict risk management
                
                4. Contrarian Investing:
                - Go against prevailing market sentiment
                - Buy fear, sell greed
                - Requires strong conviction and timing
                - Can be very profitable but psychologically difficult
                
                Strategy Selection Factors:
                - Time horizon and investment goals
                - Risk tolerance and emotional temperament
                - Available time for research and monitoring
                - Capital requirements and transaction costs
                - Market conditions and economic environment
                - Tax implications and account types
                """,
                "category": "Investment Strategies",
                "tags": ["investment strategies", "buy and hold", "value investing", "growth investing", "trading"]
            },
            {
                "title": "Market Psychology and Behavioral Finance",
                "content": """
                Understanding market psychology and behavioral biases is crucial for successful investing.
                
                Common Behavioral Biases:
                
                1. Confirmation Bias:
                - Seeking information that confirms existing beliefs
                - Ignoring contradictory evidence
                - Solution: Actively seek opposing viewpoints
                
                2. Loss Aversion:
                - Feeling losses more acutely than equivalent gains
                - Leads to holding losers too long, selling winners too early
                - Solution: Set predetermined rules and stick to them
                
                3. Overconfidence:
                - Overestimating one's ability to predict outcomes
                - Leads to excessive trading and risk-taking
                - Solution: Track performance objectively, use systematic approaches
                
                4. Anchoring:
                - Over-relying on first piece of information received
                - Purchase price becomes psychological anchor
                - Solution: Focus on current fundamentals, not past prices
                
                5. Herd Mentality:
                - Following crowd behavior without independent analysis
                - Leads to bubbles and crashes
                - Solution: Contrarian thinking, independent research
                
                6. Recency Bias:
                - Giving more weight to recent events
                - Extrapolating short-term trends indefinitely
                - Solution: Consider long-term historical patterns
                
                Market Cycles and Emotions:
                
                1. Optimism Phase:
                - Rising prices, positive sentiment
                - Increased buying activity
                - Media coverage becomes positive
                
                2. Excitement Phase:
                - Accelerating gains
                - FOMO (Fear of Missing Out) kicks in
                - New investors enter market
                
                3. Euphoria Phase:
                - Peak optimism, "this time is different"
                - Maximum risk-taking
                - Warning signs often ignored
                
                4. Anxiety Phase:
                - First signs of trouble
                - Volatility increases
                - Some investors start to worry
                
                5. Fear Phase:
                - Panic selling begins
                - Media turns negative
                - Rational thinking diminished
                
                6. Desperation Phase:
                - Capitulation, maximum pessimism
                - "I'll never invest again" mentality
                - Often marks market bottom
                
                Overcoming Behavioral Biases:
                
                1. Systematic Approach:
                - Use checklists and predetermined criteria
                - Quantitative analysis over gut feelings
                - Regular portfolio reviews and rebalancing
                
                2. Education and Awareness:
                - Understand common biases and their effects
                - Learn from past mistakes
                - Study market history and cycles
                
                3. Emotional Discipline:
                - Separate emotions from investment decisions
                - Use stop losses and profit targets
                - Take breaks during stressful periods
                
                4. Diversification:
                - Reduces impact of individual mistakes
                - Provides psychological comfort
                - Systematic rebalancing removes emotion
                """,
                "category": "Market Psychology",
                "tags": ["behavioral finance", "market psychology", "biases", "emotions", "market cycles"]
            },
            {
                "title": "Economic Indicators and Market Analysis",
                "content": """
                Economic indicators provide insights into economic health and can influence market direction.
                
                Leading Economic Indicators:
                
                1. Employment Data:
                - Non-farm Payrolls: Monthly job creation/destruction
                - Unemployment Rate: Percentage of workforce unemployed
                - Initial Jobless Claims: Weekly unemployment insurance filings
                - Impact: Strong employment = economic growth = bullish for stocks
                
                2. Manufacturing Data:
                - ISM Manufacturing PMI: Manufacturing sector health
                - Industrial Production: Output of factories, mines, utilities
                - Capacity Utilization: Percentage of productive capacity being used
                - Impact: Strong manufacturing = economic expansion
                
                3. Consumer Data:
                - Consumer Confidence Index: Consumer sentiment about economy
                - Retail Sales: Monthly consumer spending data
                - Personal Income and Spending: Individual financial health
                - Impact: Strong consumer = 70% of GDP = market positive
                
                4. Housing Data:
                - Housing Starts: New residential construction
                - Existing Home Sales: Previously owned home transactions
                - Building Permits: Future construction activity
                - Impact: Housing wealth effect influences consumer spending
                
                Coincident Indicators:
                
                1. Gross Domestic Product (GDP):
                - Total economic output
                - Released quarterly with revisions
                - Growth rate indicates economic expansion/contraction
                
                2. Industrial Production:
                - Real output of manufacturing, mining, utilities
                - Monthly release, closely watched
                - Correlates with overall economic activity
                
                Lagging Indicators:
                
                1. Inflation Measures:
                - Consumer Price Index (CPI): Cost of goods and services
                - Producer Price Index (PPI): Wholesale price changes
                - Core inflation: Excludes volatile food and energy
                - Impact: High inflation = potential Fed tightening = market negative
                
                2. Interest Rates:
                - Federal Funds Rate: Central bank policy rate
                - 10-Year Treasury Yield: Long-term interest rate benchmark
                - Yield Curve: Relationship between short and long rates
                - Impact: Rising rates = higher discount rate = lower valuations
                
                Central Bank Policy:
                
                1. Federal Reserve Tools:
                - Interest Rate Policy: Primary tool for economic influence
                - Quantitative Easing: Bond purchases to inject liquidity
                - Forward Guidance: Communication about future policy
                
                2. Policy Impacts:
                - Accommodative Policy: Lower rates, QE = bullish for risk assets
                - Restrictive Policy: Higher rates, QT = bearish for risk assets
                - Policy Uncertainty: Increases market volatility
                
                Global Economic Factors:
                
                1. Currency Movements:
                - Dollar strength affects multinational earnings
                - Emerging market currency crises
                - Trade-weighted dollar index
                
                2. Commodity Prices:
                - Oil prices affect energy sector and inflation
                - Gold as safe haven and inflation hedge
                - Agricultural commodities and food inflation
                
                3. Geopolitical Events:
                - Trade wars and tariffs
                - Political instability
                - Military conflicts
                - Brexit, elections, policy changes
                
                Market Sector Rotation:
                
                1. Economic Cycle Stages:
                - Early Cycle: Technology, Consumer Discretionary
                - Mid Cycle: Industrials, Materials
                - Late Cycle: Energy, Financials
                - Recession: Utilities, Consumer Staples, Healthcare
                
                2. Interest Rate Environment:
                - Rising Rates: Financials benefit, REITs suffer
                - Falling Rates: Growth stocks outperform, bond proxies rally
                - Flat Curve: Pressure on bank margins
                """,
                "category": "Economic Analysis",
                "tags": ["economic indicators", "GDP", "inflation", "interest rates", "central bank", "sector rotation"]
            }
        ]
        
        # Add default knowledge to the system
        for knowledge in default_knowledge:
            doc_id = self._generate_doc_id(knowledge["title"])
            document = KnowledgeDocument(
                id=doc_id,
                title=knowledge["title"],
                content=knowledge["content"],
                category=knowledge["category"],
                tags=knowledge["tags"],
                metadata={"source": "default", "importance": "high"},
                created_at=datetime.now()
            )
            self.documents[doc_id] = document
    
    def _generate_doc_id(self, title: str) -> str:
        """Generate unique document ID from title"""
        return hashlib.md5(title.encode()).hexdigest()[:12]
    
    def add_document(self, title: str, content: str, category: str, 
                    tags: List[str], metadata: Dict[str, Any] = None) -> str:
        """Add a new document to the knowledge base"""
        doc_id = self._generate_doc_id(title)
        
        document = KnowledgeDocument(
            id=doc_id,
            title=title,
            content=content,
            category=category,
            tags=tags,
            metadata=metadata or {},
            created_at=datetime.now()
        )
        
        self.documents[doc_id] = document
        self.is_indexed = False  # Need to re-index
        
        logger.info(f"Added document: {title} (ID: {doc_id})")
        return doc_id
    
    def build_index(self):
        """Build TF-IDF index for document retrieval"""
        if not self.documents:
            logger.warning("No documents to index")
            return
        
        # Prepare documents for vectorization
        doc_texts = []
        doc_ids = []
        
        for doc_id, document in self.documents.items():
            # Combine title, content, and tags for better matching
            combined_text = f"{document.title} {document.content} {' '.join(document.tags)}"
            doc_texts.append(combined_text)
            doc_ids.append(doc_id)
        
        # Create TF-IDF vectors
        try:
            self.document_vectors = self.vectorizer.fit_transform(doc_texts)
            self.doc_ids = doc_ids
            self.is_indexed = True
            logger.info(f"Successfully indexed {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error building index: {e}")
            self.is_indexed = False
    
    def search(self, query: str, top_k: int = 3, min_similarity: float = 0.1) -> List[Tuple[KnowledgeDocument, float]]:
        """Search for relevant documents using TF-IDF similarity"""
        if not self.is_indexed:
            self.build_index()
        
        if not self.is_indexed or self.document_vectors is None:
            logger.warning("Index not available, returning empty results")
            return []
        
        try:
            # Vectorize query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                similarity = similarities[idx]
                if similarity >= min_similarity:
                    doc_id = self.doc_ids[idx]
                    document = self.documents[doc_id]
                    results.append((document, similarity))
            
            logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieve document by ID"""
        return self.documents.get(doc_id)
    
    def get_documents_by_category(self, category: str) -> List[KnowledgeDocument]:
        """Get all documents in a specific category"""
        return [doc for doc in self.documents.values() if doc.category.lower() == category.lower()]
    
    def get_documents_by_tag(self, tag: str) -> List[KnowledgeDocument]:
        """Get all documents with a specific tag"""
        return [doc for doc in self.documents.values() if tag.lower() in [t.lower() for t in doc.tags]]
    
    def _save_knowledge_base(self):
        """Save knowledge base to disk"""
        try:
            kb_file = os.path.join(self.knowledge_dir, "knowledge_base.pkl")
            with open(kb_file, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'vectorizer': self.vectorizer,
                    'document_vectors': self.document_vectors,
                    'doc_ids': getattr(self, 'doc_ids', []),
                    'is_indexed': self.is_indexed
                }, f)
            logger.info(f"Knowledge base saved to {kb_file}")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
    
    def _load_knowledge_base(self):
        """Load knowledge base from disk"""
        try:
            kb_file = os.path.join(self.knowledge_dir, "knowledge_base.pkl")
            if os.path.exists(kb_file):
                with open(kb_file, 'rb') as f:
                    data = pickle.load(f)
                
                # Only load if we don't have documents (avoid overwriting defaults)
                if not self.documents:
                    self.documents = data.get('documents', {})
                    self.vectorizer = data.get('vectorizer', self.vectorizer)
                    self.document_vectors = data.get('document_vectors')
                    self.doc_ids = data.get('doc_ids', [])
                    self.is_indexed = data.get('is_indexed', False)
                    
                    logger.info(f"Loaded {len(self.documents)} documents from {kb_file}")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
    
    def save(self):
        """Public method to save knowledge base"""
        self._save_knowledge_base()


class RAGSystem:
    """
    Complete RAG (Retrieval-Augmented Generation) system
    Combines knowledge retrieval with AI generation
    """
    
    def __init__(self, knowledge_base: TradingKnowledgeBase, openai_client=None):
        """Initialize RAG system"""
        self.knowledge_base = knowledge_base
        self.openai_client = openai_client
        
        # Ensure knowledge base is indexed
        if not self.knowledge_base.is_indexed:
            self.knowledge_base.build_index()
    
    async def answer_question(self, question: str, context: str = "", 
                            max_context_length: int = 3000) -> Dict[str, Any]:
        """
        Answer a question using RAG approach
        1. Retrieve relevant knowledge
        2. Augment with context
        3. Generate comprehensive answer
        """
        try:
            # Step 1: Retrieve relevant documents
            relevant_docs = self.knowledge_base.search(question, top_k=3, min_similarity=0.1)
            
            # Step 2: Prepare context from retrieved documents
            retrieved_context = ""
            sources = []
            
            for doc, similarity in relevant_docs:
                retrieved_context += f"\n\n--- {doc.title} (Relevance: {similarity:.2f}) ---\n"
                retrieved_context += doc.content[:1000]  # Limit content length
                sources.append({
                    "title": doc.title,
                    "category": doc.category,
                    "similarity": similarity,
                    "tags": doc.tags
                })
            
            # Step 3: Combine with conversation context
            full_context = f"{context}\n\nRelevant Knowledge:\n{retrieved_context}"
            
            # Truncate if too long
            if len(full_context) > max_context_length:
                full_context = full_context[:max_context_length] + "..."
            
            # Step 4: Generate answer using AI if available
            if self.openai_client:
                answer = await self._generate_ai_answer(question, full_context)
            else:
                answer = self._generate_fallback_answer(question, relevant_docs)
            
            return {
                "answer": answer,
                "sources": sources,
                "retrieved_docs": len(relevant_docs),
                "context_used": len(full_context),
                "method": "ai" if self.openai_client else "fallback"
            }
            
        except Exception as e:
            logger.error(f"Error in RAG answer generation: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "retrieved_docs": 0,
                "context_used": 0,
                "method": "error"
            }
    
    async def _generate_ai_answer(self, question: str, context: str) -> str:
        """Generate AI-powered answer using retrieved context"""
        prompt = f"""
        You are an expert trading and investment advisor with access to comprehensive knowledge.
        
        User Question: {question}
        
        Relevant Context and Knowledge:
        {context}
        
        Instructions:
        1. Provide a comprehensive, accurate answer based on the retrieved knowledge
        2. If the context contains relevant information, use it to enhance your response
        3. Be specific and actionable where appropriate
        4. If you're unsure about something, acknowledge the uncertainty
        5. Structure your response clearly with headings if needed
        6. Include practical examples or applications when relevant
        
        Please provide a detailed, helpful response:
        """
        
        try:
            from src.integrations.openai.client import ModelType
            
            messages = [
                {"role": "system", "content": "You are a knowledgeable trading and investment advisor. Provide accurate, helpful, and well-structured responses based on the provided context and your expertise."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.openai_client.chat_completion(messages, ModelType.GPT_4O)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI answer: {e}")
            return self._generate_fallback_answer(question, [])
    
    def _generate_fallback_answer(self, question: str, relevant_docs: List[Tuple]) -> str:
        """Generate fallback answer when AI is not available"""
        if not relevant_docs:
            return f"""
            I found your question about "{question}" interesting, but I don't have specific information readily available in my knowledge base.
            
            For trading and investment questions, I recommend:
            1. Consulting reputable financial websites (Yahoo Finance, Bloomberg, MarketWatch)
            2. Reading educational resources from established brokerages
            3. Considering professional financial advice for complex situations
            4. Practicing with paper trading before risking real money
            
            Feel free to ask more specific questions about technical analysis, fundamental analysis, risk management, or investment strategies!
            """
        
        # Combine information from relevant documents
        answer = f"Based on my knowledge base, here's what I can tell you about your question:\n\n"
        
        for i, (doc, similarity) in enumerate(relevant_docs, 1):
            answer += f"**{i}. {doc.title}** (Relevance: {similarity:.1%})\n"
            
            # Extract most relevant portion of content
            content_preview = doc.content[:500]
            if len(doc.content) > 500:
                content_preview += "..."
            
            answer += f"{content_preview}\n\n"
        
        answer += """
        **Additional Resources:**
        For more detailed information, consider exploring:
        - Technical analysis books and courses
        - Financial news and market analysis websites
        - Professional trading platforms with educational resources
        - Investment advisory services for personalized guidance
        
        Would you like me to elaborate on any specific aspect of this topic?
        """
        
        return answer
    
    def add_knowledge(self, title: str, content: str, category: str, tags: List[str]) -> str:
        """Add new knowledge to the system"""
        doc_id = self.knowledge_base.add_document(title, content, category, tags)
        self.knowledge_base.save()
        return doc_id
    
    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base and return formatted results"""
        results = self.knowledge_base.search(query, top_k=top_k)
        
        formatted_results = []
        for doc, similarity in results:
            formatted_results.append({
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "tags": doc.tags,
                "similarity": similarity,
                "preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "created_at": doc.created_at.isoformat()
            })
        
        return formatted_results

