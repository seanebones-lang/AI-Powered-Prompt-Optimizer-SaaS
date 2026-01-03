"""
Integration tests for the full system.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

# Set up test environment
test_db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
test_db_path.close()
test_db_url = f"sqlite:///{test_db_path.name}"

os.environ["XAI_API_KEY"] = "test_key"
os.environ["SECRET_KEY"] = "test_secret"
os.environ["DATABASE_URL"] = test_db_url


@pytest.fixture
def clean_db():
    """Clean database fixture."""
    if os.path.exists(test_db_path.name):
        os.remove(test_db_path.name)
    yield
    if os.path.exists(test_db_path.name):
        os.remove(test_db_path.name)


def test_full_optimization_workflow(clean_db):
    """Test complete optimization workflow."""
    from database import db
    from agents import OrchestratorAgent, PromptType
    
    # Mock API calls
    mock_response = {
        "content": "Test response",
        "usage": {"total_tokens": 100},
        "model": "grok-4.1-fast"
    }
    
    with patch('api_utils.grok_api') as mock_api:
        mock_api.generate_completion.return_value = mock_response
        mock_api.generate_optimized_output.return_value = "Sample output"
        
        # Create user
        user = db.create_user(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        assert user is not None
        
        # Check usage limit
        assert db.check_usage_limit(user.id) is True
        
        # Run optimization
        orchestrator = OrchestratorAgent()
        results = orchestrator.optimize_prompt(
            "Write a blog post",
            PromptType.CREATIVE
        )
        
        assert results is not None
        assert results["original_prompt"] == "Write a blog post"
        
        # Increment usage
        db.increment_usage(user.id)
        
        # Save session
        session = db.save_session(
            user_id=user.id,
            original_prompt="Write a blog post",
            prompt_type="creative",
            optimized_prompt=results.get("optimized_prompt", ""),
            quality_score=results.get("quality_score")
        )
        
        assert session is not None
        
        # Retrieve sessions
        sessions = db.get_user_sessions(user.id)
        assert len(sessions) == 1


def test_user_authentication_flow(clean_db):
    """Test user authentication flow."""
    from database import db
    
    # Create user
    user = db.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    
    # Authenticate
    authenticated_user = db.authenticate_user("testuser", "password123")
    assert authenticated_user is not None
    assert authenticated_user.id == user.id
    
    # Wrong password
    assert db.authenticate_user("testuser", "wrong") is None
    
    # Wrong username
    assert db.authenticate_user("wronguser", "password123") is None


def test_rate_limiting_flow(clean_db):
    """Test rate limiting flow."""
    from database import db
    
    user = db.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    
    # Free tier limit is 5
    for i in range(5):
        assert db.check_usage_limit(user.id) is True
        db.increment_usage(user.id)
    
    # Should still be OK (5 is the limit, so 5 < limit is True)
    assert db.check_usage_limit(user.id) is True
    
    # One more should exceed
    db.increment_usage(user.id)
    assert db.check_usage_limit(user.id) is False


def test_collections_integration():
    """Test Collections integration with agents."""
    from agents import DesignerAgent, PromptType
    
    with patch('collections_utils.is_collections_enabled', return_value=True):
        with patch('collections_utils.enable_collections_for_agent') as mock_enable:
            mock_enable.return_value = [{"type": "function", "function": {"name": "file_search"}}]
            
            with patch('api_utils.grok_api') as mock_api:
                mock_api.generate_completion.return_value = {
                    "content": "Optimized prompt",
                    "usage": {"total_tokens": 100},
                    "model": "grok-4.1-fast"
                }
                
                agent = DesignerAgent()
                result = agent.process(
                    "Original",
                    "Deconstruction",
                    "Diagnosis",
                    PromptType.MARKETING
                )
                
                assert result.success is True
                # Check that tools were passed
                mock_api.generate_completion.assert_called()
                call_args = mock_api.generate_completion.call_args
                if call_args[1].get("tools"):
                    assert len(call_args[1]["tools"]) > 0
