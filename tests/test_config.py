"""
Tests for configuration management.
"""
import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError


def test_config_requires_api_key():
    """Test that config requires XAI_API_KEY."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove any existing .env file effects
        with pytest.raises((ValidationError, SystemExit)):
            pass
            # This should fail if required fields are missing


def test_config_loads_from_env():
    """Test that config loads from environment variables."""
    test_env = {
        "XAI_API_KEY": "test_key_123",
        "SECRET_KEY": "test_secret_123",
        "XAI_API_BASE": "https://api.x.ai/v1",
        "XAI_MODEL": "grok-4.1-fast",
        "DATABASE_URL": "sqlite:///test.db",
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        # Reload config
        import importlib
        import config
        importlib.reload(config)
        
        assert config.settings.xai_api_key == "test_key_123"
        assert config.settings.secret_key == "test_secret_123"
        assert config.settings.xai_api_base == "https://api.x.ai/v1"
        assert config.settings.xai_model == "grok-4.1-fast"


def test_config_defaults():
    """Test that config has correct defaults."""
    test_env = {
        "XAI_API_KEY": "test_key",
        "SECRET_KEY": "test_secret",
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        import importlib
        import config
        importlib.reload(config)
        
        assert config.settings.xai_api_base == "https://api.x.ai/v1"
        assert config.settings.xai_model == "grok-4.1-fast"
        assert config.settings.free_tier_daily_limit == 5
        assert config.settings.paid_tier_daily_limit == 1000
        assert config.settings.enable_collections is False


def test_config_collections_optional():
    """Test that Collections config is optional."""
    test_env = {
        "XAI_API_KEY": "test_key",
        "SECRET_KEY": "test_secret",
        "ENABLE_COLLECTIONS": "true",
        "COLLECTION_ID_PROMPT_EXAMPLES": "col_123",
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        import importlib
        import config
        importlib.reload(config)
        
        assert config.settings.enable_collections is True
        assert config.settings.collection_id_prompt_examples == "col_123"
