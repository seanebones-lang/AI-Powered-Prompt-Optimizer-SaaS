"""
Enhanced error handling and recovery utilities.
"""
import logging
import time
from typing import Callable, Any, Optional, TypeVar, Tuple, Dict
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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
    log_error: bool = True
) -> Optional[T]:
    """
    Safely execute a function, returning default on error.
    
    Args:
        func: Function to execute
        default: Default value to return on error
        error_message: Custom error message
        log_error: Whether to log errors
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            logger.error(f"Error in safe_execute: {str(e)}", exc_info=True)
        if error_message:
            logger.error(error_message)
        return default
