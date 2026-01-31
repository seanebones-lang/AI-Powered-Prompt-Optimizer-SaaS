"""
Shared UI components for the Prompt Optimizer.

This module contains reusable Streamlit components:
- Custom CSS styling
- Configuration warnings display
- Error handling with retry
- Metric cards and displays
"""

import streamlit as st
from typing import Optional, Callable, Any, List
import logging

from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Custom CSS Styling
# =============================================================================

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00BFA5;
        margin-bottom: 2rem;
    }
    .premium-badge {
        background-color: #FFD700;
        color: #000;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #00BFA5;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #009688;
    }
    .error-card {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .success-card {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .metric-card {
        background-color: #f5f5f5;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00BFA5;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #666;
    }
</style>
"""


def apply_custom_css() -> None:
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# Configuration Warnings
# =============================================================================

def show_config_warnings() -> bool:
    """
    Display configuration warnings if any exist.

    Returns:
        True if warnings were shown, False otherwise
    """
    warnings = settings.get_config_warnings()

    if not warnings:
        return False

    st.warning("Configuration Issues Detected:")
    for warning in warnings:
        st.write(f"- {warning}")
    st.markdown("---")

    return True


def show_api_not_configured() -> None:
    """Show a message when API is not configured."""
    st.error(
        "API is not configured. Please set XAI_API_KEY in your environment variables "
        "or Streamlit secrets to use this feature."
    )
    st.info(
        "Get your API key from [console.x.ai](https://console.x.ai)"
    )


# =============================================================================
# Error Display Components
# =============================================================================

def show_error_with_retry(
    error_message: str,
    retry_callback: Optional[Callable[[], Any]] = None,
    retry_label: str = "Retry"
) -> None:
    """
    Display an error with optional retry button.

    Args:
        error_message: Error message to display
        retry_callback: Optional callback function for retry
        retry_label: Label for retry button
    """
    st.error(f"Error: {error_message}")

    if retry_callback:
        if st.button(retry_label, type="secondary"):
            try:
                retry_callback()
                st.rerun()
            except Exception as e:
                logger.error(f"Retry failed: {e}")
                st.error(f"Retry failed: {str(e)}")


def show_errors_expandable(
    errors: List[str],
    title: str = "Errors",
    expanded: bool = False
) -> None:
    """
    Display errors in an expandable section.

    Args:
        errors: List of error messages
        title: Title for the expander
        expanded: Whether to show expanded by default
    """
    if not errors:
        return

    with st.expander(f"{title} ({len(errors)})", expanded=expanded):
        for error in errors:
            st.error(f"- {error}")


def categorize_errors(errors: List[str]) -> tuple[List[str], List[str]]:
    """
    Categorize errors into critical and non-critical.

    Args:
        errors: List of error messages

    Returns:
        Tuple of (critical_errors, non_critical_errors)
    """
    critical = []
    non_critical = []

    non_critical_terms = ["sample output", "evaluation", "evaluator", "optional"]

    for error in errors:
        error_lower = str(error).lower()
        if any(term in error_lower for term in non_critical_terms):
            non_critical.append(error)
        else:
            critical.append(error)

    return critical, non_critical


# =============================================================================
# Metric Display Components
# =============================================================================

def show_metric_card(
    label: str,
    value: Any,
    delta: Optional[str] = None,
    delta_color: str = "normal"
) -> None:
    """
    Display a styled metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change indicator
        delta_color: Color for delta (normal, inverse, off)
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


def show_quality_score(score: Optional[int]) -> None:
    """
    Display a quality score with appropriate styling.

    Args:
        score: Quality score (0-100)
    """
    if score is None:
        st.info("Quality score not available")
        return

    # Determine color based on score
    if score >= 80:
        color = "green"
        label = "Excellent"
    elif score >= 60:
        color = "orange"
        label = "Good"
    else:
        color = "red"
        label = "Needs Improvement"

    st.metric("Quality Score", f"{score}/100")


# =============================================================================
# Progress Indicators
# =============================================================================

class ProgressTracker:
    """Helper class for tracking multi-step progress."""

    def __init__(self, total_steps: int, step_names: Optional[List[str]] = None):
        """
        Initialize progress tracker.

        Args:
            total_steps: Total number of steps
            step_names: Optional list of step names
        """
        self.total_steps = total_steps
        self.step_names = step_names or [f"Step {i+1}" for i in range(total_steps)]
        self.current_step = 0
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()

    def update(self, step: int, message: Optional[str] = None) -> None:
        """
        Update progress to a specific step.

        Args:
            step: Current step number (0-indexed)
            message: Optional status message
        """
        self.current_step = step
        progress = (step + 1) / self.total_steps
        self.progress_bar.progress(progress)

        if message:
            self.status_text.info(message)
        elif step < len(self.step_names):
            self.status_text.info(f"Step {step + 1}/{self.total_steps}: {self.step_names[step]}")

    def complete(self, message: str = "Complete!") -> None:
        """Mark progress as complete."""
        self.progress_bar.progress(1.0)
        self.status_text.success(message)

    def clear(self) -> None:
        """Clear progress indicators."""
        self.progress_bar.empty()
        self.status_text.empty()


# =============================================================================
# Layout Helpers
# =============================================================================

def create_tabs(tab_config: dict) -> None:
    """
    Create tabs from a configuration dictionary.

    Args:
        tab_config: Dict mapping tab names to content functions
    """
    tabs = st.tabs(list(tab_config.keys()))

    for tab, (name, content_func) in zip(tabs, tab_config.items()):
        with tab:
            content_func()


def show_code_block(code: str, language: str = "text") -> None:
    """
    Display code in a styled code block.

    Args:
        code: Code to display
        language: Language for syntax highlighting
    """
    if code:
        st.code(code, language=language)
    else:
        st.info("No content available")


def copy_button(text: str, label: str = "Copy to Clipboard") -> None:
    """
    Display a copy-to-clipboard button.

    Note: Due to Streamlit limitations, this shows the text
    and instructs users to copy manually.

    Args:
        text: Text to copy
        label: Button label
    """
    if st.button(label, use_container_width=True):
        st.code(text, language="text")
        st.success("Copied! (Use Cmd/Ctrl+C)")


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state() -> None:
    """
    Initialize session state with default values.

    This is the main initialization function called from main.py.
    """
    from ui.session import init_session_state as _init
    _init()
