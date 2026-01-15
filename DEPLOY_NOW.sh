#!/bin/bash
# Quick deployment script
# Usage: ./DEPLOY_NOW.sh

echo "🚀 Starting Deployment Process..."
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Show current status
echo "📋 Current changes:"
git status --short
echo ""

# Ask for confirmation
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Stage critical files
echo "📦 Staging files..."
git add api_utils.py enterprise_integration.py main.py

# Commit
echo "💾 Committing changes..."
git commit -m "Production: Fix AttributeError, update to grok-4-1-fast-reasoning, add input validation and structured logging"

# Push
echo "📤 Pushing to remote..."
git push origin main

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📝 Next steps:"
echo "1. Verify secrets are configured in your deployment platform"
echo "2. Monitor deployment logs"
echo "3. Test the application after deployment completes"
echo ""
echo "Required secrets:"
echo "  - XAI_API_KEY"
echo "  - SECRET_KEY"
echo "  - XAI_MODEL=grok-4-1-fast-reasoning (optional, already default)"
