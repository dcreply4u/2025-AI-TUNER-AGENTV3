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
    QFileDialog,
    QComboBox,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
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

# Import CAN decoder service
try:
    from services.can_decoder import CANDecoder, DecodedMessage
    DECODER_AVAILABLE = True
except ImportError:
    DECODER_AVAILABLE = False
    CANDecoder = None  # type: ignore
    DecodedMessage = None  # type: ignore

# Import CAN simulator service
try:
    from services.can_simulator import CANSimulator, MessageType
    SIMULATOR_AVAILABLE = True
except ImportError:
    SIMULATOR_AVAILABLE = False
    CANSimulator = None  # type: ignore
    MessageType = None  # type: ignore


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
        
        # CAN decoder
        self.decoder: Optional[CANDecoder] = None
        if DECODER_AVAILABLE:
            self.decoder = CANDecoder()
        
        # CAN simulator
        self.simulator: Optional[CANSimulator] = None
        if SIMULATOR_AVAILABLE:
            self.simulator = CANSimulator(channel="vcan0", dbc_decoder=self.decoder)
        
        # Decoded messages log
        self.decoded_messages: deque = deque(maxlen=500)
        
        # CAN bus connections for monitoring
        self.bus_connections: Dict[str, "can.Bus"] = {}
        
        self.setup_ui()
        self._initialize_channels()
        if DECODER_AVAILABLE and self.decoder:
            self._update_dbc_combo()
            self._update_dbc_messages_tree()
        if SIMULATOR_AVAILABLE and self.simulator:
            self._update_simulator_messages_table()
        self._start_monitoring()
    
    def setup_ui(self) -> None:
        """Setup CAN interface UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header = QLabel("CAN Bus Interface Monitor & Decoder")
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
        
        # DBC file loading button
        if DECODER_AVAILABLE:
            load_dbc_btn = QPushButton("📁 Load DBC File")
            load_dbc_btn.clicked.connect(self._load_dbc_file)
            load_dbc_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            control_layout.addWidget(load_dbc_btn)
            
            # DBC database selector
            self.dbc_combo = QComboBox()
            self.dbc_combo.currentTextChanged.connect(self._on_dbc_changed)
            self.dbc_combo.setMinimumWidth(150)
            control_layout.addWidget(QLabel("DBC:"))
            control_layout.addWidget(self.dbc_combo)
        
        status_label = QLabel("Monitoring: Active")
        status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px;")
        self.status_label = status_label
        control_layout.addWidget(status_label)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Create tab widget for different views
        tabs = QTabWidget()
        
        # Tab 1: Monitor View
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        
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
        log_group = QGroupBox("Recent Messages (Raw)")
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
        monitor_layout.addLayout(split_layout)
        tabs.addTab(monitor_tab, "Monitor")
        
        # Tab 2: Decoded Messages (if decoder available)
        if DECODER_AVAILABLE:
            decoded_tab = QWidget()
            decoded_layout = QVBoxLayout(decoded_tab)
            
            # Decoded messages table
            decoded_group = QGroupBox("Decoded Messages")
            decoded_table_layout = QVBoxLayout(decoded_group)
            
            self.decoded_table = QTreeWidget()
            self.decoded_table.setHeaderLabels(["Time", "Channel", "Message", "CAN ID", "Signals"])
            self.decoded_table.setAlternatingRowColors(True)
            self.decoded_table.setColumnWidth(0, 100)
            self.decoded_table.setColumnWidth(1, 80)
            self.decoded_table.setColumnWidth(2, 150)
            self.decoded_table.setColumnWidth(3, 100)
            decoded_table_layout.addWidget(self.decoded_table)
            decoded_layout.addWidget(decoded_group)
            
            tabs.addTab(decoded_tab, "Decoded Messages")
            
            # Tab 3: DBC Messages Browser
            dbc_tab = QWidget()
            dbc_layout = QVBoxLayout(dbc_tab)
            
            dbc_info_group = QGroupBox("DBC Database Information")
            dbc_info_layout = QVBoxLayout(dbc_info_group)
            
            self.dbc_messages_tree = QTreeWidget()
            self.dbc_messages_tree.setHeaderLabels(["Message", "CAN ID", "Length", "Signals"])
            self.dbc_messages_tree.setAlternatingRowColors(True)
            self.dbc_messages_tree.itemDoubleClicked.connect(self._on_dbc_message_selected)
            dbc_info_layout.addWidget(self.dbc_messages_tree)
            dbc_layout.addWidget(dbc_info_group)
            
            tabs.addTab(dbc_tab, "DBC Browser")
        
        # Tab 4: CAN Simulator (if simulator available)
        if SIMULATOR_AVAILABLE:
            simulator_tab = QWidget()
            simulator_layout = QVBoxLayout(simulator_tab)
            
            # Control panel
            control_group = QGroupBox("Simulator Control")
            control_layout = QVBoxLayout(control_group)
            
            button_layout = QHBoxLayout()
            
            self.sim_start_btn = QPushButton("▶ Start Simulator")
            self.sim_start_btn.clicked.connect(self._start_simulator)
            self.sim_start_btn.setStyleSheet("""
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
            button_layout.addWidget(self.sim_start_btn)
            
            self.sim_stop_btn = QPushButton("⏹ Stop Simulator")
            self.sim_stop_btn.clicked.connect(self._stop_simulator)
            self.sim_stop_btn.setEnabled(False)
            self.sim_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            button_layout.addWidget(self.sim_stop_btn)
            
            self.sim_add_btn = QPushButton("➕ Add Message")
            self.sim_add_btn.clicked.connect(self._add_simulated_message)
            button_layout.addWidget(self.sim_add_btn)
            
            button_layout.addStretch()
            control_layout.addLayout(button_layout)
            
            # Statistics
            self.sim_stats_label = QLabel("Status: Stopped")
            self.sim_stats_label.setStyleSheet("font-weight: bold; padding: 5px;")
            control_layout.addWidget(self.sim_stats_label)
            
            simulator_layout.addWidget(control_group)
            
            # Messages table
            messages_group = QGroupBox("Simulated Messages")
            messages_layout = QVBoxLayout(messages_group)
            
            self.sim_messages_table = QTableWidget()
            self.sim_messages_table.setColumnCount(6)
            self.sim_messages_table.setHorizontalHeaderLabels([
                "Name", "CAN ID", "Period (s)", "Type", "Enabled", "Sent"
            ])
            self.sim_messages_table.horizontalHeader().setStretchLastSection(True)
            self.sim_messages_table.setAlternatingRowColors(True)
            self.sim_messages_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            messages_layout.addWidget(self.sim_messages_table)
            
            simulator_layout.addWidget(messages_group)
            
            tabs.addTab(simulator_tab, "Simulator")
        
        main_layout.addWidget(tabs)
    
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
        
        # Try to decode if decoder is available
        if self.decoder and DECODER_AVAILABLE:
            from interfaces.can_interface import CANMessage, CANMessageType
            can_msg = CANMessage(
                arbitration_id=message.arbitration_id,
                data=message.data,
                timestamp=message.timestamp or time.time(),
                channel=channel,
                dlc=message.dlc,
                is_error_frame=message.is_error_frame,
                is_remote_frame=message.is_remote_frame,
            )
            decoded = self.decoder.decode_message(can_msg)
            if decoded:
                self.decoded_messages.append(decoded)
                self._update_decoded_table()
        
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
    
    def _load_dbc_file(self) -> None:
        """Load a DBC file for decoding."""
        if not DECODER_AVAILABLE or not self.decoder:
            QMessageBox.warning(
                self,
                "DBC Decoder Not Available",
                "cantools is not installed. Install with: pip install cantools"
            )
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load DBC File",
            "",
            "DBC Files (*.dbc);;All Files (*)"
        )
        
        if file_path:
            if self.decoder.load_dbc(file_path):
                # Update DBC combo box
                self._update_dbc_combo()
                # Update DBC messages tree
                self._update_dbc_messages_tree()
                QMessageBox.information(
                    self,
                    "DBC Loaded",
                    f"Successfully loaded DBC file:\n{Path(file_path).name}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Load Failed",
                    f"Failed to load DBC file:\n{file_path}"
                )
    
    def _update_dbc_combo(self) -> None:
        """Update DBC database combo box."""
        if not DECODER_AVAILABLE or not self.decoder:
            return
        
        self.dbc_combo.clear()
        databases = self.decoder.list_databases()
        self.dbc_combo.addItems(databases)
        
        # Set active database
        active = self.decoder.get_active_database()
        if active:
            index = self.dbc_combo.findText(active)
            if index >= 0:
                self.dbc_combo.setCurrentIndex(index)
    
    def _on_dbc_changed(self, db_name: str) -> None:
        """Handle DBC database selection change."""
        if self.decoder and db_name:
            self.decoder.set_active_database(db_name)
            self._update_dbc_messages_tree()
    
    def _update_dbc_messages_tree(self) -> None:
        """Update DBC messages browser tree."""
        if not DECODER_AVAILABLE or not self.decoder:
            return
        
        self.dbc_messages_tree.clear()
        
        messages = self.decoder.list_messages()
        for msg_info in messages:
            msg_item = QTreeWidgetItem(self.dbc_messages_tree)
            msg_item.setText(0, msg_info["name"])
            msg_item.setText(1, msg_info["can_id_hex"])
            msg_item.setText(2, str(msg_info["length"]))
            msg_item.setText(3, str(msg_info["signal_count"]))
            
            # Get detailed info for signals
            detailed_info = self.decoder.get_message_info(msg_info["can_id"])
            if detailed_info:
                for signal in detailed_info["signals"]:
                    signal_item = QTreeWidgetItem(msg_item)
                    signal_item.setText(0, signal["name"])
                    signal_item.setText(1, f"Bits: {signal['start']}-{signal['start'] + signal['length'] - 1}")
                    signal_item.setText(2, signal["unit"] or "-")
                    range_str = ""
                    if signal["min"] is not None and signal["max"] is not None:
                        range_str = f"{signal['min']:.2f} - {signal['max']:.2f}"
                    signal_item.setText(3, range_str)
        
        self.dbc_messages_tree.expandAll()
    
    def _on_dbc_message_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle DBC message selection."""
        if item.parent() is None:  # Top-level item (message)
            can_id_hex = item.text(1)
            try:
                can_id = int(can_id_hex, 16)
                info = self.decoder.get_message_info(can_id) if self.decoder else None
                if info:
                    msg_text = f"Message: {info['name']}\n"
                    msg_text += f"CAN ID: {info['can_id_hex']}\n"
                    msg_text += f"Length: {info['length']} bytes\n"
                    msg_text += f"Extended: {info['is_extended']}\n"
                    if info['comment']:
                        msg_text += f"Comment: {info['comment']}\n"
                    msg_text += f"\nSignals ({len(info['signals'])}):\n"
                    for signal in info['signals']:
                        msg_text += f"  - {signal['name']}: {signal['unit'] or 'N/A'}\n"
                    
                    QMessageBox.information(self, "Message Information", msg_text)
            except ValueError:
                pass
    
    def _update_decoded_table(self) -> None:
        """Update decoded messages table."""
        if not DECODER_AVAILABLE or not hasattr(self, 'decoded_table'):
            return
        
        # Keep only recent messages visible (last 100)
        recent_messages = list(self.decoded_messages)[-100:]
        
        self.decoded_table.clear()
        
        for decoded_msg in recent_messages:
            # Create top-level item
            msg_item = QTreeWidgetItem(self.decoded_table)
            timestamp_str = time.strftime("%H:%M:%S", time.localtime(decoded_msg.timestamp))
            msg_item.setText(0, timestamp_str)
            msg_item.setText(1, decoded_msg.channel)
            msg_item.setText(2, decoded_msg.message_name)
            msg_item.setText(3, hex(decoded_msg.can_id))
            
            # Add signals as children
            signals_text = []
            for signal in decoded_msg.signals:
                signal_item = QTreeWidgetItem(msg_item)
                signal_item.setText(0, signal.name)
                if signal.choice_string:
                    signal_item.setText(1, signal.choice_string)
                else:
                    value_str = f"{signal.value:.3f}"
                    if signal.unit:
                        value_str += f" {signal.unit}"
                    signal_item.setText(1, value_str)
                signal_item.setText(2, f"Raw: {signal.raw_value}")
                signals_text.append(f"{signal.name}={signal.value:.3f}{signal.unit or ''}")
            
            msg_item.setText(4, ", ".join(signals_text))
        
        # Auto-scroll to bottom
        self.decoded_table.scrollToBottom()
    
    def _start_simulator(self) -> None:
        """Start the CAN simulator."""
        if not SIMULATOR_AVAILABLE or not self.simulator:
            QMessageBox.warning(self, "Simulator Not Available", "CAN simulator is not available")
            return
        
        if self.simulator.start():
            self.sim_start_btn.setEnabled(False)
            self.sim_stop_btn.setEnabled(True)
            self._update_simulator_stats()
            # Update stats every second
            if not hasattr(self, 'sim_stats_timer'):
                self.sim_stats_timer = QTimer()
                self.sim_stats_timer.timeout.connect(self._update_simulator_stats)
            self.sim_stats_timer.start(1000)
        else:
            QMessageBox.critical(self, "Start Failed", "Failed to start CAN simulator")
    
    def _stop_simulator(self) -> None:
        """Stop the CAN simulator."""
        if self.simulator:
            self.simulator.stop()
            self.sim_start_btn.setEnabled(True)
            self.sim_stop_btn.setEnabled(False)
            if hasattr(self, 'sim_stats_timer'):
                self.sim_stats_timer.stop()
            self._update_simulator_stats()
    
    def _add_simulated_message(self) -> None:
        """Add a simulated message dialog."""
        if not SIMULATOR_AVAILABLE or not self.simulator:
            return
        
        # Simple dialog for adding messages
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Simulated Message")
        layout = QFormLayout(dialog)
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Message name")
        layout.addRow("Message Name:", name_edit)
        
        can_id_spin = QSpinBox()
        can_id_spin.setRange(0, 0x7FF)
        can_id_spin.setDisplayIntegerBase(16)
        can_id_spin.setPrefix("0x")
        layout.addRow("CAN ID:", can_id_spin)
        
        period_spin = QDoubleSpinBox()
        period_spin.setRange(0.001, 10.0)
        period_spin.setValue(0.1)
        period_spin.setDecimals(3)
        period_spin.setSuffix(" s")
        layout.addRow("Period:", period_spin)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec():
            name = name_edit.text().strip()
            can_id = can_id_spin.value()
            period = period_spin.value()
            
            if name:
                if self.simulator.add_message(name, can_id, period=period):
                    self._update_simulator_messages_table()
                else:
                    QMessageBox.warning(self, "Add Failed", "Failed to add simulated message")
    
    def _update_simulator_stats(self) -> None:
        """Update simulator statistics display."""
        if not self.simulator:
            return
        
        stats = self.simulator.get_statistics()
        status_text = f"Status: {'Running' if stats['running'] else 'Stopped'}"
        if stats['running']:
            status_text += f" | Sent: {stats['total_sent']} | Rate: {stats['messages_per_second']:.1f} msg/s"
        self.sim_stats_label.setText(status_text)
    
    def _update_simulator_messages_table(self) -> None:
        """Update simulated messages table."""
        if not self.simulator or not hasattr(self, 'sim_messages_table'):
            return
        
        messages = self.simulator.list_messages()
        self.sim_messages_table.setRowCount(len(messages))
        
        for row, msg in enumerate(messages):
            self.sim_messages_table.setItem(row, 0, QTableWidgetItem(msg["name"]))
            self.sim_messages_table.setItem(row, 1, QTableWidgetItem(msg["can_id_hex"]))
            self.sim_messages_table.setItem(row, 2, QTableWidgetItem(f"{msg['period']:.3f}"))
            self.sim_messages_table.setItem(row, 3, QTableWidgetItem(msg["message_type"]))
            
            enabled_item = QTableWidgetItem("Yes" if msg["enabled"] else "No")
            enabled_item.setForeground(QColor(0, 200, 0) if msg["enabled"] else QColor(150, 150, 150))
            self.sim_messages_table.setItem(row, 4, enabled_item)
            
            self.sim_messages_table.setItem(row, 5, QTableWidgetItem(str(msg["send_count"])))
        
        self.sim_messages_table.resizeColumnsToContents()
    
    def closeEvent(self, event) -> None:
        """Clean up on close."""
        self._stop_monitoring()
        
        # Stop simulator
        if self.simulator:
            self.simulator.stop()
        
        # Close CAN bus connections
        for bus in self.bus_connections.values():
            try:
                bus.shutdown()
            except Exception:
                pass
        self.bus_connections.clear()
        
        super().closeEvent(event)


__all__ = ["CANInterfaceTab"]

