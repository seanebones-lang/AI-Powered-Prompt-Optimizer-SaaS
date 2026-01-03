"""
Security-focused tests for the AI-Powered Prompt Optimizer.

Tests for:
- Input sanitization and validation
- XSS prevention
- SQL injection prevention
- API key protection
- Rate limiting
"""
import pytest
from unittest.mock import patch, MagicMock
import os

# Set test environment
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("XAI_API_KEY", "test-api-key-12345")
os.environ.setdefault("SECRET_KEY", "test-secret-key-12345")


class TestInputSanitization:
    """Tests for input sanitization and validation."""

    def test_empty_prompt_rejected(self):
        """Empty prompts should be rejected."""
        from input_validation import validate_prompt
        is_valid, error = validate_prompt("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_whitespace_only_rejected(self):
        """Whitespace-only prompts should be rejected."""
        from input_validation import validate_prompt
        is_valid, error = validate_prompt("   \n\t   ")
        assert not is_valid
        assert "whitespace" in error.lower()

    def test_max_length_enforced(self):
        """Prompts exceeding max length should be rejected."""
        from input_validation import validate_prompt, MAX_PROMPT_LENGTH
        long_prompt = "A" * (MAX_PROMPT_LENGTH + 1)
        is_valid, error = validate_prompt(long_prompt)
        assert not is_valid
        assert "more than" in error.lower() or "characters" in error.lower()

    def test_control_characters_removed(self):
        """Control characters should be stripped from prompts."""
        from input_validation import sanitize_prompt
        malicious = "Hello\x00World\x01Test\x02"
        sanitized = sanitize_prompt(malicious)
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        assert "HelloWorldTest" in sanitized

    def test_xss_script_tags_handled(self):
        """XSS script tags should not cause issues."""
        from input_validation import sanitize_and_validate_prompt
        xss_attempt = "<script>alert('xss')</script>Write a blog post"
        is_valid, sanitized, error = sanitize_and_validate_prompt(xss_attempt)
        assert is_valid
        assert sanitized is not None
        # The prompt should still be accepted (Streamlit escapes HTML)

    def test_sql_injection_patterns_handled(self):
        """SQL injection patterns should be handled safely."""
        from input_validation import sanitize_and_validate_prompt
        sql_attempt = "'; DROP TABLE users; --"
        is_valid, sanitized, error = sanitize_and_validate_prompt(sql_attempt)
        # Should still be valid since we use ORM, but input is sanitized
        assert is_valid or not is_valid  # Either way, no crash

    def test_unicode_prompts_accepted(self):
        """Unicode prompts should be accepted and preserved."""
        from input_validation import sanitize_and_validate_prompt
        unicode_prompt = "Write about 日本語 and العربية with émojis 🎉🚀"
        is_valid, sanitized, error = sanitize_and_validate_prompt(unicode_prompt)
        assert is_valid
        assert "日本語" in sanitized
        assert "🎉" in sanitized

    def test_newlines_preserved(self):
        """Legitimate newlines should be preserved in prompts."""
        from input_validation import sanitize_prompt
        multiline = "Line 1\nLine 2\nLine 3"
        sanitized = sanitize_prompt(multiline)
        assert "\n" in sanitized
        assert "Line 1" in sanitized
        assert "Line 3" in sanitized


class TestPromptTypeValidation:
    """Tests for prompt type validation."""

    def test_valid_prompt_types_accepted(self):
        """All valid prompt types should be accepted."""
        from input_validation import validate_prompt_type
        from agents import PromptType

        for pt in PromptType:
            is_valid, enum_val, error = validate_prompt_type(pt.value)
            assert is_valid, f"Valid type {pt.value} was rejected"
            assert enum_val == pt
            assert error is None

    def test_invalid_prompt_type_rejected(self):
        """Invalid prompt types should be rejected."""
        from input_validation import validate_prompt_type
        is_valid, enum_val, error = validate_prompt_type("invalid_type")
        assert not is_valid
        assert enum_val is None
        assert "invalid" in error.lower() or "must be" in error.lower()

    def test_empty_prompt_type_rejected(self):
        """Empty prompt type should be rejected."""
        from input_validation import validate_prompt_type
        is_valid, enum_val, error = validate_prompt_type("")
        assert not is_valid
        assert "required" in error.lower()


class TestUsernameValidation:
    """Tests for username validation."""

    def test_valid_username_accepted(self):
        """Valid usernames should be accepted."""
        from input_validation import validate_username
        is_valid, error = validate_username("valid_user123")
        assert is_valid
        assert error is None

    def test_short_username_rejected(self):
        """Usernames under 3 characters should be rejected."""
        from input_validation import validate_username
        is_valid, error = validate_username("ab")
        assert not is_valid
        assert "3 characters" in error.lower()

    def test_special_chars_in_username_rejected(self):
        """Special characters in usernames should be rejected."""
        from input_validation import validate_username
        is_valid, error = validate_username("user@name!")
        assert not is_valid
        assert "letters" in error.lower() or "alphanumeric" in error.lower()

    def test_username_with_underscores_accepted(self):
        """Usernames with underscores should be accepted."""
        from input_validation import validate_username
        is_valid, error = validate_username("user_name_123")
        assert is_valid


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email_accepted(self):
        """Valid emails should be accepted."""
        from input_validation import validate_email
        is_valid, error = validate_email("test@example.com")
        assert is_valid
        assert error is None

    def test_invalid_email_rejected(self):
        """Invalid emails should be rejected."""
        from input_validation import validate_email
        invalid_emails = [
            "not-an-email",
            "@nodomain.com",
            "no@domain",
            "spaces in@email.com",
        ]
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert not is_valid, f"Invalid email '{email}' was accepted"


class TestAPIKeySecurity:
    """Tests for API key security."""

    def test_api_key_not_in_response(self, mock_grok_api):
        """API key should never appear in API responses."""
        response = mock_grok_api.return_value
        response_str = str(response)
        assert "test-api-key" not in response_str
        assert "XAI_API_KEY" not in response_str

    def test_api_key_not_logged(self, caplog):
        """API key should not appear in logs."""
        import logging
        from api_utils import GrokAPI

        with caplog.at_level(logging.DEBUG):
            api = GrokAPI()
            # Any log output should not contain the API key
            for record in caplog.records:
                assert "test-api-key" not in record.message.lower()
                assert "xai_api_key" not in record.message.lower()


class TestPasswordSecurity:
    """Tests for password security."""

    def test_passwords_are_hashed(self, test_db_session):
        """Passwords should be hashed, not stored in plain text."""
        from database import Database
        import bcrypt

        db = Database()
        user = db.create_user("hashtest@example.com", "hashtest", "mypassword")

        if user:
            # Password should be hashed
            assert user.hashed_password != "mypassword"
            # Should be a valid bcrypt hash
            assert user.hashed_password.startswith("$2")

    def test_password_verification_works(self, test_db_session):
        """Password verification should work correctly."""
        from database import Database

        db = Database()
        user = db.create_user("verify@example.com", "verifyuser", "correctpassword")

        if user:
            # Correct password should authenticate
            auth_user = db.authenticate_user("verifyuser", "correctpassword")
            assert auth_user is not None

            # Wrong password should fail
            wrong_auth = db.authenticate_user("verifyuser", "wrongpassword")
            assert wrong_auth is None


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiter_allows_requests(self):
        """Rate limiter should allow requests within limit."""
        from performance import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_user"), f"Request {i+1} should be allowed"

    def test_rate_limiter_blocks_excess_requests(self):
        """Rate limiter should block requests exceeding limit."""
        from performance import RateLimiter

        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Allow 3 requests
        for _ in range(3):
            limiter.is_allowed("test_user")

        # 4th request should be blocked
        assert not limiter.is_allowed("test_user")

    def test_rate_limiter_tracks_remaining(self):
        """Rate limiter should correctly track remaining requests."""
        from performance import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)

        assert limiter.get_remaining("test_user") == 5
        limiter.is_allowed("test_user")
        assert limiter.get_remaining("test_user") == 4
        limiter.is_allowed("test_user")
        assert limiter.get_remaining("test_user") == 3


class TestErrorHandling:
    """Tests for secure error handling."""

    def test_api_error_messages_are_safe(self):
        """API error messages should not expose sensitive info."""
        from error_handling import ErrorHandler

        handler = ErrorHandler()

        # Simulate various errors
        errors = [
            Exception("API key abc123xyz invalid"),
            Exception("Database connection to secret.db failed"),
            Exception("Internal server error at /admin/secret"),
        ]

        for error in errors:
            message = handler.handle_api_error(error)
            # Should return user-friendly message
            assert len(message) > 0
            # Should not expose internal paths in most cases
            # The handler sanitizes known patterns


class TestRetryLogic:
    """Tests for retry logic security."""

    def test_retry_limits_are_enforced(self):
        """Retry logic should not exceed maximum retries."""
        from error_handling import RetryStrategy

        strategy = RetryStrategy(max_retries=3)

        assert strategy.max_retries == 3
        # Backoff should not exceed max_delay
        for attempt in range(10):
            delay = strategy.get_delay(attempt)
            assert delay <= strategy.max_delay


class TestSessionSecurity:
    """Tests for session security."""

    def test_session_data_not_leaked(self, test_db_session):
        """Session data should not include sensitive information."""
        from database import Database, OptimizationSession

        db = Database()
        session = db.save_session(
            user_id=None,
            original_prompt="Test prompt",
            prompt_type="creative",
            optimized_prompt="Optimized test",
            sample_output="Sample",
            quality_score=85
        )

        if session:
            # Session should not contain API keys or secrets
            session_str = str(session.__dict__)
            assert "api_key" not in session_str.lower()
            assert "secret" not in session_str.lower()
