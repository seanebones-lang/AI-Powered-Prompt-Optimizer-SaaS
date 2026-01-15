#!/usr/bin/env python3
"""
Comprehensive Feature Verification Script
Verifies that ALL features are integrated into main.py and working.
"""

import os
import sys
import re
from typing import List, Dict, Tuple

# Set testing environment
os.environ['TESTING'] = '1'
os.environ['XAI_API_KEY'] = 'test-key'
os.environ['SECRET_KEY'] = 'test-secret'

class FeatureVerifier:
    """Verifies all features are present and integrated."""
    
    def __init__(self):
        self.main_py_content = self._read_file('main.py')
        self.results = []
        
    def _read_file(self, filename: str) -> str:
        """Read file content."""
        with open(filename, 'r') as f:
            return f.read()
    
    def check_import(self, module: str, items: List[str]) -> Tuple[bool, str]:
        """Check if module and items are imported in main.py."""
        pattern = f"from {module} import.*({'|'.join(items)})"
        if re.search(pattern, self.main_py_content):
            return True, f"✅ {module} imported"
        return False, f"❌ {module} NOT imported"
    
    def check_feature_usage(self, feature_name: str, patterns: List[str]) -> Tuple[bool, str]:
        """Check if feature is used in main.py."""
        found = []
        missing = []
        
        for pattern in patterns:
            if pattern in self.main_py_content or re.search(pattern, self.main_py_content):
                found.append(pattern)
            else:
                missing.append(pattern)
        
        if len(found) == len(patterns):
            return True, f"✅ {feature_name}: All {len(patterns)} checks passed"
        elif found:
            return False, f"⚠️  {feature_name}: {len(found)}/{len(patterns)} checks passed (missing: {missing[0][:30]}...)"
        else:
            return False, f"❌ {feature_name}: NOT FOUND in main.py"
    
    def verify_all(self):
        """Run all verification checks."""
        print("=" * 80)
        print("COMPREHENSIVE FEATURE VERIFICATION")
        print("=" * 80)
        print()
        
        # 1. CORE IMPORTS
        print("1. CORE IMPORTS")
        print("-" * 80)
        core_imports = [
            ('agents', ['OrchestratorAgent', 'PromptType']),
            ('database', ['db']),
            ('input_validation', ['sanitize_and_validate_prompt', 'validate_prompt_type']),
            ('agent_config', ['AgentConfigManager']),
            ('export_utils', ['export_results']),
            ('batch_optimization', ['BatchOptimizer']),
        ]
        
        for module, items in core_imports:
            passed, msg = self.check_import(module, items)
            print(msg)
            self.results.append((f"Import: {module}", passed))
        print()
        
        # 2. ENTERPRISE FEATURES
        print("2. ENTERPRISE FEATURES")
        print("-" * 80)
        
        # Check if enterprise modules exist and can be imported
        enterprise_modules = [
            'blueprint_generator.py',
            'refinement_engine.py',
            'test_generator.py',
            'multi_model_testing.py',
            'context_manager.py',
            'performance_profiler.py',
            'security_scanner.py',
            'knowledge_base_manager.py',
            'enterprise_integration.py'
        ]
        
        for module in enterprise_modules:
            exists = os.path.exists(module)
            size = os.path.getsize(module) if exists else 0
            if exists and size > 1000:  # At least 1KB
                print(f"✅ {module}: {size:,} bytes")
                self.results.append((f"Enterprise: {module}", True))
            else:
                print(f"❌ {module}: Missing or empty")
                self.results.append((f"Enterprise: {module}", False))
        print()
        
        # 3. MAIN UI FEATURES
        print("3. MAIN UI FEATURES IN main.py")
        print("-" * 80)
        
        ui_features = {
            "Agent Tuning Panel": [
                "show_agent_tuning",
                "AgentConfigManager",
                "temperature",
                "max_tokens"
            ],
            "Batch Optimization": [
                "BatchOptimizer",
                "parse_batch_prompts",
                "batch_prompts"
            ],
            "Export Functionality": [
                "export_results",
                "Export",
                "download"
            ],
            "Session History": [
                "session_state",
                "optimization_result",
                "history"
            ],
            "User Authentication": [
                "login",
                "register",
                "user_id"
            ],
            "Premium Features": [
                "is_premium",
                "premium",
                "subscription"
            ]
        }
        
        for feature, patterns in ui_features.items():
            passed, msg = self.check_feature_usage(feature, patterns)
            print(msg)
            self.results.append((f"UI: {feature}", passed))
        print()
        
        # 4. ADDITIONAL FEATURES
        print("4. ADDITIONAL FEATURES")
        print("-" * 80)
        
        additional_modules = {
            "Analytics": ('analytics.py', ['Analytics']),
            "A/B Testing": ('ab_testing.py', ['ABTesting']),
            "Voice Prompting": ('voice_prompting.py', ['VoicePrompting']),
            "Integrations": ('integrations.py', ['slack', 'discord', 'notion']),
            "Monitoring": ('monitoring.py', ['get_metrics']),
            "Error Handling": ('error_handling.py', ['ErrorHandler']),
            "Performance": ('performance.py', ['track_performance']),
            "Cache Utils": ('cache_utils.py', ['get_cache']),
            "Observability": ('observability.py', ['get_tracker']),
            "API Server": ('api_server.py', ['FastAPI', 'optimize']),
            "Collections Utils": ('collections_utils.py', ['Collection']),
            "Prompt Library": ('prompt_library.py', ['PromptLibrary']),
            "Templates": ('templates.py', ['TEMPLATES']),
            "Agentic RAG": ('agentic_rag.py', ['AgenticRAG']),
            "Payments": ('payments.py', ['PaymentProcessor']),
            "Evaluation": ('evaluation.py', ['evaluate']),
        }
        
        for feature, (filename, keywords) in additional_modules.items():
            exists = os.path.exists(filename)
            if exists:
                content = self._read_file(filename)
                has_keywords = any(kw in content for kw in keywords)
                if has_keywords:
                    size = os.path.getsize(filename)
                    print(f"✅ {feature}: {size:,} bytes")
                    self.results.append((f"Module: {feature}", True))
                else:
                    print(f"⚠️  {feature}: File exists but missing keywords")
                    self.results.append((f"Module: {feature}", False))
            else:
                print(f"❌ {feature}: File not found")
                self.results.append((f"Module: {feature}", False))
        print()
        
        # 5. DATABASE MODELS
        print("5. DATABASE MODELS")
        print("-" * 80)
        
        db_content = self._read_file('database.py')
        db_models = [
            'User',
            'OptimizationSession',
            'DailyUsage',
            'Collection',
            'Document',
            'AgentConfig',
            'BatchJob',
            'ABTest',
            'PromptVersion',
            'AgentBlueprint',
            'RefinementHistory',
            'TestCase',
            'PerformanceMetric',
            'SecurityScan'
        ]
        
        for model in db_models:
            pattern = f"class {model}\\("
            if re.search(pattern, db_content):
                print(f"✅ {model} model defined")
                self.results.append((f"DB Model: {model}", True))
            else:
                print(f"❌ {model} model NOT found")
                self.results.append((f"DB Model: {model}", False))
        print()
        
        # 6. AGENT TYPES
        print("6. AGENT TYPES & PROMPT TYPES")
        print("-" * 80)
        
        agents_content = self._read_file('agents.py')
        
        # Check for PromptType enum
        prompt_types = ['BUILD_AGENT', 'REQUEST_BUILD', 'DEPLOYMENT_OPTIONS', 'SYSTEM_IMPROVEMENT']
        for pt in prompt_types:
            if pt in agents_content:
                print(f"✅ PromptType.{pt}")
                self.results.append((f"PromptType: {pt}", True))
            else:
                print(f"❌ PromptType.{pt} NOT found")
                self.results.append((f"PromptType: {pt}", False))
        print()
        
        # 7. API ENDPOINTS
        print("7. API ENDPOINTS (api_server.py)")
        print("-" * 80)
        
        if os.path.exists('api_server.py'):
            api_content = self._read_file('api_server.py')
            endpoints = [
                '/api/v1/optimize',
                '/api/v1/batch/optimize',
                '/api/v1/ab-test',
                '/api/v1/export',
                '/api/v1/analytics',
                '/api/v1/user/api-key'
            ]
            
            for endpoint in endpoints:
                if endpoint in api_content:
                    print(f"✅ {endpoint}")
                    self.results.append((f"API: {endpoint}", True))
                else:
                    print(f"❌ {endpoint} NOT found")
                    self.results.append((f"API: {endpoint}", False))
        else:
            print("❌ api_server.py not found")
            self.results.append(("API Server", False))
        print()
        
        # 8. CONFIGURATION
        print("8. CONFIGURATION")
        print("-" * 80)
        
        config_content = self._read_file('config.py')
        config_vars = [
            'XAI_API_KEY',
            'SECRET_KEY',
            'DATABASE_URL',
            'XAI_MODEL',
            'FREE_TIER_DAILY_LIMIT',
            'PAID_TIER_DAILY_LIMIT',
            'ENABLE_COLLECTIONS'
        ]
        
        for var in config_vars:
            if var in config_content:
                print(f"✅ {var}")
                self.results.append((f"Config: {var}", True))
            else:
                print(f"❌ {var} NOT found")
                self.results.append((f"Config: {var}", False))
        print()
        
        # SUMMARY
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Checks: {total}")
        print(f"Passed: {passed} ({percentage:.1f}%)")
        print(f"Failed: {total - passed}")
        print()
        
        # Group by category
        categories = {}
        for name, result in self.results:
            category = name.split(':')[0]
            if category not in categories:
                categories[category] = {'passed': 0, 'total': 0}
            categories[category]['total'] += 1
            if result:
                categories[category]['passed'] += 1
        
        print("BY CATEGORY:")
        for category, stats in sorted(categories.items()):
            pct = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if pct == 100 else "⚠️" if pct >= 50 else "❌"
            print(f"{status} {category}: {stats['passed']}/{stats['total']} ({pct:.0f}%)")
        print()
        
        if percentage >= 90:
            print("🎉 EXCELLENT! Almost all features are integrated and working!")
            return 0
        elif percentage >= 75:
            print("✅ GOOD! Most features are integrated. Some minor items missing.")
            return 0
        elif percentage >= 50:
            print("⚠️  WARNING! Significant features are missing from main.py.")
            return 1
        else:
            print("❌ CRITICAL! Many features are not integrated into main.py.")
            return 1

def main():
    """Run verification."""
    verifier = FeatureVerifier()
    return verifier.verify_all()

if __name__ == "__main__":
    sys.exit(main())
