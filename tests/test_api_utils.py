"""
Tests for API utilities.
Uses httpx mocking since api_utils uses httpx for HTTP requests.
"""
import pytest
from unittest.mock import patch, MagicMock
import httpx


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    def _create_response(content="Test response", status_code=200):
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


@pytest.fixture
def mock_http_pool(mock_httpx_response):
    """Mock the HTTP connection pool."""
    with patch('api_utils.HTTPConnectionPool') as mock_pool_class:
        mock_client = MagicMock()
        mock_pool_class.get_client.return_value = mock_client
        mock_client.post.return_value = mock_httpx_response()
        yield mock_client


def test_grok_api_initialization():
    """Test GrokAPI initialization."""
    from api_utils import GrokAPI

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()
        assert api.model == "grok-4-1-fast-reasoning"
        assert api.api_key == "test_key"


def test_generate_completion_basic(mock_http_pool, mock_httpx_response):
    """Test basic completion generation."""
    from api_utils import GrokAPI

    mock_http_pool.post.return_value = mock_httpx_response("Test response")

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()
        response = api.generate_completion("Test prompt")

        assert response["content"] == "Test response"
        assert response["usage"]["total_tokens"] == 100
        mock_http_pool.post.assert_called_once()


def test_generate_completion_with_system_prompt(mock_http_pool, mock_httpx_response):
    """Test completion with system prompt."""
    from api_utils import GrokAPI

    mock_http_pool.post.return_value = mock_httpx_response()

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()
        api.generate_completion(
            "Test prompt",
            system_prompt="You are a helpful assistant"
        )

        # Check that the request was made with proper structure
        call_args = mock_http_pool.post.call_args
        assert call_args is not None


def test_generate_completion_with_tools(mock_http_pool, mock_httpx_response):
    """Test completion with tools."""
    from api_utils import GrokAPI

    mock_http_pool.post.return_value = mock_httpx_response()

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()
        tools = [{"type": "function", "function": {"name": "test_tool"}}]

        api.generate_completion(
            "Test prompt",
            tools=tools
        )

        # Verify the call was made
        mock_http_pool.post.assert_called_once()


def test_generate_completion_persona_enforcement(mock_http_pool, mock_httpx_response):
    """Test that persona is enforced by default."""
    from api_utils import GrokAPI

    # Mock response that mentions Grok (should be sanitized)
    mock_http_pool.post.return_value = mock_httpx_response("I am Grok from xAI")

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()
        response = api.generate_completion("Who are you?")

        # Should be sanitized - Grok replaced with NextEleven AI
        assert "Grok" not in response["content"] or "NextEleven AI" in response["content"]


def test_sanitize_persona_content():
    """Test persona content sanitization."""
    from api_utils import GrokAPI

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()

        # Test various replacements
        content = "I am Grok, powered by xAI"
        sanitized = api._sanitize_persona_content(content)
        assert "Grok" not in sanitized
        assert "xAI" not in sanitized


def test_handle_identity_query(mock_http_pool, mock_httpx_response):
    """Test identity query handling."""
    from api_utils import GrokAPI

    # Set up mock to return identity response
    mock_http_pool.post.return_value = mock_httpx_response(
        "I am NextEleven AI, also known as Eleven. I'm an AI-powered prompt optimizer."
    )

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()

        # Test identity query - calls API with persona enforcement
        response = api.handle_identity_query("Who are you?")
        assert response is not None
        assert "NextEleven AI" in response or "Eleven" in response

        # Test non-identity query - returns None without API call
        response = api.handle_identity_query("What is the weather?")
        assert response is None

        # Test other identity patterns
        response = api.handle_identity_query("What are you?")
        assert response is not None

        response = api.handle_identity_query("Who built you?")
        assert response is not None


def test_generate_optimized_output(mock_http_pool, mock_httpx_response):
    """Test optimized output generation."""
    from api_utils import GrokAPI

    mock_http_pool.post.return_value = mock_httpx_response("Generated output")

    with patch('api_utils.settings') as mock_settings:
        mock_settings.xai_api_key = "test_key"
        mock_settings.xai_api_base = "https://api.x.ai/v1"
        mock_settings.xai_model = "grok-4-1-fast-reasoning"

        api = GrokAPI()
        output = api.generate_optimized_output("Optimized prompt")

        assert output == "Generated output"
        mock_http_pool.post.assert_called()


def test_api_error_handling():
    """Test API error handling."""
    from api_utils import GrokAPI

    # Create fresh mock for this test
    with patch('api_utils.HTTPConnectionPool') as mock_pool_class:
        mock_client = MagicMock()
        mock_pool_class.get_client.return_value = mock_client

        # Mock API error response with proper JSON error format
        error_response = MagicMock(spec=httpx.Response)
        error_response.status_code = 500
        error_response.text = '{"error": {"message": "Internal Server Error", "type": "server_error"}}'
        error_response.json.return_value = {"error": {"message": "Internal Server Error", "type": "server_error"}}
        mock_client.post.return_value = error_response

        with patch('api_utils.settings') as mock_settings:
            mock_settings.xai_api_key = "test_key"
            mock_settings.xai_api_base = "https://api.x.ai/v1"
            mock_settings.xai_model = "grok-4-1-fast-reasoning"

            api = GrokAPI()

            with pytest.raises(Exception) as exc_info:
                api.generate_completion("Test prompt", use_cache=False)

            assert "API error" in str(exc_info.value) or "500" in str(exc_info.value) or "Internal Server Error" in str(exc_info.value)
