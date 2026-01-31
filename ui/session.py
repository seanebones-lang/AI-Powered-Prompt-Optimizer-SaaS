"""
Streamlit session state management utilities.

This module provides type-safe session state access with:
- Defined session keys as constants
- Type hints for session values
- Default value handling
- Session initialization
"""

import streamlit as st
from typing import Any, Optional, TypeVar, Dict
from enum import Enum
from dataclasses import dataclass


class SessionKeys(str, Enum):
    """
    Session state keys as an enum for type safety.

    Using an enum prevents typos and enables IDE autocomplete.
    """
    # Authentication (always True in current version)
    AUTHENTICATED = "authenticated"
    USER_ID = "user_id"
    USERNAME = "username"
    IS_PREMIUM = "is_premium"

    # Current state
    CURRENT_PROMPT = "current_prompt"
    OPTIMIZATION_RESULT = "optimization_result"
    AGENT_CONFIG = "agent_config"
    SHOW_AGENT_TUNING = "show_agent_tuning"

    # History
    HISTORY = "history"

    # Features
    ANALYTICS = "analytics"

    # Navigation
    PAGE = "page"


@dataclass
class SessionDefaults:
    """Default values for session state."""

    AUTHENTICATED: bool = True  # No login required
    USER_ID: int = 1
    USERNAME: str = "User"
    IS_PREMIUM: bool = True  # All features unlocked
    CURRENT_PROMPT: str = ""
    OPTIMIZATION_RESULT: Optional[Dict] = None
    AGENT_CONFIG: Optional[Dict] = None
    SHOW_AGENT_TUNING: bool = False
    HISTORY: list = None
    ANALYTICS: Any = None
    PAGE: str = "optimize"

    def __post_init__(self):
        if self.HISTORY is None:
            self.HISTORY = []


T = TypeVar('T')


def get_session_value(key: SessionKeys, default: T = None) -> T:
    """
    Get a value from session state with type safety.

    Args:
        key: Session key from SessionKeys enum
        default: Default value if key not found

    Returns:
        The session value or default
    """
    return st.session_state.get(key.value, default)


def set_session_value(key: SessionKeys, value: Any) -> None:
    """
    Set a value in session state.

    Args:
        key: Session key from SessionKeys enum
        value: Value to set
    """
    st.session_state[key.value] = value


def update_session_values(**kwargs: Dict[SessionKeys, Any]) -> None:
    """
    Update multiple session values at once.

    Args:
        **kwargs: Key-value pairs where keys are SessionKeys
    """
    for key, value in kwargs.items():
        if isinstance(key, SessionKeys):
            st.session_state[key.value] = value
        else:
            st.session_state[key] = value


def init_session_state() -> None:
    """
    Initialize all session state variables with defaults.

    This should be called once at app startup.
    """
    from agent_config import AgentConfigManager

    defaults = SessionDefaults()

    default_values = {
        SessionKeys.AUTHENTICATED: defaults.AUTHENTICATED,
        SessionKeys.USER_ID: defaults.USER_ID,
        SessionKeys.USERNAME: defaults.USERNAME,
        SessionKeys.IS_PREMIUM: defaults.IS_PREMIUM,
        SessionKeys.CURRENT_PROMPT: defaults.CURRENT_PROMPT,
        SessionKeys.OPTIMIZATION_RESULT: defaults.OPTIMIZATION_RESULT,
        SessionKeys.AGENT_CONFIG: AgentConfigManager.DEFAULT_CONFIG.copy(),
        SessionKeys.SHOW_AGENT_TUNING: defaults.SHOW_AGENT_TUNING,
        SessionKeys.HISTORY: [],
        SessionKeys.ANALYTICS: defaults.ANALYTICS,
        SessionKeys.PAGE: defaults.PAGE,
    }

    for key, value in default_values.items():
        if key.value not in st.session_state:
            st.session_state[key.value] = value


def clear_session() -> None:
    """Clear all session state (for logout/reset)."""
    for key in SessionKeys:
        if key.value in st.session_state:
            del st.session_state[key.value]


def get_current_page() -> str:
    """Get the current page name."""
    return get_session_value(SessionKeys.PAGE, "optimize")


def set_current_page(page: str) -> None:
    """Set the current page and trigger rerun."""
    set_session_value(SessionKeys.PAGE, page)
