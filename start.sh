#!/bin/bash
# Railway startup script - handles $PORT environment variable
set -e

# Use Railway's PORT if set, otherwise default to 8501
PORT=${PORT:-8501}

echo "Starting Streamlit on port $PORT"

streamlit run main.py \
  --server.port=$PORT \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
