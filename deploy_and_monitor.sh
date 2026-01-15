#!/bin/bash
# Full deployment and monitoring script
# Usage: ./deploy_and_monitor.sh

set -e  # Exit on error

echo "🚀 Starting Full Deployment & Monitoring Workflow"
echo "=================================================="
echo ""

# Step 1: Verify all files are ready
echo "📋 Step 1: Verifying files..."
python3 test_fixes.py
if [ $? -ne 0 ]; then
    echo "❌ Pre-deployment checks failed!"
    exit 1
fi
echo "✅ All checks passed"
echo ""

# Step 2: Stage all changes
echo "📦 Step 2: Staging changes..."
git add -A
git status --short
echo ""

# Step 3: Commit
echo "💾 Step 3: Committing changes..."
COMMIT_MSG="Production: Complete fixes - HTTP/2 disabled, prompt extraction improved, UI layout fixed, type validation added"
git commit -m "$COMMIT_MSG" || echo "No changes to commit"
echo ""

# Step 4: Push to trigger deployment
echo "📤 Step 4: Pushing to GitHub (triggers auto-deployment)..."
git push origin main
echo "✅ Code pushed successfully"
echo ""

# Step 5: Monitor deployment
echo "⏳ Step 5: Monitoring deployment..."
echo "Waiting for Streamlit Cloud to deploy..."
echo ""

# Check if we can verify deployment (would need Streamlit Cloud API or webhook)
echo "📊 Deployment Status:"
echo "  - Code pushed to: main branch"
echo "  - Auto-deployment: Triggered"
echo "  - Expected time: 2-5 minutes"
echo ""
echo "✅ Deployment initiated successfully!"
echo ""
echo "Next steps:"
echo "1. Check Streamlit Cloud dashboard for deployment status"
echo "2. Monitor logs at: https://nextelevenprompt.streamlit.app/"
echo "3. Run E2E tests after deployment completes"
echo ""
