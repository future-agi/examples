"""
Monitoring and Alerting System for the Multi-Agent AI Trading System
"""
import time
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import json
import sqlite3
from pathlib import Path

from src.utils.logging import get_component_logger

logger = get_component_logger("monitor")


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "tags": self.tags
        }


@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    metric: str
    condition: str  # "gt", "lt", "eq", "ne"
    threshold: float
    duration: int  # seconds
    severity: str  # "low", "medium", "high", "critical"
    enabled: bool
    last_triggered: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.last_triggered:
            data["last_triggered"] = self.last_triggered.isoformat()
        return data


@dataclass
class AlertEvent:
    """Alert event when threshold is breached"""
    alert_id: str
    alert_name: str
    metric: str
    value: float
    threshold: float
    condition: str
    severity: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if self.resolved_at:
            data["resolved_at"] = self.resolved_at.isoformat()
        return data


class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 points
        self.lock = threading.Lock()
        
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        try:
            with self.lock:
                metric_point = MetricPoint(
                    timestamp=datetime.now(timezone.utc),
                    value=value,
                    tags=tags or {}
                )
                self.metrics[name].append(metric_point)
                
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")
    
    def get_metric_history(self, name: str, duration_minutes: int = 60) -> List[MetricPoint]:
        """Get metric history for specified duration"""
        try:
            with self.lock:
                if name not in self.metrics:
                    return []
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
                return [
                    point for point in self.metrics[name]
                    if point.timestamp >= cutoff_time
                ]
                
        except Exception as e:
            logger.error(f"Error getting metric history for {name}: {e}")
            return []
    
    def get_latest_metric(self, name: str) -> Optional[MetricPoint]:
        """Get latest metric value"""
        try:
            with self.lock:
                if name not in self.metrics or not self.metrics[name]:
                    return None
                return self.metrics[name][-1]
                
        except Exception as e:
            logger.error(f"Error getting latest metric for {name}: {e}")
            return None
    
    def get_metric_average(self, name: str, duration_minutes: int = 60) -> Optional[float]:
        """Get average metric value over duration"""
        try:
            history = self.get_metric_history(name, duration_minutes)
            if not history:
                return None
            
            return sum(point.value for point in history) / len(history)
            
        except Exception as e:
            logger.error(f"Error calculating average for {name}: {e}")
            return None
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("system.cpu.usage", cpu_percent, {"unit": "percent"})
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric("system.memory.usage", memory.percent, {"unit": "percent"})
            self.record_metric("system.memory.available", memory.available / (1024**3), {"unit": "GB"})
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric("system.disk.usage", disk_percent, {"unit": "percent"})
            self.record_metric("system.disk.free", disk.free / (1024**3), {"unit": "GB"})
            
            # Network I/O
            network = psutil.net_io_counters()
            self.record_metric("system.network.bytes_sent", network.bytes_sent, {"unit": "bytes"})
            self.record_metric("system.network.bytes_recv", network.bytes_recv, {"unit": "bytes"})
            
            # Process count
            process_count = len(psutil.pids())
            self.record_metric("system.processes.count", process_count, {"unit": "count"})
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all metrics as dictionary"""
        try:
            with self.lock:
                result = {}
                for name, points in self.metrics.items():
                    result[name] = [point.to_dict() for point in points]
                return result
                
        except Exception as e:
            logger.error(f"Error getting all metrics: {e}")
            return {}


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts = {}
        self.alert_events = deque(maxlen=1000)  # Keep last 1000 events
        self.alert_states = {}  # Track alert states for duration checking
        self.callbacks = []  # Alert callbacks
        self.lock = threading.Lock()
        
        # Create default alerts
        self._create_default_alerts()
    
    def _create_default_alerts(self):
        """Create default system alerts"""
        default_alerts = [
            Alert(
                id="high_cpu",
                name="High CPU Usage",
                metric="system.cpu.usage",
                condition="gt",
                threshold=80.0,
                duration=300,  # 5 minutes
                severity="high",
                enabled=True
            ),
            Alert(
                id="high_memory",
                name="High Memory Usage",
                metric="system.memory.usage",
                condition="gt",
                threshold=85.0,
                duration=300,
                severity="high",
                enabled=True
            ),
            Alert(
                id="low_disk_space",
                name="Low Disk Space",
                metric="system.disk.usage",
                condition="gt",
                threshold=90.0,
                duration=600,  # 10 minutes
                severity="critical",
                enabled=True
            ),
            Alert(
                id="analysis_error_rate",
                name="High Analysis Error Rate",
                metric="trading.analysis.error_rate",
                condition="gt",
                threshold=10.0,  # 10% error rate
                duration=300,
                severity="medium",
                enabled=True
            )
        ]
        
        for alert in default_alerts:
            self.alerts[alert.id] = alert
    
    def add_alert(self, alert: Alert) -> bool:
        """Add new alert"""
        try:
            with self.lock:
                self.alerts[alert.id] = alert
                logger.info(f"Added alert: {alert.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding alert {alert.id}: {e}")
            return False
    
    def remove_alert(self, alert_id: str) -> bool:
        """Remove alert"""
        try:
            with self.lock:
                if alert_id in self.alerts:
                    del self.alerts[alert_id]
                    self.alert_states.pop(alert_id, None)
                    logger.info(f"Removed alert: {alert_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error removing alert {alert_id}: {e}")
            return False
    
    def update_alert(self, alert_id: str, **kwargs) -> bool:
        """Update alert configuration"""
        try:
            with self.lock:
                if alert_id not in self.alerts:
                    return False
                
                alert = self.alerts[alert_id]
                for key, value in kwargs.items():
                    if hasattr(alert, key):
                        setattr(alert, key, value)
                
                logger.info(f"Updated alert: {alert_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {e}")
            return False
    
    def check_alerts(self):
        """Check all alerts against current metrics"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for alert in self.alerts.values():
                if not alert.enabled:
                    continue
                
                # Get latest metric value
                latest_metric = self.metrics_collector.get_latest_metric(alert.metric)
                if not latest_metric:
                    continue
                
                # Check condition
                triggered = self._check_condition(latest_metric.value, alert.condition, alert.threshold)
                
                # Track alert state for duration checking
                if alert.id not in self.alert_states:
                    self.alert_states[alert.id] = {
                        "triggered": False,
                        "first_triggered": None,
                        "last_checked": current_time
                    }
                
                state = self.alert_states[alert.id]
                
                if triggered:
                    if not state["triggered"]:
                        # First time triggered
                        state["triggered"] = True
                        state["first_triggered"] = current_time
                    elif state["first_triggered"]:
                        # Check if duration threshold is met
                        duration = (current_time - state["first_triggered"]).total_seconds()
                        if duration >= alert.duration:
                            # Fire alert
                            self._fire_alert(alert, latest_metric.value, current_time)
                            alert.last_triggered = current_time
                            # Reset state to avoid repeated firing
                            state["first_triggered"] = current_time
                else:
                    # Reset state if not triggered
                    if state["triggered"]:
                        state["triggered"] = False
                        state["first_triggered"] = None
                
                state["last_checked"] = current_time
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Check if value meets alert condition"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.001  # Float equality with tolerance
        elif condition == "ne":
            return abs(value - threshold) >= 0.001
        else:
            return False
    
    def _fire_alert(self, alert: Alert, value: float, timestamp: datetime):
        """Fire an alert"""
        try:
            alert_event = AlertEvent(
                alert_id=alert.id,
                alert_name=alert.name,
                metric=alert.metric,
                value=value,
                threshold=alert.threshold,
                condition=alert.condition,
                severity=alert.severity,
                timestamp=timestamp
            )
            
            with self.lock:
                self.alert_events.append(alert_event)
            
            logger.warning(f"ALERT: {alert.name} - {alert.metric} = {value} {alert.condition} {alert.threshold}")
            
            # Call registered callbacks
            for callback in self.callbacks:
                try:
                    callback(alert_event)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error firing alert {alert.id}: {e}")
    
    def add_callback(self, callback: Callable[[AlertEvent], None]):
        """Add alert callback function"""
        self.callbacks.append(callback)
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts"""
        with self.lock:
            return [alert.to_dict() for alert in self.alerts.values()]
    
    def get_alert_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert events"""
        with self.lock:
            events = list(self.alert_events)[-limit:]
            return [event.to_dict() for event in events]
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        active_alerts = []
        current_time = datetime.now(timezone.utc)
        
        for alert_id, state in self.alert_states.items():
            if state.get("triggered", False):
                alert = self.alerts.get(alert_id)
                if alert:
                    active_alerts.append({
                        "alert": alert.to_dict(),
                        "triggered_at": state.get("first_triggered", current_time).isoformat(),
                        "duration": (current_time - state.get("first_triggered", current_time)).total_seconds()
                    })
        
        return active_alerts


class TradingMetrics:
    """Trading-specific metrics collector"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.analysis_count = 0
        self.analysis_errors = 0
        self.api_calls = defaultdict(int)
        self.response_times = defaultdict(list)
        
    def record_analysis_request(self, symbol: str):
        """Record analysis request"""
        self.analysis_count += 1
        self.metrics_collector.record_metric(
            "trading.analysis.requests",
            self.analysis_count,
            {"symbol": symbol}
        )
    
    def record_analysis_error(self, symbol: str, error_type: str):
        """Record analysis error"""
        self.analysis_errors += 1
        error_rate = (self.analysis_errors / max(self.analysis_count, 1)) * 100
        
        self.metrics_collector.record_metric(
            "trading.analysis.errors",
            self.analysis_errors,
            {"symbol": symbol, "error_type": error_type}
        )
        
        self.metrics_collector.record_metric(
            "trading.analysis.error_rate",
            error_rate,
            {"unit": "percent"}
        )
    
    def record_api_call(self, api_name: str, response_time: float, success: bool):
        """Record API call metrics"""
        self.api_calls[api_name] += 1
        self.response_times[api_name].append(response_time)
        
        # Keep only last 100 response times
        if len(self.response_times[api_name]) > 100:
            self.response_times[api_name] = self.response_times[api_name][-100:]
        
        self.metrics_collector.record_metric(
            f"api.{api_name}.calls",
            self.api_calls[api_name],
            {"success": str(success)}
        )
        
        self.metrics_collector.record_metric(
            f"api.{api_name}.response_time",
            response_time,
            {"unit": "seconds"}
        )
        
        # Calculate average response time
        avg_response_time = sum(self.response_times[api_name]) / len(self.response_times[api_name])
        self.metrics_collector.record_metric(
            f"api.{api_name}.avg_response_time",
            avg_response_time,
            {"unit": "seconds"}
        )
    
    def record_agent_performance(self, agent_type: str, confidence: float, processing_time: float):
        """Record agent performance metrics"""
        self.metrics_collector.record_metric(
            f"agent.{agent_type}.confidence",
            confidence,
            {"unit": "score"}
        )
        
        self.metrics_collector.record_metric(
            f"agent.{agent_type}.processing_time",
            processing_time,
            {"unit": "seconds"}
        )
    
    def record_orchestrator_metrics(self, queue_size: int, active_workers: int, cache_size: int):
        """Record orchestrator metrics"""
        self.metrics_collector.record_metric(
            "orchestrator.queue_size",
            queue_size,
            {"unit": "count"}
        )
        
        self.metrics_collector.record_metric(
            "orchestrator.active_workers",
            active_workers,
            {"unit": "count"}
        )
        
        self.metrics_collector.record_metric(
            "orchestrator.cache_size",
            cache_size,
            {"unit": "count"}
        )


class MonitoringSystem:
    """Main monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.trading_metrics = TradingMetrics(self.metrics_collector)
        
        self.is_running = False
        self.monitor_thread = None
        self.collection_interval = 30  # 30 seconds
        
        # Setup alert callbacks
        self.alert_manager.add_callback(self._log_alert)
        
        logger.info("Monitoring system initialized")
    
    def start(self):
        """Start monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Monitoring system started")
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Monitoring system stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                self.metrics_collector.collect_system_metrics()
                
                # Check alerts
                self.alert_manager.check_alerts()
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retrying
    
    def _log_alert(self, alert_event: AlertEvent):
        """Log alert event"""
        logger.warning(
            f"ALERT FIRED: {alert_event.alert_name} - "
            f"{alert_event.metric} = {alert_event.value} "
            f"({alert_event.condition} {alert_event.threshold}) "
            f"Severity: {alert_event.severity}"
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            # Get latest system metrics
            cpu_usage = self.metrics_collector.get_latest_metric("system.cpu.usage")
            memory_usage = self.metrics_collector.get_latest_metric("system.memory.usage")
            disk_usage = self.metrics_collector.get_latest_metric("system.disk.usage")
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            
            # Determine overall health
            health = "healthy"
            if active_alerts:
                severities = [alert["alert"]["severity"] for alert in active_alerts]
                if "critical" in severities:
                    health = "critical"
                elif "high" in severities:
                    health = "degraded"
                elif "medium" in severities:
                    health = "warning"
            
            return {
                "health": health,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_metrics": {
                    "cpu_usage": cpu_usage.value if cpu_usage else None,
                    "memory_usage": memory_usage.value if memory_usage else None,
                    "disk_usage": disk_usage.value if disk_usage else None
                },
                "active_alerts": len(active_alerts),
                "monitoring_status": "running" if self.is_running else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "health": "unknown",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global monitoring system instance
monitoring_system = MonitoringSystem()

