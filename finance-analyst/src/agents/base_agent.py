"""
Base agent class for the Multi-Agent AI Trading System
"""
import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from src.integrations.openai.client import openai_client, ModelType
from src.utils.logging import get_agent_logger
from src.models.trading import AgentDecision, TradeAction, AgentType, db
from config.settings import config


class AnalysisType(Enum):
    """Types of analysis that agents can perform"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    MARKET_OVERVIEW = "market_overview"


@dataclass
class AnalysisResult:
    """Standardized analysis result structure"""
    agent_type: AgentType
    symbol: str
    recommendation: TradeAction
    confidence: float  # 0.0 to 1.0
    reasoning: str
    analysis_data: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type.value,
            "symbol": self.symbol,
            "recommendation": self.recommendation.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "analysis_data": self.analysis_data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketContext:
    """Market context information for analysis"""
    symbol: str
    current_price: float
    price_history: List[Dict[str, Any]]
    volume_data: List[Dict[str, Any]]
    market_indicators: Dict[str, float]
    news_sentiment: Optional[Dict[str, Any]] = None
    fundamental_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "price_history": self.price_history,
            "volume_data": self.volume_data,
            "market_indicators": self.market_indicators,
            "news_sentiment": self.news_sentiment,
            "fundamental_data": self.fundamental_data
        }


class BaseAgent(ABC):
    """Base class for all trading agents"""
    
    def __init__(self, agent_type: AgentType, name: str):
        self.agent_type = agent_type
        self.name = name
        self.logger = get_agent_logger(name)
        self.is_active = True
        self.performance_metrics = {}
        
        # Agent-specific configuration
        self.config = config.agents
        
        # Initialize agent
        self._initialize_agent()
        
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="initialization",
            result={"status": "initialized", "agent_type": agent_type.value}
        )
    
    @abstractmethod
    def _initialize_agent(self):
        """Initialize agent-specific components"""
        pass
    
    @abstractmethod
    async def analyze(self, context: MarketContext) -> AnalysisResult:
        """Perform analysis on the given market context"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    @abstractmethod
    def get_analysis_functions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for this agent"""
        pass
    
    async def analyze_async(self, context: MarketContext) -> AnalysisResult:
        """Asynchronous wrapper for analysis"""
        try:
            if not self.is_active:
                raise Exception(f"Agent {self.name} is not active")
            
            start_time = datetime.now(timezone.utc)
            result = await self.analyze(context)
            end_time = datetime.now(timezone.utc)
            
            # Log performance metrics
            analysis_time = (end_time - start_time).total_seconds()
            self.performance_metrics["last_analysis_time"] = analysis_time
            self.performance_metrics["last_analysis_timestamp"] = end_time.isoformat()
            
            # Log the analysis result
            self.logger.log_analysis(
                symbol=context.symbol,
                analysis_type=self.agent_type.value,
                result=result.to_dict()
            )
            
            # Save to database
            await self._save_decision_to_db(result)
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol, "agent_type": self.agent_type.value})
            raise
    
    async def _save_decision_to_db(self, result: AnalysisResult):
        """Save agent decision to database"""
        try:
            decision = AgentDecision(
                agent_type=result.agent_type,
                symbol=result.symbol,
                recommendation=result.recommendation,
                confidence=result.confidence,
                reasoning=result.reasoning,
                analysis_data=result.analysis_data,
                timestamp=result.timestamp
            )
            
            db.session.add(decision)
            db.session.commit()
            
        except Exception as e:
            self.logger.log_error(e, {"context": "saving_decision_to_db"})
            db.session.rollback()
    
    async def query_openai(
        self,
        messages: List[Dict[str, str]],
        model: ModelType = ModelType.GPT_4_TURBO,
        use_functions: bool = True
    ) -> Dict[str, Any]:
        """Query OpenAI with agent-specific configuration"""
        
        # Add system prompt
        system_prompt = self.get_system_prompt()
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        if use_functions:
            functions = self.get_analysis_functions()
            return await openai_client.function_call_completion(
                messages=full_messages,
                functions=functions,
                model=model
            )
        else:
            response = await openai_client.chat_completion(
                messages=full_messages,
                model=model
            )
            return {
                "type": "text_response",
                "content": response.choices[0].message.content
            }
    
    def format_market_context(self, context: MarketContext) -> str:
        """Format market context for OpenAI prompt"""
        return f"""
Market Context for {context.symbol}:

Current Price: ${context.current_price:.2f}

Recent Price History (last 10 periods):
{self._format_price_history(context.price_history[-10:])}

Volume Data:
{self._format_volume_data(context.volume_data[-5:])}

Market Indicators:
{self._format_market_indicators(context.market_indicators)}

{self._format_additional_context(context)}
"""
    
    def _format_price_history(self, price_history: List[Dict[str, Any]]) -> str:
        """Format price history for display"""
        if not price_history:
            return "No price history available"
        
        lines = []
        for data in price_history:
            timestamp = data.get("timestamp", "Unknown")
            open_price = data.get("open", 0)
            high = data.get("high", 0)
            low = data.get("low", 0)
            close = data.get("close", 0)
            
            lines.append(f"  {timestamp}: O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}")
        
        return "\n".join(lines)
    
    def _format_volume_data(self, volume_data: List[Dict[str, Any]]) -> str:
        """Format volume data for display"""
        if not volume_data:
            return "No volume data available"
        
        lines = []
        for data in volume_data:
            timestamp = data.get("timestamp", "Unknown")
            volume = data.get("volume", 0)
            lines.append(f"  {timestamp}: {volume:,}")
        
        return "\n".join(lines)
    
    def _format_market_indicators(self, indicators: Dict[str, float]) -> str:
        """Format market indicators for display"""
        if not indicators:
            return "No market indicators available"
        
        lines = []
        for indicator, value in indicators.items():
            lines.append(f"  {indicator}: {value:.4f}")
        
        return "\n".join(lines)
    
    def _format_additional_context(self, context: MarketContext) -> str:
        """Format additional context information"""
        additional = []
        
        if context.news_sentiment:
            additional.append(f"News Sentiment: {context.news_sentiment}")
        
        if context.fundamental_data:
            additional.append(f"Fundamental Data: {context.fundamental_data}")
        
        return "\n".join(additional) if additional else ""
    
    def parse_function_response(self, response: Dict[str, Any]) -> AnalysisResult:
        """Parse OpenAI function response into AnalysisResult"""
        if response["type"] != "function_call":
            raise ValueError("Expected function call response")
        
        args = response["function_arguments"]
        
        # Extract required fields
        symbol = args.get("symbol", "UNKNOWN")
        recommendation_str = args.get("recommendation", "HOLD")
        confidence = float(args.get("confidence", 0.5))
        reasoning = args.get("reasoning", "No reasoning provided")
        analysis_data = args.get("analysis_data", {})
        
        # Convert recommendation string to enum
        try:
            recommendation = TradeAction(recommendation_str.lower())
        except ValueError:
            recommendation = TradeAction.HOLD
        
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=symbol,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            analysis_data=analysis_data,
            timestamp=datetime.now(timezone.utc)
        )
    
    def validate_analysis_result(self, result: AnalysisResult) -> bool:
        """Validate analysis result"""
        if not (0.0 <= result.confidence <= 1.0):
            self.logger.log_error(
                ValueError("Confidence must be between 0.0 and 1.0"),
                {"confidence": result.confidence}
            )
            return False
        
        if not result.reasoning or len(result.reasoning.strip()) < 10:
            self.logger.log_error(
                ValueError("Reasoning must be provided and meaningful"),
                {"reasoning": result.reasoning}
            )
            return False
        
        return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_type": self.agent_type.value,
            "name": self.name,
            "is_active": self.is_active,
            "performance_metrics": self.performance_metrics
        }
    
    def activate(self):
        """Activate the agent"""
        self.is_active = True
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="status_change",
            result={"status": "activated"}
        )
    
    def deactivate(self):
        """Deactivate the agent"""
        self.is_active = False
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="status_change",
            result={"status": "deactivated"}
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent"""
        try:
            # Test OpenAI connectivity
            test_messages = [{"role": "user", "content": "Health check"}]
            await openai_client.chat_completion(
                messages=test_messages,
                model=ModelType.GPT_4O_MINI,
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "agent_type": self.agent_type.value,
                "name": self.name,
                "is_active": self.is_active,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(e, {"context": "health_check"})
            return {
                "status": "unhealthy",
                "agent_type": self.agent_type.value,
                "name": self.name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

