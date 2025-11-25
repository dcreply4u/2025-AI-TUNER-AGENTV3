"""
Hardware Interface Management Tab
UI for configuring and managing external hardware inputs (GPIO, Arduino, I2C, etc.)
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QMessageBox,
    QTextEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor

try:
    from services.hardware_interface_manager import (
        HardwareInterfaceManager,
        HardwareInterface,
        InterfaceType,
        BreakoutBoardType,
    )
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    HardwareInterfaceManager = None  # type: ignore
    HardwareInterface = None  # type: ignore
    InterfaceType = None  # type: ignore
    BreakoutBoardType = None  # type: ignore


class HardwareInterfaceTab(QWidget):
    """Hardware interface management tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Initialize hardware interface manager
        self.hw_manager: Optional[HardwareInterfaceManager] = None
        if HARDWARE_AVAILABLE and HardwareInterfaceManager:
            try:
                self.hw_manager = HardwareInterfaceManager()
            except Exception as e:
                print(f"Failed to initialize hardware manager: {e}")
        
        self.setup_ui()
        self._update_displays()
        
        # Start update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_displays)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self) -> None:
        """Setup hardware interface tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Hardware Interface Manager - External Inputs & GPIO Breakouts")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: {RacingColor.ACCENT_NEON_BLUE.value};")
        main_layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(get_racing_stylesheet("tab_widget"))
        
        # Detected Interfaces tab
        tabs.addTab(self._create_interfaces_tab(), "Detected Interfaces")
        
        # GPIO Configuration tab
        tabs.addTab(self._create_gpio_config_tab(), "GPIO Configuration")
        
        # Arduino Setup tab
        tabs.addTab(self._create_arduino_tab(), "Arduino Setup")
        
        # Status & Diagnostics tab
        tabs.addTab(self._create_status_tab(), "Status & Diagnostics")
        
        main_layout.addWidget(tabs, stretch=1)
    
    def _create_interfaces_tab(self) -> QWidget:
        """Create detected interfaces tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Detection")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(15)
        btn_font = self.scaler.get_scaled_font_size(11)
        refresh_btn.setStyleSheet(get_racing_stylesheet("button_primary"))
        refresh_btn.clicked.connect(self._refresh_detection)
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        # Interfaces table
        self.interfaces_table = QTableWidget()
        self.interfaces_table.setColumnCount(7)
        self.interfaces_table.setHorizontalHeaderLabels([
            "Interface ID", "Type", "Board", "Name", "Status", "GPIO Pins", "Actions"
        ])
        self.interfaces_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.interfaces_table.setMinimumHeight(self.scaler.get_scaled_size(400))
        self.interfaces_table.setStyleSheet(get_racing_stylesheet("table"))
        layout.addWidget(self.interfaces_table)
        
        return panel
    
    def _create_gpio_config_tab(self) -> QWidget:
        """Create GPIO configuration tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Interface selection
        interface_group = QGroupBox("Select Interface")
        interface_group.setStyleSheet(get_racing_stylesheet("group_box"))
        interface_layout = QVBoxLayout()
        
        self.interface_combo = QComboBox()
        self.interface_combo.setStyleSheet(get_racing_stylesheet("input_field"))
        self.interface_combo.currentTextChanged.connect(self._on_interface_selected)
        interface_layout.addWidget(self.interface_combo)
        
        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)
        
        # GPIO pin configuration
        gpio_group = QGroupBox("GPIO Pin Configuration")
        gpio_group.setStyleSheet(get_racing_stylesheet("group_box"))
        gpio_layout = QVBoxLayout()
        
        # Pin number
        pin_layout = QHBoxLayout()
        pin_layout.addWidget(QLabel("Pin Number:"))
        self.pin_spin = QSpinBox()
        self.pin_spin.setRange(0, 40)
        self.pin_spin.setStyleSheet(get_racing_stylesheet("input_field"))
        pin_layout.addWidget(self.pin_spin)
        gpio_layout.addLayout(pin_layout)
        
        # Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["input", "output", "pwm"])
        self.mode_combo.setStyleSheet(get_racing_stylesheet("input_field"))
        mode_layout.addWidget(self.mode_combo)
        gpio_layout.addLayout(mode_layout)
        
        # Pull resistor
        pull_layout = QHBoxLayout()
        pull_layout.addWidget(QLabel("Pull Resistor:"))
        self.pull_combo = QComboBox()
        self.pull_combo.addItems(["none", "up", "down"])
        self.pull_combo.setStyleSheet(get_racing_stylesheet("input_field"))
        pull_layout.addWidget(self.pull_combo)
        gpio_layout.addLayout(pull_layout)
        
        # Active low
        self.active_low_check = QCheckBox("Active Low")
        self.active_low_check.setStyleSheet("color: #ffffff;")
        gpio_layout.addWidget(self.active_low_check)
        
        # Debounce
        debounce_layout = QHBoxLayout()
        debounce_layout.addWidget(QLabel("Debounce (ms):"))
        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(0, 1000)
        self.debounce_spin.setValue(50)
        self.debounce_spin.setStyleSheet(get_racing_stylesheet("input_field"))
        debounce_layout.addWidget(self.debounce_spin)
        gpio_layout.addLayout(debounce_layout)
        
        # Configure button
        config_btn = QPushButton("Configure Pin")
        config_btn.setStyleSheet(get_racing_stylesheet("button_primary"))
        config_btn.clicked.connect(self._configure_gpio_pin)
        gpio_layout.addWidget(config_btn)
        
        gpio_group.setLayout(gpio_layout)
        layout.addWidget(gpio_group)
        
        # Configured pins table
        pins_group = QGroupBox("Configured GPIO Pins")
        pins_group.setStyleSheet(get_racing_stylesheet("group_box"))
        pins_layout = QVBoxLayout()
        
        self.pins_table = QTableWidget()
        self.pins_table.setColumnCount(5)
        self.pins_table.setHorizontalHeaderLabels([
            "Pin", "Mode", "Pull", "Active Low", "Value"
        ])
        self.pins_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pins_table.setMinimumHeight(self.scaler.get_scaled_size(200))
        self.pins_table.setStyleSheet(get_racing_stylesheet("table"))
        pins_layout.addWidget(self.pins_table)
        
        pins_group.setLayout(pins_layout)
        layout.addWidget(pins_group)
        
        layout.addStretch()
        return panel
    
    def _create_arduino_tab(self) -> QWidget:
        """Create Arduino setup tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Arduino GPIO Breakout Setup")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_font = self.scaler.get_scaled_font_size(11)
        info_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {info_font}px;
                border: 1px solid #404040;
            }}
        """)
        info_text.setText("""
Arduino GPIO Breakout Instructions:
===================================

1. Upload the provided Arduino sketch (hardware/arduino_gpio_breakout.ino) to your Arduino board

2. Connect Arduino via USB to your computer

3. The system will auto-detect the Arduino

4. Configure GPIO pins using the GPIO Configuration tab

Arduino Commands:
- CONFIG:pin:mode:pull:active_low - Configure a pin
- READ:pin - Read digital pin value
- WRITE:pin:value - Write digital pin value (0 or 1)
- READ_ANALOG:pin - Read analog pin value (0-1023)
- PWM:pin:value - Set PWM value (0-255)

Example:
  CONFIG:2:input:up:0
  READ:2
  WRITE:3:1
        """)
        layout.addWidget(info_text)
        
        # Firmware download button
        download_btn = QPushButton("Download Arduino Firmware")
        download_btn.setStyleSheet(get_racing_stylesheet("button_primary"))
        download_btn.clicked.connect(self._download_arduino_firmware)
        layout.addWidget(download_btn)
        
        layout.addStretch()
        return panel
    
    def _create_status_tab(self) -> QWidget:
        """Create status and diagnostics tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Hardware Status & Diagnostics")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_font = self.scaler.get_scaled_font_size(11)
        self.status_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {status_font}px;
                border: 1px solid #404040;
            }}
        """)
        self.status_text.setMinimumHeight(self.scaler.get_scaled_size(500))
        layout.addWidget(self.status_text)
        
        return panel
    
    def _refresh_detection(self) -> None:
        """Refresh hardware detection."""
        if self.hw_manager:
            self.hw_manager._detect_hardware()
            self._update_displays()
            QMessageBox.information(self, "Detection Complete", "Hardware detection refreshed.")
    
    def _on_interface_selected(self, interface_id: str) -> None:
        """Handle interface selection."""
        self._update_pins_table()
    
    def _configure_gpio_pin(self) -> None:
        """Configure GPIO pin."""
        if not self.hw_manager:
            return
        
        interface_id = self.interface_combo.currentText()
        if not interface_id:
            QMessageBox.warning(self, "No Interface", "Please select an interface first.")
            return
        
        pin = self.pin_spin.value()
        mode = self.mode_combo.currentText()
        pull = self.pull_combo.currentText()
        active_low = self.active_low_check.isChecked()
        debounce = self.debounce_spin.value()
        
        success = self.hw_manager.configure_gpio_pin(
            interface_id,
            pin,
            mode=mode,
            pull=pull,
            active_low=active_low,
            debounce_ms=debounce,
        )
        
        if success:
            QMessageBox.information(self, "Success", f"GPIO pin {pin} configured successfully.")
            self._update_pins_table()
        else:
            QMessageBox.warning(self, "Error", f"Failed to configure GPIO pin {pin}.")
    
    def _update_displays(self) -> None:
        """Update all displays."""
        if not self.hw_manager:
            return
        
        # Update interfaces table
        interfaces = self.hw_manager.list_interfaces()
        self.interfaces_table.setRowCount(len(interfaces))
        
        for row, interface in enumerate(interfaces):
            self.interfaces_table.setItem(row, 0, QTableWidgetItem(interface.interface_id))
            self.interfaces_table.setItem(row, 1, QTableWidgetItem(interface.interface_type.value))
            board_str = interface.board_type.value if interface.board_type else "N/A"
            self.interfaces_table.setItem(row, 2, QTableWidgetItem(board_str))
            self.interfaces_table.setItem(row, 3, QTableWidgetItem(interface.name))
            status_str = "Connected" if interface.connected else "Disconnected"
            status_item = QTableWidgetItem(status_str)
            if interface.connected:
                status_item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_GREEN.value)))
            else:
                status_item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_RED.value)))
            self.interfaces_table.setItem(row, 4, status_item)
            self.interfaces_table.setItem(row, 5, QTableWidgetItem(str(len(interface.gpio_pins))))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            test_btn = QPushButton("Test")
            test_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 2px 8px; font-size: 9px;")
            test_btn.clicked.connect(lambda checked, i=interface: self._test_interface(i))
            actions_layout.addWidget(test_btn)
            
            self.interfaces_table.setCellWidget(row, 6, actions_widget)
        
        # Update interface combo
        self.interface_combo.clear()
        for interface in interfaces:
            if interface.interface_type in [InterfaceType.GPIO_DIRECT, InterfaceType.GPIO_BREAKOUT, InterfaceType.ARDUINO]:
                self.interface_combo.addItem(interface.interface_id, interface)
        
        # Update status
        status = self.hw_manager.get_status()
        status_text = f"""
Hardware Interface Status:
==========================

Total Interfaces: {status['total_interfaces']}
Connected: {status['connected']}

Interfaces:
"""
        for iface_info in status['interfaces']:
            status_text += f"""
  {iface_info['name']} ({iface_info['id']})
    Type: {iface_info['type']}
    Status: {'Connected' if iface_info['connected'] else 'Disconnected'}
    GPIO Pins: {iface_info['gpio_pins']}
    Enabled: {iface_info['enabled']}
"""
        self.status_text.setText(status_text)
        
        # Update pins table
        self._update_pins_table()
    
    def _update_pins_table(self) -> None:
        """Update configured pins table."""
        if not self.hw_manager:
            return
        
        interface_id = self.interface_combo.currentText()
        if not interface_id:
            self.pins_table.setRowCount(0)
            return
        
        interface = self.hw_manager.get_interface(interface_id)
        if not interface:
            return
        
        pins = list(interface.gpio_pins.values())
        self.pins_table.setRowCount(len(pins))
        
        for row, config in enumerate(pins):
            self.pins_table.setItem(row, 0, QTableWidgetItem(str(config.pin)))
            self.pins_table.setItem(row, 1, QTableWidgetItem(config.mode))
            self.pins_table.setItem(row, 2, QTableWidgetItem(config.pull))
            self.pins_table.setItem(row, 3, QTableWidgetItem("Yes" if config.active_low else "No"))
            
            # Read current value
            value = self.hw_manager.read_gpio(interface_id, config.pin)
            value_str = "HIGH" if value else "LOW" if value is not None else "N/A"
            value_item = QTableWidgetItem(value_str)
            if value:
                value_item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_GREEN.value)))
            elif value is False:
                value_item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_RED.value)))
            self.pins_table.setItem(row, 4, value_item)
    
    def _test_interface(self, interface: HardwareInterface) -> None:
        """Test interface connection."""
        QMessageBox.information(self, "Test", f"Testing interface: {interface.name}")
        # Could add actual test logic here
    
    def _download_arduino_firmware(self) -> None:
        """Download Arduino firmware sketch."""
        QMessageBox.information(
            self,
            "Arduino Firmware",
            "Arduino firmware sketch is located at:\n\n"
            "hardware/arduino_gpio_breakout.ino\n\n"
            "Open this file in Arduino IDE and upload to your board."
        )
















