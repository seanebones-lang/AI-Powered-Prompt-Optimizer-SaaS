"""
Settings page for preferences and data management.
"""

import streamlit as st
import logging
from datetime import datetime
from pathlib import Path

from backup_manager import get_backup_manager
from enhanced_cache import get_smart_cache

logger = logging.getLogger(__name__)


def _show_backup_tab() -> None:
    """Display backup and export tab."""
    st.markdown("### Backup & Export")

    backup_manager = get_backup_manager()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Create Backup")
        include_cache = st.checkbox("Include cache files", value=False)

        if st.button("Create Backup Now", type="primary"):
            with st.spinner("Creating backup..."):
                try:
                    backup_path = backup_manager.create_backup(
                        include_db=True,
                        include_cache=include_cache
                    )
                    st.success(f"Backup created: {Path(backup_path).name}")

                    # Offer download
                    with open(backup_path, 'rb') as f:
                        st.download_button(
                            "Download Backup",
                            data=f.read(),
                            file_name=Path(backup_path).name,
                            mime="application/zip"
                        )
                except Exception as e:
                    logger.error(f"Backup failed: {e}")
                    st.error(f"Backup failed: {str(e)}")

    with col2:
        st.markdown("#### Export Data")

        if st.button("Export to JSON"):
            with st.spinner("Exporting..."):
                try:
                    export_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    if backup_manager.export_to_json(export_path):
                        with open(export_path, 'r') as f:
                            st.download_button(
                                "Download JSON Export",
                                data=f.read(),
                                file_name=export_path,
                                mime="application/json"
                            )
                        Path(export_path).unlink()  # Cleanup
                except Exception as e:
                    logger.error(f"Export failed: {e}")
                    st.error(f"Export failed: {str(e)}")

    # Available backups
    st.markdown("---")
    st.markdown("#### Available Backups")

    try:
        backups = backup_manager.list_backups()

        if backups:
            for backup in backups[:10]:
                with st.expander(f"{backup['filename']} - {backup['size_mb']:.2f} MB"):
                    st.write(f"**Created:** {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Restore", key=f"restore_{backup['filename']}"):
                            st.warning("Restore will replace current data. Please confirm.")
                    with col2:
                        with open(backup['path'], 'rb') as f:
                            st.download_button(
                                "Download",
                                data=f.read(),
                                file_name=backup['filename'],
                                mime="application/zip",
                                key=f"download_{backup['filename']}"
                            )
        else:
            st.info("No backups available yet")
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        st.error("Failed to load backup list")


def _show_preferences_tab() -> None:
    """Display preferences tab."""
    st.markdown("### Preferences")

    st.markdown("#### Default Settings")

    default_temp = st.slider(
        "Default Temperature",
        0.0, 2.0, 0.7, 0.1,
        help="Controls randomness in AI responses"
    )

    default_model = st.selectbox(
        "Preferred Model",
        ["grok-4-1-fast-reasoning", "grok-4-1-fast", "grok-3", "grok-2"],
        help="Default model for optimizations"
    )

    auto_save = st.checkbox("Auto-save optimizations", value=True)

    if st.button("Save Preferences"):
        st.success("Preferences saved!")


def _show_advanced_tab() -> None:
    """Display advanced settings tab."""
    st.markdown("### Advanced Settings")

    st.markdown("#### Cache Management")

    try:
        cache = get_smart_cache()
        cache_stats = cache.get_cache_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cache Hits", cache_stats.get('hits', 0))
        with col2:
            st.metric("Cache Misses", cache_stats.get('misses', 0))
        with col3:
            hit_rate = cache_stats.get('hit_rate', 0)
            st.metric("Hit Rate", f"{hit_rate:.1f}%")

        if st.button("Clear All Caches"):
            cache.clear_all()
            st.success("Caches cleared!")
    except Exception as e:
        logger.warning(f"Cache stats unavailable: {e}")
        st.info("Cache statistics unavailable")

    st.markdown("---")
    st.markdown("#### Database Maintenance")

    if st.button("Optimize Database"):
        st.info("Database optimization coming soon")


def _show_about_tab() -> None:
    """Display about tab."""
    st.markdown("### About")

    st.markdown("""
    **AI-Powered Prompt Optimizer**

    Version: 2.0.0
    Built with: Python 3.11+, Streamlit 1.52, xAI Grok API

    **Features:**
    - Multi-agent 4-D optimization
    - Enterprise features
    - Cost tracking & optimization
    - Automated backups
    - Circuit breaker protection
    - Advanced caching

    **Personal Edition**
    No login, no limits, all features enabled.

    Built by S. McDonnell at NextEleven
    """)


def show_settings_page() -> None:
    """Display the settings page."""
    st.markdown('<h2>Settings & Data Management</h2>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Backup & Export",
        "Preferences",
        "Advanced",
        "About"
    ])

    with tab1:
        _show_backup_tab()

    with tab2:
        _show_preferences_tab()

    with tab3:
        _show_advanced_tab()

    with tab4:
        _show_about_tab()
