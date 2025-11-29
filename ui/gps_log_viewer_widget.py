"""
GPS Log Viewer Widget
Development-only widget to view GPS data logs in real-time for troubleshooting.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QGroupBox,
    QSpinBox,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size

LOGGER = logging.getLogger(__name__)


class GPSLogViewerWidget(QWidget):
    """
    Development-only GPS log viewer widget.
    
    Shows real-time GPS data for troubleshooting:
    - Raw GPS fixes
    - NMEA sentences (if available)
    - GPS status information
    - Data source (hardware/simulator)
    """
    
    def __init__(
        self,
        gps_interface: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize GPS log viewer.
        
        Args:
            gps_interface: GPS interface to monitor (WaveshareGPSHAT or GPSInterface)
            parent: Parent widget
        """
        super().__init__(parent)
        self.gps_interface = gps_interface
        self.auto_scroll = True
        self.max_lines = 500
        self.update_interval_ms = 500  # 2 Hz update
        
        # Data tracking
        self.fix_count = 0
        self.last_fix: Optional[Dict[str, Any]] = None
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(5))
        
        # Header
        header = QLabel("🔧 GPS Data Log (Development Only)")
        header_font = get_scaled_font_size(12)
        header.setStyleSheet(f"font-size: {header_font}px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(header)
        
        # Controls
        controls = QHBoxLayout()
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.stateChanged.connect(self._on_auto_scroll_changed)
        controls.addWidget(self.auto_scroll_cb)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_log)
        controls.addWidget(clear_btn)
        
        # Max lines
        controls.addWidget(QLabel("Max lines:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setMinimum(100)
        self.max_lines_spin.setMaximum(10000)
        self.max_lines_spin.setValue(self.max_lines)
        self.max_lines_spin.valueChanged.connect(self._on_max_lines_changed)
        controls.addWidget(self.max_lines_spin)
        
        controls.addStretch()
        
        # Status label
        self.status_label = QLabel("Status: Waiting for GPS data...")
        self.status_label.setStyleSheet("color: #95a5a6;")
        controls.addWidget(self.status_label)
        
        layout.addLayout(controls)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", get_scaled_font_size(9)))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_log)
        self.update_timer.start(self.update_interval_ms)
    
    def start_monitoring(self) -> None:
        """Start monitoring GPS data."""
        if self.gps_interface:
            self._log_message("GPS Log Viewer started", "INFO")
            self._log_gps_status()
        else:
            self._log_message("No GPS interface provided", "WARNING")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring GPS data."""
        if self.update_timer:
            self.update_timer.stop()
        self._log_message("GPS Log Viewer stopped", "INFO")
    
    def set_gps_interface(self, gps_interface: Any) -> None:
        """Set the GPS interface to monitor."""
        self.gps_interface = gps_interface
        self._log_gps_status()
    
    def _update_log(self) -> None:
        """Update log with latest GPS data."""
        if not self.gps_interface:
            return
        
        try:
            # Read GPS fix
            fix = self.gps_interface.read_fix()
            
            if fix:
                self.fix_count += 1
                self.last_fix = self._fix_to_dict(fix)
                
                # Log the fix
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                self._log_fix(fix, timestamp)
                
                # Update status
                data_source = "SIMULATOR" if hasattr(self.gps_interface, 'use_simulator') and self.gps_interface.use_simulator else "HARDWARE"
                self.status_label.setText(f"Status: {data_source} - Fix #{self.fix_count}")
                self.status_label.setStyleSheet("color: #27ae60;")
            else:
                self.status_label.setText("Status: No GPS fix available")
                self.status_label.setStyleSheet("color: #e67e22;")
                
        except Exception as e:
            self._log_message(f"Error reading GPS: {e}", "ERROR")
    
    def _fix_to_dict(self, fix: Any) -> Dict[str, Any]:
        """Convert GPS fix to dictionary."""
        if hasattr(fix, '__dict__'):
            return fix.__dict__
        elif isinstance(fix, dict):
            return fix
        else:
            return {
                'latitude': getattr(fix, 'latitude', None),
                'longitude': getattr(fix, 'longitude', None),
                'speed_mps': getattr(fix, 'speed_mps', None),
                'heading': getattr(fix, 'heading', None),
                'altitude_m': getattr(fix, 'altitude_m', None),
                'satellites': getattr(fix, 'satellites', None),
                'timestamp': getattr(fix, 'timestamp', None),
            }
    
    def _log_fix(self, fix: Any, timestamp: str) -> None:
        """Log a GPS fix."""
        try:
            lat = getattr(fix, 'latitude', None)
            lon = getattr(fix, 'longitude', None)
            speed_mps = getattr(fix, 'speed_mps', None)
            heading = getattr(fix, 'heading', None)
            altitude_m = getattr(fix, 'altitude_m', None)
            satellites = getattr(fix, 'satellites', None)
            
            # Format the log entry
            lines = [
                f"[{timestamp}] GPS Fix #{self.fix_count}",
                f"  Latitude:  {lat:.6f}°" if lat is not None else "  Latitude:  N/A",
                f"  Longitude: {lon:.6f}°" if lon is not None else "  Longitude: N/A",
                f"  Speed:     {speed_mps:.2f} m/s ({speed_mps * 2.237:.1f} mph)" if speed_mps is not None else "  Speed:     N/A",
                f"  Heading:   {heading:.1f}°" if heading is not None else "  Heading:   N/A",
                f"  Altitude:  {altitude_m:.1f} m" if altitude_m is not None else "  Altitude:  N/A",
                f"  Satellites: {satellites}" if satellites is not None else "  Satellites: N/A",
            ]
            
            # Add solution type if available
            if hasattr(fix, 'solution_type'):
                lines.append(f"  Solution:  {fix.solution_type}")
            
            # Add position quality if available
            if hasattr(fix, 'position_quality'):
                lines.append(f"  HDOP:      {fix.position_quality:.2f}")
            
            # Add data source
            if hasattr(self.gps_interface, 'use_simulator'):
                data_source = "SIMULATOR" if self.gps_interface.use_simulator else "HARDWARE"
                lines.append(f"  Source:    {data_source}")
            
            lines.append("")  # Blank line
            
            self._append_log("\n".join(lines), "INFO")
            
        except Exception as e:
            self._log_message(f"Error formatting GPS fix: {e}", "ERROR")
    
    def _log_gps_status(self) -> None:
        """Log GPS interface status."""
        if not self.gps_interface:
            self._log_message("GPS interface: None", "WARNING")
            return
        
        try:
            # Get status
            if hasattr(self.gps_interface, 'get_status'):
                status = self.gps_interface.get_status()
            else:
                status = {
                    'port': getattr(self.gps_interface, 'port', 'Unknown'),
                    'connected': getattr(self.gps_interface, 'connected', False) if hasattr(self.gps_interface, 'connected') else True,
                }
            
            lines = [
                "=" * 60,
                "GPS Interface Status",
                "=" * 60,
            ]
            
            for key, value in status.items():
                lines.append(f"  {key}: {value}")
            
            lines.append("=" * 60)
            lines.append("")
            
            self._append_log("\n".join(lines), "INFO")
            
        except Exception as e:
            self._log_message(f"Error getting GPS status: {e}", "ERROR")
    
    def _log_message(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        formatted = f"[{timestamp}] [{level}] {message}\n"
        self._append_log(formatted, level)
    
    def _append_log(self, text: str, level: str = "INFO") -> None:
        """Append text to log with color coding."""
        # Color coding
        color_map = {
            "INFO": QColor("#d4d4d4"),
            "WARNING": QColor("#f39c12"),
            "ERROR": QColor("#e74c3c"),
            "DEBUG": QColor("#95a5a6"),
        }
        
        color = color_map.get(level, QColor("#d4d4d4"))
        
        # Create format
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        
        # Append text
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text, fmt)
        
        # Limit lines
        self._limit_lines()
        
        # Auto-scroll
        if self.auto_scroll:
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
    
    def _limit_lines(self) -> None:
        """Limit the number of lines in the log."""
        text = self.log_text.toPlainText()
        lines = text.split('\n')
        
        if len(lines) > self.max_lines:
            # Keep the last max_lines
            new_text = '\n'.join(lines[-self.max_lines:])
            self.log_text.setPlainText(new_text)
    
    def _clear_log(self) -> None:
        """Clear the log."""
        self.log_text.clear()
        self.fix_count = 0
        self.last_fix = None
        self._log_message("Log cleared", "INFO")
        self._log_gps_status()
    
    def _on_auto_scroll_changed(self, state: int) -> None:
        """Handle auto-scroll checkbox change."""
        self.auto_scroll = (state == Qt.CheckState.Checked.value)
    
    def _on_max_lines_changed(self, value: int) -> None:
        """Handle max lines spinbox change."""
        self.max_lines = value
        self._limit_lines()

