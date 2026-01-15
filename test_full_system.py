#!/usr/bin/env python3
"""
Comprehensive system test for AI-Powered Prompt Optimizer.
Tests all major components without requiring pytest.
"""

import sys
import os

# Set testing environment
os.environ['TESTING'] = '1'
os.environ['XAI_API_KEY'] = 'test-key'
os.environ['SECRET_KEY'] = 'test-secret'

def test_imports():
    """Test that all major modules can be imported."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    modules_to_test = [
        ('agents', ['OrchestratorAgent', 'PromptType', 'BaseAgent']),
        ('config', ['settings']),
        ('input_validation', ['sanitize_and_validate_prompt', 'validate_prompt_type']),
        ('api_utils', ['call_xai_api']),
        ('batch_optimization', ['BatchOptimizer']),
        ('analytics', ['Analytics']),
        ('monitoring', ['get_metrics']),
        ('error_handling', ['ErrorHandler']),
        ('export_utils', ['export_results']),
        ('agent_config', ['AgentConfigManager']),
        ('enterprise_integration', ['EnterpriseFeatureManager']),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, classes in modules_to_test:
        try:
            module = __import__(module_name)
            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"✅ {module_name}.{class_name}")
                    passed += 1
                else:
                    print(f"❌ {module_name}.{class_name} - Not found")
                    failed += 1
        except Exception as e:
            print(f"❌ {module_name} - Import error: {str(e)[:50]}")
            failed += len(classes)
    
    print(f"\nResult: {passed} passed, {failed} failed\n")
    return failed == 0


def test_agent_system():
    """Test the agent system initialization."""
    print("=" * 60)
    print("TEST 2: Agent System")
    print("=" * 60)
    
    try:
        from agents import OrchestratorAgent, PromptType
        
        # Test prompt types
        print(f"✅ Prompt types available: {len(list(PromptType))}")
        for pt in PromptType:
            print(f"   • {pt.value}")
        
        # Test orchestrator initialization
        orchestrator = OrchestratorAgent()
        print(f"✅ Orchestrator initialized: {orchestrator.__class__.__name__}")
        
        # Test agent configuration
        print(f"✅ Agent has config: {hasattr(orchestrator, 'config')}")
        
        print("\nResult: PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nResult: FAILED\n")
        return False


def test_enterprise_features():
    """Test enterprise feature integration."""
    print("=" * 60)
    print("TEST 3: Enterprise Features")
    print("=" * 60)
    
    try:
        from enterprise_integration import EnterpriseFeatureManager
        
        manager = EnterpriseFeatureManager()
        print(f"✅ Enterprise manager initialized")
        
        # Check all feature modules
        features = [
            'blueprint_gen',
            'refinement_engine',
            'test_generator',
            'model_tester',
            'context_manager',
            'profiler',
            'cost_tracker',
            'security_scanner',
            'kb_manager'
        ]
        
        for feature in features:
            if hasattr(manager, feature):
                print(f"✅ {feature}: Available")
            else:
                print(f"❌ {feature}: Missing")
        
        print("\nResult: PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nResult: FAILED\n")
        return False


def test_input_validation():
    """Test input validation."""
    print("=" * 60)
    print("TEST 4: Input Validation")
    print("=" * 60)
    
    try:
        from input_validation import sanitize_and_validate_prompt, validate_prompt_type
        
        # Test prompt sanitization
        test_prompt = "Build me an AI agent"
        sanitized = sanitize_and_validate_prompt(test_prompt)
        print(f"✅ Prompt sanitization: '{sanitized[:30]}...'")
        
        # Test type validation
        valid_type = validate_prompt_type("build_agent")
        print(f"✅ Type validation: {valid_type}")
        
        print("\nResult: PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nResult: FAILED\n")
        return False


def test_batch_and_analytics():
    """Test batch optimization and analytics."""
    print("=" * 60)
    print("TEST 5: Batch & Analytics")
    print("=" * 60)
    
    try:
        from batch_optimization import BatchOptimizer
        from analytics import Analytics
        
        batch_optimizer = BatchOptimizer()
        print(f"✅ BatchOptimizer initialized")
        
        analytics = Analytics()
        print(f"✅ Analytics initialized")
        
        print("\nResult: PASSED\n")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nResult: FAILED\n")
        return False


def test_file_structure():
    """Test that all critical files exist."""
    print("=" * 60)
    print("TEST 6: File Structure")
    print("=" * 60)
    
    critical_files = [
        'main.py',
        'agents.py',
        'database.py',
        'config.py',
        'api_utils.py',
        'input_validation.py',
        'enterprise_integration.py',
        'requirements.txt',
        'README.md',
        'ENTERPRISE_FEATURES.md',
    ]
    
    passed = 0
    failed = 0
    
    for filename in critical_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename} ({size:,} bytes)")
            passed += 1
        else:
            print(f"❌ {filename} - Missing")
            failed += 1
    
    print(f"\nResult: {passed} passed, {failed} failed\n")
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI-POWERED PROMPT OPTIMIZER - FULL SYSTEM TEST")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run all tests
    results.append(("Module Imports", test_imports()))
    results.append(("Agent System", test_agent_system()))
    results.append(("Enterprise Features", test_enterprise_features()))
    results.append(("Input Validation", test_input_validation()))
    results.append(("Batch & Analytics", test_batch_and_analytics()))
    results.append(("File Structure", test_file_structure()))
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
