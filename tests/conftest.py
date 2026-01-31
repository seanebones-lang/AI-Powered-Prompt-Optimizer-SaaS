"""
Shared pytest fixtures for the prompt optimizer test suite.

IMPORTANT: Environment variables must be set before any project imports.
"""
import os

# Set test environment BEFORE any other imports
os.environ["XAI_API_KEY"] = "test-api-key-12345"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    from database import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a fresh database session for each test."""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_grok_response():
    """Standard mock response from xAI Grok API."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1735862400,
        "model": "grok-4-1-fast",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Test response content with analysis and score: 85/100"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_grok_api(mock_grok_response):
    """Mock the GrokAPI.generate_completion method."""
    with patch('api_utils.grok_api.generate_completion') as mock:
        mock.return_value = {
            "content": mock_grok_response["choices"][0]["message"]["content"],
            "model": mock_grok_response["model"],
            "usage": mock_grok_response["usage"]
        }
        yield mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API calls."""
    with patch('api_utils.HTTPConnectionPool.get_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing various scenarios."""
    return {
        "vague": "Write something about AI",
        "technical": "Explain how transformer attention mechanisms work in detail",
        "creative": "Write a poem about the ocean",
        "empty": "",
        "whitespace": "   \n\t   ",
        "long": "A" * 10000,
        "unicode": "Write about Japanese culture and use emoji: \U0001F389",
        "special_chars": "Test with <script>alert('xss')</script> and SQL; DROP TABLE;",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for tests."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepassword123"
    }


@pytest.fixture
def prompt_types():
    """All supported prompt types."""
    from agents import PromptType
    return list(PromptType)


@pytest.fixture
def mock_settings():
    """Mock settings with test values."""
    with patch('config.settings') as mock:
        mock.xai_api_key = "test-api-key"
        mock.xai_model = "grok-4-1-fast"
        mock.xai_api_base = "https://api.x.ai/v1"
        mock.database_url = "sqlite:///:memory:"
        mock.default_temperature = 0.7
        mock.default_max_tokens = 2000
        mock.enable_collections = False
        yield mock
