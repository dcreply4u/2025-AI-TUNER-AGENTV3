"""
VBOX Features Main Tab
Main tab with sub-tabs for GPS, IMU, ADAS, CAN, I/O, Communication, Logging, and Hardware features.
Matches VBOX 3i menu structure.
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QSizePolicy,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size


class VBOXFeaturesMain(QWidget):
    """Main VBOX Features tab with sub-tabs matching VBOX 3i menu structure."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup VBOX features tab with sub-tabs."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Set background
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Sub-tabs widget (scaled)
        self.sub_tabs = QTabWidget()
        sub_tab_padding_v = get_scaled_size(6)
        sub_tab_padding_h = get_scaled_size(15)
        sub_tab_font = get_scaled_font_size(10)
        sub_tab_border = get_scaled_size(1)
        sub_tab_margin = get_scaled_size(2)
        self.sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {sub_tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {sub_tab_padding_v}px {sub_tab_padding_h}px;
                margin-right: {sub_tab_margin}px;
                border: {sub_tab_border}px solid #404040;
                font-size: {sub_tab_font}px;
                min-height: {get_scaled_size(25)}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {get_scaled_size(2)}px solid #0080ff;
                color: #ffffff;
            }}
            QTabBar::tab:hover {{
                background-color: #333333;
            }}
        """)
        self.sub_tabs.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Import sub-tabs
        from ui.vbox_gps_features import VBOXGPSFeaturesTab
        from ui.vbox_imu_features import VBOXIMUFeaturesTab
        from ui.vbox_adas_features import VBOXADASFeaturesTab
        from ui.vbox_can_features import VBOXCANFeaturesTab
        from ui.vbox_io_features import VBOXIOFeaturesTab
        from ui.vbox_communication_features import VBOXCommunicationFeaturesTab
        from ui.vbox_logging_features import VBOXLoggingFeaturesTab
        from ui.vbox_hardware_features import VBOXHardwareFeaturesTab
        
        # GPS Features sub-tab
        self.gps_tab = VBOXGPSFeaturesTab()
        self.sub_tabs.addTab(self.gps_tab, "GPS Features")
        
        # IMU Features sub-tab
        self.imu_tab = VBOXIMUFeaturesTab()
        self.sub_tabs.addTab(self.imu_tab, "IMU Features")
        
        # ADAS Features sub-tab
        self.adas_tab = VBOXADASFeaturesTab()
        self.sub_tabs.addTab(self.adas_tab, "ADAS Features")
        
        # CAN Features sub-tab
        self.can_tab = VBOXCANFeaturesTab()
        self.sub_tabs.addTab(self.can_tab, "CAN Features")
        
        # I/O Features sub-tab
        self.io_tab = VBOXIOFeaturesTab()
        self.sub_tabs.addTab(self.io_tab, "I/O Features")
        
        # Communication Features sub-tab
        self.communication_tab = VBOXCommunicationFeaturesTab()
        self.sub_tabs.addTab(self.communication_tab, "Communication Features")
        
        # Logging Features sub-tab
        self.logging_tab = VBOXLoggingFeaturesTab()
        self.sub_tabs.addTab(self.logging_tab, "Logging Features")
        
        # Hardware Features sub-tab
        self.hardware_tab = VBOXHardwareFeaturesTab()
        self.sub_tabs.addTab(self.hardware_tab, "Hardware Features")
        
        main_layout.addWidget(self.sub_tabs, stretch=1)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update all sub-tabs with telemetry data."""
        if hasattr(self, 'gps_tab'):
            self.gps_tab.update_telemetry(data)
        if hasattr(self, 'imu_tab'):
            self.imu_tab.update_telemetry(data)
        if hasattr(self, 'adas_tab'):
            self.adas_tab.update_telemetry(data)
        if hasattr(self, 'can_tab'):
            self.can_tab.update_telemetry(data)
        if hasattr(self, 'io_tab'):
            self.io_tab.update_telemetry(data)

