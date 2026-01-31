"""
Enhanced caching system with TTL, LRU eviction, and persistence.
Optimizes performance and reduces API costs.
"""
import time
import pickle
import logging
import hashlib
from typing import Any, Optional, Dict
from collections import OrderedDict
from threading import Lock
from pathlib import Path

logger = logging.getLogger(__name__)


class LRUCache:
    """
    LRU (Least Recently Used) cache with TTL support.
    
    Features:
    - TTL (Time To Live) for entries
    - LRU eviction when full
    - Thread-safe operations
    - Persistence to disk
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        persist_path: Optional[str] = None
    ):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
            persist_path: Path to persist cache to disk
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.persist_path = persist_path

        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.ttls: Dict[str, int] = {}
        self.lock = Lock()

        # Load from disk if available
        if persist_path:
            self._load_from_disk()

        logger.info(f"LRU cache initialized: max_size={max_size}, default_ttl={default_ttl}s")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                return None

            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)

            return self.cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        with self.lock:
            # Remove if exists
            if key in self.cache:
                self._remove(key)

            # Evict if full
            if len(self.cache) >= self.max_size:
                self._evict_oldest()

            # Add new entry
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.ttls[key] = ttl if ttl is not None else self.default_ttl

            # Persist if configured
            if self.persist_path:
                self._persist_to_disk()

    def delete(self, key: str):
        """Delete entry from cache."""
        with self.lock:
            if key in self.cache:
                self._remove(key)

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.ttls.clear()

            if self.persist_path:
                self._persist_to_disk()

        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size * 100,
                "oldest_entry_age": self._get_oldest_age(),
                "default_ttl": self.default_ttl
            }

    def _is_expired(self, key: str) -> bool:
        """Check if entry is expired."""
        if key not in self.timestamps:
            return True

        age = time.time() - self.timestamps[key]
        ttl = self.ttls.get(key, self.default_ttl)

        return age > ttl

    def _remove(self, key: str):
        """Remove entry from cache."""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
        if key in self.ttls:
            del self.ttls[key]

    def _evict_oldest(self):
        """Evict oldest (least recently used) entry."""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)
            logger.debug(f"Evicted oldest cache entry: {oldest_key[:20]}...")

    def _get_oldest_age(self) -> float:
        """Get age of oldest entry in seconds."""
        if not self.timestamps:
            return 0.0

        oldest_timestamp = min(self.timestamps.values())
        return time.time() - oldest_timestamp

    def _persist_to_disk(self):
        """Persist cache to disk."""
        if not self.persist_path:
            return

        try:
            path = Path(self.persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "cache": dict(self.cache),
                "timestamps": self.timestamps,
                "ttls": self.ttls
            }

            with open(path, 'wb') as f:
                pickle.dump(data, f)

            logger.debug(f"Cache persisted to {self.persist_path}")
        except Exception as e:
            logger.error(f"Failed to persist cache: {str(e)}")

    def _load_from_disk(self):
        """Load cache from disk."""
        if not self.persist_path:
            return

        try:
            path = Path(self.persist_path)
            if not path.exists():
                return

            with open(path, 'rb') as f:
                data = pickle.load(f)

            self.cache = OrderedDict(data["cache"])
            self.timestamps = data["timestamps"]
            self.ttls = data["ttls"]

            # Remove expired entries
            expired_keys = [k for k in self.cache if self._is_expired(k)]
            for key in expired_keys:
                self._remove(key)

            logger.info(f"Loaded {len(self.cache)} entries from cache")
        except Exception as e:
            logger.error(f"Failed to load cache: {str(e)}")


class SmartCache:
    """
    Smart caching system with automatic key generation and optimization.
    
    Features:
    - Automatic cache key generation from function args
    - Separate caches for different data types
    - Cache warming
    - Statistics tracking
    """

    def __init__(self, cache_dir: str = ".cache"):
        """Initialize smart cache system."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Separate caches for different purposes
        self.api_cache = LRUCache(
            max_size=500,
            default_ttl=3600,  # 1 hour
            persist_path=str(self.cache_dir / "api_cache.pkl")
        )

        self.prompt_cache = LRUCache(
            max_size=1000,
            default_ttl=86400,  # 24 hours
            persist_path=str(self.cache_dir / "prompt_cache.pkl")
        )

        self.result_cache = LRUCache(
            max_size=500,
            default_ttl=7200,  # 2 hours
            persist_path=str(self.cache_dir / "result_cache.pkl")
        )

        # Hit/miss tracking
        self.hits = 0
        self.misses = 0

        logger.info(f"Smart cache system initialized in {cache_dir}")

    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args, **kwargs: Function arguments
            
        Returns:
            Cache key hash
        """
        # Create deterministic string from args
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)

        # Hash for consistent length
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get_api_response(self, key: str) -> Optional[Any]:
        """Get cached API response."""
        result = self.api_cache.get(key)
        if result:
            self.hits += 1
        else:
            self.misses += 1
        return result

    def cache_api_response(self, key: str, response: Any, ttl: Optional[int] = None):
        """Cache API response."""
        self.api_cache.set(key, response, ttl)

    def get_prompt_result(self, key: str) -> Optional[Any]:
        """Get cached prompt optimization result."""
        result = self.prompt_cache.get(key)
        if result:
            self.hits += 1
        else:
            self.misses += 1
        return result

    def cache_prompt_result(self, key: str, result: Any, ttl: Optional[int] = None):
        """Cache prompt optimization result."""
        self.prompt_cache.set(key, result, ttl)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "api_cache": self.api_cache.get_stats(),
            "prompt_cache": self.prompt_cache.get_stats(),
            "result_cache": self.result_cache.get_stats()
        }

    def clear_all(self):
        """Clear all caches."""
        self.api_cache.clear()
        self.prompt_cache.clear()
        self.result_cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("All caches cleared")


# Global smart cache instance
_smart_cache = SmartCache()


def get_smart_cache() -> SmartCache:
    """Get global smart cache instance."""
    return _smart_cache
