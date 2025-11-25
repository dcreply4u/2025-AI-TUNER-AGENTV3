"""
Import ECU Support Tab
Full support for Honda, Nissan, Toyota, Subaru, Mitsubishi, Mazda, VW, BMW, Audi ECUs
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet
from ui.ecu_tuning_widgets import AnalogGauge, RealTimeGraph, VETableWidget


class ImportECUTab(QWidget):
    """Import ECU Support tab with manufacturer-specific sub-tabs."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup import ECU tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Import ECU Support - Multi-Platform Tuning")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Manufacturer tabs
        self.manufacturer_tabs = QTabWidget()
        tab_stylesheet = get_scaled_stylesheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 8px 20px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 11px;
                min-height: 30px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 3px solid #0080ff;
            }
        """)
        self.manufacturer_tabs.setStyleSheet(tab_stylesheet)
        
        # Add manufacturer sub-tabs
        self.manufacturer_tabs.addTab(self._create_honda_tab(), "Honda")
        self.manufacturer_tabs.addTab(self._create_nissan_tab(), "Nissan")
        self.manufacturer_tabs.addTab(self._create_toyota_tab(), "Toyota")
        self.manufacturer_tabs.addTab(self._create_subaru_tab(), "Subaru")
        self.manufacturer_tabs.addTab(self._create_mitsubishi_tab(), "Mitsubishi")
        self.manufacturer_tabs.addTab(self._create_mazda_tab(), "Mazda")
        self.manufacturer_tabs.addTab(self._create_vw_tab(), "VW/Audi")
        self.manufacturer_tabs.addTab(self._create_bmw_tab(), "BMW")
        
        main_layout.addWidget(self.manufacturer_tabs, stretch=1)
    
    def _create_honda_tab(self) -> QWidget:
        """Create Honda-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.honda_model = QComboBox()
        self.honda_model.addItems([
            "Civic (EG/EK)", "Civic (EP/ES)", "Civic (FG/FK)", "Civic (FC)", 
            "S2000 (AP1)", "S2000 (AP2)", "Integra (DC2)", "Integra (DC5)",
            "Accord", "Prelude", "CRX", "Custom"
        ])
        self.honda_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.honda_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.honda_engine = QComboBox()
        self.honda_engine.addItems([
            "B16A", "B16B", "B18C", "B18C5", "B20B", "F20C", "F22C", 
            "K20A", "K24A", "H22A", "D16", "Custom"
        ])
        self.honda_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.honda_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # VTEC Control
        feature_tabs.addTab(self._create_vtec_control(), "VTEC Control")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("Honda"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control (for turbo builds)
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Idle Air Control
        feature_tabs.addTab(self._create_iac_control(), "Idle Control")
        
        # Auxiliary I/O
        feature_tabs.addTab(self._create_aux_io(), "Auxiliary I/O")
        
        # CAN Network
        feature_tabs.addTab(self._create_can_network(), "CAN Network")
        
        # Safety Features
        feature_tabs.addTab(self._create_safety_features(), "Safety Features")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_vtec_control(self) -> QWidget:
        """Create VTEC control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("VTEC (Variable Valve Timing and Lift Electronic Control)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # VTEC engagement map
        vtec_map_group = QGroupBox("VTEC Engagement Map (vs RPM & TPS)")
        vtec_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vtec_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)  # RPM
        table.setColumnCount(10)  # TPS
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        tps_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, tps in enumerate(tps_values):
            item = QTableWidgetItem(f"{tps}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with VTEC engagement (ON/OFF)
        for row in range(10):
            for col in range(10):
                # VTEC typically engages at 5500-6000 RPM with sufficient throttle
                if rpm_values[row] >= 5500 and tps_values[col] >= 50:
                    item = QTableWidgetItem("ON")
                    item.setBackground(QBrush(QColor("#00ff00")))
                else:
                    item = QTableWidgetItem("OFF")
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                table.setItem(row, col, item)
        
        vtec_map_layout.addWidget(table)
        vtec_map_group.setLayout(vtec_map_layout)
        layout.addWidget(vtec_map_group)
        
        # VTEC settings
        settings_group = QGroupBox("VTEC Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("VTEC Engagement RPM:"), 0, 0)
        self.vtec_rpm = QSpinBox()
        self.vtec_rpm.setRange(3000, 9000)
        self.vtec_rpm.setValue(5500)
        self.vtec_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.vtec_rpm, 0, 1)
        
        settings_layout.addWidget(QLabel("Min TPS for VTEC:"), 1, 0)
        self.vtec_min_tps = QDoubleSpinBox()
        self.vtec_min_tps.setRange(0, 100)
        self.vtec_min_tps.setValue(50.0)
        self.vtec_min_tps.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.vtec_min_tps, 1, 1)
        
        settings_layout.addWidget(QLabel("VTEC Oil Pressure (psi):"), 2, 0)
        self.vtec_oil_pressure = QDoubleSpinBox()
        self.vtec_oil_pressure.setRange(0, 100)
        self.vtec_oil_pressure.setValue(25.0)
        self.vtec_oil_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.vtec_oil_pressure, 2, 1)
        
        self.vtec_enabled = QCheckBox("VTEC Enabled")
        self.vtec_enabled.setChecked(True)
        self.vtec_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.vtec_enabled, 3, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_nissan_tab(self) -> QWidget:
        """Create Nissan-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.nissan_model = QComboBox()
        self.nissan_model.addItems([
            "Skyline GT-R (R32)", "Skyline GT-R (R33)", "Skyline GT-R (R34)",
            "240SX (S13)", "240SX (S14)", "240SX (S15)",
            "350Z", "370Z", "Silvia", "180SX", "Custom"
        ])
        self.nissan_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.nissan_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.nissan_engine = QComboBox()
        self.nissan_engine.addItems([
            "RB26DETT", "RB25DET", "RB20DET", "SR20DET", "SR20DE",
            "VQ35DE", "VQ37VHR", "KA24DE", "CA18DET", "Custom"
        ])
        self.nissan_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.nissan_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # VVT Control (Variable Valve Timing)
        feature_tabs.addTab(self._create_vvt_control("Nissan"), "VVT Control")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("Nissan"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_toyota_tab(self) -> QWidget:
        """Create Toyota-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.toyota_model = QComboBox()
        self.toyota_model.addItems([
            "Supra (Mk IV)", "Supra (A90)", "86/GR86", "Celica",
            "MR2", "Corolla", "AE86", "Custom"
        ])
        self.toyota_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.toyota_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.toyota_engine = QComboBox()
        self.toyota_engine.addItems([
            "2JZ-GTE", "2JZ-GE", "B58", "FA20", "4A-GE", "3S-GTE",
            "1JZ-GTE", "4A-GZE", "Custom"
        ])
        self.toyota_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.toyota_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # VVTi Control (Variable Valve Timing - intelligent)
        feature_tabs.addTab(self._create_vvti_control(), "VVTi Control")
        
        # Drive-by-Wire (for A90 Supra)
        feature_tabs.addTab(self._create_dbw_control(), "Drive-by-Wire")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("Toyota"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Idle Air Control
        feature_tabs.addTab(self._create_iac_control(), "Idle Control")
        
        # Auxiliary I/O
        feature_tabs.addTab(self._create_aux_io(), "Auxiliary I/O")
        
        # CAN Network
        feature_tabs.addTab(self._create_can_network(), "CAN Network")
        
        # Safety Features
        feature_tabs.addTab(self._create_safety_features(), "Safety Features")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_subaru_tab(self) -> QWidget:
        """Create Subaru-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.subaru_model = QComboBox()
        self.subaru_model.addItems([
            "Impreza WRX", "Impreza STI", "BRZ", "Forester XT",
            "Legacy GT", "Custom"
        ])
        self.subaru_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.subaru_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.subaru_engine = QComboBox()
        self.subaru_engine.addItems([
            "EJ205", "EJ207", "EJ257", "FA20", "FA24", "Custom"
        ])
        self.subaru_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.subaru_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # AVCS Control (Active Valve Control System)
        feature_tabs.addTab(self._create_avcs_control(), "AVCS Control")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("Subaru"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Idle Air Control
        feature_tabs.addTab(self._create_iac_control(), "Idle Control")
        
        # Auxiliary I/O
        feature_tabs.addTab(self._create_aux_io(), "Auxiliary I/O")
        
        # CAN Network
        feature_tabs.addTab(self._create_can_network(), "CAN Network")
        
        # Safety Features
        feature_tabs.addTab(self._create_safety_features(), "Safety Features")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_mitsubishi_tab(self) -> QWidget:
        """Create Mitsubishi-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.mitsubishi_model = QComboBox()
        self.mitsubishi_model.addItems([
            "Lancer Evolution (IV)", "Lancer Evolution (V)", "Lancer Evolution (VI)",
            "Lancer Evolution (VII)", "Lancer Evolution (VIII)", "Lancer Evolution (IX)",
            "Lancer Evolution (X)", "3000GT VR-4", "Custom"
        ])
        self.mitsubishi_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.mitsubishi_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.mitsubishi_engine = QComboBox()
        self.mitsubishi_engine.addItems([
            "4G63", "4G63T", "4B11T", "6G72", "Custom"
        ])
        self.mitsubishi_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.mitsubishi_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # MIVEC Control (Mitsubishi Innovative Valve timing Electronic Control)
        feature_tabs.addTab(self._create_mivec_control(), "MIVEC Control")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("Mitsubishi"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Idle Air Control
        feature_tabs.addTab(self._create_iac_control(), "Idle Control")
        
        # Auxiliary I/O
        feature_tabs.addTab(self._create_aux_io(), "Auxiliary I/O")
        
        # CAN Network
        feature_tabs.addTab(self._create_can_network(), "CAN Network")
        
        # Safety Features
        feature_tabs.addTab(self._create_safety_features(), "Safety Features")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_mazda_tab(self) -> QWidget:
        """Create Mazda-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.mazda_model = QComboBox()
        self.mazda_model.addItems([
            "RX-7 (FD)", "RX-8", "Miata/MX-5 (NA)", "Miata/MX-5 (NB)",
            "Miata/MX-5 (NC)", "Miata/MX-5 (ND)", "Mazdaspeed3", "Mazdaspeed6", "Custom"
        ])
        self.mazda_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.mazda_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.mazda_engine = QComboBox()
        self.mazda_engine.addItems([
            "13B-REW", "13B-MSP", "BP", "L3-VDT", "MZR", "Skyactiv", "Custom"
        ])
        self.mazda_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.mazda_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # Rotary-specific features
        feature_tabs.addTab(self._create_rotary_control(), "Rotary Engine")
        
        # VVT Control
        feature_tabs.addTab(self._create_vvt_control("Mazda"), "VVT Control")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("Mazda"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Idle Air Control
        feature_tabs.addTab(self._create_iac_control(), "Idle Control")
        
        # Auxiliary I/O
        feature_tabs.addTab(self._create_aux_io(), "Auxiliary I/O")
        
        # CAN Network
        feature_tabs.addTab(self._create_can_network(), "CAN Network")
        
        # Safety Features
        feature_tabs.addTab(self._create_safety_features(), "Safety Features")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_vw_tab(self) -> QWidget:
        """Create VW/Audi-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Brand/Model:"))
        self.vw_model = QComboBox()
        self.vw_model.addItems([
            "VW Golf GTI", "VW Golf R", "VW Jetta", "Audi A3", "Audi A4",
            "Audi S4", "Audi TT", "Audi R8", "Custom"
        ])
        self.vw_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.vw_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.vw_engine = QComboBox()
        self.vw_engine.addItems([
            "EA888", "EA113", "EA855", "VR6", "1.8T", "2.0T", "Custom"
        ])
        self.vw_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.vw_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # VVT Control
        feature_tabs.addTab(self._create_vvt_control("VW/Audi"), "VVT Control")
        
        # Drive-by-Wire
        feature_tabs.addTab(self._create_dbw_control(), "Drive-by-Wire")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("VW/Audi"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Idle Air Control
        feature_tabs.addTab(self._create_iac_control(), "Idle Control")
        
        # Auxiliary I/O
        feature_tabs.addTab(self._create_aux_io(), "Auxiliary I/O")
        
        # CAN Network
        feature_tabs.addTab(self._create_can_network(), "CAN Network")
        
        # Safety Features
        feature_tabs.addTab(self._create_safety_features(), "Safety Features")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_bmw_tab(self) -> QWidget:
        """Create BMW-specific ECU tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Vehicle selection
        vehicle_group = QGroupBox("Vehicle Selection")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vehicle_layout = QHBoxLayout()
        
        vehicle_layout.addWidget(QLabel("Model:"))
        self.bmw_model = QComboBox()
        self.bmw_model.addItems([
            "3 Series (E36)", "3 Series (E46)", "3 Series (E90)", "M3",
            "1 Series", "Z3", "Z4", "Custom"
        ])
        self.bmw_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.bmw_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.bmw_engine = QComboBox()
        self.bmw_engine.addItems([
            "S50", "S52", "S54", "S55", "N54", "N55", "B58", "M50", "M52", "Custom"
        ])
        self.bmw_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.bmw_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        feature_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # VANOS Control (Variable Nockenwellen Steuerung)
        feature_tabs.addTab(self._create_vanos_control(), "VANOS Control")
        
        # Drive-by-Wire
        feature_tabs.addTab(self._create_dbw_control(), "Drive-by-Wire")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config("BMW"), "Sensors")
        
        # Fuel/Ignition Maps
        feature_tabs.addTab(self._create_fuel_ignition_maps(), "Fuel/Ignition")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control(), "Boost Control")
        
        # Datalogging
        feature_tabs.addTab(self._create_datalogging(), "Datalogging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_vvti_control(self) -> QWidget:
        """Create VVTi control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("VVTi (Variable Valve Timing - intelligent)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # VVTi map
        vvti_map_group = QGroupBox("VVTi Advance Map (vs RPM & Load)")
        vvti_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vvti_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with VVTi advance values
        for row in range(10):
            for col in range(10):
                advance = (load_values[col] / 100) * 40 + (rpm_values[row] / 10000) * 20
                advance = max(0, min(60, advance))
                
                item = QTableWidgetItem(f"{advance:.0f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if advance > 45:
                    item.setBackground(QBrush(QColor("#00ff00")))
                elif advance > 30:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                
                table.setItem(row, col, item)
        
        vvti_map_layout.addWidget(table)
        vvti_map_group.setLayout(vvti_map_layout)
        layout.addWidget(vvti_map_group)
        
        # VVTi settings
        settings_group = QGroupBox("VVTi Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Max Advance (°):"), 0, 0)
        self.vvti_max_advance = QDoubleSpinBox()
        self.vvti_max_advance.setRange(0, 60)
        self.vvti_max_advance.setValue(40.0)
        self.vvti_max_advance.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.vvti_max_advance, 0, 1)
        
        self.vvti_enabled = QCheckBox("VVTi Enabled")
        self.vvti_enabled.setChecked(True)
        self.vvti_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.vvti_enabled, 1, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_vvt_control(self, manufacturer: str) -> QWidget:
        """Create generic VVT control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel(f"{manufacturer} VVT (Variable Valve Timing) Control")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # VVT map
        vvt_map_group = QGroupBox("VVT Advance Map (vs RPM & Load)")
        vvt_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vvt_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with VVT advance values
        for row in range(10):
            for col in range(10):
                advance = (load_values[col] / 100) * 35 + (rpm_values[row] / 10000) * 15
                advance = max(0, min(50, advance))
                
                item = QTableWidgetItem(f"{advance:.0f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if advance > 35:
                    item.setBackground(QBrush(QColor("#00ff00")))
                elif advance > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                
                table.setItem(row, col, item)
        
        vvt_map_layout.addWidget(table)
        vvt_map_group.setLayout(vvt_map_layout)
        layout.addWidget(vvt_map_group)
        
        layout.addStretch()
        return panel
    
    def _create_avcs_control(self) -> QWidget:
        """Create AVCS (Active Valve Control System) control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("AVCS (Active Valve Control System) - Subaru")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # AVCS map (similar to VVT)
        avcs_map_group = QGroupBox("AVCS Advance Map (vs RPM & Load)")
        avcs_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        avcs_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with AVCS advance values
        for row in range(10):
            for col in range(10):
                advance = (load_values[col] / 100) * 30 + (rpm_values[row] / 10000) * 20
                advance = max(0, min(50, advance))
                
                item = QTableWidgetItem(f"{advance:.0f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if advance > 35:
                    item.setBackground(QBrush(QColor("#00ff00")))
                elif advance > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                
                table.setItem(row, col, item)
        
        avcs_map_layout.addWidget(table)
        avcs_map_group.setLayout(avcs_map_layout)
        layout.addWidget(avcs_map_group)
        
        layout.addStretch()
        return panel
    
    def _create_mivec_control(self) -> QWidget:
        """Create MIVEC control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("MIVEC (Mitsubishi Innovative Valve timing Electronic Control)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # MIVEC map (similar to VTEC)
        mivec_map_group = QGroupBox("MIVEC Engagement Map (vs RPM & TPS)")
        mivec_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        mivec_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        tps_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, tps in enumerate(tps_values):
            item = QTableWidgetItem(f"{tps}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with MIVEC engagement
        for row in range(10):
            for col in range(10):
                if rpm_values[row] >= 5000 and tps_values[col] >= 50:
                    item = QTableWidgetItem("ON")
                    item.setBackground(QBrush(QColor("#00ff00")))
                else:
                    item = QTableWidgetItem("OFF")
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                table.setItem(row, col, item)
        
        mivec_map_layout.addWidget(table)
        mivec_map_group.setLayout(mivec_map_layout)
        layout.addWidget(mivec_map_group)
        
        layout.addStretch()
        return panel
    
    def _create_rotary_control(self) -> QWidget:
        """Create rotary engine-specific control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Rotary Engine (Wankel) Specific Controls")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Rotary-specific settings
        settings_group = QGroupBox("Rotary Engine Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Rotor Count:"))
        self.rotor_count = QComboBox()
        self.rotor_count.addItems(["2-Rotor (13B)", "3-Rotor (20B)", "4-Rotor (26B)"])
        self.rotor_count.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.rotor_count)
        
        settings_layout.addWidget(QLabel("Apex Seal Type:"))
        self.apex_seal = QComboBox()
        self.apex_seal.addItems(["Stock", "Ceramic", "Carbon", "Custom"])
        self.apex_seal.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.apex_seal)
        
        settings_layout.addWidget(QLabel("Port Type:"))
        self.port_type = QComboBox()
        self.port_type.addItems(["Side Port", "Peripheral Port", "Bridge Port", "Monster Port"])
        self.port_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.port_type)
        
        # Trailing Ignition (rotary-specific)
        settings_layout.addWidget(QLabel("Trailing Ignition Enabled:"))
        self.trailing_ignition = QCheckBox("Enable Trailing Ignition")
        self.trailing_ignition.setChecked(True)
        self.trailing_ignition.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.trailing_ignition)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_vanos_control(self) -> QWidget:
        """Create VANOS control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("VANOS (Variable Nockenwellen Steuerung) - BMW")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # VANOS map
        vanos_map_group = QGroupBox("VANOS Advance Map (vs RPM & Load)")
        vanos_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        vanos_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)
        table.setColumnCount(10)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with VANOS advance values
        for row in range(10):
            for col in range(10):
                advance = (load_values[col] / 100) * 45 + (rpm_values[row] / 10000) * 25
                advance = max(0, min(70, advance))
                
                item = QTableWidgetItem(f"{advance:.0f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if advance > 50:
                    item.setBackground(QBrush(QColor("#00ff00")))
                elif advance > 30:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                
                table.setItem(row, col, item)
        
        vanos_map_layout.addWidget(table)
        vanos_map_group.setLayout(vanos_map_layout)
        layout.addWidget(vanos_map_group)
        
        layout.addStretch()
        return panel
    
    def _create_dbw_control(self) -> QWidget:
        """Create Drive-by-Wire control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Drive-by-Wire (DBW) Throttle Control")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # DBW throttle map
        dbw_map_group = QGroupBox("Throttle Response Map (Pedal Position vs Actual Throttle)")
        dbw_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        dbw_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(1)  # Single row for throttle curve
        table.setColumnCount(10)  # Pedal positions
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(100)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        pedal_values = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col in range(10):
            item = QTableWidgetItem(f"{pedal_values[col]}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        item = QTableWidgetItem("Throttle %")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setVerticalHeaderItem(0, item)
        
        # Fill with throttle response (can be linear or aggressive)
        for col in range(10):
            # Linear response (can be modified for aggressive/smooth)
            throttle = pedal_values[col]
            item = QTableWidgetItem(f"{throttle}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QBrush(QColor("#ffffff")))
            
            if throttle > 80:
                item.setBackground(QBrush(QColor("#00ff00")))
            elif throttle > 50:
                item.setBackground(QBrush(QColor("#0080ff")))
            else:
                item.setBackground(QBrush(QColor("#2a2a2a")))
            
            table.setItem(0, col, item)
        
        dbw_map_layout.addWidget(table)
        dbw_map_group.setLayout(dbw_map_layout)
        layout.addWidget(dbw_map_group)
        
        # DBW settings
        settings_group = QGroupBox("DBW Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Response Mode:"), 0, 0)
        self.dbw_mode = QComboBox()
        self.dbw_mode.addItems(["Linear", "Aggressive", "Smooth", "Custom"])
        self.dbw_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.dbw_mode, 0, 1)
        
        settings_layout.addWidget(QLabel("Max Throttle Rate (%/sec):"), 1, 0)
        self.dbw_rate = QDoubleSpinBox()
        self.dbw_rate.setRange(10, 500)
        self.dbw_rate.setValue(200.0)
        self.dbw_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.dbw_rate, 1, 1)
        
        self.dbw_enabled = QCheckBox("Drive-by-Wire Enabled")
        self.dbw_enabled.setChecked(True)
        self.dbw_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.dbw_enabled, 2, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_sensor_config(self, manufacturer: str) -> QWidget:
        """Create sensor configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel(f"{manufacturer} Sensor Configuration")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Sensor table
        sensor_group = QGroupBox("Sensor Inputs")
        sensor_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        sensor_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(15)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Sensor", "Type", "Pin/Channel", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(400)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        sensors = [
            ("Crankshaft Position (CKP)", "Hall/Magnetic", "Pin 1", "Active"),
            ("Camshaft Position (CMP)", "Hall/Magnetic", "Pin 2", "Active"),
            ("MAP Sensor", "Analog 0-5V", "Pin 3", "Active"),
            ("IAT Sensor", "Analog 0-5V", "Pin 4", "Active"),
            ("Coolant Temp", "Analog 0-5V", "Pin 5", "Active"),
            ("Wideband O2 (Lambda)", "Analog 0-5V", "Pin 6", "Active"),
            ("TPS", "Analog 0-5V", "Pin 7", "Active"),
            ("Knock Sensor", "Piezoelectric", "Pin 8", "Active"),
            ("Fuel Pressure", "Analog 0-5V", "Pin 9", "Active"),
            ("Oil Pressure", "Analog 0-5V", "Pin 10", "Active"),
            ("Wheel Speed FL", "Hall/Magnetic", "Pin 11", "Active"),
            ("Wheel Speed FR", "Hall/Magnetic", "Pin 12", "Active"),
            ("Wheel Speed RL", "Hall/Magnetic", "Pin 13", "Active"),
            ("Wheel Speed RR", "Hall/Magnetic", "Pin 14", "Active"),
            ("Flex Fuel Sensor", "Frequency", "Pin 15", "Active"),
        ]
        
        for row, (sensor, sensor_type, pin, status) in enumerate(sensors):
            table.setItem(row, 0, QTableWidgetItem(sensor))
            table.setItem(row, 1, QTableWidgetItem(sensor_type))
            table.setItem(row, 2, QTableWidgetItem(pin))
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(QBrush(QColor("#00ff00")))
            else:
                status_item.setForeground(QBrush(QColor("#ff0000")))
            table.setItem(row, 3, status_item)
        
        sensor_layout.addWidget(table)
        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)
        
        layout.addStretch()
        return panel
    
    def _create_fuel_ignition_maps(self) -> QWidget:
        """Create fuel and ignition maps panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for Fuel and Ignition
        maps_tabs = QTabWidget()
        maps_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # Fuel Map (VE Table)
        fuel_tab = QWidget()
        fuel_layout = QVBoxLayout(fuel_tab)
        fuel_layout.setContentsMargins(10, 10, 10, 10)
        
        fuel_title = QLabel("Fuel Map (VE Table) - Full control over injector pulse width and flow rates")
        fuel_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        fuel_layout.addWidget(fuel_title)
        
        self.fuel_ve_table = VETableWidget()
        fuel_layout.addWidget(self.fuel_ve_table, stretch=1)
        maps_tabs.addTab(fuel_tab, "Fuel Map")
        
        # Ignition Map
        ignition_tab = QWidget()
        ignition_layout = QVBoxLayout(ignition_tab)
        ignition_layout.setContentsMargins(10, 10, 10, 10)
        
        ignition_title = QLabel("Ignition Timing Map - Control over timing maps, dwell settings, and cylinder trim")
        ignition_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        ignition_layout.addWidget(ignition_title)
        
        # Use VETableWidget for ignition (same structure)
        self.ignition_table = VETableWidget()
        ignition_layout.addWidget(self.ignition_table, stretch=1)
        maps_tabs.addTab(ignition_tab, "Ignition Map")
        
        layout.addWidget(maps_tabs)
        return panel
    
    def _create_boost_control(self) -> QWidget:
        """Create boost control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Boost Control - Advanced open and closed-loop strategies")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Boost control map
        boost_map_group = QGroupBox("Target Boost Map (vs RPM & Gear)")
        boost_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        boost_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(6)  # Gears
        table.setColumnCount(10)  # RPM
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(300)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        gear_values = [1, 2, 3, 4, 5, 6]
        for row, gear in enumerate(gear_values):
            item = QTableWidgetItem(f"Gear {gear}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with boost targets (lower in lower gears)
        for row in range(6):
            for col in range(10):
                base_boost = 15 + (rpm_values[col] / 11000) * 15
                # Reduce boost in lower gears
                if gear_values[row] <= 2:
                    boost = base_boost * 0.6
                elif gear_values[row] == 3:
                    boost = base_boost * 0.8
                else:
                    boost = base_boost
                boost = max(0, min(30, boost))
                
                item = QTableWidgetItem(f"{boost:.1f}psi")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if boost > 25:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif boost > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))
                elif boost > 15:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))
                
                table.setItem(row, col, item)
        
        boost_map_layout.addWidget(table)
        boost_map_group.setLayout(boost_map_layout)
        layout.addWidget(boost_map_group)
        
        # Boost control settings
        settings_group = QGroupBox("Boost Control Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Control Mode:"), 0, 0)
        self.boost_mode = QComboBox()
        self.boost_mode.addItems(["Open Loop", "Closed Loop", "Hybrid"])
        self.boost_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.boost_mode, 0, 1)
        
        settings_layout.addWidget(QLabel("Max Boost (psi):"), 1, 0)
        self.max_boost = QDoubleSpinBox()
        self.max_boost.setRange(0, 50)
        self.max_boost.setValue(25.0)
        self.max_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_boost, 1, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_datalogging(self) -> QWidget:
        """Create datalogging panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Onboard Datalogging - Essential for post-race analysis and tuning")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Datalogging settings
        settings_group = QGroupBox("Datalogging Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        
        settings_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.log_sample_rate = QComboBox()
        self.log_sample_rate.addItems(["10", "20", "50", "100", "200", "500", "1000"])
        self.log_sample_rate.setCurrentIndex(4)  # 200 Hz
        self.log_sample_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.log_sample_rate)
        
        settings_layout.addWidget(QLabel("Memory Size (MB):"))
        self.log_memory = QSpinBox()
        self.log_memory.setRange(10, 1000)
        self.log_memory.setValue(100)
        self.log_memory.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.log_memory)
        
        self.auto_logging = QCheckBox("Auto Start/Stop Logging")
        self.auto_logging.setChecked(True)
        self.auto_logging.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.auto_logging)
        
        settings_layout.addWidget(QLabel("Trigger Conditions:"))
        self.log_trigger = QComboBox()
        self.log_trigger.addItems([
            "Manual", "RPM > Threshold", "TPS > Threshold", 
            "Boost > Threshold", "Always On"
        ])
        self.log_trigger.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.log_trigger)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Real-time graph
        graph_group = QGroupBox("Real-Time Data Graph")
        graph_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        graph_layout = QVBoxLayout()
        
        self.datalog_graph = RealTimeGraph()
        self.datalog_graph.setMinimumHeight(300)
        graph_layout.addWidget(self.datalog_graph)
        
        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)
        
        layout.addStretch()
        return panel
    
    def _create_iac_control(self) -> QWidget:
        """Create Idle Air Control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Idle Air Control (IAC) - Stable idle speed management")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # IAC settings
        settings_group = QGroupBox("IAC Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("IAC Type:"), 0, 0)
        self.iac_type = QComboBox()
        self.iac_type.addItems(["Stepper Motor", "PWM Valve", "Solenoid", "E-Throttle"])
        self.iac_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.iac_type, 0, 1)
        
        settings_layout.addWidget(QLabel("Target Idle RPM:"), 1, 0)
        self.target_idle_rpm = QSpinBox()
        self.target_idle_rpm.setRange(500, 2000)
        self.target_idle_rpm.setValue(850)
        self.target_idle_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.target_idle_rpm, 1, 1)
        
        settings_layout.addWidget(QLabel("Idle RPM Tolerance:"), 2, 0)
        self.idle_tolerance = QSpinBox()
        self.idle_tolerance.setRange(10, 200)
        self.idle_tolerance.setValue(50)
        self.idle_tolerance.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.idle_tolerance, 2, 1)
        
        self.closed_loop_idle = QCheckBox("Closed-Loop Idle Control")
        self.closed_loop_idle.setChecked(True)
        self.closed_loop_idle.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.closed_loop_idle, 3, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_aux_io(self) -> QWidget:
        """Create Auxiliary Inputs/Outputs panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Auxiliary Inputs/Outputs (I/O) - Programmable I/O channels for external devices")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # I/O table
        io_group = QGroupBox("Programmable I/O Channels")
        io_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        io_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(16)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Channel", "Type", "Function", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(400)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        io_channels = [
            ("Output 1", "Digital", "Extra Fuel Pump", "Active"),
            ("Output 2", "Digital", "Cooling Fan", "Active"),
            ("Output 3", "Digital", "Nitrous Solenoid", "Inactive"),
            ("Output 4", "Digital", "Boost Solenoid", "Active"),
            ("Output 5", "PWM", "Wastegate Control", "Active"),
            ("Output 6", "PWM", "Idle Solenoid", "Active"),
            ("Output 7", "Digital", "Check Engine Light", "Inactive"),
            ("Output 8", "Digital", "Shift Light", "Active"),
            ("Input 1", "Digital", "Launch Control Switch", "Active"),
            ("Input 2", "Digital", "Traction Control Switch", "Active"),
            ("Input 3", "Digital", "Boost Level Switch", "Active"),
            ("Input 4", "Analog", "External MAP", "Active"),
            ("Input 5", "Analog", "External Temp", "Inactive"),
            ("Input 6", "Frequency", "VSS Input", "Active"),
            ("Input 7", "Digital", "Clutch Switch", "Active"),
            ("Input 8", "Digital", "Brake Switch", "Active"),
        ]
        
        for row, (channel, io_type, function, status) in enumerate(io_channels):
            table.setItem(row, 0, QTableWidgetItem(channel))
            table.setItem(row, 1, QTableWidgetItem(io_type))
            table.setItem(row, 2, QTableWidgetItem(function))
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(QBrush(QColor("#00ff00")))
            else:
                status_item.setForeground(QBrush(QColor("#888888")))
            table.setItem(row, 3, status_item)
        
        io_layout.addWidget(table)
        io_group.setLayout(io_layout)
        layout.addWidget(io_group)
        
        layout.addStretch()
        return panel
    
    def _create_can_network(self) -> QWidget:
        """Create CAN Network Communication panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("CAN Network Communication - Integration with dashes, input expanders, and modules")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # CAN settings
        can_group = QGroupBox("CAN Network Settings")
        can_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        can_layout = QVBoxLayout()
        
        can_layout.addWidget(QLabel("CAN Bus Speed:"))
        self.can_speed = QComboBox()
        self.can_speed.addItems(["125 kbps", "250 kbps", "500 kbps", "1000 kbps"])
        self.can_speed.setCurrentIndex(2)  # 500 kbps
        self.can_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        can_layout.addWidget(self.can_speed)
        
        can_layout.addWidget(QLabel("CAN Devices:"))
        can_devices_table = QTableWidget()
        can_devices_table.setRowCount(8)
        can_devices_table.setColumnCount(3)
        can_devices_table.setHorizontalHeaderLabels(["Device", "CAN ID", "Status"])
        can_devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        can_devices_table.setMinimumHeight(200)
        can_devices_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        
        can_devices = [
            ("Digital Dash", "0x100", "Connected"),
            ("Input Expander", "0x200", "Connected"),
            ("Wideband Controller", "0x300", "Connected"),
            ("Boost Controller", "0x400", "Connected"),
            ("Traction Control", "0x500", "Disconnected"),
            ("Data Logger", "0x600", "Connected"),
            ("Display Module", "0x700", "Disconnected"),
            ("Custom Device", "0x800", "Disconnected"),
        ]
        
        for row, (device, can_id, status) in enumerate(can_devices):
            can_devices_table.setItem(row, 0, QTableWidgetItem(device))
            can_devices_table.setItem(row, 1, QTableWidgetItem(can_id))
            status_item = QTableWidgetItem(status)
            if status == "Connected":
                status_item.setForeground(QBrush(QColor("#00ff00")))
            else:
                status_item.setForeground(QBrush(QColor("#ff0000")))
            can_devices_table.setItem(row, 2, status_item)
        
        can_layout.addWidget(can_devices_table)
        can_group.setLayout(can_layout)
        layout.addWidget(can_group)
        
        layout.addStretch()
        return panel
    
    def _create_safety_features(self) -> QWidget:
        """Create advanced safety features panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Advanced Safety Features - Engine protection strategies")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Safety limits
        limits_group = QGroupBox("Safety Limits & Protection")
        limits_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        limits_layout = QGridLayout()
        
        limits_layout.addWidget(QLabel("Max AFR (Lean):"), 0, 0)
        self.max_afr = QDoubleSpinBox()
        self.max_afr.setRange(14.0, 20.0)
        self.max_afr.setValue(16.0)
        self.max_afr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.max_afr, 0, 1)
        
        limits_layout.addWidget(QLabel("Min AFR (Rich):"), 1, 0)
        self.min_afr = QDoubleSpinBox()
        self.min_afr.setRange(10.0, 14.0)
        self.min_afr.setValue(11.0)
        self.min_afr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.min_afr, 1, 1)
        
        limits_layout.addWidget(QLabel("Max Oil Temp (°C):"), 2, 0)
        self.max_oil_temp = QSpinBox()
        self.max_oil_temp.setRange(100, 150)
        self.max_oil_temp.setValue(130)
        self.max_oil_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.max_oil_temp, 2, 1)
        
        limits_layout.addWidget(QLabel("Min Oil Pressure (psi):"), 3, 0)
        self.min_oil_pressure_safety = QDoubleSpinBox()
        self.min_oil_pressure_safety.setRange(0, 100)
        self.min_oil_pressure_safety.setValue(20.0)
        self.min_oil_pressure_safety.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.min_oil_pressure_safety, 3, 1)
        
        limits_layout.addWidget(QLabel("Max Coolant Temp (°C):"), 4, 0)
        self.max_coolant_temp_safety = QSpinBox()
        self.max_coolant_temp_safety.setRange(90, 130)
        self.max_coolant_temp_safety.setValue(110)
        self.max_coolant_temp_safety.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.max_coolant_temp_safety, 4, 1)
        
        limits_layout.addWidget(QLabel("Knock Threshold:"), 5, 0)
        self.knock_threshold = QDoubleSpinBox()
        self.knock_threshold.setRange(0.1, 5.0)
        self.knock_threshold.setValue(2.0)
        self.knock_threshold.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.knock_threshold, 5, 1)
        
        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)
        
        # Protection actions
        actions_group = QGroupBox("Protection Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        actions_layout = QVBoxLayout()
        
        actions_layout.addWidget(QLabel("High AFR Action:"))
        self.high_afr_action = QComboBox()
        self.high_afr_action.addItems(["Retard Timing", "Add Fuel", "Cut Fuel", "Reduce Boost", "Shutdown"])
        self.high_afr_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.high_afr_action)
        
        actions_layout.addWidget(QLabel("High Oil Temp Action:"))
        self.high_oil_temp_action = QComboBox()
        self.high_oil_temp_action.addItems(["Reduce Boost", "Retard Timing", "Cut Fuel", "Shutdown"])
        self.high_oil_temp_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.high_oil_temp_action)
        
        actions_layout.addWidget(QLabel("Low Oil Pressure Action:"))
        self.low_oil_pressure_action = QComboBox()
        self.low_oil_pressure_action.addItems(["Shutdown", "Cut Fuel", "Reduce Boost", "Warning Only"])
        self.low_oil_pressure_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.low_oil_pressure_action)
        
        actions_layout.addWidget(QLabel("Knock Detection Action:"))
        self.knock_action = QComboBox()
        self.knock_action.addItems(["Retard Timing", "Reduce Boost", "Add Fuel", "Cut Fuel", "Shutdown"])
        self.knock_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.knock_action)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return panel
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update import ECU tab with telemetry data."""
        # Update datalogging graph if available
        if hasattr(self, 'datalog_graph'):
            rpm = data.get("RPM", data.get("Engine_RPM", 0))
            map_val = data.get("Boost_Pressure", 0) * 6.895
            afr = data.get("AFR", 14.7)
            lambda_val = data.get("Lambda", data.get("lambda_value", 1.0))
            self.datalog_graph.update_data(rpm, map_val, afr, lambda_val)

