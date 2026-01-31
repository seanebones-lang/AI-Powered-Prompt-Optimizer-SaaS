"""
Analytics dashboard page for viewing optimization statistics.
"""

import streamlit as st
import logging

from analytics import Analytics
from ui.session import SessionKeys, get_session_value, set_session_value

logger = logging.getLogger(__name__)


def show_analytics_page() -> None:
    """Display the analytics dashboard page."""
    st.markdown('<h2>Analytics Dashboard</h2>', unsafe_allow_html=True)

    # Initialize analytics
    analytics = get_session_value(SessionKeys.ANALYTICS)
    if analytics is None:
        analytics = Analytics()
        set_session_value(SessionKeys.ANALYTICS, analytics)

    user_id = get_session_value(SessionKeys.USER_ID, 1)

    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        ["7 days", "30 days", "90 days", "All time"]
    )

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Optimizations",
            analytics.get_total_optimizations(user_id)
        )

    with col2:
        avg_score = analytics.get_average_quality_score(user_id)
        st.metric("Avg Quality Score", f"{avg_score:.1f}")

    with col3:
        st.metric(
            "Tokens Used",
            analytics.get_total_tokens(user_id)
        )

    with col4:
        avg_time = analytics.get_avg_processing_time(user_id)
        st.metric("Avg Processing Time", f"{avg_time:.2f}s")

    # Charts section
    st.markdown("---")

    st.markdown("### Quality Score Trends")
    trends = analytics.get_quality_trends(user_id)
    if trends:
        st.line_chart(trends)
    else:
        st.info("No trend data available yet. Run some optimizations to see trends.")

    st.markdown("### Prompt Type Distribution")
    distribution = analytics.get_prompt_type_distribution(user_id)
    if distribution:
        st.bar_chart(distribution)
    else:
        st.info("No distribution data available yet.")
