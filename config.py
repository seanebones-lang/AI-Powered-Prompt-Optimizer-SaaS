"""
Configuration management for the AI-Powered Prompt Optimizer SaaS.
Supports both Streamlit Cloud secrets (st.secrets) and environment variables (.env).
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

# Try to import streamlit for secrets access (available in Streamlit Cloud)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get setting from Streamlit secrets first, then environment variables.
    
    Args:
        key: Setting key name
        default: Default value if not found
    
    Returns:
        Setting value or default
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    if STREAMLIT_AVAILABLE and st is not None:
        try:
            # Access secrets dict (st.secrets is a dict-like object)
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass  # Fall through to environment variables
    
    # Fall back to environment variables (for local development)
    return os.getenv(key, default)


class Settings:
    """Application settings loaded from Streamlit secrets or environment variables."""
    
    def __init__(self):
        # xAI Grok API Configuration
        self.xai_api_key = get_setting("XAI_API_KEY") or get_setting("xai_api_key")
        if not self.xai_api_key:
            raise ValueError("XAI_API_KEY is required. Set it in Streamlit secrets or environment variables.")
        
        self.xai_api_base = get_setting("XAI_API_BASE", "https://api.x.ai/v1") or get_setting("xai_api_base", "https://api.x.ai/v1")
        self.xai_model = get_setting("XAI_MODEL", "grok-4.1-fast") or get_setting("xai_model", "grok-4.1-fast")
        
        # Application Configuration
        self.secret_key = get_setting("SECRET_KEY") or get_setting("secret_key")
        if not self.secret_key:
            raise ValueError("SECRET_KEY is required. Set it in Streamlit secrets or environment variables.")
        
        self.app_env = get_setting("APP_ENV", "development") or get_setting("app_env", "development")
        
        # Database
        self.database_url = get_setting("DATABASE_URL", "sqlite:///prompt_optimizer.db") or get_setting("database_url", "sqlite:///prompt_optimizer.db")
        
        # Usage Limits
        free_limit = get_setting("FREE_TIER_DAILY_LIMIT", "5") or get_setting("free_tier_daily_limit", "5")
        paid_limit = get_setting("PAID_TIER_DAILY_LIMIT", "1000") or get_setting("paid_tier_daily_limit", "1000")
        self.free_tier_daily_limit = int(free_limit) if free_limit else 5
        self.paid_tier_daily_limit = int(paid_limit) if paid_limit else 1000
        
        # Grok Collections API Configuration (Optional - for RAG)
        self.collection_id_prompt_examples = get_setting("COLLECTION_ID_PROMPT_EXAMPLES") or get_setting("collection_id_prompt_examples")
        self.collection_id_marketing = get_setting("COLLECTION_ID_MARKETING") or get_setting("collection_id_marketing")
        self.collection_id_technical = get_setting("COLLECTION_ID_TECHNICAL") or get_setting("collection_id_technical")
        
        enable_collections_str = get_setting("ENABLE_COLLECTIONS", "false") or get_setting("enable_collections", "false")
        self.enable_collections = str(enable_collections_str).lower() == "true"


# Global settings instance
# Check if we're in a test environment
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
    # Create a mock settings for testing
    class MockSettings:
        def __init__(self):
            self.xai_api_key = os.getenv("XAI_API_KEY", "test_key")
            self.xai_api_base = os.getenv("XAI_API_BASE", "https://api.x.ai/v1")
            self.xai_model = os.getenv("XAI_MODEL", "grok-4.1-fast")
            self.secret_key = os.getenv("SECRET_KEY", "test_secret")
            self.database_url = os.getenv("DATABASE_URL", "sqlite:///test.db")
            self.free_tier_daily_limit = int(os.getenv("FREE_TIER_DAILY_LIMIT", "5"))
            self.paid_tier_daily_limit = int(os.getenv("PAID_TIER_DAILY_LIMIT", "1000"))
            self.collection_id_prompt_examples = os.getenv("COLLECTION_ID_PROMPT_EXAMPLES")
            self.collection_id_marketing = os.getenv("COLLECTION_ID_MARKETING")
            self.collection_id_technical = os.getenv("COLLECTION_ID_TECHNICAL")
            self.enable_collections = os.getenv("ENABLE_COLLECTIONS", "false").lower() == "true"
    
    settings = MockSettings()
else:
    try:
        settings = Settings()
    except Exception as e:
        # Provide helpful error message
        raise ValueError(
            f"Configuration error: {str(e)}. "
            "For Streamlit Cloud: Set secrets in the app settings (XAI_API_KEY, SECRET_KEY). "
            "For local development: Create a .env file with XAI_API_KEY and SECRET_KEY. "
            "See env.example for reference."
        ) from e
