"""
Logging configuration for the Multi-Agent AI Trading System
"""
import os
import sys
import logging
import structlog
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from config.settings import config


class TradingSystemLogger:
    """Custom logger for the trading system with structured logging"""
    
    def __init__(self, name: str = "trading_system"):
        self.name = name
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging with appropriate handlers"""
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Setup standard logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, config.log_level.upper())
        )
        
        # Create file handler for persistent logging
        file_handler = logging.FileHandler(
            log_dir / config.log_file,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    def get_logger(self, component: str) -> structlog.BoundLogger:
        """Get a logger for a specific component"""
        return structlog.get_logger(f"{self.name}.{component}")


class AgentLogger:
    """Specialized logger for trading agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = structlog.get_logger(f"agent.{agent_name}")
    
    def log_analysis(self, symbol: str, analysis_type: str, result: Dict[str, Any]):
        """Log analysis results"""
        self.logger.info(
            "analysis_completed",
            agent=self.agent_name,
            symbol=symbol,
            analysis_type=analysis_type,
            result=result,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_decision(self, symbol: str, decision: str, confidence: float, reasoning: str):
        """Log trading decisions"""
        self.logger.info(
            "trading_decision",
            agent=self.agent_name,
            symbol=symbol,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log errors with context"""
        self.logger.error(
            "agent_error",
            agent=self.agent_name,
            error=str(error),
            error_type=type(error).__name__,
            context=context or {},
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_performance(self, metrics: Dict[str, float]):
        """Log performance metrics"""
        self.logger.info(
            "performance_metrics",
            agent=self.agent_name,
            metrics=metrics,
            timestamp=datetime.utcnow().isoformat()
        )


class TradingLogger:
    """Logger for trading operations"""
    
    def __init__(self):
        self.logger = structlog.get_logger("trading")
    
    def log_trade_execution(self, symbol: str, action: str, quantity: float, 
                          price: float, order_id: str):
        """Log trade execution"""
        self.logger.info(
            "trade_executed",
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            order_id=order_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_risk_alert(self, alert_type: str, severity: str, message: str, 
                      data: Optional[Dict[str, Any]] = None):
        """Log risk management alerts"""
        self.logger.warning(
            "risk_alert",
            alert_type=alert_type,
            severity=severity,
            message=message,
            data=data or {},
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_portfolio_update(self, portfolio_value: float, positions: Dict[str, Any]):
        """Log portfolio updates"""
        self.logger.info(
            "portfolio_update",
            portfolio_value=portfolio_value,
            positions=positions,
            timestamp=datetime.utcnow().isoformat()
        )


class SystemLogger:
    """Logger for system-level events"""
    
    def __init__(self):
        self.logger = structlog.get_logger("system")
    
    def log_startup(self, component: str, version: str):
        """Log system startup"""
        self.logger.info(
            "system_startup",
            component=component,
            version=version,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_shutdown(self, component: str, reason: str):
        """Log system shutdown"""
        self.logger.info(
            "system_shutdown",
            component=component,
            reason=reason,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_health_check(self, component: str, status: str, metrics: Dict[str, Any]):
        """Log health check results"""
        self.logger.info(
            "health_check",
            component=component,
            status=status,
            metrics=metrics,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_configuration_change(self, component: str, changes: Dict[str, Any]):
        """Log configuration changes"""
        self.logger.info(
            "configuration_change",
            component=component,
            changes=changes,
            timestamp=datetime.utcnow().isoformat()
        )


class AuditLogger:
    """Logger for audit and compliance"""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_user_action(self, user_id: str, action: str, resource: str, 
                       result: str, ip_address: Optional[str] = None):
        """Log user actions for audit trail"""
        self.logger.info(
            "user_action",
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_data_access(self, user_id: str, data_type: str, query: str, 
                       record_count: int):
        """Log data access for compliance"""
        self.logger.info(
            "data_access",
            user_id=user_id,
            data_type=data_type,
            query=query,
            record_count=record_count,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_compliance_check(self, check_type: str, result: str, 
                           details: Dict[str, Any]):
        """Log compliance checks"""
        self.logger.info(
            "compliance_check",
            check_type=check_type,
            result=result,
            details=details,
            timestamp=datetime.utcnow().isoformat()
        )


# Global logger instances
trading_logger = TradingSystemLogger()
system_logger = SystemLogger()
trading_ops_logger = TradingLogger()
audit_logger = AuditLogger()


def get_agent_logger(agent_name: str) -> AgentLogger:
    """Get a logger for a specific agent"""
    return AgentLogger(agent_name)


def get_component_logger(component_name: str) -> structlog.BoundLogger:
    """Get a logger for a specific component"""
    return trading_logger.get_logger(component_name)

