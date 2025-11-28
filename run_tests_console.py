#!/usr/bin/env python3
"""Simple test runner that prints directly to console."""

import sys
import subprocess
import os

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Set environment for unbuffered Python
os.environ['PYTHONUNBUFFERED'] = '1'

print("=" * 80, flush=True)
print("QA TEST RUNNER - REAL-TIME OUTPUT", flush=True)
print("=" * 80, flush=True)
print("", flush=True)

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

for module in test_modules:
    print(f"\n{'='*80}", flush=True)
    print(f"Testing: {module}", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    # Run pytest with unbuffered output
    cmd = [sys.executable, "-u", "-m", "pytest", module, "-v", "--tb=short", "-s"]
    
    # Run directly - output goes to terminal
    process = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        bufsize=0,  # Unbuffered
        text=True,
    )
    
    process.wait()
    
    if process.returncode == 0:
        print(f"\n✓ {module} PASSED\n", flush=True)
    else:
        print(f"\n✗ {module} FAILED\n", flush=True)

print("=" * 80, flush=True)
print("TEST RUN COMPLETE", flush=True)
print("=" * 80, flush=True)

