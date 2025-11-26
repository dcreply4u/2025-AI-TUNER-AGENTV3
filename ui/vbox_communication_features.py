"""VBOX Communication Features Tab - Serial, Bluetooth, Voice."""

from __future__ import annotations
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QCheckBox, QComboBox, QScrollArea


class VBOXCommunicationFeaturesTab(QWidget):
    """Communication Features sub-tab."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Bluetooth
        bt_group = QGroupBox("Bluetooth")
        bt_form = QFormLayout()
        self.bluetooth_enable = QCheckBox("Enable Bluetooth")
        bt_form.addRow("Bluetooth:", self.bluetooth_enable)
        self.bt_rate = QComboBox()
        self.bt_rate.addItems(["20 Hz", "50 Hz", "100 Hz"])
        bt_form.addRow("Output Rate:", self.bt_rate)
        bt_group.setLayout(bt_form)
        content_layout.addWidget(bt_group)
        
        # Voice Tagging
        voice_group = QGroupBox("Voice Tagging")
        voice_form = QFormLayout()
        self.voice_enable = QCheckBox("Enable Voice Tagging")
        voice_form.addRow("Voice Tagging:", self.voice_enable)
        voice_group.setLayout(voice_form)
        content_layout.addWidget(voice_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        pass

