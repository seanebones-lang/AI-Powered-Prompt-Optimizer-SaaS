"""
Observability module for comprehensive logging, tracing, and monitoring.

Features:
- Structured JSON logging with python-json-logger
- LLM call tracking with cost estimation
- Sentry error tracking integration
- Performance metrics and tracing
"""
import logging
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from contextlib import contextmanager
import os
import json

# Check for optional dependencies
try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


# Model pricing per 1M tokens (January 2026 pricing)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "grok-4-1-fast-reasoning": {"input": 3.00, "output": 15.00},
    "grok-4-1-fast": {"input": 2.00, "output": 10.00},
    "grok-3": {"input": 5.00, "output": 15.00},
    "grok-3-fast": {"input": 3.00, "output": 10.00},
    "grok-2": {"input": 2.00, "output": 6.00},
    "grok-vision": {"input": 5.00, "output": 15.00},
}


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM API call."""
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: Optional[str] = None
    prompt_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": round(self.latency_ms, 2),
            "cost_usd": round(self.cost_usd, 6),
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "prompt_type": self.prompt_type,
        }


class CustomJsonFormatter(jsonlogger.JsonFormatter if JSON_LOGGER_AVAILABLE else logging.Formatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Add log level
        log_record['level'] = record.levelname

        # Add source information
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Add service info
        log_record['service'] = os.getenv('SERVICE_NAME', 'prompt-optimizer')
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')


def setup_structured_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_json: bool = True
) -> logging.Logger:
    """
    Set up structured JSON logging.

    Args:
        level: Logging level
        log_file: Optional file path for log output
        enable_json: Whether to use JSON format

    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers = []

    if enable_json and JSON_LOGGER_AVAILABLE:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            json_ensure_ascii=False
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def setup_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
) -> bool:
    """
    Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Environment name
        traces_sample_rate: Sampling rate for performance monitoring
        profiles_sample_rate: Sampling rate for profiling

    Returns:
        True if Sentry was initialized successfully
    """
    if not SENTRY_AVAILABLE:
        logging.warning("Sentry SDK not available. Error tracking disabled.")
        return False

    dsn = dsn or os.getenv('SENTRY_DSN')
    if not dsn:
        logging.info("SENTRY_DSN not set. Sentry error tracking disabled.")
        return False

    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )

    sentry_sdk.init(
        dsn=dsn,
        integrations=[sentry_logging],
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        send_default_pii=False,
    )

    logging.info("Sentry error tracking initialized")
    return True


class LLMCallTracker:
    """
    Tracks LLM API calls with cost estimation and performance metrics.

    Usage:
        tracker = LLMCallTracker()

        with tracker.track_call("grok-4-1-fast", prompt_type="creative") as call:
            response = api.generate(...)
            call.set_tokens(response.usage)

        print(tracker.get_summary())
    """

    def __init__(self):
        self.calls: list[LLMCallMetrics] = []
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def track_call(
        self,
        model: str,
        prompt_type: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Context manager to track an LLM API call.

        Args:
            model: Model name
            prompt_type: Type of prompt being processed
            request_id: Optional request identifier

        Yields:
            CallContext object for setting token counts
        """
        start_time = time.perf_counter()
        metrics = LLMCallMetrics(
            model=model,
            prompt_type=prompt_type,
            request_id=request_id
        )

        context = _CallContext(metrics)

        try:
            yield context
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            raise
        finally:
            metrics.latency_ms = (time.perf_counter() - start_time) * 1000
            metrics.cost_usd = self._calculate_cost(model, metrics.prompt_tokens, metrics.completion_tokens)
            self.calls.append(metrics)

            # Log the call
            self.logger.info(
                "LLM call completed",
                extra={"llm_metrics": metrics.to_dict()}
            )

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD for the API call."""
        pricing = MODEL_PRICING.get(model, {"input": 2.0, "output": 10.0})

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all tracked calls."""
        if not self.calls:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0.0,
            }

        successful = [c for c in self.calls if c.success]
        failed = [c for c in self.calls if not c.success]

        return {
            "total_calls": len(self.calls),
            "successful_calls": len(successful),
            "failed_calls": len(failed),
            "total_prompt_tokens": sum(c.prompt_tokens for c in self.calls),
            "total_completion_tokens": sum(c.completion_tokens for c in self.calls),
            "total_tokens": sum(c.total_tokens for c in self.calls),
            "total_cost_usd": round(sum(c.cost_usd for c in self.calls), 4),
            "avg_latency_ms": round(sum(c.latency_ms for c in self.calls) / len(self.calls), 2),
            "calls_by_model": self._group_by_model(),
        }

    def _group_by_model(self) -> Dict[str, Dict[str, Any]]:
        """Group call statistics by model."""
        by_model: Dict[str, list] = {}
        for call in self.calls:
            if call.model not in by_model:
                by_model[call.model] = []
            by_model[call.model].append(call)

        result = {}
        for model, calls in by_model.items():
            result[model] = {
                "count": len(calls),
                "total_tokens": sum(c.total_tokens for c in calls),
                "total_cost_usd": round(sum(c.cost_usd for c in calls), 4),
                "avg_latency_ms": round(sum(c.latency_ms for c in calls) / len(calls), 2),
            }
        return result

    def reset(self) -> None:
        """Clear all tracked calls."""
        self.calls = []


class _CallContext:
    """Context object for setting token counts in a tracked call."""

    def __init__(self, metrics: LLMCallMetrics):
        self.metrics = metrics

    def set_tokens(self, usage: Dict[str, int]) -> None:
        """Set token counts from API response usage dict."""
        self.metrics.prompt_tokens = usage.get("prompt_tokens", 0)
        self.metrics.completion_tokens = usage.get("completion_tokens", 0)
        self.metrics.total_tokens = usage.get("total_tokens", 0)

    def set_request_id(self, request_id: str) -> None:
        """Set the request ID from API response."""
        self.metrics.request_id = request_id


def track_performance(func: Callable) -> Callable:
    """
    Decorator to track function performance.

    Logs execution time and any errors.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.debug(
                f"Function {func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "success": True,
                }
            )
            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                f"Function {func.__name__} failed: {str(e)}",
                extra={
                    "function": func.__name__,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "success": False,
                    "error": str(e),
                }
            )
            raise

    return wrapper


# Global tracker instance
llm_tracker = LLMCallTracker()


def get_tracker() -> LLMCallTracker:
    """Get the global LLM call tracker."""
    return llm_tracker


# Initialize logging on import if not in testing mode
if os.getenv("TESTING") != "1":
    setup_structured_logging()
