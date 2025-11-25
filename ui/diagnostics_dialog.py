"""
Diagnostics Dialog

Provides a UI for running system diagnostics and viewing results.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QProgressBar,
    QTreeWidget,
    QTreeWidgetItem,
)

from core.logging_config import get_logger
from core.troubleshooter import DiagnosticLevel, Troubleshooter

LOGGER = get_logger(__name__)


class DiagnosticsWorker(QThread):
    """Worker thread for running diagnostics."""
    
    finished = Signal(object)  # SystemDiagnostics
    progress = Signal(str)
    
    def __init__(self, level: DiagnosticLevel) -> None:
        """Initialize worker."""
        super().__init__()
        self.level = level
        self.troubleshooter = Troubleshooter()
    
    def run(self) -> None:
        """Run diagnostics."""
        self.progress.emit("Starting diagnostics...")
        diagnostics = self.troubleshooter.run_diagnostics(self.level)
        self.finished.emit(diagnostics)


class DiagnosticsDialog(QDialog):
    """Dialog for running and viewing system diagnostics."""
    
    def __init__(self, parent=None) -> None:
        """Initialize diagnostics dialog."""
        super().__init__(parent)
        self.setWindowTitle("System Diagnostics")
        self.setMinimumSize(800, 600)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.run_quick_btn = QPushButton("Run Quick Diagnostics")
        self.run_quick_btn.clicked.connect(lambda: self._run_diagnostics(DiagnosticLevel.QUICK))
        controls_layout.addWidget(self.run_quick_btn)
        
        self.run_standard_btn = QPushButton("Run Standard Diagnostics")
        self.run_standard_btn.clicked.connect(lambda: self._run_diagnostics(DiagnosticLevel.STANDARD))
        controls_layout.addWidget(self.run_standard_btn)
        
        self.run_comprehensive_btn = QPushButton("Run Comprehensive Diagnostics")
        self.run_comprehensive_btn.clicked.connect(lambda: self._run_diagnostics(DiagnosticLevel.COMPREHENSIVE))
        controls_layout.addWidget(self.run_comprehensive_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results tree
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Check", "Status", "Message", "Details"])
        self.results_tree.setColumnWidth(0, 200)
        self.results_tree.setColumnWidth(1, 80)
        self.results_tree.setColumnWidth(2, 300)
        layout.addWidget(self.results_tree)
        
        # Summary
        summary_layout = QHBoxLayout()
        self.summary_label = QLabel("Click a button above to run diagnostics")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _run_diagnostics(self, level: DiagnosticLevel) -> None:
        """Run diagnostics in background thread."""
        # Disable buttons
        self.run_quick_btn.setEnabled(False)
        self.run_standard_btn.setEnabled(False)
        self.run_comprehensive_btn.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Clear previous results
        self.results_tree.clear()
        
        # Create and start worker
        self.worker = DiagnosticsWorker(level)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_diagnostics_complete)
        self.worker.start()
    
    def _on_progress(self, message: str) -> None:
        """Handle progress update."""
        self.summary_label.setText(message)
    
    def _on_diagnostics_complete(self, diagnostics) -> None:
        """Handle diagnostics completion."""
        # Hide progress
        self.progress_bar.setVisible(False)
        
        # Re-enable buttons
        self.run_quick_btn.setEnabled(True)
        self.run_standard_btn.setEnabled(True)
        self.run_comprehensive_btn.setEnabled(True)
        
        # Populate results
        self.results_tree.clear()
        
        for check in diagnostics.checks:
            item = QTreeWidgetItem([
                check.name,
                check.status.value.upper(),
                check.message,
                f"{check.duration_ms:.2f}ms"
            ])
            
            # Color code status
            if check.status.value == "pass":
                item.setForeground(1, Qt.GlobalColor.green)
            elif check.status.value == "warning":
                item.setForeground(1, Qt.GlobalColor.yellow)
            elif check.status.value == "fail":
                item.setForeground(1, Qt.GlobalColor.red)
            
            # Add details as child items
            if check.details:
                for key, value in check.details.items():
                    detail_item = QTreeWidgetItem([key, "", str(value), ""])
                    item.addChild(detail_item)
            
            self.results_tree.addTopLevelItem(item)
        
        # Expand all
        self.results_tree.expandAll()
        
        # Update summary
        summary = diagnostics.summary
        self.summary_label.setText(
            f"Diagnostics Complete: {summary['passed']} passed, "
            f"{summary['warnings']} warnings, {summary['failed']} failed "
            f"({summary['total']} total checks)"
        )
    
    def closeEvent(self, event) -> None:
        """Clean up on close."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        super().closeEvent(event)


__all__ = ["DiagnosticsDialog"]

