"""
Optimization page for the Prompt Optimizer.

This is the main page where users enter prompts and receive
optimized versions using the 4-D methodology.
"""

import streamlit as st
import logging
import time
from typing import Optional, Dict, Any

from agents import PromptType
from agent_config import AgentConfigManager
from input_validation import sanitize_and_validate_prompt, validate_prompt_type
from voice_prompting import VoicePrompting
from cost_tracker import get_cost_optimizer
from ui.session import SessionKeys, get_session_value, set_session_value
from ui.components import (
    ProgressTracker,
    show_quality_score,
    categorize_errors,
    show_errors_expandable,
)

logger = logging.getLogger(__name__)


def _show_agent_config_panel() -> Dict[str, Any]:
    """
    Display the agent configuration panel.

    Returns:
        Updated agent configuration dictionary
    """
    config = get_session_value(SessionKeys.AGENT_CONFIG) or AgentConfigManager.DEFAULT_CONFIG.copy()

    with st.expander("Agent Configuration", expanded=get_session_value(SessionKeys.SHOW_AGENT_TUNING, False)):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Global Settings**")
            global_temp = st.slider(
                "Temperature",
                0.0, 2.0,
                config.get("temperature", 0.7),
                0.1
            )
            max_tokens = st.slider(
                "Max Tokens",
                1000, 4000,
                config.get("max_tokens", 2000),
                500
            )

        with col2:
            st.markdown("**Per-Agent Override**")
            deconstruct_temp = st.slider("Deconstructor", 0.0, 1.0, 0.5, 0.1)
            diagnose_temp = st.slider("Diagnoser", 0.0, 1.0, 0.4, 0.1)
            design_temp = st.slider("Designer", 0.0, 1.5, 0.8, 0.1)
            eval_temp = st.slider("Evaluator", 0.0, 1.0, 0.3, 0.1)

        config.update({
            "temperature": global_temp,
            "max_tokens": max_tokens,
            "deconstructor": {"temperature": deconstruct_temp, "max_tokens": 1500},
            "diagnoser": {"temperature": diagnose_temp, "max_tokens": 1500},
            "designer": {"temperature": design_temp, "max_tokens": 2000},
            "evaluator": {"temperature": eval_temp, "max_tokens": 1000}
        })

        set_session_value(SessionKeys.AGENT_CONFIG, config)

    return config


def _show_voice_input() -> Optional[str]:
    """
    Display voice input option if user is premium.

    Returns:
        Transcribed text if successful, None otherwise
    """
    if not get_session_value(SessionKeys.IS_PREMIUM, False):
        return None

    use_voice = st.checkbox("Use Voice Input")
    if not use_voice:
        return None

    audio_file = st.file_uploader(
        "Upload audio",
        type=['wav', 'mp3', 'm4a', 'ogg']
    )

    if audio_file:
        with st.spinner("Transcribing audio..."):
            try:
                voice_prompt = VoicePrompting()
                transcribed = voice_prompt.transcribe_audio(audio_file.read())
                st.success("Audio transcribed!")
                return transcribed
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                st.error(f"Transcription failed: {str(e)}")

    return None


def _run_optimization(
    prompt: str,
    prompt_type: str,
    thinking_mode: str,
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Run the prompt optimization workflow.

    Args:
        prompt: User's input prompt
        prompt_type: Selected prompt type
        thinking_mode: Selected thinking mode
        config: Agent configuration

    Returns:
        Optimization result dictionary or None on error
    """
    # Validate prompt
    is_valid, sanitized, error = sanitize_and_validate_prompt(prompt)
    if not is_valid:
        st.error(f"Invalid prompt: {error}")
        return None

    # Validate prompt type
    is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
    if not is_valid_type:
        st.error(f"Invalid type: {type_error}")
        return None

    # Create progress tracker
    progress = ProgressTracker(
        total_steps=4,
        step_names=[
            "Deconstructing prompt",
            "Diagnosing issues",
            "Designing optimized version",
            "Evaluating quality"
        ]
    )

    try:
        # Create orchestrator with config
        orchestrator = AgentConfigManager.apply_config_to_agent(None, config)

        # Run optimization with progress updates
        progress.update(0, "Deconstructing prompt...")

        result = orchestrator.optimize_prompt(
            sanitized,
            prompt_type_enum,
            methodology=thinking_mode
        )

        progress.update(1, "Diagnosing issues...")
        time.sleep(0.3)  # Brief UX pause

        progress.update(2, "Designing optimized version...")
        time.sleep(0.3)

        progress.update(3, "Evaluating quality...")
        time.sleep(0.3)

        progress.complete("Optimization complete!")

        return result

    except Exception as e:
        logger.error(f"Optimization error: {e}")
        progress.clear()
        st.error(f"Error: {str(e)}")
        return None


def _show_optimization_results(result: Dict[str, Any]) -> None:
    """
    Display the optimization results.

    Args:
        result: Optimization result dictionary
    """
    # Extract optimized prompt
    optimized = result.get("optimized_prompt", "")
    design_output = result.get("design_output", "")

    # Fallback logic if optimized is empty
    if not optimized or not optimized.strip():
        if design_output and design_output.strip():
            optimized = design_output
        elif result.get("deconstruction"):
            optimized = result.get("deconstruction", "")
        else:
            optimized = "No optimized prompt available."

    # Show errors if any (categorized)
    errors = result.get("errors", [])
    critical_errors, non_critical_errors = categorize_errors(errors)

    if critical_errors:
        show_errors_expandable(
            critical_errors,
            title=f"{len(critical_errors)} error(s) during optimization",
            expanded=False
        )

    # Show quality score
    score = result.get("quality_score")
    if score:
        show_quality_score(score)

    # Create tabs for different result views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Optimized Prompt",
        "Analysis",
        "Sample Output",
        "Details"
    ])

    with tab1:
        st.markdown("### Your Optimized Prompt")

        if optimized and optimized.strip():
            st.code(optimized, language="text")

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Copy to Clipboard", use_container_width=True):
                    st.code(optimized, language="text")
                    st.success("Copied! (Use Cmd/Ctrl+C)")
            with col2:
                if st.button("Save to History", use_container_width=True):
                    history = get_session_value(SessionKeys.HISTORY) or []
                    history.append(result)
                    set_session_value(SessionKeys.HISTORY, history)
                    st.success("Saved!")
        else:
            st.info("No optimized prompt available.")

        # Show full design output if different
        if design_output and design_output != optimized and len(design_output) > len(optimized):
            with st.expander("View Full Design Output"):
                st.text(design_output)

    with tab2:
        st.markdown("### Analysis")

        if result.get("deconstruction"):
            with st.expander("Deconstruction", expanded=True):
                st.write(result.get("deconstruction", ""))

        if result.get("diagnosis"):
            with st.expander("Diagnosis", expanded=False):
                st.write(result.get("diagnosis", ""))

        if result.get("evaluation"):
            with st.expander("Evaluation", expanded=False):
                st.write(result.get("evaluation", ""))

        if not any([result.get("deconstruction"), result.get("diagnosis"), result.get("evaluation")]):
            st.info("Analysis data will appear here after optimization.")

    with tab3:
        st.markdown("### Sample Output")
        sample = result.get("sample_output", "")

        if sample and sample.strip() and "failed" not in sample.lower():
            st.write(sample)
        else:
            st.info("Sample output will appear here after optimization.")

    with tab4:
        st.markdown("### Technical Details")
        st.json({
            "prompt_type": result.get("prompt_type"),
            "workflow_mode": result.get("workflow_mode"),
            "quality_score": result.get("quality_score"),
            "has_errors": len(errors) > 0,
            "error_count": len(errors)
        })

        if errors:
            st.markdown("#### Errors/Warnings")
            for error in errors:
                st.warning(f"- {error}")


def show_optimize_page() -> None:
    """Display the main optimization page."""
    st.markdown('<h2>Optimize Your Prompt</h2>', unsafe_allow_html=True)

    # Agent configuration panel
    config = _show_agent_config_panel()

    # Voice input (if premium)
    voice_text = _show_voice_input()
    if voice_text:
        set_session_value(SessionKeys.CURRENT_PROMPT, voice_text)

    # Prompt input
    current_prompt = get_session_value(SessionKeys.CURRENT_PROMPT, "")
    prompt_input = st.text_area(
        "Prompt to optimize:",
        value=current_prompt,
        height=150,
        placeholder="Enter your prompt here..."
    )
    set_session_value(SessionKeys.CURRENT_PROMPT, prompt_input)

    # Options row
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        prompt_type = st.selectbox(
            "Prompt Type",
            [pt.value for pt in PromptType]
        )

    with col_b:
        thinking_mode = st.selectbox(
            "Thinking Mode",
            ["4d", "chain_of_thought", "tree_of_thought"]
        )

    with col_c:
        optimize_clicked = st.button(
            "Optimize",
            type="primary",
            use_container_width=True
        )

    # Handle optimization
    if optimize_clicked:
        if not prompt_input.strip():
            st.error("Please enter a prompt")
        else:
            with st.spinner("Optimizing..."):
                result = _run_optimization(
                    prompt_input,
                    prompt_type,
                    thinking_mode,
                    config
                )

                if result:
                    set_session_value(SessionKeys.OPTIMIZATION_RESULT, result)

                    # Add to history
                    history = get_session_value(SessionKeys.HISTORY) or []
                    history.append(result)
                    set_session_value(SessionKeys.HISTORY, history)

                    st.success("Optimization complete!")

                    # Show cost info
                    cost_optimizer = get_cost_optimizer()
                    if cost_optimizer.records:
                        recent_cost = cost_optimizer.records[-1]
                        st.info(
                            f"Cost: ${recent_cost.cost_usd:.4f} | "
                            f"Tokens: {recent_cost.total_tokens:,}"
                        )

    # Results section
    st.markdown("---")
    st.subheader("Results")

    result = get_session_value(SessionKeys.OPTIMIZATION_RESULT)
    if result:
        _show_optimization_results(result)
    else:
        st.info("Enter a prompt above and click 'Optimize' to see results here.")
