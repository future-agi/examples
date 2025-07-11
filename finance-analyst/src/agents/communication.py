"""
Agent communication protocol and event system
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import weakref

from src.utils.logging import get_component_logger

logger = get_component_logger("agent_communication")


class EventType(Enum):
    """Types of events in the system"""
    MARKET_UPDATE = "market_update"
    TRADE_SIGNAL = "trade_signal"
    RISK_ALERT = "risk_alert"
    ANALYSIS_COMPLETE = "analysis_complete"
    AGENT_STATUS = "agent_status"
    SYSTEM_STATUS = "system_status"
    PORTFOLIO_UPDATE = "portfolio_update"
    ORDER_EXECUTION = "order_execution"
    ERROR_OCCURRED = "error_occurred"


class Priority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TradingEvent:
    """Trading system event"""
    event_id: str
    event_type: EventType
    source_agent: str
    target_agents: Optional[List[str]]  # None means broadcast to all
    payload: Dict[str, Any]
    priority: Priority
    timestamp: datetime
    correlation_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source_agent": self.source_agent,
            "target_agents": self.target_agents,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingEvent':
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            source_agent=data["source_agent"],
            target_agents=data["target_agents"],
            payload=data["payload"],
            priority=Priority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )


class EventHandler:
    """Base class for event handlers"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.subscriptions: Set[EventType] = set()
    
    async def handle_event(self, event: TradingEvent) -> Optional[TradingEvent]:
        """Handle an incoming event. Return response event if needed."""
        pass
    
    def subscribe_to(self, event_type: EventType):
        """Subscribe to an event type"""
        self.subscriptions.add(event_type)
    
    def unsubscribe_from(self, event_type: EventType):
        """Unsubscribe from an event type"""
        self.subscriptions.discard(event_type)


class MessageBroker:
    """In-memory message broker for agent communication"""
    
    def __init__(self):
        self.handlers: Dict[str, EventHandler] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.event_history: List[TradingEvent] = []
        self.max_history_size = 10000
        
        logger.info("Message broker initialized")
    
    def register_handler(self, handler: EventHandler):
        """Register an event handler"""
        self.handlers[handler.agent_name] = handler
        logger.info(f"Registered handler for agent: {handler.agent_name}")
    
    def unregister_handler(self, agent_name: str):
        """Unregister an event handler"""
        if agent_name in self.handlers:
            del self.handlers[agent_name]
            logger.info(f"Unregistered handler for agent: {agent_name}")
    
    async def publish_event(self, event: TradingEvent):
        """Publish an event to the broker"""
        # Add to event history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        
        # Add to processing queue
        await self.event_queue.put(event)
        
        logger.info(f"Published event: {event.event_type.value} from {event.source_agent}")
    
    async def start(self):
        """Start the message broker"""
        if self.running:
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._process_events())
        logger.info("Message broker started")
    
    async def stop(self):
        """Stop the message broker"""
        if not self.running:
            return
        
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Message broker stopped")
    
    async def _process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                # Get event with timeout to allow for graceful shutdown
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._route_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _route_event(self, event: TradingEvent):
        """Route event to appropriate handlers"""
        # Check if event has expired
        if event.expires_at and datetime.now(timezone.utc) > event.expires_at:
            logger.warning(f"Event {event.event_id} expired, discarding")
            return
        
        # Determine target handlers
        target_handlers = []
        
        if event.target_agents:
            # Specific targets
            for agent_name in event.target_agents:
                if agent_name in self.handlers:
                    handler = self.handlers[agent_name]
                    if event.event_type in handler.subscriptions:
                        target_handlers.append(handler)
        else:
            # Broadcast to all subscribed handlers
            for handler in self.handlers.values():
                if event.event_type in handler.subscriptions:
                    target_handlers.append(handler)
        
        # Process handlers concurrently
        if target_handlers:
            tasks = [self._handle_event_safely(handler, event) for handler in target_handlers]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process any response events
            for response in responses:
                if isinstance(response, TradingEvent):
                    await self.publish_event(response)
                elif isinstance(response, Exception):
                    logger.error(f"Handler error: {response}")
    
    async def _handle_event_safely(self, handler: EventHandler, event: TradingEvent) -> Optional[TradingEvent]:
        """Handle event with error protection"""
        try:
            return await handler.handle_event(event)
        except Exception as e:
            logger.error(f"Error in handler {handler.agent_name}: {e}")
            return None
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         agent_name: Optional[str] = None, 
                         limit: int = 100) -> List[TradingEvent]:
        """Get event history with optional filtering"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if agent_name:
            events = [e for e in events if e.source_agent == agent_name]
        
        return events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics"""
        return {
            "running": self.running,
            "registered_handlers": len(self.handlers),
            "queue_size": self.event_queue.qsize(),
            "event_history_size": len(self.event_history),
            "handlers": list(self.handlers.keys())
        }


class AgentCommunicator:
    """Communication interface for agents"""
    
    def __init__(self, agent_name: str, broker: MessageBroker):
        self.agent_name = agent_name
        self.broker = broker
        self.handler = EventHandler(agent_name)
        self.broker.register_handler(self.handler)
    
    def subscribe_to_events(self, event_types: List[EventType]):
        """Subscribe to multiple event types"""
        for event_type in event_types:
            self.handler.subscribe_to(event_type)
    
    def set_event_handler(self, handler_func: Callable[[TradingEvent], Optional[TradingEvent]]):
        """Set custom event handler function"""
        async def async_handler(event: TradingEvent) -> Optional[TradingEvent]:
            return handler_func(event)
        
        self.handler.handle_event = async_handler
    
    async def send_market_update(self, symbol: str, price_data: Dict[str, Any], 
                               target_agents: Optional[List[str]] = None):
        """Send market update event"""
        event = TradingEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MARKET_UPDATE,
            source_agent=self.agent_name,
            target_agents=target_agents,
            payload={
                "symbol": symbol,
                "price_data": price_data
            },
            priority=Priority.NORMAL,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.broker.publish_event(event)
    
    async def send_trade_signal(self, symbol: str, action: str, confidence: float,
                              reasoning: str, target_agents: Optional[List[str]] = None):
        """Send trade signal event"""
        event = TradingEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.TRADE_SIGNAL,
            source_agent=self.agent_name,
            target_agents=target_agents,
            payload={
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning
            },
            priority=Priority.HIGH,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.broker.publish_event(event)
    
    async def send_risk_alert(self, alert_type: str, severity: str, message: str,
                            data: Optional[Dict[str, Any]] = None):
        """Send risk alert event"""
        event = TradingEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.RISK_ALERT,
            source_agent=self.agent_name,
            target_agents=None,  # Broadcast to all
            payload={
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "data": data or {}
            },
            priority=Priority.CRITICAL,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.broker.publish_event(event)
    
    async def send_analysis_complete(self, symbol: str, analysis_result: Dict[str, Any],
                                   correlation_id: Optional[str] = None):
        """Send analysis complete event"""
        event = TradingEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ANALYSIS_COMPLETE,
            source_agent=self.agent_name,
            target_agents=None,
            payload={
                "symbol": symbol,
                "analysis_result": analysis_result
            },
            priority=Priority.NORMAL,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id
        )
        
        await self.broker.publish_event(event)
    
    async def request_analysis(self, symbol: str, analysis_type: str, 
                             target_agent: str, timeout_seconds: int = 30) -> Optional[Dict[str, Any]]:
        """Request analysis from another agent and wait for response"""
        correlation_id = str(uuid.uuid4())
        
        # Send request
        request_event = TradingEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MARKET_UPDATE,  # Using as request type
            source_agent=self.agent_name,
            target_agents=[target_agent],
            payload={
                "symbol": symbol,
                "analysis_type": analysis_type,
                "request_type": "analysis_request"
            },
            priority=Priority.HIGH,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id
        )
        
        await self.broker.publish_event(request_event)
        
        # Wait for response
        start_time = datetime.now(timezone.utc)
        while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout_seconds:
            # Check event history for response
            for event in self.broker.get_event_history(EventType.ANALYSIS_COMPLETE):
                if (event.correlation_id == correlation_id and 
                    event.source_agent == target_agent):
                    return event.payload.get("analysis_result")
            
            await asyncio.sleep(0.1)
        
        logger.warning(f"Analysis request timeout for {symbol} from {target_agent}")
        return None
    
    def disconnect(self):
        """Disconnect from the broker"""
        self.broker.unregister_handler(self.agent_name)


# Global message broker instance
message_broker = MessageBroker()


async def start_communication_system():
    """Start the global communication system"""
    await message_broker.start()


async def stop_communication_system():
    """Stop the global communication system"""
    await message_broker.stop()


def get_communicator(agent_name: str) -> AgentCommunicator:
    """Get a communicator for an agent"""
    return AgentCommunicator(agent_name, message_broker)

