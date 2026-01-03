"""
Configuration management for the AI-Powered Prompt Optimizer SaaS.
Uses pydantic-settings for type-safe configuration with environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # xAI Grok API Configuration
    xai_api_key: str
    xai_api_base: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.1-fast"
    
    # Application Configuration
    secret_key: str
    app_env: str = "development"
    
    # Database
    database_url: str = "sqlite:///prompt_optimizer.db"
    
    # Usage Limits
    free_tier_daily_limit: int = 5
    paid_tier_daily_limit: int = 1000
    
    # Grok Collections API Configuration (Optional - for RAG)
    collection_id_prompt_examples: Optional[str] = None
    collection_id_marketing: Optional[str] = None
    collection_id_technical: Optional[str] = None
    enable_collections: bool = False  # Set to True to enable RAG features
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
# Note: Settings() will raise ValidationError if required fields are missing
# This is expected behavior - ensure .env file is configured
import os

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
        # If .env is missing, provide helpful error
        raise ValueError(
            "Configuration error: Missing required environment variables. "
            "Please create a .env file with XAI_API_KEY and SECRET_KEY. "
            "See env.example for reference."
        ) from e
