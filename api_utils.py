"""
xAI Grok API integration utilities.
Handles API calls to Grok 4.1 Fast with agent tools support for multi-step reasoning.

Uses direct HTTP requests with httpx for maximum compatibility.
"""
import json
import logging
from typing import Dict, List, Optional, Any
import httpx
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
    """Wrapper for xAI Grok API using direct HTTP requests."""
    
    def __init__(self, timeout: float = 60.0):
        """
        Initialize Grok API client.
        
        Uses direct HTTP requests with httpx for maximum compatibility.
        
        Args:
            timeout: Request timeout in seconds (default: 60.0)
        """
        self.api_key = settings.xai_api_key
        self.base_url = settings.xai_api_base.rstrip('/')
        self.model = settings.xai_model
        self.timeout = timeout
        # Don't create persistent client - create new one per request to avoid connection issues
    
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
        Generate a completion using Grok API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for role definition (appended after persona)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            tools: Optional list of tool definitions for agent capabilities
            tool_choice: Tool choice strategy ("auto", "required", or specific tool name)
            enforce_persona: Whether to enforce NextEleven AI persona (default: True)
        
        Returns:
            Dictionary with response content and metadata
        """
        try:
            messages = []
            
            # Build system prompt with persona enforcement
            full_system_prompt = ""
            if enforce_persona:
                full_system_prompt = BASE_PERSONA_PROMPT
                if system_prompt:
                    full_system_prompt += f"\n\n{system_prompt}"
            else:
                full_system_prompt = system_prompt or ""
            
            if full_system_prompt:
                messages.append({"role": "system", "content": full_system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add tools if provided
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice or "auto"
            
            # Make API request - create client per request for better compatibility
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            with httpx.Client(timeout=httpx.Timeout(self.timeout, connect=10.0)) as client:
                response = client.post(url, json=payload, headers=headers)
                
                # Check for HTTP errors first
                if response.status_code != 200:
                    error_text = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", error_text)
                    except:
                        error_msg = error_text
                    raise Exception(f"API error ({response.status_code}): {error_msg}")
                
                data = response.json()
            
            # Validate response structure
            if data is None:
                raise Exception("API returned None response")
            
            if not isinstance(data, dict):
                raise Exception(f"Invalid API response format (expected dict, got {type(data)}): {data}")
            
            # Check for error in response
            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                raise Exception(f"API returned error: {error_msg}")
            
            if "choices" not in data:
                raise Exception(f"API response missing 'choices' field: {list(data.keys())}")
            
            choices = data.get("choices")
            if choices is None:
                raise Exception("API returned None for 'choices' field")
            
            if not isinstance(choices, list):
                raise Exception(f"API returned invalid 'choices' type (expected list, got {type(choices)}): {choices}")
            
            if len(choices) == 0:
                raise Exception("API returned empty choices list")
            
            # Handle response
            choice = choices[0]
            if choice is None:
                raise Exception("First choice is None")
            
            if not isinstance(choice, dict):
                raise Exception(f"Invalid choice format (expected dict, got {type(choice)}): {choice}")
            
            if "message" not in choice:
                raise Exception(f"Choice missing 'message' field: {list(choice.keys())}")
            
            message = choice["message"]
            if message is None:
                raise Exception("Message is None")
            
            # Handle tool calls if present
            tool_calls = None
            content = message.get("content")
            usage = data.get("usage") or {}  # Ensure usage is always a dict, never None
            
            if message.get("tool_calls"):
                logger.info(f"Tool calls detected: {len(message['tool_calls'])} tool(s)")
                tool_calls = message["tool_calls"]
                
                # Process tool calls and make recursive call
                tool_results = self._process_tool_calls(tool_calls)
                
                # Build recursive messages
                recursive_messages = list(messages)
                recursive_messages.append({
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": tool_calls
                })
                
                # Add tool results
                for tc in tool_calls:
                    recursive_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_results
                    })
                
                # Recursive call
                logger.info("Making recursive API call with tool results...")
                try:
                    recursive_payload = {
                        "model": self.model,
                        "messages": recursive_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                    if tools:
                        recursive_payload["tools"] = tools
                        recursive_payload["tool_choice"] = tool_choice or "auto"
                    
                    with httpx.Client(timeout=httpx.Timeout(self.timeout, connect=10.0)) as recursive_client:
                        recursive_response = recursive_client.post(url, json=recursive_payload, headers=headers)
                        
                        if recursive_response.status_code != 200:
                            error_text = recursive_response.text
                            raise Exception(f"Recursive API error ({recursive_response.status_code}): {error_text}")
                        
                        recursive_data = recursive_response.json()
                    
                    if not recursive_data or not isinstance(recursive_data, dict):
                        raise Exception(f"Invalid recursive response: {recursive_data}")
                    
                    recursive_choices = recursive_data.get("choices")
                    if not recursive_choices or not isinstance(recursive_choices, list) or len(recursive_choices) == 0:
                        raise Exception(f"Invalid recursive choices: {recursive_choices}")
                    
                    recursive_choice = recursive_choices[0]
                    if not recursive_choice or "message" not in recursive_choice:
                        raise Exception(f"Invalid recursive choice: {recursive_choice}")
                    
                    content = recursive_choice["message"].get("content")
                    recursive_usage = recursive_data.get("usage", {}) or {}
                    
                    # Combine usage
                    usage = {
                        "prompt_tokens": usage.get("prompt_tokens", 0) + recursive_usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0) + recursive_usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0) + recursive_usage.get("total_tokens", 0),
                    }
                except Exception as e:
                    logger.warning(f"Recursive call failed: {str(e)}")
                    # Use original response - ensure usage is always a dict
                    usage = data.get("usage") or {}
            
            # Post-process to enforce persona
            if enforce_persona and content:
                content = self._sanitize_persona_content(content)
            
            return {
                "content": content or "",
                "tool_calls": tool_calls,
                "model": data.get("model", self.model),
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "finish_reason": choice.get("finish_reason", "stop"),
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Error calling Grok API: {error_msg}", exc_info=True)
            raise Exception(f"API call failed: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error(f"API call timed out after {self.timeout}s: {error_msg}")
                raise Exception(f"API call timed out after {self.timeout} seconds. Please try again.")
            else:
                logger.error(f"Error calling Grok API: {error_msg}", exc_info=True)
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
        additional_system = "Generate a high-quality response based on the user's optimized prompt. Provide an example of what the optimized prompt would produce."
        
        response = self.generate_completion(
            prompt=optimized_prompt,
            system_prompt=additional_system,
            temperature=0.8,
            max_tokens=max_tokens,
            enforce_persona=True
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
    
    def _process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> str:
        """
        Process tool calls (e.g., Collections search).
        
        Args:
            tool_calls: List of tool call dictionaries
        
        Returns:
            Formatted tool results as string
        """
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.get("function", {}).get("name", "")
            arguments = tool_call.get("function", {}).get("arguments", {})
            
            if function_name == "file_search":
                query = arguments.get("query", "unknown query") if isinstance(arguments, dict) else "unknown query"
                collection_ids = arguments.get("collection_ids", []) if isinstance(arguments, dict) else []
                logger.info(f"Collections search tool called: '{query}' in collections {collection_ids}")
                results.append(f"Collections search executed for: {query}")
            else:
                logger.warning(f"Unknown tool call: {function_name}")
                results.append(f"Tool {function_name} called")
        
        return "\n".join(results) if results else "Tool calls processed."
    
    def handle_identity_query(self, query: str) -> Optional[str]:
        """
        Handle identity-related queries specifically.
        
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
                system_prompt=None,
                temperature=0.7,
                max_tokens=500,
                enforce_persona=True
            )
            return response["content"]
        
        return None
    


# Global API instance
grok_api = GrokAPI(timeout=60.0)
