"""
Session history page for viewing past optimizations.
"""

import streamlit as st
import logging

from database import db
from ui.session import SessionKeys, get_session_value, set_session_value

logger = logging.getLogger(__name__)


def show_history_page() -> None:
    """Display the session history page."""
    st.markdown('<h2>Session History</h2>', unsafe_allow_html=True)

    user_id = get_session_value(SessionKeys.USER_ID, 1)

    try:
        sessions = db.get_user_sessions(user_id, limit=50)

        if sessions:
            for session in sessions:
                # Handle both dict and ORM object
                if hasattr(session, '__dict__'):
                    session_data = {
                        'id': session.id,
                        'created_at': session.created_at,
                        'quality_score': session.quality_score,
                        'original_prompt': session.original_prompt,
                        'optimized_prompt': session.optimized_prompt,
                    }
                else:
                    session_data = session

                with st.expander(
                    f"{session_data.get('created_at', 'Unknown')} - "
                    f"Score: {session_data.get('quality_score', 'N/A')}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Original:**")
                        original = session_data.get('original_prompt', '')
                        st.text(original[:200] if original else "N/A")

                    with col2:
                        st.markdown("**Optimized:**")
                        optimized = session_data.get('optimized_prompt', '')
                        st.text(optimized[:200] if optimized else "N/A")

                    session_id = session_data.get('id')
                    if st.button(
                        f"Load Session {session_id}",
                        key=f"load_{session_id}"
                    ):
                        set_session_value(SessionKeys.OPTIMIZATION_RESULT, session_data)
                        set_session_value(SessionKeys.PAGE, 'optimize')
                        st.rerun()
        else:
            st.info("No optimization history yet. Start optimizing!")

    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        st.error("Failed to load session history")

        # Show in-memory history as fallback
        history = get_session_value(SessionKeys.HISTORY) or []
        if history:
            st.markdown("### Recent Session History")
            for idx, result in enumerate(reversed(history[-10:])):
                with st.expander(f"Session {len(history) - idx}"):
                    st.write(f"**Quality Score:** {result.get('quality_score', 'N/A')}")
                    st.code(result.get('optimized_prompt', '')[:500], language="text")
