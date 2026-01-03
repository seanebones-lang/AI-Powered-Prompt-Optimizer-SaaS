"""
Performance optimization utilities.
Includes connection pooling, request batching, and performance tracking.
"""
import logging
import time
from typing import Optional, Dict, Any
from functools import wraps
import httpx
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class HTTPConnectionPool:
    """HTTP connection pool for reusing connections."""
    
    _pools: Dict[str, httpx.Client] = {}
    
    @classmethod
    def get_client(cls, base_url: str, timeout: float = 60.0) -> httpx.Client:
        """
        Get or create HTTP client with connection pooling.
        
        Args:
            base_url: Base URL for the client
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Client instance
        """
        if base_url not in cls._pools:
            cls._pools[base_url] = httpx.Client(
                base_url=base_url,
                timeout=timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20
                )
            )
            logger.info(f"Created HTTP connection pool for {base_url}")
        
        return cls._pools[base_url]
    
    @classmethod
    def close_all(cls) -> None:
        """Close all connection pools."""
        for base_url, client in cls._pools.items():
            try:
                client.close()
                logger.info(f"Closed connection pool for {base_url}")
            except Exception as e:
                logger.error(f"Error closing pool for {base_url}: {str(e)}")
        cls._pools.clear()


def track_performance(metric_name: str):
    """
    Decorator to track function performance.
    
    Args:
        metric_name: Name of the performance metric
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from monitoring import get_metrics
            metrics = get_metrics()
            
            with metrics.time_block(metric_name):
                result = func(*args, **kwargs)
            
            metrics.increment(f"{metric_name}.calls")
            return result
        
        return wrapper
    return decorator


@contextmanager
def performance_tracker(operation_name: str):
    """
    Context manager for tracking operation performance.
    
    Args:
        operation_name: Name of the operation being tracked
    """
    from monitoring import get_metrics
    metrics = get_metrics()
    
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metrics.timer(f"{operation_name}.duration", duration)
        metrics.increment(f"{operation_name}.count")


class RateLimiter:
    """Enhanced rate limiter with sliding window."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            
        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.window_seconds
            ]
        else:
            self.requests[identifier] = []
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window."""
        if identifier not in self.requests:
            return self.max_requests
        
        now = time.time()
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))


def optimize_batch_size(items: list, max_batch_size: int = 10) -> list:
    """
    Optimize batch processing by splitting into optimal batch sizes.
    
    Args:
        items: List of items to process
        max_batch_size: Maximum items per batch
        
    Returns:
        List of batches
    """
    return [
        items[i:i + max_batch_size]
        for i in range(0, len(items), max_batch_size)
    ]
