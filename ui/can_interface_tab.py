"""
CAN Bus Interface Tab
Visual CAN bus monitor with channel status, message statistics, and device detection
"""

from __future__ import annotations

import logging
import platform
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QScrollArea,
    QSizePolicy,
    QFrame,
    QMessageBox,
    QTextEdit,
)

LOGGER = logging.getLogger(__name__)

# Try to import CAN libraries
try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    can = None  # type: ignore

try:
    import cantools
    CANTOOLS_AVAILABLE = True
except ImportError:
    CANTOOLS_AVAILABLE = False
    cantools = None  # type: ignore


class CANChannelStatus(Enum):
    """CAN channel status."""
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    ERROR = "Error"
    UNKNOWN = "Unknown"


@dataclass
class CANChannelInfo:
    """Information about a CAN channel."""
    channel_name: str  # e.g., "can0", "can1"
    status: CANChannelStatus = CANChannelStatus.UNKNOWN
    bitrate: Optional[int] = None  # e.g., 500000, 250000
    messages_per_second: float = 0.0
    total_messages: int = 0
    error_frames: int = 0
    unique_ids: int = 0
    last_message_time: float = 0.0
    device_name: Optional[str] = None  # e.g., "MCP2515", "USB-CAN", etc.
    interface_type: Optional[str] = None  # e.g., "socketcan", "slcan"


class CANChannelWidget(QWidget):
    """Visual representation of a CAN channel."""
    
    def __init__(self, channel_info: CANChannelInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.channel_info = channel_info
        self.setFixedSize(120, 140)
        self.setToolTip(self._get_tooltip())
    
    def _get_tooltip(self) -> str:
        """Get tooltip text for channel."""
        tooltip = f"CAN Channel: {self.channel_info.channel_name}"
        if self.channel_info.status == CANChannelStatus.CONNECTED:
            tooltip += f"\nStatus: Connected"
            if self.channel_info.bitrate:
                tooltip += f"\nBitrate: {self.channel_info.bitrate} bps"
            tooltip += f"\nMessages/sec: {self.channel_info.messages_per_second:.1f}"
            tooltip += f"\nTotal Messages: {self.channel_info.total_messages}"
            if self.channel_info.device_name:
                tooltip += f"\nDevice: {self.channel_info.device_name}"
        else:
            tooltip += f"\nStatus: {self.channel_info.status.value}"
        return tooltip
    
    def paintEvent(self, event) -> None:
        """Paint the CAN channel."""
        if not event.rect().intersects(self.rect()):
            return
        
        painter = QPainter(self)
        
        # Determine channel color based on status
        if self.channel_info.status == CANChannelStatus.CONNECTED:
            if self.channel_info.messages_per_second > 0:
                channel_color = QColor(0, 200, 0)  # Green for active
            else:
                channel_color = QColor(0, 150, 255)  # Blue for connected but idle
        elif self.channel_info.status == CANChannelStatus.ERROR:
            channel_color = QColor(255, 0, 0)  # Red for error
        else:
            channel_color = QColor(150, 150, 150)  # Gray for disconnected
        
        # Draw channel body
        channel_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setBrush(QBrush(channel_color))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(channel_rect, 8, 8)
        
        # Draw channel name
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(channel_rect.adjusted(0, 0, 0, -60), Qt.AlignmentFlag.AlignCenter, 
                        self.channel_info.channel_name.upper())
        
        # Draw status
        font_small = QFont("Arial", 9)
        painter.setFont(font_small)
        status_text = self.channel_info.status.value
        painter.drawText(channel_rect.adjusted(0, 25, 0, -35), Qt.AlignmentFlag.AlignCenter, status_text)
        
        # Draw messages/sec if connected
        if self.channel_info.status == CANChannelStatus.CONNECTED:
            msg_text = f"{self.channel_info.messages_per_second:.1f} msg/s"
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawText(channel_rect.adjusted(0, 45, 0, -15), Qt.AlignmentFlag.AlignCenter, msg_text)
        
        # Draw activity indicator
        if self.channel_info.status == CANChannelStatus.CONNECTED:
            indicator_rect = channel_rect.adjusted(5, 5, -5, -5)
            if self.channel_info.messages_per_second > 0:
                painter.setBrush(QBrush(QColor(0, 255, 0)))
                painter.setPen(QPen(QColor(0, 200, 0), 1))
            else:
                painter.setBrush(QBrush(QColor(100, 100, 100)))
                painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawEllipse(indicator_rect.topLeft(), 6, 6)
    
    def update_channel_info(self, channel_info: CANChannelInfo) -> None:
        """Update channel information."""
        if (self.channel_info.status != channel_info.status or
            self.channel_info.messages_per_second != channel_info.messages_per_second):
            self.channel_info = channel_info
            self.setToolTip(self._get_tooltip())
            self.update()


class CANInterfaceTab(QWidget):
    """CAN bus interface tab with visual channel display and monitoring."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.channels: Dict[str, CANChannelInfo] = {}
        self.channel_widgets: Dict[str, CANChannelWidget] = {}
        self.monitoring = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_channels)
        
        # Message log
        self.message_log: deque = deque(maxlen=100)
        
        self.setup_ui()
        self._initialize_channels()
        self._start_monitoring()
    
    def setup_ui(self) -> None:
        """Setup CAN interface UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header = QLabel("CAN Bus Interface Monitor")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_channels)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        control_layout.addWidget(refresh_btn)
        
        auto_detect_btn = QPushButton("🔍 Auto-Detect")
        auto_detect_btn.clicked.connect(self._auto_detect_channels)
        auto_detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        control_layout.addWidget(auto_detect_btn)
        
        status_label = QLabel("Monitoring: Active")
        status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px;")
        self.status_label = status_label
        control_layout.addWidget(status_label)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Split layout: Visual channels on left, details on right
        split_layout = QHBoxLayout()
        
        # Visual CAN channels (left side)
        visual_group = QGroupBox("CAN Channels (Visual)")
        visual_layout = QVBoxLayout(visual_group)
        
        # Create scroll area for channels
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        channels_container = QWidget()
        channels_layout = QHBoxLayout(channels_container)
        channels_layout.setSpacing(10)
        channels_layout.setContentsMargins(10, 10, 10, 10)
        
        self.channels_container_layout = channels_layout
        scroll.setWidget(channels_container)
        visual_layout.addWidget(scroll)
        split_layout.addWidget(visual_group, stretch=1)
        
        # Right side: Channel details table and message log
        right_layout = QVBoxLayout()
        
        # Channel details table
        table_group = QGroupBox("Channel Details")
        table_layout = QVBoxLayout(table_group)
        
        self.channel_table = QTableWidget()
        self.channel_table.setColumnCount(7)
        self.channel_table.setHorizontalHeaderLabels([
            "Channel", "Status", "Bitrate", "Msg/s", "Total", "Errors", "Device"
        ])
        self.channel_table.horizontalHeader().setStretchLastSection(True)
        self.channel_table.setAlternatingRowColors(True)
        self.channel_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self.channel_table)
        right_layout.addWidget(table_group)
        
        # Message log
        log_group = QGroupBox("Recent Messages (Last 100)")
        log_layout = QVBoxLayout(log_group)
        
        self.message_log_text = QTextEdit()
        self.message_log_text.setReadOnly(True)
        self.message_log_text.setMaximumHeight(200)
        self.message_log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.message_log_text)
        right_layout.addWidget(log_group)
        
        split_layout.addLayout(right_layout, stretch=1)
        main_layout.addLayout(split_layout)
    
    def _initialize_channels(self) -> None:
        """Initialize CAN channels."""
        self._auto_detect_channels()
        self._update_channel_table()
    
    def _start_monitoring(self) -> None:
        """Start monitoring CAN channels."""
        self.monitoring = True
        self.monitor_timer.start(2000)  # Update every 2 seconds
        LOGGER.info("CAN monitoring started")
    
    def _stop_monitoring(self) -> None:
        """Stop monitoring CAN channels."""
        self.monitoring = False
        self.monitor_timer.stop()
        LOGGER.info("CAN monitoring stopped")
    
    def _auto_detect_channels(self) -> None:
        """Auto-detect CAN channels."""
        LOGGER.info("Starting CAN channel auto-detection...")
        self.status_label.setText("Auto-detecting channels...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 8px;")
        
        detected_channels = []
        
        # Check for socketcan interfaces (Linux)
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["ip", "link", "show"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'can' in line.lower() or 'slcan' in line.lower():
                            # Extract interface name
                            parts = line.split(':')
                            if len(parts) >= 2:
                                interface = parts[1].strip().split()[0]
                                if interface.startswith('can') or interface.startswith('slcan'):
                                    detected_channels.append(interface)
            except Exception as e:
                LOGGER.debug("Failed to detect CAN interfaces via ip: %s", e)
            
            # Check /sys/class/net for CAN interfaces
            try:
                net_path = Path("/sys/class/net")
                if net_path.exists():
                    for interface_dir in net_path.iterdir():
                        interface_name = interface_dir.name
                        if interface_name.startswith('can') or interface_name.startswith('slcan'):
                            if interface_name not in detected_channels:
                                detected_channels.append(interface_name)
            except Exception as e:
                LOGGER.debug("Failed to detect CAN interfaces via sysfs: %s", e)
        
        # Try to detect via python-can
        if CAN_AVAILABLE:
            try:
                # Try common channel names
                for channel_name in ["can0", "can1", "vcan0", "slcan0"]:
                    try:
                        bus = can.interface.Bus(channel=channel_name, bustype="socketcan")
                        bus.shutdown()
                        if channel_name not in detected_channels:
                            detected_channels.append(channel_name)
                    except Exception:
                        pass
            except Exception as e:
                LOGGER.debug("Failed to detect CAN via python-can: %s", e)
        
        # Create channel info for detected channels
        for channel_name in detected_channels:
            if channel_name not in self.channels:
                channel_info = CANChannelInfo(channel_name=channel_name)
                self.channels[channel_name] = channel_info
                
                # Create visual widget
                channel_widget = CANChannelWidget(channel_info, self)
                self.channel_widgets[channel_name] = channel_widget
                self.channels_container_layout.addWidget(channel_widget)
        
        # Update status
        detected_count = len(detected_channels)
        self.status_label.setText(f"Monitoring: Active ({detected_count} channels)")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px;")
        LOGGER.info("CAN auto-detection complete: %d channels detected", detected_count)
    
    def _update_channels(self) -> None:
        """Update CAN channel states."""
        if not self.monitoring:
            return
        
        updated = False
        for channel_name, channel_info in list(self.channels.items()):
            try:
                # Try to check channel status
                if CAN_AVAILABLE:
                    try:
                        # Try to create a bus to check if channel is available
                        bus = can.interface.Bus(channel=channel_name, bustype="socketcan", receive_own_messages=False)
                        
                        # Try to get bitrate (may not be available on all systems)
                        bitrate = None
                        try:
                            # Check /sys/class/net/canX/bitrate
                            bitrate_path = Path(f"/sys/class/net/{channel_name}/bitrate")
                            if bitrate_path.exists():
                                bitrate = int(bitrate_path.read_text().strip())
                        except Exception:
                            pass
                        
                        channel_info.status = CANChannelStatus.CONNECTED
                        channel_info.bitrate = bitrate
                        
                        # Try to read a message to check activity
                        try:
                            msg = bus.recv(timeout=0.1)
                            if msg:
                                channel_info.total_messages += 1
                                channel_info.last_message_time = time.time()
                                # Add to message log
                                self._add_message_to_log(channel_name, msg)
                        except Exception:
                            pass
                        
                        # Calculate messages per second (simple moving average)
                        if channel_info.last_message_time > 0:
                            time_since_last = time.time() - channel_info.last_message_time
                            if time_since_last < 1.0:
                                channel_info.messages_per_second = 1.0 / max(time_since_last, 0.1)
                            else:
                                channel_info.messages_per_second *= 0.9  # Decay
                        
                        bus.shutdown()
                        updated = True
                    except Exception as e:
                        channel_info.status = CANChannelStatus.DISCONNECTED
                        LOGGER.debug("Channel %s not available: %s", channel_name, e)
                else:
                    # Simulate for testing
                    channel_info.status = CANChannelStatus.DISCONNECTED
            except Exception as e:
                LOGGER.debug("Error checking channel %s: %s", channel_name, e)
            
            # Update visual widget
            if channel_name in self.channel_widgets:
                old_status = self.channel_widgets[channel_name].channel_info.status
                if old_status != channel_info.status:
                    self.channel_widgets[channel_name].update_channel_info(channel_info)
        
        # Only update table every 5 cycles
        if not hasattr(self, '_table_update_counter'):
            self._table_update_counter = 0
        self._table_update_counter += 1
        if updated and self._table_update_counter >= 5:
            self._update_channel_table()
            self._table_update_counter = 0
    
    def _add_message_to_log(self, channel: str, message) -> None:
        """Add a CAN message to the log."""
        timestamp = time.strftime("%H:%M:%S")
        can_id = hex(message.arbitration_id)
        data_hex = message.data.hex().upper()
        log_entry = f"[{timestamp}] {channel}: ID={can_id} Data={data_hex}"
        self.message_log.append(log_entry)
        
        # Update text widget (keep last 20 visible)
        if len(self.message_log) > 20:
            visible_log = list(self.message_log)[-20:]
        else:
            visible_log = list(self.message_log)
        
        self.message_log_text.setPlainText("\n".join(visible_log))
        # Auto-scroll to bottom
        scrollbar = self.message_log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _refresh_channels(self) -> None:
        """Refresh all CAN channels."""
        self._update_channels()
        self._update_channel_table()
        LOGGER.info("CAN channels refreshed")
    
    def _update_channel_table(self) -> None:
        """Update the channel details table."""
        self.channel_table.setRowCount(len(self.channels))
        
        for row, (channel_name, channel_info) in enumerate(sorted(self.channels.items())):
            # Channel name
            self.channel_table.setItem(row, 0, QTableWidgetItem(channel_name))
            
            # Status
            status_item = QTableWidgetItem(channel_info.status.value)
            if channel_info.status == CANChannelStatus.CONNECTED:
                status_item.setForeground(QColor(0, 200, 0))
            elif channel_info.status == CANChannelStatus.ERROR:
                status_item.setForeground(QColor(255, 0, 0))
            else:
                status_item.setForeground(QColor(150, 150, 150))
            self.channel_table.setItem(row, 1, status_item)
            
            # Bitrate
            bitrate_text = f"{channel_info.bitrate:,}" if channel_info.bitrate else "-"
            self.channel_table.setItem(row, 2, QTableWidgetItem(bitrate_text))
            
            # Messages per second
            msg_s_text = f"{channel_info.messages_per_second:.1f}"
            self.channel_table.setItem(row, 3, QTableWidgetItem(msg_s_text))
            
            # Total messages
            self.channel_table.setItem(row, 4, QTableWidgetItem(str(channel_info.total_messages)))
            
            # Error frames
            self.channel_table.setItem(row, 5, QTableWidgetItem(str(channel_info.error_frames)))
            
            # Device
            device_text = channel_info.device_name or "-"
            self.channel_table.setItem(row, 6, QTableWidgetItem(device_text))
        
        self.channel_table.resizeColumnsToContents()
    
    def closeEvent(self, event) -> None:
        """Clean up on close."""
        self._stop_monitoring()
        super().closeEvent(event)


__all__ = ["CANInterfaceTab"]

