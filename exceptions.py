"""
Custom exception hierarchy for the AI-Powered Prompt Optimizer.

This module provides a structured exception hierarchy that enables:
- Precise error handling and recovery
- Better debugging with contextual information
- Type-safe exception catching
- Consistent error messages across the application

Usage:
    from exceptions import APIError, ValidationError, DatabaseError

    try:
        response = api.call()
    except RateLimitError as e:
        # Handle rate limiting specifically
        await asyncio.sleep(e.retry_after)
    except APIError as e:
        # Handle all API errors
        logger.error(f"API failed: {e}")
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """Standardized error codes for categorization and monitoring."""

    # API Errors (1000-1999)
    API_UNKNOWN = 1000
    API_TIMEOUT = 1001
    API_RATE_LIMIT = 1002
    API_AUTHENTICATION = 1003
    API_AUTHORIZATION = 1004
    API_INVALID_RESPONSE = 1005
    API_SERVICE_UNAVAILABLE = 1006
    API_CIRCUIT_OPEN = 1007

    # Validation Errors (2000-2999)
    VALIDATION_UNKNOWN = 2000
    VALIDATION_PROMPT_EMPTY = 2001
    VALIDATION_PROMPT_TOO_LONG = 2002
    VALIDATION_PROMPT_INVALID_CHARS = 2003
    VALIDATION_PROMPT_TYPE_INVALID = 2004
    VALIDATION_CONFIG_INVALID = 2005

    # Database Errors (3000-3999)
    DATABASE_UNKNOWN = 3000
    DATABASE_CONNECTION = 3001
    DATABASE_QUERY = 3002
    DATABASE_INTEGRITY = 3003
    DATABASE_NOT_FOUND = 3004
    DATABASE_DUPLICATE = 3005

    # Agent Errors (4000-4999)
    AGENT_UNKNOWN = 4000
    AGENT_DECONSTRUCT_FAILED = 4001
    AGENT_DIAGNOSE_FAILED = 4002
    AGENT_DESIGN_FAILED = 4003
    AGENT_EVALUATE_FAILED = 4004
    AGENT_ORCHESTRATION_FAILED = 4005
    AGENT_TIMEOUT = 4006

    # Configuration Errors (5000-5999)
    CONFIG_UNKNOWN = 5000
    CONFIG_MISSING_KEY = 5001
    CONFIG_INVALID_VALUE = 5002
    CONFIG_FILE_NOT_FOUND = 5003

    # Cache Errors (6000-6999)
    CACHE_UNKNOWN = 6000
    CACHE_MISS = 6001
    CACHE_WRITE_FAILED = 6002
    CACHE_CORRUPTED = 6003


class PromptOptimizerError(Exception):
    """
    Base exception for all Prompt Optimizer errors.

    Provides structured error information including:
    - Error code for categorization
    - Original exception for debugging
    - Context dictionary for additional info

    Attributes:
        message: Human-readable error message
        code: ErrorCode enum for categorization
        context: Additional context dictionary
        original_error: The underlying exception, if any
    """

    default_code = ErrorCode.API_UNKNOWN

    def __init__(
        self,
        message: str,
        code: Optional[ErrorCode] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.code = code or self.default_code
        self.context = context or {}
        self.original_error = original_error

        # Build detailed message
        detailed_message = f"[{self.code.name}] {message}"
        if context:
            detailed_message += f" | Context: {context}"

        super().__init__(detailed_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code.name,
            "code_value": self.code.value,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code.name})"


# =============================================================================
# API Exceptions
# =============================================================================

class APIError(PromptOptimizerError):
    """Base exception for all API-related errors."""
    default_code = ErrorCode.API_UNKNOWN


class APITimeoutError(APIError):
    """Raised when an API request times out."""
    default_code = ErrorCode.API_TIMEOUT

    def __init__(
        self,
        message: str = "API request timed out",
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if timeout_seconds:
            context["timeout_seconds"] = timeout_seconds
        super().__init__(message, context=context, **kwargs)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    default_code = ErrorCode.API_RATE_LIMIT

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[float] = None,
        **kwargs
    ):
        self.retry_after = retry_after
        context = kwargs.pop("context", {})
        if retry_after:
            context["retry_after_seconds"] = retry_after
        super().__init__(message, context=context, **kwargs)


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    default_code = ErrorCode.API_AUTHENTICATION

    def __init__(
        self,
        message: str = "API authentication failed. Check your XAI_API_KEY.",
        **kwargs
    ):
        super().__init__(message, **kwargs)


class AuthorizationError(APIError):
    """Raised when API authorization fails."""
    default_code = ErrorCode.API_AUTHORIZATION


class InvalidResponseError(APIError):
    """Raised when API returns an invalid or unexpected response."""
    default_code = ErrorCode.API_INVALID_RESPONSE

    def __init__(
        self,
        message: str = "API returned invalid response",
        response_type: Optional[str] = None,
        response_preview: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if response_type:
            context["response_type"] = response_type
        if response_preview:
            context["response_preview"] = response_preview[:200]
        super().__init__(message, context=context, **kwargs)


class ServiceUnavailableError(APIError):
    """Raised when the API service is unavailable."""
    default_code = ErrorCode.API_SERVICE_UNAVAILABLE


class CircuitBreakerError(APIError):
    """Raised when the circuit breaker is open."""
    default_code = ErrorCode.API_CIRCUIT_OPEN

    def __init__(
        self,
        message: str = "Circuit breaker is open - service temporarily unavailable",
        reset_time: Optional[float] = None,
        **kwargs
    ):
        self.reset_time = reset_time
        context = kwargs.pop("context", {})
        if reset_time:
            context["reset_time_seconds"] = reset_time
        super().__init__(message, context=context, **kwargs)


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(PromptOptimizerError):
    """Base exception for all validation-related errors."""
    default_code = ErrorCode.VALIDATION_UNKNOWN


class PromptValidationError(ValidationError):
    """Raised when prompt validation fails."""

    def __init__(
        self,
        message: str,
        prompt_preview: Optional[str] = None,
        validation_rule: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if prompt_preview:
            context["prompt_preview"] = prompt_preview[:100]
        if validation_rule:
            context["validation_rule"] = validation_rule
        super().__init__(message, context=context, **kwargs)


class EmptyPromptError(PromptValidationError):
    """Raised when prompt is empty or whitespace only."""
    default_code = ErrorCode.VALIDATION_PROMPT_EMPTY

    def __init__(self, message: str = "Prompt cannot be empty", **kwargs):
        super().__init__(message, validation_rule="non_empty", **kwargs)


class PromptTooLongError(PromptValidationError):
    """Raised when prompt exceeds maximum length."""
    default_code = ErrorCode.VALIDATION_PROMPT_TOO_LONG

    def __init__(
        self,
        message: str = "Prompt exceeds maximum length",
        actual_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if actual_length:
            context["actual_length"] = actual_length
        if max_length:
            context["max_length"] = max_length
        super().__init__(message, validation_rule="max_length", context=context, **kwargs)


class InvalidPromptTypeError(ValidationError):
    """Raised when prompt type is invalid."""
    default_code = ErrorCode.VALIDATION_PROMPT_TYPE_INVALID

    def __init__(
        self,
        message: str = "Invalid prompt type",
        provided_type: Optional[str] = None,
        valid_types: Optional[list] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if provided_type:
            context["provided_type"] = provided_type
        if valid_types:
            context["valid_types"] = valid_types
        super().__init__(message, context=context, **kwargs)


class ConfigValidationError(ValidationError):
    """Raised when configuration validation fails."""
    default_code = ErrorCode.VALIDATION_CONFIG_INVALID


# =============================================================================
# Database Exceptions
# =============================================================================

class DatabaseError(PromptOptimizerError):
    """Base exception for all database-related errors."""
    default_code = ErrorCode.DATABASE_UNKNOWN


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    default_code = ErrorCode.DATABASE_CONNECTION


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""
    default_code = ErrorCode.DATABASE_QUERY

    def __init__(
        self,
        message: str,
        query_type: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if query_type:
            context["query_type"] = query_type
        if table:
            context["table"] = table
        super().__init__(message, context=context, **kwargs)


class RecordNotFoundError(DatabaseError):
    """Raised when a database record is not found."""
    default_code = ErrorCode.DATABASE_NOT_FOUND

    def __init__(
        self,
        message: str = "Record not found",
        table: Optional[str] = None,
        record_id: Optional[Any] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        if table:
            context["table"] = table
        if record_id:
            context["record_id"] = str(record_id)
        super().__init__(message, context=context, **kwargs)


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create a duplicate record."""
    default_code = ErrorCode.DATABASE_DUPLICATE


# =============================================================================
# Agent Exceptions
# =============================================================================

class AgentError(PromptOptimizerError):
    """Base exception for all agent-related errors."""
    default_code = ErrorCode.AGENT_UNKNOWN


class DeconstructionError(AgentError):
    """Raised when the Deconstructor agent fails."""
    default_code = ErrorCode.AGENT_DECONSTRUCT_FAILED


class DiagnosisError(AgentError):
    """Raised when the Diagnoser agent fails."""
    default_code = ErrorCode.AGENT_DIAGNOSE_FAILED


class DesignError(AgentError):
    """Raised when the Designer agent fails."""
    default_code = ErrorCode.AGENT_DESIGN_FAILED


class EvaluationError(AgentError):
    """Raised when the Evaluator agent fails."""
    default_code = ErrorCode.AGENT_EVALUATE_FAILED


class OrchestrationError(AgentError):
    """Raised when the Orchestrator agent fails."""
    default_code = ErrorCode.AGENT_ORCHESTRATION_FAILED


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""
    default_code = ErrorCode.AGENT_TIMEOUT


# =============================================================================
# Configuration Exceptions
# =============================================================================

class ConfigurationError(PromptOptimizerError):
    """Base exception for all configuration-related errors."""
    default_code = ErrorCode.CONFIG_UNKNOWN


class MissingConfigKeyError(ConfigurationError):
    """Raised when a required configuration key is missing."""
    default_code = ErrorCode.CONFIG_MISSING_KEY

    def __init__(
        self,
        key: str,
        message: Optional[str] = None,
        **kwargs
    ):
        self.key = key
        msg = message or f"Missing required configuration key: {key}"
        context = kwargs.pop("context", {})
        context["missing_key"] = key
        super().__init__(msg, context=context, **kwargs)


class InvalidConfigValueError(ConfigurationError):
    """Raised when a configuration value is invalid."""
    default_code = ErrorCode.CONFIG_INVALID_VALUE

    def __init__(
        self,
        key: str,
        value: Any,
        reason: Optional[str] = None,
        **kwargs
    ):
        self.key = key
        self.value = value
        msg = f"Invalid configuration value for '{key}': {value}"
        if reason:
            msg += f" ({reason})"
        context = kwargs.pop("context", {})
        context["key"] = key
        context["value_type"] = type(value).__name__
        super().__init__(msg, context=context, **kwargs)


# =============================================================================
# Cache Exceptions
# =============================================================================

class CacheError(PromptOptimizerError):
    """Base exception for all cache-related errors."""
    default_code = ErrorCode.CACHE_UNKNOWN


class CacheMissError(CacheError):
    """Raised when a cache lookup fails (optional - for explicit miss handling)."""
    default_code = ErrorCode.CACHE_MISS


class CacheWriteError(CacheError):
    """Raised when writing to cache fails."""
    default_code = ErrorCode.CACHE_WRITE_FAILED


class CacheCorruptedError(CacheError):
    """Raised when cache data is corrupted."""
    default_code = ErrorCode.CACHE_CORRUPTED


# =============================================================================
# Utility Functions
# =============================================================================

def wrap_exception(
    exception: Exception,
    wrapper_class: type = PromptOptimizerError,
    message: Optional[str] = None
) -> PromptOptimizerError:
    """
    Wrap a generic exception in a typed PromptOptimizerError.

    Args:
        exception: The original exception
        wrapper_class: The wrapper exception class (default: PromptOptimizerError)
        message: Optional custom message (default: uses original exception message)

    Returns:
        A properly typed exception
    """
    if isinstance(exception, PromptOptimizerError):
        return exception

    msg = message or str(exception)
    return wrapper_class(msg, original_error=exception)


def classify_api_error(status_code: int, error_message: str) -> APIError:
    """
    Classify an HTTP error into the appropriate exception type.

    Args:
        status_code: HTTP status code
        error_message: Error message from response

    Returns:
        Appropriate APIError subclass instance
    """
    error_lower = error_message.lower()

    # Check for timeout first (message-based, regardless of status code)
    if "timeout" in error_lower:
        return APITimeoutError(error_message)

    # Authentication errors
    if status_code == 401 or "unauthorized" in error_lower or "authentication" in error_lower:
        return AuthenticationError(error_message)

    # Authorization errors
    if status_code == 403 or "forbidden" in error_lower:
        return AuthorizationError(error_message)

    # Rate limit errors
    if status_code == 429 or "rate limit" in error_lower:
        return RateLimitError(error_message)

    # Service unavailable
    if status_code in (500, 502, 503, 504):
        return ServiceUnavailableError(error_message)

    return APIError(
        f"API error ({status_code}): {error_message}",
        context={"status_code": status_code}
    )
