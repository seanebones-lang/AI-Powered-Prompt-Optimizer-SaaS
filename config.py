"""
Configuration management for the AI-Powered Prompt Optimizer SaaS.

This module provides:
- Pydantic-validated settings with type safety
- Environment variable loading with proper defaults
- Support for both Streamlit Cloud secrets and local .env files
- Graceful degradation when non-critical settings are missing

Usage:
    from config import settings

    api_key = settings.xai_api_key
    model = settings.xai_model
"""
import os
import logging
from typing import Optional
from functools import lru_cache

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable with case-insensitive fallback.

    Checks: KEY, key, Key (in that order)

    Args:
        key: The environment variable name
        default: Default value if not found

    Returns:
        The environment variable value or default
    """
    # Try exact case first
    value = os.getenv(key)
    if value is not None:
        return value

    # Try uppercase
    value = os.getenv(key.upper())
    if value is not None:
        return value

    # Try lowercase
    value = os.getenv(key.lower())
    if value is not None:
        return value

    return default


class APISettings(BaseModel):
    """xAI Grok API configuration settings."""

    api_key: str = Field(
        default="",
        description="xAI API key for Grok model access"
    )
    api_base: str = Field(
        default="https://api.x.ai/v1",
        description="xAI API base URL"
    )
    model: str = Field(
        default="grok-4-1-fast-reasoning",
        description="Default Grok model to use"
    )
    light_model: Optional[str] = Field(
        default=None,
        description="Lighter model for simpler tasks"
    )
    timeout: float = Field(
        default=60.0,
        ge=10.0,
        le=300.0,
        description="API request timeout in seconds"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v:
            return ""  # Allow empty, will be caught at runtime
        if len(v) < 10:
            logger.warning("API key appears too short - verify XAI_API_KEY is correct")
        return v

    @field_validator("api_base")
    @classmethod
    def validate_api_base(cls, v: str) -> str:
        """Ensure API base URL is properly formatted."""
        return v.rstrip("/")

    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured."""
        return bool(self.api_key) and self.api_key != "placeholder-key"


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    url: str = Field(
        default="sqlite:///prompt_optimizer.db",
        description="Database connection URL"
    )
    pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Connection pool size"
    )
    pool_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Pool connection timeout in seconds"
    )


class CollectionsSettings(BaseModel):
    """RAG Collections configuration settings."""

    enabled: bool = Field(
        default=False,
        description="Enable Grok Collections for RAG"
    )
    prompt_examples_id: Optional[str] = Field(
        default=None,
        description="Collection ID for prompt examples"
    )
    marketing_id: Optional[str] = Field(
        default=None,
        description="Collection ID for marketing content"
    )
    technical_id: Optional[str] = Field(
        default=None,
        description="Collection ID for technical content"
    )


class AgentSettings(BaseModel):
    """Default agent configuration settings."""

    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for agent calls"
    )
    default_max_tokens: int = Field(
        default=2000,
        ge=100,
        le=8000,
        description="Default max tokens for agent calls"
    )
    preferred_thinking_mode: str = Field(
        default="4d",
        description="Default thinking mode (4d, chain_of_thought, tree_of_thought)"
    )

    @field_validator("preferred_thinking_mode")
    @classmethod
    def validate_thinking_mode(cls, v: str) -> str:
        """Validate thinking mode value."""
        valid_modes = {"4d", "chain_of_thought", "tree_of_thought"}
        if v.lower() not in valid_modes:
            logger.warning(f"Invalid thinking mode '{v}', defaulting to '4d'")
            return "4d"
        return v.lower()


class UserSettings(BaseModel):
    """User preference settings."""

    auto_save_sessions: bool = Field(
        default=True,
        description="Automatically save optimization sessions"
    )
    show_token_costs: bool = Field(
        default=True,
        description="Display token usage and costs"
    )
    default_prompt_type: str = Field(
        default="system_prompt",
        description="Default prompt type selection"
    )


class Settings(BaseSettings):
    """
    Main application settings with Pydantic validation.

    Settings are loaded from environment variables with fallbacks.
    All settings have sensible defaults for development.

    Attributes:
        xai: API configuration for xAI Grok
        database: Database configuration
        collections: RAG Collections configuration
        agents: Default agent settings
        user: User preference settings
        secret_key: Application secret key
        app_env: Application environment (development/production)
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore"
    )

    # Flat settings for backwards compatibility
    secret_key: str = Field(default="development-secret-key-placeholder")
    app_env: str = Field(default="development")

    # Nested settings (loaded manually due to env var naming)
    xai: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    collections: CollectionsSettings = Field(default_factory=CollectionsSettings)
    agents: AgentSettings = Field(default_factory=AgentSettings)
    user: UserSettings = Field(default_factory=UserSettings)

    # Computed properties for backwards compatibility
    @property
    def xai_api_key(self) -> str:
        """Backwards compatible API key access."""
        return self.xai.api_key

    @property
    def xai_api_base(self) -> str:
        """Backwards compatible API base access."""
        return self.xai.api_base

    @property
    def xai_model(self) -> str:
        """Backwards compatible model name access."""
        return self.xai.model

    @property
    def database_url(self) -> str:
        """Backwards compatible database URL access."""
        return self.database.url

    @property
    def enable_collections(self) -> bool:
        """Backwards compatible collections enabled access."""
        return self.collections.enabled

    @property
    def default_temperature(self) -> float:
        """Backwards compatible temperature access."""
        return self.agents.default_temperature

    @property
    def default_max_tokens(self) -> int:
        """Backwards compatible max tokens access."""
        return self.agents.default_max_tokens

    @property
    def preferred_thinking_mode(self) -> str:
        """Backwards compatible thinking mode access."""
        return self.agents.preferred_thinking_mode

    @property
    def auto_save_sessions(self) -> bool:
        """Backwards compatible auto save access."""
        return self.user.auto_save_sessions

    @property
    def show_token_costs(self) -> bool:
        """Backwards compatible token costs access."""
        return self.user.show_token_costs

    @property
    def default_prompt_type(self) -> str:
        """Backwards compatible prompt type access."""
        return self.user.default_prompt_type

    # Collection ID accessors for backwards compatibility
    @property
    def collection_id_prompt_examples(self) -> Optional[str]:
        return self.collections.prompt_examples_id

    @property
    def collection_id_marketing(self) -> Optional[str]:
        return self.collections.marketing_id

    @property
    def collection_id_technical(self) -> Optional[str]:
        return self.collections.technical_id

    def get_config_warnings(self) -> list[str]:
        """Get list of configuration warnings."""
        warnings = []

        if not self.xai.is_configured:
            warnings.append(
                "XAI_API_KEY is not configured. Set it in environment variables or Streamlit secrets."
            )

        if self.secret_key == "development-secret-key-placeholder":
            warnings.append(
                "SECRET_KEY is using development default. Set a secure key for production."
            )

        if self.app_env == "production" and not self.xai.is_configured:
            warnings.append(
                "Running in production mode without valid API key configuration."
            )

        return warnings

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"))


def _load_settings_from_env() -> Settings:
    """
    Load settings from environment variables.

    Handles the mapping from flat env vars to nested Pydantic model.
    """
    # API Settings
    api_key = _get_env("XAI_API_KEY", "")
    if not api_key:
        logger.warning("XAI_API_KEY is not set. Application will show configuration error.")
        api_key = "placeholder-key"

    api_settings = APISettings(
        api_key=api_key,
        api_base=_get_env("XAI_API_BASE", "https://api.x.ai/v1"),
        model=_get_env("XAI_MODEL", "grok-4-1-fast-reasoning"),
        light_model=_get_env("XAI_LIGHT_MODEL"),
        timeout=float(_get_env("XAI_TIMEOUT", "60.0")),
    )

    # Database Settings
    db_settings = DatabaseSettings(
        url=_get_env("DATABASE_URL", "sqlite:///prompt_optimizer.db"),
        pool_size=int(_get_env("DATABASE_POOL_SIZE", "5")),
        pool_timeout=int(_get_env("DATABASE_POOL_TIMEOUT", "30")),
    )

    # Collections Settings
    collections_settings = CollectionsSettings(
        enabled=_get_env("ENABLE_COLLECTIONS", "false").lower() == "true",
        prompt_examples_id=_get_env("COLLECTION_ID_PROMPT_EXAMPLES"),
        marketing_id=_get_env("COLLECTION_ID_MARKETING"),
        technical_id=_get_env("COLLECTION_ID_TECHNICAL"),
    )

    # Agent Settings
    agent_settings = AgentSettings(
        default_temperature=float(_get_env("DEFAULT_TEMPERATURE", "0.7")),
        default_max_tokens=int(_get_env("DEFAULT_MAX_TOKENS", "2000")),
        preferred_thinking_mode=_get_env("PREFERRED_THINKING_MODE", "4d"),
    )

    # User Settings
    user_settings = UserSettings(
        auto_save_sessions=_get_env("AUTO_SAVE_SESSIONS", "true").lower() == "true",
        show_token_costs=_get_env("SHOW_TOKEN_COSTS", "true").lower() == "true",
        default_prompt_type=_get_env("DEFAULT_PROMPT_TYPE", "system_prompt"),
    )

    # Main settings
    secret_key = _get_env("SECRET_KEY")
    if not secret_key:
        logger.warning("SECRET_KEY is not set. Using default secret for development.")
        secret_key = "development-secret-key-placeholder"

    return Settings(
        secret_key=secret_key,
        app_env=_get_env("APP_ENV", "development"),
        xai=api_settings,
        database=db_settings,
        collections=collections_settings,
        agents=agent_settings,
        user=user_settings,
    )


class MockSettings(Settings):
    """Mock settings for testing environment."""

    def __init__(self):
        """Initialize mock settings with test defaults."""
        super().__init__(
            secret_key=os.getenv("SECRET_KEY", "test_secret"),
            app_env="testing",
            xai=APISettings(
                api_key=os.getenv("XAI_API_KEY", "test_key"),
                api_base=os.getenv("XAI_API_BASE", "https://api.x.ai/v1"),
                model=os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
            ),
            database=DatabaseSettings(
                url=os.getenv("DATABASE_URL", "sqlite:///test.db"),
            ),
            collections=CollectionsSettings(
                enabled=os.getenv("ENABLE_COLLECTIONS", "false").lower() == "true",
            ),
            agents=AgentSettings(),
            user=UserSettings(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings (cached).

    Returns MockSettings in test environment, otherwise production Settings.
    """
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
        return MockSettings()
    return _load_settings_from_env()


# Global settings instance for backwards compatibility
settings = get_settings()
