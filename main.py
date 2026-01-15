"""
NextEleven AI Prompt Optimizer - Complete Streamlit UI
Full-featured application with all enterprise capabilities integrated.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import time

# Core imports
from agents import OrchestratorAgent, PromptType
from agent_config import AgentConfigManager
from database import db
from input_validation import sanitize_and_validate_prompt, validate_prompt_type, validate_username, validate_email
from export_utils import export_results

# Feature imports
from batch_optimization import BatchOptimizer
from analytics import Analytics
from ab_testing import ABTesting
from voice_prompting import VoicePrompting
from monitoring import get_metrics
from error_handling import ErrorHandler
from performance import performance_tracker
from observability import get_tracker

# Enterprise imports
from enterprise_integration import (
    EnterpriseFeatureManager,
    create_blueprint,
    refine_prompt,
    generate_tests,
    compare_models,
    analyze_tokens,
    check_security
)

# Cost tracking and reliability
from cost_tracker import get_cost_optimizer
from circuit_breaker import get_api_circuit_breaker
from backup_manager import get_backup_manager

# Integration imports
try:
    from integrations import SlackIntegration, DiscordIntegration, NotionIntegration
    INTEGRATIONS_AVAILABLE = True
except ImportError:
    INTEGRATIONS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="NextEleven AI - Prompt Optimizer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# Initialize session state - NO LOGIN REQUIRED
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'authenticated': True,  # ALWAYS TRUE - NO LOGIN
        'user_id': 1,
        'username': 'User',
        'is_premium': True,  # ALWAYS TRUE - NO PAYWALL
        'current_prompt': "",
        'optimization_result': None,
        'agent_config': AgentConfigManager.DEFAULT_CONFIG.copy(),
        'show_agent_tuning': False,
        'history': [],
        'analytics': None,
        'page': 'optimize'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# NO HELPER FUNCTIONS - NO CHECKS - EVERYTHING UNLOCKED
def check_premium(feature_name: str = "This feature") -> bool:
    return True  # ALWAYS TRUE

def check_auth() -> bool:
    return True  # ALWAYS TRUE

# Main pages
def show_optimize_page():
    """Main optimization page."""
    st.markdown('<h2>✏️ Optimize Your Prompt</h2>', unsafe_allow_html=True)
    
    # Agent tuning panel
    with st.expander("🎛️ Agent Configuration", expanded=st.session_state.show_agent_tuning):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Global Settings**")
            global_temp = st.slider("Temperature", 0.0, 2.0, 
                                   st.session_state.agent_config.get("temperature", 0.7), 0.1)
            max_tokens = st.slider("Max Tokens", 1000, 4000,
                                  st.session_state.agent_config.get("max_tokens", 2000), 500)
        
        with col2:
            st.markdown("**Per-Agent Override**")
            deconstruct_temp = st.slider("Deconstructor", 0.0, 1.0, 0.5, 0.1)
            diagnose_temp = st.slider("Diagnoser", 0.0, 1.0, 0.4, 0.1)
            design_temp = st.slider("Designer", 0.0, 1.5, 0.8, 0.1)
            eval_temp = st.slider("Evaluator", 0.0, 1.0, 0.3, 0.1)
        
        st.session_state.agent_config.update({
            "temperature": global_temp,
            "max_tokens": max_tokens,
            "deconstructor": {"temperature": deconstruct_temp, "max_tokens": 1500},
            "diagnoser": {"temperature": diagnose_temp, "max_tokens": 1500},
            "designer": {"temperature": design_temp, "max_tokens": 2000},
            "evaluator": {"temperature": eval_temp, "max_tokens": 1000}
        })
    
    # Voice input (Premium)
    if st.session_state.is_premium:
        use_voice = st.checkbox("🎤 Use Voice Input")
        if use_voice:
            audio_file = st.file_uploader("Upload audio", type=['wav', 'mp3', 'm4a', 'ogg'])
            if audio_file:
                with st.spinner("Transcribing audio..."):
                    try:
                        voice_prompt = VoicePrompting()
                        transcribed = voice_prompt.transcribe_audio(audio_file.read())
                        st.session_state.current_prompt = transcribed
                        st.success("Audio transcribed!")
                    except Exception as e:
                        st.error(f"Transcription failed: {str(e)}")
    
    # Prompt input
    prompt_input = st.text_area(
        "Prompt to optimize:",
        value=st.session_state.current_prompt,
        height=150,
        placeholder="Enter your prompt here..."
    )
    st.session_state.current_prompt = prompt_input
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        prompt_type = st.selectbox("Prompt Type", [pt.value for pt in PromptType])
    
    with col_b:
        thinking_mode = st.selectbox("Thinking Mode", 
                                    ["4d", "chain_of_thought", "tree_of_thought"])
    
    with col_c:
        if st.button("🚀 Optimize", type="primary", use_container_width=True):
            if not prompt_input.strip():
                st.error("Please enter a prompt")
                return
            
            with st.spinner("Optimizing..."):
                try:
                    # Validate
                    is_valid, sanitized, error = sanitize_and_validate_prompt(prompt_input)
                    if not is_valid:
                        st.error(f"Invalid prompt: {error}")
                        return
                    
                    is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
                    if not is_valid_type:
                        st.error(f"Invalid type: {type_error}")
                        return
                    
                    # Create progress containers
                    progress_container = st.empty()
                    status_container = st.empty()
                    
                    # Optimize with progress updates
                    status_container.info("⏳ Step 1/4: Deconstructing prompt...")
                    orchestrator = AgentConfigManager.apply_config_to_agent(
                        None, st.session_state.agent_config
                    )
                    
                    status_container.info("⏳ Step 2/4: Diagnosing issues...")
                    time.sleep(0.5)  # Brief pause for UX
                    
                    result = orchestrator.optimize_prompt(
                        sanitized, prompt_type_enum, methodology=thinking_mode
                    )
                    
                    status_container.info("⏳ Step 3/4: Designing optimized version...")
                    time.sleep(0.5)
                    
                    status_container.info("⏳ Step 4/4: Evaluating quality...")
                    time.sleep(0.5)
                    
                    st.session_state.optimization_result = result
                    st.session_state.history.append(result)
                    
                    # Clear progress indicators
                    progress_container.empty()
                    status_container.empty()
                    
                    st.success("✅ Optimization complete!")
                    
                    # Show cost info
                    cost_optimizer = get_cost_optimizer()
                    recent_cost = cost_optimizer.records[-1] if cost_optimizer.records else None
                    if recent_cost:
                        st.info(f"💰 Cost: ${recent_cost.cost_usd:.4f} | Tokens: {recent_cost.total_tokens:,}")
                    
                except Exception as e:
                    logger.error(f"Optimization error: {str(e)}")
                    if 'progress_container' in locals():
                        progress_container.empty()
                    if 'status_container' in locals():
                        status_container.empty()
                    st.error(f"❌ Error: {str(e)}")
    
    # Results section - NOW BELOW THE INPUT
    st.markdown("---")
    st.subheader("📊 Results")
    
    if st.session_state.optimization_result:
        result = st.session_state.optimization_result
        
        # Check if we have a valid optimized prompt
        optimized = result.get("optimized_prompt", "")
        design_output = result.get("design_output", "")
        
        # If optimized is empty but we have design_output, use that
        if not optimized or optimized.strip() == "":
            if design_output and design_output.strip():
                optimized = design_output
            elif result.get("deconstruction"):
                optimized = result.get("deconstruction", "")
            else:
                optimized = "No optimized prompt available yet."
        
        # Show errors if any (but don't block display - errors in later phases shouldn't hide the prompt)
        # Only show errors that are NOT related to sample output or evaluation (those are non-critical)
        critical_errors = []
        non_critical_errors = []
        for error in result.get("errors", []):
            error_lower = str(error).lower()
            if any(term in error_lower for term in ["sample output", "evaluation", "evaluator"]):
                non_critical_errors.append(error)
            else:
                critical_errors.append(error)
        
        if critical_errors:
            error_count = len(critical_errors)
            with st.expander(f"⚠️ {error_count} error(s) during optimization", expanded=False):
                for error in critical_errors:
                    st.error(f"• {error}")
        
        if non_critical_errors:
            # These are just warnings - optimization succeeded but some optional steps failed
            pass  # Don't show these prominently
        
        score = result.get("quality_score", 0)
        if score:
            st.metric("Quality Score", f"{score}/100")
        
        tab1, tab2, tab3, tab4 = st.tabs(["✨ Optimized Prompt", "🔍 Analysis", "📝 Sample Output", "⚙️ Details"])
        
        with tab1:
            st.markdown("### ✨ Your Optimized Prompt")
            if optimized and optimized.strip():
                st.code(optimized, language="text")
                
                # Copy button
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Copy to Clipboard", use_container_width=True):
                        st.code(optimized, language="text")
                        st.success("Copied! (Use Cmd/Ctrl+C)")
                with col2:
                    if st.button("💾 Save to History", use_container_width=True):
                        st.info("Saved!")
            else:
                st.info("No optimized prompt available. The optimization may have encountered errors.")
            
            # Show full design output if different from extracted
            if design_output and design_output != optimized and len(design_output) > len(optimized):
                with st.expander("🔍 View Full Design Output"):
                    st.text(design_output)
            
        with tab2:
            st.markdown("### 🔍 Analysis")
            
            if result.get("deconstruction"):
                with st.expander("📋 Deconstruction", expanded=True):
                    st.write(result.get("deconstruction", ""))
            
            if result.get("diagnosis"):
                with st.expander("🔬 Diagnosis", expanded=False):
                    st.write(result.get("diagnosis", ""))
            
            if result.get("evaluation"):
                with st.expander("⭐ Evaluation", expanded=False):
                    st.write(result.get("evaluation", ""))
            
            if not any([result.get("deconstruction"), result.get("diagnosis"), result.get("evaluation")]):
                st.info("Analysis data will appear here after optimization.")
        
        with tab3:
            st.markdown("### 📝 Sample Output")
            sample = result.get("sample_output", "")
            if sample and sample.strip() and "failed" not in sample.lower():
                st.write(sample)
            else:
                st.info("Sample output will appear here after optimization.")
        
        with tab4:
            st.markdown("### ⚙️ Technical Details")
            st.json({
                "prompt_type": result.get("prompt_type"),
                "workflow_mode": result.get("workflow_mode"),
                "quality_score": result.get("quality_score"),
                "has_errors": len(result.get("errors", [])) > 0,
                "error_count": len(result.get("errors", []))
            })
            
            if result.get("errors"):
                st.markdown("#### Errors/Warnings")
                for error in result.get("errors", []):
                    st.warning(f"• {error}")
    else:
        st.info("👆 Enter a prompt above and click '🚀 Optimize' to see results here.")

def show_batch_page():
    """Batch optimization page."""
    st.markdown('<h2>📦 Batch Optimization</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "JSON Upload", "CSV Upload"])
    
    with tab1:
        batch_input = st.text_area(
            "Enter multiple prompts (one per line or numbered):",
            height=200,
            placeholder="1. Build a code review agent\n2. Create API docs\n3. Design workflow"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            batch_prompt_type = st.selectbox("Prompt Type for All", [pt.value for pt in PromptType])
        with col2:
            batch_methodology = st.selectbox("Methodology", ["4d", "chain_of_thought", "tree_of_thought"])
        
        if st.button("🚀 Process Batch", type="primary"):
            if batch_input:
                # Parse prompts (handle numbered lists and plain lines)
                lines = batch_input.strip().split('\n')
                prompts = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Remove numbering (1., 2., etc.)
                    import re
                    cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                    if cleaned:
                        prompts.append(cleaned)
                
                if not prompts:
                    st.error("No valid prompts found")
                    return
                
                st.info(f"Processing {len(prompts)} prompts...")
                
                # Create progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                results = []
                orchestrator = AgentConfigManager.apply_config_to_agent(
                    None, st.session_state.agent_config
                )
                
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
                        
                        is_valid_type, prompt_type_enum, type_error = validate_prompt_type(batch_prompt_type)
                        if not is_valid_type:
                            results.append({
                                "prompt": prompt,
                                "status": "error",
                                "error": type_error
                            })
                            continue
                        
                        result = orchestrator.optimize_prompt(
                            sanitized, prompt_type_enum, methodology=batch_methodology
                        )
                        result["status"] = "success"
                        result["original_prompt"] = prompt
                        results.append(result)
                        
                    except Exception as e:
                        logger.error(f"Batch processing error for prompt {idx + 1}: {str(e)}")
                        results.append({
                            "prompt": prompt,
                            "status": "error",
                            "error": str(e)
                        })
                    
                    progress_bar.progress((idx + 1) / len(prompts))
                
                status_text.text("✅ Batch processing complete!")
                
                # Display results
                with results_container:
                    st.markdown("### Results")
                    
                    successful = [r for r in results if r.get("status") == "success"]
                    failed = [r for r in results if r.get("status") == "error"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total", len(prompts))
                    with col2:
                        st.metric("Successful", len(successful))
                    with col3:
                        st.metric("Failed", len(failed))
                    
                    # Export all results
                    if successful:
                        export_data = json.dumps(results, indent=2)
                        st.download_button(
                            "📥 Download All Results (JSON)",
                            data=export_data,
                            file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    # Show individual results
                    for idx, result in enumerate(results):
                        with st.expander(f"Prompt {idx + 1}: {result.get('original_prompt', result.get('prompt', ''))[:60]}..."):
                            if result.get("status") == "success":
                                st.markdown("**✅ Optimized Prompt:**")
                                st.code(result.get("optimized_prompt", ""), language="text")
                                st.markdown(f"**Quality Score:** {result.get('quality_score', 'N/A')}/100")
                            else:
                                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            else:
                st.error("Please enter prompts")
    
    with tab2:
        st.markdown("### Upload JSON File")
        st.markdown("Expected format: `{\"prompts\": [\"prompt1\", \"prompt2\", ...]}`")
        
        json_file = st.file_uploader("Upload JSON file", type=['json'])
        
        if json_file:
            try:
                data = json.load(json_file)
                prompts = data.get("prompts", [])
                
                if prompts:
                    st.success(f"Loaded {len(prompts)} prompts from JSON")
                    st.text_area("Preview:", value='\n'.join(prompts[:5]), height=150, disabled=True)
                    
                    if len(prompts) > 5:
                        st.info(f"... and {len(prompts) - 5} more")
                    
                    if st.button("Process JSON Batch"):
                        st.session_state['batch_input_from_json'] = '\n'.join(prompts)
                        st.rerun()
                else:
                    st.warning("No prompts found in JSON file")
            except Exception as e:
                st.error(f"Error reading JSON: {str(e)}")
    
    with tab3:
        st.markdown("### Upload CSV File")
        st.markdown("Expected format: CSV with a 'prompt' column")
        
        csv_file = st.file_uploader("Upload CSV file", type=['csv'])
        
        if csv_file:
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                
                if 'prompt' in df.columns:
                    prompts = df['prompt'].dropna().tolist()
                    st.success(f"Loaded {len(prompts)} prompts from CSV")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("Process CSV Batch"):
                        st.session_state['batch_input_from_csv'] = '\n'.join(prompts)
                        st.rerun()
                else:
                    st.error("CSV must have a 'prompt' column")
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")

def show_analytics_page():
    """Analytics dashboard page."""
    st.markdown('<h2>📊 Analytics Dashboard</h2>', unsafe_allow_html=True)
    
    # Initialize analytics
    if st.session_state.analytics is None:
        st.session_state.analytics = Analytics()
    
    analytics = st.session_state.analytics
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["7 days", "30 days", "90 days", "All time"])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Optimizations", analytics.get_total_optimizations(st.session_state.user_id))
    with col2:
        st.metric("Avg Quality Score", f"{analytics.get_average_quality_score(st.session_state.user_id):.1f}")
    with col3:
        st.metric("Tokens Used", analytics.get_total_tokens(st.session_state.user_id))
    with col4:
        st.metric("Avg Processing Time", f"{analytics.get_avg_processing_time(st.session_state.user_id):.2f}s")
    
    # Charts
    st.markdown("### Quality Score Trends")
    st.line_chart(analytics.get_quality_trends(st.session_state.user_id))
    
    st.markdown("### Prompt Type Distribution")
    st.bar_chart(analytics.get_prompt_type_distribution(st.session_state.user_id))

def show_ab_testing_page():
    """A/B testing page."""
    st.markdown('<h2>🧪 A/B Testing</h2>', unsafe_allow_html=True)
    
    ab_tester = ABTesting()
    
    # Create new test
    with st.expander("Create New A/B Test"):
        test_name = st.text_input("Test Name")
        original_prompt = st.text_area("Original Prompt")
        variant_a = st.text_area("Variant A")
        variant_b = st.text_area("Variant B")
        
        if st.button("Create Test"):
            if all([test_name, original_prompt, variant_a, variant_b]):
                test_id = ab_tester.create_test(
                    user_id=st.session_state.user_id,
                    test_name=test_name,
                    original_prompt=original_prompt,
                    variant_a=variant_a,
                    variant_b=variant_b
                )
                st.success(f"Test created! ID: {test_id}")
            else:
                st.error("Please fill all fields")
    
    # View existing tests
    st.markdown("### Your A/B Tests")
    tests = ab_tester.get_user_tests(st.session_state.user_id)
    for test in tests:
        with st.expander(f"{test['name']} - {test['status']}"):
            st.write(f"**Created:** {test['created_at']}")
            st.write(f"**Variant A Score:** {test['variant_a_score']}")
            st.write(f"**Variant B Score:** {test['variant_b_score']}")
            if test['winner']:
                st.success(f"Winner: {test['winner']}")

def show_enterprise_page():
    """Enterprise features page."""
    st.markdown('<h2>🏢 Enterprise Features</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Blueprints", "Refinement", "Testing", "Security"])
    
    with tab1:
        st.markdown("### Agent Blueprint Generator")
        description = st.text_area("Agent Description")
        agent_type = st.selectbox("Agent Type", 
                                  ["conversational", "task_executor", "analyst", "orchestrator"])
        
        if st.button("Generate Blueprint"):
            if description:
                with st.spinner("Generating blueprint..."):
                    blueprint = create_blueprint(description, agent_type)
                    st.json(blueprint)
            else:
                st.error("Please enter a description")
    
    with tab2:
        st.markdown("### Iterative Refinement")
        prompt_to_refine = st.text_area("Prompt to Refine")
        feedback = st.text_area("Feedback")
        
        if st.button("Refine Prompt"):
            if prompt_to_refine and feedback:
                refined = refine_prompt(prompt_to_refine, feedback)
                st.code(refined, language="text")
            else:
                st.error("Please provide prompt and feedback")
    
    with tab3:
        st.markdown("### Test Case Generator")
        prompt_for_tests = st.text_area("Prompt to Generate Tests For")
        
        if st.button("Generate Tests"):
            if prompt_for_tests:
                tests = generate_tests(prompt_for_tests)
                st.json(tests)
            else:
                st.error("Please enter a prompt")
    
    with tab4:
        st.markdown("### Security Scanner")
        prompt_to_scan = st.text_area("Prompt to Scan")
        
        if st.button("Scan for Security Issues"):
            if prompt_to_scan:
                security_report = check_security(prompt_to_scan)
                if security_report['is_safe']:
                    st.success("✅ No security issues found")
                else:
                    st.warning("⚠️ Security issues detected:")
                    for issue in security_report['issues']:
                        st.error(f"- {issue}")
            else:
                st.error("Please enter a prompt")

def show_history_page():
    """Session history page."""
    st.markdown('<h2>📚 Session History</h2>', unsafe_allow_html=True)
    
    sessions = db.get_user_sessions(st.session_state.user_id, limit=50)
    
    if sessions:
        for session in sessions:
            with st.expander(f"{session['created_at']} - Score: {session['quality_score']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original:**")
                    st.text(session['original_prompt'][:200])
                with col2:
                    st.markdown("**Optimized:**")
                    st.text(session['optimized_prompt'][:200])
                
                if st.button(f"Load Session {session['id']}", key=f"load_{session['id']}"):
                    st.session_state.optimization_result = session
                    st.session_state.page = 'optimize'
                    st.rerun()
    else:
        st.info("No optimization history yet. Start optimizing!")

def show_settings_page():
    """Settings page with backup and data management."""
    st.markdown('<h2>⚙️ Settings & Data Management</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Backup & Export", "Preferences", "Advanced", "About"])
    
    with tab1:
        st.markdown("### 💾 Backup & Export")
        
        backup_manager = get_backup_manager()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Create Backup")
            include_cache = st.checkbox("Include cache files", value=False)
            
            if st.button("📦 Create Backup Now", type="primary"):
                with st.spinner("Creating backup..."):
                    try:
                        backup_path = backup_manager.create_backup(
                            include_db=True,
                            include_cache=include_cache
                        )
                        st.success(f"✅ Backup created: {Path(backup_path).name}")
                        
                        # Offer download
                        with open(backup_path, 'rb') as f:
                            st.download_button(
                                "📥 Download Backup",
                                data=f.read(),
                                file_name=Path(backup_path).name,
                                mime="application/zip"
                            )
                    except Exception as e:
                        st.error(f"Backup failed: {str(e)}")
        
        with col2:
            st.markdown("#### Export Data")
            
            if st.button("📄 Export to JSON"):
                with st.spinner("Exporting..."):
                    try:
                        export_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        if backup_manager.export_to_json(export_path):
                            with open(export_path, 'r') as f:
                                st.download_button(
                                    "📥 Download JSON Export",
                                    data=f.read(),
                                    file_name=export_path,
                                    mime="application/json"
                                )
                            Path(export_path).unlink()  # Cleanup
                    except Exception as e:
                        st.error(f"Export failed: {str(e)}")
        
        st.markdown("---")
        st.markdown("#### 📚 Available Backups")
        
        backups = backup_manager.list_backups()
        
        if backups:
            for backup in backups[:10]:  # Show last 10
                with st.expander(f"{backup['filename']} - {backup['size_mb']:.2f} MB"):
                    st.write(f"**Created:** {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Restore", key=f"restore_{backup['filename']}"):
                            if st.confirm("Are you sure? This will replace current data."):
                                with st.spinner("Restoring..."):
                                    if backup_manager.restore_backup(backup['path']):
                                        st.success("Restore completed! Please restart the app.")
                                    else:
                                        st.error("Restore failed")
                    
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
    
    with tab2:
        st.markdown("### 🎨 Preferences")
        
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
    
    with tab3:
        st.markdown("### 🔧 Advanced Settings")
        
        st.markdown("#### Cache Management")
        
        from enhanced_cache import get_smart_cache
        cache = get_smart_cache()
        cache_stats = cache.get_cache_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cache Hits", cache_stats['hits'])
        with col2:
            st.metric("Cache Misses", cache_stats['misses'])
        with col3:
            st.metric("Hit Rate", f"{cache_stats['hit_rate']:.1f}%")
        
        if st.button("Clear All Caches"):
            cache.clear_all()
            st.success("Caches cleared!")
        
        st.markdown("---")
        st.markdown("#### Database Maintenance")
        
        if st.button("Optimize Database"):
            st.info("Database optimization coming soon")
    
    with tab4:
        st.markdown("### ℹ️ About")
        
        st.markdown("""
        **AI-Powered Prompt Optimizer**
        
        Version: 2.0.0  
        Built with: Python 3.14, Streamlit 1.52, xAI Grok API
        
        **Features:**
        - Multi-agent 4-D optimization
        - 10+ enterprise features
        - Cost tracking & optimization
        - Automated backups
        - Circuit breaker protection
        - Advanced caching
        
        **Personal Edition**  
        No login, no limits, all features enabled.
        
        Built by S. McDonnell at NextEleven
        """)

def show_monitoring_page():
    """Monitoring dashboard with cost tracking."""
    st.markdown('<h2>📡 Monitoring & Cost Dashboard</h2>', unsafe_allow_html=True)
    
    # Get cost optimizer and circuit breaker
    cost_optimizer = get_cost_optimizer()
    circuit_breaker = get_api_circuit_breaker()
    metrics = get_metrics()
    
    # Cost Summary Section
    st.markdown("### 💰 Cost Tracking")
    
    col1, col2, col3, col4 = st.columns(4)
    
    today_cost = cost_optimizer.get_today_cost()
    month_cost = cost_optimizer.get_month_cost()
    
    with col1:
        st.metric("Today's Cost", f"${today_cost:.2f}")
    with col2:
        st.metric("This Month", f"${month_cost:.2f}")
    with col3:
        forecast = cost_optimizer.get_forecast(30)
        st.metric("30-Day Forecast", f"${forecast['estimated_cost']:.2f}")
    with col4:
        summary = cost_optimizer.get_summary()
        st.metric("Total Calls", summary['total_calls'])
    
    # Budget Management
    with st.expander("💵 Budget Management"):
        col1, col2 = st.columns(2)
        with col1:
            daily_budget = st.number_input("Daily Budget ($)", min_value=0.0, value=10.0, step=1.0)
        with col2:
            monthly_budget = st.number_input("Monthly Budget ($)", min_value=0.0, value=100.0, step=10.0)
        
        if st.button("Set Budgets"):
            cost_optimizer.set_budgets(daily=daily_budget, monthly=monthly_budget)
            st.success("Budgets updated!")
    
    # Detailed Cost Breakdown
    st.markdown("### 📊 Cost Breakdown")
    
    tab1, tab2, tab3 = st.tabs(["By Model", "By Operation", "Recent Calls"])
    
    with tab1:
        if summary['by_model']:
            import pandas as pd
            model_data = []
            for model, stats in summary['by_model'].items():
                model_data.append({
                    "Model": model,
                    "Calls": stats['calls'],
                    "Total Cost": f"${stats['cost']:.4f}",
                    "Tokens": f"{stats['tokens']:,}"
                })
            df = pd.DataFrame(model_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No cost data yet")
    
    with tab2:
        if summary['by_operation']:
            import pandas as pd
            op_data = []
            for operation, stats in summary['by_operation'].items():
                op_data.append({
                    "Operation": operation,
                    "Calls": stats['calls'],
                    "Total Cost": f"${stats['cost']:.4f}",
                    "Tokens": f"{stats['tokens']:,}"
                })
            df = pd.DataFrame(op_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No cost data yet")
    
    with tab3:
        recent_records = cost_optimizer.records[-20:]  # Last 20
        if recent_records:
            import pandas as pd
            recent_data = []
            for record in reversed(recent_records):
                recent_data.append({
                    "Time": record.timestamp.strftime("%H:%M:%S"),
                    "Model": record.model,
                    "Operation": record.operation,
                    "Tokens": f"{record.total_tokens:,}",
                    "Cost": f"${record.cost_usd:.4f}"
                })
            df = pd.DataFrame(recent_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent calls")
    
    # Export costs
    if st.button("📥 Export Cost Data"):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            cost_optimizer.export_records(f.name)
            with open(f.name, 'r') as rf:
                data = rf.read()
            st.download_button(
                "Download JSON",
                data=data,
                file_name=f"cost_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    st.markdown("---")
    
    # System Health Section
    st.markdown("### 🏥 System Health")
    
    col1, col2, col3 = st.columns(3)
    
    circuit_state = circuit_breaker.get_state()
    
    with col1:
        if circuit_state.value == "closed":
            st.success("✅ API Circuit: HEALTHY")
        elif circuit_state.value == "half_open":
            st.warning("⚠️ API Circuit: TESTING")
        else:
            st.error("❌ API Circuit: DEGRADED")
    
    with col2:
        st.metric("API Calls", metrics.get_counter('api_requests'))
    with col3:
        cache_hits = metrics.get_counter('api_cache_hits')
        total_requests = metrics.get_counter('api_requests')
        cache_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        st.metric("Cache Hit Rate", f"{cache_rate:.1f}%")
    
    # Performance Metrics
    st.markdown("### ⚡ Performance Metrics")
    
    timer_stats = metrics.get_timer_stats('api_request')
    if timer_stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Latency", f"{timer_stats['avg']*1000:.0f}ms")
        with col2:
            st.metric("P95 Latency", f"{timer_stats['p95']*1000:.0f}ms")
        with col3:
            st.metric("Min Latency", f"{timer_stats['min']*1000:.0f}ms")
        with col4:
            st.metric("Max Latency", f"{timer_stats['max']*1000:.0f}ms")
    
    # Reset options
    with st.expander("⚙️ System Controls"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset Circuit Breaker"):
                circuit_breaker.reset()
                st.success("Circuit breaker reset!")
        with col2:
            if st.button("Clear Metrics"):
                metrics.reset()
                st.success("Metrics cleared!")

# Main app
def main():
    """Main application."""
    # NO LOGIN CHECK - ALWAYS SHOW APP
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🚀 NextEleven AI")
        st.markdown("**All Features Unlocked**")
        
        st.markdown("---")
        
        # Navigation
        pages = {
            "optimize": "✏️ Optimize",
            "batch": "📦 Batch",
            "analytics": "📊 Analytics",
            "ab_testing": "🧪 A/B Testing",
            "enterprise": "🏢 Enterprise",
            "history": "📚 History",
            "settings": "⚙️ Settings",
            "monitoring": "📡 Monitoring"
        }
        
        for key, label in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()
        
        st.markdown("---")
        st.caption("No login • All features enabled")
    
    # Show selected page
    page_functions = {
        "optimize": show_optimize_page,
        "batch": show_batch_page,
        "analytics": show_analytics_page,
        "ab_testing": show_ab_testing_page,
        "enterprise": show_enterprise_page,
        "history": show_history_page,
        "settings": show_settings_page,
        "monitoring": show_monitoring_page
    }
    
    page_func = page_functions.get(st.session_state.page, show_optimize_page)
    page_func()

if __name__ == "__main__":
    main()
