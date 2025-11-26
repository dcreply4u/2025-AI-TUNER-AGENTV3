"""VBOX Hardware Features Tab - Hardware controls and indicators."""

from __future__ import annotations
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QVBoxLayout as VLayout, QLabel, QScrollArea


class VBOXHardwareFeaturesTab(QWidget):
    """Hardware Features sub-tab."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # LED Status
        led_group = QGroupBox("LED Indicators")
        led_layout = VLayout()
        self.pwr_led = QLabel("PWR: Green (Ready)")
        self.pwr_led.setStyleSheet("color: #0f0;")
        led_layout.addWidget(self.pwr_led)
        self.log_led = QLabel("LOG: Off")
        led_layout.addWidget(self.log_led)
        led_group.setLayout(led_layout)
        content_layout.addWidget(led_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        pass

