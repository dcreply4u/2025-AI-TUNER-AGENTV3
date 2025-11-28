# Advanced Code Review Guide

This guide explains how to use the advanced code review tools that provide comprehensive analysis beyond basic syntax checking.

---

## Overview

The advanced code review system provides:

1. **Security Scanning (SAST)** - Automated vulnerability detection
2. **Dependency Vulnerability Analysis** - Known CVE scanning
3. **Complexity Analysis** - Code complexity and maintainability metrics
4. **Performance Profiling** - CPU and memory profiling tools
5. **Edge Case Testing** - Property-based testing for edge cases

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:
- `bandit` - Security scanning
- `pip-audit` - Dependency vulnerability scanning
- `radon` - Complexity analysis
- `hypothesis` - Property-based testing
- `memory-profiler` - Memory profiling
- And more...

### 2. Run Full Code Review

**Windows PowerShell:**
```powershell
.\scripts\run_advanced_code_review.ps1
```

**Windows Batch:**
```batch
scripts\run_advanced_code_review.bat
```

**Linux/Mac:**
```bash
python tools/advanced_code_review.py
```

### 3. View Results

Reports are saved to `reports/` directory:
- `bandit-report.json` - Security scan results
- `pip-audit-report.json` - Dependency vulnerabilities
- `radon-complexity.json` - Code complexity metrics
- `radon-maintainability.json` - Maintainability index
- `full-code-review.json` - Complete analysis

---

## Security Scanning

### Bandit (SAST)

Bandit performs static analysis to find common security issues in Python code.

**Run manually:**
```bash
bandit -r . -f json -o reports/bandit-report.json
```

**Common Issues Found:**
- SQL injection vulnerabilities
- Hardcoded passwords
- Insecure random number generation
- Use of `eval()` or `exec()`
- Insecure file operations

**Severity Levels:**
- **HIGH** - Critical security issues (fix immediately)
- **MEDIUM** - Security concerns (fix soon)
- **LOW** - Best practice violations (fix when possible)

### pip-audit

Scans dependencies for known vulnerabilities from the National Vulnerability Database (NVD).

**Run manually:**
```bash
pip-audit --format json --output reports/pip-audit-report.json
```

**What It Checks:**
- Known CVEs in installed packages
- Outdated packages with security fixes
- Vulnerable dependency versions

**Action Items:**
- Update packages with critical vulnerabilities
- Review high-severity CVEs
- Consider alternative packages if no fix available

---

## Complexity Analysis

### Radon Complexity

Measures cyclomatic complexity of functions and methods.

**Run manually:**
```bash
radon cc . -j --min A --exclude tests,venv,env
```

**Complexity Levels:**
- **A (1-5)** - Simple, easy to understand
- **B (6-10)** - Moderate complexity
- **C (11-20)** - High complexity (consider refactoring)
- **D (21-30)** - Very high complexity (refactor recommended)
- **E (31-40)** - Extremely complex (refactor required)
- **F (41+)** - Unmaintainable (must refactor)

**Recommendations:**
- Functions with complexity > 10 should be reviewed
- Functions with complexity > 20 should be refactored
- Break complex functions into smaller, testable units

### Radon Maintainability Index

Measures how maintainable code is (0-100 scale).

**Run manually:**
```bash
radon mi . -j --min B --exclude tests,venv,env
```

**Maintainability Levels:**
- **A (80-100)** - Highly maintainable
- **B (60-79)** - Maintainable
- **C (40-59)** - Moderately maintainable
- **D (20-39)** - Low maintainability
- **E (0-19)** - Very low maintainability

---

## Performance Profiling

### CPU Profiling

Use the `PerformanceProfiler` context manager:

```python
from tools.performance_profiler import PerformanceProfiler
from pathlib import Path

# Profile a code block
with PerformanceProfiler(output_file=Path("reports/profile.txt")):
    # Your code here
    result = expensive_function()
```

### Memory Profiling

Use the `@profile_memory` decorator:

```python
from tools.performance_profiler import profile_memory

@profile_memory
def my_function():
    # Function code
    pass
```

**Run with:**
```bash
python -m memory_profiler script.py
```

### Line-by-Line Profiling

Use the `@profile_line_by_line` decorator:

```python
from tools.performance_profiler import profile_line_by_line

@profile_line_by_line
def my_function():
    # Function code
    pass
```

**Run with:**
```bash
kernprof -l -v script.py
```

---

## Edge Case Testing

### Property-Based Testing with Hypothesis

Automatically generates edge cases to test your functions:

```python
from hypothesis import given, strategies as st
from tools.edge_case_tester import generate_edge_cases_for_numeric_function

@given(value=st.floats(min_value=0, max_value=1000))
def test_my_function(value):
    # Hypothesis will test with edge cases like:
    # - 0, -1, 1, very large numbers, etc.
    result = my_function(value)
    assert result >= 0  # Property to verify
```

### Generate Edge Cases

```python
from tools.edge_case_tester import generate_edge_cases_for_numeric_function

def divide_by_two(x):
    return x / 2

# Find edge cases that cause issues
issues = generate_edge_cases_for_numeric_function(divide_by_two)
# Returns: ["Edge case 0 raised exception: ZeroDivisionError"]
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Advanced Code Review

on: [push, pull_request]

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run security scan
        run: |
          python tools/advanced_code_review.py --security-only
      
      - name: Run complexity analysis
        run: |
          python tools/advanced_code_review.py --complexity-only
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: code-review-reports
          path: reports/
```

---

## Best Practices

### 1. Run Before Commits

Add a pre-commit hook:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python tools/advanced_code_review.py --security-only
if [ $? -ne 0 ]; then
    echo "Security issues found. Please fix before committing."
    exit 1
fi
```

### 2. Regular Reviews

- Run full review weekly
- Run security scan before releases
- Run complexity analysis when refactoring

### 3. Fix Priority

1. **Critical Security Issues** (HIGH severity) - Fix immediately
2. **Dependency Vulnerabilities** (CRITICAL/HIGH) - Update packages
3. **High Complexity** (>20) - Refactor when possible
4. **Medium Security Issues** - Fix in next sprint
5. **Low Complexity** - Fix during code cleanup

---

## Troubleshooting

### Tools Not Found

If tools are not found, install dependencies:
```bash
pip install -r requirements-dev.txt
```

### Permission Errors

On Linux/Mac, you may need:
```bash
chmod +x tools/advanced_code_review.py
```

### Import Errors

Ensure you're in the project root:
```bash
cd 2025-AI-TUNER-AGENTV3
python tools/advanced_code_review.py
```

---

## Advanced Usage

### Custom Configuration

Edit `tools/advanced_code_review.py` to:
- Exclude additional directories
- Change severity thresholds
- Add custom analysis rules

### Extending Analysis

Add new analyzers by:
1. Creating a new analyzer class
2. Adding it to `CodeReviewRunner`
3. Integrating results into the report

---

## Resources

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)
- [Radon Documentation](https://radon.readthedocs.io/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Python Profiling Guide](https://docs.python.org/3/library/profile.html)

---

**Last Updated:** January 2025

