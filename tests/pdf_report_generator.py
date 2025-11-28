"""
PDF Report Generator for Test Results

Generates comprehensive PDF reports from test results.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Try to import reportlab, fallback to basic PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Fallback: try fpdf
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class PDFReportGenerator:
    """Generate PDF reports from test results."""
    
    def __init__(self):
        self.reportlab_available = REPORTLAB_AVAILABLE
        self.fpdf_available = FPDF_AVAILABLE
    
    def generate_report(self, results: Dict[str, Any], output_path: Path) -> bool:
        """
        Generate PDF report from test results.
        
        Args:
            results: Test results dictionary
            output_path: Path to save PDF file
        
        Returns:
            True if generated successfully
        """
        if self.reportlab_available:
            return self._generate_with_reportlab(results, output_path)
        elif self.fpdf_available:
            return self._generate_with_fpdf(results, output_path)
        else:
            # Fallback: create a text file with instructions
            return self._generate_fallback(results, output_path)
    
    def _generate_with_reportlab(self, results: Dict[str, Any], output_path: Path) -> bool:
        """Generate PDF using reportlab."""
        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            story.append(Paragraph("AI TUNER AGENT", title_style))
            story.append(Paragraph("Comprehensive QA Test Report", styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            # Summary
            summary = results.get("summary", {})
            summary_data = [
                ["Metric", "Value"],
                ["Total Modules", f"{summary.get('passed_modules', 0)}/{summary.get('total_modules', 0)} passed"],
                ["Total Tests", f"{summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} passed"],
                ["Failed Tests", str(summary.get('failed_tests', 0))],
                ["Skipped Tests", str(summary.get('skipped_tests', 0))],
                ["Total Time", f"{summary.get('total_time_seconds', 0):.2f} seconds"],
                ["Generated", results.get("generated", datetime.now().isoformat())],
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Module Results
            story.append(Paragraph("Module Results", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            modules = results.get("modules", {})
            module_data = [["Module", "Status", "Tests", "Time (s)"]]
            
            for module_name, module_result in modules.items():
                status = "PASS" if module_result.get("success") else "FAIL"
                tests = f"{module_result.get('tests_passed', 0)}/{module_result.get('tests_run', 0)}"
                elapsed = f"{module_result.get('elapsed', 0):.2f}"
                module_data.append([module_name, status, tests, elapsed])
            
            module_table = Table(module_data, colWidths=[3.5*inch, 1*inch, 1.5*inch, 1*inch])
            module_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(module_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Issues
            issues = results.get("issues", [])
            if issues:
                story.append(Paragraph("Issues Found", styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))
                
                for i, issue in enumerate(issues[:20], 1):  # First 20 issues
                    severity = issue.get("severity", "unknown").upper()
                    category = issue.get("category", "Unknown")
                    description = issue.get("description", "")
                    
                    issue_text = f"<b>{i}. [{severity}] {category}</b><br/>{description}"
                    story.append(Paragraph(issue_text, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF with reportlab: {e}")
            return False
    
    def _generate_with_fpdf(self, results: Dict[str, Any], output_path: Path) -> bool:
        """Generate PDF using fpdf (fallback)."""
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=0.5)
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", "B", 20)
            pdf.cell(0, 10, "AI TUNER AGENT", ln=1, align="C")
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Comprehensive QA Test Report", ln=1, align="C")
            pdf.ln(10)
            
            # Summary
            summary = results.get("summary", {})
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Summary", ln=1)
            pdf.set_font("Arial", "", 12)
            
            pdf.cell(0, 8, f"Total Modules: {summary.get('passed_modules', 0)}/{summary.get('total_modules', 0)} passed", ln=1)
            pdf.cell(0, 8, f"Total Tests: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} passed", ln=1)
            pdf.cell(0, 8, f"Failed: {summary.get('failed_tests', 0)}, Skipped: {summary.get('skipped_tests', 0)}", ln=1)
            pdf.cell(0, 8, f"Total Time: {summary.get('total_time_seconds', 0):.2f} seconds", ln=1)
            pdf.ln(5)
            
            # Module Results
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Module Results", ln=1)
            pdf.set_font("Arial", "", 10)
            
            modules = results.get("modules", {})
            for module_name, module_result in modules.items():
                status = "PASS" if module_result.get("success") else "FAIL"
                tests = f"{module_result.get('tests_passed', 0)}/{module_result.get('tests_run', 0)}"
                elapsed = f"{module_result.get('elapsed', 0):.2f}s"
                pdf.cell(0, 8, f"{module_name}: {status} - {tests} ({elapsed})", ln=1)
            
            pdf.ln(5)
            
            # Issues
            issues = results.get("issues", [])
            if issues:
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Issues Found", ln=1)
                pdf.set_font("Arial", "", 10)
                
                for i, issue in enumerate(issues[:20], 1):
                    severity = issue.get("severity", "unknown").upper()
                    category = issue.get("category", "Unknown")
                    description = issue.get("description", "")
                    pdf.cell(0, 8, f"{i}. [{severity}] {category}: {description}", ln=1)
            
            pdf.output(str(output_path))
            return True
            
        except Exception as e:
            print(f"Error generating PDF with fpdf: {e}")
            return False
    
    def _generate_fallback(self, results: Dict[str, Any], output_path: Path) -> bool:
        """Generate fallback text file with PDF generation instructions."""
        try:
            # Create a text file explaining how to generate PDF
            text_path = output_path.with_suffix('.txt')
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write("PDF REPORT GENERATION\n")
                f.write("="*80 + "\n\n")
                f.write("To generate PDF reports, install one of the following:\n\n")
                f.write("Option 1 (Recommended):\n")
                f.write("  pip install reportlab\n\n")
                f.write("Option 2:\n")
                f.write("  pip install fpdf\n\n")
                f.write("Then re-run the test suite.\n\n")
                f.write("JSON report is available at: test_report.json\n")
                f.write("Text report is available at: test_report.txt\n")
            
            print(f"PDF generation not available. Install 'reportlab' or 'fpdf'.")
            print(f"Fallback instructions saved to: {text_path}")
            return False
            
        except Exception as e:
            print(f"Error creating fallback file: {e}")
            return False

