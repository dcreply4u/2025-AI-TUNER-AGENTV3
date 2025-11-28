#!/usr/bin/env python3
"""Simple test runner that shows output in real-time."""

import sys
import subprocess
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent

print("="*80)
print("RUNNING QA TESTS - OUTPUT IN REAL-TIME")
print("="*80)
print()

# Test modules
test_modules = [
    "tests/test_file_operations.py",
    "tests/test_graphing.py",
    "tests/test_data_reading.py",
    "tests/test_ai_advisor.py",
    "tests/test_telemetry_processing.py",
    "tests/test_integration.py",
    "tests/test_configuration.py",
    "tests/test_ui_components.py",
    "tests/test_error_handling.py",
    "tests/test_performance.py",
    "tests/test_can_bus.py",
    "tests/test_comprehensive_qa.py",
]

total_passed = 0
total_failed = 0

for module in test_modules:
    print(f"\n{'='*80}")
    print(f"Testing: {module}")
    print(f"{'='*80}\n")
    sys.stdout.flush()
    
    # Run pytest - output goes directly to terminal
    result = subprocess.run(
        [sys.executable, "-m", "pytest", module, "-v", "--tb=short"],
        cwd=str(project_root),
    )
    
    if result.returncode == 0:
        print(f"✓ {module} PASSED\n")
        total_passed += 1
    else:
        print(f"✗ {module} FAILED\n")
        total_failed += 1

print("="*80)
print(f"SUMMARY: {total_passed} passed, {total_failed} failed")
print("="*80)

