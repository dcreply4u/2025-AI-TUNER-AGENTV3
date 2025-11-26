"""VBOX ADAS Features Tab - ADAS testing modes."""

from __future__ import annotations
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QCheckBox, QDoubleSpinBox, QScrollArea
from ui.ui_scaling import get_scaled_size


class VBOXADASFeaturesTab(QWidget):
    """ADAS Features sub-tab."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # ADAS Mode
        mode_group = QGroupBox("ADAS Mode Selection")
        mode_form = QFormLayout()
        self.adas_mode = QComboBox()
        self.adas_mode.addItems(["Off", "1 Target", "2 Target", "3 Target", "Static Point", "Lane Departure", "Multi Static"])
        mode_form.addRow("ADAS Mode:", self.adas_mode)
        mode_group.setLayout(mode_form)
        content_layout.addWidget(mode_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        pass

