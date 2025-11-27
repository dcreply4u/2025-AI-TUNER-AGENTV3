"""
GPIO Interface Tab
Visual GPIO pin monitor with auto-detection for Raspberry Pi
"""

from __future__ import annotations

import logging
import platform
import time
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
)

LOGGER = logging.getLogger(__name__)

# Try to import GPIO libraries
try:
    import RPi.GPIO as GPIO
    RPI_GPIO_AVAILABLE = True
except ImportError:
    try:
        import Jetson.GPIO as GPIO
        RPI_GPIO_AVAILABLE = True
    except ImportError:
        RPI_GPIO_AVAILABLE = False
        GPIO = None  # type: ignore

# Try to import gpiod for modern GPIO access
try:
    import gpiod
    GPIOD_AVAILABLE = True
except ImportError:
    GPIOD_AVAILABLE = False
    gpiod = None  # type: ignore


class PinFunction(Enum):
    """GPIO pin function."""
    GPIO = "GPIO"
    POWER = "Power"
    GROUND = "Ground"
    I2C = "I2C"
    SPI = "SPI"
    UART = "UART"
    PWM = "PWM"
    ADC = "ADC"
    UNKNOWN = "Unknown"


class PinDirection(Enum):
    """Pin direction."""
    INPUT = "Input"
    OUTPUT = "Output"
    UNKNOWN = "Unknown"


@dataclass
class PinInfo:
    """Information about a GPIO pin."""
    physical_pin: int  # Physical pin number on header
    bcm_pin: Optional[int] = None  # BCM pin number (if GPIO)
    function: PinFunction = PinFunction.UNKNOWN
    direction: PinDirection = PinDirection.UNKNOWN
    value: Optional[bool] = None  # Current value (for GPIO)
    connected: bool = False  # Whether something is detected
    device_name: Optional[str] = None  # Name of connected device
    last_update: float = 0.0


class GPIOPinWidget(QWidget):
    """Visual representation of a single GPIO pin."""
    
    def __init__(self, pin_info: PinInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pin_info = pin_info
        self.setFixedSize(60, 100)
        self.setToolTip(self._get_tooltip())
    
    def _get_tooltip(self) -> str:
        """Get tooltip text for pin."""
        tooltip = f"Physical Pin {self.pin_info.physical_pin}"
        if self.pin_info.bcm_pin is not None:
            tooltip += f"\nBCM GPIO {self.pin_info.bcm_pin}"
        tooltip += f"\nFunction: {self.pin_info.function.value}"
        if self.pin_info.connected:
            tooltip += f"\nConnected: {self.pin_info.device_name or 'Device'}"
        if self.pin_info.value is not None:
            tooltip += f"\nValue: {'HIGH' if self.pin_info.value else 'LOW'}"
        return tooltip
    
    def paintEvent(self, event) -> None:
        """Paint the GPIO pin."""
        # Only repaint if the update rect intersects our area
        if not event.rect().intersects(self.rect()):
            return
        
        painter = QPainter(self)
        # Disable antialiasing for better performance
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine pin color based on function and state
        if self.pin_info.function == PinFunction.POWER:
            pin_color = QColor(255, 0, 0)  # Red for power
        elif self.pin_info.function == PinFunction.GROUND:
            pin_color = QColor(0, 0, 0)  # Black for ground
        elif self.pin_info.connected:
            if self.pin_info.value is True:
                pin_color = QColor(0, 255, 0)  # Green for HIGH
            elif self.pin_info.value is False:
                pin_color = QColor(100, 100, 100)  # Gray for LOW
            else:
                pin_color = QColor(0, 150, 255)  # Blue for connected but unknown state
        else:
            pin_color = QColor(150, 150, 150)  # Gray for unconnected
        
        # Draw pin body
        pin_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setBrush(QBrush(pin_color))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(pin_rect, 5, 5)
        
        # Draw pin number
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pin_rect, Qt.AlignmentFlag.AlignCenter, str(self.pin_info.physical_pin))
        
        # Draw BCM number if GPIO
        if self.pin_info.bcm_pin is not None:
            font_small = QFont("Arial", 7)
            painter.setFont(font_small)
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            bcm_rect = pin_rect.adjusted(0, 20, 0, 0)
            painter.drawText(bcm_rect, Qt.AlignmentFlag.AlignCenter, f"GPIO{self.pin_info.bcm_pin}")
        
        # Draw connection indicator
        if self.pin_info.connected:
            indicator_rect = pin_rect.adjusted(5, 5, -5, -5)
            painter.setBrush(QBrush(QColor(0, 255, 0)))
            painter.setPen(QPen(QColor(0, 200, 0), 1))
            painter.drawEllipse(indicator_rect.topLeft(), 5, 5)
    
    def update_pin_info(self, pin_info: PinInfo) -> None:
        """Update pin information."""
        # Only update if something actually changed
        if (self.pin_info.value != pin_info.value or 
            self.pin_info.connected != pin_info.connected or
            self.pin_info.device_name != pin_info.device_name):
            self.pin_info = pin_info
            self.setToolTip(self._get_tooltip())
            self.update()  # Trigger repaint


class GPIOInterfaceTab(QWidget):
    """GPIO interface tab with visual pin display and auto-detection."""
    
    # Raspberry Pi GPIO pinout (40-pin header)
    # Format: (Physical Pin, BCM Pin, Function)
    PI_GPIO_PINS = [
        (1, None, PinFunction.POWER),   # 3.3V
        (2, None, PinFunction.POWER),   # 5V
        (3, 2, PinFunction.I2C),        # GPIO 2 (SDA)
        (4, None, PinFunction.POWER),   # 5V
        (5, 3, PinFunction.I2C),        # GPIO 3 (SCL)
        (6, None, PinFunction.GROUND),  # GND
        (7, 4, PinFunction.GPIO),        # GPIO 4
        (8, 14, PinFunction.UART),      # GPIO 14 (TXD)
        (9, None, PinFunction.GROUND),  # GND
        (10, 15, PinFunction.UART),     # GPIO 15 (RXD)
        (11, 17, PinFunction.GPIO),     # GPIO 17
        (12, 18, PinFunction.PWM),      # GPIO 18 (PWM)
        (13, 27, PinFunction.GPIO),     # GPIO 27
        (14, None, PinFunction.GROUND), # GND
        (15, 22, PinFunction.GPIO),     # GPIO 22
        (16, 23, PinFunction.GPIO),     # GPIO 23
        (17, None, PinFunction.POWER),   # 3.3V
        (18, 24, PinFunction.GPIO),     # GPIO 24
        (19, 10, PinFunction.SPI),      # GPIO 10 (MOSI)
        (20, None, PinFunction.GROUND), # GND
        (21, 9, PinFunction.SPI),       # GPIO 9 (MISO)
        (22, 25, PinFunction.GPIO),    # GPIO 25
        (23, 11, PinFunction.SPI),      # GPIO 11 (SCLK)
        (24, 8, PinFunction.SPI),       # GPIO 8 (CE0)
        (25, None, PinFunction.GROUND), # GND
        (26, 7, PinFunction.SPI),      # GPIO 7 (CE1)
        (27, 0, PinFunction.I2C),      # GPIO 0 (ID_SD)
        (28, 1, PinFunction.I2C),      # GPIO 1 (ID_SC)
        (29, 5, PinFunction.GPIO),     # GPIO 5
        (30, None, PinFunction.GROUND), # GND
        (31, 6, PinFunction.GPIO),     # GPIO 6
        (32, 12, PinFunction.PWM),     # GPIO 12 (PWM)
        (33, 13, PinFunction.PWM),     # GPIO 13 (PWM)
        (34, None, PinFunction.GROUND), # GND
        (35, 19, PinFunction.GPIO),    # GPIO 19
        (36, 16, PinFunction.GPIO),    # GPIO 16
        (37, 26, PinFunction.GPIO),   # GPIO 26
        (38, 20, PinFunction.GPIO),   # GPIO 20
        (39, None, PinFunction.GROUND), # GND
        (40, 21, PinFunction.GPIO),   # GPIO 21
    ]
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pins: Dict[int, PinInfo] = {}
        self.pin_widgets: Dict[int, GPIOPinWidget] = {}
        self.monitoring = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_pins)
        
        self.setup_ui()
        self._initialize_pins()
        self._start_monitoring()
    
    def setup_ui(self) -> None:
        """Setup GPIO interface UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header = QLabel("GPIO Interface Monitor")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_pins)
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
        auto_detect_btn.clicked.connect(self._auto_detect_devices)
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
        
        # Split layout: Visual pins on left, table on right
        split_layout = QHBoxLayout()
        
        # Visual GPIO header (left side)
        visual_group = QGroupBox("GPIO Header (Visual)")
        visual_layout = QVBoxLayout(visual_group)
        
        # Create scroll area for pins
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        
        pins_container = QWidget()
        pins_layout = QVBoxLayout(pins_container)
        pins_layout.setSpacing(5)
        
        # Create two columns of pins (like physical header)
        columns_layout = QHBoxLayout()
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()
        
        # Add pins in two columns (physical layout)
        for i, (physical, bcm, func) in enumerate(self.PI_GPIO_PINS):
            if i < 20:  # Left column (pins 1-20)
                col = left_column
            else:  # Right column (pins 21-40)
                col = right_column
            
            pin_info = PinInfo(
                physical_pin=physical,
                bcm_pin=bcm,
                function=func,
            )
            self.pins[physical] = pin_info
            
            pin_widget = GPIOPinWidget(pin_info, self)
            self.pin_widgets[physical] = pin_widget
            col.addWidget(pin_widget)
        
        columns_layout.addLayout(left_column)
        columns_layout.addLayout(right_column)
        pins_layout.addLayout(columns_layout)
        pins_layout.addStretch()
        
        scroll.setWidget(pins_container)
        visual_layout.addWidget(scroll)
        split_layout.addWidget(visual_group, stretch=1)
        
        # Pin details table (right side)
        table_group = QGroupBox("Pin Details")
        table_layout = QVBoxLayout(table_group)
        
        self.pin_table = QTableWidget()
        self.pin_table.setColumnCount(6)
        self.pin_table.setHorizontalHeaderLabels([
            "Physical", "BCM", "Function", "Direction", "Value", "Device"
        ])
        self.pin_table.horizontalHeader().setStretchLastSection(True)
        self.pin_table.setAlternatingRowColors(True)
        self.pin_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self.pin_table)
        
        split_layout.addWidget(table_group, stretch=1)
        main_layout.addLayout(split_layout)
    
    def _initialize_pins(self) -> None:
        """Initialize GPIO pins."""
        if RPI_GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                LOGGER.info("GPIO initialized for monitoring")
            except Exception as e:
                LOGGER.error("Failed to initialize GPIO: %s", e)
        
        self._update_pin_table()
    
    def _start_monitoring(self) -> None:
        """Start monitoring GPIO pins."""
        self.monitoring = True
        self.monitor_timer.start(2000)  # Update every 2 seconds to reduce UI lag
        LOGGER.info("GPIO monitoring started")
    
    def _stop_monitoring(self) -> None:
        """Stop monitoring GPIO pins."""
        self.monitoring = False
        self.monitor_timer.stop()
        LOGGER.info("GPIO monitoring stopped")
    
    def _update_pins(self) -> None:
        """Update GPIO pin states."""
        if not self.monitoring:
            return
        
        # Only update a subset of pins per cycle to reduce load
        updated = False
        pin_list = list(self.pins.values())
        # Process max 10 pins per update cycle
        start_idx = getattr(self, '_update_index', 0)
        end_idx = min(start_idx + 10, len(pin_list))
        
        for pin_info in pin_list[start_idx:end_idx]:
            if pin_info.function == PinFunction.GPIO and pin_info.bcm_pin is not None:
                try:
                    if RPI_GPIO_AVAILABLE:
                        # Try to read pin (may fail if not configured)
                        try:
                            value = GPIO.input(pin_info.bcm_pin)
                            pin_info.value = value == GPIO.HIGH
                            pin_info.connected = True
                            pin_info.last_update = time.time()
                            updated = True
                        except (RuntimeError, ValueError):
                            # Pin not configured, try to detect if something is connected
                            pin_info.connected = self._detect_connection(pin_info.bcm_pin)
                except Exception as e:
                    LOGGER.debug("Error reading pin %d: %s", pin_info.bcm_pin, e)
            
            # Update visual widget (only if changed)
            if pin_info.physical_pin in self.pin_widgets:
                old_value = getattr(self.pin_widgets[pin_info.physical_pin].pin_info, 'value', None)
                if old_value != pin_info.value or not hasattr(self, '_last_table_update'):
                    self.pin_widgets[pin_info.physical_pin].update_pin_info(pin_info)
        
        # Cycle through all pins
        self._update_index = end_idx if end_idx < len(pin_list) else 0
        
        # Only update table every 5 cycles to reduce lag
        if not hasattr(self, '_table_update_counter'):
            self._table_update_counter = 0
        self._table_update_counter += 1
        if updated and self._table_update_counter >= 5:
            self._update_pin_table()
            self._table_update_counter = 0
            self._last_table_update = time.time()
    
    def _detect_connection(self, bcm_pin: int) -> bool:
        """Detect if something is connected to a GPIO pin."""
        if not RPI_GPIO_AVAILABLE:
            return False
        
        try:
            # Try to configure pin as input and read
            GPIO.setup(bcm_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            value1 = GPIO.input(bcm_pin)
            time.sleep(0.01)
            value2 = GPIO.input(bcm_pin)
            
            # If value changes or is not floating, something might be connected
            # This is a simple heuristic - could be improved
            return value1 != value2 or value1 != GPIO.HIGH
        except Exception:
            return False
    
    def _auto_detect_devices(self) -> None:
        """Auto-detect devices connected to GPIO pins."""
        LOGGER.info("Starting GPIO auto-detection...")
        self.status_label.setText("Auto-detecting devices...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 8px;")
        
        detected_count = 0
        
        # Check I2C devices
        try:
            import subprocess
            result = subprocess.run(
                ["i2cdetect", "-y", "1"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Parse I2C addresses
                for line in result.stdout.split('\n')[1:]:
                    if ':' in line:
                        addresses = line.split(':')[1].strip().split()
                        for addr in addresses:
                            if addr != '--' and addr != 'UU':
                                # I2C device detected
                                # Mark I2C pins as connected
                                for pin_info in self.pins.values():
                                    if pin_info.function == PinFunction.I2C:
                                        pin_info.connected = True
                                        pin_info.device_name = f"I2C Device 0x{addr}"
                                        detected_count += 1
        except Exception as e:
            LOGGER.debug("I2C detection failed: %s", e)
        
        # Check SPI devices
        try:
            spi_devices = list(Path("/dev").glob("spidev*"))
            if spi_devices:
                for pin_info in self.pins.values():
                    if pin_info.function == PinFunction.SPI:
                        pin_info.connected = True
                        pin_info.device_name = "SPI Device"
                        detected_count += 1
        except Exception as e:
            LOGGER.debug("SPI detection failed: %s", e)
        
        # Check UART devices
        try:
            uart_devices = list(Path("/dev").glob("ttyAMA*")) + list(Path("/dev").glob("ttyUSB*"))
            if uart_devices:
                for pin_info in self.pins.values():
                    if pin_info.function == PinFunction.UART:
                        pin_info.connected = True
                        pin_info.device_name = "UART Device"
                        detected_count += 1
        except Exception as e:
            LOGGER.debug("UART detection failed: %s", e)
        
        # Update visual widgets
        for pin_info in self.pins.values():
            if pin_info.physical_pin in self.pin_widgets:
                self.pin_widgets[pin_info.physical_pin].update_pin_info(pin_info)
        
        self._update_pin_table()
        
        self.status_label.setText(f"Monitoring: Active ({detected_count} devices detected)")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 8px;")
        LOGGER.info("Auto-detection complete: %d devices detected", detected_count)
    
    def _refresh_pins(self) -> None:
        """Refresh all GPIO pins."""
        self._update_pins()
        self._update_pin_table()
        LOGGER.info("GPIO pins refreshed")
    
    def _update_pin_table(self) -> None:
        """Update the pin details table."""
        self.pin_table.setRowCount(len(self.pins))
        
        for row, (physical, pin_info) in enumerate(sorted(self.pins.items())):
            # Physical pin
            self.pin_table.setItem(row, 0, QTableWidgetItem(str(physical)))
            
            # BCM pin
            bcm_text = str(pin_info.bcm_pin) if pin_info.bcm_pin is not None else "-"
            self.pin_table.setItem(row, 1, QTableWidgetItem(bcm_text))
            
            # Function
            func_item = QTableWidgetItem(pin_info.function.value)
            if pin_info.function == PinFunction.POWER:
                func_item.setForeground(QColor(255, 0, 0))
            elif pin_info.function == PinFunction.GROUND:
                func_item.setForeground(QColor(0, 0, 0))
            self.pin_table.setItem(row, 2, func_item)
            
            # Direction
            self.pin_table.setItem(row, 3, QTableWidgetItem(pin_info.direction.value))
            
            # Value
            if pin_info.value is not None:
                value_text = "HIGH" if pin_info.value else "LOW"
                value_item = QTableWidgetItem(value_text)
                value_item.setForeground(QColor(0, 150, 0) if pin_info.value else QColor(100, 100, 100))
                self.pin_table.setItem(row, 4, value_item)
            else:
                self.pin_table.setItem(row, 4, QTableWidgetItem("-"))
            
            # Device
            device_text = pin_info.device_name or ("Connected" if pin_info.connected else "-")
            device_item = QTableWidgetItem(device_text)
            if pin_info.connected:
                device_item.setForeground(QColor(0, 150, 255))
            self.pin_table.setItem(row, 5, device_item)
        
        self.pin_table.resizeColumnsToContents()
    
    def closeEvent(self, event) -> None:
        """Clean up on close."""
        self._stop_monitoring()
        super().closeEvent(event)


__all__ = ["GPIOInterfaceTab"]

