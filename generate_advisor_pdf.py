#!/usr/bin/env python3
"""
Generate PDF Report from Advisor Test Results

Reads advisor_test_results.json and generates a PDF report.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from tests.pdf_report_generator import PDFReportGenerator
except ImportError:
    print("Error: Could not import PDF generator")
    sys.exit(1)

# Read JSON results
json_path = project_root / "advisor_test_results.json"
if not json_path.exists():
    print(f"Error: Results file not found: {json_path}")
    sys.exit(1)

print(f"Reading results from: {json_path}")
with open(json_path, 'r', encoding='utf-8') as f:
    test_results = json.load(f)

# Convert to PDF format
pdf_results = {
    "test_name": test_results.get("test_name", "AI Advisor Test"),
    "generated": test_results.get("timestamp", datetime.now().isoformat()),
    "summary": test_results.get("summary", {}),
    "modules": [{
        "name": "AI Advisor Knowledge Base",
        "passed": test_results["summary"].get("successful", 0),
        "failed": test_results["summary"].get("failed", 0),
        "skipped": 0,
        "total": test_results["summary"].get("total_questions", 0),
        "tests": [
            {
                "name": r.get("question", "Unknown"),
                "status": "passed" if "error" not in r else "failed",
                "message": r.get("status", ""),
                "details": {
                    "confidence": r.get("confidence", 0.0),
                    "response_time": r.get("response_time", 0.0),
                    "answer_length": r.get("answer_length", 0),
                    "error": r.get("error", None),
                    "expected_topic": r.get("expected_topic", "")
                }
            } for r in test_results.get("questions", [])
        ]
    }]
}

# Generate PDF
pdf_gen = PDFReportGenerator()
pdf_path = project_root / "advisor_test_report.pdf"

print(f"Generating PDF report: {pdf_path}")
if pdf_gen.generate_report(pdf_results, pdf_path):
    print(f"✓ PDF report generated successfully: {pdf_path}")
else:
    print("✗ PDF generation failed")
    sys.exit(1)

