"""
Batch optimization page for processing multiple prompts.
"""

import streamlit as st
import logging
import json
import re
from datetime import datetime
from typing import List, Dict, Any

from agents import PromptType
from agent_config import AgentConfigManager
from input_validation import sanitize_and_validate_prompt, validate_prompt_type
from ui.session import SessionKeys, get_session_value

logger = logging.getLogger(__name__)


def _parse_prompts_from_text(text: str) -> List[str]:
    """
    Parse prompts from text input.

    Handles numbered lists and plain lines.

    Args:
        text: Raw input text

    Returns:
        List of cleaned prompts
    """
    lines = text.strip().split('\n')
    prompts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove numbering (1., 2., etc.)
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
        if cleaned:
            prompts.append(cleaned)

    return prompts


def _process_batch(
    prompts: List[str],
    prompt_type: str,
    methodology: str,
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Process a batch of prompts.

    Args:
        prompts: List of prompts to process
        prompt_type: Prompt type for all prompts
        methodology: Optimization methodology
        config: Agent configuration

    Returns:
        List of results
    """
    results = []
    orchestrator = AgentConfigManager.apply_config_to_agent(None, config)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, prompt in enumerate(prompts):
        status_text.text(f"Processing prompt {idx + 1}/{len(prompts)}: {prompt[:50]}...")

        try:
            is_valid, sanitized, error = sanitize_and_validate_prompt(prompt)
            if not is_valid:
                results.append({
                    "prompt": prompt,
                    "status": "error",
                    "error": error
                })
                continue

            is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
            if not is_valid_type:
                results.append({
                    "prompt": prompt,
                    "status": "error",
                    "error": type_error
                })
                continue

            result = orchestrator.optimize_prompt(
                sanitized,
                prompt_type_enum,
                methodology=methodology
            )
            result["status"] = "success"
            result["original_prompt"] = prompt
            results.append(result)

        except Exception as e:
            logger.error(f"Batch processing error for prompt {idx + 1}: {e}")
            results.append({
                "prompt": prompt,
                "status": "error",
                "error": str(e)
            })

        progress_bar.progress((idx + 1) / len(prompts))

    status_text.text("Batch processing complete!")

    return results


def _show_batch_results(results: List[Dict[str, Any]]) -> None:
    """Display batch processing results."""
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "error"]

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", len(results))
    with col2:
        st.metric("Successful", len(successful))
    with col3:
        st.metric("Failed", len(failed))

    # Export button
    if successful:
        export_data = json.dumps(results, indent=2)
        st.download_button(
            "Download All Results (JSON)",
            data=export_data,
            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    # Individual results
    for idx, result in enumerate(results):
        prompt_preview = result.get('original_prompt', result.get('prompt', ''))[:60]
        with st.expander(f"Prompt {idx + 1}: {prompt_preview}..."):
            if result.get("status") == "success":
                st.markdown("**Optimized Prompt:**")
                st.code(result.get("optimized_prompt", ""), language="text")
                st.markdown(f"**Quality Score:** {result.get('quality_score', 'N/A')}/100")
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")


def _show_manual_entry_tab() -> None:
    """Show the manual entry tab content."""
    config = get_session_value(SessionKeys.AGENT_CONFIG) or {}

    batch_input = st.text_area(
        "Enter multiple prompts (one per line or numbered):",
        height=200,
        placeholder="1. Build a code review agent\n2. Create API docs\n3. Design workflow"
    )

    col1, col2 = st.columns(2)
    with col1:
        batch_prompt_type = st.selectbox(
            "Prompt Type for All",
            [pt.value for pt in PromptType],
            key="batch_prompt_type"
        )
    with col2:
        batch_methodology = st.selectbox(
            "Methodology",
            ["4d", "chain_of_thought", "tree_of_thought"],
            key="batch_methodology"
        )

    if st.button("Process Batch", type="primary"):
        if not batch_input:
            st.error("Please enter prompts")
            return

        prompts = _parse_prompts_from_text(batch_input)
        if not prompts:
            st.error("No valid prompts found")
            return

        st.info(f"Processing {len(prompts)} prompts...")

        results = _process_batch(
            prompts,
            batch_prompt_type,
            batch_methodology,
            config
        )

        st.markdown("### Results")
        _show_batch_results(results)


def _show_json_upload_tab() -> None:
    """Show the JSON upload tab content."""
    st.markdown("### Upload JSON File")
    st.markdown("Expected format: `{\"prompts\": [\"prompt1\", \"prompt2\", ...]}`")

    json_file = st.file_uploader("Upload JSON file", type=['json'], key="json_upload")

    if json_file:
        try:
            data = json.load(json_file)
            prompts = data.get("prompts", [])

            if prompts:
                st.success(f"Loaded {len(prompts)} prompts from JSON")
                st.text_area(
                    "Preview:",
                    value='\n'.join(prompts[:5]),
                    height=150,
                    disabled=True
                )

                if len(prompts) > 5:
                    st.info(f"... and {len(prompts) - 5} more")

                if st.button("Process JSON Batch", key="process_json"):
                    st.session_state['batch_input_from_json'] = '\n'.join(prompts)
                    st.rerun()
            else:
                st.warning("No prompts found in JSON file")

        except Exception as e:
            st.error(f"Error reading JSON: {str(e)}")


def _show_csv_upload_tab() -> None:
    """Show the CSV upload tab content."""
    st.markdown("### Upload CSV File")
    st.markdown("Expected format: CSV with a 'prompt' column")

    csv_file = st.file_uploader("Upload CSV file", type=['csv'], key="csv_upload")

    if csv_file:
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)

            if 'prompt' in df.columns:
                prompts = df['prompt'].dropna().tolist()
                st.success(f"Loaded {len(prompts)} prompts from CSV")
                st.dataframe(df.head(), use_container_width=True)

                if st.button("Process CSV Batch", key="process_csv"):
                    st.session_state['batch_input_from_csv'] = '\n'.join(prompts)
                    st.rerun()
            else:
                st.error("CSV must have a 'prompt' column")

        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")


def show_batch_page() -> None:
    """Display the batch optimization page."""
    st.markdown('<h2>Batch Optimization</h2>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Manual Entry", "JSON Upload", "CSV Upload"])

    with tab1:
        _show_manual_entry_tab()

    with tab2:
        _show_json_upload_tab()

    with tab3:
        _show_csv_upload_tab()
