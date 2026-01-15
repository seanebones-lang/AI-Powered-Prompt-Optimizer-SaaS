#!/bin/bash
# setup_local.sh - One-command local setup

set -e  # Exit on any error

echo "=== NextEleven AI Prompt Optimizer - Local Setup ==="

# 1. Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 2. Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp env.example .env
    echo ""
    echo ">>> IMPORTANT: Edit .env and add your XAI_API_KEY <<<"
    echo ""
fi

# 4. Initialize database
echo "Initializing database..."
python -c "from database import db; print('Database ready!')"

# 5. Run migrations if alembic is configured
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

echo ""
echo "=== Setup Complete! ==="
echo "To start the app, run: ./start.sh"