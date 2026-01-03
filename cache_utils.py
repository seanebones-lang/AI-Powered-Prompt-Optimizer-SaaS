"""
Caching utilities for API responses and optimization results.
Reduces API calls and improves performance.
"""
import logging
import hashlib
import json
import time
from typing import Optional, Any, Dict
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Cache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.now() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self.cleanup_expired()
        return {
            "total_entries": len(self._cache),
            "default_ttl": self.default_ttl
        }


# Global cache instance
_global_cache = Cache(default_ttl=3600)


def cached(ttl: int = 3600, key_func: Optional[callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Optional function to generate cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _global_cache._generate_key(
                    func.__name__, *args, **kwargs
                )
            
            # Try to get from cache
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def get_cache() -> Cache:
    """Get global cache instance."""
    return _global_cache
