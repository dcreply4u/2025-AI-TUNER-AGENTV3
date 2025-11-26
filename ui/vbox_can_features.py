"""VBOX CAN Features Tab - CAN input/output configuration."""

from __future__ import annotations
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QCheckBox, QPushButton, QScrollArea


class VBOXCANFeaturesTab(QWidget):
    """CAN Features sub-tab."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # CAN Output
        output_group = QGroupBox("CAN Output")
        output_form = QFormLayout()
        self.can_format = QComboBox()
        self.can_format.addItems(["Motorola", "Intel"])
        output_form.addRow("Output Format:", self.can_format)
        self.can_output_enable = QCheckBox("Enable CAN Output")
        output_form.addRow("CAN Output:", self.can_output_enable)
        output_group.setLayout(output_form)
        content_layout.addWidget(output_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        pass

