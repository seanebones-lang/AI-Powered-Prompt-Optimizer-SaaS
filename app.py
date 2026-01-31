# This file exists to prevent Railway from auto-detecting FastAPI
# Railway should use Streamlit instead as configured in railway.toml

# If Railway tries to run this as a FastAPI app, it will fail gracefully
# and fall back to the Streamlit configuration

import sys
sys.exit("This is not a FastAPI application. Please use Streamlit.")
