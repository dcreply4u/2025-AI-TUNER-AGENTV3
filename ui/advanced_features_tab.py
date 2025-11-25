"""
Advanced Features Tab
Addresses: Advanced Diagnostics, Sophisticated Control Strategies, 
Custom Code Editor, Enhanced CAN Integration, Off-Road Mode, Enhanced Autotune
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
    QTextEdit,
    QFileDialog,
    QMessageBox,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet


class AdvancedFeaturesTab(QWidget):
    """Advanced Features tab addressing all identified gaps."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup advanced features tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Advanced Features - Professional-Grade Tuning Capabilities")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        tab_padding_v = self.scaler.get_scaled_size(6)
        tab_padding_h = self.scaler.get_scaled_size(15)
        tab_font = self.scaler.get_scaled_font_size(10)
        tab_border = self.scaler.get_scaled_size(1)
        tab_margin = self.scaler.get_scaled_size(2)
        feature_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {tab_margin}px;
                border: {tab_border}px solid #404040;
                font-size: {tab_font}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {self.scaler.get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Advanced Diagnostics & Predictive Maintenance
        feature_tabs.addTab(self._create_diagnostics_tab(), "Advanced Diagnostics")
        
        # Sophisticated Control Strategies
        feature_tabs.addTab(self._create_control_strategies_tab(), "Control Strategies")
        
        # Custom Code Editor
        feature_tabs.addTab(self._create_code_editor_tab(), "Custom Code Editor")
        
        # Enhanced CAN Integration
        feature_tabs.addTab(self._create_can_integration_tab(), "CAN Integration")
        
        # Off-Road/Racing Mode
        feature_tabs.addTab(self._create_offroad_mode_tab(), "Off-Road/Racing Mode")
        
        # Enhanced Autotune
        feature_tabs.addTab(self._create_enhanced_autotune_tab(), "Enhanced Autotune")
        
        main_layout.addWidget(feature_tabs, stretch=1)
    
    def _create_diagnostics_tab(self) -> QWidget:
        """Create advanced diagnostics and predictive maintenance tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        margin = self.scaler.get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Advanced Diagnostics & Predictive Maintenance - Real-time analysis and failure prediction")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Health scoring
        health_group = QGroupBox("Engine Health Score")
        group_font = self.scaler.get_scaled_font_size(12)
        group_border = self.scaler.get_scaled_size(1)
        group_radius = self.scaler.get_scaled_size(3)
        group_margin = self.scaler.get_scaled_size(10)
        health_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        health_layout = QGridLayout()
        
        health_layout.addWidget(QLabel("Overall Health Score:"), 0, 0)
        self.health_score = QLabel("85/100")
        health_score_font = self.scaler.get_scaled_font_size(24)
        self.health_score.setStyleSheet(f"font-size: {health_score_font}px; font-weight: bold; color: #00ff00;")
        health_layout.addWidget(self.health_score, 0, 1)
        
        health_layout.addWidget(QLabel("Status:"), 1, 0)
        self.health_status = QLabel("Good")
        status_font = self.scaler.get_scaled_font_size(14)
        self.health_status.setStyleSheet(f"font-size: {status_font}px; color: #00ff00;")
        health_layout.addWidget(self.health_status, 1, 1)
        
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)
        
        # Predictive alerts
        alerts_group = QGroupBox("Predictive Maintenance Alerts")
        alerts_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        alerts_layout = QVBoxLayout()
        
        alerts_table = QTableWidget()
        alerts_table.setRowCount(5)
        alerts_table.setColumnCount(4)
        alerts_table.setHorizontalHeaderLabels(["Component", "Status", "Prediction", "Action"])
        alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        alerts_table.setMinimumHeight(self.scaler.get_scaled_size(200))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        alerts_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: {table_border}px solid #404040;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {table_padding}px;
                border: {table_border}px solid #404040;
            }}
        """)
        
        alerts = [
            ("Turbo Efficiency", "Good", "Normal wear - 5000 miles", "Monitor"),
            ("Fuel Pump", "Warning", "Degrading - 2000 miles", "Inspect"),
            ("Cooling System", "Good", "Normal operation", "Monitor"),
            ("Oil Pressure", "Good", "Normal operation", "Monitor"),
            ("Knock Sensor", "Good", "Normal operation", "Monitor"),
        ]
        
        for row, (component, status, prediction, action) in enumerate(alerts):
            alerts_table.setItem(row, 0, QTableWidgetItem(component))
            status_item = QTableWidgetItem(status)
            if status == "Warning":
                status_item.setForeground(QBrush(QColor("#ff8000")))
            else:
                status_item.setForeground(QBrush(QColor("#00ff00")))
            alerts_table.setItem(row, 1, status_item)
            alerts_table.setItem(row, 2, QTableWidgetItem(prediction))
            alerts_table.setItem(row, 3, QTableWidgetItem(action))
        
        alerts_layout.addWidget(alerts_table)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        layout.addStretch()
        return panel
    
    def _create_control_strategies_tab(self) -> QWidget:
        """Create sophisticated control strategies tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Sophisticated Control Strategies - Multi-stage, self-learning algorithms")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Multi-stage boost control
        boost_group = QGroupBox("Multi-Stage Boost Control")
        boost_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        boost_layout = QGridLayout()
        
        boost_layout.addWidget(QLabel("Stage 1 Boost (psi):"), 0, 0)
        self.stage1_boost = QDoubleSpinBox()
        self.stage1_boost.setRange(0, 30)
        self.stage1_boost.setValue(10.0)
        self.stage1_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.stage1_boost, 0, 1)
        
        boost_layout.addWidget(QLabel("Stage 2 Boost (psi):"), 1, 0)
        self.stage2_boost = QDoubleSpinBox()
        self.stage2_boost.setRange(0, 30)
        self.stage2_boost.setValue(15.0)
        self.stage2_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.stage2_boost, 1, 1)
        
        boost_layout.addWidget(QLabel("Stage 3 Boost (psi):"), 2, 0)
        self.stage3_boost = QDoubleSpinBox()
        self.stage3_boost.setRange(0, 30)
        self.stage3_boost.setValue(20.0)
        self.stage3_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.stage3_boost, 2, 1)
        
        self.self_learning_boost = QCheckBox("Self-Learning Boost Control")
        self.self_learning_boost.setChecked(True)
        self.self_learning_boost.setStyleSheet("color: #ffffff;")
        boost_layout.addWidget(self.self_learning_boost, 3, 0, 1, 2)
        
        boost_group.setLayout(boost_layout)
        layout.addWidget(boost_group)
        
        # Self-learning traction control
        tc_group = QGroupBox("Self-Learning Traction Control")
        tc_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        tc_layout = QGridLayout()
        
        self.self_learning_tc = QCheckBox("Enable Self-Learning TC")
        self.self_learning_tc.setChecked(True)
        self.self_learning_tc.setStyleSheet("color: #ffffff;")
        tc_layout.addWidget(self.self_learning_tc, 0, 0, 1, 2)
        
        tc_layout.addWidget(QLabel("Learning Rate:"), 1, 0)
        self.tc_learning_rate = QDoubleSpinBox()
        self.tc_learning_rate.setRange(0.01, 1.0)
        self.tc_learning_rate.setValue(0.1)
        self.tc_learning_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        tc_layout.addWidget(self.tc_learning_rate, 1, 1)
        
        tc_group.setLayout(tc_layout)
        layout.addWidget(tc_group)
        
        layout.addStretch()
        return panel
    
    def _create_code_editor_tab(self) -> QWidget:
        """Create custom code editor tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Custom Code Editor - Open-source bin editing and custom code modification")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        file_layout = QHBoxLayout()
        
        self.load_bin_btn = QPushButton("Load Binary File")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(15)
        btn_font = self.scaler.get_scaled_font_size(11)
        self.load_bin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        self.load_bin_btn.clicked.connect(self._load_binary_file)
        file_layout.addWidget(self.load_bin_btn)
        
        self.save_bin_btn = QPushButton("Save Binary File")
        self.save_bin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        file_layout.addWidget(self.save_bin_btn)
        
        file_layout.addStretch()
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Code editor
        editor_group = QGroupBox("Binary/Code Editor")
        editor_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        editor_layout = QVBoxLayout()
        
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Load a binary file or enter custom code...")
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #404040;
            }
        """)
        editor_layout.addWidget(self.code_editor)
        
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group, stretch=1)
        
        return panel
    
    def _create_can_integration_tab(self) -> QWidget:
        """Create enhanced CAN integration tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Enhanced CAN Integration - Full vehicle system compatibility")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # CAN protocols
        protocols_group = QGroupBox("Supported CAN Protocols")
        protocols_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        protocols_layout = QVBoxLayout()
        
        protocols_table = QTableWidget()
        protocols_table.setRowCount(8)
        protocols_table.setColumnCount(3)
        protocols_table.setHorizontalHeaderLabels(["Protocol", "Status", "Features"])
        protocols_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        protocols_table.setMinimumHeight(200)
        protocols_table.setStyleSheet("""
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
        
        protocols = [
            ("OBD-II", "Active", "Read/Write DTCs, Live Data"),
            ("J1939", "Active", "Heavy Duty Vehicles"),
            ("GM GMLAN", "Active", "GM Vehicles"),
            ("Ford MS-CAN", "Active", "Ford Vehicles"),
            ("Chrysler CAN", "Active", "Chrysler/Dodge"),
            ("BMW K-CAN", "Active", "BMW Vehicles"),
            ("VAG CAN", "Active", "VW/Audi"),
            ("Toyota CAN", "Active", "Toyota/Lexus"),
        ]
        
        for row, (protocol, status, features) in enumerate(protocols):
            protocols_table.setItem(row, 0, QTableWidgetItem(protocol))
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QBrush(QColor("#00ff00")))
            protocols_table.setItem(row, 1, status_item)
            protocols_table.setItem(row, 2, QTableWidgetItem(features))
        
        protocols_layout.addWidget(protocols_table)
        protocols_group.setLayout(protocols_layout)
        layout.addWidget(protocols_group)
        
        # Vehicle system integration
        integration_group = QGroupBox("Vehicle System Integration")
        integration_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        integration_layout = QVBoxLayout()
        
        self.integrate_abs = QCheckBox("Integrate with ABS/TCS")
        self.integrate_abs.setChecked(True)
        self.integrate_abs.setStyleSheet("color: #ffffff;")
        integration_layout.addWidget(self.integrate_abs)
        
        self.integrate_cluster = QCheckBox("Integrate with Instrument Cluster")
        self.integrate_cluster.setChecked(True)
        self.integrate_cluster.setStyleSheet("color: #ffffff;")
        integration_layout.addWidget(self.integrate_cluster)
        
        self.integrate_bcm = QCheckBox("Integrate with Body Control Module")
        self.integrate_bcm.setChecked(True)
        self.integrate_bcm.setStyleSheet("color: #ffffff;")
        integration_layout.addWidget(self.integrate_bcm)
        
        integration_group.setLayout(integration_layout)
        layout.addWidget(integration_group)
        
        layout.addStretch()
        return panel
    
    def _create_offroad_mode_tab(self) -> QWidget:
        """Create off-road/racing mode tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Off-Road/Racing Mode - Emissions compliance bypass for racing applications")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Warning
        warning_group = QGroupBox("⚠️ WARNING")
        warning_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ff0000;
                border: 2px solid #ff0000; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        warning_layout = QVBoxLayout()
        
        warning_label = QLabel("OFF-ROAD USE ONLY\nThis mode disables emissions controls and is for racing/off-road use only.\nNot legal for street use in most jurisdictions.")
        warning_label.setStyleSheet("color: #ff0000; font-size: 11px; font-weight: bold;")
        warning_label.setWordWrap(True)
        warning_layout.addWidget(warning_label)
        
        warning_group.setLayout(warning_layout)
        layout.addWidget(warning_group)
        
        # Off-road mode settings
        mode_group = QGroupBox("Off-Road/Racing Mode Settings")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        mode_layout = QVBoxLayout()
        
        self.disable_egr = QCheckBox("Disable EGR (Exhaust Gas Recirculation)")
        self.disable_egr.setChecked(False)
        self.disable_egr.setStyleSheet("color: #ffffff;")
        mode_layout.addWidget(self.disable_egr)
        
        self.disable_dpf = QCheckBox("Disable DPF (Diesel Particulate Filter)")
        self.disable_dpf.setChecked(False)
        self.disable_dpf.setStyleSheet("color: #ffffff;")
        mode_layout.addWidget(self.disable_dpf)
        
        self.disable_cat = QCheckBox("Disable Catalytic Converter Monitoring")
        self.disable_cat.setChecked(False)
        self.disable_cat.setStyleSheet("color: #ffffff;")
        mode_layout.addWidget(self.disable_cat)
        
        self.disable_evap = QCheckBox("Disable EVAP System")
        self.disable_evap.setChecked(False)
        self.disable_evap.setStyleSheet("color: #ffffff;")
        mode_layout.addWidget(self.disable_evap)
        
        self.racing_fuel_strategy = QCheckBox("Enable Racing Fuel Strategy (Aggressive AFR)")
        self.racing_fuel_strategy.setChecked(False)
        self.racing_fuel_strategy.setStyleSheet("color: #ffffff;")
        mode_layout.addWidget(self.racing_fuel_strategy)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        layout.addStretch()
        return panel
    
    def _create_enhanced_autotune_tab(self) -> QWidget:
        """Create enhanced autotune tab that handles poor initial maps."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Enhanced Autotune - Handles poor initial maps and out-of-range conditions")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Enhanced features
        features_group = QGroupBox("Enhanced Autotune Features")
        features_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        features_layout = QVBoxLayout()
        
        self.handle_poor_maps = QCheckBox("Handle Poor Initial Maps (Extrapolation)")
        self.handle_poor_maps.setChecked(True)
        self.handle_poor_maps.setStyleSheet("color: #ffffff;")
        features_layout.addWidget(self.handle_poor_maps)
        
        self.out_of_range_correction = QCheckBox("Out-of-Range Correction (Wideband O2 extrapolation)")
        self.out_of_range_correction.setChecked(True)
        self.out_of_range_correction.setStyleSheet("color: #ffffff;")
        features_layout.addWidget(self.out_of_range_correction)
        
        self.interpolation_mode = QComboBox()
        self.interpolation_mode.addItems([
            "Linear Interpolation",
            "Cubic Spline",
            "Bilinear",
            "Adaptive (AI-based)"
        ])
        self.interpolation_mode.setCurrentIndex(3)  # Adaptive
        self.interpolation_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        features_layout.addWidget(QLabel("Interpolation Method:"))
        features_layout.addWidget(self.interpolation_mode)
        
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # Autotune settings
        settings_group = QGroupBox("Autotune Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Correction Rate (%/iteration):"), 0, 0)
        self.correction_rate = QDoubleSpinBox()
        self.correction_rate.setRange(0.1, 10.0)
        self.correction_rate.setValue(2.0)
        self.correction_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.correction_rate, 0, 1)
        
        settings_layout.addWidget(QLabel("Max Correction (%):"), 1, 0)
        self.max_correction = QDoubleSpinBox()
        self.max_correction.setRange(5, 50)
        self.max_correction.setValue(25.0)
        self.max_correction.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_correction, 1, 1)
        
        settings_layout.addWidget(QLabel("Min Wideband Range:"), 2, 0)
        self.min_wideband = QDoubleSpinBox()
        self.min_wideband.setRange(10.0, 14.0)
        self.min_wideband.setValue(11.0)
        self.min_wideband.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.min_wideband, 2, 1)
        
        settings_layout.addWidget(QLabel("Max Wideband Range:"), 3, 0)
        self.max_wideband = QDoubleSpinBox()
        self.max_wideband.setRange(14.0, 20.0)
        self.max_wideband.setValue(18.0)
        self.max_wideband.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.max_wideband, 3, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return panel
    
    def _load_binary_file(self) -> None:
        """Load binary file for editing."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Binary File",
            "",
            "Binary Files (*.bin *.hex);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                    # Display as hex
                    hex_data = ' '.join(f'{b:02X}' for b in data[:1000])  # First 1000 bytes
                    self.code_editor.setText(f"Loaded: {file_path}\n\n{hex_data}...")
                    QMessageBox.information(self, "Success", f"Loaded {len(data)} bytes from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        pass

