#!/usr/bin/env python3
"""
Comprehensive QA Test Runner

Runs all tests and generates a detailed report.
This is your QA test suite - run this regularly to ensure everything works.
"""

import sys
import subprocess
import time
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import traceback

# Fix Windows encoding issues and force unbuffered output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    import os
    os.environ['PYTHONUNBUFFERED'] = '1'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import PDF generator
try:
    from tests.pdf_report_generator import PDFReportGenerator
    PDF_GENERATOR_AVAILABLE = True
except ImportError:
    PDF_GENERATOR_AVAILABLE = False
    PDFReportGenerator = None


class TestRunner:
    """Comprehensive test runner with detailed reporting."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.issues: List[Dict[str, Any]] = []
        self.start_time = time.time()
        
    def run_tests(self) -> bool:
        """Run all tests and generate report."""
        print("="*80)
        print("AI TUNER AGENT - COMPREHENSIVE QA TEST SUITE")
        print("="*80)
        print(f"Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Test categories - comprehensive coverage
        # Use file paths instead of module paths for pytest
        test_modules = [
            ("tests/test_file_operations.py", "File Operations"),
            ("tests/test_graphing.py", "Graphing & Visualization"),
            ("tests/test_data_reading.py", "Data Reading"),
            ("tests/test_ai_advisor.py", "AI Advisor"),
            ("tests/test_ai_advisor_advanced.py", "AI Advisor Advanced"),
            ("tests/test_telemetry_processing.py", "Telemetry Processing"),
            ("tests/test_integration.py", "Integration"),
            ("tests/test_configuration.py", "Configuration"),
            ("tests/test_ui_components.py", "UI Components"),
            ("tests/test_error_handling.py", "Error Handling"),
            ("tests/test_performance.py", "Performance"),
            ("tests/test_can_bus.py", "CAN Bus"),
            ("tests/test_comprehensive_qa.py", "Comprehensive QA"),
            ("tests/test_virtual_dyno.py", "Virtual Dyno"),
            ("tests/test_video_recording.py", "Video Recording"),
            ("tests/test_gps_lap_timing.py", "GPS & Lap Timing"),
            ("tests/test_voice_control.py", "Voice Control"),
            ("tests/test_ai_racing_coach.py", "AI Racing Coach"),
            ("tests/test_auto_tuning.py", "Auto-Tuning Engine"),
            ("tests/test_enhanced_graphing.py", "Enhanced Graphing"),
        ]
        
        for module_path, module_name in test_modules:
            print(f"\n{'='*80}")
            print(f"Running: {module_name} ({module_path})")
            print(f"{'='*80}")
            
            result = self._run_test_module(module_path, module_name)
            self.results[module_name] = result
        
        return self._generate_report()
    
    def _run_test_module(self, module_path: str, module_name: str) -> Dict[str, Any]:
        """Run a single test module."""
        start_time = time.time()
        result = {
            "module": module_path,
            "name": module_name,
            "success": False,
            "elapsed": 0,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "errors": [],
            "output": "",
            "error_output": "",
        }
        
        try:
            # Run pytest with verbose output
            cmd = [
                sys.executable, "-m", "pytest",
                module_path,
                "-v",
                "--tb=short",
                "--disable-warnings",
            ]
            
            # Print header
            print(f"\n{'='*80}")
            print(f"Running: {module_name}")
            print(f"{'='*80}\n")
            sys.stdout.flush()
            
            # Run pytest directly - output goes to terminal in real-time
            # Use os.system for immediate output, or subprocess without capture
            import os
            old_cwd = os.getcwd()
            os.chdir(str(project_root))
            
            try:
                # Run pytest - output streams directly to terminal with unbuffered output
                cmd = f'"{sys.executable}" -u -m pytest {module_path} -v --tb=short --disable-warnings'
                return_code = os.system(cmd)
                return_code = return_code >> 8  # os.system returns exit code in high byte
            finally:
                os.chdir(old_cwd)
            
            elapsed = time.time() - start_time
            result["elapsed"] = elapsed
            
            # Re-run with capture just to parse results for reporting
            parse_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(project_root),
                encoding='utf-8',
                errors='replace',
            )
            combined_output = parse_process.stdout + "\n" + parse_process.stderr
            result["output"] = combined_output
            result["error_output"] = parse_process.stderr
            
            # Parse pytest text output
            import re
            # Use combined output for parsing
            lines = combined_output.split('\n')
            
            # Method 1: Look for summary line with ====== separators
            # Pattern: "======================== X passed, Y failed, Z skipped in T seconds ========================="
            for line in lines:
                line_stripped = line.strip()
                # Check if line contains test results summary
                if 'passed' in line_stripped.lower() or 'failed' in line_stripped.lower():
                    # Extract all numbers with their status - match "8 passed" or "1 skipped" etc.
                    matches = re.findall(r'(\d+)\s+(passed|failed|skipped|error)', line_stripped.lower())
                    if matches:
                        for num_str, status in matches:
                            num = int(num_str)
                            if status == 'passed':
                                result["tests_passed"] = num
                            elif status == 'failed':
                                result["tests_failed"] = num
                            elif status == 'skipped':
                                result["tests_skipped"] = num
                            elif status == 'error':
                                result["tests_failed"] += num
                        
                        result["tests_run"] = result["tests_passed"] + result["tests_failed"] + result["tests_skipped"]
                        break
            
            # Method 2: Count collected tests if summary not found
            if result["tests_run"] == 0:
                for line in lines:
                    if 'collected' in line.lower():
                        # Pattern: "collected 9 items" or "collected 9 item"
                        match = re.search(r'collected\s+(\d+)\s+item', line.lower())
                        if match:
                            collected = int(match.group(1))
                            result["tests_run"] = collected
                            # If we have collected count but no summary, assume all passed
                            if result["tests_passed"] == 0 and result["tests_failed"] == 0:
                                result["tests_passed"] = collected
                            break
            
            # Method 3: Count test lines (PASSED, FAILED, SKIPPED)
            if result["tests_run"] == 0:
                passed_count = sum(1 for line in lines if 'PASSED' in line and '[' in line)
                failed_count = sum(1 for line in lines if 'FAILED' in line and '[' in line)
                skipped_count = sum(1 for line in lines if 'SKIPPED' in line and '[' in line)
                if passed_count > 0 or failed_count > 0 or skipped_count > 0:
                    result["tests_passed"] = passed_count
                    result["tests_failed"] = failed_count
                    result["tests_skipped"] = skipped_count
                    result["tests_run"] = passed_count + failed_count + skipped_count
            
            # Extract failed test names and errors
            current_test = None
            collecting_error = False
            error_lines = []
            for line in lines:
                if line.strip().startswith('FAILED'):
                    # Extract test name
                    parts = line.split('::')
                    if len(parts) >= 2:
                        current_test = parts[-1].strip()
                        collecting_error = True
                        error_lines = []
                elif collecting_error and current_test:
                    if line.strip() and not line.strip().startswith('='):
                        error_lines.append(line.strip())
                    elif line.strip().startswith('=') and error_lines:
                        # End of error block
                        result["errors"].append({
                            "test": current_test,
                            "message": '\n'.join(error_lines[:10]),  # First 10 lines
                        })
                        collecting_error = False
                        current_test = None
                        error_lines = []
            
            # Determine success - if no tests found, that's also a failure
            if result["tests_run"] == 0:
                result["success"] = False
                result["errors"].append({
                    "test": "all",
                    "message": "No tests found or discovered in this module",
                })
            else:
                result["success"] = (
                    parse_process.returncode == 0 and
                    result["tests_failed"] == 0 and
                    result["tests_run"] > 0
                )
            
            if result["success"]:
                print(f"[PASS] - {result['tests_passed']} tests passed ({elapsed:.2f}s)")
            else:
                print(f"[FAIL] - {result['tests_failed']} tests failed ({elapsed:.2f}s)")
                if result["errors"]:
                    for error in result["errors"][:3]:  # Show first 3 errors
                        print(f"  - {error.get('test', 'Unknown')}: {error.get('message', '')[:100]}")
                
                # Add to issues list
                self.issues.append({
                    "category": module_name,
                    "severity": "high" if result["tests_failed"] > 0 else "medium",
                    "description": f"{result['tests_failed']} test(s) failed in {module_name}",
                    "module": module_path,
                    "errors": result["errors"],
                })
        
        except subprocess.TimeoutExpired:
            result["elapsed"] = 600
            result["success"] = False
            result["errors"].append({"test": "all", "message": "Test module timed out after 10 minutes"})
            print(f"[TIMEOUT] (exceeded 10 minutes)")
            
            self.issues.append({
                "category": module_name,
                "severity": "critical",
                "description": f"Test module {module_name} timed out",
                "module": module_path,
            })
        
        except Exception as e:
            result["elapsed"] = time.time() - start_time
            result["success"] = False
            result["errors"].append({"test": "all", "message": str(e)})
            print(f"[ERROR]: {e}")
            traceback.print_exc()
            
            self.issues.append({
                "category": module_name,
                "severity": "critical",
                "description": f"Error running {module_name}: {str(e)}",
                "module": module_path,
                "exception": str(e),
            })
        
        return result
    
    def _generate_report(self) -> bool:
        """Generate comprehensive test report."""
        total_elapsed = time.time() - self.start_time
        
        # Calculate summary
        total_modules = len(self.results)
        passed_modules = sum(1 for r in self.results.values() if r.get("success", False))
        total_tests = sum(r.get("tests_run", 0) for r in self.results.values())
        total_passed = sum(r.get("tests_passed", 0) for r in self.results.values())
        total_failed = sum(r.get("tests_failed", 0) for r in self.results.values())
        total_skipped = sum(r.get("tests_skipped", 0) for r in self.results.values())
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        for module_name, result in self.results.items():
            status = "[PASS]" if result.get("success") else "[FAIL]"
            elapsed = result.get("elapsed", 0)
            tests_info = f"{result.get('tests_passed', 0)}/{result.get('tests_run', 0)}"
            print(f"  {module_name:40s} {status:6s} {tests_info:15s} ({elapsed:6.2f}s)")
        
        print(f"\nTotal Modules: {passed_modules}/{total_modules} passed")
        print(f"Total Tests: {total_passed}/{total_tests} passed ({total_failed} failed, {total_skipped} skipped)")
        print(f"Total Time: {total_elapsed:.2f}s")
        print(f"Test Run Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Generate text report
        report_file = project_root / "test_report.txt"
        self._write_text_report(report_file, total_elapsed, total_modules, passed_modules, 
                               total_tests, total_passed, total_failed, total_skipped)
        
        # Generate JSON report
        json_file = project_root / "test_report.json"
        self._write_json_report(json_file, total_elapsed, total_modules, passed_modules,
                               total_tests, total_passed, total_failed, total_skipped)
        
        # Generate issues report
        issues_file = project_root / "test_issues_list.txt"
        self._write_issues_report(issues_file)
        
        # Generate PDF report
        pdf_file = project_root / "test_report.pdf"
        self._generate_pdf_report(json_file, pdf_file)
        
        print(f"\n📄 Reports Generated:")
        print(f"  - Text Report: {report_file}")
        print(f"  - JSON Report: {json_file}")
        print(f"  - Issues List: {issues_file}")
        if pdf_file.exists():
            print(f"  - PDF Report: {pdf_file}")
        else:
            print(f"  - PDF Report: Not generated (install 'reportlab' or 'fpdf' for PDF support)")
        
        return passed_modules == total_modules and total_failed == 0
    
    def _write_text_report(self, file_path: Path, total_elapsed: float,
                          total_modules: int, passed_modules: int,
                          total_tests: int, total_passed: int,
                          total_failed: int, total_skipped: int):
        """Write text report file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("AI TUNER AGENT - COMPREHENSIVE TEST REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Modules: {passed_modules}/{total_modules} passed\n")
            f.write(f"Total Tests: {total_passed}/{total_tests} passed ({total_failed} failed, {total_skipped} skipped)\n")
            f.write(f"Total Time: {total_elapsed:.2f}s\n\n")
            
            f.write("MODULE RESULTS:\n")
            f.write("-"*80 + "\n")
            for module_name, result in self.results.items():
                status = "PASS" if result.get("success") else "FAIL"
                f.write(f"\n{module_name} ({result.get('module', '')}):\n")
                f.write(f"  Status: {status}\n")
                f.write(f"  Time: {result.get('elapsed', 0):.2f}s\n")
                f.write(f"  Tests: {result.get('tests_passed', 0)}/{result.get('tests_run', 0)} passed")
                if result.get('tests_failed', 0) > 0:
                    f.write(f" ({result.get('tests_failed', 0)} failed)")
                if result.get('tests_skipped', 0) > 0:
                    f.write(f" ({result.get('tests_skipped', 0)} skipped)")
                f.write("\n")
                
                if result.get("errors"):
                    f.write("  Errors:\n")
                    for error in result["errors"][:5]:  # First 5 errors
                        f.write(f"    - {error.get('test', 'Unknown')}\n")
                        msg = error.get('message', '')
                        if msg:
                            f.write(f"      {msg[:200]}\n")
            
            if self.issues:
                f.write("\n\nISSUES FOUND:\n")
                f.write("-"*80 + "\n")
                for issue in self.issues:
                    f.write(f"\n[{issue.get('severity', 'unknown').upper()}] {issue.get('category', 'Unknown')}\n")
                    f.write(f"  {issue.get('description', '')}\n")
                    if issue.get('module'):
                        f.write(f"  Module: {issue['module']}\n")
    
    def _write_json_report(self, file_path: Path, total_elapsed: float,
                          total_modules: int, passed_modules: int,
                          total_tests: int, total_passed: int,
                          total_failed: int, total_skipped: int):
        """Write JSON report file."""
        report = {
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_modules": total_modules,
                "passed_modules": passed_modules,
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "skipped_tests": total_skipped,
                "total_time_seconds": total_elapsed,
            },
            "modules": {
                name: {
                    "module": result.get("module", ""),
                    "success": result.get("success", False),
                    "elapsed": result.get("elapsed", 0),
                    "tests_run": result.get("tests_run", 0),
                    "tests_passed": result.get("tests_passed", 0),
                    "tests_failed": result.get("tests_failed", 0),
                    "tests_skipped": result.get("tests_skipped", 0),
                    "errors": result.get("errors", []),
                }
                for name, result in self.results.items()
            },
            "issues": self.issues,
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
    
    def _generate_pdf_report(self, json_file: Path, pdf_file: Path):
        """Generate PDF report from JSON results."""
        if not PDF_GENERATOR_AVAILABLE:
            return
        
        try:
            # Load JSON results
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Generate PDF
            generator = PDFReportGenerator()
            success = generator.generate_report(results, pdf_file)
            
            if success:
                print(f"  ✓ PDF report generated successfully")
            else:
                print(f"  ⚠ PDF generation failed (check dependencies)")
        except Exception as e:
            print(f"  ⚠ PDF generation error: {e}")
    
    def _write_issues_report(self, file_path: Path):
        """Write issues list for easy review."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("AI TUNER AGENT - TEST ISSUES LIST\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Issues: {len(self.issues)}\n\n")
            
            if not self.issues:
                f.write("✓ No issues found! All tests passed.\n")
                return
            
            # Group by severity
            by_severity = {}
            for issue in self.issues:
                severity = issue.get("severity", "unknown")
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(issue)
            
            for severity in ["critical", "high", "medium", "low"]:
                if severity in by_severity:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"{severity.upper()} PRIORITY ISSUES ({len(by_severity[severity])})\n")
                    f.write(f"{'='*80}\n\n")
                    
                    for i, issue in enumerate(by_severity[severity], 1):
                        f.write(f"{i}. [{issue.get('category', 'Unknown')}] {issue.get('description', '')}\n")
                        if issue.get('module'):
                            f.write(f"   Module: {issue['module']}\n")
                        if issue.get('errors'):
                            f.write(f"   Errors: {len(issue['errors'])} test(s) failed\n")
                        f.write("\n")


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
