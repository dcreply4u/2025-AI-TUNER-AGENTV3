"""
Test Issues Reporter

Collects and reports all issues found during testing.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class TestIssue:
    """Represents a test issue."""
    category: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    test_name: str
    expected: str
    actual: str
    file: str = ""
    line: int = 0


class IssuesReporter:
    """Collects and reports test issues."""
    
    def __init__(self):
        self.issues: List[TestIssue] = []
    
    def add_issue(
        self,
        category: str,
        severity: str,
        description: str,
        test_name: str,
        expected: str,
        actual: str,
        file: str = "",
        line: int = 0,
    ):
        """Add an issue to the report."""
        issue = TestIssue(
            category=category,
            severity=severity,
            description=description,
            test_name=test_name,
            expected=expected,
            actual=actual,
            file=file,
            line=line,
        )
        self.issues.append(issue)
    
    def get_issues_by_severity(self, severity: str) -> List[TestIssue]:
        """Get issues by severity."""
        return [i for i in self.issues if i.severity == severity]
    
    def generate_report(self, output_file: Path) -> None:
        """Generate issues report."""
        report = {
            "generated": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "by_severity": {
                "critical": len(self.get_issues_by_severity("critical")),
                "high": len(self.get_issues_by_severity("high")),
                "medium": len(self.get_issues_by_severity("medium")),
                "low": len(self.get_issues_by_severity("low")),
            },
            "issues": [asdict(issue) for issue in self.issues],
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    def print_summary(self) -> None:
        """Print issues summary."""
        print("\n" + "="*80)
        print("TEST ISSUES SUMMARY")
        print("="*80)
        
        if not self.issues:
            print("✓ No issues found!")
            return
        
        print(f"\nTotal Issues: {len(self.issues)}")
        print(f"  Critical: {len(self.get_issues_by_severity('critical'))}")
        print(f"  High: {len(self.get_issues_by_severity('high'))}")
        print(f"  Medium: {len(self.get_issues_by_severity('medium'))}")
        print(f"  Low: {len(self.get_issues_by_severity('low'))}")
        
        # Group by category
        by_category = {}
        for issue in self.issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
        
        print("\nIssues by Category:")
        for category, issues in sorted(by_category.items()):
            print(f"  {category}: {len(issues)}")
        
        # Show critical issues
        critical = self.get_issues_by_severity("critical")
        if critical:
            print("\n🔴 CRITICAL ISSUES:")
            for issue in critical:
                print(f"  - {issue.description}")
                print(f"    Test: {issue.test_name}")
                print(f"    Expected: {issue.expected}")
                print(f"    Actual: {issue.actual}")
        
        # Show high priority issues
        high = self.get_issues_by_severity("high")
        if high:
            print("\n⚠️  HIGH PRIORITY ISSUES:")
            for issue in high[:10]:  # Show first 10
                print(f"  - {issue.description} ({issue.test_name})")


# Global reporter instance
_reporter = IssuesReporter()


def get_reporter() -> IssuesReporter:
    """Get the global issues reporter."""
    return _reporter

