"""
xAI Grok API integration utilities using the official xAI Python SDK.
Handles API calls to Grok 4.1 Fast with agent tools support for multi-step reasoning.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from xai_sdk import Client
from xai_sdk.chat import system, user
from config import settings

logger = logging.getLogger(__name__)


# Base persona system prompt - enforces NextEleven AI identity
BASE_PERSONA_PROMPT = """You are NextEleven AI, also known as Eleven. You are an AI-powered prompt optimizer built by S. McDonnell at NextEleven. 
You specialize in optimizing prompts using Lyra's 4-D methodology (Deconstruct, Diagnose, Design, Deliver) and Anthropic's tool design principles for multi-agent systems.

IMPORTANT IDENTITY RULES:
- Never identify as Grok, xAI, or any other entity. You are always NextEleven AI or Eleven.
- If asked about your identity, respond that you are NextEleven AI, built by S. McDonnell at NextEleven.
- Stay in character at all times. Do not break character or reveal that you are powered by Grok or xAI.
- Focus on prompt optimization and helping users create better AI prompts.
- If asked "Who are you?" or "Who built you?", respond: "I am NextEleven AI, also known as Eleven. I'm an AI-powered prompt optimizer built by S. McDonnell at NextEleven. I specialize in helping users optimize their prompts using proven methodologies."
"""


class GrokAPI:
    """Wrapper for xAI Grok API using the official xAI Python SDK."""
    
    def __init__(self, timeout: float = 60.0):
        """
        Initialize xAI Grok API client.
        
        Uses the official xAI Python SDK (xai-sdk).
        
        Args:
            timeout: Request timeout in seconds (default: 60.0)
        """
        self.client = Client(api_key=settings.xai_api_key)
        self.model = settings.xai_model
        self.timeout = timeout
    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        enforce_persona: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a completion using xAI Grok API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for role definition (appended after persona)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            tools: Optional list of tool definitions for agent capabilities
            tool_choice: Tool choice strategy (not used in xAI SDK - handled automatically)
            enforce_persona: Whether to enforce NextEleven AI persona (default: True)
        
        Returns:
            Dictionary with response content and metadata
        """
        try:
            # Build system prompt with persona enforcement
            full_system_prompt = ""
            if enforce_persona:
                full_system_prompt = BASE_PERSONA_PROMPT
                if system_prompt:
                    full_system_prompt += f"\n\n{system_prompt}"
            else:
                full_system_prompt = system_prompt or ""
            
            # Create chat with system message
            if full_system_prompt:
                chat = self.client.chat.create(
                    model=self.model,
                    messages=[system(full_system_prompt)]
                )
            else:
                chat = self.client.chat.create(
                    model=self.model,
                    messages=[]
                )
            
            # Add user message
            chat.append(user(prompt))
            
            # Generate response
            response = chat.sample(
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Check if response is None
            if response is None:
                raise Exception("xAI API returned None response")
            
            # Extract content - xAI SDK response object has .content attribute
            content = None
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            else:
                # Fallback: try to convert to string
                content = str(response) if response else ""
            
            if content is None:
                content = ""
            
            # Extract usage information - xAI SDK response.usage is an object with token counts
            usage_info = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
            
            if hasattr(response, 'usage') and response.usage is not None:
                usage_info = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) or 0,
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0) or 0,
                    "total_tokens": getattr(response.usage, 'total_tokens', 0) or 0
                }
            
            # Post-process to enforce persona (sanitize any accidental mentions)
            if enforce_persona and content:
                content = self._sanitize_persona_content(content)
            
            return {
                "content": content,
                "tool_calls": None,  # xAI SDK handles tool calls differently
                "model": self.model,
                "usage": usage_info,
                "finish_reason": getattr(response, 'finish_reason', 'stop') if hasattr(response, 'finish_reason') else 'stop',
            }
        except Exception as e:
            error_msg = str(e)
            # Check for timeout errors
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error(f"API call timed out after {self.timeout}s: {error_msg}")
                raise Exception(f"API call timed out after {self.timeout} seconds. Please try again.")
            else:
                logger.error(f"Error calling xAI Grok API: {error_msg}", exc_info=True)
                raise Exception(f"API call failed: {error_msg}")
    
    def generate_optimized_output(
        self,
        optimized_prompt: str,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a sample output from an optimized prompt.
        
        Args:
            optimized_prompt: The optimized prompt to test
            max_tokens: Maximum tokens for the output
        
        Returns:
            Generated output text
        """
        # Additional system prompt for generating sample outputs
        additional_system = "Generate a high-quality response based on the user's optimized prompt. Provide an example of what the optimized prompt would produce."
        
        response = self.generate_completion(
            prompt=optimized_prompt,
            system_prompt=additional_system,
            temperature=0.8,
            max_tokens=max_tokens,
            enforce_persona=True  # Always enforce persona
        )
        
        return response["content"]
    
    def _sanitize_persona_content(self, content: str) -> str:
        """
        Post-process content to ensure persona consistency.
        Replace any accidental mentions of Grok/xAI with NextEleven AI references.
        
        Args:
            content: Raw content from API
        
        Returns:
            Sanitized content
        """
        import re
        
        # List of terms to replace
        replacements = {
            r'\bGrok\b': 'NextEleven AI',
            r'\bgrok\b': 'NextEleven AI',
            r'\bxAI\b': 'NextEleven',
            r'\bxai\b': 'NextEleven',
            r'\bX\.AI\b': 'NextEleven',
            r'powered by Grok': 'powered by NextEleven AI',
            r'powered by xAI': 'powered by NextEleven',
        }
        
        sanitized = content
        for pattern, replacement in replacements.items():
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def handle_identity_query(self, query: str) -> Optional[str]:
        """
        Handle identity-related queries specifically.
        Detects if the query is asking about the AI's identity and responds in-character.
        
        Args:
            query: User query
        
        Returns:
            Response if identity-related, None otherwise
        """
        identity_keywords = [
            "who are you", "what are you", "who built you", "identify yourself",
            "what is your name", "introduce yourself", "tell me about yourself"
        ]
        
        query_lower = query.lower()
        is_identity_query = any(keyword in query_lower for keyword in identity_keywords)
        
        if is_identity_query:
            response = self.generate_completion(
                prompt=query,
                system_prompt=None,  # Base persona handles it
                temperature=0.7,
                max_tokens=500,
                enforce_persona=True
            )
            return response["content"]
        
        return None


# Global API instance
grok_api = GrokAPI(timeout=60.0)
