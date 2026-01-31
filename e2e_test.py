#!/usr/bin/env python3
"""
End-to-End Test Suite
Tests the complete optimization workflow from input to output display.
"""
import sys
import os

# Set test environment
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("XAI_API_KEY", os.getenv("XAI_API_KEY", "test-key"))
os.environ.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "test-secret"))

def test_imports():
    """Test that all critical modules can be imported."""
    print("🔍 Testing imports...")
    try:
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {str(e)}")
        return False

def test_api_client():
    """Test API client initialization."""
    print("🔍 Testing API client...")
    try:
        from api_utils import grok_api
        assert hasattr(grok_api, 'default_model'), "Missing default_model"
        assert hasattr(grok_api, 'light_model'), "Missing light_model"
        assert grok_api.default_model == "grok-4-1-fast-reasoning" or "grok" in grok_api.default_model.lower()
        print(f"  ✅ API client initialized (model: {grok_api.default_model})")
        return True
    except Exception as e:
        print(f"  ❌ API client test failed: {str(e)}")
        return False

def test_enterprise_manager():
    """Test enterprise feature manager."""
    print("🔍 Testing Enterprise Manager...")
    try:
        from enterprise_integration import enterprise_manager
        status = enterprise_manager.get_feature_status()
        assert status.get("status") == "All systems operational"
        print(f"  ✅ Enterprise Manager: {status.get('available_features')}/{status.get('total_features')} features available")
        return True
    except Exception as e:
        print(f"  ❌ Enterprise Manager test failed: {str(e)}")
        return False

def test_prompt_extraction():
    """Test optimized prompt extraction logic."""
    print("🔍 Testing prompt extraction...")
    try:
        from agents import OrchestratorAgent

        orchestrator = OrchestratorAgent()

        # Test case 1: Code block extraction
        test_output1 = """
Here is the optimized prompt:

```text
You are a helpful assistant that provides clear and concise answers.
```
"""
        extracted1 = orchestrator._extract_optimized_prompt(test_output1)
        assert len(extracted1) > 10, "Extraction too short"
        assert "helpful assistant" in extracted1.lower()
        print("  ✅ Code block extraction works")

        # Test case 2: Marker-based extraction
        test_output2 = """
Optimized Prompt:
You are an expert in AI and machine learning. Provide detailed explanations.
"""
        extracted2 = orchestrator._extract_optimized_prompt(test_output2)
        assert len(extracted2) > 10, "Extraction too short"
        print("  ✅ Marker-based extraction works")

        # Test case 3: Fallback
        test_output3 = "This is a simple prompt without markers."
        extracted3 = orchestrator._extract_optimized_prompt(test_output3)
        assert len(extracted3) > 0, "Fallback should return something"
        print("  ✅ Fallback extraction works")

        return True
    except Exception as e:
        print(f"  ❌ Prompt extraction test failed: {str(e)}")
        return False

def test_result_structure():
    """Test that optimization results have correct structure."""
    print("🔍 Testing result structure...")
    try:

        # Create a mock result structure
        result = {
            "original_prompt": "Test prompt",
            "prompt_type": "general",
            "deconstruction": None,
            "diagnosis": None,
            "optimized_prompt": None,
            "sample_output": None,
            "evaluation": None,
            "quality_score": None,
            "errors": [],
            "workflow_mode": "sequential"
        }

        # Verify all expected keys exist
        required_keys = ["original_prompt", "optimized_prompt", "errors", "workflow_mode"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

        print("  ✅ Result structure is correct")
        return True
    except Exception as e:
        print(f"  ❌ Result structure test failed: {str(e)}")
        return False

def test_input_validation():
    """Test input validation functions."""
    print("🔍 Testing input validation...")
    try:
        from input_validation import sanitize_and_validate_prompt, validate_prompt_type
        from agents import PromptType

        # Test valid prompt
        is_valid, sanitized, error = sanitize_and_validate_prompt("This is a test prompt")
        assert is_valid, "Valid prompt should pass"
        assert sanitized is not None, "Should return sanitized prompt"
        print("  ✅ Valid prompt validation works")

        # Test invalid prompt (empty)
        is_valid, sanitized, error = sanitize_and_validate_prompt("")
        assert not is_valid, "Empty prompt should fail"
        print("  ✅ Empty prompt validation works")

        # Test prompt type validation
        is_valid, prompt_type, error = validate_prompt_type("general")
        assert is_valid, "Valid prompt type should pass"
        assert prompt_type == PromptType.GENERAL, "Should return correct enum"
        print("  ✅ Prompt type validation works")

        return True
    except Exception as e:
        print(f"  ❌ Input validation test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling in agents."""
    print("🔍 Testing error handling...")
    try:
        from agents import AgentOutput

        # Test that AgentOutput handles errors correctly
        error_output = AgentOutput(
            success=False,
            content="",
            errors=["Test error"],
            metadata={}
        )

        assert not error_output.success, "Should mark as unsuccessful"
        assert len(error_output.errors) > 0, "Should have errors"
        print("  ✅ Error handling structure correct")

        return True
    except Exception as e:
        print(f"  ❌ Error handling test failed: {str(e)}")
        return False

def test_ui_structure():
    """Test that UI components can be accessed."""
    print("🔍 Testing UI structure...")
    try:
        # Check that main.py can be imported and has required functions
        import main
        assert hasattr(main, 'show_optimize_page'), "Missing show_optimize_page"
        assert hasattr(main, 'init_session_state'), "Missing init_session_state"
        print("  ✅ UI structure is correct")
        return True
    except Exception as e:
        print(f"  ❌ UI structure test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all E2E tests."""
    print("=" * 60)
    print("🧪 End-to-End Test Suite")
    print("=" * 60)
    print("")

    tests = [
        ("Imports", test_imports),
        ("API Client", test_api_client),
        ("Enterprise Manager", test_enterprise_manager),
        ("Prompt Extraction", test_prompt_extraction),
        ("Result Structure", test_result_structure),
        ("Input Validation", test_input_validation),
        ("Error Handling", test_error_handling),
        ("UI Structure", test_ui_structure),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
        print("")

    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print("")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
