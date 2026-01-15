#!/bin/bash
# deploy.sh - One-command Railway deployment

set -e

echo "=== Deploying to Railway ==="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway..."
    railway login
fi

# Deploy
echo "Pushing to Railway..."
railway up --detach

echo ""
echo "=== Deployment Started! ==="
echo "Check status: railway logs"
echo "Open app: railway open"