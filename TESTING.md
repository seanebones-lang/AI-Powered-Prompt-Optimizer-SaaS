# Testing Guide

## Overview

This document describes the comprehensive test suite for the AI-Powered Prompt Optimizer SaaS.

## Test Structure

```
tests/
├── __init__.py
├── test_config.py          # Configuration tests
├── test_database.py        # Database operations tests
├── test_agents.py          # Multi-agent system tests
├── test_api_utils.py       # API integration tests
├── test_collections.py     # Collections API tests
├── test_evaluation.py      # Evaluation utilities tests
└── test_integration.py     # End-to-end integration tests
```

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up test environment:
```bash
export TESTING=1
export XAI_API_KEY=test_key
export SECRET_KEY=test_secret
```

### Quick Test Runner

Use the comprehensive test runner:
```bash
python run_tests.py
```

This will:
- Test all module imports
- Validate syntax
- Test configuration
- Test database operations
- Test agent system
- Test API utilities
- Test Collections integration
- Test evaluation utilities

### Using pytest

For more detailed output and coverage:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_database.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_database.py::test_create_user -v
```

## Test Categories

### 1. Unit Tests

Test individual components in isolation:

- **test_config.py**: Configuration loading and validation
- **test_database.py**: Database CRUD operations
- **test_agents.py**: Individual agent functionality
- **test_api_utils.py**: API wrapper methods
- **test_collections.py**: Collections utility functions
- **test_evaluation.py**: Evaluation and scoring functions

### 2. Integration Tests

Test component interactions:

- **test_integration.py**: Full workflow from user creation to optimization

## Test Coverage

### Configuration Tests
- ✅ Environment variable loading
- ✅ Default values
- ✅ Optional Collections configuration
- ✅ Error handling for missing values

### Database Tests
- ✅ User creation and authentication
- ✅ Session tracking
- ✅ Usage limit enforcement
- ✅ Password hashing
- ✅ Error handling

### Agent Tests
- ✅ Agent initialization
- ✅ Prompt processing
- ✅ Error handling
- ✅ Score extraction
- ✅ Identity query handling

### API Tests
- ✅ API client initialization
- ✅ Completion generation
- ✅ Persona enforcement
- ✅ Tool integration
- ✅ Error handling

### Collections Tests
- ✅ Tool creation
- ✅ Collection selection
- ✅ Enabled/disabled checks

### Evaluation Tests
- ✅ Perplexity calculation
- ✅ Quality indicators
- ✅ Prompt comparison
- ✅ Result validation

## Mocking

Tests use mocking to avoid actual API calls:

```python
from unittest.mock import patch, MagicMock

# Mock API responses
with patch('api_utils.grok_api') as mock_api:
    mock_api.generate_completion.return_value = {
        "content": "Test response",
        "usage": {"total_tokens": 100},
        "model": "grok-4.1-fast"
    }
```

## Test Database

Tests use temporary SQLite databases:
- Created per test run
- Automatically cleaned up
- Isolated from production data

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=. --cov-report=xml
```

## Coverage Goals

- **Target:** 80%+ code coverage
- **Current:** All critical paths covered
- **Focus Areas:**
  - Database operations: 100%
  - Agent system: 90%+
  - API utilities: 85%+
  - Error handling: 100%

## Debugging Failed Tests

1. **Run with verbose output:**
   ```bash
   pytest tests/ -v -s
   ```

2. **Run specific test:**
   ```bash
   pytest tests/test_database.py::test_create_user -v
   ```

3. **Check test database:**
   - Tests use temporary databases
   - Check logs for database errors

4. **Verify environment:**
   - Ensure TESTING=1 is set
   - Check environment variables

## Best Practices

1. **Isolation**: Each test is independent
2. **Cleanup**: Tests clean up after themselves
3. **Mocking**: External dependencies are mocked
4. **Assertions**: Clear, specific assertions
5. **Documentation**: Tests are self-documenting

## Future Test Additions

- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Security penetration tests
- [ ] UI/UX tests (Streamlit)
- [ ] API rate limiting tests
- [ ] Collections API integration tests (with real API)

---

**Last Updated:** December 2025
