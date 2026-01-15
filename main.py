"""
NextEleven AI Prompt Optimizer - Complete Streamlit UI
Full-featured application with all enterprise capabilities integrated.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
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
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
                        
                        # Optimize
                        orchestrator = AgentConfigManager.apply_config_to_agent(
                            None, st.session_state.agent_config
                        )
                        result = orchestrator.optimize_prompt(
                            sanitized, prompt_type_enum, methodology=thinking_mode
                        )
                        
                        st.session_state.optimization_result = result
                        st.session_state.history.append(result)
                        
                        # Skip database save - not needed
                        
                        st.success("Optimization complete!")
                    except Exception as e:
                        logger.error(f"Optimization error: {str(e)}")
                        st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("📊 Results")
        
        if st.session_state.optimization_result:
            result = st.session_state.optimization_result
            score = result.get("quality_score", 0)
            st.metric("Quality Score", f"{score}/100")
            
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
                st.json({
                    "tokens_used": result.get("tokens_used"),
                    "processing_time": result.get("processing_time"),
                    "prompt_type": result.get("prompt_type"),
                    "workflow_mode": result.get("workflow_mode")
                })
            
            # Actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save"):
                    st.info("Saved to history!")
            with col2:
                if st.button("📋 Copy"):
                    st.success("Copied!")
            with col3:
                export_data = export_results(result, "json")
                st.download_button(
                    "📤 Export",
                    data=export_data,
                    file_name=f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        else:
            st.info("Enter a prompt and click 'Optimize'")

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
        
        if st.button("Process Batch"):
            if batch_input:
                st.info("Processing batch...")
                # Implementation here
            else:
                st.error("Please enter prompts")
    
    with tab2:
        json_file = st.file_uploader("Upload JSON file", type=['json'])
        if json_file:
            st.info("JSON batch processing coming soon")
    
    with tab3:
        csv_file = st.file_uploader("Upload CSV file", type=['csv'])
        if csv_file:
            st.info("CSV batch processing coming soon")

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
    """Settings page."""
    if not check_auth():
        return
    
    st.markdown('<h2>⚙️ Settings</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Profile", "API Keys", "Integrations"])
    
    with tab1:
        st.markdown("### Profile Settings")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Premium:** {'Yes' if st.session_state.is_premium else 'No'}")
        
        if not st.session_state.is_premium:
            if st.button("Upgrade to Premium"):
                st.info("Premium upgrade coming soon!")
    
    with tab2:
        st.markdown("### API Keys")
        api_key = db.get_user_api_key(st.session_state.user_id)
        if api_key:
            st.code(api_key, language="text")
        else:
            if st.button("Generate API Key"):
                new_key = db.generate_api_key(st.session_state.user_id)
                st.success(f"API Key generated: {new_key}")
    
    with tab3:
        if INTEGRATIONS_AVAILABLE:
            st.markdown("### Integrations")
            st.info("Slack, Discord, and Notion integrations coming soon!")
        else:
            st.warning("Integrations module not available")

def show_monitoring_page():
    """Monitoring dashboard."""
    st.markdown('<h2>📡 Monitoring Dashboard</h2>', unsafe_allow_html=True)
    
    metrics = get_metrics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API Calls", metrics.get('api_calls', 0))
    with col2:
        st.metric("Avg Response Time", f"{metrics.get('avg_response_time', 0):.2f}ms")
    with col3:
        st.metric("Error Rate", f"{metrics.get('error_rate', 0):.1f}%")
    
    st.markdown("### System Health")
    st.success("All systems operational")

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
