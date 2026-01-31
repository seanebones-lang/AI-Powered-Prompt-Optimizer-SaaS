"""
HTTP connection pooling for optimal API performance.
Reuses connections to reduce latency and overhead.
"""
import httpx
import logging
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    Manages HTTP connection pools for API calls.
    
    Features:
    - Connection reuse
    - Automatic retry with backoff
    - Timeout management
    - Connection limits
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global connection pool."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize connection pool manager."""
        if self._initialized:
            return

        # Connection pool settings
        self.limits = httpx.Limits(
            max_keepalive_connections=20,  # Keep 20 connections alive
            max_connections=100,  # Max 100 total connections
            keepalive_expiry=30.0  # Keep connections alive for 30s
        )

        # Timeout settings
        self.timeout = httpx.Timeout(
            connect=10.0,  # 10s to establish connection
            read=60.0,  # 60s to read response
            write=10.0,  # 10s to write request
            pool=5.0  # 5s to get connection from pool
        )

        # Transport with retry
        self.transport = httpx.HTTPTransport(
            limits=self.limits,
            retries=3  # Retry failed connections 3 times
        )

        # Create client
        self._client: Optional[httpx.Client] = None
        self._initialized = True

        logger.info("Connection pool manager initialized with 20 keepalive connections")

    def get_client(self) -> httpx.Client:
        """
        Get or create HTTP client with connection pooling.
        
        Returns:
            Configured httpx.Client
        """
        if self._client is None or self._client.is_closed:
            with self._lock:
                if self._client is None or self._client.is_closed:
                    # Disable HTTP/2 to avoid h2 dependency requirement (HTTP/1.1 works fine)
                    self._client = httpx.Client(
                        timeout=self.timeout,
                        transport=self.transport,
                        limits=self.limits,
                        http2=False,  # Disabled to avoid h2 package requirement
                        follow_redirects=True
                    )
                    logger.info("Created new HTTP client with connection pooling")

        return self._client

    def close(self):
        """Close the connection pool."""
        if self._client and not self._client.is_closed:
            self._client.close()
            logger.info("Connection pool closed")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Global connection pool manager
_pool_manager = ConnectionPoolManager()


def get_pooled_client() -> httpx.Client:
    """Get HTTP client with connection pooling."""
    return _pool_manager.get_client()


def close_pool():
    """Close the global connection pool."""
    _pool_manager.close()
