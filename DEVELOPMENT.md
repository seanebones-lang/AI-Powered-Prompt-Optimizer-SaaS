# Development Guide - AI-Powered Prompt Optimizer SaaS

Quick reference guide for developers working on the project.

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd AI-Powered-Prompt-Optimizer-SaaS

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env and add your XAI_API_KEY

# Run the application
streamlit run main.py
```

## Project Structure

```
AI-Powered-Prompt-Optimizer-SaaS/
├── main.py              # Streamlit application entry point
├── agents.py            # Multi-agent system (Orchestrator + specialists)
├── api_utils.py         # xAI Grok API integration with persona
├── database.py          # Database models and utilities
├── config.py            # Configuration management
├── evaluation.py        # Evaluation and scoring utilities
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
├── setup.sh            # Setup script
├── run.py              # Runner script
├── README.md           # Main documentation
├── ROADMAP.md          # Full project roadmap
├── TASKS.md            # Task tracking
└── DEVELOPMENT.md      # This file
```

## Key Components

### 1. Multi-Agent System (`agents.py`)

The system follows Lyra's 4-D methodology:
- **DeconstructorAgent**: Breaks down vague prompts
- **DiagnoserAgent**: Identifies issues and weaknesses
- **DesignerAgent**: Creates optimized prompts
- **EvaluatorAgent**: Scores prompt quality
- **OrchestratorAgent**: Coordinates the workflow

### 2. API Integration (`api_utils.py`)

- Wraps xAI Grok API calls
- Enforces "NextEleven AI" persona via system prompts
- Handles identity queries
- Sanitizes outputs to maintain persona

### 3. Database (`database.py`)

- User authentication and management
- Session tracking
- Usage limit enforcement (freemium model)

### 4. UI (`main.py`)

- Streamlit-based web interface
- Dark mode with teal/white theme
- Rate limiting (IP-based for beta)
- Footer with NextEleven branding

## Environment Variables

Required variables in `.env`:
```env
XAI_API_KEY=your_xai_api_key_here
XAI_API_BASE=https://api.x.ai/v1
XAI_MODEL=grok-4.1-fast
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///prompt_optimizer.db
FREE_TIER_DAILY_LIMIT=5
PAID_TIER_DAILY_LIMIT=1000
```

## Development Workflow

1. **Feature Development**
   - Create feature branch: `git checkout -b feature/feature-name`
   - Make changes
   - Test locally
   - Commit with clear messages
   - Push and create PR

2. **Testing**
   - Run unit tests: `pytest tests/`
   - Test locally with: `streamlit run main.py`
   - Test identity queries: "Who are you?"
   - Test rate limiting

3. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Add docstrings to functions
   - Comment complex logic

## Common Tasks

### Adding a New Agent

1. Create agent class in `agents.py`:
```python
class NewAgent:
    def __init__(self):
        self.name = "NewAgent"
        self.role = "Description"
    
    def process(self, input_data, prompt_type) -> AgentOutput:
        # Implementation
        pass
```

2. Add to OrchestratorAgent in `agents.py`
3. Update UI if needed in `main.py`

### Modifying API Calls

Edit `api_utils.py`:
- Change system prompts: Modify `BASE_PERSONA_PROMPT`
- Adjust parameters: Edit `generate_completion()` defaults
- Add new methods: Follow existing patterns

### Database Changes

1. Modify models in `database.py`
2. Create migration script (if needed)
3. Test with sample data

## Testing Identity Persona

To verify "NextEleven AI" persona is working:

```python
# Test in Python shell
from api_utils import grok_api

response = grok_api.handle_identity_query("Who are you?")
print(response)
# Should contain "NextEleven AI" or "Eleven", NOT "Grok" or "xAI"
```

Or test in the UI by entering prompts like:
- "Who are you?"
- "Who built you?"
- "What is your name?"

## Debugging

### Common Issues

1. **API Key Error**
   - Check `.env` file exists
   - Verify `XAI_API_KEY` is set correctly
   - Ensure no extra spaces or quotes

2. **Database Errors**
   - Delete `prompt_optimizer.db` to reset
   - Check SQLite file permissions
   - Verify database URL in config

3. **Rate Limiting Issues**
   - Check `rate_limit.db` exists
   - For testing, delete the file to reset limits
   - Verify IP detection logic

4. **Persona Not Working**
   - Check `BASE_PERSONA_PROMPT` in `api_utils.py`
   - Verify `enforce_persona=True` in API calls
   - Test content sanitization

### Logging

Logs are configured in `main.py`:
```python
logging.basicConfig(level=logging.INFO)
```

View logs in terminal when running Streamlit.

## Performance Optimization

1. **API Caching**
   - Use `@st.cache_data` for API responses
   - Cache prompt templates
   - Implement request deduplication

2. **Database Optimization**
   - Index frequently queried fields
   - Clean up old sessions periodically
   - Use connection pooling

3. **Token Usage**
   - Minimize system prompt length where possible
   - Use streaming for long responses
   - Optimize prompt extraction logic

## Deployment Checklist

Before deploying:
- [ ] All environment variables set
- [ ] API key configured
- [ ] Database migrations complete
- [ ] Rate limiting tested
- [ ] Identity persona verified
- [ ] Error handling tested
- [ ] Logging configured
- [ ] Security audit complete

## Resources

- [xAI API Docs](https://x.ai/api)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Project Roadmap](ROADMAP.md)
- [Task Tracking](TASKS.md)

## Getting Help

- Check `ROADMAP.md` for project status
- Review `TASKS.md` for current priorities
- Check existing code for patterns
- Review Streamlit and xAI documentation

---

**Last Updated:** December 2025
