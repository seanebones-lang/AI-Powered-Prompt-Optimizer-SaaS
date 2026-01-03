"""
Main Streamlit application for AI-Powered Prompt Optimizer SaaS.
Implements the full UI with authentication, optimization workflow, and evaluation dashboard.
"""
import streamlit as st
import logging
import sqlite3
import time
from agents import OrchestratorAgent, PromptType
from database import db
from config import settings
from input_validation import (
    sanitize_and_validate_prompt,
    validate_prompt_type,
    validate_username,
    validate_email
)
from export_utils import export_results
from analytics import Analytics
from batch_optimization import BatchOptimizer
from ab_testing import ABTesting
from agent_config import AgentConfigManager
from voice_prompting import VoicePrompting
from monitoring import get_metrics
from error_handling import ErrorHandler
from performance import performance_tracker
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Prompt Optimizer (Beta)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- IP-Based Rate Limiting Setup (Beta/Public Access) ---
@st.cache_resource
def get_rate_limit_db():
    """Get rate limiting database connection."""
    conn = sqlite3.connect('rate_limit.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests 
                 (ip TEXT, timestamp REAL)''')
    conn.commit()
    return conn, c

rate_limit_conn, rate_limit_c = get_rate_limit_db()

def get_ip():
    """Extract client IP address."""
    try:
        # Try to get IP from Streamlit context
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            x_forwarded_for = st.context.headers.get('X-Forwarded-For')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0].strip()
        
        # Fallback for local development
        return 'localhost'
    except Exception as e:
        logger.warning(f"Could not determine IP: {str(e)}")
        return 'unknown'

def check_ip_rate_limit(ip: str, max_requests: int = 5, window_hours: int = 24) -> bool:
    """
    Check if IP has exceeded rate limit.
    
    Args:
        ip: IP address
        max_requests: Maximum requests allowed
        window_hours: Time window in hours
    
    Returns:
        True if within limit, False if exceeded
    
    Security: Fails closed (returns False on error) to prevent bypassing rate limits.
    """
    try:
        cutoff = time.time() - (window_hours * 3600)
        # Clean old records
        rate_limit_c.execute("DELETE FROM requests WHERE timestamp < ?", (cutoff,))
        # Count requests in window
        rate_limit_c.execute(
            "SELECT COUNT(*) FROM requests WHERE ip = ? AND timestamp >= ?",
            (ip, cutoff)
        )
        count = rate_limit_c.fetchone()[0]
        
        if count >= max_requests:
            return False
        
        # Record this request
        rate_limit_c.execute(
            "INSERT INTO requests (ip, timestamp) VALUES (?, ?)",
            (ip, time.time())
        )
        rate_limit_conn.commit()
        return True
    except Exception as e:
        logger.error(f"Rate limit check error: {str(e)}", exc_info=True)
        # Fail closed for security - deny request if we can't verify limit
        return False

# --- Force Dark Mode with Teal/White Theme via CSS ---
# Professional styling with glassmorphism effects (January 2026)
st.markdown("""
    <style>
    /* Import Inter font for modern look */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global font */
    .stApp, .stMarkdown, p, label, span {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Base dark mode with slate colors */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        color: #F8FAFC !important;
    }

    /* Main container background */
    .main .block-container {
        background-color: transparent !important;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* Text and headers */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, div[data-baseweb="select"] {
        color: #F8FAFC !important;
    }

    /* Main header styling with gradient */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #14B8A6 0%, #2DD4BF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
    }

    /* Teal accents for buttons with gradient and hover effect */
    .stButton > button {
        background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%) !important;
        color: #0F172A !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px -1px rgba(20, 184, 166, 0.25) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(20, 184, 166, 0.3) !important;
    }

    /* Glassmorphism cards for containers */
    .glass-card {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        padding: 1.5rem !important;
    }

    /* Select boxes with modern styling */
    .stSelectbox > div > div {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* Input fields with focus effects */
    .stTextInput > div > div > input {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 2px solid #334155 !important;
        border-radius: 8px !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #14B8A6 !important;
        box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15) !important;
    }

    .stTextArea > div > div > textarea {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 2px solid #334155 !important;
        border-radius: 8px !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #14B8A6 !important;
        box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.15) !important;
    }

    /* Sidebar with gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #F8FAFC !important;
    }

    /* Tabs with modern styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border-radius: 12px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94A3B8 !important;
        border-radius: 8px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #14B8A6 !important;
        color: #0F172A !important;
    }

    /* Code blocks */
    .stCodeBlock {
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* Info boxes with glassmorphism */
    .stAlert {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
    }

    /* Score badges with gradient backgrounds */
    .score-badge {
        padding: 0.75rem 1.25rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.2rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .score-high {
        background: linear-gradient(135deg, #14B8A6 0%, #10B981 100%) !important;
        color: #0F172A !important;
    }
    .score-medium {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
    }
    .score-low {
        background: linear-gradient(135deg, #64748B 0%, #475569 100%) !important;
        color: #F8FAFC !important;
    }

    /* Agent status badges */
    .agent-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .agent-badge.active {
        background: rgba(20, 184, 166, 0.15);
        color: #2DD4BF;
        border: 1px solid #14B8A6;
    }
    .agent-badge.complete {
        background: rgba(34, 197, 94, 0.15);
        color: #4ADE80;
        border: 1px solid #22C55E;
    }

    /* Metrics cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
    }
    [data-testid="stMetricValue"] {
        color: #14B8A6 !important;
        font-weight: 700 !important;
    }

    /* Progress bar with gradient */
    .stProgress > div > div {
        background: linear-gradient(90deg, #14B8A6 0%, #2DD4BF 100%) !important;
        border-radius: 9999px !important;
    }

    /* Footer styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: linear-gradient(180deg, transparent 0%, #0F172A 100%);
        color: #94A3B8;
        text-align: center;
        padding: 15px;
        font-size: 12px;
        z-index: 999;
    }
    .footer a {
        color: #14B8A6;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .footer a:hover {
        color: #2DD4BF;
    }

    /* Success/Error messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        border-radius: 12px !important;
    }
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 8px !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #14B8A6 !important;
    }

    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    </style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    # Beta mode: Skip authentication, auto-authenticate
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = True  # Auto-authenticate for beta
    if "user" not in st.session_state:
        st.session_state.user = None  # No user required for beta
    if "optimization_results" not in st.session_state:
        st.session_state.optimization_results = None


def check_auth_required():
    """Check if user needs to authenticate."""
    # Beta mode: Always return True (skip auth)
    return True


def check_usage_limit() -> bool:
    """Check if user has reached daily usage limit."""
    # Beta mode: No usage limits
    return True


def show_login_page():
    """Display login/signup page."""
    st.title("🚀 AI-Powered Prompt Optimizer (Beta)")
    st.markdown("### Sign in or create an account to get started")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if username and password:
                # Validate username format
                is_valid, error = validate_username(username)
                if not is_valid:
                    st.error(f"❌ {error}")
                else:
                    user = db.authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create Account")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        
        if st.button("Sign Up", type="primary", use_container_width=True):
            if not all([new_username, new_email, new_password, confirm_password]):
                st.warning("Please fill in all fields")
            else:
                # Validate inputs
                is_valid_username, username_error = validate_username(new_username)
                if not is_valid_username:
                    st.error(f"❌ Username: {username_error}")
                    return
                
                is_valid_email, email_error = validate_email(new_email)
                if not is_valid_email:
                    st.error(f"❌ Email: {email_error}")
                    return
                
                if new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    user = db.create_user(new_username, new_email, new_password)
                    if user:
                        st.success("✅ Account created successfully! Please log in.")
                    else:
                        st.error("❌ Username or email already exists")


def show_main_app():
    """Display main application interface."""
    # Sidebar navigation
    with st.sidebar:
        st.title("🚀 Prompt Optimizer")
        
        # Beta mode: No user display needed
        st.markdown("**🚀 Beta Testing Mode**")
        st.info("💡 All features are available for testing!")
        
        st.markdown("---")
        st.markdown("### Navigation")
        
        # Page selection
        page = st.radio(
            "Select Page",
            ["Optimize", "Analytics", "Batch", "A/B Testing", "Export", "Settings"],
            label_visibility="collapsed"
        )
        
        # Beta mode: All features available
        st.markdown("---")
        st.markdown("### All Features")
        if st.button("Agent Config", use_container_width=True):
            page = "Agent Config"
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool uses a multi-agent system to optimize your prompts using Lyra's 4-D methodology:
        - **Deconstruct**: Break down your prompt
        - **Diagnose**: Identify issues
        - **Design**: Create optimized version
        - **Deliver**: Generate sample output
        """)
    
    # Route to appropriate page
    if page == "Optimize":
        show_optimize_page()
    elif page == "Analytics":
        show_analytics_page()
    elif page == "Batch":
        show_batch_page()
    elif page == "A/B Testing":
        show_ab_testing_page()
    elif page == "Export":
        show_export_page()
    elif page == "Settings":
        show_settings_page()
    elif page == "Agent Config":
        show_agent_config_page()


def show_optimize_page():
    """Display the main optimization page."""
    
    # Main content
    st.markdown('<div class="main-header">AI-Powered Prompt Optimizer (Beta)</div>', unsafe_allow_html=True)
    
    # Prompt input section
    st.subheader("📝 Enter Your Prompt")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt_type = st.selectbox(
            "Prompt Type",
            options=[pt.value for pt in PromptType],
            format_func=lambda x: x.capitalize()
        )
    
    # Voice input option (beta: available to all)
    use_voice = st.checkbox("🎤 Use Voice Input")
    
    if use_voice:
        audio_file = st.file_uploader("Upload Audio File", type=["wav", "mp3", "m4a", "ogg"])
        if audio_file:
            voice_prompting = VoicePrompting()
            with st.spinner("Transcribing audio..."):
                result = voice_prompting.process_voice_prompt(audio_file.read(), audio_file.name.split('.')[-1])
                if result.get("success"):
                    user_prompt = st.text_area(
                        "Your Prompt (from voice)",
                        value=result.get("text", ""),
                        height=150,
                        help="Transcribed from audio. You can edit if needed."
                    )
                else:
                    st.error(f"Error transcribing audio: {result.get('error')}")
                    user_prompt = st.text_area(
                        "Your Prompt",
                        height=150,
                        placeholder="Enter your prompt here... For example: 'Write a blog post about AI'",
                        help="Enter the prompt you want to optimize"
                    )
        else:
            user_prompt = st.text_area(
                "Your Prompt",
                height=150,
                placeholder="Upload an audio file to transcribe, or enter text manually",
                help="Enter the prompt you want to optimize"
            )
    else:
        user_prompt = st.text_area(
            "Your Prompt",
            height=150,
            placeholder="Enter your prompt here... For example: 'Write a blog post about AI'",
            help="Enter the prompt you want to optimize"
        )
    
    # Beta mode: No usage limits
    
    # Optimize button
    if st.button("🚀 Optimize Prompt", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.warning("⚠️ Please enter a prompt to optimize")
        else:
            # Validate and sanitize prompt
            is_valid, sanitized_prompt, validation_error = sanitize_and_validate_prompt(user_prompt)
            if not is_valid:
                st.error(f"❌ {validation_error}")
                return
            
            # Validate prompt type
            is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type)
            if not is_valid_type:
                st.error(f"❌ {type_error}")
                return
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Initializing optimization...")
                progress_bar.progress(10)
                
                # Beta mode: Agent config available to all (if user exists)
                agent_config = None
                if st.session_state.user:
                    agent_config = AgentConfigManager.get_default_config(st.session_state.user.id)
                
                orchestrator = OrchestratorAgent()
                # Apply config if available (placeholder - would need agent modification)
                if agent_config:
                    orchestrator = AgentConfigManager.apply_config_to_agent(orchestrator, agent_config)
                
                # Check if this is an identity query (use sanitized prompt)
                status_text.text("🔍 Checking query type...")
                progress_bar.progress(20)
                identity_response = orchestrator.handle_identity_query(sanitized_prompt)
                if identity_response:
                    # Identity queries don't count toward usage limits
                    st.session_state.optimization_results = {
                        "original_prompt": sanitized_prompt,  # Store sanitized version
                        "prompt_type": prompt_type,
                        "identity_response": identity_response,
                        "is_identity_query": True
                    }
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    st.success("✅ Response from NextEleven AI!")
                    st.rerun()
                
                # Regular optimization workflow (use sanitized prompt and validated type)
                status_text.text("🚀 Optimizing prompt with multi-agent system...")
                progress_bar.progress(30)
                
                with performance_tracker("optimization"):
                    results = orchestrator.optimize_prompt(
                        sanitized_prompt,
                        prompt_type_enum
                    )
                
                progress_bar.progress(90)
                status_text.text("💾 Saving results...")
                
                # Beta mode: Don't track usage limits
                # user_id = st.session_state.user.id if st.session_state.user else None
                # db.increment_usage(user_id)
                
                # Beta mode: Optionally save session (for analytics, not required)
                # Save session (use sanitized prompt)
                optimized_prompt_text = results.get("optimized_prompt", "")[:1000]  # Limit length
                sample_output = results.get("sample_output", "")[:2000]
                quality_score = results.get("quality_score")
                
                # Optional: Save for analytics (user_id can be None in beta)
                user_id = st.session_state.user.id if st.session_state.user else None
                try:
                    db.save_session(
                        user_id=user_id,
                        original_prompt=sanitized_prompt,  # Store sanitized version
                        prompt_type=prompt_type,
                        optimized_prompt=optimized_prompt_text,
                        sample_output=sample_output,
                        quality_score=quality_score
                    )
                except Exception as e:
                    logger.debug(f"Optional session save failed (beta mode): {str(e)}")
                
                st.session_state.optimization_results = results
                
                # Store in recent optimizations (beta mode)
                if "recent_optimizations" not in st.session_state:
                    st.session_state.recent_optimizations = []
                st.session_state.recent_optimizations.append({
                    "original_prompt": sanitized_prompt,
                    "optimized_prompt": results.get("optimized_prompt", ""),
                    "quality_score": quality_score,
                    "prompt_type": prompt_type
                })
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                st.success("✅ Optimization complete!")
                
                # Track metrics
                metrics = get_metrics()
                metrics.increment("optimizations.completed")
                if quality_score:
                    metrics.gauge("optimizations.avg_quality_score", quality_score)
                
                st.rerun()
                
            except Exception as e:
                logger.error(f"Optimization error: {str(e)}")
                error_handler = ErrorHandler()
                user_message = error_handler.handle_api_error(e, "during optimization")
                error_handler.log_error(e, context={"operation": "optimization"})
                
                progress_bar.progress(100)
                status_text.text("❌ Error occurred")
                st.error(f"❌ {user_message}")
                st.info("💡 Tip: Check your API key configuration and internet connection.")
    
    # Display results
    if st.session_state.optimization_results:
        results = st.session_state.optimization_results
        st.markdown("---")
        
        # Handle identity query responses
        if results.get("is_identity_query") and results.get("identity_response"):
            st.subheader("💬 Response from NextEleven AI")
            st.info("This appears to be an identity query. Here's how NextEleven AI responded:")
            st.markdown(f"**{results.get('identity_response')}**")
            st.markdown("---")
            st.info("💡 To optimize a prompt, enter a prompt that needs optimization in the text area above.")
            return
        
        # Quality score banner
        if results.get("quality_score"):
            score = results["quality_score"]
            score_class = "score-high" if score >= 80 else "score-medium" if score >= 60 else "score-low"
            st.markdown(
                f'<div class="score-badge {score_class}">Quality Score: {score}/100</div>',
                unsafe_allow_html=True
            )
            st.markdown("")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Optimized Prompt",
            "📊 Analysis",
            "📝 Sample Output",
            "🔍 Details",
            "📈 Evaluation"
        ])
        
        with tab1:
            st.subheader("Optimized Prompt")
            if results.get("optimized_prompt"):
                st.markdown(results["optimized_prompt"])
                st.code(results["optimized_prompt"], language="text")
            else:
                st.info("Optimized prompt not available")
        
        with tab2:
            st.subheader("Deconstruction")
            if results.get("deconstruction"):
                st.markdown(results["deconstruction"])
            
            st.markdown("---")
            st.subheader("Diagnosis")
            if results.get("diagnosis"):
                st.markdown(results["diagnosis"])
        
        with tab3:
            st.subheader("Sample Output")
            if results.get("sample_output"):
                st.markdown(results["sample_output"])
            else:
                st.info("Sample output not available")
        
        with tab4:
            st.subheader("Original Prompt")
            st.markdown(results.get("original_prompt", ""))
            
            st.markdown("---")
            st.subheader("Prompt Type")
            st.info(results.get("prompt_type", "N/A").capitalize())
        
        with tab5:
            st.subheader("Quality Evaluation")
            if results.get("evaluation"):
                st.markdown(results["evaluation"])
            else:
                st.info("Evaluation not available")
            
            if results.get("errors"):
                st.error("Errors encountered:")
                for error in results["errors"]:
                    st.error(f"- {error}")
        
        # History section (beta: show recent from session state)
        with st.sidebar:
            st.markdown("---")
            st.markdown("### Recent Optimizations")
            if "recent_optimizations" in st.session_state:
                for i, opt in enumerate(st.session_state.recent_optimizations[-5:], 1):
                    with st.expander(f"Optimization {i}"):
                        if opt.get("quality_score"):
                            st.text(f"Score: {opt['quality_score']}/100")
                        st.text(opt.get("original_prompt", "")[:100] + "...")
            else:
                st.info("No recent optimizations")


def show_analytics_page():
    """Display advanced analytics dashboard."""
    st.markdown('<div class="main-header">📊 Analytics Dashboard</div>', unsafe_allow_html=True)
    
    # Beta mode: Analytics available to all (shows aggregate or session data)
    user_id = st.session_state.user.id if st.session_state.user else None
    st.info("💡 Analytics shown for all optimizations (beta mode)")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Time Period", [7, 30, 90, 365], index=1)
    
    # Get analytics data
    analytics = Analytics()
    analytics_data = analytics.get_user_analytics(user_id, days)
    trends = analytics.get_quality_trends(user_id, days)
    top_prompts = analytics.get_top_prompts(user_id, 10)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Optimizations", analytics_data.get("total_optimizations", 0))
    with col2:
        st.metric("Avg Quality Score", f"{analytics_data.get('average_quality_score', 0)}/100")
    with col3:
        st.metric("Avg Processing Time", f"{analytics_data.get('average_processing_time', 0):.2f}s")
    with col4:
        st.metric("Total Tokens Used", analytics_data.get("total_tokens_used", 0))
    
    st.markdown("---")
    
    # Charts
    try:
        import plotly.express as px
        import pandas as pd
        
        # Quality trends chart
        if trends:
            df_trends = pd.DataFrame(trends)
            fig = px.line(df_trends, x='date', y='average_score', 
                         title='Quality Score Trends Over Time',
                         labels={'average_score': 'Average Quality Score', 'date': 'Date'})
            fig.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#121212', 
                            font_color='#FFFFFF')
            st.plotly_chart(fig, use_container_width=True)
        
        # Prompt type distribution
        if analytics_data.get("type_distribution"):
            type_data = analytics_data["type_distribution"]
            df_types = pd.DataFrame(list(type_data.items()), columns=['Type', 'Count'])
            fig = px.pie(df_types, values='Count', names='Type', 
                        title='Prompt Type Distribution')
            fig.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#121212', 
                            font_color='#FFFFFF')
            st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Install plotly and pandas for interactive charts: pip install plotly pandas")
    
    # Top prompts
    if top_prompts:
        st.subheader("🏆 Top Performing Prompts")
        for i, prompt in enumerate(top_prompts, 1):
            with st.expander(f"#{i} - Score: {prompt['quality_score']}/100"):
                st.text(f"Type: {prompt['prompt_type']}")
                st.text(f"Prompt: {prompt['original_prompt']}")


def show_batch_page():
    """Display batch optimization page."""
    st.markdown('<div class="main-header">📦 Batch Optimization</div>', unsafe_allow_html=True)
    
    st.info("💡 Upload multiple prompts to optimize them all at once.")
    
    # Beta mode: Available to all
    user_id = st.session_state.user.id if st.session_state.user else None
    
    # Batch input
    st.subheader("Enter Prompts")
    
    input_method = st.radio("Input Method", ["Manual Entry", "JSON Upload", "CSV Upload"])
    
    prompts = []
    
    if input_method == "Manual Entry":
        num_prompts = st.number_input("Number of Prompts", min_value=1, max_value=50, value=5)
        for i in range(num_prompts):
            with st.expander(f"Prompt {i+1}"):
                prompt_text = st.text_area("Prompt", key=f"prompt_{i}")
                prompt_type = st.selectbox("Type", [pt.value for pt in PromptType], key=f"type_{i}")
                if prompt_text:
                    prompts.append({"prompt": prompt_text, "type": prompt_type})
    
    elif input_method == "JSON Upload":
        uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                if isinstance(data, list):
                    prompts = data
                else:
                    st.error("JSON must be an array of prompt objects")
            except Exception as e:
                st.error(f"Error parsing JSON: {str(e)}")
    
    elif input_method == "CSV Upload":
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file:
            try:
                import pandas as pd
                df = pd.read_csv(uploaded_file)
                if "prompt" in df.columns:
                    prompts = [
                        {"prompt": row["prompt"], "type": row.get("type", "creative")}
                        for _, row in df.iterrows()
                    ]
                else:
                    st.error("CSV must have a 'prompt' column")
            except Exception as e:
                st.error(f"Error parsing CSV: {str(e)}")
    
    if st.button("🚀 Start Batch Optimization", type="primary", disabled=len(prompts) == 0):
        if len(prompts) == 0:
            st.warning("Please add at least one prompt")
        else:
            with st.spinner(f"Processing {len(prompts)} prompts..."):
                # Progress tracking for batch
                batch_progress = st.progress(0)
                batch_status = st.empty()
                
                batch_status.text(f"🚀 Processing {len(prompts)} prompts...")
                batch_progress.progress(0)
                
                batch_optimizer = BatchOptimizer()
                
                with performance_tracker("batch_optimization"):
                    job = batch_optimizer.create_and_process_batch(
                        prompts,
                        user_id
                    )
                
                if job:
                    batch_progress.progress(100)
                    batch_status.text("✅ Batch job created!")
                    st.success(f"✅ Batch job created! Job ID: {job.id}")
                    st.session_state.batch_job_id = job.id
                    
                    # Track metrics
                    metrics = get_metrics()
                    metrics.increment("batch_jobs.created")
                    metrics.gauge("batch_jobs.prompt_count", len(prompts))
                    
                    st.rerun()
                else:
                    batch_status.text("❌ Failed to create batch job")
                    st.error("❌ Failed to create batch job. Please try again.")

    # Show batch job results
    if "batch_job_id" in st.session_state:
        st.markdown("---")
        st.subheader("Batch Job Results")
        from database import BatchJob
        db_session = db.get_session()
        job = db_session.query(BatchJob).filter(
            BatchJob.id == st.session_state.batch_job_id
        ).first()
        db_session.close()
        
        if job:
            st.write(f"Status: {job.status}")
            st.write(f"Completed: {job.completed_prompts}/{job.total_prompts}")
            
            if job.results_json:
                results = json.loads(job.results_json)
                for i, result in enumerate(results, 1):
                    with st.expander(f"Result {i}"):
                        if result.get("success"):
                            st.success("✅ Success")
                            st.text_area("Optimized Prompt", result.get("optimized_prompt", ""), height=100)
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")


def show_ab_testing_page():
    """Display A/B testing page."""
    st.markdown('<div class="main-header">🧪 A/B Testing</div>', unsafe_allow_html=True)
    
    st.info("💡 Compare two prompt variants to see which performs better.")
    
    # Beta mode: Available to all
    
    tab1, tab2 = st.tabs(["Create Test", "View Results"])
    
    with tab1:
        st.subheader("Create New A/B Test")
        
        test_name = st.text_input("Test Name")
        original_prompt = st.text_area("Original Prompt", height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            variant_a = st.text_area("Variant A (Optional - will be generated if empty)", height=100)
        with col2:
            variant_b = st.text_area("Variant B (Optional - will be generated if empty)", height=100)
        
        if st.button("Create A/B Test", type="primary"):
            if test_name and original_prompt:
                ab_testing = ABTesting()
                user_id = st.session_state.user.id if st.session_state.user else None
                ab_test = ab_testing.create_test(
                    user_id,
                    test_name,
                    original_prompt,
                    variant_a if variant_a else None,
                    variant_b if variant_b else None
                )
                
                if ab_test:
                    st.success(f"✅ A/B test created! Test ID: {ab_test.id}")
                    st.session_state.ab_test_id = ab_test.id
                    st.rerun()
            else:
                st.warning("Please fill in test name and original prompt")
    
    with tab2:
        st.subheader("Test Results")
        # Display existing tests and their results (beta: show all or session-based)
        user_id = st.session_state.user.id if st.session_state.user else None
        from database import ABTest
        db_session = db.get_session()
        if user_id:
            tests = db_session.query(ABTest).filter(
                ABTest.user_id == user_id
            ).order_by(ABTest.created_at.desc()).limit(10).all()
        else:
            # Beta: Show recent tests (last 10)
            tests = db_session.query(ABTest).order_by(
                ABTest.created_at.desc()
            ).limit(10).all()
        db_session.close()

        for test in tests:
            with st.expander(f"{test.name} - {test.status}"):
                results = ABTesting().get_test_results(test.id)
                if results:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Variant A Score", f"{results['variant_a']['score']:.2f}")
                        st.metric("Variant A Responses", results['variant_a']['responses'])
                    with col2:
                        st.metric("Variant B Score", f"{results['variant_b']['score']:.2f}")
                        st.metric("Variant B Responses", results['variant_b']['responses'])

                    if results.get("winner"):
                        st.success(f"🏆 Winner: Variant {results['winner'].upper()}")


def show_export_page():
    """Display export page."""
    st.markdown('<div class="main-header">📥 Export Results</div>', unsafe_allow_html=True)
    
    if not st.session_state.optimization_results:
        st.info("💡 Optimize a prompt first, then export the results here.")
        return
    
    results = st.session_state.optimization_results
    
    st.subheader("Export Format")
    export_format = st.selectbox("Select Format", ["JSON", "Markdown", "PDF"])
    
    if st.button("📥 Export", type="primary"):
        try:
            exported = export_results(results, export_format.lower())
            
            if export_format == "PDF":
                st.download_button(
                    label="Download PDF",
                    data=exported.read(),
                    file_name=f"optimization_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.download_button(
                    label=f"Download {export_format}",
                    data=exported,
                    file_name=f"optimization_{time.strftime('%Y%m%d_%H%M%S')}.{export_format.lower()}",
                    mime="application/json" if export_format == "JSON" else "text/markdown"
                )
            
            # Log export event (optional in beta)
            try:
                user_id = st.session_state.user.id if st.session_state.user else None
                Analytics().log_event(
                    user_id,
                    "export",
                    {"format": export_format.lower()}
                )
            except Exception:
                pass  # Optional in beta mode
        except Exception as e:
            st.error(f"Error exporting: {str(e)}")


def show_settings_page():
    """Display settings page."""
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
    
    # Beta mode: Settings available to all
    user = st.session_state.user if st.session_state.user else None
    
    st.subheader("API Access")
    st.info("💡 Generate an API key for programmatic access to the optimizer.")
    
    if user and user.api_key:
        st.text_input("Your API Key", value=user.api_key, type="password", disabled=True)
        if st.button("Regenerate API Key"):
            new_key = db.generate_api_key(user.id)
            if new_key:
                st.success("✅ New API key generated!")
                st.rerun()
    elif user:
        if st.button("Generate API Key"):
            api_key = db.generate_api_key(user.id)
            if api_key:
                st.success("✅ API key generated!")
                st.rerun()
    else:
        st.info("💡 API access is available. Create an account (optional) to generate a persistent API key, or use the API without authentication for beta testing.")
    
    st.markdown("---")
    st.subheader("Integrations")
    
    tab1, tab2, tab3 = st.tabs(["Slack", "Discord", "Notion"])
    
    with tab1:
        st.info("Configure Slack integration to optimize prompts via slash commands.")
        st.text_input("Slack Webhook URL", type="password")
        if st.button("Save Slack Settings"):
            st.success("✅ Settings saved!")
    
    with tab2:
        st.info("Configure Discord integration to optimize prompts via bot commands.")
        st.text_input("Discord Webhook URL", type="password")
        if st.button("Save Discord Settings"):
            st.success("✅ Settings saved!")
    
    with tab3:
        st.info("Configure Notion integration to optimize prompts from Notion pages.")
        api_key = st.text_input("Notion API Key", type="password")
        if st.button("Save Notion Settings"):
            st.success("✅ Settings saved!")


def show_agent_config_page():
    """Display agent configuration page."""
    st.markdown('<div class="main-header">🤖 Agent Configuration</div>', unsafe_allow_html=True)
    
    # Beta mode: Available to all (create anonymous configs if needed)
    
    st.info("💡 Customize agent behavior, temperature, and other parameters.")
    
    # Beta mode: Allow configs for anonymous users (use None as user_id)
    user_id = st.session_state.user.id if st.session_state.user else None
    if user_id:
        configs = AgentConfigManager.get_user_configs(user_id)
    else:
        configs = []
        st.info("💡 Create configurations will be saved for this session.")
    
    if configs:
        st.subheader("Your Configurations")
        for config in configs:
            with st.expander(f"{config['name']} {'(Default)' if config['is_default'] else ''}"):
                st.json(config['config'])
    
    st.markdown("---")
    st.subheader("Create New Configuration")
    
    config_name = st.text_input("Configuration Name")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.number_input("Max Tokens", min_value=100, max_value=4000, value=2000)
    use_parallel = st.checkbox("Use Parallel Execution", value=True)
    
    if st.button("Create Configuration", type="primary"):
        if config_name:
            config = {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "use_parallel_execution": use_parallel
            }
            # Beta mode: Allow configs for anonymous users
            user_id = st.session_state.user.id if st.session_state.user else None
            if user_id:
                agent_config = AgentConfigManager.create_config(
                    user_id,
                    config_name,
                    config
                )
            else:
                # Store in session state for anonymous users
                if "agent_configs" not in st.session_state:
                    st.session_state.agent_configs = []
                st.session_state.agent_configs.append({
                    "name": config_name,
                    "config": config
                })
                st.success("✅ Configuration created for this session!")
                st.rerun()
                return
            if agent_config:
                st.success("✅ Configuration created!")
                st.rerun()
        else:
            st.warning("Please enter a configuration name")


def show_footer():
    """Display footer with branding and legal links."""
    st.markdown("""
        <div class="footer">
            Brought to you by <a href="https://nextelevenstudio.online" target="_blank">NextEleven</a> | 
            <a href="mailto:info@mothership-ai.com">info@mothership-ai.com</a> | 
            <a href="?page=terms" target="_self">Terms of Service</a> | 
            <a href="?page=privacy" target="_self">Privacy Policy</a> | 
            Built by S. McDonnell
        </div>
    """, unsafe_allow_html=True)


def show_terms_page():
    """Display Terms of Service page."""
    try:
        with open("TERMS_OF_SERVICE.md", "r", encoding="utf-8") as f:
            terms_content = f.read()
        st.markdown(terms_content)
    except FileNotFoundError:
        st.error("Terms of Service document not found. Please ensure TERMS_OF_SERVICE.md exists.")
    except Exception as e:
        st.error(f"Error loading Terms of Service: {str(e)}")


def show_privacy_page():
    """Display Privacy Policy page."""
    try:
        with open("PRIVACY_POLICY.md", "r", encoding="utf-8") as f:
            privacy_content = f.read()
        st.markdown(privacy_content)
    except FileNotFoundError:
        st.error("Privacy Policy document not found. Please ensure PRIVACY_POLICY.md exists.")
    except Exception as e:
        st.error(f"Error loading Privacy Policy: {str(e)}")


def main():
    """Main application entry point."""
    init_session_state()
    
    # Check for legal page requests (via query params or URL)
    query_params = st.query_params
    page = query_params.get("page", None)
    
    if page == "terms":
        st.title("Terms of Service")
        show_terms_page()
        show_footer()
        return
    elif page == "privacy":
        st.title("Privacy Policy")
        show_privacy_page()
        show_footer()
        return
    
    # Check IP-based rate limit (for beta/public access)
    client_ip = get_ip()
    if client_ip != 'localhost' and client_ip != 'unknown':
        if not check_ip_rate_limit(client_ip, max_requests=5, window_hours=24):
            st.error("⚠️ Rate limit exceeded: 5 requests per 24 hours per IP. Try again later.")
            show_footer()
            st.stop()
    
    # Check for required environment variables
    try:
        if not settings.xai_api_key or settings.xai_api_key == "your_xai_api_key_here":
            st.error("❌ API key not configured. Please set XAI_API_KEY in your .env file.")
            st.info("See env.example for configuration details.")
            show_footer()
            st.stop()
    except Exception as e:
        st.error(f"❌ Configuration error: {str(e)}")
        show_footer()
        st.stop()
    
    # Beta mode: Always show main app (no authentication required)
    # Skip login page entirely
    show_main_app()
    
    # Always show footer
    show_footer()


if __name__ == "__main__":
    main()
