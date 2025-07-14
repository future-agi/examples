"""
Agent Orchestration and Coordination System for the Multi-Agent AI Trading System
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import threading
from queue import Queue, Empty

from src.agents.base_agent import BaseAgent, AnalysisResult, MarketContext
from src.agents.technical.technical_agent import TechnicalAnalysisAgent
from src.agents.fundamental.fundamental_agent import FundamentalAnalysisAgent
from src.agents.sentiment.sentiment_agent import SentimentAnalysisAgent
from src.agents.risk.risk_agent import RiskManagementAgent
from src.models.trading import AgentType, TradeAction, AgentDecision
from src.integrations.market_data.data_provider import MarketDataManager
from src.integrations.news.news_provider import NewsDataManager
from src.knowledge.knowledge_base import KnowledgeManager
from src.utils.logging import get_component_logger

logger = get_component_logger("orchestrator")


class DecisionStrategy(Enum):
    """Decision-making strategies"""
    CONSENSUS = "consensus"  # Require majority agreement
    WEIGHTED_AVERAGE = "weighted_average"  # Weight by confidence
    RISK_ADJUSTED = "risk_adjusted"  # Prioritize risk management
    TECHNICAL_PRIORITY = "technical_priority"  # Prioritize technical analysis
    FUNDAMENTAL_PRIORITY = "fundamental_priority"  # Prioritize fundamental analysis


@dataclass
class AgentWeight:
    """Agent weighting configuration"""
    technical: float = 0.3
    fundamental: float = 0.3
    sentiment: float = 0.2
    risk: float = 0.2
    
    def normalize(self):
        """Normalize weights to sum to 1.0"""
        total = self.technical + self.fundamental + self.sentiment + self.risk
        if total > 0:
            self.technical /= total
            self.fundamental /= total
            self.sentiment /= total
            self.risk /= total


@dataclass
class OrchestrationResult:
    """Result of agent orchestration"""
    symbol: str
    final_decision: TradeAction
    confidence: float
    reasoning: str
    agent_results: Dict[str, AnalysisResult]
    consensus_score: float
    risk_assessment: Dict[str, Any]
    execution_priority: int  # 1-10, higher = more urgent
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "final_decision": self.final_decision.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "agent_results": {k: v.to_dict() for k, v in self.agent_results.items()},
            "consensus_score": self.consensus_score,
            "risk_assessment": self.risk_assessment,
            "execution_priority": self.execution_priority,
            "timestamp": self.timestamp.isoformat()
        }


class ConsensusEngine:
    """Consensus decision-making engine"""
    
    def __init__(self, strategy: DecisionStrategy = DecisionStrategy.WEIGHTED_AVERAGE):
        self.strategy = strategy
        self.min_consensus_threshold = 0.6  # 60% agreement required
        
    def calculate_consensus(self, agent_results: Dict[str, AnalysisResult]) -> Tuple[TradeAction, float, float]:
        """Calculate consensus decision from agent results"""
        if not agent_results:
            return TradeAction.HOLD, 0.0, 0.0
        
        if self.strategy == DecisionStrategy.CONSENSUS:
            return self._consensus_voting(agent_results)
        elif self.strategy == DecisionStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average(agent_results)
        elif self.strategy == DecisionStrategy.RISK_ADJUSTED:
            return self._risk_adjusted_decision(agent_results)
        elif self.strategy == DecisionStrategy.TECHNICAL_PRIORITY:
            return self._technical_priority(agent_results)
        elif self.strategy == DecisionStrategy.FUNDAMENTAL_PRIORITY:
            return self._fundamental_priority(agent_results)
        else:
            return self._weighted_average(agent_results)
    
    def _consensus_voting(self, agent_results: Dict[str, AnalysisResult]) -> Tuple[TradeAction, float, float]:
        """Simple majority voting"""
        votes = {}
        total_confidence = 0.0
        
        for result in agent_results.values():
            action = result.recommendation
            confidence = result.confidence
            
            if action not in votes:
                votes[action] = {"count": 0, "total_confidence": 0.0}
            
            votes[action]["count"] += 1
            votes[action]["total_confidence"] += confidence
            total_confidence += confidence
        
        # Find majority decision
        total_agents = len(agent_results)
        majority_threshold = total_agents / 2
        
        for action, vote_data in votes.items():
            if vote_data["count"] > majority_threshold:
                avg_confidence = vote_data["total_confidence"] / vote_data["count"]
                consensus_score = vote_data["count"] / total_agents
                return action, avg_confidence, consensus_score
        
        # No majority, default to HOLD
        return TradeAction.HOLD, total_confidence / total_agents, 0.5
    
    def _weighted_average(self, agent_results: Dict[str, AnalysisResult]) -> Tuple[TradeAction, float, float]:
        """Weighted average based on confidence"""
        weights = AgentWeight()
        weights.normalize()
        
        # Map agent types to weights
        weight_map = {
            AgentType.TECHNICAL: weights.technical,
            AgentType.FUNDAMENTAL: weights.fundamental,
            AgentType.SENTIMENT: weights.sentiment,
            AgentType.RISK: weights.risk
        }
        
        # Calculate weighted scores for each action
        action_scores = {
            TradeAction.BUY: 0.0,
            TradeAction.SELL: 0.0,
            TradeAction.HOLD: 0.0
        }
        
        total_weight = 0.0
        total_confidence = 0.0
        
        for result in agent_results.values():
            agent_weight = weight_map.get(result.agent_type, 0.1)
            confidence_weight = result.confidence * agent_weight
            
            action_scores[result.recommendation] += confidence_weight
            total_weight += agent_weight
            total_confidence += result.confidence * agent_weight
        
        # Normalize scores
        if total_weight > 0:
            for action in action_scores:
                action_scores[action] /= total_weight
            total_confidence /= total_weight
        
        # Find highest scoring action
        best_action = max(action_scores, key=action_scores.get)
        best_score = action_scores[best_action]
        
        # Calculate consensus score (how much agreement there is)
        consensus_score = best_score / max(sum(action_scores.values()), 0.001)
        
        return best_action, total_confidence, consensus_score
    
    def _risk_adjusted_decision(self, agent_results: Dict[str, AnalysisResult]) -> Tuple[TradeAction, float, float]:
        """Risk-adjusted decision prioritizing risk management"""
        risk_result = None
        other_results = []
        
        for result in agent_results.values():
            if result.agent_type == AgentType.RISK:
                risk_result = result
            else:
                other_results.append(result)
        
        # If risk agent says SELL, prioritize that
        if risk_result and risk_result.recommendation == TradeAction.SELL:
            return TradeAction.SELL, risk_result.confidence, 1.0
        
        # If risk agent says HOLD and confidence is high, be conservative
        if risk_result and risk_result.recommendation == TradeAction.HOLD and risk_result.confidence > 0.7:
            return TradeAction.HOLD, risk_result.confidence, 0.8
        
        # Otherwise, use weighted average of other agents
        if other_results:
            other_agent_results = {f"agent_{i}": result for i, result in enumerate(other_results)}
            return self._weighted_average(other_agent_results)
        
        return TradeAction.HOLD, 0.5, 0.5
    
    def _technical_priority(self, agent_results: Dict[str, AnalysisResult]) -> Tuple[TradeAction, float, float]:
        """Prioritize technical analysis"""
        technical_result = None
        
        for result in agent_results.values():
            if result.agent_type == AgentType.TECHNICAL:
                technical_result = result
                break
        
        if technical_result and technical_result.confidence > 0.6:
            return technical_result.recommendation, technical_result.confidence, 1.0
        
        # Fall back to weighted average
        return self._weighted_average(agent_results)
    
    def _fundamental_priority(self, agent_results: Dict[str, AnalysisResult]) -> Tuple[TradeAction, float, float]:
        """Prioritize fundamental analysis"""
        fundamental_result = None
        
        for result in agent_results.values():
            if result.agent_type == AgentType.FUNDAMENTAL:
                fundamental_result = result
                break
        
        if fundamental_result and fundamental_result.confidence > 0.6:
            return fundamental_result.recommendation, fundamental_result.confidence, 1.0
        
        # Fall back to weighted average
        return self._weighted_average(agent_results)


class TaskQueue:
    """Task queue for managing analysis requests"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = Queue(maxsize=max_size)
        self.processing = set()
        self.completed = {}
        self.lock = threading.Lock()
    
    def add_task(self, symbol: str, priority: int = 5) -> str:
        """Add analysis task to queue"""
        task_id = f"{symbol}_{datetime.now(timezone.utc).timestamp()}"
        
        try:
            self.queue.put({
                "task_id": task_id,
                "symbol": symbol,
                "priority": priority,
                "created_at": datetime.now(timezone.utc)
            }, block=False)
            
            logger.info(f"Added task to queue: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to add task to queue: {e}")
            return ""
    
    def get_task(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Get next task from queue"""
        try:
            task = self.queue.get(timeout=timeout)
            
            with self.lock:
                self.processing.add(task["task_id"])
            
            return task
            
        except Empty:
            return None
    
    def complete_task(self, task_id: str, result: Any):
        """Mark task as completed"""
        with self.lock:
            self.processing.discard(task_id)
            self.completed[task_id] = {
                "result": result,
                "completed_at": datetime.now(timezone.utc)
            }
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get completed task result"""
        with self.lock:
            return self.completed.get(task_id, {}).get("result")
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status"""
        with self.lock:
            return {
                "queue_size": self.queue.qsize(),
                "processing": len(self.processing),
                "completed": len(self.completed)
            }


class TradingOrchestrator:
    """Main orchestrator for coordinating trading agents"""
    
    def __init__(self, market_data_manager: MarketDataManager, 
                 news_data_manager: NewsDataManager,
                 knowledge_manager: KnowledgeManager):
        
        self.market_data_manager = market_data_manager
        self.news_data_manager = news_data_manager
        self.knowledge_manager = knowledge_manager
        
        # Initialize agents
        self.agents = {
            AgentType.TECHNICAL: TechnicalAnalysisAgent(),
            AgentType.FUNDAMENTAL: FundamentalAnalysisAgent(),
            AgentType.SENTIMENT: SentimentAnalysisAgent(),
            AgentType.RISK: RiskManagementAgent()
        }
        
        # Initialize orchestration components
        self.consensus_engine = ConsensusEngine(DecisionStrategy.WEIGHTED_AVERAGE)
        self.task_queue = TaskQueue()
        
        # Configuration
        self.max_concurrent_analyses = 5
        self.analysis_timeout = 300  # 5 minutes
        self.cache_duration = 600  # 10 minutes
        
        # State management
        self.active_analyses = {}
        self.analysis_cache = {}
        self.cache_timestamps = {}
        
        # Worker management
        self.workers = []
        self.is_running = False
        
        logger.info("Trading Orchestrator initialized")
    
    async def start(self):
        """Start the orchestrator and worker processes"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_analyses):
            worker = asyncio.create_task(self._worker_loop(f"worker_{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started orchestrator with {len(self.workers)} workers")
    
    async def stop(self):
        """Stop the orchestrator and worker processes"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("Stopped orchestrator")
    
    async def analyze_symbol(self, symbol: str, priority: int = 5) -> str:
        """Request analysis for a symbol (async)"""
        # Check cache first
        if self._is_cached(symbol):
            logger.info(f"Using cached analysis for {symbol}")
            return f"cached_{symbol}"
        
        # Add to task queue
        task_id = self.task_queue.add_task(symbol, priority)
        return task_id
    
    async def get_analysis_result(self, task_id: str) -> Optional[OrchestrationResult]:
        """Get analysis result by task ID"""
        # Check if it's a cached result
        if task_id.startswith("cached_"):
            symbol = task_id.replace("cached_", "")
            return self.analysis_cache.get(symbol)
        
        # Check completed tasks
        return self.task_queue.get_result(task_id)
    
    async def analyze_symbol_sync(self, symbol: str) -> OrchestrationResult:
        """Synchronous analysis for immediate results"""
        try:
            # Check cache first
            if self._is_cached(symbol):
                return self.analysis_cache[symbol]
            
            # Perform analysis
            result = await self._perform_analysis(symbol)
            
            # Cache result
            self._cache_result(symbol, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in synchronous analysis for {symbol}: {e}")
            return self._create_error_result(symbol, str(e))
    
    async def _worker_loop(self, worker_id: str):
        """Worker loop for processing analysis tasks"""
        logger.info(f"Started worker: {worker_id}")
        
        while self.is_running:
            try:
                # Get next task
                task = self.task_queue.get_task(timeout=1.0)
                
                if task is None:
                    continue
                
                task_id = task["task_id"]
                symbol = task["symbol"]
                
                logger.info(f"Worker {worker_id} processing {symbol}")
                
                # Perform analysis
                result = await self._perform_analysis(symbol)
                
                # Cache and complete task
                self._cache_result(symbol, result)
                self.task_queue.complete_task(task_id, result)
                
                logger.info(f"Worker {worker_id} completed {symbol}")
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _perform_analysis(self, symbol: str) -> OrchestrationResult:
        """Perform comprehensive analysis using all agents"""
        try:
            # Gather market context
            market_context = await self._build_market_context(symbol)
            
            # Run all agents in parallel
            agent_tasks = []
            for agent_type, agent in self.agents.items():
                task = asyncio.create_task(
                    self._run_agent_with_timeout(agent, market_context)
                )
                agent_tasks.append((agent_type, task))
            
            # Collect results
            agent_results = {}
            for agent_type, task in agent_tasks:
                try:
                    result = await task
                    if result:
                        agent_results[agent_type.value] = result
                except Exception as e:
                    logger.error(f"Agent {agent_type.value} failed for {symbol}: {e}")
            
            # Generate consensus decision
            if agent_results:
                final_decision, confidence, consensus_score = self.consensus_engine.calculate_consensus(agent_results)
            else:
                final_decision = TradeAction.HOLD
                confidence = 0.1
                consensus_score = 0.0
            
            # Extract risk assessment
            risk_assessment = self._extract_risk_assessment(agent_results)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(agent_results, final_decision, consensus_score)
            
            # Calculate execution priority
            execution_priority = self._calculate_execution_priority(
                final_decision, confidence, consensus_score, risk_assessment
            )
            
            # Create orchestration result
            result = OrchestrationResult(
                symbol=symbol,
                final_decision=final_decision,
                confidence=confidence,
                reasoning=reasoning,
                agent_results=agent_results,
                consensus_score=consensus_score,
                risk_assessment=risk_assessment,
                execution_priority=execution_priority,
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"Completed analysis for {symbol}: {final_decision.value} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error performing analysis for {symbol}: {e}")
            return self._create_error_result(symbol, str(e))
    
    async def _build_market_context(self, symbol: str) -> MarketContext:
        """Build comprehensive market context"""
        try:
            # Get market data
            market_data = await self.market_data_manager.get_market_context(symbol)
            
            # Get news and sentiment data
            news_articles = await self.news_data_manager.get_news_for_symbol(symbol)
            social_posts = await self.news_data_manager.get_social_media_for_symbol(symbol)
            
            # Convert to MarketContext format
            context = MarketContext(
                symbol=symbol,
                current_price=market_data.get("current_price"),
                price_history=market_data.get("price_history", []),
                volume_data=market_data.get("volume_data", []),
                market_indicators=market_data.get("market_indicators", {}),
                news_data=[article.to_dict() for article in news_articles],
                social_data=[post.to_dict() for post in social_posts],
                fundamental_data=None,  # Would be populated from financial data APIs
                timestamp=datetime.now(timezone.utc)
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error building market context for {symbol}: {e}")
            # Return minimal context
            return MarketContext(
                symbol=symbol,
                current_price=None,
                price_history=[],
                volume_data=[],
                market_indicators={},
                news_data=[],
                social_data=[],
                fundamental_data=None,
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _run_agent_with_timeout(self, agent: BaseAgent, context: MarketContext) -> Optional[AnalysisResult]:
        """Run agent analysis with timeout"""
        try:
            return await asyncio.wait_for(
                agent.analyze(context),
                timeout=self.analysis_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent.agent_type.value} timed out for {context.symbol}")
            return None
        except Exception as e:
            logger.error(f"Agent {agent.agent_type.value} error for {context.symbol}: {e}")
            return None
    
    def _extract_risk_assessment(self, agent_results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """Extract risk assessment from agent results"""
        risk_assessment = {
            "overall_risk": "medium",
            "risk_factors": [],
            "risk_score": 0.5
        }
        
        # Get risk agent result
        risk_result = agent_results.get(AgentType.RISK.value)
        if risk_result and risk_result.analysis_data:
            risk_data = risk_result.analysis_data
            
            # Extract portfolio risk
            portfolio_risk = risk_data.get("portfolio_risk", {})
            if portfolio_risk:
                var_95 = abs(portfolio_risk.get("var_95", 0))
                if var_95 > 0.05:
                    risk_assessment["overall_risk"] = "high"
                    risk_assessment["risk_factors"].append("High portfolio VaR")
                elif var_95 < 0.02:
                    risk_assessment["overall_risk"] = "low"
                
                risk_assessment["risk_score"] = min(var_95 * 10, 1.0)  # Scale VaR to 0-1
        
        # Check other agents for risk factors
        for agent_type, result in agent_results.items():
            if result.confidence < 0.3:
                risk_assessment["risk_factors"].append(f"Low confidence from {agent_type}")
        
        return risk_assessment
    
    def _generate_reasoning(self, agent_results: Dict[str, AnalysisResult], 
                          final_decision: TradeAction, consensus_score: float) -> str:
        """Generate human-readable reasoning"""
        reasoning_parts = []
        
        # Overall decision
        reasoning_parts.append(f"Final recommendation: {final_decision.value}")
        reasoning_parts.append(f"Consensus score: {consensus_score:.2f}")
        
        # Agent summaries
        for agent_type, result in agent_results.items():
            reasoning_parts.append(
                f"{agent_type}: {result.recommendation.value} "
                f"(confidence: {result.confidence:.2f}) - {result.reasoning[:100]}..."
            )
        
        return " | ".join(reasoning_parts)
    
    def _calculate_execution_priority(self, decision: TradeAction, confidence: float,
                                    consensus_score: float, risk_assessment: Dict[str, Any]) -> int:
        """Calculate execution priority (1-10)"""
        base_priority = 5
        
        # Adjust for decision type
        if decision == TradeAction.SELL:
            base_priority += 2  # Selling is often more urgent
        elif decision == TradeAction.BUY:
            base_priority += 1
        
        # Adjust for confidence
        confidence_adjustment = int((confidence - 0.5) * 4)  # -2 to +2
        base_priority += confidence_adjustment
        
        # Adjust for consensus
        consensus_adjustment = int((consensus_score - 0.5) * 2)  # -1 to +1
        base_priority += consensus_adjustment
        
        # Adjust for risk
        risk_score = risk_assessment.get("risk_score", 0.5)
        if risk_score > 0.7:
            base_priority += 2  # High risk = higher priority
        
        return max(1, min(10, base_priority))
    
    def _is_cached(self, symbol: str) -> bool:
        """Check if analysis is cached and still valid"""
        if symbol not in self.analysis_cache:
            return False
        
        cache_time = self.cache_timestamps.get(symbol)
        if not cache_time:
            return False
        
        age = (datetime.now(timezone.utc) - cache_time).total_seconds()
        return age < self.cache_duration
    
    def _cache_result(self, symbol: str, result: OrchestrationResult):
        """Cache analysis result"""
        self.analysis_cache[symbol] = result
        self.cache_timestamps[symbol] = datetime.now(timezone.utc)
    
    def _create_error_result(self, symbol: str, error_message: str) -> OrchestrationResult:
        """Create error result"""
        return OrchestrationResult(
            symbol=symbol,
            final_decision=TradeAction.HOLD,
            confidence=0.1,
            reasoning=f"Analysis failed: {error_message}",
            agent_results={},
            consensus_score=0.0,
            risk_assessment={"overall_risk": "unknown", "risk_factors": ["Analysis error"]},
            execution_priority=1,
            timestamp=datetime.now(timezone.utc)
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "is_running": self.is_running,
            "workers": len(self.workers),
            "queue_status": self.task_queue.get_status(),
            "cache_size": len(self.analysis_cache),
            "active_analyses": len(self.active_analyses)
        }
    
    def get_cached_symbols(self) -> List[str]:
        """Get list of symbols with cached analysis"""
        return list(self.analysis_cache.keys())
    
    async def clear_cache(self):
        """Clear analysis cache"""
        self.analysis_cache.clear()
        self.cache_timestamps.clear()
        logger.info("Cleared analysis cache")

