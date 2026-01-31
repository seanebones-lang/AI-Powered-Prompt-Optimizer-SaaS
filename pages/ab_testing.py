"""
A/B testing page for comparing prompt variants.
"""

import streamlit as st
import logging

from ab_testing import ABTesting
from ui.session import SessionKeys, get_session_value

logger = logging.getLogger(__name__)


def show_ab_testing_page() -> None:
    """Display the A/B testing page."""
    st.markdown('<h2>A/B Testing</h2>', unsafe_allow_html=True)

    ab_tester = ABTesting()
    user_id = get_session_value(SessionKeys.USER_ID, 1)

    # Create new test section
    with st.expander("Create New A/B Test", expanded=False):
        test_name = st.text_input("Test Name", key="ab_test_name")
        original_prompt = st.text_area("Original Prompt", key="ab_original")
        variant_a = st.text_area("Variant A", key="ab_variant_a")
        variant_b = st.text_area("Variant B", key="ab_variant_b")

        if st.button("Create Test", key="create_ab_test"):
            if all([test_name, original_prompt, variant_a, variant_b]):
                try:
                    test_id = ab_tester.create_test(
                        user_id=user_id,
                        test_name=test_name,
                        original_prompt=original_prompt,
                        variant_a=variant_a,
                        variant_b=variant_b
                    )
                    st.success(f"Test created! ID: {test_id}")
                except Exception as e:
                    logger.error(f"Failed to create A/B test: {e}")
                    st.error(f"Failed to create test: {str(e)}")
            else:
                st.error("Please fill all fields")

    # Existing tests section
    st.markdown("---")
    st.markdown("### Your A/B Tests")

    try:
        tests = ab_tester.get_user_tests(user_id)

        if tests:
            for test in tests:
                with st.expander(f"{test['name']} - {test['status']}"):
                    st.write(f"**Created:** {test['created_at']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Variant A Score", test['variant_a_score'] or "N/A")
                    with col2:
                        st.metric("Variant B Score", test['variant_b_score'] or "N/A")

                    if test.get('winner'):
                        st.success(f"Winner: {test['winner']}")
        else:
            st.info("No A/B tests created yet. Create one above to get started.")

    except Exception as e:
        logger.error(f"Failed to load A/B tests: {e}")
        st.error("Failed to load A/B tests")
