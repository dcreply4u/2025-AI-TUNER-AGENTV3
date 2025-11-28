"""
Development Log Viewer Tab
Real-time log viewer for development purposes only.

This tab is only visible when:
- AITUNER_DEMO_MODE environment variable is set
- Or AITUNER_DEV_MODE environment variable is set
- Or running from demo_safe.py
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QSpinBox,
    QFileDialog,
    QMessageBox,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

LOGGER = logging.getLogger(__name__)


class LogHandler(QObject, logging.Handler):
    """Custom logging handler that emits signals for Qt."""
    
    log_record = Signal(str, str, str)  # message, level, timestamp
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        QObject.__init__(self, parent)
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record as signal."""
        try:
            msg = self.format(record)
            level = record.levelname
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            self.log_record.emit(msg, level, timestamp)
        except Exception:
            self.handleError(record)


class LogFileReader(QThread):
    """Thread for reading log files in real-time."""
    
    log_line = Signal(str, str, str)  # line, level, timestamp
    
    def __init__(self, log_file: Path, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.log_file = log_file
        self.running = False
        self.last_position = 0
        
    def run(self) -> None:
        """Read log file and emit new lines."""
        self.running = True
        
        while self.running:
            try:
                if not self.log_file.exists():
                    self.msleep(1000)
                    continue
                
                with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()
                    
                    for line in new_lines:
                        if line.strip():
                            # Try to extract level and timestamp
                            level = "INFO"
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            
                            # Parse log line
                            if '[DEBUG]' in line:
                                level = "DEBUG"
                            elif '[INFO]' in line or '[OK]' in line:
                                level = "INFO"
                            elif '[WARN]' in line or '[WARNING]' in line:
                                level = "WARNING"
                            elif '[ERROR]' in line or '[FATAL]' in line:
                                level = "ERROR"
                            
                            self.log_line.emit(line.strip(), level, timestamp)
                
                self.msleep(100)  # Check every 100ms
                
            except Exception as e:
                LOGGER.error(f"Error reading log file: {e}")
                self.msleep(1000)
    
    def stop(self) -> None:
        """Stop reading."""
        self.running = False


class DevLogViewerTab(QWidget):
    """Development-only log viewer tab with real-time updates."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Check if this is development mode
        self.is_dev_mode = self._check_dev_mode()
        if not self.is_dev_mode:
            # Hide tab if not in dev mode
            self.setVisible(False)
            return
        
        self.log_handler: Optional[LogHandler] = None
        self.log_file_reader: Optional[LogFileReader] = None
        self.log_file_path: Optional[Path] = None
        
        # Log level colors
        self.level_colors = {
            "DEBUG": QColor(128, 128, 128),
            "INFO": QColor(255, 255, 255),
            "WARNING": QColor(255, 200, 0),
            "ERROR": QColor(255, 0, 0),
            "CRITICAL": QColor(255, 0, 128),
        }
        
        self.setup_ui()
        self._setup_logging()
        
    def _check_dev_mode(self) -> bool:
        """Check if we're in development mode."""
        # Check environment variables
        if os.getenv("AITUNER_DEMO_MODE") == "true":
            return True
        if os.getenv("AITUNER_DEV_MODE") == "true":
            return True
        
        # Check if running from demo_safe.py
        if "demo_safe" in sys.argv[0] or "demo_safe.py" in str(Path(sys.argv[0]).name):
            return True
        
        # Check if __file__ contains demo_safe
        try:
            if "demo_safe" in str(Path(__file__).parent):
                return True
        except Exception:
            pass
        
        return False
    
    def setup_ui(self) -> None:
        """Setup log viewer UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Warning banner
        warning_banner = QLabel("⚠️ DEVELOPMENT MODE ONLY - This tab is for development purposes")
        warning_banner.setStyleSheet("""
            QLabel {
                background-color: #ffaa00;
                color: #000000;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(warning_banner)
        
        # Top controls
        controls = self._create_controls()
        main_layout.addWidget(controls)
        
        # Log display
        log_display = self._create_log_display()
        main_layout.addWidget(log_display, stretch=1)
        
        # Status bar
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)
        
    def _create_controls(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.auto_scroll_cb)
        
        # Log level filter
        layout.addWidget(QLabel("Filter:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("ALL")
        self.level_filter.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 3px;")
        layout.addWidget(self.level_filter)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 15px;")
        clear_btn.clicked.connect(self._clear_logs)
        layout.addWidget(clear_btn)
        
        # Load log file button
        load_file_btn = QPushButton("Load Log File")
        load_file_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 5px 15px;")
        load_file_btn.clicked.connect(self._load_log_file)
        layout.addWidget(load_file_btn)
        
        layout.addStretch()
        
        # Max lines
        layout.addWidget(QLabel("Max lines:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 10000)
        self.max_lines_spin.setValue(1000)
        self.max_lines_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 3px;")
        layout.addWidget(self.max_lines_spin)
        
        return bar
        
    def _create_log_display(self) -> QWidget:
        """Create log display widget."""
        group = QGroupBox("Real-Time Logs")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(self.log_text, stretch=1)
        
        return group
        
    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.line_count_label = QLabel("Lines: 0")
        self.line_count_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        layout.addWidget(self.line_count_label)
        
        return bar
        
    def _setup_logging(self) -> None:
        """Setup real-time logging."""
        # Add custom handler to root logger
        self.log_handler = LogHandler(self)
        self.log_handler.log_record.connect(self._on_log_record)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
        # Try to find and monitor log file
        log_file = Path("logs/demo.log")
        if not log_file.exists():
            log_file = Path("logs/app.log")
        if not log_file.exists():
            log_file = Path("logs/application.log")
        
        if log_file.exists():
            self.log_file_path = log_file
            self._start_file_reader()
            self.status_label.setText(f"Monitoring: {log_file.name}")
        else:
            self.status_label.setText("Monitoring: Live logs only (no log file found)")
    
    def _start_file_reader(self) -> None:
        """Start reading log file."""
        if not self.log_file_path or not self.log_file_path.exists():
            return
        
        if self.log_file_reader:
            self.log_file_reader.stop()
            self.log_file_reader.wait()
        
        self.log_file_reader = LogFileReader(self.log_file_path)
        self.log_file_reader.log_line.connect(self._on_log_line)
        self.log_file_reader.start()
    
    def _on_log_record(self, message: str, level: str, timestamp: str) -> None:
        """Handle log record from handler."""
        self._add_log_line(message, level, timestamp)
    
    def _on_log_line(self, line: str, level: str, timestamp: str) -> None:
        """Handle log line from file reader."""
        self._add_log_line(line, level, timestamp)
    
    def _add_log_line(self, line: str, level: str, timestamp: str) -> None:
        """Add a log line to the display."""
        # Check filter
        filter_level = self.level_filter.currentText()
        if filter_level != "ALL" and level != filter_level:
            return
        
        # Get color for level
        color = self.level_colors.get(level, QColor(255, 255, 255))
        
        # Format line
        char_format = QTextCharFormat()
        char_format.setForeground(color)
        char_format.setFont(QFont("Courier New", 10))
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(line + "\n", char_format)
        
        # Limit lines
        max_lines = self.max_lines_spin.value()
        if self.log_text.document().blockCount() > max_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, 1)
            cursor.movePosition(cursor.MoveOperation.Start, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        
        # Auto-scroll
        if self.auto_scroll_cb.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Update line count
        self.line_count_label.setText(f"Lines: {self.log_text.document().blockCount()}")
    
    def _clear_logs(self) -> None:
        """Clear log display."""
        self.log_text.clear()
        self.line_count_label.setText("Lines: 0")
    
    def _load_log_file(self) -> None:
        """Load a log file manually."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Log File",
            str(Path("logs")),
            "Log Files (*.log *.txt);;All Files (*)"
        )
        
        if file_path:
            self.log_file_path = Path(file_path)
            self._start_file_reader()
            self.status_label.setText(f"Monitoring: {self.log_file_path.name}")
    
    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        if self.log_file_reader:
            self.log_file_reader.stop()
            self.log_file_reader.wait()
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
        event.accept()


__all__ = ["DevLogViewerTab"]

