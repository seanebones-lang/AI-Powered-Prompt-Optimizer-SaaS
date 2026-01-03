"""
Monitoring and observability utilities.
Tracks metrics, performance, and system health.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from database import db

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates application metrics."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of historical data points
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.counters[metric_name] += value
        self.metrics[metric_name].append({
            "timestamp": datetime.now(),
            "value": self.counters[metric_name],
            "type": "counter"
        })
    
    def gauge(self, metric_name: str, value: float) -> None:
        """Set a gauge metric."""
        self.gauges[metric_name] = value
        self.metrics[metric_name].append({
            "timestamp": datetime.now(),
            "value": value,
            "type": "gauge"
        })
    
    def timer(self, metric_name: str, duration: float) -> None:
        """Record a timing metric."""
        self.timers[metric_name].append(duration)
        if len(self.timers[metric_name]) > self.max_history:
            self.timers[metric_name] = self.timers[metric_name][-self.max_history:]
        
        self.metrics[metric_name].append({
            "timestamp": datetime.now(),
            "value": duration,
            "type": "timer"
        })
    
    def time_block(self, metric_name: str):
        """Context manager for timing code blocks."""
        return TimerContext(self, metric_name)
    
    def get_counter(self, metric_name: str) -> int:
        """Get current counter value."""
        return self.counters.get(metric_name, 0)
    
    def get_gauge(self, metric_name: str) -> Optional[float]:
        """Get current gauge value."""
        return self.gauges.get(metric_name)
    
    def get_timer_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a timer metric."""
        if metric_name not in self.timers or not self.timers[metric_name]:
            return {}
        
        values = self.timers[metric_name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": sorted(values)[len(values) // 2] if values else 0,
            "p95": sorted(values)[int(len(values) * 0.95)] if values else 0,
            "p99": sorted(values)[int(len(values) * 0.99)] if values else 0
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics in a structured format."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {
                name: self.get_timer_stats(name)
                for name in self.timers.keys()
            }
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.timers.clear()


class TimerContext:
    """Context manager for timing code blocks."""
    
    def __init__(self, collector: MetricsCollector, metric_name: str):
        self.collector = collector
        self.metric_name = metric_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.timer(self.metric_name, duration)


class HealthChecker:
    """Checks system health and dependencies."""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        self.checks[name] = check_func
    
    def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Dictionary with health status for each check
        """
        results = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        for name, check_func in self.checks.items():
            try:
                check_result = check_func()
                results["checks"][name] = {
                    "status": "healthy" if check_result else "unhealthy",
                    "result": check_result
                }
                if not check_result:
                    results["status"] = "degraded"
            except Exception as e:
                logger.error(f"Health check {name} failed: {str(e)}")
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["status"] = "unhealthy"
        
        return results
    
    def check_database(self) -> bool:
        """Check database connectivity."""
        try:
            db_session = db.get_session()
            db_session.execute("SELECT 1")
            db_session.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def check_api_key(self) -> bool:
        """Check if API key is configured."""
        try:
            from config import settings
            return bool(settings.xai_api_key and settings.xai_api_key != "your_xai_api_key_here")
        except Exception:
            return False


# Global instances
_metrics_collector = MetricsCollector()
_health_checker = HealthChecker()

# Register default health checks
_health_checker.register_check("database", _health_checker.check_database)
_health_checker.register_check("api_key", _health_checker.check_api_key)


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics_collector


def get_health_checker() -> HealthChecker:
    """Get global health checker."""
    return _health_checker
