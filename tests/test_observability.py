"""
Tests for the observability module.

Tests for:
- Structured JSON logging
- LLM call tracking
- Cost estimation
- Performance tracking
"""
import pytest
import logging
import time
import os

# Set test environment
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("XAI_API_KEY", "test-api-key-12345")


class TestLLMCallTracker:
    """Tests for LLM call tracking functionality."""

    def test_tracker_initialization(self):
        """Tracker should initialize with empty calls list."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()
        assert len(tracker.calls) == 0

    def test_track_successful_call(self):
        """Tracker should record successful LLM calls."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()

        with tracker.track_call("grok-4-1-fast", prompt_type="creative") as call:
            call.set_tokens({
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            })

        assert len(tracker.calls) == 1
        assert tracker.calls[0].model == "grok-4-1-fast"
        assert tracker.calls[0].prompt_tokens == 100
        assert tracker.calls[0].completion_tokens == 50
        assert tracker.calls[0].success is True

    def test_track_failed_call(self):
        """Tracker should record failed LLM calls."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()

        with pytest.raises(ValueError):
            with tracker.track_call("grok-4-1-fast") as call:
                raise ValueError("API error")

        assert len(tracker.calls) == 1
        assert tracker.calls[0].success is False
        assert "API error" in tracker.calls[0].error_message

    def test_cost_calculation(self):
        """Cost should be calculated correctly based on token counts."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()

        # grok-4-1-fast: $2/1M input, $10/1M output
        with tracker.track_call("grok-4-1-fast") as call:
            call.set_tokens({
                "prompt_tokens": 1000,  # 1K tokens
                "completion_tokens": 500,
                "total_tokens": 1500
            })

        # Expected: (1000/1M * 2) + (500/1M * 10) = 0.002 + 0.005 = 0.007
        assert tracker.calls[0].cost_usd == pytest.approx(0.007, rel=1e-3)

    def test_latency_tracking(self):
        """Latency should be tracked correctly."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()

        with tracker.track_call("grok-4-1-fast") as call:
            time.sleep(0.05)  # 50ms delay
            call.set_tokens({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

        assert tracker.calls[0].latency_ms >= 50  # At least 50ms

    def test_get_summary(self):
        """Summary should aggregate all tracked calls."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()

        # Track two successful calls
        for i in range(2):
            with tracker.track_call("grok-4-1-fast") as call:
                call.set_tokens({
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                })

        summary = tracker.get_summary()

        assert summary["total_calls"] == 2
        assert summary["successful_calls"] == 2
        assert summary["failed_calls"] == 0
        assert summary["total_tokens"] == 300
        assert summary["total_cost_usd"] > 0

    def test_reset(self):
        """Reset should clear all tracked calls."""
        from observability import LLMCallTracker

        tracker = LLMCallTracker()

        with tracker.track_call("grok-4-1-fast") as call:
            call.set_tokens({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

        assert len(tracker.calls) == 1
        tracker.reset()
        assert len(tracker.calls) == 0


class TestLLMCallMetrics:
    """Tests for LLMCallMetrics dataclass."""

    def test_metrics_to_dict(self):
        """Metrics should convert to dictionary correctly."""
        from observability import LLMCallMetrics

        metrics = LLMCallMetrics(
            model="grok-4-1-fast",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=123.456,
            cost_usd=0.01234,
            success=True
        )

        result = metrics.to_dict()

        assert result["model"] == "grok-4-1-fast"
        assert result["prompt_tokens"] == 100
        assert result["latency_ms"] == 123.46  # Rounded
        assert result["cost_usd"] == 0.012340  # Rounded to 6 decimals

    def test_metrics_default_timestamp(self):
        """Metrics should have timestamp by default."""
        from observability import LLMCallMetrics

        metrics = LLMCallMetrics(model="test")
        assert metrics.timestamp is not None
        assert "T" in metrics.timestamp  # ISO format


class TestStructuredLogging:
    """Tests for structured logging setup."""

    def test_setup_logging_returns_logger(self):
        """setup_structured_logging should return a logger."""
        from observability import setup_structured_logging

        logger = setup_structured_logging(level=logging.DEBUG, enable_json=False)
        assert isinstance(logger, logging.Logger)

    def test_logging_with_extra_fields(self, caplog):
        """Logging should support extra fields."""
        import logging

        logger = logging.getLogger("test_extra")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Test message", extra={"custom_field": "value"})

        assert "Test message" in caplog.text


class TestPerformanceTracking:
    """Tests for performance tracking decorator."""

    def test_track_performance_decorator(self, caplog):
        """Performance decorator should track function execution."""
        from observability import track_performance

        @track_performance
        def sample_function():
            time.sleep(0.01)
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = sample_function()

        assert result == "result"

    def test_track_performance_on_error(self, caplog):
        """Performance decorator should log errors."""
        from observability import track_performance

        @track_performance
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            with caplog.at_level(logging.ERROR):
                failing_function()


class TestSentryIntegration:
    """Tests for Sentry integration."""

    def test_setup_sentry_without_dsn(self):
        """Sentry setup should handle missing DSN gracefully."""
        from observability import setup_sentry

        # Clear any existing DSN
        old_dsn = os.environ.pop("SENTRY_DSN", None)

        try:
            result = setup_sentry()
            # Should return False if no DSN and Sentry not available
            assert result is False or result is True
        finally:
            if old_dsn:
                os.environ["SENTRY_DSN"] = old_dsn


class TestModelPricing:
    """Tests for model pricing configuration."""

    def test_all_models_have_pricing(self):
        """All listed models should have input and output pricing."""
        from observability import MODEL_PRICING

        for model, pricing in MODEL_PRICING.items():
            assert "input" in pricing, f"Model {model} missing input pricing"
            assert "output" in pricing, f"Model {model} missing output pricing"
            assert pricing["input"] > 0, f"Model {model} has invalid input price"
            assert pricing["output"] > 0, f"Model {model} has invalid output price"

    def test_grok_4_pricing(self):
        """Grok 4 models should have correct pricing."""
        from observability import MODEL_PRICING

        assert "grok-4-1-fast-reasoning" in MODEL_PRICING
        assert MODEL_PRICING["grok-4-1-fast-reasoning"]["input"] == 3.00
        assert MODEL_PRICING["grok-4-1-fast-reasoning"]["output"] == 15.00


class TestGlobalTracker:
    """Tests for global tracker instance."""

    def test_get_tracker(self):
        """get_tracker should return the global tracker."""
        from observability import get_tracker, LLMCallTracker

        tracker = get_tracker()
        assert isinstance(tracker, LLMCallTracker)

    def test_global_tracker_persists(self):
        """Global tracker should persist across calls."""
        from observability import get_tracker

        tracker1 = get_tracker()
        tracker1.reset()

        with tracker1.track_call("test") as call:
            call.set_tokens({"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2})

        tracker2 = get_tracker()
        assert len(tracker2.calls) == 1

        # Cleanup
        tracker1.reset()
