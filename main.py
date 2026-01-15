"""
NextEleven AI Prompt Optimizer - Streamlit UI
Personal powerhouse for building agentic AI systems and crafting build plans.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Import our modules
from agents import OrchestratorAgent, PromptType
from agent_config import AgentConfigManager
from database import db
from input_validation import sanitize_and_validate_prompt, validate_prompt_type
from export_utils import export_results
from batch_optimization import BatchOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="NextEleven AI - Prompt Optimizer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00BFA5;
        margin-bottom: 2rem;
    }
    .agent-tuning-panel {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .agent-tuning-header {
        color: #00BFA5;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = ""
if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None
if 'agent_config' not in st.session_state:
    st.session_state.agent_config = AgentConfigManager.DEFAULT_CONFIG.copy()
if 'show_agent_tuning' not in st.session_state:
    st.session_state.show_agent_tuning = False

def parse_batch_prompts(text: str) -> list:
    """Parse input text into multiple prompts based on numbered list or delimiters."""
    import re
    # Check for numbered list (e.g., 1., 2., etc.)
    pattern = r'\d+\s*\.?\s*'
    prompts = re.split(pattern, text)
    prompts = [p.strip() for p in prompts if p.strip()]
    if len(prompts) > 1:
        return prompts
    # If not a numbered list, check for other delimiters like '---' or multiple newlines
    if '---' in text:
        prompts = text.split('---')
        prompts = [p.strip() for p in prompts if p.strip()]
        if len(prompts) > 1:
            return prompts
    if '\n\n' in text:
        prompts = text.split('\n\n')
        prompts = [p.strip() for p in prompts if p.strip()]
        if len(prompts) > 1:
            return prompts
    # Default to single prompt if no batch detected
    return [text.strip()]

def create_agent_tuning_panel():
    """Create the collapsible agent configuration panel."""
    with st.expander("🎛️ Agent Configuration", expanded=st.session_state.show_agent_tuning):

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Global Settings**")
            global_temp = st.slider(
                "Global Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.agent_config.get("temperature", 0.7),
                step=0.1,
                key="global_temp"
            )

            max_tokens = st.slider(
                "Max Tokens",
                min_value=1000,
                max_value=4000,
                value=st.session_state.agent_config.get("max_tokens", 2000),
                step=500,
                key="max_tokens"
            )

        with col2:
            st.markdown("**Per-Agent Temperature Override**")

            # Deconstructor
            deconstruct_temp = st.slider(
                "Deconstructor",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.agent_config.get("deconstructor", {}).get("temperature", 0.5),
                step=0.1,
                key="deconstruct_temp"
            )

            # Diagnoser
            diagnose_temp = st.slider(
                "Diagnoser",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.agent_config.get("diagnoser", {}).get("temperature", 0.4),
                step=0.1,
                key="diagnose_temp"
            )

            # Designer
            design_temp = st.slider(
                "Designer",
                min_value=0.0,
                max_value=1.5,
                value=st.session_state.agent_config.get("designer", {}).get("temperature", 0.8),
                step=0.1,
                key="design_temp"
            )

            # Evaluator
            eval_temp = st.slider(
                "Evaluator",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.agent_config.get("evaluator", {}).get("temperature", 0.3),
                step=0.1,
                key="eval_temp"
            )

        # Update config
        st.session_state.agent_config.update({
            "temperature": global_temp,
            "max_tokens": max_tokens,
            "deconstructor": {"temperature": deconstruct_temp, "max_tokens": 1500},
            "diagnoser": {"temperature": diagnose_temp, "max_tokens": 1500},
            "designer": {"temperature": design_temp, "max_tokens": 2000},
            "evaluator": {"temperature": eval_temp, "max_tokens": 1000}
        })

        if st.button("Reset to Defaults"):
            st.session_state.agent_config = AgentConfigManager.DEFAULT_CONFIG.copy()
            st.rerun()

def main():
    """Main application function."""
    st.markdown('<h1 class="main-header">🚀 NextEleven AI - Prompt Optimizer</h1>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("📚 Prompt Library")
        st.write("Coming soon...")

        st.header("⚙️ Settings")
        if st.checkbox("Show Agent Tuning", value=st.session_state.show_agent_tuning):
            st.session_state.show_agent_tuning = True
        else:
            st.session_state.show_agent_tuning = False

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Agent tuning panel
        create_agent_tuning_panel()

        # Prompt input
        st.subheader("✏️ Enter Your Prompt")
        prompt_input = st.text_area(
            "Prompt to optimize:",
            value=st.session_state.current_prompt,
            height=150,
            placeholder="Enter your prompt here...",
            help="Describe what you want the AI to do. Be specific for better results."
        )

        # Update session state
        st.session_state.current_prompt = prompt_input

        col_a, col_b, col_c = st.columns([1, 1, 1])

        with col_a:
            prompt_type = st.selectbox(
                "Prompt Type",
                options=[pt.value for pt in PromptType],
                index=0,
                help="Select the type of prompt you're creating"
            )

        with col_b:
            thinking_mode = st.selectbox(
                "Thinking Mode",
                options=["4d", "chain_of_thought", "tree_of_thought"],
                index=0,
                help="Choose the reasoning approach"
            )

        with col_c:
            if st.button("🚀 Optimize", type="primary", use_container_width=True):
                if not prompt_input.strip():
                    st.error("Please enter a prompt to optimize.")
                    return

                with st.spinner("Optimizing your prompt..."):
                    try:
                        # Validate input
                        is_valid, sanitized_prompt, error = sanitize_and_validate_prompt(prompt_input)
                        if not is_valid:
                            st.error(f"Invalid prompt: {error}")
                            return

                        is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
                        if not is_valid_type:
                            st.error(f"Invalid prompt type: {type_error}")
                            return

                        # Create orchestrator with config
                        orchestrator = AgentConfigManager.apply_config_to_agent(
                            None, st.session_state.agent_config
                        )

                        # Optimize
                        result = orchestrator.optimize_prompt(
                            sanitized_prompt,
                            prompt_type_enum,
                            methodology=thinking_mode
                        )

                        st.session_state.optimization_result = result
                        st.success("Optimization complete!")

                    except Exception as e:
                        logger.error(f"Optimization error: {str(e)}")
                        st.error(f"Error during optimization: {str(e)}")

    with col2:
        st.subheader("📊 Results")

        if st.session_state.optimization_result:
            result = st.session_state.optimization_result

            # Quality score
            score = result.get("quality_score", 0)
            st.metric("Quality Score", f"{score}/100")

            # Tabs for results
            tab1, tab2, tab3, tab4 = st.tabs(["Optimized", "Analysis", "Sample", "Details"])

            with tab1:
                st.markdown("### Optimized Prompt")
                st.code(result.get("optimized_prompt", ""), language="text")

            with tab2:
                st.markdown("### Deconstruction")
                st.write(result.get("deconstruction", ""))

                st.markdown("### Diagnosis")
                st.write(result.get("diagnosis", ""))

                st.markdown("### Evaluation")
                st.write(result.get("evaluation", ""))

            with tab3:
                st.markdown("### Sample Output")
                st.write(result.get("sample_output", ""))

            with tab4:
                st.markdown("### Technical Details")
                st.json({
                    "tokens_used": result.get("tokens_used"),
                    "processing_time": result.get("processing_time"),
                    "prompt_type": result.get("prompt_type"),
                    "workflow_mode": result.get("workflow_mode")
                })

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save to Library"):
                    st.info("Save functionality coming soon...")

            with col2:
                if st.button("📋 Copy"):
                    st.code(result.get("optimized_prompt", ""), language="text")
                    st.success("Copied to clipboard!")

            with col3:
                if st.button("📤 Export"):
                    export_data = export_results(result, "json")
                    st.download_button(
                        label="Download JSON",
                        data=export_data,
                        file_name=f"optimized_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        else:
            st.info("Enter a prompt and click 'Optimize' to see results here.")

    # Batch processing section
    st.markdown("---")
    st.subheader("📦 Batch Processing")

    with st.expander("Process Multiple Prompts"):
        batch_input = st.text_area(
            "Enter multiple prompts (one per line or numbered list):",
            height=100,
            placeholder="1. Build a code review agent\n2. Create API documentation prompt\n3. Design multi-agent workflow"
        )

        col1, col2 = st.columns(2)
        with col1:
            batch_prompt_type = st.selectbox(
                "Batch Prompt Type",
                options=[pt.value for pt in PromptType],
                index=0,
                key="batch_type"
            )

        with col2:
            if st.button("🔄 Process Batch"):
                if not batch_input.strip():
                    st.error("Please enter prompts to process.")
                    return

                prompts = parse_batch_prompts(batch_input)
                if len(prompts) <= 1:
                    st.error("Could not parse multiple prompts. Try using numbered lists or --- separators.")
                    return

                st.info(f"Processing {len(prompts)} prompts...")

                # Process batch
                batch_optimizer = BatchOptimizer()
                try:
                    # This is simplified - in reality would be async
                    results = []
                    for prompt in prompts:
                        is_valid, sanitized, error = sanitize_and_validate_prompt(prompt)
                        if is_valid:
                            # Create orchestrator and optimize
                            orchestrator = AgentConfigManager.apply_config_to_agent(
                                None, st.session_state.agent_config
                            )
                            result = orchestrator.optimize_prompt(sanitized, PromptType(batch_prompt_type))
                            results.append(result)
                        else:
                            results.append({"success": False, "error": error, "original_prompt": prompt})

                    st.success(f"Batch processing complete! {len([r for r in results if r.get('success')])}/{len(results)} successful.")

                    # Show results summary
                    for i, result in enumerate(results, 1):
                        with st.expander(f"Prompt {i}: {'✅' if result.get('success') else '❌'}"):
                            if result.get("success"):
                                st.code(result.get("optimized_prompt", ""), language="text")
                                st.metric("Score", f"{result.get('quality_score', 0)}/100")
                            else:
                                st.error(f"Failed: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    st.error(f"Batch processing error: {str(e)}")

if __name__ == "__main__":
    main()