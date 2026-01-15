#!/bin/bash
# start.sh - One-command app start

source venv/bin/activate

# Check if .env exists and has API key
if [ ! -f ".env" ] || ! grep -q "XAI_API_KEY=xai-" .env; then
    echo "ERROR: Please set XAI_API_KEY in .env file"
    exit 1
fi

echo "Starting NextEleven AI Prompt Optimizer..."
streamlit run main.py --server.port=8501 --server.headless=true