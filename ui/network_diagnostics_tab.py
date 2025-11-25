"""
Network Diagnostics Tab
Wi-Fi/LTE status monitoring, network speed testing, and connection quality indicators
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QSplitter,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_theme, RacingColor

LOGGER = logging.getLogger(__name__)

try:
    from services.connectivity_manager import ConnectivityManager, ConnectivityStatus
except ImportError:
    ConnectivityManager = None
    ConnectivityStatus = None


class NetworkSpeedTest(QObject):
    """Network speed test worker."""

    speed_test_complete = Signal(float, float)  # download_mbps, upload_mbps

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

    def run_test(self) -> None:
        """Run speed test in background thread."""
        thread = threading.Thread(target=self._test_speed, daemon=True)
        thread.start()

    def _test_speed(self) -> None:
        """Perform speed test."""
        try:
            # Simple ping-based latency test
            # For actual speed test, would need speedtest-cli or similar
            import socket

            start_time = time.time()
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                latency = (time.time() - start_time) * 1000  # ms
            except Exception:
                latency = 999

            # Estimate speed (this is a placeholder - real implementation would use speedtest)
            # For demo purposes, simulate based on latency
            if latency < 50:
                download_mbps = 50.0
                upload_mbps = 10.0
            elif latency < 100:
                download_mbps = 25.0
                upload_mbps = 5.0
            else:
                download_mbps = 5.0
                upload_mbps = 1.0

            self.speed_test_complete.emit(download_mbps, upload_mbps)
        except Exception as e:
            LOGGER.error(f"Speed test failed: {e}")
            self.speed_test_complete.emit(0.0, 0.0)


class NetworkDiagnosticsTab(QWidget):
    """Network Diagnostics tab."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.connectivity_manager: Optional[ConnectivityManager] = None
        self.speed_test = NetworkSpeedTest(self)
        self.speed_test.speed_test_complete.connect(self._on_speed_test_complete)

        # Initialize connectivity manager
        if ConnectivityManager:
            try:
                self.connectivity_manager = ConnectivityManager()
                self.connectivity_manager.start()
            except Exception as e:
                LOGGER.error(f"Failed to initialize ConnectivityManager: {e}")

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(5000)  # Update every 5 seconds

        self.setup_ui()
        self._update_display()

    def setup_ui(self) -> None:
        """Setup network diagnostics tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)

        theme = get_racing_theme()
        self.setStyleSheet(f"background-color: {theme.bg_primary};")

        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)

        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Connection status
        left_panel = self._create_status_panel()
        splitter.addWidget(left_panel)

        # Right: Speed test and diagnostics
        right_panel = self._create_diagnostics_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, stretch=1)

    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        theme = get_racing_theme()
        padding = get_scaled_size(5)
        bar.setStyleSheet(
            f"background-color: {theme.bg_secondary}; padding: {padding}px; border: 1px solid {theme.border_default};"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(get_scaled_size(10), padding, get_scaled_size(10), padding)

        title = QLabel("Network Diagnostics")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: {theme.text_primary};")
        layout.addWidget(title)

        layout.addStretch()

        # Speed test button
        self.speed_test_btn = QPushButton("Run Speed Test")
        btn_font = get_scaled_font_size(11)
        self.speed_test_btn.setStyleSheet(
            f"background-color: {theme.status_optimal}; color: #000000; padding: 5px 10px; font-weight: bold; font-size: {btn_font}px;"
        )
        self.speed_test_btn.clicked.connect(self._run_speed_test)
        layout.addWidget(self.speed_test_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px 10px; font-size: {btn_font}px;"
        )
        refresh_btn.clicked.connect(self._update_display)
        layout.addWidget(refresh_btn)

        return bar

    def _create_status_panel(self) -> QWidget:
        """Create connection status panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))

        # Wi-Fi status
        wifi_group = QGroupBox("Wi-Fi Connection")
        wifi_layout = QVBoxLayout()

        self.wifi_status_label = QLabel("Status: Disconnected")
        wifi_font = get_scaled_font_size(16)
        self.wifi_status_label.setStyleSheet(
            f"font-size: {wifi_font}px; font-weight: bold; color: {theme.status_critical};"
        )
        wifi_layout.addWidget(self.wifi_status_label)

        self.wifi_ssid_label = QLabel("SSID: --")
        self.wifi_ssid_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        wifi_layout.addWidget(self.wifi_ssid_label)

        # Signal strength (placeholder - would need actual signal strength)
        self.wifi_signal_label = QLabel("Signal: --")
        self.wifi_signal_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        wifi_layout.addWidget(self.wifi_signal_label)

        wifi_group.setLayout(wifi_layout)
        layout.addWidget(wifi_group)

        # LTE status
        lte_group = QGroupBox("LTE Connection")
        lte_layout = QVBoxLayout()

        self.lte_status_label = QLabel("Status: Disconnected")
        lte_font = get_scaled_font_size(16)
        self.lte_status_label.setStyleSheet(
            f"font-size: {lte_font}px; font-weight: bold; color: {theme.status_critical};"
        )
        lte_layout.addWidget(self.lte_status_label)

        self.lte_interface_label = QLabel("Interface: --")
        self.lte_interface_label.setStyleSheet(
            f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};"
        )
        lte_layout.addWidget(self.lte_interface_label)

        lte_group.setLayout(lte_layout)
        layout.addWidget(lte_group)

        # Other connections
        other_group = QGroupBox("Other Connections")
        other_layout = QVBoxLayout()

        self.bluetooth_label = QLabel("Bluetooth: --")
        self.bluetooth_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        other_layout.addWidget(self.bluetooth_label)

        self.serial_label = QLabel("Serial Ports: --")
        self.serial_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        other_layout.addWidget(self.serial_label)

        self.usb_label = QLabel("USB Devices: --")
        self.usb_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        other_layout.addWidget(self.usb_label)

        other_group.setLayout(other_layout)
        layout.addWidget(other_group)

        layout.addStretch()
        return panel

    def _create_diagnostics_panel(self) -> QWidget:
        """Create diagnostics panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))

        # Speed test
        speed_group = QGroupBox("Speed Test")
        speed_layout = QVBoxLayout()

        # Download speed
        speed_layout.addWidget(QLabel("Download Speed:"))
        self.download_speed_label = QLabel("-- Mbps")
        speed_font = get_scaled_font_size(18)
        self.download_speed_label.setStyleSheet(
            f"font-size: {speed_font}px; font-weight: bold; color: {theme.accent_neon_blue};"
        )
        speed_layout.addWidget(self.download_speed_label)

        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        speed_layout.addWidget(self.download_progress)

        # Upload speed
        speed_layout.addWidget(QLabel("Upload Speed:"))
        self.upload_speed_label = QLabel("-- Mbps")
        self.upload_speed_label.setStyleSheet(
            f"font-size: {speed_font}px; font-weight: bold; color: {theme.accent_neon_green};"
        )
        speed_layout.addWidget(self.upload_speed_label)

        self.upload_progress = QProgressBar()
        self.upload_progress.setRange(0, 100)
        self.upload_progress.setValue(0)
        speed_layout.addWidget(self.upload_progress)

        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # Connection quality
        quality_group = QGroupBox("Connection Quality")
        quality_layout = QVBoxLayout()

        self.quality_label = QLabel("Quality: --")
        quality_font = get_scaled_font_size(14)
        self.quality_label.setStyleSheet(f"font-size: {quality_font}px; color: {theme.text_primary};")
        quality_layout.addWidget(self.quality_label)

        self.quality_progress = QProgressBar()
        self.quality_progress.setRange(0, 100)
        self.quality_progress.setValue(0)
        quality_layout.addWidget(self.quality_progress)

        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

        # Network info
        info_group = QGroupBox("Network Information")
        info_layout = QVBoxLayout()

        self.network_info_text = QTextEdit()
        self.network_info_text.setReadOnly(True)
        self.network_info_text.setMaximumHeight(get_scaled_size(150))
        self.network_info_text.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};"
        )
        info_layout.addWidget(self.network_info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        return panel

    def _update_display(self) -> None:
        """Update display with current network status."""
        if not self.connectivity_manager:
            return

        try:
            status = self.connectivity_manager.status

            # Update Wi-Fi
            if status.wifi_connected:
                theme = get_racing_theme()
                self.wifi_status_label.setText("Status: Connected")
                self.wifi_status_label.setStyleSheet(
                    f"font-size: 16px; font-weight: bold; color: {theme.status_optimal};"
                )
                self.wifi_ssid_label.setText(f"SSID: {status.wifi_ssid or 'Unknown'}")
            else:
                theme = get_racing_theme()
                self.wifi_status_label.setText("Status: Disconnected")
                self.wifi_status_label.setStyleSheet(
                    f"font-size: 16px; font-weight: bold; color: {theme.status_critical};"
                )
                self.wifi_ssid_label.setText("SSID: --")

            # Update LTE
            if status.lte_connected:
                theme = get_racing_theme()
                self.lte_status_label.setText("Status: Connected")
                self.lte_status_label.setStyleSheet(
                    f"font-size: 16px; font-weight: bold; color: {theme.status_optimal};"
                )
                self.lte_interface_label.setText(f"Interface: {status.lte_interface or 'Unknown'}")
            else:
                theme = get_racing_theme()
                self.lte_status_label.setText("Status: Disconnected")
                self.lte_status_label.setStyleSheet(
                    f"font-size: 16px; font-weight: bold; color: {theme.status_critical};"
                )
                self.lte_interface_label.setText("Interface: --")

            # Update other connections
            self.bluetooth_label.setText(f"Bluetooth: {len(status.bluetooth_devices)} devices")
            self.serial_label.setText(f"Serial Ports: {len(status.serial_ports)} ports")
            self.usb_label.setText(f"USB Devices: {len(status.usb_devices)} devices")

            # Update network info
            info_lines = []
            info_lines.append(f"Gateway Reachable: {'Yes' if status.gateway_reachable else 'No'}")
            info_lines.append(f"Last Updated: {time.strftime('%H:%M:%S', time.localtime(status.last_updated))}")
            self.network_info_text.setText("\n".join(info_lines))

        except Exception as e:
            LOGGER.error(f"Error updating network status: {e}")

    def _run_speed_test(self) -> None:
        """Run network speed test."""
        self.speed_test_btn.setEnabled(False)
        self.speed_test_btn.setText("Testing...")
        self.download_speed_label.setText("Testing...")
        self.upload_speed_label.setText("Testing...")
        self.speed_test.run_test()

    def _on_speed_test_complete(self, download_mbps: float, upload_mbps: float) -> None:
        """Handle speed test completion."""
        self.speed_test_btn.setEnabled(True)
        self.speed_test_btn.setText("Run Speed Test")

        # Update download
        self.download_speed_label.setText(f"{download_mbps:.2f} Mbps")
        self.download_progress.setValue(int(min(download_mbps / 100.0 * 100, 100)))

        # Update upload
        self.upload_speed_label.setText(f"{upload_mbps:.2f} Mbps")
        self.upload_progress.setValue(int(min(upload_mbps / 50.0 * 100, 100)))

        # Update quality (based on speeds)
        if download_mbps > 25 and upload_mbps > 5:
            quality = "Excellent"
            quality_value = 100
            color = get_racing_theme().status_optimal
        elif download_mbps > 10 and upload_mbps > 2:
            quality = "Good"
            quality_value = 75
            color = get_racing_theme().status_adjustable
        elif download_mbps > 5 and upload_mbps > 1:
            quality = "Fair"
            quality_value = 50
            color = get_racing_theme().status_warning
        else:
            quality = "Poor"
            quality_value = 25
            color = get_racing_theme().status_critical

        self.quality_label.setText(f"Quality: {quality}")
        self.quality_label.setStyleSheet(f"font-size: 14px; color: {color};")
        self.quality_progress.setValue(quality_value)


__all__ = ["NetworkDiagnosticsTab", "NetworkSpeedTest"]







