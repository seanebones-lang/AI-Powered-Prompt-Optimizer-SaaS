"""
Grok Collections API integration for RAG capabilities.
Enables semantic search over curated prompt datasets for enhanced optimization.
"""
import logging
from typing import Dict, List, Optional, Any
from api_utils import grok_api
from config import settings

logger = logging.getLogger(__name__)


def get_default_collections() -> Dict[str, Optional[str]]:
    """
    Get default collection IDs from settings.
    
    Returns:
        Dictionary mapping collection names to IDs
    """
    return {
        "prompt_examples": getattr(settings, 'collection_id_prompt_examples', None),
        "marketing_prompts": getattr(settings, 'collection_id_marketing', None),
        "technical_prompts": getattr(settings, 'collection_id_technical', None),
    }


def get_collections_search_tool(collection_ids: List[str]) -> Dict[str, Any]:
    """
    Create a collections_search tool definition for Grok API.
    
    Based on xAI Collections API (December 2025, production-ready as of January 2026),
    this tool allows Grok to semantically search through uploaded document collections.
    Grok automatically handles the search and returns results in tool calls.
    
    Args:
        collection_ids: List of collection IDs to search
    
    Returns:
        Tool definition dictionary for use in API calls
    """
    return {
        "type": "function",
        "function": {
            "name": "file_search",  # OpenAI-compatible name (Grok uses this)
            "description": """Search through uploaded document collections using semantic search. 
Use this to find relevant prompt examples, templates, or domain-specific knowledge to enhance prompt optimization.
When designing an optimized prompt, search for similar high-quality examples that can inspire your design.
The search uses hybrid semantic+keyword matching for best accuracy.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query in natural language. Describe what you're looking for (e.g., 'marketing email prompts', 'technical API documentation prompts', 'creative writing prompts'). Be specific about the prompt type and use case."
                    },
                    "collection_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of collection IDs to search. Defaults to provided collection_ids if not specified.",
                        "default": collection_ids
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (1-10). Default: 5 for balanced results.",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["semantic", "keyword", "hybrid"],
                        "description": "Search type: 'semantic' for meaning-based (best for finding similar concepts), 'keyword' for exact matches, 'hybrid' for best accuracy (recommended).",
                        "default": "hybrid"
                    }
                },
                "required": ["query"]
            }
        }
    }


def get_collections_for_prompt_type(prompt_type: str) -> List[str]:
    """
    Get appropriate collection IDs for a given prompt type.
    
    Args:
        prompt_type: Type of prompt (creative, technical, marketing, etc.)
    
    Returns:
        List of collection IDs to search
    """
    collections = []
    default_collections = get_default_collections()
    
    # Always include general prompt examples
    if default_collections.get("prompt_examples"):
        collections.append(default_collections["prompt_examples"])
    
    # Add type-specific collections
    prompt_type_lower = prompt_type.lower()
    if prompt_type_lower in ["marketing", "creative"]:
        if default_collections.get("marketing_prompts"):
            collections.append(default_collections["marketing_prompts"])
    elif prompt_type_lower in ["technical", "analytical"]:
        if default_collections.get("technical_prompts"):
            collections.append(default_collections["technical_prompts"])
    
    return collections


def enable_collections_for_agent(
    prompt_type: str,
    include_collections: bool = True
) -> Optional[List[Dict[str, Any]]]:
    """
    Get tools configuration for an agent, optionally including Collections search.
    
    Args:
        prompt_type: Type of prompt being optimized
        include_collections: Whether to include Collections search tool
    
    Returns:
        List of tool definitions, or None if collections disabled or not configured
    """
    if not include_collections:
        return None
    
    collection_ids = get_collections_for_prompt_type(prompt_type)
    
    if not collection_ids:
        logger.warning("No collections configured for prompt type: %s", prompt_type)
        return None
    
    tool = get_collections_search_tool(collection_ids)
    return [tool]


class CollectionsManager:
    """
    Manager class for Grok Collections API operations.
    
    Note: Collection creation and file uploads are typically done via xAI dashboard
    or direct API calls. This class provides helper methods for integration.
    """
    
    def __init__(self):
        self.api = grok_api
    
    def search_collections(
        self,
        query: str,
        collection_ids: List[str],
        limit: int = 5,
        search_type: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Search collections and return results.
        
        Note: In practice, Grok performs this search autonomously via tool calling.
        This method is for direct searches if needed.
        
        Args:
            query: Search query
            collection_ids: Collection IDs to search
            limit: Maximum results (1-10)
            search_type: semantic, keyword, or hybrid
        
        Returns:
            Search results dictionary
        """
        # This would typically be done via Grok's tool calling
        # Direct API calls would use xAI's REST API endpoints
        logger.info(f"Collections search requested: {query} in {collection_ids}")
        
        return {
            "query": query,
            "collection_ids": collection_ids,
            "limit": limit,
            "search_type": search_type,
            "note": "Use Grok's tool calling for actual searches"
        }
    
    def get_collection_info(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a collection.
        
        Args:
            collection_id: Collection ID
        
        Returns:
            Collection metadata or None
        """
        # This would require direct API calls to xAI's Collections API
        # For now, return placeholder
        logger.info(f"Collection info requested: {collection_id}")
        return None


# Global collections manager instance
collections_manager = CollectionsManager()


def is_collections_enabled() -> bool:
    """
    Check if Collections API is enabled (collections configured).
    
    Returns:
        True if Collections is enabled in settings and at least one collection is configured
    """
    if not getattr(settings, 'enable_collections', False):
        return False
    
    default_collections = get_default_collections()
    return any(
        collection_id for collection_id in default_collections.values()
        if collection_id
    )
