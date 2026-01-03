#!/usr/bin/env python3
"""
Comprehensive test runner for AI-Powered Prompt Optimizer SaaS.
Run this script to test all components of the system.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Set test environment
os.environ["TESTING"] = "1"
os.environ["XAI_API_KEY"] = "test_key_for_testing"
os.environ["SECRET_KEY"] = "test_secret_for_testing"
os.environ["DATABASE_URL"] = "sqlite:///test_prompt_optimizer.db"

def run_basic_import_tests():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("TEST 1: Module Import Tests")
    print("=" * 60)
    
    modules = [
        "config",
        "database",
        "api_utils",
        "agents",
        "collections_utils",
        "evaluation"
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} imports successfully")
        except Exception as e:
            print(f"✗ {module} failed to import: {e}")
            failed.append(module)
    
    if failed:
        print(f"\n✗ {len(failed)} modules failed to import")
        return False
    else:
        print(f"\n✓ All {len(modules)} modules import successfully")
        return True


def run_syntax_tests():
    """Test that all Python files have valid syntax."""
    print("\n" + "=" * 60)
    print("TEST 2: Syntax Validation")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    python_files = list(project_root.glob("*.py"))
    python_files.extend(project_root.glob("tests/*.py"))
    
    failed = []
    for py_file in python_files:
        if py_file.name == "__init__.py":
            continue
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
            print(f"✓ {py_file.name} syntax valid")
        except SyntaxError as e:
            print(f"✗ {py_file.name} syntax error: {e}")
            failed.append(py_file)
    
    if failed:
        print(f"\n✗ {len(failed)} files have syntax errors")
        return False
    else:
        print(f"\n✓ All {len(python_files)} files have valid syntax")
        return True


def run_config_tests():
    """Test configuration management."""
    print("\n" + "=" * 60)
    print("TEST 3: Configuration Tests")
    print("=" * 60)
    
    try:
        from config import settings
        
        # Test that settings exist
        assert hasattr(settings, 'xai_api_key'), "Missing xai_api_key"
        assert hasattr(settings, 'secret_key'), "Missing secret_key"
        assert hasattr(settings, 'database_url'), "Missing database_url"
        
        print("✓ Settings object created")
        print(f"✓ API Base: {settings.xai_api_base}")
        print(f"✓ Model: {settings.xai_model}")
        print(f"✓ Free tier limit: {settings.free_tier_daily_limit}")
        print(f"✓ Paid tier limit: {settings.paid_tier_daily_limit}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_database_tests():
    """Test database functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: Database Tests")
    print("=" * 60)
    
    try:
        from database import Database, User
        
        # Use test database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{test_db.name}"
        
        # Reload database module
        import importlib
        import database
        importlib.reload(database)
        
        db = database.Database()
        print("✓ Database initialized")
        
        # Test user creation
        user = db.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        assert user is not None, "User creation failed"
        print("✓ User creation works")
        
        # Test authentication
        auth_user = db.authenticate_user("testuser", "testpass123")
        assert auth_user is not None, "Authentication failed"
        assert auth_user.id == user.id, "User ID mismatch"
        print("✓ User authentication works")
        
        # Test usage limits
        assert db.check_usage_limit(user.id) is True, "Initial usage check failed"
        print("✓ Usage limit checking works")
        
        # Cleanup
        os.unlink(test_db.name)
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_agent_tests():
    """Test agent system."""
    print("\n" + "=" * 60)
    print("TEST 5: Agent System Tests")
    print("=" * 60)
    
    try:
        from agents import (
            OrchestratorAgent,
            DeconstructorAgent,
            DiagnoserAgent,
            DesignerAgent,
            EvaluatorAgent,
            PromptType
        )
        
        # Test enum
        assert PromptType.CREATIVE.value == "creative"
        print("✓ PromptType enum works")
        
        # Test agent initialization
        orchestrator = OrchestratorAgent()
        assert orchestrator.name == "Orchestrator"
        print("✓ OrchestratorAgent initializes")
        
        deconstructor = DeconstructorAgent()
        assert deconstructor.name == "Deconstructor"
        print("✓ DeconstructorAgent initializes")
        
        diagnoser = DiagnoserAgent()
        assert diagnoser.name == "Diagnoser"
        print("✓ DiagnoserAgent initializes")
        
        designer = DesignerAgent()
        assert designer.name == "Designer"
        print("✓ DesignerAgent initializes")
        
        evaluator = EvaluatorAgent()
        assert evaluator.name == "Evaluator"
        print("✓ EvaluatorAgent initializes")
        
        return True
    except Exception as e:
        print(f"✗ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_api_utils_tests():
    """Test API utilities."""
    print("\n" + "=" * 60)
    print("TEST 6: API Utilities Tests")
    print("=" * 60)
    
    try:
        from api_utils import GrokAPI, BASE_PERSONA_PROMPT
        
        # Test persona prompt exists
        assert "NextEleven AI" in BASE_PERSONA_PROMPT
        print("✓ Persona prompt defined")
        
        # Test API class initialization (won't actually call API)
        api = GrokAPI()
        assert api.model == "grok-4.1-fast"
        print("✓ GrokAPI initializes")
        
        # Test sanitization
        test_content = "I am Grok, powered by xAI"
        sanitized = api._sanitize_persona_content(test_content)
        assert "Grok" not in sanitized or "NextEleven AI" in sanitized
        print("✓ Persona sanitization works")
        
        return True
    except Exception as e:
        print(f"✗ API utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_collections_tests():
    """Test Collections integration."""
    print("\n" + "=" * 60)
    print("TEST 7: Collections Integration Tests")
    print("=" * 60)
    
    try:
        from collections_utils import (
            get_collections_search_tool,
            get_collections_for_prompt_type,
            is_collections_enabled
        )
        
        # Test tool creation
        tool = get_collections_search_tool(["col_123"])
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "file_search"
        print("✓ Collections tool creation works")
        
        # Test collection selection
        collections = get_collections_for_prompt_type("marketing")
        assert isinstance(collections, list)
        print("✓ Collection selection works")
        
        # Test enabled check
        enabled = is_collections_enabled()
        assert isinstance(enabled, bool)
        print("✓ Collections enabled check works")
        
        return True
    except Exception as e:
        print(f"✗ Collections test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_evaluation_tests():
    """Test evaluation utilities."""
    print("\n" + "=" * 60)
    print("TEST 8: Evaluation Utilities Tests")
    print("=" * 60)
    
    try:
        from evaluation import (
            calculate_perplexity_score,
            extract_quality_indicators,
            compare_prompts,
            validate_optimization_result
        )
        
        # Test perplexity
        score = calculate_perplexity_score("Test text")
        assert isinstance(score, float)
        assert 0 <= score <= 100
        print("✓ Perplexity calculation works")
        
        # Test quality indicators
        indicators = extract_quality_indicators("Test prompt with instructions")
        assert "word_count" in indicators
        print("✓ Quality indicators extraction works")
        
        # Test comparison
        comparison = compare_prompts("Original", "Optimized version")
        assert "original" in comparison
        assert "optimized" in comparison
        print("✓ Prompt comparison works")
        
        # Test validation
        result = {
            "original_prompt": "Test",
            "optimized_prompt": "Optimized",
            "quality_score": 85
        }
        is_valid, errors = validate_optimization_result(result)
        assert is_valid is True
        print("✓ Result validation works")
        
        return True
    except Exception as e:
        print(f"✗ Evaluation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI-Powered Prompt Optimizer SaaS - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", run_basic_import_tests),
        ("Syntax Validation", run_syntax_tests),
        ("Configuration", run_config_tests),
        ("Database", run_database_tests),
        ("Agent System", run_agent_tests),
        ("API Utilities", run_api_utils_tests),
        ("Collections", run_collections_tests),
        ("Evaluation", run_evaluation_tests),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is functional.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
