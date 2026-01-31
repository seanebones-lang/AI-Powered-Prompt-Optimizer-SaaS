"""
Advanced rate limiting with token bucket and sliding window algorithms.
Protects against DoS attacks and ensures fair resource allocation.
"""
import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10  # Token bucket burst capacity
    cost_per_request: int = 1  # Base cost


class TokenBucket:
    """Token bucket algorithm for rate limiting with burst support."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens (burst capacity)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if insufficient
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait until tokens are available."""
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                return 0.0

            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate


class SlidingWindowCounter:
    """Sliding window algorithm for precise rate limiting."""

    def __init__(self, window_size: int):
        """
        Initialize sliding window counter.
        
        Args:
            window_size: Window size in seconds
        """
        self.window_size = window_size
        self.requests: deque = deque()
        self.lock = Lock()

    def add_request(self, timestamp: Optional[float] = None) -> None:
        """Add a request to the window."""
        if timestamp is None:
            timestamp = time.time()

        with self.lock:
            self.requests.append(timestamp)
            self._cleanup()

    def get_count(self) -> int:
        """Get number of requests in current window."""
        with self.lock:
            self._cleanup()
            return len(self.requests)

    def _cleanup(self):
        """Remove requests outside the window."""
        cutoff = time.time() - self.window_size
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies.
    
    Combines token bucket (for burst) and sliding window (for precision).
    Supports per-user, per-IP, and global rate limits.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter with configuration."""
        self.config = config or RateLimitConfig()

        # Per-identifier rate limiters
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.user_windows: Dict[str, Dict[str, SlidingWindowCounter]] = {}

        # Global rate limiter
        self.global_bucket = TokenBucket(
            capacity=self.config.burst_size * 100,
            refill_rate=self.config.requests_per_minute / 60.0
        )

        self.lock = Lock()

        logger.info(f"Rate limiter initialized: {self.config.requests_per_minute} req/min, "
                   f"{self.config.requests_per_hour} req/hour, {self.config.requests_per_day} req/day")

    def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1,
        check_global: bool = True
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Check if request is allowed under rate limits.
        
        Args:
            identifier: User ID, IP address, or API key
            cost: Cost of this request (default 1)
            check_global: Whether to check global limits
            
        Returns:
            Tuple of (allowed, reason, retry_after_seconds)
        """
        # Check global rate limit first
        if check_global and not self.global_bucket.consume(cost):
            wait_time = self.global_bucket.get_wait_time(cost)
            logger.warning(f"Global rate limit exceeded. Retry after {wait_time:.2f}s")
            return False, "Global rate limit exceeded", wait_time

        # Get or create user-specific limiters
        with self.lock:
            if identifier not in self.user_buckets:
                self.user_buckets[identifier] = TokenBucket(
                    capacity=self.config.burst_size,
                    refill_rate=self.config.requests_per_minute / 60.0
                )

            if identifier not in self.user_windows:
                self.user_windows[identifier] = {
                    'minute': SlidingWindowCounter(60),
                    'hour': SlidingWindowCounter(3600),
                    'day': SlidingWindowCounter(86400)
                }

        bucket = self.user_buckets[identifier]
        windows = self.user_windows[identifier]

        # Check token bucket (burst)
        if not bucket.consume(cost):
            wait_time = bucket.get_wait_time(cost)
            logger.warning(f"Rate limit exceeded for {identifier}: burst limit. Retry after {wait_time:.2f}s")
            return False, "Too many requests (burst limit)", wait_time

        # Check sliding windows
        now = time.time()

        # Minute limit
        if windows['minute'].get_count() >= self.config.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {identifier}: {self.config.requests_per_minute} req/min")
            return False, f"Rate limit: {self.config.requests_per_minute} requests per minute", 60.0

        # Hour limit
        if windows['hour'].get_count() >= self.config.requests_per_hour:
            logger.warning(f"Rate limit exceeded for {identifier}: {self.config.requests_per_hour} req/hour")
            return False, f"Rate limit: {self.config.requests_per_hour} requests per hour", 3600.0

        # Day limit
        if windows['day'].get_count() >= self.config.requests_per_day:
            logger.warning(f"Rate limit exceeded for {identifier}: {self.config.requests_per_day} req/day")
            return False, f"Rate limit: {self.config.requests_per_day} requests per day", 86400.0

        # Add request to windows
        for window in windows.values():
            window.add_request(now)

        return True, None, None

    def get_rate_limit_status(self, identifier: str) -> Dict[str, any]:
        """
        Get current rate limit status for an identifier.
        
        Returns:
            Dictionary with current usage and limits
        """
        with self.lock:
            if identifier not in self.user_windows:
                return {
                    'minute': {'used': 0, 'limit': self.config.requests_per_minute, 'remaining': self.config.requests_per_minute},
                    'hour': {'used': 0, 'limit': self.config.requests_per_hour, 'remaining': self.config.requests_per_hour},
                    'day': {'used': 0, 'limit': self.config.requests_per_day, 'remaining': self.config.requests_per_day}
                }

            windows = self.user_windows[identifier]

            minute_used = windows['minute'].get_count()
            hour_used = windows['hour'].get_count()
            day_used = windows['day'].get_count()

            return {
                'minute': {
                    'used': minute_used,
                    'limit': self.config.requests_per_minute,
                    'remaining': max(0, self.config.requests_per_minute - minute_used)
                },
                'hour': {
                    'used': hour_used,
                    'limit': self.config.requests_per_hour,
                    'remaining': max(0, self.config.requests_per_hour - hour_used)
                },
                'day': {
                    'used': day_used,
                    'limit': self.config.requests_per_day,
                    'remaining': max(0, self.config.requests_per_day - day_used)
                }
            }

    def reset_limits(self, identifier: str) -> None:
        """Reset rate limits for an identifier."""
        with self.lock:
            if identifier in self.user_buckets:
                del self.user_buckets[identifier]
            if identifier in self.user_windows:
                del self.user_windows[identifier]

        logger.info(f"Rate limits reset for {identifier}")


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _global_rate_limiter


def rate_limit_check(identifier: str, cost: int = 1) -> Tuple[bool, Optional[str], Optional[float]]:
    """Convenience function for rate limit checking."""
    return _global_rate_limiter.check_rate_limit(identifier, cost)
