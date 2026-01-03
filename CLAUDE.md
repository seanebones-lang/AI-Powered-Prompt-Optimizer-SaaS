# AI-Powered Prompt Optimizer - Claude Code Instructions

## Project Overview
Multi-agent system implementing Lyra's 4-D methodology (Deconstruct, Diagnose, Design, Deliver)
for prompt optimization using xAI Grok API (grok-4-1-fast-reasoning model).

**Tech Stack:**
- Python 3.11+, Streamlit 1.52.0, SQLAlchemy 2.0
- xAI Grok API with agent tools support
- Pydantic v2 for validation

## Bash Commands
```bash
# Start the application
streamlit run main.py

# Run all tests
TESTING=1 pytest tests/ -v

# Run quick unit tests only
TESTING=1 pytest tests/unit -v -m "not slow"

# Run with coverage
TESTING=1 pytest tests/ --cov=. --cov-report=term-missing

# Lint and auto-fix
ruff check . --fix

# Format code
ruff format .

# Type checking
mypy --strict *.py
```

## Code Style
- Use Python 3.11+ features (match/case, type hints, dataclasses)
- Follow Google-style docstrings
- Use async/await for API calls where appropriate
- Keep functions under 50 lines
- Use Pydantic models for data validation
- Apply `@functools.cache` for expensive computations

## Architecture Rules
- **NEVER** modify the 4-D agent workflow order (Deconstruct -> Diagnose -> Design -> Deliver)
- All API calls go through `api_utils.py`
- Database operations use SQLAlchemy ORM only (no raw SQL)
- Streamlit session state for UI persistence
- Keep `agents.py` modular - one class per agent

## Testing Requirements
- Write tests BEFORE implementation (TDD)
- Mock all xAI Grok API calls in tests
- Use pytest fixtures from `tests/conftest.py`
- Minimum 85% coverage target on core modules
- Set environment variables: `TESTING=1 XAI_API_KEY=test-key SECRET_KEY=test-secret`

## Critical Files
| File | Purpose |
|------|---------|
| `main.py` | Streamlit entry point (DO NOT add business logic here) |
| `agents.py` | Multi-agent orchestration (core of 4-D system) |
| `api_utils.py` | xAI Grok API integration with retry logic |
| `database.py` | SQLAlchemy models and operations |
| `config.py` | Pydantic settings (secrets via .env) |
| `input_validation.py` | Input sanitization and validation |
| `error_handling.py` | Retry logic and error recovery |

## Security Rules
- **NEVER** log or expose XAI_API_KEY
- Always use parameterized queries (even with ORM)
- Validate and sanitize all user inputs via `input_validation.py`
- Test with mocks, not live API calls
- Check rate limits before API calls

## Shortcuts

### QPLAN
Analyze similar code patterns and determine if plan is consistent with architecture.
Identify minimal changes required and list files to modify.

### QCODE
Implement the approved plan, run tests, format with ruff, and verify with mypy.

### QCHECK
Review changes as a skeptical senior engineer. Verify CLAUDE.md rules and security.

### QTEST
Generate comprehensive tests including edge cases. Mock external dependencies.

### QFIX
Analyze error, identify root cause, propose minimal fix with explanation.

## Agent System Quick Reference

```python
# OrchestratorAgent coordinates the 4-D workflow
from agents import OrchestratorAgent, PromptType

orchestrator = OrchestratorAgent()
results = orchestrator.optimize_prompt(
    prompt="Write about AI",
    prompt_type=PromptType.CREATIVE
)

# Results contain: deconstruction, diagnosis, optimized_prompt,
# sample_output, evaluation, quality_score
```

## Environment Variables Required
```
XAI_API_KEY=your_xai_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///prompt_optimizer.db (optional)
ENABLE_COLLECTIONS=false (optional, for RAG)
```

## Common Patterns

### Adding a new feature
1. Write tests in `tests/test_*.py`
2. Implement in appropriate module
3. Add UI in `main.py` if needed
4. Run full test suite
5. Update docstrings

### Fixing a bug
1. Write failing test that reproduces bug
2. Implement fix
3. Verify test passes
4. Check for regressions

### Modifying agents
1. Update agent class in `agents.py`
2. Maintain BaseAgent pattern
3. Update orchestrator if workflow changes
4. Add/update tests in `tests/test_agents.py`

## Git Commit Conventions
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `style:` Formatting
- `chore:` Maintenance
