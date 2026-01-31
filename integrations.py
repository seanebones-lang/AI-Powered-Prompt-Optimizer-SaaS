"""
Integration modules for Slack, Discord, and Notion.
Allows users to optimize prompts directly from these platforms.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from agents import OrchestratorAgent, PromptType
from database import db
from input_validation import sanitize_and_validate_prompt, validate_prompt_type

logger = logging.getLogger(__name__)


class SlackIntegration:
    """Slack integration for prompt optimization."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack integration.
        
        Args:
            webhook_url: Slack webhook URL for sending messages
        """
        self.webhook_url = webhook_url
        self.orchestrator = OrchestratorAgent()

    def handle_slash_command(
        self,
        command_text: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle Slack slash command.
        
        Args:
            command_text: Command text from Slack
            user_id: User ID
            
        Returns:
            Response dictionary for Slack
        """
        try:
            # Parse command (format: /optimize <prompt> [type])
            parts = command_text.split(maxsplit=1)
            if len(parts) < 1:
                return {
                    "response_type": "ephemeral",
                    "text": "Usage: /optimize <prompt> [type]\nExample: /optimize Write a blog post about AI creative"
                }

            prompt = parts[0] if len(parts) == 1 else parts[1]
            prompt_type = "creative"  # Default

            # Extract prompt type if provided
            if " " in prompt:
                words = prompt.split()
                if words[-1] in ["creative", "technical", "analytical", "educational", "marketing"]:
                    prompt_type = words[-1]
                    prompt = " ".join(words[:-1])

            # Validate and sanitize
            is_valid, sanitized_prompt, validation_error = sanitize_and_validate_prompt(prompt)
            if not is_valid:
                return {
                    "response_type": "ephemeral",
                    "text": f"❌ Error: {validation_error}"
                }

            is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
            if not is_valid_type:
                return {
                    "response_type": "ephemeral",
                    "text": f"❌ Error: {type_error}"
                }

            # Check usage limit
            if not db.check_usage_limit(user_id):
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Daily usage limit exceeded. Upgrade to premium for unlimited access!"
                }

            # Optimize
            results = self.orchestrator.optimize_prompt(sanitized_prompt, prompt_type_enum)

            # Increment usage
            db.increment_usage(user_id)

            # Format response
            quality_score = results.get("quality_score", "N/A")
            optimized_prompt = results.get("optimized_prompt", "")

            return {
                "response_type": "in_channel",
                "text": f"✅ Prompt Optimized (Quality Score: {quality_score}/100)",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Original Prompt:*\n{sanitized_prompt}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Optimized Prompt:*\n{optimized_prompt}"
                        }
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error handling Slack command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": f"❌ Error: {str(e)}"
            }

    def send_webhook_message(self, message: str, channel: Optional[str] = None):
        """Send a message to Slack via webhook."""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            payload = {
                "text": message
            }
            if channel:
                payload["channel"] = channel

            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error sending Slack webhook: {str(e)}")
            return False


class DiscordIntegration:
    """Discord integration for prompt optimization."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Discord integration.
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
        self.orchestrator = OrchestratorAgent()

    def handle_command(
        self,
        command_text: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle Discord command.
        
        Args:
            command_text: Command text from Discord
            user_id: User ID
            
        Returns:
            Response dictionary for Discord
        """
        try:
            # Parse command (format: !optimize <prompt> [type])
            parts = command_text.split(maxsplit=1)
            if len(parts) < 1:
                return {
                    "content": "Usage: `!optimize <prompt> [type]`\nExample: `!optimize Write a blog post about AI creative`"
                }

            prompt = parts[0] if len(parts) == 1 else parts[1]
            prompt_type = "creative"  # Default

            # Extract prompt type if provided
            if " " in prompt:
                words = prompt.split()
                if words[-1] in ["creative", "technical", "analytical", "educational", "marketing"]:
                    prompt_type = words[-1]
                    prompt = " ".join(words[:-1])

            # Validate and sanitize
            is_valid, sanitized_prompt, validation_error = sanitize_and_validate_prompt(prompt)
            if not is_valid:
                return {
                    "content": f"❌ Error: {validation_error}"
                }

            is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
            if not is_valid_type:
                return {
                    "content": f"❌ Error: {type_error}"
                }

            # Check usage limit
            if not db.check_usage_limit(user_id):
                return {
                    "content": "❌ Daily usage limit exceeded. Upgrade to premium for unlimited access!"
                }

            # Optimize
            results = self.orchestrator.optimize_prompt(sanitized_prompt, prompt_type_enum)

            # Increment usage
            db.increment_usage(user_id)

            # Format response
            quality_score = results.get("quality_score", "N/A")
            optimized_prompt = results.get("optimized_prompt", "")

            return {
                "embeds": [
                    {
                        "title": "✅ Prompt Optimized",
                        "description": f"Quality Score: **{quality_score}/100**",
                        "fields": [
                            {
                                "name": "Original Prompt",
                                "value": sanitized_prompt[:1000],
                                "inline": False
                            },
                            {
                                "name": "Optimized Prompt",
                                "value": optimized_prompt[:1000],
                                "inline": False
                            }
                        ],
                        "color": 0x00BFA5  # Teal color
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error handling Discord command: {str(e)}")
            return {
                "content": f"❌ Error: {str(e)}"
            }

    def send_webhook_message(self, content: str, embeds: Optional[list] = None):
        """Send a message to Discord via webhook."""
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        try:
            payload = {
                "content": content
            }
            if embeds:
                payload["embeds"] = embeds

            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {str(e)}")
            return False


class NotionIntegration:
    """Notion integration for prompt optimization."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Notion integration.
        
        Args:
            api_key: Notion API key
        """
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.orchestrator = OrchestratorAgent()

    def optimize_and_update_page(
        self,
        page_id: str,
        prompt_property: str,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Optimize a prompt from a Notion page and update it.
        
        Args:
            page_id: Notion page ID
            prompt_property: Property name containing the prompt
            user_id: User ID
            
        Returns:
            True if successful
        """
        if not self.api_key:
            logger.warning("Notion API key not configured")
            return False

        try:
            # Get page content
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }

            with httpx.Client(timeout=30.0) as client:
                # Get page
                page_response = client.get(
                    f"{self.base_url}/pages/{page_id}",
                    headers=headers
                )
                page_response.raise_for_status()
                page_data = page_response.json()

                # Extract prompt
                prompt = page_data.get("properties", {}).get(prompt_property, {}).get("rich_text", [{}])[0].get("plain_text", "")

                if not prompt:
                    logger.error("No prompt found in Notion page")
                    return False

                # Validate and sanitize
                is_valid, sanitized_prompt, validation_error = sanitize_and_validate_prompt(prompt)
                if not is_valid:
                    logger.error(f"Invalid prompt: {validation_error}")
                    return False

                # Check usage limit
                if not db.check_usage_limit(user_id):
                    logger.error("Usage limit exceeded")
                    return False

                # Optimize (using creative as default type)
                results = self.orchestrator.optimize_prompt(sanitized_prompt, PromptType.CREATIVE)

                # Increment usage
                db.increment_usage(user_id)

                # Update page with optimized prompt
                optimized_prompt = results.get("optimized_prompt", "")
                update_payload = {
                    "properties": {
                        f"{prompt_property}_optimized": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": optimized_prompt
                                    }
                                }
                            ]
                        }
                    }
                }

                update_response = client.patch(
                    f"{self.base_url}/pages/{page_id}",
                    headers=headers,
                    json=update_payload
                )
                update_response.raise_for_status()

                return True
        except Exception as e:
            logger.error(f"Error updating Notion page: {str(e)}")
            return False
