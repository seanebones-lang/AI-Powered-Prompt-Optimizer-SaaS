# Streamlit Cloud Setup Guide

## Setting Environment Variables (Secrets)

Streamlit Cloud uses a "Secrets" system to store environment variables securely.

### Steps to Add Secrets:

1. **Go to your Streamlit Cloud app dashboard**
   - Click "Manage app" in your deployed app
   - Or go to: https://share.streamlit.io/

2. **Open Secrets Configuration**
   - Click on the "⚙️ Settings" button (or "Secrets" in the menu)
   - Look for "Secrets" section

3. **Add the following secrets:**

```toml
XAI_API_KEY = "your_actual_xai_api_key_here"
SECRET_KEY = "your_secret_key_for_session_management_here"
XAI_API_BASE = "https://api.x.ai/v1"
XAI_MODEL = "grok-4-1-fast-reasoning"
DATABASE_URL = "sqlite:///prompt_optimizer.db"
FREE_TIER_DAILY_LIMIT = "5"
PAID_TIER_DAILY_LIMIT = "1000"
ENABLE_COLLECTIONS = "false"
```

### Required Secrets:

**Minimum required (must have):**
- `XAI_API_KEY` - Your xAI Grok API key (get from https://x.ai/api)
- `SECRET_KEY` - A random secret string for session management (generate with: `openssl rand -hex 32`)

**Optional (will use defaults if not set):**
- `XAI_API_BASE` - Default: `https://api.x.ai/v1`
- `XAI_MODEL` - Default: `grok-4-1-fast-reasoning` (use hyphens, NOT dots)
- `DATABASE_URL` - Default: `sqlite:///prompt_optimizer.db`
- `FREE_TIER_DAILY_LIMIT` - Default: `5`
- `PAID_TIER_DAILY_LIMIT` - Default: `1000`
- `ENABLE_COLLECTIONS` - Default: `false`

### Generating a SECRET_KEY:

Run this command to generate a secure secret key:

```bash
openssl rand -hex 32
```

Or use Python:
```python
import secrets
print(secrets.token_hex(32))
```

### After Adding Secrets:

1. Save the secrets
2. The app will automatically redeploy
3. Wait for the deployment to complete
4. Your app should now work!

### Important Notes:

- Secrets are encrypted and secure
- Never commit secrets to GitHub
- The `.env` file is for local development only
- Streamlit Cloud automatically makes secrets available as environment variables
- Changes to secrets trigger automatic redeployment

### Troubleshooting:

**Error: "Missing required environment variables"**
- Make sure you've added `XAI_API_KEY` and `SECRET_KEY` to Secrets
- Check for typos in secret names (case-sensitive in some contexts)
- Wait for redeployment to complete

**Error: "API call failed" or "NoneType object is not subscriptable"**
- Verify your `XAI_API_KEY` is correct and active at https://console.x.ai/api-keys
- **Test your API key locally** using the test script:
  ```bash
  python3 test_api_key.py
  ```
- **Or test with curl:**
  ```bash
  curl https://api.x.ai/v1/chat/completions \
    -H "Authorization: Bearer YOUR_XAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model": "grok-4-1-fast-reasoning", "messages": [{"role": "user", "content": "Test"}]}'
  ```
  Expected: 200 OK response. If 400/401, your key is invalid.

**Error: "Invalid model" or "Model not found"**
- Ensure `XAI_MODEL` in secrets is exactly: `grok-4-1-fast-reasoning` (with hyphens, no dots)
- Alternative: `grok-4-1-fast-non-reasoning` for faster responses
- Do NOT use: `grok-4.1-fast` (old format with dots - invalid)

**Common Issues:**
- **Invalid/Expired API Key**: Regenerate at https://console.x.ai/api-keys
- **Model Name Mismatch**: Must be `grok-4-1-fast-reasoning` (hyphens, not dots)
- **Network/Quota**: Check xAI console for usage limits (free tier: $25/month credits)
- **Rate Limits**: 4M tokens/minute limit - if exceeded, wait and retry