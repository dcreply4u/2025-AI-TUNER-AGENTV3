#!/usr/bin/env python3
"""
Comprehensive Test Runner

Runs all tests and generates a detailed report.
This is your QA test suite - run this regularly to ensure everything works.
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run all tests and generate report."""
    print("="*80)
    print("AI TUNER AGENT - COMPREHENSIVE QA TEST SUITE")
    print("="*80)
    print(f"Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Test categories - comprehensive coverage
    test_modules = [
        "tests.test_file_operations",
        "tests.test_graphing",
        "tests.test_data_reading",
        "tests.test_ai_advisor",
        "tests.test_telemetry_processing",
        "tests.test_integration",
        "tests.test_configuration",
        "tests.test_ui_components",
        "tests.test_error_handling",
        "tests.test_performance",
        "tests.test_comprehensive_qa",
    ]
    
    results = {}
    total_start = time.time()
    
    for module in test_modules:
        print(f"\n{'='*80}")
        print(f"Running: {module}")
        print(f"{'='*80}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", module, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per module
            )
            
            elapsed = time.time() - start_time
            results[module] = {
                "success": result.returncode == 0,
                "elapsed": elapsed,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            
            if result.returncode == 0:
                print(f"✓ PASSED ({elapsed:.2f}s)")
            else:
                print(f"✗ FAILED ({elapsed:.2f}s)")
                print(result.stdout)
                if result.stderr:
                    print("Errors:", result.stderr)
                    
        except subprocess.TimeoutExpired:
            results[module] = {
                "success": False,
                "elapsed": 300,
                "error": "Timeout",
            }
            print(f"✗ TIMEOUT (exceeded 5 minutes)")
        except Exception as e:
            results[module] = {
                "success": False,
                "elapsed": 0,
                "error": str(e),
            }
            print(f"✗ ERROR: {e}")
    
    # Summary
    total_elapsed = time.time() - total_start
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r.get("success", False))
    total = len(results)
    
    for module, result in results.items():
        status = "✓ PASS" if result.get("success") else "✗ FAIL"
        elapsed = result.get("elapsed", 0)
        print(f"  {module:50s} {status:6s} ({elapsed:6.2f}s)")
    
    print(f"\nTotal: {passed}/{total} test modules passed")
    print(f"Total Time: {total_elapsed:.2f}s")
    print(f"Test Run Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Generate report file
    report_file = project_root / "test_report.txt"
    with open(report_file, 'w') as f:
        f.write("AI TUNER AGENT - TEST REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Results: {passed}/{total} modules passed\n")
        f.write(f"Total Time: {total_elapsed:.2f}s\n\n")
        
        for module, result in results.items():
            f.write(f"\n{module}:\n")
            f.write(f"  Status: {'PASS' if result.get('success') else 'FAIL'}\n")
            f.write(f"  Time: {result.get('elapsed', 0):.2f}s\n")
            if result.get('stdout'):
                f.write(f"  Output:\n{result['stdout']}\n")
            if result.get('error'):
                f.write(f"  Error: {result['error']}\n")
    
    print(f"\nReport saved to: {report_file}")
    
    # Generate issues report
    try:
        from tests.test_issues_reporter import get_reporter
        reporter = get_reporter()
        issues_file = project_root / "test_issues.json"
        reporter.generate_report(issues_file)
        reporter.print_summary()
        print(f"\nIssues report saved to: {issues_file}")
    except Exception as e:
        print(f"\nNote: Could not generate issues report: {e}")
    
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

