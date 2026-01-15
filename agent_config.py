"""
Custom agent configuration module for premium users.
Allows users to customize agent behavior, temperature, and other parameters.
"""
import logging
import json
from typing import Dict, Any, Optional
from database import db, AgentConfig
from agents import OrchestratorAgent

logger = logging.getLogger(__name__)


class AgentConfigManager:
    """Manages custom agent configurations for premium users."""
    
    DEFAULT_CONFIG = {
        "temperature": 0.2,
        "max_tokens": 4000,
        "deconstructor": {
            "temperature": 0.2,
            "max_tokens": 4000
        },
        "diagnoser": {
            "temperature": 0.2,
            "max_tokens": 4000
        },
        "designer": {
            "temperature": 0.2,
            "max_tokens": 4000
        },
        "evaluator": {
            "temperature": 0.2,
            "max_tokens": 4000
        },
        "use_parallel_execution": True,
        "enable_collections": False
    }
    
    @staticmethod
    def create_config(
        user_id: int,
        name: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        is_default: bool = False
    ) -> Optional[AgentConfig]:
        """
        Create a custom agent configuration.
        
        Args:
            user_id: User ID
            name: Configuration name
            config: Configuration dictionary
            description: Optional description
            is_default: Whether this should be the default config
            
        Returns:
            AgentConfig object or None
        """
        try:
            # Merge with defaults
            merged_config = AgentConfigManager.DEFAULT_CONFIG.copy()
            merged_config.update(config)
            
            # Validate config
            if not AgentConfigManager._validate_config(merged_config):
                logger.error("Invalid agent configuration")
                return None
            
            config_json = json.dumps(merged_config)
            return db.create_agent_config(
                user_id,
                name,
                config_json,
                description,
                is_default
            )
        except Exception as e:
            logger.error(f"Error creating agent config: {str(e)}")
            return None
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> bool:
        """Validate agent configuration."""
        try:
            # Check required fields
            if "temperature" not in config:
                return False
            
            # Validate temperature range
            if not (0.0 <= config["temperature"] <= 2.0):
                return False
            
            # Validate max_tokens
            if "max_tokens" in config and config["max_tokens"] < 1:
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_user_configs(user_id: int) -> list:
        """Get all agent configurations for a user."""
        try:
            configs = db.get_agent_configs(user_id)
            return [
                {
                    "id": config.id,
                    "name": config.name,
                    "description": config.description,
                    "config": json.loads(config.config_json),
                    "is_default": config.is_default,
                    "created_at": config.created_at.isoformat()
                }
                for config in configs
            ]
        except Exception as e:
            logger.error(f"Error getting user configs: {str(e)}")
            return []
    
    @staticmethod
    def get_default_config(user_id: int) -> Optional[Dict[str, Any]]:
        """Get default agent configuration for a user."""
        try:
            config = db.get_default_agent_config(user_id)
            if config:
                return json.loads(config.config_json)
            return AgentConfigManager.DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Error getting default config: {str(e)}")
            return AgentConfigManager.DEFAULT_CONFIG
    
    @staticmethod
    def apply_config_to_agent(
        orchestrator: OrchestratorAgent,
        config: Dict[str, Any]
    ) -> OrchestratorAgent:
        """
        Apply configuration to an orchestrator agent.

        Creates a new OrchestratorAgent instance with the specified configuration.

        Args:
            orchestrator: OrchestratorAgent instance (not used in current implementation)
            config: Configuration dictionary

        Returns:
            New OrchestratorAgent instance with applied configuration
        """
        # Validate config first
        if not AgentConfigManager._validate_config(config):
            logger.warning("Invalid agent configuration provided, using defaults")
            config = AgentConfigManager.DEFAULT_CONFIG

        # Create new orchestrator with config
        return OrchestratorAgent(config=config)
