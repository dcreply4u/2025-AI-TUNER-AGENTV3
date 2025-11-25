"""
3D Individual Cylinder Control Tab
True 3D individual cylinder trims for fuel and ignition (vs RPM & Load)
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


class CylinderControlTab(QWidget):
    """3D Individual Cylinder Control tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.cylinder_count = 8
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup cylinder control tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("3D Individual Cylinder Control - Fuel & Ignition Trim vs RPM & Load")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Cylinder count selector
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Cylinder Count:"))
        self.cyl_count_combo = QComboBox()
        self.cyl_count_combo.addItems(["4", "5", "6", "8", "10", "12"])
        self.cyl_count_combo.setCurrentIndex(3)  # 8 cylinders
        self.cyl_count_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.cyl_count_combo.currentTextChanged.connect(self._update_cylinder_count)
        count_layout.addWidget(self.cyl_count_combo)
        count_layout.addStretch()
        main_layout.addLayout(count_layout)
        
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
        
        # Fuel trim tabs
        feature_tabs.addTab(self._create_fuel_trim_tab(), "Fuel Trim")
        
        # Ignition trim tabs
        feature_tabs.addTab(self._create_ignition_trim_tab(), "Ignition Trim")
        
        # Global settings
        feature_tabs.addTab(self._create_global_settings(), "Global Settings")
        
        main_layout.addWidget(feature_tabs, stretch=1)
    
    def _create_fuel_trim_tab(self) -> QWidget:
        """Create fuel trim tab with 3D maps per cylinder."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for each cylinder
        cylinder_tabs = QTabWidget()
        cylinder_tabs.setStyleSheet("""
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
        
        for i in range(self.cylinder_count):
            cylinder_tabs.addTab(self._create_cylinder_fuel_map(i+1), f"Cylinder {i+1}")
        
        layout.addWidget(cylinder_tabs)
        return tab
    
    def _create_cylinder_fuel_map(self, cylinder_num: int) -> QWidget:
        """Create 3D fuel trim map for a single cylinder."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel(f"Cylinder {cylinder_num} - Fuel Trim Map (vs RPM & Load)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # 3D map table
        map_group = QGroupBox(f"Cylinder {cylinder_num} Fuel Trim (%)")
        map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        map_layout = QVBoxLayout()
        
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
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with fuel trim values (can be adjusted per cell)
        for row in range(12):
            for col in range(12):
                trim_value = 0.0  # Default: no trim
                
                item = QTableWidgetItem(f"{trim_value:+.1f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if trim_value > 5:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Rich
                elif trim_value < -5:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Lean
                elif abs(trim_value) > 2:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))  # Neutral
                
                # Make editable
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, col, item)
        
        map_layout.addWidget(table)
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
        
        # Quick adjustment buttons
        quick_adj_group = QGroupBox("Quick Adjustments")
        quick_adj_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        quick_adj_layout = QHBoxLayout()
        
        self._add_quick_adj_button(quick_adj_layout, "Add 1%", 1.0)
        self._add_quick_adj_button(quick_adj_layout, "Add 5%", 5.0)
        self._add_quick_adj_button(quick_adj_layout, "Subtract 1%", -1.0)
        self._add_quick_adj_button(quick_adj_layout, "Subtract 5%", -5.0)
        self._add_quick_adj_button(quick_adj_layout, "Reset", 0.0)
        
        quick_adj_group.setLayout(quick_adj_layout)
        layout.addWidget(quick_adj_group)
        
        layout.addStretch()
        return panel
    
    def _add_quick_adj_button(self, layout: QHBoxLayout, label: str, value: float) -> None:
        """Add quick adjustment button."""
        btn = QPushButton(label)
        btn.setStyleSheet(get_scaled_stylesheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                padding: 5px 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """))
        layout.addWidget(btn)
    
    def _create_ignition_trim_tab(self) -> QWidget:
        """Create ignition trim tab with 3D maps per cylinder."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for each cylinder
        cylinder_tabs = QTabWidget()
        cylinder_tabs.setStyleSheet("""
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
        
        for i in range(self.cylinder_count):
            cylinder_tabs.addTab(self._create_cylinder_ignition_map(i+1), f"Cylinder {i+1}")
        
        layout.addWidget(cylinder_tabs)
        return tab
    
    def _create_cylinder_ignition_map(self, cylinder_num: int) -> QWidget:
        """Create 3D ignition trim map for a single cylinder."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel(f"Cylinder {cylinder_num} - Ignition Timing Trim Map (vs RPM & Load)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # 3D map table
        map_group = QGroupBox(f"Cylinder {cylinder_num} Ignition Trim (°)")
        map_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        map_layout = QVBoxLayout()
        
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
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with ignition trim values
        for row in range(12):
            for col in range(12):
                trim_value = 0.0  # Default: no trim
                
                item = QTableWidgetItem(f"{trim_value:+.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if trim_value > 2:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Advanced
                elif trim_value < -2:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Retarded
                elif abs(trim_value) > 1:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))  # Neutral
                
                # Make editable
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, col, item)
        
        map_layout.addWidget(table)
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
        
        layout.addStretch()
        return panel
    
    def _create_global_settings(self) -> QWidget:
        """Create global cylinder control settings."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Global Cylinder Control Settings")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        self.cylinder_control_enabled = QCheckBox("Individual Cylinder Control Enabled")
        self.cylinder_control_enabled.setChecked(True)
        self.cylinder_control_enabled.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.cylinder_control_enabled, 0, 0, 1, 2)
        
        settings_layout.addWidget(QLabel("Max Fuel Trim (%):"), 1, 0)
        self.max_fuel_trim = QDoubleSpinBox()
        self.max_fuel_trim.setRange(0, 50)
        self.max_fuel_trim.setValue(20.0)
        self.max_fuel_trim.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_fuel_trim, 1, 1)
        
        settings_layout.addWidget(QLabel("Max Ignition Trim (°):"), 2, 0)
        self.max_ignition_trim = QDoubleSpinBox()
        self.max_ignition_trim.setRange(0, 10)
        self.max_ignition_trim.setValue(5.0)
        self.max_ignition_trim.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_ignition_trim, 2, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _update_cylinder_count(self, count_str: str) -> None:
        """Update cylinder count."""
        self.cylinder_count = int(count_str)
        # Rebuild UI
        self.setup_ui()
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        pass
















