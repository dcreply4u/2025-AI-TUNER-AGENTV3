"""
Console Log Viewer Widget

Displays console output and errors in the GUI for debugging.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConsoleLogViewer(QDialog):
    """Dialog widget for viewing console logs and errors."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize console log viewer."""
        super().__init__(parent)
        self.setWindowTitle("Console Log Viewer")
        self.resize(900, 600)
        
        # Log file paths
        self.log_files = {
            "Demo Log": Path("logs/demo.log"),
            "Error Log": Path("logs/demo_errors.log"),
            "Main Log": Path("logs/ai_tuner.log"),
            "Crash Logs": Path("logs/crashes/crashes.json"),
        }
        
        # Current log file
        self.current_log_file: Optional[Path] = None
        
        # Setup UI
        self._setup_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_log)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
        
        # Load initial log
        self._load_log("Demo Log")

    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Console Log Viewer")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header.addWidget(title)
        header.addStretch()
        
        # Log file selector buttons
        self.log_buttons = {}
        for log_name in self.log_files.keys():
            btn = QPushButton(log_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=log_name: self._load_log(name))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    background-color: #ecf0f1;
                }
                QPushButton:checked {
                    background-color: #3498db;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #d5dbdb;
                }
            """)
            self.log_buttons[log_name] = btn
            header.addWidget(btn)
        
        layout.addLayout(header)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 11px; color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFontFamily("Consolas")
        self.log_display.setFontPointSize(9)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_display)
        
        # Control buttons
        controls = QHBoxLayout()
        controls.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_log)
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_log)
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        controls.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        controls.addWidget(close_btn)
        
        layout.addLayout(controls)

    def _load_log(self, log_name: str) -> None:
        """Load a log file."""
        if log_name not in self.log_files:
            return
        
        # Update button states
        for name, btn in self.log_buttons.items():
            btn.setChecked(name == log_name)
        
        self.current_log_file = self.log_files[log_name]
        self._refresh_log()

    def _refresh_log(self) -> None:
        """Refresh the log display."""
        if not self.current_log_file:
            return
        
        try:
            if not self.current_log_file.exists():
                self.log_display.setPlainText(
                    f"Log file not found: {self.current_log_file}\n\n"
                    f"File will be created when logging starts."
                )
                self.status_label.setText(f"File not found: {self.current_log_file.name}")
                return
            
            # Read log file
            with open(self.current_log_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Display content (show last 50000 characters to avoid performance issues)
            if len(content) > 50000:
                content = "..." + content[-50000:]
                self.status_label.setText(
                    f"Showing last 50KB of {self.current_log_file.name} "
                    f"({datetime.now().strftime('%H:%M:%S')})"
                )
            else:
                self.status_label.setText(
                    f"{self.current_log_file.name} ({datetime.now().strftime('%H:%M:%S')})"
                )
            
            # Apply syntax highlighting for errors
            html_content = self._format_log_content(content)
            self.log_display.setHtml(html_content)
            
            # Auto-scroll to bottom
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            self.log_display.setPlainText(f"Error reading log file: {e}")
            self.status_label.setText(f"Error: {e}")

    def _format_log_content(self, content: str) -> str:
        """Format log content with HTML highlighting."""
        # Escape HTML
        import html
        content = html.escape(content)
        
        # Highlight error patterns
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            formatted_line = line
            
            # Highlight ERROR lines
            if '[ERROR]' in line or 'ERROR:' in line or 'Error:' in line:
                formatted_line = f'<span style="color: #e74c3c; font-weight: bold;">{line}</span>'
            # Highlight WARNING lines
            elif '[WARN]' in line or 'WARNING:' in line or 'Warning:' in line:
                formatted_line = f'<span style="color: #f39c12;">{line}</span>'
            # Highlight INFO lines
            elif '[INFO]' in line or '[OK]' in line:
                formatted_line = f'<span style="color: #2ecc71;">{line}</span>'
            # Highlight DEBUG lines
            elif '[DEBUG]' in line:
                formatted_line = f'<span style="color: #3498db;">{line}</span>'
            # Highlight traceback
            elif 'Traceback' in line or 'File "' in line or 'line ' in line:
                formatted_line = f'<span style="color: #e67e22;">{line}</span>'
            else:
                formatted_line = f'<span style="color: #ecf0f1;">{line}</span>'
            
            formatted_lines.append(formatted_line)
        
        return '<pre style="margin: 0; font-family: Consolas, monospace;">' + '\n'.join(formatted_lines) + '</pre>'

    def _clear_log(self) -> None:
        """Clear the log display."""
        self.log_display.clear()
        self.status_label.setText("Log cleared")

    def closeEvent(self, event) -> None:  # noqa: N802
        """Handle close event."""
        if self.refresh_timer:
            self.refresh_timer.stop()
        super().closeEvent(event)


__all__ = ["ConsoleLogViewer"]





