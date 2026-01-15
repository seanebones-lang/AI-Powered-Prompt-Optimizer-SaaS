"""
Utility functions for caching agent responses to improve performance.
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Cache directory
CACHE_DIR = ".cache"
AGENT_CACHE_FILE = os.path.join(CACHE_DIR, "agent_responses.json")
CACHE_EXPIRY_DAYS = 7


def ensure_cache_dir():
    """Ensure the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def load_agent_cache() -> Dict[str, Any]:
    """Load the agent response cache from file."""
    ensure_cache_dir()
    try:
        if os.path.exists(AGENT_CACHE_FILE):
            with open(AGENT_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                # Remove expired entries
                expiry_date = datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)
                cache = {k: v for k, v in cache.items() if datetime.fromisoformat(v['timestamp']) > expiry_date}
                return cache
    except Exception as e:
        print(f"Error loading cache: {e}")
    return {}


def save_agent_cache(cache: Dict[str, Any]):
    """Save the agent response cache to file."""
    ensure_cache_dir()
    try:
        with open(AGENT_CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Error saving cache: {e}")


def get_cached_response(prompt: str, agent_name: str) -> Optional[Dict[str, Any]]:
    """Get a cached response for a given prompt and agent if it exists and is not expired."""
    cache = load_agent_cache()
    cache_key = f"{agent_name}:{prompt}"
    if cache_key in cache:
        entry = cache[cache_key]
        expiry_date = datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)
        if datetime.fromisoformat(entry['timestamp']) > expiry_date:
            return entry['response']
    return None


def cache_response(prompt: str, agent_name: str, response: Dict[str, Any]):
    """Cache a response for a given prompt and agent."""
    cache = load_agent_cache()
    cache_key = f"{agent_name}:{prompt}"
    cache[cache_key] = {
        'timestamp': datetime.now().isoformat(),
        'response': response
    }
    save_agent_cache(cache)
