"""
Beginner-Friendly Diagnostic Module
Simple one-button interface for automatic engine diagnosis and fixes.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QProgressBar, QMessageBox, QGroupBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from services.automatic_engine_diagnostic import AutomaticEngineDiagnostic
from services.auto_fix_engine import AutoFixEngine

LOGGER = logging.getLogger(__name__)


class DiagnosticWorker(QThread):
    """Worker thread for running diagnostics."""
    
    finished = Signal(object)  # Emits DiagnosticReport
    progress = Signal(str)  # Emits progress message
    
    def __init__(
        self,
        telemetry_data: dict,
        current_parameters: dict,
        vehicle_info: Optional[dict] = None,
        is_diesel: bool = False,
    ):
        """Initialize diagnostic worker."""
        super().__init__()
        self.telemetry_data = telemetry_data
        self.current_parameters = current_parameters
        self.vehicle_info = vehicle_info
        self.is_diesel = is_diesel
        self.diagnostic = AutomaticEngineDiagnostic()
    
    def run(self) -> None:
        """Run diagnostics."""
        self.progress.emit("Starting engine diagnosis...")
        
        try:
            report = self.diagnostic.diagnose_engine(
                self.telemetry_data,
                self.current_parameters,
                self.vehicle_info,
                self.is_diesel,
            )
            
            self.finished.emit(report)
        except Exception as e:
            LOGGER.error("Diagnostic failed: %s", e)
            self.progress.emit(f"Error: {str(e)}")


class BeginnerDiagnosticModule(QWidget):
    """
    Beginner-friendly diagnostic module.
    
    Features:
    - One-button diagnosis
    - Automatic fix application
    - Simple, clear reports
    - Progress indication
    """
    
    def __init__(self, parent: Optional[QWidget] = None, ecu_control=None):
        """
        Initialize beginner diagnostic module.
        
        Args:
            parent: Parent widget
            ecu_control: ECU control interface
        """
        super().__init__(parent)
        
        self.ecu_control = ecu_control
        self.diagnostic = AutomaticEngineDiagnostic()
        self.auto_fix = AutoFixEngine(ecu_control)
        
        self.current_report = None
        self.telemetry_provider = None
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Automatic Engine Diagnosis & Fix")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Click the button below to automatically diagnose your engine.\n"
            "The system will detect problems and can automatically apply safe fixes."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Main button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.diagnose_btn = QPushButton("🔍 Diagnose Engine")
        self.diagnose_btn.setMinimumHeight(60)
        self.diagnose_btn.setStyleSheet("""
            QPushButton {
                background-color: #00E0FF;
                color: #0D1117;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #00C0DF;
            }
            QPushButton:pressed {
                background-color: #00A0BF;
            }
        """)
        self.diagnose_btn.clicked.connect(self._run_diagnosis)
        button_layout.addWidget(self.diagnose_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to diagnose")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Results area
        results_group = QGroupBox("Diagnosis Results")
        results_layout = QVBoxLayout()
        
        # Health score
        self.health_label = QLabel("Engine Health: --")
        health_font = QFont()
        health_font.setPointSize(14)
        health_font.setBold(True)
        self.health_label.setFont(health_font)
        self.health_label.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(self.health_label)
        
        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        results_layout.addWidget(QLabel("Summary:"))
        results_layout.addWidget(self.summary_text)
        
        # Problems table
        self.problems_table = QTableWidget()
        self.problems_table.setColumnCount(4)
        self.problems_table.setHorizontalHeaderLabels(["Severity", "Category", "Problem", "Description"])
        self.problems_table.horizontalHeader().setStretchLastSection(True)
        self.problems_table.setMaximumHeight(200)
        results_layout.addWidget(QLabel("Problems Detected:"))
        results_layout.addWidget(self.problems_table)
        
        # Auto-fix button
        self.auto_fix_btn = QPushButton("🔧 Apply Safe Fixes Automatically")
        self.auto_fix_btn.setMinimumHeight(50)
        self.auto_fix_btn.setStyleSheet("""
            QPushButton {
                background-color: #00FF00;
                color: #0D1117;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #00DF00;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.auto_fix_btn.clicked.connect(self._apply_auto_fixes)
        self.auto_fix_btn.setEnabled(False)
        results_layout.addWidget(self.auto_fix_btn)
        
        # Fixes applied table
        self.fixes_table = QTableWidget()
        self.fixes_table.setColumnCount(3)
        self.fixes_table.setHorizontalHeaderLabels(["Parameter", "Old Value", "New Value"])
        self.fixes_table.horizontalHeader().setStretchLastSection(True)
        self.fixes_table.setMaximumHeight(150)
        results_layout.addWidget(QLabel("Fixes Applied:"))
        results_layout.addWidget(self.fixes_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
    
    def set_telemetry_provider(self, provider) -> None:
        """Set telemetry data provider."""
        self.telemetry_provider = provider
    
    def _run_diagnosis(self) -> None:
        """Run engine diagnosis."""
        # Get current telemetry and parameters
        if self.telemetry_provider:
            telemetry = self.telemetry_provider.get_current_telemetry() or {}
            parameters = self.telemetry_provider.get_current_parameters() or {}
        else:
            telemetry = {}
            parameters = {}
        
        # Check if diesel (simplified - would use detector)
        is_diesel = "injection_pressure" in telemetry or "rail_pressure" in telemetry
        
        # Disable button
        self.diagnose_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Diagnosing engine... Please wait.")
        
        # Run in worker thread
        self.worker = DiagnosticWorker(telemetry, parameters, None, is_diesel)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_diagnosis_complete)
        self.worker.start()
    
    def _on_progress(self, message: str) -> None:
        """Handle progress update."""
        self.status_label.setText(message)
    
    def _on_diagnosis_complete(self, report) -> None:
        """Handle diagnosis completion."""
        self.current_report = report
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.diagnose_btn.setEnabled(True)
        self.status_label.setText("Diagnosis complete!")
        
        # Update health score
        health = report.overall_health_score
        if health >= 80:
            color = "#00FF00"
        elif health >= 60:
            color = "#FFFF00"
        else:
            color = "#FF0000"
        
        self.health_label.setText(f"Engine Health: {health:.1f}%")
        self.health_label.setStyleSheet(f"color: {color};")
        
        # Update summary
        self.summary_text.setPlainText(report.summary)
        
        # Update problems table
        self.problems_table.setRowCount(0)
        for problem in report.problems:
            row = self.problems_table.rowCount()
            self.problems_table.insertRow(row)
            
            # Severity
            severity_item = QTableWidgetItem(problem.severity.value.upper())
            if problem.severity.value == "critical":
                severity_item.setForeground(Qt.red)
            elif problem.severity.value == "high":
                severity_item.setForeground(Qt.yellow)
            self.problems_table.setItem(row, 0, severity_item)
            
            # Category
            self.problems_table.setItem(row, 1, QTableWidgetItem(problem.category.value))
            
            # Title
            self.problems_table.setItem(row, 2, QTableWidgetItem(problem.title))
            
            # Description
            self.problems_table.setItem(row, 3, QTableWidgetItem(problem.description))
        
        # Enable auto-fix button if safe fixes available
        self.auto_fix_btn.setEnabled(report.can_auto_fix and len(report.fixes) > 0)
        
        # Show message
        if report.can_auto_fix:
            QMessageBox.information(
                self,
                "Diagnosis Complete",
                f"Found {len(report.problems)} problem(s).\n"
                f"Engine Health: {health:.1f}%\n\n"
                f"{len([f for f in report.fixes if f.safety_level == 'safe'])} safe fix(es) can be applied automatically."
            )
        else:
            QMessageBox.warning(
                self,
                "Diagnosis Complete",
                f"Found {len(report.problems)} problem(s).\n"
                f"Engine Health: {health:.1f}%\n\n"
                "Some fixes require manual review."
            )
    
    def _apply_auto_fixes(self) -> None:
        """Apply automatic fixes."""
        if not self.current_report:
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Apply Fixes",
            f"Apply {len([f for f in self.current_report.fixes if f.safety_level == 'safe'])} safe fix(es)?\n\n"
            "These changes will modify your engine tuning parameters.",
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Apply fixes
        self.status_label.setText("Applying fixes...")
        self.auto_fix_btn.setEnabled(False)
        
        result = self.auto_fix.apply_fixes(
            self.current_report,
            auto_apply_safe=True,
            require_approval=False,  # User already approved
        )
        
        # Update fixes table
        self.fixes_table.setRowCount(0)
        for fix in result.fixes_applied:
            row = self.fixes_table.rowCount()
            self.fixes_table.insertRow(row)
            self.fixes_table.setItem(row, 0, QTableWidgetItem(fix.parameter_name))
            self.fixes_table.setItem(row, 1, QTableWidgetItem(f"{fix.old_value:.2f}"))
            self.fixes_table.setItem(row, 2, QTableWidgetItem(f"{fix.new_value:.2f}"))
        
        # Show result
        self.status_label.setText("Fixes applied!")
        
        QMessageBox.information(
            self,
            "Fixes Applied",
            f"Successfully applied {result.success_count} fix(es).\n\n"
            f"{result.summary}"
        )
        
        # Re-run diagnosis to see improvement
        self._run_diagnosis()


