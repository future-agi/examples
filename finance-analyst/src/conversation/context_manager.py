"""
Context-Aware Conversation Management System
Maintains conversation history, context, and user preferences
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ConversationState(Enum):
    """Current state of conversation"""
    GREETING = "greeting"
    STOCK_ANALYSIS = "stock_analysis"
    EDUCATION = "education"
    PLANNING = "planning"
    EXECUTION = "execution"
    GENERAL = "general"

@dataclass
class Message:
    """Represents a single message in conversation"""
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    tokens: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['type'] = self.type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary"""
        data['type'] = MessageType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class ConversationContext:
    """Maintains conversation context and state"""
    session_id: str
    user_id: Optional[str]
    state: ConversationState
    current_topic: Optional[str]
    mentioned_stocks: List[str]
    user_preferences: Dict[str, Any]
    conversation_summary: str
    last_activity: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['state'] = self.state.value
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create from dictionary"""
        data['state'] = ConversationState(data['state'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        return cls(**data)

class ConversationManager:
    """
    Manages conversation history, context, and state
    Provides context-aware responses and maintains user preferences
    """
    
    def __init__(self, storage_dir: str = "data/conversations", max_history: int = 100):
        """Initialize conversation manager"""
        self.storage_dir = storage_dir
        self.max_history = max_history
        self.conversations: Dict[str, List[Message]] = {}
        self.contexts: Dict[str, ConversationContext] = {}
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing conversations
        self._load_conversations()
    
    def start_conversation(self, session_id: str, user_id: Optional[str] = None) -> ConversationContext:
        """Start a new conversation or resume existing one"""
        if session_id in self.contexts:
            # Resume existing conversation
            context = self.contexts[session_id]
            context.last_activity = datetime.now()
            logger.info(f"Resumed conversation {session_id}")
        else:
            # Create new conversation
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                state=ConversationState.GREETING,
                current_topic=None,
                mentioned_stocks=[],
                user_preferences={
                    "risk_tolerance": "moderate",
                    "investment_horizon": "long_term",
                    "preferred_analysis": "both",  # technical, fundamental, both
                    "experience_level": "intermediate"
                },
                conversation_summary="",
                last_activity=datetime.now()
            )
            self.contexts[session_id] = context
            self.conversations[session_id] = []
            logger.info(f"Started new conversation {session_id}")
        
        return context
    
    def add_message(self, session_id: str, message_type: MessageType, 
                   content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add a message to conversation history"""
        if session_id not in self.conversations:
            self.start_conversation(session_id)
        
        message = Message(
            id=f"{session_id}_{len(self.conversations[session_id])}",
            type=message_type,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
            tokens=self._estimate_tokens(content)
        )
        
        self.conversations[session_id].append(message)
        
        # Update context
        self._update_context(session_id, message)
        
        # Trim history if too long
        self._trim_history(session_id)
        
        # Auto-save periodically
        if len(self.conversations[session_id]) % 10 == 0:
            self._save_conversation(session_id)
        
        return message
    
    def get_conversation_history(self, session_id: str, 
                               last_n: Optional[int] = None) -> List[Message]:
        """Get conversation history for a session"""
        if session_id not in self.conversations:
            return []
        
        messages = self.conversations[session_id]
        if last_n:
            return messages[-last_n:]
        return messages
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context"""
        return self.contexts.get(session_id)
    
    def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]):
        """Update user preferences"""
        if session_id in self.contexts:
            self.contexts[session_id].user_preferences.update(preferences)
            logger.info(f"Updated preferences for {session_id}: {preferences}")
    
    def get_contextual_prompt(self, session_id: str, current_query: str) -> str:
        """Generate contextual prompt including conversation history"""
        context = self.get_context(session_id)
        if not context:
            return current_query
        
        # Get recent conversation history
        recent_messages = self.get_conversation_history(session_id, last_n=10)
        
        # Build contextual prompt
        prompt_parts = []
        
        # Add conversation summary if available
        if context.conversation_summary:
            prompt_parts.append(f"Conversation Summary: {context.conversation_summary}")
        
        # Add user preferences
        prefs = context.user_preferences
        prompt_parts.append(f"""
        User Profile:
        - Risk Tolerance: {prefs.get('risk_tolerance', 'moderate')}
        - Investment Horizon: {prefs.get('investment_horizon', 'long_term')}
        - Preferred Analysis: {prefs.get('preferred_analysis', 'both')}
        - Experience Level: {prefs.get('experience_level', 'intermediate')}
        """)
        
        # Add current topic and mentioned stocks
        if context.current_topic:
            prompt_parts.append(f"Current Topic: {context.current_topic}")
        
        if context.mentioned_stocks:
            prompt_parts.append(f"Previously Mentioned Stocks: {', '.join(context.mentioned_stocks)}")
        
        # Add recent conversation history
        if recent_messages:
            prompt_parts.append("Recent Conversation:")
            for msg in recent_messages[-5:]:  # Last 5 messages
                role = "User" if msg.type == MessageType.USER else "Assistant"
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                prompt_parts.append(f"{role}: {content_preview}")
        
        # Add current query
        prompt_parts.append(f"Current Question: {current_query}")
        
        return "\n\n".join(prompt_parts)
    
    def extract_entities(self, message: str) -> Dict[str, List[str]]:
        """Extract entities from message (stocks, topics, etc.)"""
        entities = {
            "stocks": [],
            "topics": [],
            "indicators": [],
            "strategies": []
        }
        
        message_upper = message.upper()
        
        # Extract stock symbols
        import re
        stock_patterns = [
            r'\b([A-Z]{2,5})\b',  # Standard symbols
            r'\b(APPLE|MICROSOFT|GOOGLE|AMAZON|TESLA|META|NVIDIA)\b'  # Company names
        ]
        
        for pattern in stock_patterns:
            matches = re.findall(pattern, message_upper)
            entities["stocks"].extend(matches)
        
        # Extract trading topics
        topic_keywords = {
            "technical analysis": ["TECHNICAL", "CHART", "RSI", "MACD", "MOVING AVERAGE"],
            "fundamental analysis": ["FUNDAMENTAL", "P/E", "EARNINGS", "REVENUE", "VALUATION"],
            "risk management": ["RISK", "DIVERSIFICATION", "STOP LOSS", "POSITION SIZE"],
            "market psychology": ["PSYCHOLOGY", "SENTIMENT", "FEAR", "GREED", "EMOTION"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_upper for keyword in keywords):
                entities["topics"].append(topic)
        
        # Extract indicators
        indicators = ["RSI", "MACD", "SMA", "EMA", "BOLLINGER", "STOCHASTIC", "ATR"]
        for indicator in indicators:
            if indicator in message_upper:
                entities["indicators"].append(indicator)
        
        # Extract strategies
        strategies = ["BUY AND HOLD", "VALUE INVESTING", "GROWTH INVESTING", "DAY TRADING", "SWING TRADING"]
        for strategy in strategies:
            if strategy in message_upper:
                entities["strategies"].append(strategy)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def _update_context(self, session_id: str, message: Message):
        """Update conversation context based on new message"""
        context = self.contexts[session_id]
        
        if message.type == MessageType.USER:
            # Extract entities from user message
            entities = self.extract_entities(message.content)
            
            # Update mentioned stocks
            new_stocks = entities["stocks"]
            for stock in new_stocks:
                if stock not in context.mentioned_stocks:
                    context.mentioned_stocks.append(stock)
            
            # Update current topic
            if entities["topics"]:
                context.current_topic = entities["topics"][0]
            
            # Update conversation state based on content
            content_lower = message.content.lower()
            if any(word in content_lower for word in ["analyze", "analysis", "stock", "price"]):
                context.state = ConversationState.STOCK_ANALYSIS
            elif any(word in content_lower for word in ["what is", "explain", "how does", "learn"]):
                context.state = ConversationState.EDUCATION
            elif any(word in content_lower for word in ["plan", "strategy", "approach", "steps"]):
                context.state = ConversationState.PLANNING
            else:
                context.state = ConversationState.GENERAL
        
        context.last_activity = datetime.now()
        
        # Update conversation summary periodically
        if len(self.conversations[session_id]) % 20 == 0:
            self._update_conversation_summary(session_id)
    
    def _update_conversation_summary(self, session_id: str):
        """Update conversation summary for long conversations"""
        messages = self.conversations[session_id]
        if len(messages) < 10:
            return
        
        # Get last 20 messages for summary
        recent_messages = messages[-20:]
        
        # Extract key topics and stocks discussed
        all_stocks = set()
        all_topics = set()
        
        for msg in recent_messages:
            if msg.type == MessageType.USER:
                entities = self.extract_entities(msg.content)
                all_stocks.update(entities["stocks"])
                all_topics.update(entities["topics"])
        
        # Create summary
        summary_parts = []
        if all_stocks:
            summary_parts.append(f"Discussed stocks: {', '.join(list(all_stocks)[:5])}")
        if all_topics:
            summary_parts.append(f"Topics covered: {', '.join(list(all_topics)[:3])}")
        
        summary = "; ".join(summary_parts)
        self.contexts[session_id].conversation_summary = summary
        
        logger.info(f"Updated conversation summary for {session_id}: {summary}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _trim_history(self, session_id: str):
        """Trim conversation history if it exceeds max_history"""
        if len(self.conversations[session_id]) > self.max_history:
            # Keep the most recent messages
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
            logger.info(f"Trimmed conversation history for {session_id}")
    
    def _save_conversation(self, session_id: str):
        """Save conversation to disk"""
        try:
            # Save messages
            messages_file = os.path.join(self.storage_dir, f"{session_id}_messages.json")
            messages_data = [msg.to_dict() for msg in self.conversations[session_id]]
            
            with open(messages_file, 'w') as f:
                json.dump(messages_data, f, indent=2)
            
            # Save context
            context_file = os.path.join(self.storage_dir, f"{session_id}_context.json")
            context_data = self.contexts[session_id].to_dict()
            
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            logger.debug(f"Saved conversation {session_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation {session_id}: {e}")
    
    def _load_conversations(self):
        """Load existing conversations from disk"""
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith("_messages.json"):
                    session_id = filename.replace("_messages.json", "")
                    
                    # Load messages
                    messages_file = os.path.join(self.storage_dir, filename)
                    with open(messages_file, 'r') as f:
                        messages_data = json.load(f)
                    
                    messages = [Message.from_dict(data) for data in messages_data]
                    self.conversations[session_id] = messages
                    
                    # Load context
                    context_file = os.path.join(self.storage_dir, f"{session_id}_context.json")
                    if os.path.exists(context_file):
                        with open(context_file, 'r') as f:
                            context_data = json.load(f)
                        
                        context = ConversationContext.from_dict(context_data)
                        self.contexts[session_id] = context
            
            logger.info(f"Loaded {len(self.conversations)} conversations")
            
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
    
    def save_all(self):
        """Save all conversations to disk"""
        for session_id in self.conversations:
            self._save_conversation(session_id)
    
    def cleanup_old_conversations(self, days: int = 30):
        """Clean up conversations older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        sessions_to_remove = []
        for session_id, context in self.contexts.items():
            if context.last_activity < cutoff_date:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            # Remove from memory
            del self.conversations[session_id]
            del self.contexts[session_id]
            
            # Remove files
            try:
                messages_file = os.path.join(self.storage_dir, f"{session_id}_messages.json")
                context_file = os.path.join(self.storage_dir, f"{session_id}_context.json")
                
                if os.path.exists(messages_file):
                    os.remove(messages_file)
                if os.path.exists(context_file):
                    os.remove(context_file)
                    
            except Exception as e:
                logger.error(f"Error removing files for {session_id}: {e}")
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old conversations")
    
    def get_conversation_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics about a conversation"""
        if session_id not in self.conversations:
            return {}
        
        messages = self.conversations[session_id]
        context = self.contexts[session_id]
        
        user_messages = [m for m in messages if m.type == MessageType.USER]
        assistant_messages = [m for m in messages if m.type == MessageType.ASSISTANT]
        
        total_tokens = sum(m.tokens or 0 for m in messages)
        
        return {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_tokens": total_tokens,
            "mentioned_stocks": context.mentioned_stocks,
            "current_topic": context.current_topic,
            "conversation_state": context.state.value,
            "duration": (datetime.now() - messages[0].timestamp).total_seconds() if messages else 0,
            "last_activity": context.last_activity.isoformat()
        }

