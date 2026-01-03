"""
xAI Grok API integration utilities.
Handles API calls to Grok 4.1 Fast with agent tools support for multi-step reasoning.

Note: This implementation uses the OpenAI-compatible client. If xAI provides
a dedicated SDK, you may want to replace this with the official xAI Python SDK.
Check https://x.ai/api for the latest SDK and API documentation.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI
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
    """Wrapper for xAI Grok API with agent tools support."""
    
    def __init__(self, timeout: float = 60.0):
        """
        Initialize Grok API client.
        
        Uses OpenAI-compatible client assuming xAI provides OpenAI-compatible endpoints.
        If xAI has a dedicated SDK (e.g., xai-python), update this accordingly.
        
        Args:
            timeout: Request timeout in seconds (default: 60.0)
            Note: Timeout not set in client init due to version compatibility.
            Timeouts are handled at the request level if needed.
        """
        # Don't set timeout in client init due to OpenAI/httpx version compatibility issue
        # The OpenAI client will use its default timeout (typically 600 seconds)
        # Timeout handling can be added per-request if needed
        self.client = OpenAI(
            api_key=settings.xai_api_key,
            base_url=settings.xai_api_base
        )
        self.model = settings.xai_model
        self.timeout = timeout  # Store for reference, even though not used in client init
    
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
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add tools if provided (for agent capabilities, including Collections)
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice or "auto"
            
            # Note: Grok Collections API uses tool calling with "file_search" tool name
            # Collections are automatically searched when tools are enabled and collections_search is included
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Handle tool calls recursively if present (for Collections API)
            # Grok Collections API: When file_search tool is called, we need to handle it recursively
            tool_calls = None
            content = None
            total_usage = None
            
            if response.choices[0].message.tool_calls:
                logger.info(f"Tool calls detected: {len(response.choices[0].message.tool_calls)} tool(s)")
                
                # Extract tool calls
                tool_calls = []
                for tc in response.choices[0].message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                    except:
                        args = tc.function.arguments
                    
                    tool_calls.append({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": args
                        }
                    })
                
                # Process tool calls and make recursive call with results
                # For Collections API, Grok handles the search server-side, but we need to
                # continue the conversation with tool results
                tool_results = self._process_tool_calls(tool_calls)
                
                # Build messages for recursive call
                recursive_messages = list(messages)  # Copy original messages
                
                # Add assistant message with tool calls
                recursive_messages.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": json.dumps(tc.function.arguments) if isinstance(tc.function.arguments, dict) else str(tc.function.arguments)
                            }
                        }
                        for tc in response.choices[0].message.tool_calls
                    ]
                })
                
                # Add tool results for each tool call
                for tc in response.choices[0].message.tool_calls:
                    recursive_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_results  # Grok will have already executed the search
                    })
                
                # Recursive call with tool results
                logger.info("Making recursive API call with tool results for Collections search...")
                try:
                    recursive_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=recursive_messages,
                        temperature=kwargs.get("temperature", 0.7),
                        max_tokens=kwargs.get("max_tokens", 2000),
                        tools=kwargs.get("tools"),
                        tool_choice=kwargs.get("tool_choice", "auto")
                    )
                    
                    content = recursive_response.choices[0].message.content
                    
                    # Update usage (add recursive call tokens)
                    total_usage = {
                        "prompt_tokens": response.usage.prompt_tokens + recursive_response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens + recursive_response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens + recursive_response.usage.total_tokens,
                    }
                except Exception as e:
                    logger.warning(f"Recursive call failed, using original response: {str(e)}")
                    # Fallback to original response if recursive call fails
                    content = response.choices[0].message.content
                    total_usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
            else:
                # No tool calls, use direct content
                content = response.choices[0].message.content
                total_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            # Post-process to enforce persona (sanitize any accidental mentions)
            if enforce_persona and content:
                content = self._sanitize_persona_content(content)
            
            return {
                "content": content,
                "tool_calls": tool_calls,
                "model": response.model,
                "usage": total_usage,
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            error_msg = str(e)
            # Check for timeout errors (OpenAI client raises various timeout exceptions)
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
    
    def _process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> str:
        """
        Process tool calls (e.g., Collections search).
        
        Note: For Grok Collections API, the search is executed server-side by Grok.
        This method logs the tool calls and prepares for recursive API handling.
        The actual search results are returned by Grok in the recursive API call.
        
        Args:
            tool_calls: List of tool call dictionaries
        
        Returns:
            Formatted tool results as string (for logging/tracking)
        """
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.get("function", {}).get("name", "")
            arguments = tool_call.get("function", {}).get("arguments", {})
            
            if function_name == "file_search":
                # Collections search - Grok executes this server-side
                query = arguments.get("query", "unknown query") if isinstance(arguments, dict) else "unknown query"
                collection_ids = arguments.get("collection_ids", []) if isinstance(arguments, dict) else []
                
                logger.info(f"Collections search tool called: '{query}' in collections {collection_ids}")
                logger.info("Grok will execute the search server-side and return results in recursive call")
                
                # Note: Grok's API handles the actual Collections search automatically
                # We return a placeholder - Grok will provide actual results
                results.append(f"Collections search executed for: {query}")
            else:
                logger.warning(f"Unknown tool call: {function_name}")
                results.append(f"Tool {function_name} called")
        
        # Return formatted results (Grok will provide actual search results in recursive call)
        return "\n".join(results) if results else "Tool calls processed. Grok will provide results."
    
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


# Global API instance with 60-second timeout
grok_api = GrokAPI(timeout=60.0)
