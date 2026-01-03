"""
Main Streamlit application for AI-Powered Prompt Optimizer SaaS.
Implements the full UI with authentication, optimization workflow, and evaluation dashboard.
"""
import streamlit as st
import logging
import sqlite3
import time
from datetime import date, datetime, timedelta
from typing import Optional
from agents import OrchestratorAgent, PromptType
from database import db, User
from config import settings
from input_validation import (
    sanitize_and_validate_prompt,
    validate_prompt_type,
    validate_username,
    validate_email
)

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
st.markdown("""
    <style>
    /* Base dark mode */
    [data-testid="stAppViewContainer"] {
        background-color: #121212 !important;
        color: #FFFFFF !important;
    }
    
    /* Main container background */
    .main .block-container {
        background-color: #121212 !important;
        padding-top: 2rem;
        padding-bottom: 5rem; /* Space for footer */
    }
    
    /* Text and headers */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, div[data-baseweb="select"] {
        color: #FFFFFF !important;
    }
    
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00BFA5 !important;
        margin-bottom: 1rem;
    }
    
    /* Teal accents for buttons */
    .stButton > button {
        background-color: #00BFA5 !important;
        color: #121212 !important;
        border: 1px solid #00BFA5 !important;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #008F7A !important;
        border-color: #008F7A !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #00BFA5 !important;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #00BFA5 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #FFFFFF !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1E1E1E !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #FFFFFF !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
    }
    
    /* Info boxes */
    .stAlert {
        background-color: #1E1E1E !important;
    }
    
    /* Score badges */
    .score-badge {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .score-high {
        background-color: #00BFA5 !important;
        color: #121212 !important;
    }
    .score-medium {
        background-color: #008F7A !important;
        color: #FFFFFF !important;
    }
    .score-low {
        background-color: #4A5568 !important;
        color: #FFFFFF !important;
    }
    
    /* Footer styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #121212;
        color: #FFFFFF;
        text-align: center;
        padding: 10px;
        border-top: 1px solid #00BFA5;
        font-size: 12px;
        z-index: 999;
    }
    .footer a {
        color: #00BFA5;
        text-decoration: none;
    }
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #1E1E1E !important;
    }
    .stError {
        background-color: #1E1E1E !important;
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
    user_id = st.session_state.user.id if st.session_state.user else None
    return db.check_usage_limit(user_id)


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
    # Sidebar
    with st.sidebar:
        st.title("🚀 Prompt Optimizer")
        
        if st.session_state.user:
            st.markdown(f"**Welcome, {st.session_state.user.username}!**")
            if st.session_state.user.is_premium:
                st.success("⭐ Premium User")
            else:
                st.info("💡 Free Tier")
                st.markdown(f"Daily limit: {settings.free_tier_daily_limit} optimizations")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool uses a multi-agent system to optimize your prompts using Lyra's 4-D methodology:
        - **Deconstruct**: Break down your prompt
        - **Diagnose**: Identify issues
        - **Design**: Create optimized version
        - **Deliver**: Generate sample output
        """)
    
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
    
    user_prompt = st.text_area(
        "Your Prompt",
        height=150,
        placeholder="Enter your prompt here... For example: 'Write a blog post about AI'",
        help="Enter the prompt you want to optimize"
    )
    
    # Check usage limit
    if not check_usage_limit():
        st.error("❌ You've reached your daily usage limit. Upgrade to premium for unlimited access!")
        st.stop()
    
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
            
            with st.spinner("🔄 Optimizing with NextEleven AI... This may take a moment."):
                try:
                    orchestrator = OrchestratorAgent()
                    
                    # Check if this is an identity query (use sanitized prompt)
                    identity_response = orchestrator.handle_identity_query(sanitized_prompt)
                    if identity_response:
                        # Identity queries don't count toward usage limits
                        st.session_state.optimization_results = {
                            "original_prompt": sanitized_prompt,  # Store sanitized version
                            "prompt_type": prompt_type,
                            "identity_response": identity_response,
                            "is_identity_query": True
                        }
                        st.success("✅ Response from NextEleven AI!")
                        st.rerun()
                    
                    # Regular optimization workflow (use sanitized prompt and validated type)
                    results = orchestrator.optimize_prompt(
                        sanitized_prompt,
                        prompt_type_enum
                    )
                    
                    # Increment usage (only for actual optimizations, not identity queries)
                    user_id = st.session_state.user.id if st.session_state.user else None
                    db.increment_usage(user_id)
                    
                    # Save session (use sanitized prompt)
                    optimized_prompt_text = results.get("optimized_prompt", "")[:1000]  # Limit length
                    sample_output = results.get("sample_output", "")[:2000]
                    quality_score = results.get("quality_score")
                    
                    db.save_session(
                        user_id=user_id,
                        original_prompt=sanitized_prompt,  # Store sanitized version
                        prompt_type=prompt_type,
                        optimized_prompt=optimized_prompt_text,
                        sample_output=sample_output,
                        quality_score=quality_score
                    )
                    
                    st.session_state.optimization_results = results
                    st.success("✅ Optimization complete!")
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Optimization error: {str(e)}")
                    st.error(f"❌ Error during optimization: {str(e)}")
                    st.info("Please check your API key configuration and try again.")
    
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
        
        # History section (for logged-in users)
        if st.session_state.user:
            with st.sidebar:
                st.markdown("---")
                st.markdown("### Recent Sessions")
                sessions = db.get_user_sessions(st.session_state.user.id, limit=5)
                if sessions:
                    for session in sessions:
                        with st.expander(f"Session {session.id} - {session.created_at.strftime('%Y-%m-%d')}"):
                            st.text(f"Type: {session.prompt_type}")
                            if session.quality_score:
                                st.text(f"Score: {session.quality_score}/100")
                            st.text(session.original_prompt[:100] + "...")
                else:
                    st.info("No previous sessions")


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
    
    # Beta mode: Always show main app (authentication bypassed)
    show_main_app()
    
    # Always show footer
    show_footer()


if __name__ == "__main__":
    main()
