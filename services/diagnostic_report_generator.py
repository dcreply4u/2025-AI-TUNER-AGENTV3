"""
Diagnostic Report Generator
Generates comprehensive diagnosis and fix reports.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.auto_engine_diagnostic import DiagnosticReport, IssueSeverity

LOGGER = logging.getLogger(__name__)


class DiagnosticReportGenerator:
    """
    Generate diagnostic and fix reports.
    
    Features:
    - HTML reports
    - PDF reports (optional)
    - Text summaries
    - Export capabilities
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize report generator."""
        self.output_dir = output_dir or Path("data/diagnostic_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        report: DiagnosticReport,
        format: str = "html",
        include_fixes: bool = True,
    ) -> str:
        """
        Generate diagnostic report.
        
        Args:
            report: Diagnostic report
            format: Report format (html, text, json)
            include_fixes: Include fix recommendations
        
        Returns:
            Path to generated report file
        """
        if format == "html":
            return self._generate_html_report(report, include_fixes)
        elif format == "text":
            return self._generate_text_report(report, include_fixes)
        elif format == "json":
            return self._generate_json_report(report, include_fixes)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _generate_html_report(
        self,
        report: DiagnosticReport,
        include_fixes: bool,
    ) -> str:
        """Generate HTML report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Engine Diagnostic Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .health-score {{
            font-size: 48px;
            font-weight: bold;
            color: {'#e74c3c' if report.overall_health_score < 50 else '#f39c12' if report.overall_health_score < 75 else '#27ae60'};
            text-align: center;
            margin: 20px 0;
        }}
        .issue {{
            border-left: 4px solid;
            padding: 15px;
            margin: 15px 0;
            background-color: #f8f9fa;
        }}
        .issue.critical {{ border-color: #e74c3c; }}
        .issue.high {{ border-color: #e67e22; }}
        .issue.medium {{ border-color: #f39c12; }}
        .issue.low {{ border-color: #3498db; }}
        .issue.info {{ border-color: #95a5a6; }}
        .fix {{
            background-color: #d5f4e6;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }}
        .fix.auto-apply {{
            background-color: #d1ecf1;
            border-color: #3498db;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .badge.critical {{ background-color: #e74c3c; color: white; }}
        .badge.high {{ background-color: #e67e22; color: white; }}
        .badge.medium {{ background-color: #f39c12; color: white; }}
        .badge.low {{ background-color: #3498db; color: white; }}
        .badge.safe {{ background-color: #27ae60; color: white; }}
        .badge.caution {{ background-color: #f39c12; color: white; }}
        .badge.expert {{ background-color: #e74c3c; color: white; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        .recommendations {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        .recommendations ul {{
            margin: 10px 0;
            padding-left: 25px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Engine Diagnostic Report</h1>
        <p><strong>Generated:</strong> {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Engine Type:</strong> {report.engine_type.title()}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="health-score">{report.overall_health_score:.0f}/100</div>
            <p>{report.summary}</p>
        </div>
        
        <h2>Issues Found ({len(report.issues)})</h2>
"""
        
        # Group issues by severity
        issues_by_severity = {}
        for issue in report.issues:
            severity = issue.severity.value
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)
        
        # Display issues
        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in issues_by_severity:
                for issue in issues_by_severity[severity]:
                    html += f"""
        <div class="issue {severity}">
            <h3>
                <span class="badge {severity}">{severity.upper()}</span>
                {issue.title}
            </h3>
            <p><strong>Description:</strong> {issue.description}</p>
            <p><strong>Category:</strong> {issue.category.value.replace('_', ' ').title()}</p>
            <p><strong>Confidence:</strong> {issue.confidence * 100:.0f}%</p>
            
            <h4>Symptoms:</h4>
            <ul>
"""
                    for symptom in issue.symptoms:
                        html += f"                <li>{symptom}</li>\n"
                    
                    html += """            </ul>
            
            <h4>Possible Causes:</h4>
            <ul>
"""
                    for cause in issue.possible_causes:
                        html += f"                <li>{cause}</li>\n"
                    
                    html += """            </ul>
        </div>
"""
        
        # Fixes section
        if include_fixes and report.fixes:
            html += f"""
        <h2>Recommended Fixes ({len(report.fixes)})</h2>
"""
            for fix in report.fixes:
                auto_class = "auto-apply" if fix.can_auto_apply else ""
                html += f"""
        <div class="fix {auto_class}">
            <h3>
                {fix.title}
                {f'<span class="badge {fix.safety_level}">{fix.safety_level.upper()}</span>' if fix.safety_level else ''}
                {f'<span class="badge safe">AUTO-APPLY</span>' if fix.can_auto_apply else ''}
            </h3>
            <p><strong>Description:</strong> {fix.description}</p>
            <p><strong>Confidence:</strong> {fix.confidence * 100:.0f}%</p>
            {f'<p><strong>Estimated Improvement:</strong> {fix.estimated_improvement}</p>' if fix.estimated_improvement else ''}
            
            {f'''
            <h4>Parameter Changes:</h4>
            <table>
                <tr>
                    <th>Parameter</th>
                    <th>New Value</th>
                </tr>
''' + '\n'.join(f'                <tr><td>{param}</td><td>{value}</td></tr>' for param, value in fix.parameter_changes.items()) + '''
            </table>
''' if fix.parameter_changes else ''}
        </div>
"""
        
        # Recommendations
        if report.recommendations:
            html += """
        <div class="recommendations">
            <h2>Recommendations</h2>
            <ul>
"""
            for rec in report.recommendations:
                html += f"                <li>{rec}</li>\n"
            
            html += """            </ul>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        # Save report
        report_file = self.output_dir / f"diagnostic_report_{report.report_id}.html"
        report_file.write_text(html)
        
        LOGGER.info("Generated HTML report: %s", report_file)
        return str(report_file)
    
    def _generate_text_report(
        self,
        report: DiagnosticReport,
        include_fixes: bool,
    ) -> str:
        """Generate text report."""
        text = f"""
ENGINE DIAGNOSTIC REPORT
{'=' * 50}

Generated: {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
Engine Type: {report.engine_type.title()}

SUMMARY
{'-' * 50}
Health Score: {report.overall_health_score:.0f}/100
{report.summary}

ISSUES FOUND ({len(report.issues)})
{'-' * 50}
"""
        
        for issue in report.issues:
            text += f"""
[{issue.severity.value.upper()}] {issue.title}
  Description: {issue.description}
  Category: {issue.category.value.replace('_', ' ').title()}
  Confidence: {issue.confidence * 100:.0f}%
  Symptoms: {', '.join(issue.symptoms)}
  Possible Causes: {', '.join(issue.possible_causes)}
"""
        
        if include_fixes and report.fixes:
            text += f"""
RECOMMENDED FIXES ({len(report.fixes)})
{'-' * 50}
"""
            for fix in report.fixes:
                text += f"""
{fix.title} {'[AUTO-APPLY]' if fix.can_auto_apply else ''}
  Description: {fix.description}
  Safety Level: {fix.safety_level}
  Confidence: {fix.confidence * 100:.0f}%
"""
                if fix.parameter_changes:
                    text += "  Parameter Changes:\n"
                    for param, value in fix.parameter_changes.items():
                        text += f"    - {param}: {value}\n"
        
        if report.recommendations:
            text += f"""
RECOMMENDATIONS
{'-' * 50}
"""
            for rec in report.recommendations:
                text += f"  - {rec}\n"
        
        # Save report
        report_file = self.output_dir / f"diagnostic_report_{report.report_id}.txt"
        report_file.write_text(text)
        
        LOGGER.info("Generated text report: %s", report_file)
        return str(report_file)
    
    def _generate_json_report(
        self,
        report: DiagnosticReport,
        include_fixes: bool,
    ) -> str:
        """Generate JSON report."""
        import json
        
        data = {
            "report_id": report.report_id,
            "timestamp": report.timestamp,
            "engine_type": report.engine_type,
            "overall_health_score": report.overall_health_score,
            "summary": report.summary,
            "issues": [
                {
                    "issue_id": i.issue_id,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity.value,
                    "category": i.category.value,
                    "confidence": i.confidence,
                    "symptoms": i.symptoms,
                    "possible_causes": i.possible_causes,
                }
                for i in report.issues
            ],
        }
        
        if include_fixes:
            data["fixes"] = [
                {
                    "fix_id": f.fix_id,
                    "issue_id": f.issue_id,
                    "title": f.title,
                    "description": f.description,
                    "parameter_changes": f.parameter_changes,
                    "safety_level": f.safety_level,
                    "can_auto_apply": f.can_auto_apply,
                    "confidence": f.confidence,
                }
                for f in report.fixes
            ]
        
        data["recommendations"] = report.recommendations
        
        # Save report
        report_file = self.output_dir / f"diagnostic_report_{report.report_id}.json"
        report_file.write_text(json.dumps(data, indent=2))
        
        LOGGER.info("Generated JSON report: %s", report_file)
        return str(report_file)

