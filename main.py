"""
NextEleven AI Prompt Optimizer - Streamlit Entry Point

This is the main entry point for the Streamlit application.
Business logic has been modularized into the pages/ package.

Architecture:
- main.py: App configuration and navigation only
- pages/: Individual page modules
- ui/: Shared UI components and session management
"""

import streamlit as st
import logging

# Configuration and UI
from ui.components import apply_custom_css, init_session_state, show_config_warnings
from ui.session import SessionKeys, get_session_value, set_session_value

# Page registry
from pages import PAGE_REGISTRY, PAGE_LABELS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="NextEleven AI - Prompt Optimizer",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def show_sidebar() -> str:
    """
    Display the sidebar navigation.

    Returns:
        Selected page name
    """
    with st.sidebar:
        st.markdown("### NextEleven AI")
        st.markdown("**All Features Unlocked**")
        st.markdown("---")

        # Navigation buttons
        for key, label in PAGE_LABELS.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                set_session_value(SessionKeys.PAGE, key)
                st.rerun()

        st.markdown("---")
        st.caption("No login - All features enabled")

    return get_session_value(SessionKeys.PAGE, "optimize")


def main() -> None:
    """Main application entry point."""
    # Configure page
    configure_page()

    # Apply custom styling
    apply_custom_css()

    # Initialize session state
    init_session_state()

    # Show configuration warnings if any
    show_config_warnings()

    # Show sidebar and get current page
    current_page = show_sidebar()

    # Get and execute page function
    page_func = PAGE_REGISTRY.get(current_page)

    if page_func:
        try:
            page_func()
        except Exception as e:
            logger.error(f"Page error on {current_page}: {e}", exc_info=True)
            st.error(f"An error occurred: {str(e)}")
            st.info("Please try refreshing the page or contact support.")
    else:
        logger.warning(f"Unknown page requested: {current_page}")
        st.error(f"Page not found: {current_page}")
        set_session_value(SessionKeys.PAGE, "optimize")
        st.rerun()


if __name__ == "__main__":
    main()
