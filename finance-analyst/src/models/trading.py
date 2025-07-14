"""
Database models for the Multi-Agent AI Trading System
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from src.models.user import db


class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AgentType(Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    ORCHESTRATOR = "orchestrator"


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Portfolio(db.Model):
    """Portfolio model for tracking investment portfolios"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    initial_capital = Column(Float, nullable=False, default=1000000.0)
    current_value = Column(Float, nullable=False, default=1000000.0)
    cash_balance = Column(Float, nullable=False, default=1000000.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Portfolio {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'initial_capital': self.initial_capital,
            'current_value': self.current_value,
            'cash_balance': self.cash_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


class Position(db.Model):
    """Position model for tracking individual stock positions"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    average_cost = Column(Float, nullable=False, default=0.0)
    current_price = Column(Float, nullable=False, default=0.0)
    market_value = Column(Float, nullable=False, default=0.0)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    
    def __repr__(self):
        return f'<Position {self.symbol}: {self.quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_cost': self.average_cost,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Trade(db.Model):
    """Trade model for tracking individual trades"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    action = Column(SQLEnum(TradeAction), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    commission = Column(Float, nullable=False, default=0.0)
    status = Column(SQLEnum(TradeStatus), nullable=False, default=TradeStatus.PENDING)
    order_id = Column(String(100))
    execution_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Agent decision tracking
    agent_decisions = relationship("AgentDecision", back_populates="trade", cascade="all, delete-orphan")
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
    
    def __repr__(self):
        return f'<Trade {self.action.value} {self.quantity} {self.symbol} @ {self.price}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'symbol': self.symbol,
            'action': self.action.value,
            'quantity': self.quantity,
            'price': self.price,
            'total_value': self.total_value,
            'commission': self.commission,
            'status': self.status.value,
            'order_id': self.order_id,
            'execution_time': self.execution_time.isoformat() if self.execution_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MarketData(db.Model):
    """Market data model for storing price and volume information"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Float)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<MarketData {self.symbol} {self.timestamp} {self.close_price}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'adjusted_close': self.adjusted_close,
            'timeframe': self.timeframe,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentDecision(db.Model):
    """Agent decision model for tracking AI agent recommendations"""
    __tablename__ = 'agent_decisions'
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    symbol = Column(String(20), nullable=False)
    recommendation = Column(SQLEnum(TradeAction), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    reasoning = Column(Text)
    analysis_data = Column(JSON)  # Store detailed analysis results
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    trade = relationship("Trade", back_populates="agent_decisions")
    
    def __repr__(self):
        return f'<AgentDecision {self.agent_type.value} {self.symbol} {self.recommendation.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'agent_type': self.agent_type.value,
            'symbol': self.symbol,
            'recommendation': self.recommendation.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'analysis_data': self.analysis_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class RiskAlert(db.Model):
    """Risk alert model for tracking risk management alerts"""
    __tablename__ = 'risk_alerts'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON)  # Additional alert data
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<RiskAlert {self.alert_type} {self.severity.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'alert_type': self.alert_type,
            'severity': self.severity.value,
            'message': self.message,
            'data': self.data,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PerformanceMetrics(db.Model):
    """Performance metrics model for tracking system and portfolio performance"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True)
    metric_type = Column(String(50), nullable=False)  # sharpe_ratio, max_drawdown, etc.
    value = Column(Float, nullable=False)
    period = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    calculation_date = Column(DateTime, nullable=False)
    metric_metadata = Column(JSON)  # Additional metric data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<PerformanceMetrics {self.metric_type} {self.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'metric_type': self.metric_type,
            'value': self.value,
            'period': self.period,
            'calculation_date': self.calculation_date.isoformat() if self.calculation_date else None,
            'metric_metadata': self.metric_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemHealth(db.Model):
    """System health model for monitoring system status"""
    __tablename__ = 'system_health'
    
    id = Column(Integer, primary_key=True)
    component = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # healthy, warning, critical
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    response_time = Column(Float)  # in milliseconds
    error_rate = Column(Float)  # percentage
    additional_metrics = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<SystemHealth {self.component} {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'component': self.component,
            'status': self.status,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'response_time': self.response_time,
            'error_rate': self.error_rate,
            'additional_metrics': self.additional_metrics,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class AuditLog(db.Model):
    """Audit log model for compliance and security tracking"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100))
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    result = Column(String(20), nullable=False)  # success, failure
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    details = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.resource} {self.result}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource': self.resource,
            'result': self.result,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

