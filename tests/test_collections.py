"""
Tests for Grok Collections API integration.
"""
from unittest.mock import patch
from collections_utils import (
    get_collections_search_tool,
    get_collections_for_prompt_type,
    enable_collections_for_agent,
    is_collections_enabled,
    CollectionsManager
)


def test_get_collections_search_tool():
    """Test collections search tool creation."""
    tool = get_collections_search_tool(["col_123", "col_456"])

    assert tool["type"] == "function"
    assert tool["function"]["name"] == "file_search"
    assert "query" in tool["function"]["parameters"]["properties"]
    assert "collection_ids" in tool["function"]["parameters"]["properties"]


def test_get_collections_for_prompt_type():
    """Test collection selection by prompt type."""
    with patch('collections_utils.get_default_collections') as mock_get:
        mock_get.return_value = {
            "prompt_examples": "col_general",
            "marketing_prompts": "col_marketing",
            "technical_prompts": "col_technical"
        }

        # Test general type
        collections = get_collections_for_prompt_type("creative")
        assert "col_general" in collections

        # Test marketing type
        collections = get_collections_for_prompt_type("marketing")
        assert "col_general" in collections
        assert "col_marketing" in collections

        # Test technical type
        collections = get_collections_for_prompt_type("technical")
        assert "col_general" in collections
        assert "col_technical" in collections


def test_enable_collections_for_agent():
    """Test enabling collections for agents."""
    with patch('collections_utils.get_collections_for_prompt_type') as mock_get:
        mock_get.return_value = ["col_123"]

        tools = enable_collections_for_agent("creative", include_collections=True)
        assert tools is not None
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "file_search"

        # Test disabled
        tools = enable_collections_for_agent("creative", include_collections=False)
        assert tools is None


def test_is_collections_enabled():
    """Test collections enabled check."""
    with patch('collections_utils.settings') as mock_settings:
        mock_settings.enable_collections = True

        with patch('collections_utils.get_default_collections') as mock_get:
            mock_get.return_value = {
                "prompt_examples": "col_123",
                "marketing_prompts": None,
                "technical_prompts": None
            }

            assert is_collections_enabled() is True

            # Test disabled
            mock_settings.enable_collections = False
            assert is_collections_enabled() is False

            # Test no collections
            mock_settings.enable_collections = True
            mock_get.return_value = {
                "prompt_examples": None,
                "marketing_prompts": None,
                "technical_prompts": None
            }
            assert is_collections_enabled() is False


def test_collections_manager():
    """Test CollectionsManager."""
    manager = CollectionsManager()
    assert manager.api is not None


def test_collections_manager_search():
    """Test collections search."""
    manager = CollectionsManager()

    result = manager.search_collections(
        query="test query",
        collection_ids=["col_123"],
        limit=5
    )

    assert result["query"] == "test query"
    assert "col_123" in result["collection_ids"]
