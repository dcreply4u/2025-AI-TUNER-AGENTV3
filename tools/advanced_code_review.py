#!/usr/bin/env python3
"""
Advanced Code Review Automation Tool

Performs comprehensive code analysis including:
- Security scanning (SAST)
- Dependency vulnerability analysis
- Complexity analysis
- Performance profiling
- Code quality metrics
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)

# Update PATH to include user local bin
USER_LOCAL_BIN = Path.home() / ".local" / "bin"
if USER_LOCAL_BIN.exists():
    os.environ["PATH"] = str(USER_LOCAL_BIN) + os.pathsep + os.environ.get("PATH", "")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)


class SecurityScanner:
    """Security scanning using bandit and pip-audit."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[str, Any] = {}
        
    def check_bandit_available(self) -> bool:
        """Check if bandit is installed."""
        # Check in PATH and common locations
        bandit_path = shutil.which('bandit')
        if not bandit_path:
            # Check in user local bin
            user_bin = Path.home() / ".local" / "bin" / "bandit"
            if user_bin.exists():
                return True
            return False
        try:
            subprocess.run([bandit_path or 'bandit', '--version'], capture_output=True, check=True, env=os.environ)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def check_pip_audit_available(self) -> bool:
        """Check if pip-audit is installed."""
        # Check in PATH and common locations
        pip_audit_path = shutil.which('pip-audit')
        if not pip_audit_path:
            # Check in user local bin
            user_bin = Path.home() / ".local" / "bin" / "pip-audit"
            if user_bin.exists():
                return True
            return False
        try:
            subprocess.run([pip_audit_path or 'pip-audit', '--version'], capture_output=True, check=True, env=os.environ)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def run_bandit(self) -> Dict[str, Any]:
        """Run bandit security scan."""
        if not self.check_bandit_available():
            return {
                "available": False,
                "error": "bandit not installed. Install with: pip install bandit"
            }
        
        try:
            output_file = self.project_root / "reports" / "bandit-report.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Find bandit executable
            bandit_cmd = shutil.which('bandit') or str(Path.home() / ".local" / "bin" / "bandit")
            if not Path(bandit_cmd).exists():
                bandit_cmd = 'bandit'
            
            cmd = [
                bandit_cmd,
                '-r', str(self.project_root),
                '-f', 'json',
                '-o', str(output_file),
                '--exclude', 'tests,venv,env,.venv,node_modules',
                '--severity-level', 'all',
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=os.environ
            )
            
            # Read results
            if output_file.exists():
                with open(output_file, 'r') as f:
                    bandit_data = json.load(f)
            else:
                bandit_data = {}
            
            return {
                "available": True,
                "exit_code": result.returncode,
                "results": bandit_data,
                "summary": {
                    "high_severity": bandit_data.get("metrics", {}).get("_totals", {}).get("SEVERITY.HIGH", 0),
                    "medium_severity": bandit_data.get("metrics", {}).get("_totals", {}).get("SEVERITY.MEDIUM", 0),
                    "low_severity": bandit_data.get("metrics", {}).get("_totals", {}).get("SEVERITY.LOW", 0),
                }
            }
        except Exception as e:
            return {
                "available": True,
                "error": str(e)
            }
    
    def run_pip_audit(self) -> Dict[str, Any]:
        """Run pip-audit dependency vulnerability scan."""
        if not self.check_pip_audit_available():
            return {
                "available": False,
                "error": "pip-audit not installed. Install with: pip install pip-audit"
            }
        
        try:
            output_file = self.project_root / "reports" / "pip-audit-report.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Find requirements files
            req_files = list(self.project_root.glob("requirements*.txt"))
            if not req_files:
                return {
                    "available": True,
                    "error": "No requirements*.txt files found"
                }
            
            # Find pip-audit executable
            pip_audit_cmd = shutil.which('pip-audit') or str(Path.home() / ".local" / "bin" / "pip-audit")
            if not Path(pip_audit_cmd).exists():
                pip_audit_cmd = 'pip-audit'
            
            cmd = [
                pip_audit_cmd,
                '--format', 'json',
                '--output', str(output_file),
            ]
            
            # Add requirements files
            for req_file in req_files:
                cmd.extend(['--requirement', str(req_file)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=os.environ
            )
            
            # Read results
            if output_file.exists():
                with open(output_file, 'r') as f:
                    audit_data = json.load(f)
            else:
                audit_data = {"vulnerabilities": []}
            
            return {
                "available": True,
                "exit_code": result.returncode,
                "results": audit_data,
                "summary": {
                    "total_vulnerabilities": len(audit_data.get("vulnerabilities", [])),
                    "critical": len([v for v in audit_data.get("vulnerabilities", []) if v.get("severity") == "CRITICAL"]),
                    "high": len([v for v in audit_data.get("vulnerabilities", []) if v.get("severity") == "HIGH"]),
                }
            }
        except Exception as e:
            return {
                "available": True,
                "error": str(e)
            }
    
    def run_all(self) -> Dict[str, Any]:
        """Run all security scans."""
        LOGGER.info("Running security scans...")
        
        results = {
            "bandit": self.run_bandit(),
            "pip_audit": self.run_pip_audit(),
        }
        
        self.results = results
        return results


class ComplexityAnalyzer:
    """Code complexity analysis using radon and mccabe."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[str, Any] = {}
    
    def check_radon_available(self) -> bool:
        """Check if radon is installed."""
        # Check in PATH and common locations
        radon_path = shutil.which('radon')
        if not radon_path:
            # Check in user local bin
            user_bin = Path.home() / ".local" / "bin" / "radon"
            if user_bin.exists():
                return True
            return False
        try:
            subprocess.run([radon_path or 'radon', '--version'], capture_output=True, check=True, env=os.environ)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def run_radon_complexity(self) -> Dict[str, Any]:
        """Run radon complexity analysis."""
        if not self.check_radon_available():
            return {
                "available": False,
                "error": "radon not installed. Install with: pip install radon"
            }
        
        try:
            output_file = self.project_root / "reports" / "radon-complexity.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Find radon executable
            radon_cmd = shutil.which('radon') or str(Path.home() / ".local" / "bin" / "radon")
            if not Path(radon_cmd).exists():
                radon_cmd = 'radon'
            
            cmd = [
                radon_cmd, 'cc',
                str(self.project_root),
                '-j',  # JSON output
                '--min', 'A',  # Minimum complexity to report
                '--exclude', 'tests,venv,env,.venv,node_modules',
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=os.environ
            )
            
            # Parse JSON output
            try:
                complexity_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                complexity_data = {}
            
            # Calculate statistics
            total_functions = 0
            high_complexity = 0  # > 10
            very_high_complexity = 0  # > 20
            
            for file_path, functions in complexity_data.items():
                for func in functions:
                    total_functions += 1
                    complexity = func.get('complexity', 0)
                    if complexity > 20:
                        very_high_complexity += 1
                    elif complexity > 10:
                        high_complexity += 1
            
            # Save results
            with open(output_file, 'w') as f:
                json.dump(complexity_data, f, indent=2)
            
            return {
                "available": True,
                "results": complexity_data,
                "summary": {
                    "total_functions": total_functions,
                    "high_complexity": high_complexity,
                    "very_high_complexity": very_high_complexity,
                }
            }
        except Exception as e:
            return {
                "available": True,
                "error": str(e)
            }
    
    def run_radon_maintainability(self) -> Dict[str, Any]:
        """Run radon maintainability index."""
        if not self.check_radon_available():
            return {
                "available": False,
                "error": "radon not installed"
            }
        
        try:
            output_file = self.project_root / "reports" / "radon-maintainability.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Find radon executable
            radon_cmd = shutil.which('radon') or str(Path.home() / ".local" / "bin" / "radon")
            if not Path(radon_cmd).exists():
                radon_cmd = 'radon'

            cmd = [
                radon_cmd, 'mi',
                str(self.project_root),
                '-j',  # JSON output
                '--min', 'B',  # Minimum maintainability
                '--exclude', 'tests,venv,env,.venv,node_modules',
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=os.environ,
            )
            
            try:
                maintainability_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                maintainability_data = {}
            
            # Save results
            with open(output_file, 'w') as f:
                json.dump(maintainability_data, f, indent=2)
            
            return {
                "available": True,
                "results": maintainability_data,
            }
        except Exception as e:
            return {
                "available": True,
                "error": str(e)
            }
    
    def run_all(self) -> Dict[str, Any]:
        """Run all complexity analyses."""
        LOGGER.info("Running complexity analysis...")
        
        results = {
            "complexity": self.run_radon_complexity(),
            "maintainability": self.run_radon_maintainability(),
        }
        
        self.results = results
        return results


class CodeReviewRunner:
    """Main code review automation runner."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.security_scanner = SecurityScanner(project_root)
        self.complexity_analyzer = ComplexityAnalyzer(project_root)
        
    def run_full_review(self) -> Dict[str, Any]:
        """Run full code review."""
        LOGGER.info("=" * 80)
        LOGGER.info("Advanced Code Review - Full Analysis")
        LOGGER.info("=" * 80)
        
        review_results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "security": {},
            "complexity": {},
        }
        
        # Security scans
        LOGGER.info("\n[1/2] Running security scans...")
        review_results["security"] = self.security_scanner.run_all()
        
        # Complexity analysis
        LOGGER.info("\n[2/2] Running complexity analysis...")
        review_results["complexity"] = self.complexity_analyzer.run_all()
        
        # Save full report
        report_file = self.reports_dir / "full-code-review.json"
        with open(report_file, 'w') as f:
            json.dump(review_results, f, indent=2)
        
        LOGGER.info(f"\nFull report saved to: {report_file}")
        
        # Print summary
        self._print_summary(review_results)
        
        return review_results
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """Print summary of results."""
        LOGGER.info("\n" + "=" * 80)
        LOGGER.info("CODE REVIEW SUMMARY")
        LOGGER.info("=" * 80)
        
        # Security summary
        security = results.get("security", {})
        LOGGER.info("\n🔒 Security Analysis:")
        
        bandit = security.get("bandit", {})
        if bandit.get("available"):
            summary = bandit.get("summary", {})
            LOGGER.info(f"  Bandit:")
            LOGGER.info(f"    High: {summary.get('high_severity', 0)}")
            LOGGER.info(f"    Medium: {summary.get('medium_severity', 0)}")
            LOGGER.info(f"    Low: {summary.get('low_severity', 0)}")
        else:
            LOGGER.info(f"  Bandit: {bandit.get('error', 'Not available')}")
        
        pip_audit = security.get("pip_audit", {})
        if pip_audit.get("available"):
            summary = pip_audit.get("summary", {})
            LOGGER.info(f"  pip-audit:")
            LOGGER.info(f"    Total Vulnerabilities: {summary.get('total_vulnerabilities', 0)}")
            LOGGER.info(f"    Critical: {summary.get('critical', 0)}")
            LOGGER.info(f"    High: {summary.get('high', 0)}")
        else:
            LOGGER.info(f"  pip-audit: {pip_audit.get('error', 'Not available')}")
        
        # Complexity summary
        complexity = results.get("complexity", {})
        LOGGER.info("\n📊 Complexity Analysis:")
        
        comp = complexity.get("complexity", {})
        if comp.get("available"):
            summary = comp.get("summary", {})
            LOGGER.info(f"  Total Functions: {summary.get('total_functions', 0)}")
            LOGGER.info(f"  High Complexity (>10): {summary.get('high_complexity', 0)}")
            LOGGER.info(f"  Very High Complexity (>20): {summary.get('very_high_complexity', 0)}")
        else:
            LOGGER.info(f"  Complexity: {comp.get('error', 'Not available')}")
        
        LOGGER.info("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Advanced Code Review Automation")
    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--security-only',
        action='store_true',
        help='Run only security scans'
    )
    parser.add_argument(
        '--complexity-only',
        action='store_true',
        help='Run only complexity analysis'
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        LOGGER.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    runner = CodeReviewRunner(project_root)
    
    if args.security_only:
        results = runner.security_scanner.run_all()
        print(json.dumps(results, indent=2))
    elif args.complexity_only:
        results = runner.complexity_analyzer.run_all()
        print(json.dumps(results, indent=2))
    else:
        runner.run_full_review()


if __name__ == "__main__":
    main()

