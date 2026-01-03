"""
Tests for API utilities.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch('api_utils.OpenAI') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock chat completions response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 100
        mock_response.model = "grok-4.1-fast"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        yield mock_client


def test_grok_api_initialization(mock_openai_client):
    """Test GrokAPI initialization."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        assert api.model == "grok-4.1-fast"


def test_generate_completion_basic(mock_openai_client):
    """Test basic completion generation."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        response = api.generate_completion("Test prompt")
        
        assert response["content"] == "Test response"
        assert response["usage"]["total_tokens"] == 100
        assert response["model"] == "grok-4.1-fast"
        mock_openai_client.chat.completions.create.assert_called_once()


def test_generate_completion_with_system_prompt(mock_openai_client):
    """Test completion with system prompt."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        api.generate_completion(
            "Test prompt",
            system_prompt="You are a helpful assistant"
        )
        
        # Check that system prompt was included
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert "NextEleven AI" in messages[0]["content"]  # Persona prompt


def test_generate_completion_with_tools(mock_openai_client):
    """Test completion with tools."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        
        api.generate_completion(
            "Test prompt",
            tools=tools
        )
        
        call_args = mock_openai_client.chat.completions.create.call_args
        assert "tools" in call_args[1]
        assert call_args[1]["tools"] == tools


def test_generate_completion_persona_enforcement(mock_openai_client):
    """Test that persona is enforced by default."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        
        # Mock response that mentions Grok (should be sanitized)
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "I am Grok"
        
        response = api.generate_completion("Who are you?")
        
        # Should be sanitized
        assert "Grok" not in response["content"] or "NextEleven AI" in response["content"]


def test_sanitize_persona_content():
    """Test persona content sanitization."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        
        # Test various replacements
        content = "I am Grok, powered by xAI"
        sanitized = api._sanitize_persona_content(content)
        assert "Grok" not in sanitized
        assert "xAI" not in sanitized


def test_handle_identity_query(mock_openai_client):
    """Test identity query handling."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        
        # Test identity query
        response = api.handle_identity_query("Who are you?")
        assert response is not None
        
        # Test non-identity query
        response = api.handle_identity_query("What is the weather?")
        assert response is None


def test_generate_optimized_output(mock_openai_client):
    """Test optimized output generation."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        output = api.generate_optimized_output("Optimized prompt")
        
        assert output == "Test response"
        mock_openai_client.chat.completions.create.assert_called()


def test_api_error_handling(mock_openai_client):
    """Test API error handling."""
    from api_utils import GrokAPI
    
    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4.1-fast"
        
        api = GrokAPI()
        
        # Mock API error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            api.generate_completion("Test prompt")
        
        assert "API call failed" in str(exc_info.value)
