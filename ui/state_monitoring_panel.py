"""
State Monitoring Panel
Central panel with wireframe car model
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout

from ui.hud_theme import HUDTheme
from ui.hud_widgets import HUDLabel, GridBackgroundWidget
from ui.wireframe_car_widget import WireframeCarWidget


class StateMonitoringPanel(GridBackgroundWidget):
    """State monitoring panel with wireframe car."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = HUDLabel("STATE MONITORING", self.theme.colors.orange_accent, 16)
        layout.addWidget(title)
        
        # Wireframe car model
        self.car_widget = WireframeCarWidget()
        layout.addWidget(self.car_widget, stretch=1)
        
        layout.addStretch()
        
    def set_battery_charge(self, charge: float) -> None:
        """Update battery charge."""
        if hasattr(self, 'car_widget'):
            self.car_widget.set_battery_charge(charge)


__all__ = ["StateMonitoringPanel"]


