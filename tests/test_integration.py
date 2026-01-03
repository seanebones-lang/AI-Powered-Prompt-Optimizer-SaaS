"""
Integration tests for the full system.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import httpx

# Set up test environment
test_db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
test_db_path.close()
test_db_url = f"sqlite:///{test_db_path.name}"

os.environ["XAI_API_KEY"] = "test_key"
os.environ["SECRET_KEY"] = "test_secret"
os.environ["DATABASE_URL"] = test_db_url


@pytest.fixture
def fresh_db():
    """Create a fresh database instance for each test."""
    from database import Database

    # Clean up any existing test database
    if os.path.exists(test_db_path.name):
        os.remove(test_db_path.name)

    db = Database()
    yield db

    # Cleanup
    if os.path.exists(test_db_path.name):
        os.remove(test_db_path.name)


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    def _create_response(content="Test optimized prompt", status_code=200):
        response_data = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1735862400,
            "model": "grok-4-1-fast-reasoning",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 50,
                "total_tokens": 100
            }
        }
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.json.return_value = response_data
        mock_response.text = str(response_data)
        return mock_response
    return _create_response


def test_full_optimization_workflow(fresh_db, mock_httpx_response):
    """Test complete optimization workflow."""
    from agents import OrchestratorAgent, PromptType

    # Mock HTTP pool for API calls
    with patch('api_utils.HTTPConnectionPool') as mock_pool_class:
        mock_client = MagicMock()
        mock_pool_class.get_client.return_value = mock_client
        mock_client.post.return_value = mock_httpx_response("Optimized prompt for creative writing")

        # Create user
        user = fresh_db.create_user(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        assert user is not None

        # Check usage limit (beta mode always returns True)
        assert fresh_db.check_usage_limit(user.id) is True

        # Run optimization
        orchestrator = OrchestratorAgent()
        results = orchestrator.optimize_prompt(
            "Write a blog post",
            PromptType.CREATIVE
        )

        assert results is not None
        assert results["original_prompt"] == "Write a blog post"

        # Increment usage
        fresh_db.increment_usage(user.id)

        # Save session
        session = fresh_db.save_session(
            user_id=user.id,
            original_prompt="Write a blog post",
            prompt_type="creative",
            optimized_prompt=results.get("optimized_prompt", ""),
            quality_score=results.get("quality_score")
        )

        assert session is not None

        # Retrieve sessions
        sessions = fresh_db.get_user_sessions(user.id)
        assert len(sessions) == 1


def test_user_authentication_flow(fresh_db):
    """Test user authentication flow."""
    # Create user
    user = fresh_db.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    assert user is not None

    # Authenticate
    authenticated_user = fresh_db.authenticate_user("testuser", "password123")
    assert authenticated_user is not None
    assert authenticated_user.id == user.id

    # Wrong password
    assert fresh_db.authenticate_user("testuser", "wrong") is None

    # Wrong username
    assert fresh_db.authenticate_user("wronguser", "password123") is None


def test_rate_limiting_flow_beta_mode(fresh_db):
    """Test rate limiting flow in beta mode (no limits enforced)."""
    user = fresh_db.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    assert user is not None

    # Beta mode: check_usage_limit always returns True
    for i in range(10):
        assert fresh_db.check_usage_limit(user.id) is True
        fresh_db.increment_usage(user.id)

    # Should still return True even after exceeding normal limits
    assert fresh_db.check_usage_limit(user.id) is True


def test_collections_integration(mock_httpx_response):
    """Test Collections integration with agents."""
    from agents import DesignerAgent, PromptType

    with patch('collections_utils.is_collections_enabled', return_value=True):
        with patch('collections_utils.enable_collections_for_agent') as mock_enable:
            mock_enable.return_value = [{"type": "function", "function": {"name": "file_search"}}]

            # Mock HTTP pool
            with patch('api_utils.HTTPConnectionPool') as mock_pool_class:
                mock_client = MagicMock()
                mock_pool_class.get_client.return_value = mock_client
                mock_client.post.return_value = mock_httpx_response("Optimized marketing prompt")

                agent = DesignerAgent()
                result = agent.process(
                    "Original",
                    "Deconstruction",
                    "Diagnosis",
                    PromptType.MARKETING
                )

                assert result.success is True
                assert result.content != ""


def test_session_persistence(fresh_db):
    """Test that sessions are properly persisted and retrieved."""
    user = fresh_db.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Create multiple sessions
    for i in range(5):
        fresh_db.save_session(
            user_id=user.id,
            original_prompt=f"Prompt {i}",
            prompt_type="creative",
            optimized_prompt=f"Optimized {i}",
            quality_score=80 + i
        )

    # Verify all sessions are saved
    sessions = fresh_db.get_user_sessions(user.id, limit=10)
    assert len(sessions) == 5

    # Verify ordering (most recent first)
    scores = [s.quality_score for s in sessions]
    assert scores == sorted(scores, reverse=True)


def test_anonymous_user_workflow(fresh_db, mock_httpx_response):
    """Test workflow for anonymous users."""
    from agents import OrchestratorAgent, PromptType

    with patch('api_utils.HTTPConnectionPool') as mock_pool_class:
        mock_client = MagicMock()
        mock_pool_class.get_client.return_value = mock_client
        mock_client.post.return_value = mock_httpx_response("Optimized prompt")

        # Anonymous usage should work
        assert fresh_db.check_usage_limit(None) is True

        # Run optimization without user (using CREATIVE as a valid PromptType)
        orchestrator = OrchestratorAgent()
        results = orchestrator.optimize_prompt(
            "Test prompt",
            PromptType.CREATIVE
        )

        assert results is not None

        # Save anonymous session
        session = fresh_db.save_session(
            user_id=None,
            original_prompt="Test prompt",
            prompt_type="creative"
        )

        assert session is not None
        assert session.user_id is None
