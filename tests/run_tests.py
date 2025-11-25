"""
Test runner script.

Run all tests with: python -m pytest tests/
Or use this script: python tests/run_tests.py
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run all tests."""
    test_dir = Path(__file__).parent
    project_root = test_dir.parent

    # Run pytest
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(test_dir),
            "-v",
            "--tb=short",
            "--cov=AI-TUNER-AGENT",
            "--cov-report=html",
            "--cov-report=term",
        ],
        cwd=str(project_root),
    )

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())

