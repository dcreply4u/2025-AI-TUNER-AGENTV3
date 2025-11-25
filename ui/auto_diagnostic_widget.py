"""
Automatic Engine Diagnostic Widget
Beginner-friendly UI for automatic engine diagnosis and fixes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QProgressBar, QGroupBox, QMessageBox, QFileDialog,
    QScrollArea, QFrame,
)

from services.auto_engine_diagnostic import AutoEngineDiagnostic, DiagnosticReport
from services.auto_fix_engine import AutoFixEngine
from services.diagnostic_report_generator import DiagnosticReportGenerator
from services.diesel_engine_detector import DieselEngineDetector

LOGGER = logging.getLogger(__name__)


class DiagnosticWorker(QThread):
    """Worker thread for running diagnostics."""
    
    finished = Signal(DiagnosticReport)
    error = Signal(str)
    
    def __init__(
        self,
        telemetry_data: Dict[str, Any],
        vehicle_info: Optional[Dict[str, Any]] = None,
        is_diesel: bool = False,
    ):
        """Initialize diagnostic worker."""
        super().__init__()
        self.telemetry_data = telemetry_data
        self.vehicle_info = vehicle_info
        self.is_diesel = is_diesel
    
    def run(self) -> None:
        """Run diagnostics."""
        try:
            diagnostic = AutoEngineDiagnostic()
            report = diagnostic.diagnose_engine(
                self.telemetry_data,
                self.vehicle_info,
                self.is_diesel,
            )
            self.finished.emit(report)
        except Exception as e:
            LOGGER.error("Diagnostic error: %s", e, exc_info=True)
            self.error.emit(str(e))


class AutoDiagnosticWidget(QWidget):
    """
    Beginner-friendly automatic engine diagnostic widget.
    
    Features:
    - One-click diagnosis
    - Automatic fix application
    - Clear, simple interface
    - Report generation
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize diagnostic widget."""
        super().__init__(parent)
        self.diagnostic = AutoEngineDiagnostic()
        self.auto_fix = AutoFixEngine()
        self.report_generator = DiagnosticReportGenerator()
        self.diesel_detector = DieselEngineDetector()
        
        self.current_report: Optional[DiagnosticReport] = None
        self.current_telemetry: Dict[str, Any] = {}
        self.is_diesel = False
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Automatic Engine Diagnostic")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Automatically diagnose your engine and apply safe fixes. "
            "Perfect for beginners - just click the button below!"
        )
        desc.setStyleSheet("""
            font-size: 14px;
            color: #555;
            padding: 10px;
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Main button
        self.diagnose_btn = QPushButton("🔍 Diagnose Engine")
        self.diagnose_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.diagnose_btn.clicked.connect(self._run_diagnosis)
        layout.addWidget(self.diagnose_btn)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)
        
        # Status label
        self.status_label = QLabel("Ready to diagnose")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            padding: 5px;
        """)
        layout.addWidget(self.status_label)
        
        # Results area
        results_group = QGroupBox("Diagnostic Results")
        results_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        results_layout = QVBoxLayout()
        
        # Health score
        self.health_score_label = QLabel()
        self.health_score_label.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #27ae60;
            text-align: center;
            padding: 20px;
        """)
        self.health_score_label.setVisible(False)
        results_layout.addWidget(self.health_score_label)
        
        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: #ecf0f1;
            }
        """)
        self.summary_text.setVisible(False)
        results_layout.addWidget(self.summary_text)
        
        # Auto-fix button
        self.auto_fix_btn = QPushButton("✅ Apply Automatic Fixes")
        self.auto_fix_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.auto_fix_btn.clicked.connect(self._apply_auto_fixes)
        self.auto_fix_btn.setVisible(False)
        results_layout.addWidget(self.auto_fix_btn)
        
        # Issues scroll area
        self.issues_scroll = QScrollArea()
        self.issues_scroll.setWidgetResizable(True)
        self.issues_scroll.setVisible(False)
        self.issues_widget = QWidget()
        self.issues_layout = QVBoxLayout(self.issues_widget)
        self.issues_scroll.setWidget(self.issues_widget)
        results_layout.addWidget(self.issues_scroll)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.view_report_btn = QPushButton("📄 View Full Report")
        self.view_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        self.view_report_btn.clicked.connect(self._view_report)
        self.view_report_btn.setVisible(False)
        actions_layout.addWidget(self.view_report_btn)
        
        self.export_report_btn = QPushButton("💾 Export Report")
        self.export_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        self.export_report_btn.clicked.connect(self._export_report)
        self.export_report_btn.setVisible(False)
        actions_layout.addWidget(self.export_report_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Graphing section
        graph_group = QGroupBox("Data Visualization")
        graph_layout = QVBoxLayout()
        
        try:
            from ui.advanced_log_graphing import AdvancedLogGraphingWidget
            self.diag_graph = AdvancedLogGraphingWidget()
            graph_layout.addWidget(self.diag_graph, stretch=1)
        except ImportError:
            try:
                from ui.ecu_tuning_widgets import RealTimeGraph
                self.diag_graph = RealTimeGraph()
                graph_layout.addWidget(self.diag_graph, stretch=1)
            except ImportError:
                graph_placeholder = QLabel("Graphing not available")
                graph_placeholder.setStyleSheet("color: #555; padding: 20px;")
                graph_layout.addWidget(graph_placeholder)
                self.diag_graph = None
        
        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)
        
        # Import button
        import_btn = QPushButton("📥 Import Diagnostic Data")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        import_btn.clicked.connect(self._import_diagnostic_data)
        layout.addWidget(import_btn)
        
        layout.addStretch()
    
    def set_telemetry_data(self, telemetry: Dict[str, Any]) -> None:
        """Set current telemetry data."""
        self.current_telemetry = telemetry
        
        # Auto-detect diesel
        detection_result = self.diesel_detector.detect_engine(telemetry)
        self.is_diesel = detection_result.is_diesel
        
        # Update graph if available
        if hasattr(self, 'diag_graph') and self.diag_graph:
            try:
                if hasattr(self.diag_graph, 'update_data'):
                    self.diag_graph.update_data(telemetry)
                elif hasattr(self.diag_graph, 'add_data'):
                    for key, value in telemetry.items():
                        self.diag_graph.add_data(key, value)
            except Exception:
                pass
    
    def _run_diagnosis(self) -> None:
        """Run engine diagnosis."""
        if not self.current_telemetry:
            QMessageBox.warning(
                self,
                "No Data",
                "No telemetry data available. Please connect to your vehicle first.",
            )
            return
        
        # Disable button and show progress
        self.diagnose_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Running diagnostics...")
        
        # Run in worker thread
        self.worker = DiagnosticWorker(
            self.current_telemetry,
            None,
            self.is_diesel,
        )
        self.worker.finished.connect(self._on_diagnosis_complete)
        self.worker.error.connect(self._on_diagnosis_error)
        self.worker.start()
    
    def _on_diagnosis_complete(self, report: DiagnosticReport) -> None:
        """Handle diagnosis completion."""
        self.current_report = report
        
        # Hide progress
        self.progress.setVisible(False)
        self.diagnose_btn.setEnabled(True)
        
        # Update UI
        self._display_results(report)
        
        self.status_label.setText(f"Diagnosis complete! Found {len(report.issues)} issue(s)")
    
    def _on_diagnosis_error(self, error_msg: str) -> None:
        """Handle diagnosis error."""
        self.progress.setVisible(False)
        self.diagnose_btn.setEnabled(True)
        self.status_label.setText("Diagnosis failed")
        
        QMessageBox.critical(
            self,
            "Diagnosis Error",
            f"An error occurred during diagnosis:\n{error_msg}",
        )
    
    def _display_results(self, report: DiagnosticReport) -> None:
        """Display diagnostic results."""
        # Health score
        score = report.overall_health_score
        color = "#e74c3c" if score < 50 else "#f39c12" if score < 75 else "#27ae60"
        self.health_score_label.setText(f"{score:.0f}/100")
        self.health_score_label.setStyleSheet(f"""
            font-size: 48px;
            font-weight: bold;
            color: {color};
            text-align: center;
            padding: 20px;
        """)
        self.health_score_label.setVisible(True)
        
        # Summary
        self.summary_text.setPlainText(report.summary)
        self.summary_text.setVisible(True)
        
        # Auto-fix button
        if report.can_auto_fix:
            self.auto_fix_btn.setText(f"✅ Apply {report.auto_fix_count} Automatic Fix(es)")
            self.auto_fix_btn.setVisible(True)
        else:
            self.auto_fix_btn.setVisible(False)
        
        # Issues
        self._display_issues(report)
        
        # Action buttons
        self.view_report_btn.setVisible(True)
        self.export_report_btn.setVisible(True)
    
    def _display_issues(self, report: DiagnosticReport) -> None:
        """Display issues."""
        # Clear existing
        while self.issues_layout.count():
            child = self.issues_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not report.issues:
            no_issues = QLabel("✅ No issues found! Your engine is running well.")
            no_issues.setStyleSheet("""
                font-size: 16px;
                color: #27ae60;
                padding: 20px;
                text-align: center;
            """)
            self.issues_layout.addWidget(no_issues)
        else:
            for issue in report.issues:
                issue_widget = self._create_issue_widget(issue)
                self.issues_layout.addWidget(issue_widget)
        
        self.issues_scroll.setVisible(True)
    
    def _create_issue_widget(self, issue) -> QWidget:
        """Create widget for an issue."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        
        severity_colors = {
            "critical": "#e74c3c",
            "high": "#e67e22",
            "medium": "#f39c12",
            "low": "#3498db",
            "info": "#95a5a6",
        }
        color = severity_colors.get(issue.severity.value, "#95a5a6")
        
        frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 10px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        
        # Title
        title = QLabel(f"[{issue.severity.value.upper()}] {issue.title}")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(issue.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(desc)
        
        # Symptoms
        if issue.symptoms:
            symptoms_text = "Symptoms: " + ", ".join(issue.symptoms)
            symptoms = QLabel(symptoms_text)
            symptoms.setStyleSheet("font-size: 12px; color: #555; font-style: italic;")
            layout.addWidget(symptoms)
        
        return frame
    
    def _apply_auto_fixes(self) -> None:
        """Apply automatic fixes."""
        if not self.current_report:
            return
        
        reply = QMessageBox.question(
            self,
            "Apply Automatic Fixes",
            f"Apply {self.current_report.auto_fix_count} automatic fix(es)?\n\n"
            "This will modify your engine tuning parameters. "
            "A backup will be created automatically.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Apply fixes
        result = self.auto_fix.apply_fixes(self.current_report, auto_apply_safe=True)
        
        if result["success"]:
            QMessageBox.information(
                self,
                "Fixes Applied",
                f"Successfully applied {result['applied_count']} fix(es).\n\n"
                "Your engine should now run better!",
            )
            self.status_label.setText(f"Applied {result['applied_count']} fix(es)")
        else:
            QMessageBox.warning(
                self,
                "Fix Application Failed",
                result.get("message", "Failed to apply fixes"),
            )
    
    def _view_report(self) -> None:
        """View full diagnostic report."""
        if not self.current_report:
            return
        
        # Generate HTML report
        report_path = self.report_generator.generate_report(
            self.current_report,
            format="html",
            include_fixes=True,
        )
        
        # Open in default browser
        import webbrowser
        import os
        webbrowser.open(f"file://{os.path.abspath(report_path)}")
    
    def _export_report(self) -> None:
        """Export diagnostic report."""
        if not self.current_report:
            return
        
        # Ask for format
        formats = ["HTML", "Text", "JSON"]
        format_choice, ok = QMessageBox.getItem(
            self,
            "Export Report",
            "Select export format:",
            formats,
            0,
            False,
        )
        
        if not ok:
            return
        
        # Ask for location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            f"diagnostic_report_{self.current_report.report_id}",
            f"{format_choice} Files (*.{format_choice.lower()})",
        )
        
        if not file_path:
            return
        
        # Generate report
        format_map = {"HTML": "html", "Text": "text", "JSON": "json"}
        report_path = self.report_generator.generate_report(
            self.current_report,
            format=format_map[format_choice],
            include_fixes=True,
        )
        
        # Copy to user's chosen location
        import shutil
        shutil.copy(report_path, file_path)
        
        QMessageBox.information(
            self,
            "Report Exported",
            f"Report exported to:\n{file_path}",
        )
    
    def _import_diagnostic_data(self) -> None:
        """Import diagnostic data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Diagnostic Data",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            QMessageBox.information(
                self,
                "Import",
                f"Importing diagnostic data from:\n{file_path}",
            )

