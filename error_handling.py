"""
Enhanced error handling and recovery utilities.

This module provides:
- Retry logic with exponential backoff
- Error classification and handling
- Integration with the typed exception hierarchy
- Structured logging for errors

Usage:
    from error_handling import retry_with_backoff, ErrorHandler
    from exceptions import APIError, RateLimitError

    @retry_with_backoff(retryable_exceptions=(APIError, RateLimitError))
    def call_api():
        ...
"""
import logging
import time
from typing import Callable, Any, Optional, TypeVar, Tuple, Dict, Type
from functools import wraps
from enum import Enum

from exceptions import (
    PromptOptimizerError,
    APIError,
    RateLimitError,
    APITimeoutError,
    ServiceUnavailableError,
    ValidationError,
    DatabaseError,
    AgentError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for logging and alerting."""
    LOW = "low"        # Recoverable, minor impact
    MEDIUM = "medium"  # Degraded functionality
    HIGH = "high"      # Feature unavailable
    CRITICAL = "critical"  # System failure


class RetryStrategy:
    """Retry strategy configuration."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        import random
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)  # Add 50% jitter
        return delay


def retry_with_backoff(
    strategy: Optional[RetryStrategy] = None,
    retryable_exceptions: Tuple[Exception, ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        strategy: Retry strategy configuration
        retryable_exceptions: Tuple of exceptions that should trigger retry
        on_retry: Optional callback called before each retry
    """
    if strategy is None:
        strategy = RetryStrategy()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(strategy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < strategy.max_retries:
                        delay = strategy.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{strategy.max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        if on_retry:
                            on_retry(attempt + 1, e)
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {strategy.max_retries + 1} attempts failed for {func.__name__}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


class ErrorHandler:
    """Centralized error handling."""

    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> str:
        """
        Handle API errors with user-friendly messages.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            User-friendly error message
        """
        error_msg = str(error).lower()

        if "timeout" in error_msg or "timed out" in error_msg:
            return f"Request timed out. The API is taking longer than expected. Please try again.{' ' + context if context else ''}"

        if "401" in error_msg or "unauthorized" in error_msg:
            return "Authentication failed. Please check your API key configuration."

        if "429" in error_msg or "rate limit" in error_msg:
            return "Rate limit exceeded. Please wait a moment and try again."

        if "500" in error_msg or "internal server error" in error_msg:
            return "The API service is experiencing issues. Please try again later."

        if "connection" in error_msg or "network" in error_msg:
            return "Network connection error. Please check your internet connection and try again."

        # Generic error
        return f"An error occurred: {str(error)}. Please try again.{' ' + context if context else ''}"

    @staticmethod
    def log_error(
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error with appropriate level.
        
        Args:
            error: The exception
            severity: Error severity level
            context: Additional context dictionary
        """
        context_str = f" Context: {context}" if context else ""

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {str(error)}{context_str}", exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {str(error)}{context_str}", exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {str(error)}{context_str}", exc_info=True)
        else:
            logger.info(f"LOW SEVERITY ERROR: {str(error)}{context_str}")


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    error_message: Optional[str] = None,
    log_error: bool = True,
    reraise_types: Tuple[Type[Exception], ...] = ()
) -> Optional[T]:
    """
    Safely execute a function, returning default on error.

    Args:
        func: Function to execute
        default: Default value to return on error
        error_message: Custom error message
        log_error: Whether to log errors
        reraise_types: Exception types that should be re-raised instead of caught

    Returns:
        Function result or default value
    """
    try:
        return func()
    except reraise_types:
        raise
    except Exception as e:
        if log_error:
            logger.error(f"Error in safe_execute: {str(e)}", exc_info=True)
        if error_message:
            logger.error(error_message)
        return default


# =============================================================================
# Exception Severity Mapping
# =============================================================================

EXCEPTION_SEVERITY_MAP: Dict[Type[Exception], ErrorSeverity] = {
    # Critical - system cannot function
    DatabaseError: ErrorSeverity.CRITICAL,

    # High - major feature unavailable
    APIError: ErrorSeverity.HIGH,
    AgentError: ErrorSeverity.HIGH,

    # Medium - degraded but functional
    RateLimitError: ErrorSeverity.MEDIUM,
    ServiceUnavailableError: ErrorSeverity.MEDIUM,
    APITimeoutError: ErrorSeverity.MEDIUM,

    # Low - minor issues
    ValidationError: ErrorSeverity.LOW,
}


def get_exception_severity(exception: Exception) -> ErrorSeverity:
    """
    Get the severity level for an exception.

    Args:
        exception: The exception to classify

    Returns:
        ErrorSeverity enum value
    """
    for exc_type, severity in EXCEPTION_SEVERITY_MAP.items():
        if isinstance(exception, exc_type):
            return severity
    return ErrorSeverity.MEDIUM  # Default


# =============================================================================
# Default Retryable Exceptions
# =============================================================================

DEFAULT_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    APITimeoutError,
    RateLimitError,
    ServiceUnavailableError,
    ConnectionError,
    TimeoutError,
)


def is_retryable(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.

    Args:
        exception: The exception to check

    Returns:
        True if the exception is retryable
    """
    # Check if it's a known retryable type
    if isinstance(exception, DEFAULT_RETRYABLE_EXCEPTIONS):
        return True

    # Check error message for retryable patterns
    error_msg = str(exception).lower()
    retryable_patterns = [
        "timeout",
        "connection",
        "rate limit",
        "503",
        "502",
        "504",
        "temporarily unavailable",
        "try again",
    ]

    return any(pattern in error_msg for pattern in retryable_patterns)


# =============================================================================
# Enhanced Error Handler
# =============================================================================

class EnhancedErrorHandler(ErrorHandler):
    """
    Extended error handler with additional capabilities.

    Provides:
    - Exception classification
    - Structured error context
    - Integration with monitoring
    """

    @staticmethod
    def classify_exception(exception: Exception) -> PromptOptimizerError:
        """
        Classify a generic exception into a typed exception.

        Args:
            exception: The exception to classify

        Returns:
            A properly typed PromptOptimizerError
        """
        if isinstance(exception, PromptOptimizerError):
            return exception

        error_msg = str(exception).lower()

        # Classify based on error message patterns
        if "timeout" in error_msg:
            return APITimeoutError(str(exception), original_error=exception)

        if "rate limit" in error_msg or "429" in error_msg:
            return RateLimitError(str(exception), original_error=exception)

        if "401" in error_msg or "unauthorized" in error_msg:
            from exceptions import AuthenticationError
            return AuthenticationError(str(exception), original_error=exception)

        if "database" in error_msg or "sql" in error_msg:
            from exceptions import DatabaseQueryError
            return DatabaseQueryError(str(exception), original_error=exception)

        if "validation" in error_msg or "invalid" in error_msg:
            return ValidationError(str(exception), original_error=exception)

        # Default to generic API error
        return APIError(str(exception), original_error=exception)

    @staticmethod
    def format_error_context(
        exception: Exception,
        operation: str,
        **additional_context
    ) -> Dict[str, Any]:
        """
        Format error context for logging and monitoring.

        Args:
            exception: The exception
            operation: Name of the operation that failed
            **additional_context: Additional context values

        Returns:
            Structured context dictionary
        """
        context = {
            "operation": operation,
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "severity": get_exception_severity(exception).value,
            "retryable": is_retryable(exception),
        }

        if isinstance(exception, PromptOptimizerError):
            context["error_code"] = exception.code.name
            context["error_code_value"] = exception.code.value
            context.update(exception.context)

        context.update(additional_context)
        return context


# Backwards compatibility alias
error_handler = EnhancedErrorHandler()
