"""
Memory System - Conversation Context and Customer History Management
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .json_encoder import safe_json_dumps, safe_json_loads

@dataclass
class Interaction:
    """Single customer interaction record"""
    interaction_id: str
    customer_id: str
    session_id: str
    timestamp: str
    query: str
    response: str
    plan_id: str
    confidence_score: float
    compliance_status: str
    metadata: Dict[str, Any]

@dataclass
class CustomerProfile:
    """Customer profile with preferences and history"""
    customer_id: str
    preferences: Dict[str, Any]
    interaction_count: int
    last_interaction: str
    risk_profile: str
    preferred_language: str
    communication_preferences: Dict[str, Any]

class MemorySystem:
    """
    Advanced memory system for maintaining conversation context and customer history
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('MemorySystem')
        
        # Database configuration
        self.db_path = config.get('database_path', 'src/database/memory.db')
        self.max_context_length = config.get('max_context_length', 10)
        self.context_window_hours = config.get('context_window_hours', 24)
        
        # Initialize database
        self._init_database()
        
        # In-memory cache for active sessions
        self.session_cache = {}
        self.customer_cache = {}
        
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    interaction_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    session_id TEXT,
                    timestamp TEXT,
                    query TEXT,
                    response TEXT,
                    plan_id TEXT,
                    confidence_score REAL,
                    compliance_status TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create customer profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_profiles (
                    customer_id TEXT PRIMARY KEY,
                    preferences TEXT,
                    interaction_count INTEGER,
                    last_interaction TEXT,
                    risk_profile TEXT,
                    preferred_language TEXT,
                    communication_preferences TEXT
                )
            ''')
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    start_time TEXT,
                    last_activity TEXT,
                    status TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_id ON interactions(customer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON interactions(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON interactions(timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Memory database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing memory database: {str(e)}")
            raise
    
    async def get_context(self, 
                         customer_id: Optional[str] = None,
                         session_id: Optional[str] = None,
                         query: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve relevant context for the current interaction
        """
        try:
            context = {
                'history': [],
                'customer_profile': None,
                'session_info': None,
                'relevant_interactions': []
            }
            
            # Get customer profile if customer_id provided
            if customer_id:
                context['customer_profile'] = await self._get_customer_profile(customer_id)
            
            # Get session history if session_id provided
            if session_id:
                context['session_info'] = await self._get_session_info(session_id)
                context['history'] = await self._get_session_history(session_id)
            
            # Get relevant past interactions based on query similarity
            if query and customer_id:
                context['relevant_interactions'] = await self._get_relevant_interactions(
                    customer_id, query
                )
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return {'history': [], 'customer_profile': None, 'session_info': None}
    
    async def store_interaction(self,
                              customer_id: Optional[str],
                              session_id: Optional[str],
                              query: str,
                              response: str,
                              plan: Any,
                              reflection: Any) -> str:
        """
        Store a new interaction in memory
        """
        try:
            import uuid
            
            interaction_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Create interaction record
            interaction = Interaction(
                interaction_id=interaction_id,
                customer_id=customer_id or "anonymous",
                session_id=session_id or "default",
                timestamp=timestamp,
                query=query,
                response=response,
                plan_id=getattr(plan, 'plan_id', 'unknown'),
                confidence_score=getattr(reflection, 'confidence_score', 0.5),
                compliance_status=getattr(reflection, 'compliance_status', 'unknown'),
                metadata={
                    'plan': asdict(plan) if hasattr(plan, '__dict__') else str(plan),
                    'reflection': asdict(reflection) if hasattr(reflection, '__dict__') else str(reflection)
                }
            )
            
            # Store in database
            await self._store_interaction_db(interaction)
            
            # Update customer profile
            if customer_id:
                await self._update_customer_profile(customer_id, interaction)
            
            # Update session cache
            if session_id:
                await self._update_session_cache(session_id, interaction)
            
            self.logger.info(f"Stored interaction {interaction_id}")
            return interaction_id
            
        except Exception as e:
            self.logger.error(f"Error storing interaction: {str(e)}")
            return ""
    
    async def _get_customer_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """Retrieve customer profile from database"""
        try:
            # Check cache first
            if customer_id in self.customer_cache:
                return self.customer_cache[customer_id]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM customer_profiles WHERE customer_id = ?',
                (customer_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                profile = CustomerProfile(
                    customer_id=row[0],
                    preferences=json.loads(row[1]) if row[1] else {},
                    interaction_count=row[2],
                    last_interaction=row[3],
                    risk_profile=row[4],
                    preferred_language=row[5],
                    communication_preferences=json.loads(row[6]) if row[6] else {}
                )
                
                # Cache the profile
                self.customer_cache[customer_id] = profile
                return profile
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving customer profile: {str(e)}")
            return None
    
    async def _get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve session interaction history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent interactions for this session
            cutoff_time = (datetime.now() - timedelta(hours=self.context_window_hours)).isoformat()
            
            cursor.execute('''
                SELECT query, response, timestamp, confidence_score
                FROM interactions 
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, cutoff_time, self.max_context_length))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'query': row[0],
                    'response': row[1],
                    'timestamp': row[2],
                    'confidence_score': row[3]
                })
            
            return list(reversed(history))  # Return in chronological order
            
        except Exception as e:
            self.logger.error(f"Error retrieving session history: {str(e)}")
            return []
    
    async def _get_relevant_interactions(self, customer_id: str, query: str) -> List[Dict[str, Any]]:
        """Find relevant past interactions based on query similarity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple keyword-based relevance (could be enhanced with embeddings)
            query_words = set(query.lower().split())
            
            cursor.execute('''
                SELECT query, response, timestamp, confidence_score
                FROM interactions 
                WHERE customer_id = ?
                ORDER BY timestamp DESC
                LIMIT 50
            ''', (customer_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            relevant = []
            for row in rows:
                interaction_words = set(row[0].lower().split())
                overlap = len(query_words.intersection(interaction_words))
                
                if overlap >= 2:  # At least 2 words in common
                    relevant.append({
                        'query': row[0],
                        'response': row[1],
                        'timestamp': row[2],
                        'confidence_score': row[3],
                        'relevance_score': overlap / len(query_words)
                    })
            
            # Sort by relevance and return top 5
            relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
            return relevant[:5]
            
        except Exception as e:
            self.logger.error(f"Error finding relevant interactions: {str(e)}")
            return []
    
    async def _store_interaction_db(self, interaction: Interaction):
        """Store interaction in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO interactions 
                (interaction_id, customer_id, session_id, timestamp, query, response, 
                 plan_id, confidence_score, compliance_status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                interaction.interaction_id,
                interaction.customer_id,
                interaction.session_id,
                interaction.timestamp,
                interaction.query,
                interaction.response,
                interaction.plan_id,
                interaction.confidence_score,
                interaction.compliance_status,
                safe_json_dumps(interaction.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing interaction in database: {str(e)}")
            raise
    
    async def _update_customer_profile(self, customer_id: str, interaction: Interaction):
        """Update customer profile with new interaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if profile exists
            cursor.execute(
                'SELECT interaction_count FROM customer_profiles WHERE customer_id = ?',
                (customer_id,)
            )
            
            row = cursor.fetchone()
            
            if row:
                # Update existing profile
                new_count = row[0] + 1
                cursor.execute('''
                    UPDATE customer_profiles 
                    SET interaction_count = ?, last_interaction = ?
                    WHERE customer_id = ?
                ''', (new_count, interaction.timestamp, customer_id))
            else:
                # Create new profile
                cursor.execute('''
                    INSERT INTO customer_profiles 
                    (customer_id, preferences, interaction_count, last_interaction, 
                     risk_profile, preferred_language, communication_preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id,
                    json.dumps({}),
                    1,
                    interaction.timestamp,
                    'standard',
                    'en',
                    json.dumps({})
                ))
            
            conn.commit()
            conn.close()
            
            # Clear cache to force refresh
            if customer_id in self.customer_cache:
                del self.customer_cache[customer_id]
            
        except Exception as e:
            self.logger.error(f"Error updating customer profile: {str(e)}")
    
    async def _get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM sessions WHERE session_id = ?',
                (session_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'session_id': row[0],
                    'customer_id': row[1],
                    'start_time': row[2],
                    'last_activity': row[3],
                    'status': row[4],
                    'metadata': json.loads(row[5]) if row[5] else {}
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving session info: {str(e)}")
            return None
    
    async def _update_session_cache(self, session_id: str, interaction: Interaction):
        """Update session cache with new interaction"""
        if session_id not in self.session_cache:
            self.session_cache[session_id] = []
        
        self.session_cache[session_id].append({
            'query': interaction.query,
            'response': interaction.response,
            'timestamp': interaction.timestamp
        })
        
        # Keep only recent interactions in cache
        if len(self.session_cache[session_id]) > self.max_context_length:
            self.session_cache[session_id] = self.session_cache[session_id][-self.max_context_length:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get memory system status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute('SELECT COUNT(*) FROM interactions')
            interaction_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM customer_profiles')
            customer_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM sessions')
            session_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "module": "memory",
                "status": "healthy",
                "statistics": {
                    "total_interactions": interaction_count,
                    "total_customers": customer_count,
                    "active_sessions": session_count,
                    "cached_sessions": len(self.session_cache),
                    "cached_customers": len(self.customer_cache)
                },
                "capabilities": [
                    "conversation_context",
                    "customer_profiling",
                    "session_management",
                    "interaction_history",
                    "relevance_matching"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting memory status: {str(e)}")
            return {
                "module": "memory",
                "status": "error",
                "error": str(e)
            }

