#!/bin/bash
# Monitor deployment status
# Checks git status and validates deployment readiness

echo "🔍 Monitoring Deployment Status"
echo "================================"
echo ""

# Check git status
echo "📋 Git Status:"
git status --short
echo ""

# Check recent commits
echo "📦 Recent Commits:"
git log --oneline -5
echo ""

# Validate code
echo "✅ Code Validation:"
python3 validate_deployment.py
echo ""

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
echo "🌿 Current Branch: $CURRENT_BRANCH"
if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "  ✅ On main branch (correct for deployment)"
else
    echo "  ⚠️  Not on main branch"
fi
echo ""

# Check remote status
echo "🔗 Remote Status:"
git fetch origin 2>/dev/null
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "none")

if [ "$REMOTE" = "none" ]; then
    echo "  ⚠️  No remote tracking branch"
elif [ "$LOCAL" = "$REMOTE" ]; then
    echo "  ✅ Local and remote are in sync"
else
    echo "  ⚠️  Local and remote differ"
    echo "  Local:  $LOCAL"
    echo "  Remote: $REMOTE"
fi
echo ""

echo "✅ Deployment monitoring complete!"
echo ""
echo "Next: Check Streamlit Cloud dashboard for deployment status"
echo "URL: https://nextelevenprompt.streamlit.app/"
