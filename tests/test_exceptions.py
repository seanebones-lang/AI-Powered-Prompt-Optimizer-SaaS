"""
Tests for the typed exception hierarchy.

Verifies:
- Exception inheritance
- Error codes
- Context handling
- Exception classification
"""

import pytest
from exceptions import (
    # Base
    PromptOptimizerError,
    ErrorCode,
    # API
    APIError,
    APITimeoutError,
    RateLimitError,
    AuthenticationError,
    AuthorizationError,
    InvalidResponseError,
    ServiceUnavailableError,
    CircuitBreakerError,
    # Validation
    ValidationError,
    PromptValidationError,
    EmptyPromptError,
    PromptTooLongError,
    InvalidPromptTypeError,
    ConfigValidationError,
    # Database
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    RecordNotFoundError,
    DuplicateRecordError,
    # Agent
    AgentError,
    DeconstructionError,
    DiagnosisError,
    DesignError,
    EvaluationError,
    OrchestrationError,
    AgentTimeoutError,
    # Configuration
    ConfigurationError,
    MissingConfigKeyError,
    CacheError,
    wrap_exception,
    classify_api_error,
)


class TestExceptionHierarchy:
    """Test exception inheritance."""

    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions should inherit from PromptOptimizerError."""
        exceptions = [
            APIError,
            ValidationError,
            DatabaseError,
            AgentError,
            ConfigurationError,
            CacheError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, PromptOptimizerError)

    def test_api_exceptions_inherit_from_api_error(self):
        """API exceptions should inherit from APIError."""
        api_exceptions = [
            APITimeoutError,
            RateLimitError,
            AuthenticationError,
            AuthorizationError,
            InvalidResponseError,
            ServiceUnavailableError,
            CircuitBreakerError,
        ]
        for exc_class in api_exceptions:
            assert issubclass(exc_class, APIError)

    def test_validation_exceptions_inherit_from_validation_error(self):
        """Validation exceptions should inherit from ValidationError."""
        validation_exceptions = [
            PromptValidationError,
            EmptyPromptError,
            PromptTooLongError,
            InvalidPromptTypeError,
            ConfigValidationError,
        ]
        for exc_class in validation_exceptions:
            assert issubclass(exc_class, ValidationError)

    def test_database_exceptions_inherit_from_database_error(self):
        """Database exceptions should inherit from DatabaseError."""
        db_exceptions = [
            DatabaseConnectionError,
            DatabaseQueryError,
            RecordNotFoundError,
            DuplicateRecordError,
        ]
        for exc_class in db_exceptions:
            assert issubclass(exc_class, DatabaseError)

    def test_agent_exceptions_inherit_from_agent_error(self):
        """Agent exceptions should inherit from AgentError."""
        agent_exceptions = [
            DeconstructionError,
            DiagnosisError,
            DesignError,
            EvaluationError,
            OrchestrationError,
            AgentTimeoutError,
        ]
        for exc_class in agent_exceptions:
            assert issubclass(exc_class, AgentError)


class TestErrorCodes:
    """Test error codes are properly assigned."""

    def test_api_error_codes(self):
        """API errors should have correct error codes."""
        assert APIError("test").code == ErrorCode.API_UNKNOWN
        assert APITimeoutError().code == ErrorCode.API_TIMEOUT
        assert RateLimitError().code == ErrorCode.API_RATE_LIMIT
        assert AuthenticationError().code == ErrorCode.API_AUTHENTICATION
        assert AuthorizationError("test").code == ErrorCode.API_AUTHORIZATION
        assert InvalidResponseError().code == ErrorCode.API_INVALID_RESPONSE
        assert ServiceUnavailableError("test").code == ErrorCode.API_SERVICE_UNAVAILABLE
        assert CircuitBreakerError().code == ErrorCode.API_CIRCUIT_OPEN

    def test_validation_error_codes(self):
        """Validation errors should have correct error codes."""
        assert ValidationError("test").code == ErrorCode.VALIDATION_UNKNOWN
        assert EmptyPromptError().code == ErrorCode.VALIDATION_PROMPT_EMPTY
        assert PromptTooLongError().code == ErrorCode.VALIDATION_PROMPT_TOO_LONG
        assert InvalidPromptTypeError().code == ErrorCode.VALIDATION_PROMPT_TYPE_INVALID

    def test_database_error_codes(self):
        """Database errors should have correct error codes."""
        assert DatabaseError("test").code == ErrorCode.DATABASE_UNKNOWN
        assert DatabaseConnectionError("test").code == ErrorCode.DATABASE_CONNECTION
        assert DatabaseQueryError("test").code == ErrorCode.DATABASE_QUERY
        assert RecordNotFoundError().code == ErrorCode.DATABASE_NOT_FOUND
        assert DuplicateRecordError("test").code == ErrorCode.DATABASE_DUPLICATE


class TestExceptionContext:
    """Test context handling in exceptions."""

    def test_basic_exception_creation(self):
        """Test basic exception with message."""
        exc = APIError("Something went wrong")
        assert exc.message == "Something went wrong"
        assert exc.context == {}
        assert exc.original_error is None

    def test_exception_with_context(self):
        """Test exception with additional context."""
        exc = APIError(
            "Something went wrong",
            context={"request_id": "123", "endpoint": "/api/test"}
        )
        assert exc.context["request_id"] == "123"
        assert exc.context["endpoint"] == "/api/test"

    def test_exception_with_original_error(self):
        """Test exception wrapping another exception."""
        original = ValueError("Original error")
        exc = APIError("Wrapped error", original_error=original)
        assert exc.original_error is original

    def test_to_dict(self):
        """Test exception serialization to dict."""
        exc = APIError(
            "Test error",
            code=ErrorCode.API_TIMEOUT,
            context={"timeout": 30}
        )
        data = exc.to_dict()
        assert data["error_type"] == "APIError"
        assert data["message"] == "Test error"
        assert data["code"] == "API_TIMEOUT"
        assert data["context"]["timeout"] == 30

    def test_rate_limit_error_retry_after(self):
        """Test RateLimitError with retry_after."""
        exc = RateLimitError("Rate limited", retry_after=30.0)
        assert exc.retry_after == 30.0
        assert exc.context["retry_after_seconds"] == 30.0

    def test_prompt_too_long_error(self):
        """Test PromptTooLongError with length info."""
        exc = PromptTooLongError(
            "Prompt too long",
            actual_length=5000,
            max_length=4000
        )
        assert exc.context["actual_length"] == 5000
        assert exc.context["max_length"] == 4000

    def test_record_not_found_error(self):
        """Test RecordNotFoundError with table and id."""
        exc = RecordNotFoundError(
            "User not found",
            table="users",
            record_id=123
        )
        assert exc.context["table"] == "users"
        assert exc.context["record_id"] == "123"

    def test_missing_config_key_error(self):
        """Test MissingConfigKeyError stores the key."""
        exc = MissingConfigKeyError("XAI_API_KEY")
        assert exc.key == "XAI_API_KEY"
        assert exc.context["missing_key"] == "XAI_API_KEY"


class TestClassifyApiError:
    """Test the classify_api_error utility function."""

    def test_classify_401_as_authentication(self):
        """401 should be classified as AuthenticationError."""
        exc = classify_api_error(401, "Unauthorized")
        assert isinstance(exc, AuthenticationError)

    def test_classify_403_as_authorization(self):
        """403 should be classified as AuthorizationError."""
        exc = classify_api_error(403, "Forbidden")
        assert isinstance(exc, AuthorizationError)

    def test_classify_429_as_rate_limit(self):
        """429 should be classified as RateLimitError."""
        exc = classify_api_error(429, "Too many requests")
        assert isinstance(exc, RateLimitError)

    def test_classify_500_as_service_unavailable(self):
        """500 should be classified as ServiceUnavailableError."""
        exc = classify_api_error(500, "Internal server error")
        assert isinstance(exc, ServiceUnavailableError)

    def test_classify_502_as_service_unavailable(self):
        """502 should be classified as ServiceUnavailableError."""
        exc = classify_api_error(502, "Bad gateway")
        assert isinstance(exc, ServiceUnavailableError)

    def test_classify_503_as_service_unavailable(self):
        """503 should be classified as ServiceUnavailableError."""
        exc = classify_api_error(503, "Service unavailable")
        assert isinstance(exc, ServiceUnavailableError)

    def test_classify_timeout_message(self):
        """Message containing 'timeout' should be APITimeoutError."""
        exc = classify_api_error(500, "Request timeout exceeded")
        assert isinstance(exc, APITimeoutError)

    def test_classify_unknown_error(self):
        """Unknown status should be generic APIError."""
        exc = classify_api_error(418, "I'm a teapot")
        assert isinstance(exc, APIError)
        assert not isinstance(exc, (
            APITimeoutError, RateLimitError, AuthenticationError,
            AuthorizationError, ServiceUnavailableError
        ))


class TestWrapException:
    """Test the wrap_exception utility function."""

    def test_wrap_generic_exception(self):
        """Wrap a generic exception in PromptOptimizerError."""
        original = ValueError("Something failed")
        wrapped = wrap_exception(original)
        assert isinstance(wrapped, PromptOptimizerError)
        assert wrapped.original_error is original

    def test_wrap_with_custom_class(self):
        """Wrap with a specific exception class."""
        original = ValueError("DB failed")
        wrapped = wrap_exception(original, wrapper_class=DatabaseError)
        assert isinstance(wrapped, DatabaseError)

    def test_wrap_with_custom_message(self):
        """Wrap with a custom message."""
        original = ValueError("Original")
        wrapped = wrap_exception(original, message="Custom message")
        assert wrapped.message == "Custom message"

    def test_wrap_returns_typed_as_is(self):
        """Already typed exceptions should be returned as-is."""
        original = APIError("Already typed")
        wrapped = wrap_exception(original)
        assert wrapped is original


class TestExceptionCatching:
    """Test exception catching patterns."""

    def test_catch_specific_api_error(self):
        """Catch specific API error type."""
        with pytest.raises(RateLimitError):
            raise RateLimitError("Too many requests")

    def test_catch_base_api_error(self):
        """Catch base APIError catches all API errors."""
        with pytest.raises(APIError):
            raise RateLimitError("Too many requests")

    def test_catch_base_prompt_optimizer_error(self):
        """Catch base error catches all custom errors."""
        with pytest.raises(PromptOptimizerError):
            raise DatabaseConnectionError("Connection failed")

    def test_exception_in_try_except_chain(self):
        """Test exception handling in try-except chain."""
        def process():
            raise RateLimitError("Limited", retry_after=30)

        try:
            process()
        except RateLimitError as e:
            assert e.retry_after == 30
        except APIError:
            pytest.fail("Should have caught RateLimitError first")
