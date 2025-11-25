"""
Domestic ECU Support Tab
Full support for Ford, GM (LS/LT), and Dodge (Hemi) ECUs
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


class DomesticECUTab(QWidget):
    """Domestic ECU Support tab with manufacturer-specific sub-tabs."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup domestic ECU tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Domestic ECU Support - Ford, GM, Dodge Performance Tuning")
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
        self.manufacturer_tabs.addTab(self._create_ford_tab(), "Ford")
        self.manufacturer_tabs.addTab(self._create_gm_tab(), "GM (LS/LT)")
        self.manufacturer_tabs.addTab(self._create_dodge_tab(), "Dodge (Hemi)")
        
        main_layout.addWidget(self.manufacturer_tabs, stretch=1)
    
    def _create_ford_tab(self) -> QWidget:
        """Create Ford-specific ECU tab."""
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
        self.ford_model = QComboBox()
        self.ford_model.addItems([
            "Mustang (S197)", "Mustang (S550)", "Mustang (S650)",
            "Mustang GT", "Mustang EcoBoost", "Mustang Shelby GT350/GT500",
            "F-150", "F-150 Raptor", "Focus ST/RS", "Custom"
        ])
        self.ford_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.ford_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.ford_engine = QComboBox()
        self.ford_engine.addItems([
            "5.0L Coyote V8", "5.2L Voodoo V8", "5.2L Predator V8",
            "2.3L EcoBoost I4", "3.5L EcoBoost V6", "3.7L Cyclone V6",
            "4.6L Modular V8", "5.4L Modular V8", "Custom"
        ])
        self.ford_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.ford_engine)
        
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
        
        # Fuel Injection Timing & Quantity
        feature_tabs.addTab(self._create_fuel_injection_control(), "Fuel Injection")
        
        # AFR Targeting
        feature_tabs.addTab(self._create_afr_targeting(), "AFR Targeting")
        
        # Ignition Timing Control
        feature_tabs.addTab(self._create_ignition_timing_control(), "Ignition Timing")
        
        # Idle Speed Control
        feature_tabs.addTab(self._create_idle_control(), "Idle Control")
        
        # Boost Control
        feature_tabs.addTab(self._create_boost_control_domestic(), "Boost Control")
        
        # Engine Protection/Fail-Safes
        feature_tabs.addTab(self._create_engine_protection(), "Engine Protection")
        
        # Traction & Launch Control
        feature_tabs.addTab(self._create_traction_launch_control(), "Traction/Launch")
        
        # Flex Fuel Support
        feature_tabs.addTab(self._create_flex_fuel_support(), "Flex Fuel")
        
        # Sensor Configuration
        feature_tabs.addTab(self._create_sensor_config_domestic("Ford"), "Sensors")
        
        # CAN Bus Integration
        feature_tabs.addTab(self._create_can_bus_integration(), "CAN Bus")
        
        # Data Logging
        feature_tabs.addTab(self._create_datalogging_domestic(), "Data Logging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_gm_tab(self) -> QWidget:
        """Create GM (LS/LT) specific ECU tab."""
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
        self.gm_model = QComboBox()
        self.gm_model.addItems([
            "Camaro (5th Gen)", "Camaro (6th Gen)", "Camaro ZL1",
            "Corvette (C5)", "Corvette (C6)", "Corvette (C7)", "Corvette (C8)",
            "Silverado", "GMC Sierra", "CTS-V", "SS", "Custom"
        ])
        self.gm_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.gm_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.gm_engine = QComboBox()
        self.gm_engine.addItems([
            "LS1", "LS2", "LS3", "LS6", "LS7", "LS9", "LSA",
            "LT1", "LT4", "LT5", "L83", "L86", "L87", "L8T",
            "Custom"
        ])
        self.gm_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.gm_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs (same as Ford)
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
        
        feature_tabs.addTab(self._create_fuel_injection_control(), "Fuel Injection")
        feature_tabs.addTab(self._create_afr_targeting(), "AFR Targeting")
        feature_tabs.addTab(self._create_ignition_timing_control(), "Ignition Timing")
        feature_tabs.addTab(self._create_idle_control(), "Idle Control")
        feature_tabs.addTab(self._create_boost_control_domestic(), "Boost Control")
        feature_tabs.addTab(self._create_engine_protection(), "Engine Protection")
        feature_tabs.addTab(self._create_traction_launch_control(), "Traction/Launch")
        feature_tabs.addTab(self._create_flex_fuel_support(), "Flex Fuel")
        feature_tabs.addTab(self._create_sensor_config_domestic("GM"), "Sensors")
        feature_tabs.addTab(self._create_can_bus_integration(), "CAN Bus")
        feature_tabs.addTab(self._create_datalogging_domestic(), "Data Logging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_dodge_tab(self) -> QWidget:
        """Create Dodge (Hemi) specific ECU tab."""
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
        self.dodge_model = QComboBox()
        self.dodge_model.addItems([
            "Challenger", "Challenger SRT Hellcat", "Challenger SRT Demon",
            "Charger", "Charger SRT Hellcat", "Charger SRT Redeye",
            "Durango SRT", "Ram TRX", "Custom"
        ])
        self.dodge_model.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.dodge_model)
        
        vehicle_layout.addWidget(QLabel("Engine:"))
        self.dodge_engine = QComboBox()
        self.dodge_engine.addItems([
            "5.7L Hemi V8", "6.1L Hemi V8", "6.4L Hemi V8",
            "6.2L Hellcat V8", "6.2L Demon V8", "6.2L Redeye V8",
            "Custom"
        ])
        self.dodge_engine.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        vehicle_layout.addWidget(self.dodge_engine)
        
        vehicle_group.setLayout(vehicle_layout)
        layout.addWidget(vehicle_group)
        
        # Feature tabs (same as Ford/GM)
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
        
        feature_tabs.addTab(self._create_fuel_injection_control(), "Fuel Injection")
        feature_tabs.addTab(self._create_afr_targeting(), "AFR Targeting")
        feature_tabs.addTab(self._create_ignition_timing_control(), "Ignition Timing")
        feature_tabs.addTab(self._create_idle_control(), "Idle Control")
        feature_tabs.addTab(self._create_boost_control_domestic(), "Boost Control")
        feature_tabs.addTab(self._create_engine_protection(), "Engine Protection")
        feature_tabs.addTab(self._create_traction_launch_control(), "Traction/Launch")
        feature_tabs.addTab(self._create_flex_fuel_support(), "Flex Fuel")
        feature_tabs.addTab(self._create_sensor_config_domestic("Dodge"), "Sensors")
        feature_tabs.addTab(self._create_can_bus_integration(), "CAN Bus")
        feature_tabs.addTab(self._create_datalogging_domestic(), "Data Logging")
        
        layout.addWidget(feature_tabs, stretch=1)
        return tab
    
    def _create_fuel_injection_control(self) -> QWidget:
        """Create fuel injection timing and quantity control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Fuel Injection Timing and Quantity - Optimize AFR across all load conditions")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Sub-tabs for different aspects
        injection_tabs = QTabWidget()
        injection_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px 12px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # Fuel Quantity Map (VE Table)
        quantity_tab = QWidget()
        quantity_layout = QVBoxLayout(quantity_tab)
        quantity_layout.setContentsMargins(10, 10, 10, 10)
        
        quantity_title = QLabel("Fuel Quantity Map (VE Table) - Injector Pulse Width vs RPM & Load")
        quantity_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        quantity_layout.addWidget(quantity_title)
        
        self.fuel_quantity_table = VETableWidget()
        quantity_layout.addWidget(self.fuel_quantity_table, stretch=1)
        injection_tabs.addTab(quantity_tab, "Fuel Quantity")
        
        # Injection Timing Map
        timing_tab = QWidget()
        timing_layout = QVBoxLayout(timing_tab)
        timing_layout.setContentsMargins(10, 10, 10, 10)
        
        timing_title = QLabel("Injection Timing Map (Start of Injection vs RPM & Load)")
        timing_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        timing_layout.addWidget(timing_title)
        
        table = QTableWidget()
        table.setRowCount(12)  # RPM
        table.setColumnCount(12)  # Load
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 9000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with injection timing values (degrees BTDC)
        for row in range(12):
            for col in range(12):
                # Injection timing: earlier at high load, later at low load
                timing = 360 - (load_values[col] / 100) * 60 - (rpm_values[row] / 9000) * 30
                timing = max(270, min(360, timing))  # Range: 270-360 degrees
                
                item = QTableWidgetItem(f"{timing:.0f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing > 350:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Early injection
                elif timing > 330:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Late injection
                
                table.setItem(row, col, item)
        
        timing_layout.addWidget(table)
        injection_tabs.addTab(timing_tab, "Injection Timing")
        
        # Injector Settings
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        settings_title = QLabel("Injector Configuration")
        settings_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        settings_layout.addWidget(settings_title)
        
        settings_group = QGroupBox("Injector Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_group_layout = QGridLayout()
        
        settings_group_layout.addWidget(QLabel("Injector Size (cc/min):"), 0, 0)
        self.injector_size = QSpinBox()
        self.injector_size.setRange(100, 5000)
        self.injector_size.setValue(1000)
        self.injector_size.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_group_layout.addWidget(self.injector_size, 0, 1)
        
        settings_group_layout.addWidget(QLabel("Injector Type:"), 1, 0)
        self.injector_type = QComboBox()
        self.injector_type.addItems(["High Impedance", "Low Impedance", "Peak & Hold"])
        self.injector_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_group_layout.addWidget(self.injector_type, 1, 1)
        
        settings_group_layout.addWidget(QLabel("Dead Time (ms):"), 2, 0)
        self.injector_dead_time = QDoubleSpinBox()
        self.injector_dead_time.setRange(0.1, 5.0)
        self.injector_dead_time.setValue(1.0)
        self.injector_dead_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_group_layout.addWidget(self.injector_dead_time, 2, 1)
        
        settings_group_layout.addWidget(QLabel("Fuel Pressure (psi):"), 3, 0)
        self.fuel_pressure = QDoubleSpinBox()
        self.fuel_pressure.setRange(0, 100)
        self.fuel_pressure.setValue(43.5)
        self.fuel_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_group_layout.addWidget(self.fuel_pressure, 3, 1)
        
        settings_group_layout.addWidget(QLabel("Injection Mode:"), 4, 0)
        self.injection_mode = QComboBox()
        self.injection_mode.addItems(["Sequential", "Batch Fire", "Semi-Sequential"])
        self.injection_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_group_layout.addWidget(self.injection_mode, 4, 1)
        
        settings_group.setLayout(settings_group_layout)
        settings_layout.addWidget(settings_group)
        settings_layout.addStretch()
        injection_tabs.addTab(settings_tab, "Injector Config")
        
        layout.addWidget(injection_tabs)
        return panel
    
    def _create_afr_targeting(self) -> QWidget:
        """Create AFR targeting panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Air-Fuel Ratio (AFR) Targeting - Balance power, efficiency, and engine safety")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # AFR Target Map
        afr_map_group = QGroupBox("AFR Target Map (vs RPM & Load)")
        afr_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        afr_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(12)  # RPM
        table.setColumnCount(12)  # Load
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 9000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with AFR targets (lean at idle/light load, richer at heavy load)
        for row in range(12):
            for col in range(12):
                if rpm_values[row] < 1500 or load_values[col] < 30:
                    afr = 14.7  # Stoichiometric at idle/light load
                else:
                    # Richer at high load for safety and power
                    afr = 14.7 - (load_values[col] / 100) * 2.5 - (rpm_values[row] / 9000) * 0.5
                    afr = max(11.5, min(14.7, afr))  # Range: 11.5-14.7
                
                item = QTableWidgetItem(f"{afr:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if afr < 12.0:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very rich
                elif afr < 13.0:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Rich
                elif afr < 14.0:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Lean/Stoich
                
                table.setItem(row, col, item)
        
        afr_map_layout.addWidget(table)
        afr_map_group.setLayout(afr_map_layout)
        layout.addWidget(afr_map_group)
        
        # Closed-loop settings
        closed_loop_group = QGroupBox("Closed-Loop AFR Control")
        closed_loop_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        closed_loop_layout = QGridLayout()
        
        self.closed_loop_enabled = QCheckBox("Closed-Loop AFR Enabled")
        self.closed_loop_enabled.setChecked(True)
        self.closed_loop_enabled.setStyleSheet("color: #ffffff;")
        closed_loop_layout.addWidget(self.closed_loop_enabled, 0, 0, 1, 2)
        
        closed_loop_layout.addWidget(QLabel("Correction Rate (%/sec):"), 1, 0)
        self.afr_correction_rate = QDoubleSpinBox()
        self.afr_correction_rate.setRange(0.1, 10.0)
        self.afr_correction_rate.setValue(2.0)
        self.afr_correction_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        closed_loop_layout.addWidget(self.afr_correction_rate, 1, 1)
        
        closed_loop_layout.addWidget(QLabel("Max Correction (%):"), 2, 0)
        self.max_afr_correction = QDoubleSpinBox()
        self.max_afr_correction.setRange(5, 50)
        self.max_afr_correction.setValue(25.0)
        self.max_afr_correction.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        closed_loop_layout.addWidget(self.max_afr_correction, 2, 1)
        
        closed_loop_group.setLayout(closed_loop_layout)
        layout.addWidget(closed_loop_group)
        
        layout.addStretch()
        return panel
    
    def _create_ignition_timing_control(self) -> QWidget:
        """Create ignition timing control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Control - Maximize power while avoiding detonation")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Ignition timing map
        timing_map_group = QGroupBox("Ignition Timing Map (vs RPM & Load)")
        timing_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        timing_map_layout = QVBoxLayout()
        
        self.ignition_timing_table = VETableWidget()
        timing_map_layout.addWidget(self.ignition_timing_table, stretch=1)
        timing_map_group.setLayout(timing_map_layout)
        layout.addWidget(timing_map_group)
        
        # Knock sensing and correction
        knock_group = QGroupBox("Knock Sensing & Correction")
        knock_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        knock_layout = QGridLayout()
        
        self.knock_sensing_enabled = QCheckBox("Knock Sensing Enabled")
        self.knock_sensing_enabled.setChecked(True)
        self.knock_sensing_enabled.setStyleSheet("color: #ffffff;")
        knock_layout.addWidget(self.knock_sensing_enabled, 0, 0, 1, 2)
        
        knock_layout.addWidget(QLabel("Knock Threshold:"), 1, 0)
        self.knock_threshold = QDoubleSpinBox()
        self.knock_threshold.setRange(0.1, 5.0)
        self.knock_threshold.setValue(2.0)
        self.knock_threshold.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        knock_layout.addWidget(self.knock_threshold, 1, 1)
        
        knock_layout.addWidget(QLabel("Retard Rate (°/event):"), 2, 0)
        self.knock_retard_rate = QDoubleSpinBox()
        self.knock_retard_rate.setRange(0.5, 5.0)
        self.knock_retard_rate.setValue(2.0)
        self.knock_retard_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        knock_layout.addWidget(self.knock_retard_rate, 2, 1)
        
        knock_layout.addWidget(QLabel("Max Retard (°):"), 3, 0)
        self.max_knock_retard = QDoubleSpinBox()
        self.max_knock_retard.setRange(5, 20)
        self.max_knock_retard.setValue(10.0)
        self.max_knock_retard.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        knock_layout.addWidget(self.max_knock_retard, 3, 1)
        
        knock_layout.addWidget(QLabel("Recovery Rate (°/sec):"), 4, 0)
        self.knock_recovery_rate = QDoubleSpinBox()
        self.knock_recovery_rate.setRange(0.5, 10.0)
        self.knock_recovery_rate.setValue(2.0)
        self.knock_recovery_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        knock_layout.addWidget(self.knock_recovery_rate, 4, 1)
        
        knock_group.setLayout(knock_layout)
        layout.addWidget(knock_group)
        
        # Individual cylinder trim
        cylinder_trim_group = QGroupBox("Individual Cylinder Timing Trim")
        cylinder_trim_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        cylinder_trim_layout = QGridLayout()
        
        for i in range(8):  # Up to 8 cylinders
            cylinder_trim_layout.addWidget(QLabel(f"Cyl {i+1} Trim (°):"), i, 0)
            trim_spin = QDoubleSpinBox()
            trim_spin.setRange(-5, 5)
            trim_spin.setValue(0.0)
            trim_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
            cylinder_trim_layout.addWidget(trim_spin, i, 1)
            setattr(self, f"cyl_{i+1}_trim", trim_spin)
        
        cylinder_trim_group.setLayout(cylinder_trim_layout)
        layout.addWidget(cylinder_trim_group)
        
        layout.addStretch()
        return panel
    
    def _create_idle_control(self) -> QWidget:
        """Create idle speed control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Idle Speed Control - Manage idle conditions including cold start")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Idle control map
        idle_map_group = QGroupBox("Idle Control Map (vs Coolant Temp & Load)")
        idle_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        idle_map_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)  # Coolant temp
        table.setColumnCount(8)  # Load/AC/PS
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
        
        load_conditions = ["Idle", "AC On", "PS Load", "Fan On", "AC+PS", "AC+Fan", "PS+Fan", "All Load"]
        for col, condition in enumerate(load_conditions):
            item = QTableWidgetItem(condition)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        temp_values = [-20, -10, 0, 20, 40, 60, 80, 90, 100, 110]
        for row, temp in enumerate(temp_values):
            item = QTableWidgetItem(f"{temp}°C")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with idle RPM targets (higher when cold, higher with loads)
        for row in range(10):
            for col in range(8):
                base_idle = 850
                # Higher idle when cold
                if temp_values[row] < 20:
                    idle_rpm = base_idle + (20 - temp_values[row]) * 5
                else:
                    idle_rpm = base_idle
                # Add RPM for loads
                if col > 0:
                    idle_rpm += col * 50
                idle_rpm = max(600, min(2000, idle_rpm))
                
                item = QTableWidgetItem(f"{idle_rpm}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if idle_rpm > 1500:
                    item.setBackground(QBrush(QColor("#ff0000")))  # High idle
                elif idle_rpm > 1200:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Elevated
                elif idle_rpm > 900:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Normal
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Low
                
                table.setItem(row, col, item)
        
        idle_map_layout.addWidget(table)
        idle_map_group.setLayout(idle_map_layout)
        layout.addWidget(idle_map_group)
        
        # Idle control settings
        settings_group = QGroupBox("Idle Control Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Target Idle RPM:"), 0, 0)
        self.target_idle_rpm = QSpinBox()
        self.target_idle_rpm.setRange(500, 2000)
        self.target_idle_rpm.setValue(850)
        self.target_idle_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.target_idle_rpm, 0, 1)
        
        settings_layout.addWidget(QLabel("IAC Type:"), 1, 0)
        self.iac_type = QComboBox()
        self.iac_type.addItems(["Stepper Motor", "PWM Valve", "Solenoid", "E-Throttle"])
        self.iac_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.iac_type, 1, 1)
        
        self.closed_loop_idle = QCheckBox("Closed-Loop Idle Control")
        self.closed_loop_idle.setChecked(True)
        self.closed_loop_idle.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.closed_loop_idle, 2, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_boost_control_domestic(self) -> QWidget:
        """Create boost control panel for domestic platforms."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Boost Control - Mechanical or electronic boost control for forced induction")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Boost control map
        boost_map_group = QGroupBox("Target Boost Map (vs RPM & Gear) - Gear-dependent boost limiting")
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
        
        # Fill with boost targets (lower in lower gears for traction)
        for row in range(6):
            for col in range(10):
                base_boost = 10 + (rpm_values[col] / 11000) * 20
                # Reduce boost in lower gears
                if gear_values[row] <= 2:
                    boost = base_boost * 0.5  # 50% in 1st/2nd
                elif gear_values[row] == 3:
                    boost = base_boost * 0.75  # 75% in 3rd
                else:
                    boost = base_boost  # Full boost in 4th+
                boost = max(0, min(30, boost))
                
                item = QTableWidgetItem(f"{boost:.1f}psi")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if boost > 25:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very high
                elif boost > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))  # High
                elif boost > 15:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Low
                
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
        
        settings_layout.addWidget(QLabel("Control Type:"), 0, 0)
        self.boost_control_type = QComboBox()
        self.boost_control_type.addItems(["Mechanical (Wastegate)", "Electronic (Solenoid)", "Hybrid"])
        self.boost_control_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.boost_control_type, 0, 1)
        
        settings_layout.addWidget(QLabel("Control Mode:"), 1, 0)
        self.boost_control_mode = QComboBox()
        self.boost_control_mode.addItems(["Open Loop", "Closed Loop", "Hybrid"])
        self.boost_control_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.boost_control_mode, 1, 1)
        
        settings_layout.addWidget(QLabel("Max Boost (psi):"), 2, 0)
        self.max_boost_domestic = QDoubleSpinBox()
        self.max_boost_domestic.setRange(0, 50)
        self.max_boost_domestic.setValue(25.0)
        self.max_boost_domestic.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_boost_domestic, 2, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _create_engine_protection(self) -> QWidget:
        """Create engine protection/fail-safes panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Engine Protection/Fail-Safes - Programmable safety functions")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Protection limits
        limits_group = QGroupBox("Protection Limits")
        limits_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        limits_layout = QGridLayout()
        
        limits_layout.addWidget(QLabel("Max Coolant Temp (°C):"), 0, 0)
        self.max_coolant_temp = QSpinBox()
        self.max_coolant_temp.setRange(90, 130)
        self.max_coolant_temp.setValue(110)
        self.max_coolant_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.max_coolant_temp, 0, 1)
        
        limits_layout.addWidget(QLabel("Max Oil Temp (°C):"), 1, 0)
        self.max_oil_temp = QSpinBox()
        self.max_oil_temp.setRange(100, 150)
        self.max_oil_temp.setValue(130)
        self.max_oil_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.max_oil_temp, 1, 1)
        
        limits_layout.addWidget(QLabel("Min Oil Pressure (psi):"), 2, 0)
        self.min_oil_pressure = QDoubleSpinBox()
        self.min_oil_pressure.setRange(0, 100)
        self.min_oil_pressure.setValue(20.0)
        self.min_oil_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.min_oil_pressure, 2, 1)
        
        limits_layout.addWidget(QLabel("Max AFR (Lean):"), 3, 0)
        self.max_afr_protection = QDoubleSpinBox()
        self.max_afr_protection.setRange(14.0, 20.0)
        self.max_afr_protection.setValue(16.0)
        self.max_afr_protection.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.max_afr_protection, 3, 1)
        
        limits_layout.addWidget(QLabel("Min AFR (Rich):"), 4, 0)
        self.min_afr_protection = QDoubleSpinBox()
        self.min_afr_protection.setRange(10.0, 14.0)
        self.min_afr_protection.setValue(11.0)
        self.min_afr_protection.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        limits_layout.addWidget(self.min_afr_protection, 4, 1)
        
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
        
        actions_layout.addWidget(QLabel("Over-Temperature Action:"))
        self.overtemp_action = QComboBox()
        self.overtemp_action.addItems(["Warning Light", "Limp Mode", "Shutdown", "Reduce Power"])
        self.overtemp_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.overtemp_action)
        
        actions_layout.addWidget(QLabel("Low Oil Pressure Action:"))
        self.low_oil_pressure_action = QComboBox()
        self.low_oil_pressure_action.addItems(["Warning Light", "Limp Mode", "Shutdown"])
        self.low_oil_pressure_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.low_oil_pressure_action)
        
        actions_layout.addWidget(QLabel("Lean AFR Action:"))
        self.lean_afr_action = QComboBox()
        self.lean_afr_action.addItems(["Warning Light", "Add Fuel", "Reduce Boost", "Limp Mode", "Shutdown"])
        self.lean_afr_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        actions_layout.addWidget(self.lean_afr_action)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return panel
    
    def _create_traction_launch_control(self) -> QWidget:
        """Create traction and launch control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Traction & Launch Control - Gear-dependent traction and launch control")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Sub-tabs for Traction and Launch
        control_tabs = QTabWidget()
        control_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px 12px;
                margin-right: 2px;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
            }
        """)
        
        # Traction Control
        traction_tab = QWidget()
        traction_layout = QVBoxLayout(traction_tab)
        traction_layout.setContentsMargins(10, 10, 10, 10)
        
        traction_title = QLabel("Traction Control - Gear-dependent slip management")
        traction_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        traction_layout.addWidget(traction_title)
        
        # Traction control map
        tc_map_group = QGroupBox("Traction Control Map (Slip Target vs RPM & Gear)")
        tc_map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        tc_map_layout = QVBoxLayout()
        
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
        
        # Fill with slip targets (tighter in lower gears)
        for row in range(6):
            for col in range(10):
                # Tighter slip control in lower gears
                if gear_values[row] <= 2:
                    slip_target = 5.0  # 5% slip in 1st/2nd
                elif gear_values[row] == 3:
                    slip_target = 8.0  # 8% in 3rd
                else:
                    slip_target = 12.0  # 12% in 4th+
                
                item = QTableWidgetItem(f"{slip_target:.1f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if slip_target < 6:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very tight
                elif slip_target < 10:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Tight
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                
                table.setItem(row, col, item)
        
        tc_map_layout.addWidget(table)
        tc_map_group.setLayout(tc_map_layout)
        traction_layout.addWidget(tc_map_group)
        
        # Traction control settings
        tc_settings_group = QGroupBox("Traction Control Settings")
        tc_settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        tc_settings_layout = QGridLayout()
        
        self.tc_enabled = QCheckBox("Traction Control Enabled")
        self.tc_enabled.setChecked(True)
        self.tc_enabled.setStyleSheet("color: #ffffff;")
        tc_settings_layout.addWidget(self.tc_enabled, 0, 0, 1, 2)
        
        tc_settings_layout.addWidget(QLabel("Control Method:"), 1, 0)
        self.tc_method = QComboBox()
        self.tc_method.addItems(["Ignition Retard", "Torque Cut", "Combined"])
        self.tc_method.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        tc_settings_layout.addWidget(self.tc_method, 1, 1)
        
        tc_settings_layout.addWidget(QLabel("Wheel Speed Sensors:"), 2, 0)
        self.wheel_sensors = QComboBox()
        self.wheel_sensors.addItems(["2-Channel (FL/FR)", "4-Channel (All Wheels)"])
        self.wheel_sensors.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        tc_settings_layout.addWidget(self.wheel_sensors, 2, 1)
        
        tc_settings_group.setLayout(tc_settings_layout)
        traction_layout.addWidget(tc_settings_group)
        traction_layout.addStretch()
        control_tabs.addTab(traction_tab, "Traction Control")
        
        # Launch Control
        launch_tab = QWidget()
        launch_layout = QVBoxLayout(launch_tab)
        launch_layout.setContentsMargins(10, 10, 10, 10)
        
        launch_title = QLabel("Launch Control - Maximize grip and acceleration off the line")
        launch_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        launch_layout.addWidget(launch_title)
        
        # Launch control settings
        launch_settings_group = QGroupBox("Launch Control Settings")
        launch_settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        launch_settings_layout = QGridLayout()
        
        self.launch_enabled = QCheckBox("Launch Control Enabled")
        self.launch_enabled.setChecked(True)
        self.launch_enabled.setStyleSheet("color: #ffffff;")
        launch_settings_layout.addWidget(self.launch_enabled, 0, 0, 1, 2)
        
        launch_settings_layout.addWidget(QLabel("Launch RPM:"), 1, 0)
        self.launch_rpm = QSpinBox()
        self.launch_rpm.setRange(2000, 8000)
        self.launch_rpm.setValue(4000)
        self.launch_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        launch_settings_layout.addWidget(self.launch_rpm, 1, 1)
        
        launch_settings_layout.addWidget(QLabel("Launch Boost (psi):"), 2, 0)
        self.launch_boost = QDoubleSpinBox()
        self.launch_boost.setRange(0, 30)
        self.launch_boost.setValue(15.0)
        self.launch_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        launch_settings_layout.addWidget(self.launch_boost, 2, 1)
        
        launch_settings_layout.addWidget(QLabel("Release Speed (MPH):"), 3, 0)
        self.launch_release_speed = QDoubleSpinBox()
        self.launch_release_speed.setRange(0, 100)
        self.launch_release_speed.setValue(20.0)
        self.launch_release_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        launch_settings_layout.addWidget(self.launch_release_speed, 3, 1)
        
        launch_settings_group.setLayout(launch_settings_layout)
        launch_layout.addWidget(launch_settings_group)
        launch_layout.addStretch()
        control_tabs.addTab(launch_tab, "Launch Control")
        
        layout.addWidget(control_tabs)
        return panel
    
    def _create_flex_fuel_support(self) -> QWidget:
        """Create flex fuel support panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Flex Fuel Support - Automatic tuning adjustments based on ethanol content")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Flex fuel settings
        flex_settings_group = QGroupBox("Flex Fuel Settings")
        flex_settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        flex_settings_layout = QGridLayout()
        
        self.flex_fuel_enabled = QCheckBox("Flex Fuel Support Enabled")
        self.flex_fuel_enabled.setChecked(True)
        self.flex_fuel_enabled.setStyleSheet("color: #ffffff;")
        flex_settings_layout.addWidget(self.flex_fuel_enabled, 0, 0, 1, 2)
        
        flex_settings_layout.addWidget(QLabel("Ethanol Sensor Type:"), 1, 0)
        self.ethanol_sensor_type = QComboBox()
        self.ethanol_sensor_type.addItems(["GM Flex Fuel Sensor", "Ford Flex Fuel Sensor", "Universal"])
        self.ethanol_sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        flex_settings_layout.addWidget(self.ethanol_sensor_type, 1, 1)
        
        flex_settings_layout.addWidget(QLabel("Current Ethanol %:"), 2, 0)
        self.current_ethanol = QDoubleSpinBox()
        self.current_ethanol.setRange(0, 100)
        self.current_ethanol.setValue(0.0)
        self.current_ethanol.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        flex_settings_layout.addWidget(self.current_ethanol, 2, 1)
        
        flex_settings_group.setLayout(flex_settings_layout)
        layout.addWidget(flex_settings_group)
        
        # Fuel compensation map
        compensation_group = QGroupBox("Fuel Compensation Map (vs Ethanol % & Load)")
        compensation_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        compensation_layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setRowCount(10)  # Load
        table.setColumnCount(11)  # Ethanol %
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
        
        ethanol_values = [0, 10, 20, 30, 40, 50, 60, 70, 80, 85, 100]
        for col, ethanol in enumerate(ethanol_values):
            item = QTableWidgetItem(f"{ethanol}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        load_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for row, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with fuel compensation (more fuel for higher ethanol)
        for row in range(10):
            for col in range(11):
                # E85 requires ~30% more fuel than gasoline
                compensation = (ethanol_values[col] / 100) * 35
                compensation = max(0, min(40, compensation))
                
                item = QTableWidgetItem(f"+{compensation:.1f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if compensation > 30:
                    item.setBackground(QBrush(QColor("#00ff00")))  # High compensation
                elif compensation > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                elif compensation > 10:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Low
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))  # Minimal
                
                table.setItem(row, col, item)
        
        compensation_layout.addWidget(table)
        compensation_group.setLayout(compensation_layout)
        layout.addWidget(compensation_group)
        
        layout.addStretch()
        return panel
    
    def _create_sensor_config_domestic(self, manufacturer: str) -> QWidget:
        """Create sensor configuration panel for domestic platforms."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel(f"{manufacturer} Sensor Configuration - OEM and aftermarket sensor compatibility")
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
        table.setRowCount(18)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Sensor", "Type", "Pin/Channel", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(500)
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
            ("MAF Sensor", "Frequency/Analog", "Pin 4", "Active"),
            ("IAT Sensor", "Analog 0-5V", "Pin 5", "Active"),
            ("Coolant Temp", "Analog 0-5V", "Pin 6", "Active"),
            ("Wideband O2 (Lambda)", "Analog 0-5V", "Pin 7", "Active"),
            ("Narrowband O2", "Analog 0-1V", "Pin 8", "Active"),
            ("TPS", "Analog 0-5V", "Pin 9", "Active"),
            ("Knock Sensor", "Piezoelectric", "Pin 10", "Active"),
            ("Fuel Pressure", "Analog 0-5V", "Pin 11", "Active"),
            ("Oil Pressure", "Analog 0-5V", "Pin 12", "Active"),
            ("EGT Sensor", "Type-K Thermocouple", "Pin 13", "Active"),
            ("Wheel Speed FL", "Hall/Magnetic", "Pin 14", "Active"),
            ("Wheel Speed FR", "Hall/Magnetic", "Pin 15", "Active"),
            ("Wheel Speed RL", "Hall/Magnetic", "Pin 16", "Active"),
            ("Wheel Speed RR", "Hall/Magnetic", "Pin 17", "Active"),
            ("Flex Fuel Sensor", "Frequency", "Pin 18", "Active"),
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
    
    def _create_can_bus_integration(self) -> QWidget:
        """Create CAN bus integration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("CAN Bus Integration - Read and control other vehicle systems")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # CAN settings
        can_group = QGroupBox("CAN Bus Settings")
        can_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        can_layout = QVBoxLayout()
        
        can_layout.addWidget(QLabel("CAN Bus Speed:"))
        self.can_speed_domestic = QComboBox()
        self.can_speed_domestic.addItems(["125 kbps", "250 kbps", "500 kbps", "1000 kbps"])
        self.can_speed_domestic.setCurrentIndex(2)  # 500 kbps
        self.can_speed_domestic.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        can_layout.addWidget(self.can_speed_domestic)
        
        can_layout.addWidget(QLabel("CAN Protocol:"))
        self.can_protocol = QComboBox()
        self.can_protocol.addItems(["OBD-II", "J1939", "GM GMLAN", "Ford MS-CAN", "Chrysler CAN", "Custom"])
        self.can_protocol.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        can_layout.addWidget(self.can_protocol)
        
        can_group.setLayout(can_layout)
        layout.addWidget(can_group)
        
        # CAN devices
        devices_group = QGroupBox("CAN Bus Devices")
        devices_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        devices_layout = QVBoxLayout()
        
        devices_table = QTableWidget()
        devices_table.setRowCount(10)
        devices_table.setColumnCount(3)
        devices_table.setHorizontalHeaderLabels(["Device", "CAN ID", "Status"])
        devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        devices_table.setMinimumHeight(250)
        devices_table.setStyleSheet("""
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
            ("Transmission Control", "0x200", "Connected"),
            ("ABS/TCS Module", "0x300", "Connected"),
            ("Body Control Module", "0x400", "Disconnected"),
            ("Instrument Cluster", "0x500", "Connected"),
            ("Wideband Controller", "0x600", "Connected"),
            ("Boost Controller", "0x700", "Connected"),
            ("Data Logger", "0x800", "Connected"),
            ("Display Module", "0x900", "Disconnected"),
            ("Custom Device", "0xA00", "Disconnected"),
        ]
        
        for row, (device, can_id, status) in enumerate(can_devices):
            devices_table.setItem(row, 0, QTableWidgetItem(device))
            devices_table.setItem(row, 1, QTableWidgetItem(can_id))
            status_item = QTableWidgetItem(status)
            if status == "Connected":
                status_item.setForeground(QBrush(QColor("#00ff00")))
            else:
                status_item.setForeground(QBrush(QColor("#ff0000")))
            devices_table.setItem(row, 2, status_item)
        
        devices_layout.addWidget(devices_table)
        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)
        
        layout.addStretch()
        return panel
    
    def _create_datalogging_domestic(self) -> QWidget:
        """Create datalogging panel for domestic platforms."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Data Logging - In-depth logging of sensors for post-race analysis and tuning")
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
        self.log_sample_rate_domestic = QComboBox()
        self.log_sample_rate_domestic.addItems(["10", "20", "50", "100", "200", "500", "1000"])
        self.log_sample_rate_domestic.setCurrentIndex(4)  # 200 Hz
        self.log_sample_rate_domestic.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.log_sample_rate_domestic)
        
        settings_layout.addWidget(QLabel("Memory Size (MB):"))
        self.log_memory_domestic = QSpinBox()
        self.log_memory_domestic.setRange(10, 1000)
        self.log_memory_domestic.setValue(200)
        self.log_memory_domestic.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.log_memory_domestic)
        
        self.auto_logging_domestic = QCheckBox("Auto Start/Stop Logging")
        self.auto_logging_domestic.setChecked(True)
        self.auto_logging_domestic.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.auto_logging_domestic)
        
        settings_layout.addWidget(QLabel("Logged Parameters:"))
        self.logged_params = QComboBox()
        self.logged_params.addItems([
            "All Sensors", "Essential Only", "Performance Focus", "Safety Focus", "Custom"
        ])
        self.logged_params.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.logged_params)
        
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
        
        self.datalog_graph_domestic = RealTimeGraph()
        self.datalog_graph_domestic.setMinimumHeight(300)
        graph_layout.addWidget(self.datalog_graph_domestic)
        
        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)
        
        layout.addStretch()
        return panel
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update domestic ECU tab with telemetry data."""
        # Update datalogging graph if available
        if hasattr(self, 'datalog_graph_domestic'):
            rpm = data.get("RPM", data.get("Engine_RPM", 0))
            map_val = data.get("Boost_Pressure", 0) * 6.895
            afr = data.get("AFR", 14.7)
            lambda_val = data.get("Lambda", data.get("lambda_value", 1.0))
            self.datalog_graph_domestic.update_data(rpm, map_val, afr, lambda_val)

