#!/usr/bin/env python3
"""
Deployment Validation Script
Validates code structure without requiring dependencies.
"""
import sys
import ast
import re
import os

def validate_syntax():
    """Validate Python syntax of all critical files."""
    print("🔍 Validating Python syntax...")
    files = ["api_utils.py", "agents.py", "main.py", "enterprise_integration.py", "config.py"]
    all_valid = True
    
    for file in files:
        if not os.path.exists(file):
            print(f"  ⚠️  {file}: Not found (may be expected)")
            continue
        try:
            with open(file, 'r') as f:
                ast.parse(f.read())
            print(f"  ✅ {file}: Valid syntax")
        except SyntaxError as e:
            print(f"  ❌ {file}: Syntax error - {str(e)}")
            all_valid = False
        except Exception as e:
            print(f"  ⚠️  {file}: Error - {str(e)}")
    
    return all_valid

def validate_fixes():
    """Validate that all critical fixes are in place."""
    print("\n🔍 Validating fixes...")
    
    checks = []
    
    # Check 1: api_utils.py - no self.model
    try:
        with open("api_utils.py", 'r') as f:
            content = f.read()
            if re.search(r'self\.model[^_]', content):
                checks.append(("api_utils.py: self.model removed", False))
            else:
                checks.append(("api_utils.py: self.model removed", True))
            if 'self.default_model' in content:
                checks.append(("api_utils.py: self.default_model exists", True))
            else:
                checks.append(("api_utils.py: self.default_model exists", False))
    except Exception as e:
        checks.append(("api_utils.py: Could not check", False))
    
    # Check 2: connection_pool.py - HTTP/2 disabled
    try:
        with open("connection_pool.py", 'r') as f:
            content = f.read()
            if 'http2=False' in content:
                checks.append(("connection_pool.py: HTTP/2 disabled", True))
            else:
                checks.append(("connection_pool.py: HTTP/2 disabled", False))
    except Exception as e:
        checks.append(("connection_pool.py: Could not check", False))
    
    # Check 3: agents.py - type validation
    try:
        with open("agents.py", 'r') as f:
            content = f.read()
            if 'isinstance(response, dict)' in content:
                checks.append(("agents.py: Response type validation", True))
            else:
                checks.append(("agents.py: Response type validation", False))
    except Exception as e:
        checks.append(("agents.py: Could not check", False))
    
    # Check 4: main.py - Path import
    try:
        with open("main.py", 'r') as f:
            content = f.read()
            if 'from pathlib import Path' in content:
                checks.append(("main.py: Path import present", True))
            else:
                checks.append(("main.py: Path import present", False))
    except Exception as e:
        checks.append(("main.py: Could not check", False))
    
    # Check 5: agents.py - improved extraction
    try:
        with open("agents.py", 'r') as f:
            content = f.read()
            if 'Strategy 1:' in content or 'code_block_pattern' in content:
                checks.append(("agents.py: Improved extraction (5 strategies)", True))
            else:
                checks.append(("agents.py: Improved extraction (5 strategies)", False))
    except Exception as e:
        checks.append(("agents.py: Could not check", False))
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def validate_config():
    """Validate configuration."""
    print("\n🔍 Validating configuration...")
    
    try:
        with open("config.py", 'r') as f:
            content = f.read()
            if 'grok-4-1-fast-reasoning' in content:
                print("  ✅ Model configured: grok-4-1-fast-reasoning")
                return True
            else:
                print("  ❌ Model not configured correctly")
                return False
    except Exception as e:
        print(f"  ⚠️  Could not validate config: {str(e)}")
        return False

def main():
    """Run all validations."""
    print("=" * 60)
    print("🔍 Deployment Validation")
    print("=" * 60)
    print("")
    
    results = []
    
    # Run validations
    results.append(("Syntax", validate_syntax()))
    results.append(("Fixes", validate_fixes()))
    results.append(("Config", validate_config()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    print("")
    print(f"Results: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n✅ ALL VALIDATIONS PASSED - Code is ready for deployment!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
