"""
xAI Grok API integration utilities.
Handles API calls to Grok 4.1 Fast with agent tools support for multi-step reasoning.

Uses direct HTTP requests with httpx - verified working approach as of Jan 2026.
"""
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from config import settings
from performance import track_performance
from cache_utils import get_cache
from monitoring import get_metrics
from observability import get_tracker
from circuit_breaker import get_api_circuit_breaker, CircuitBreakerOpenError
from cost_tracker import get_cost_optimizer
from connection_pool import get_pooled_client

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
        
        # Validate API key format (basic check)
        if not self.api_key:
            raise ValueError(
                "XAI_API_KEY is not set. Please set it in Streamlit secrets or environment variables. "
                "Get your API key from https://console.x.ai"
            )
        
        if not isinstance(self.api_key, str) or len(self.api_key) < 10:
            logger.warning(
                f"API key appears invalid (length: {len(self.api_key) if self.api_key else 0}). "
                "Please verify your XAI_API_KEY is correct. Get your API key from https://console.x.ai"
            )
        
        # API Base URL: https://api.x.ai/v1 (verified correct as of Jan 2026)
        self.base_url = settings.xai_api_base.rstrip('/')
        # Model name: grok-4-1-fast-reasoning (use hyphens, not dots)
        # This is the correct model identifier for xAI Grok 4.1 Fast Reasoning
        self.default_model = settings.xai_model  # Default: grok-4-1-fast-reasoning
        # Use fast-reasoning for both default and light model (fast reasoning is already optimized)
        self.light_model = getattr(settings, 'xai_light_model', self.default_model) or self.default_model
        self.timeout = timeout
        
        # Log configuration for debugging (without exposing API key)
        api_key_preview = f"{self.api_key[:4]}***{self.api_key[-2:]}" if len(self.api_key) > 6 else "***"
        logger.info(f"GrokAPI initialized: base_url={self.base_url}, model={self.default_model}, api_key={api_key_preview}")
    
    @track_performance("grok_api.generate_completion")
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        enforce_persona: bool = True,
        use_cache: bool = True
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
            use_cache: Whether to use cached results for identical prompts (default: True)
        
        Returns:
            Dictionary with response content and metadata
        """
        # Check cache first (for non-tool calls)
        if use_cache and not tools:
            cache = get_cache()
            cache_data = {
                'prompt': prompt,
                'system_prompt': system_prompt,
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            cache_hash = hashlib.sha256(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
            cache_key = f"completion:{cache_hash}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug("Cache hit for API completion")
                metrics = get_metrics()
                metrics.increment("api_cache_hits")
                return cached_result
        
        metrics = get_metrics()
        metrics.increment("api_requests")
        
        # Get LLM call tracker for observability
        tracker = get_tracker()
        
        # Get circuit breaker and cost optimizer
        circuit_breaker = get_api_circuit_breaker()
        cost_optimizer = get_cost_optimizer()

        try:
            # Wrap API call in circuit breaker
            def _make_request():
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
                    "model": self.light_model if max_tokens < 1000 else self.default_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                
                # Add tools if provided
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = tool_choice or "auto"
                
                # Make API request
                url = f"{self.base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                logger.debug(f"Making API request to {url} with model {payload['model']}")

                # Use connection pooling for better performance
                # Track LLM call for observability (cost, latency, tokens)
                metrics = get_metrics()
                with metrics.time_block("api_request"):
                    # Use pooled client for connection reuse
                    client = get_pooled_client()
                    response = client.post(url, json=payload, headers=headers)
                    
                    # Log response status
                    logger.debug(f"API response status: {response.status_code}")

                    # Handle non-200 status codes
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"API returned status {response.status_code}: {error_text}")
                        
                        # Safely extract error message from response
                        error_msg = error_text
                        try:
                            # Try to parse as JSON first
                            if isinstance(error_text, str) and error_text.strip().startswith('{'):
                                error_data = response.json()
                                # Handle both dict and string responses
                                if isinstance(error_data, dict):
                                    # Try nested error.message structure
                                    if "error" in error_data:
                                        error_obj = error_data["error"]
                                        if isinstance(error_obj, dict) and "message" in error_obj:
                                            error_msg = error_obj["message"]
                                        elif isinstance(error_obj, str):
                                            error_msg = error_obj
                                    # Try direct message field
                                    elif "message" in error_data:
                                        error_msg = error_data["message"]
                                elif isinstance(error_data, str):
                                    error_msg = error_data
                        except (json.JSONDecodeError, ValueError, KeyError, AttributeError, TypeError) as e:
                            # Fallback to raw error text
                            logger.debug(f"Could not parse error response as JSON: {e}")
                            error_msg = error_text if isinstance(error_text, str) else str(error_text)
                        
                        # Provide helpful error message for authentication issues
                        if response.status_code == 401 or response.status_code == 403:
                            if "API key" in error_msg or "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                                error_msg = f"{error_msg} Please verify your XAI_API_KEY is set correctly in Streamlit secrets or environment variables."
                        
                        raise Exception(f"API error ({response.status_code}): {error_msg}")

                    # Parse JSON response
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {response.text}")
                        raise Exception(f"Invalid JSON response from API: {str(e)}")
                
                return data
            
            # Execute request through circuit breaker
            try:
                data = circuit_breaker.call(_make_request)
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker is open: {str(e)}")
                raise Exception(f"Service temporarily unavailable: {str(e)}")
            except Exception as e:
                # Re-raise any exceptions from _make_request
                # This ensures we never return a string instead of raising
                logger.error(f"Request failed in circuit breaker: {str(e)}")
                raise
            
            # Validate response structure - ensure data is a dict
            # This is critical: we must NEVER return a string from this function
            if not isinstance(data, dict):
                error_msg = f"API returned non-dict response: {type(data)}"
                if isinstance(data, str):
                    error_msg += f" - String content: {data[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Check for error field in response
            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                logger.error(f"API returned error in response: {error_msg}")
                raise Exception(f"API error: {error_msg}")
            
            # Validate choices field
            if "choices" not in data:
                logger.error(f"API response missing 'choices' field. Keys: {list(data.keys())}")
                raise Exception("API response missing 'choices' field")
            
            choices = data.get("choices")
            if choices is None:
                logger.error("API returned None for 'choices' field")
                raise Exception("API returned None for 'choices' field")
            
            if not isinstance(choices, list):
                logger.error(f"API returned invalid 'choices' type: {type(choices)}")
                raise Exception(f"API returned invalid 'choices' type: {type(choices)}")
            
            if len(choices) == 0:
                logger.error("API returned empty choices list")
                raise Exception("API returned empty choices list")
            
            # Get first choice
            choice = choices[0]
            if not isinstance(choice, dict):
                logger.error(f"Invalid choice type: {type(choice)}")
                raise Exception(f"Invalid choice type: {type(choice)}")
            
            if "message" not in choice:
                logger.error(f"Choice missing 'message' field. Keys: {list(choice.keys())}")
                raise Exception("Choice missing 'message' field")
            
            message = choice["message"]
            if not isinstance(message, dict):
                logger.error(f"Invalid message type: {type(message)}")
                raise Exception(f"Invalid message type: {type(message)}")
            
            # Extract content and usage with safe defaults
            content = message.get("content") or ""
            usage_data = data.get("usage")
            if usage_data is None:
                usage_data = {}
            elif not isinstance(usage_data, dict):
                usage_data = {}
            
            # Get model name from response (or use default)
            model_name = data.get("model", self.default_model)

            # Track LLM call for observability (cost, latency, tokens)
            with tracker.track_call(model_name) as llm_call:
                llm_call.set_tokens(usage_data)

            # Record cost
            cost_optimizer.record_cost(
                model=model_name,
                prompt_tokens=usage_data.get("prompt_tokens", 0) or 0,
                completion_tokens=usage_data.get("completion_tokens", 0) or 0,
                operation="api_completion"
            )

            # Handle tool calls if present
            tool_calls = None
            if message.get("tool_calls"):
                logger.info(f"Tool calls detected: {len(message['tool_calls'])} tool(s)")
                tool_calls = message["tool_calls"]

                # For now, just log tool calls - full recursive handling can be added later
                logger.info("Tool calls detected but recursive handling simplified for stability")
            
            # Post-process to enforce persona
            if enforce_persona and content:
                content = self._sanitize_persona_content(content)
            
            # Always return a properly structured dict
            result = {
                "content": content,
                "tool_calls": tool_calls,
                "model": data.get("model", self.default_model),
                "usage": {
                    "prompt_tokens": usage_data.get("prompt_tokens", 0) or 0,
                    "completion_tokens": usage_data.get("completion_tokens", 0) or 0,
                    "total_tokens": usage_data.get("total_tokens", 0) or 0,
                },
                "finish_reason": choice.get("finish_reason", "stop"),
            }
            
            logger.debug(f"Successfully parsed API response. Content length: {len(content)}")
            
            # Cache result if caching enabled and no tools used
            if use_cache and not tools:
                cache = get_cache()
                cache_data = {
                    'prompt': prompt,
                    'system_prompt': system_prompt,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                cache_hash = hashlib.sha256(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
                cache_key = f"completion:{cache_hash}"
                cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error calling Grok API: {error_msg}", exc_info=True)
            
            # Always raise a proper Exception (never return a string)
            # This ensures callers get an exception, not a string response
            if "API error" in error_msg or "API returned" in error_msg:
                raise Exception(error_msg)
            else:
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
        
        try:
            response = self.generate_completion(
                prompt=optimized_prompt,
                system_prompt=additional_system,
                temperature=0.8,
                max_tokens=max_tokens,
                enforce_persona=True
            )
            
            # Validate response is a dict
            if not isinstance(response, dict):
                logger.error(f"generate_optimized_output: response is not a dict: {type(response)}")
                return ""
            
            content = response.get("content", "")
            if not isinstance(content, str):
                content = str(content) if content else ""
            
            return content
        except Exception as e:
            logger.error(f"Error generating optimized output: {str(e)}")
            return ""
    
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
            return response.get("content", "") or ""
        
        return None


# Module-level convenience function (already synchronous)
def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for generating completions.
    
    This is a synchronous wrapper around the GrokAPI class.
    """
    api = GrokAPI()
    return api.generate_completion(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


# Global API instance
grok_api = GrokAPI(timeout=60.0)
