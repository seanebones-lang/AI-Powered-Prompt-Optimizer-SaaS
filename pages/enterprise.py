"""
Enterprise features page with advanced capabilities.
"""

import streamlit as st
import logging

from enterprise_integration import (
    create_blueprint,
    refine_prompt,
    generate_tests,
    check_security,
)

logger = logging.getLogger(__name__)


def _show_blueprints_tab() -> None:
    """Display the agent blueprint generator tab."""
    st.markdown("### Agent Blueprint Generator")

    description = st.text_area(
        "Agent Description",
        placeholder="Describe the agent you want to build...",
        key="blueprint_description"
    )
    agent_type = st.selectbox(
        "Agent Type",
        ["conversational", "task_executor", "analyst", "orchestrator"],
        key="blueprint_type"
    )

    if st.button("Generate Blueprint", key="gen_blueprint"):
        if description:
            with st.spinner("Generating blueprint..."):
                try:
                    blueprint = create_blueprint(description, agent_type)
                    st.json(blueprint)
                except Exception as e:
                    logger.error(f"Blueprint generation failed: {e}")
                    st.error(f"Failed to generate blueprint: {str(e)}")
        else:
            st.error("Please enter a description")


def _show_refinement_tab() -> None:
    """Display the iterative refinement tab."""
    st.markdown("### Iterative Refinement")

    prompt_to_refine = st.text_area(
        "Prompt to Refine",
        placeholder="Enter the prompt you want to refine...",
        key="refine_prompt"
    )
    feedback = st.text_area(
        "Feedback",
        placeholder="What would you like to improve?",
        key="refine_feedback"
    )

    if st.button("Refine Prompt", key="do_refine"):
        if prompt_to_refine and feedback:
            with st.spinner("Refining prompt..."):
                try:
                    refined = refine_prompt(prompt_to_refine, feedback)
                    st.code(refined, language="text")
                except Exception as e:
                    logger.error(f"Refinement failed: {e}")
                    st.error(f"Refinement failed: {str(e)}")
        else:
            st.error("Please provide prompt and feedback")


def _show_testing_tab() -> None:
    """Display the test case generator tab."""
    st.markdown("### Test Case Generator")

    prompt_for_tests = st.text_area(
        "Prompt to Generate Tests For",
        placeholder="Enter the prompt you want to test...",
        key="test_prompt"
    )

    if st.button("Generate Tests", key="gen_tests"):
        if prompt_for_tests:
            with st.spinner("Generating test cases..."):
                try:
                    tests = generate_tests(prompt_for_tests)
                    st.json(tests)
                except Exception as e:
                    logger.error(f"Test generation failed: {e}")
                    st.error(f"Test generation failed: {str(e)}")
        else:
            st.error("Please enter a prompt")


def _show_security_tab() -> None:
    """Display the security scanner tab."""
    st.markdown("### Security Scanner")

    prompt_to_scan = st.text_area(
        "Prompt to Scan",
        placeholder="Enter the prompt to scan for security issues...",
        key="security_prompt"
    )

    if st.button("Scan for Security Issues", key="do_scan"):
        if prompt_to_scan:
            with st.spinner("Scanning for security issues..."):
                try:
                    security_report = check_security(prompt_to_scan)

                    if security_report.get('is_safe', True):
                        st.success("No security issues found")
                    else:
                        st.warning("Security issues detected:")
                        for issue in security_report.get('issues', []):
                            st.error(f"- {issue}")
                except Exception as e:
                    logger.error(f"Security scan failed: {e}")
                    st.error(f"Security scan failed: {str(e)}")
        else:
            st.error("Please enter a prompt")


def show_enterprise_page() -> None:
    """Display the enterprise features page."""
    st.markdown('<h2>Enterprise Features</h2>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Blueprints",
        "Refinement",
        "Testing",
        "Security"
    ])

    with tab1:
        _show_blueprints_tab()

    with tab2:
        _show_refinement_tab()

    with tab3:
        _show_testing_tab()

    with tab4:
        _show_security_tab()
