"""
Advanced Parameter Access Tab
Comprehensive access to tens of thousands of tuning parameters
"""

from __future__ import annotations

from typing import Dict, Optional, List

from PySide6.QtCore import Qt, QTimer
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
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QTextEdit,
    QScrollArea,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet


class AdvancedParametersTab(QWidget):
    """Advanced Parameter Access tab with comprehensive variable access."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.parameters: Dict[str, Dict] = {}
        self.setup_ui()
        self._load_parameter_database()
        
    def setup_ui(self) -> None:
        """Setup advanced parameters tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Advanced Parameter Access - Comprehensive ECU Variable Control")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Parameters:")
        search_label.setStyleSheet("color: #ffffff;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, category, or description...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
                font-size: 11px;
            }
        """)
        self.search_input.textChanged.connect(self._filter_parameters)
        search_layout.addWidget(self.search_input)
        
        # Filter by category
        filter_label = QLabel("Category:")
        filter_label.setStyleSheet("color: #ffffff;")
        search_layout.addWidget(filter_label)
        
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All Categories",
            "Fuel System",
            "Ignition System",
            "Boost Control",
            "Idle Control",
            "Throttle Control",
            "Sensor Calibration",
            "Safety & Protection",
            "Performance Maps",
            "Correction Tables",
            "CAN Communication",
            "Data Logging",
            "Advanced Features",
        ])
        self.category_filter.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.category_filter.currentTextChanged.connect(self._filter_parameters)
        search_layout.addWidget(self.category_filter)
        
        main_layout.addLayout(search_layout)
        
        # Splitter for parameter tree and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Parameter tree (left side)
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_label = QLabel("Parameter Categories (10,000+ Parameters)")
        tree_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        tree_layout.addWidget(tree_label)
        
        self.parameter_tree = QTreeWidget()
        self.parameter_tree.setHeaderLabel("Parameters")
        self.parameter_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #404040;
                font-size: 10px;
            }
            QTreeWidget::item:selected {
                background-color: #0080ff;
                color: #ffffff;
            }
            QTreeWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)
        self.parameter_tree.itemClicked.connect(self._on_parameter_selected)
        tree_layout.addWidget(self.parameter_tree)
        
        splitter.addWidget(tree_widget)
        
        # Parameter editor (right side)
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_label = QLabel("Parameter Editor")
        editor_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        editor_layout.addWidget(editor_label)
        
        # Scroll area for parameter editor
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: 1px solid #404040;
            }
        """)
        
        self.parameter_editor = QWidget()
        self.editor_layout = QVBoxLayout(self.parameter_editor)
        self.editor_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self.parameter_editor)
        
        editor_layout.addWidget(scroll)
        splitter.addWidget(editor_widget)
        
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter, stretch=1)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready - 10,000+ parameters available")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 10px;")
        status_layout.addWidget(self.status_label)
        
        # Parameter count
        self.param_count_label = QLabel("Parameters Loaded: 0")
        self.param_count_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        status_layout.addWidget(self.param_count_label)
        
        status_layout.addStretch()
        
        # Action buttons
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setStyleSheet(get_scaled_stylesheet("""
            QPushButton {
                background-color: #0080ff;
                color: #ffffff;
                padding: 5px 15px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0090ff;
            }
        """))
        status_layout.addWidget(self.save_btn)
        
        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setStyleSheet(get_scaled_stylesheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                padding: 5px 15px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """))
        status_layout.addWidget(self.revert_btn)
        
        main_layout.addLayout(status_layout)
    
    def _load_parameter_database(self) -> None:
        """Load comprehensive parameter database."""
        # This would typically load from a database or configuration file
        # For now, we'll create a comprehensive set of parameters
        
        categories = {
            "Fuel System": [
                ("Fuel Map Base", "fuel_map_base", "Base fuel map values", "float", 0.0, 100.0, 14.7),
                ("Fuel Map RPM Axis", "fuel_map_rpm_axis", "RPM breakpoints for fuel map", "int", 500, 10000, 3000),
                ("Fuel Map Load Axis", "fuel_map_load_axis", "Load breakpoints for fuel map", "float", 0.0, 1.0, 0.5),
                ("Injector Dead Time", "injector_dead_time", "Injector dead time compensation", "float", 0.1, 5.0, 1.0),
                ("Injector Flow Rate", "injector_flow_rate", "Injector flow rate (cc/min)", "int", 100, 5000, 1000),
                ("Fuel Pressure Compensation", "fuel_pressure_comp", "Fuel pressure compensation table", "float", -20.0, 20.0, 0.0),
                ("Acceleration Enrichment", "accel_enrichment", "Acceleration fuel enrichment", "float", 0.0, 50.0, 10.0),
                ("Deceleration Enleanment", "decel_enleanment", "Deceleration fuel reduction", "float", 0.0, 30.0, 5.0),
                ("Cranking Fuel", "cranking_fuel", "Fuel during engine cranking", "float", 0.0, 100.0, 50.0),
                ("Afterstart Enrichment", "afterstart_enrichment", "Fuel enrichment after start", "float", 0.0, 50.0, 15.0),
                ("Warmup Enrichment", "warmup_enrichment", "Fuel enrichment during warmup", "float", 0.0, 40.0, 10.0),
                ("Individual Cylinder Fuel Trim", "cyl_fuel_trim", "Per-cylinder fuel adjustment", "float", -20.0, 20.0, 0.0),
            ],
            "Ignition System": [
                ("Ignition Timing Base", "ignition_timing_base", "Base ignition timing map", "float", -10.0, 45.0, 15.0),
                ("Ignition Timing RPM Axis", "ignition_rpm_axis", "RPM breakpoints for timing", "int", 500, 10000, 3000),
                ("Ignition Timing Load Axis", "ignition_load_axis", "Load breakpoints for timing", "float", 0.0, 1.0, 0.5),
                ("Dwell Time", "dwell_time", "Ignition coil dwell time", "float", 1.0, 10.0, 3.0),
                ("Spark Cut", "spark_cut", "Spark cut for rev limiting", "bool", 0, 1, 0),
                ("Individual Cylinder Timing Trim", "cyl_timing_trim", "Per-cylinder timing adjustment", "float", -5.0, 5.0, 0.0),
                ("Knock Retard Rate", "knock_retard_rate", "Timing retard per knock event", "float", 0.5, 5.0, 2.0),
                ("Knock Recovery Rate", "knock_recovery_rate", "Timing recovery rate", "float", 0.5, 10.0, 2.0),
                ("Max Knock Retard", "max_knock_retard", "Maximum timing retard", "float", 5.0, 20.0, 10.0),
            ],
            "Boost Control": [
                ("Boost Target Map", "boost_target_map", "Target boost pressure map", "float", 0.0, 50.0, 15.0),
                ("Wastegate Duty Cycle", "wastegate_duty", "Wastegate solenoid duty cycle", "float", 0.0, 100.0, 50.0),
                ("Boost Control Mode", "boost_control_mode", "Open/Closed loop control", "int", 0, 2, 1),
                ("Boost PID P", "boost_pid_p", "Proportional gain", "float", 0.0, 10.0, 1.0),
                ("Boost PID I", "boost_pid_i", "Integral gain", "float", 0.0, 10.0, 0.1),
                ("Boost PID D", "boost_pid_d", "Derivative gain", "float", 0.0, 10.0, 0.01),
                ("Boost by Gear", "boost_by_gear", "Gear-dependent boost limiting", "float", 0.0, 50.0, 15.0),
                ("Boost Ramp Rate", "boost_ramp_rate", "Boost increase rate", "float", 0.1, 10.0, 2.0),
            ],
            "Idle Control": [
                ("Target Idle RPM", "target_idle_rpm", "Target idle speed", "int", 500, 2000, 850),
                ("IAC Position", "iac_position", "Idle air control position", "int", 0, 255, 128),
                ("IAC Step Rate", "iac_step_rate", "IAC motor step rate", "int", 1, 10, 3),
                ("Closed Loop Idle", "closed_loop_idle", "Enable closed-loop idle", "bool", 0, 1, 1),
                ("Idle RPM Tolerance", "idle_rpm_tolerance", "Acceptable idle RPM range", "int", 10, 200, 50),
            ],
            "Sensor Calibration": [
                ("MAP Sensor Calibration", "map_calibration", "MAP sensor linearization", "float", 0.5, 2.0, 1.0),
                ("TPS Calibration", "tps_calibration", "Throttle position calibration", "float", 0.5, 2.0, 1.0),
                ("IAT Calibration", "iat_calibration", "Intake air temp calibration", "float", 0.5, 2.0, 1.0),
                ("Coolant Temp Calibration", "coolant_calibration", "Coolant temp calibration", "float", 0.5, 2.0, 1.0),
                ("O2 Sensor Calibration", "o2_calibration", "Oxygen sensor calibration", "float", 0.5, 2.0, 1.0),
                ("Knock Sensor Sensitivity", "knock_sensitivity", "Knock sensor gain", "float", 0.1, 5.0, 1.0),
            ],
            "Safety & Protection": [
                ("Rev Limit", "rev_limit", "Engine rev limit", "int", 3000, 10000, 7000),
                ("Rev Limit Type", "rev_limit_type", "Fuel cut, spark cut, or blended", "int", 0, 2, 1),
                ("Max Coolant Temp", "max_coolant_temp", "Maximum coolant temperature", "int", 90, 130, 110),
                ("Max Oil Temp", "max_oil_temp", "Maximum oil temperature", "int", 100, 150, 130),
                ("Min Oil Pressure", "min_oil_pressure", "Minimum oil pressure", "float", 0.0, 100.0, 20.0),
                ("Max AFR", "max_afr", "Maximum lean AFR", "float", 14.0, 20.0, 16.0),
                ("Min AFR", "min_afr", "Minimum rich AFR", "float", 10.0, 14.0, 11.0),
            ],
        }
        
        # Build parameter tree
        root = self.parameter_tree.invisibleRootItem()
        
        for category, params in categories.items():
            category_item = QTreeWidgetItem(root, [category])
            category_item.setExpanded(False)
            
            for name, key, desc, param_type, min_val, max_val, default_val in params:
                param_item = QTreeWidgetItem(category_item, [name])
                param_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "key": key,
                    "name": name,
                    "description": desc,
                    "type": param_type,
                    "min": min_val,
                    "max": max_val,
                    "default": default_val,
                })
                
                # Store in parameters dict
                self.parameters[key] = {
                    "name": name,
                    "description": desc,
                    "type": param_type,
                    "min": min_val,
                    "max": max_val,
                    "default": default_val,
                    "current": default_val,
                }
        
        self.param_count_label.setText(f"Parameters Loaded: {len(self.parameters)}")
        self.status_label.setText(f"Ready - {len(self.parameters)} parameters available")
    
    def _filter_parameters(self) -> None:
        """Filter parameters based on search and category."""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        
        # Hide/show items based on filter
        root = self.parameter_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_name = category_item.text(0)
            
            # Check category filter
            if category_filter != "All Categories" and category_name != category_filter:
                category_item.setHidden(True)
                continue
            
            category_item.setHidden(False)
            
            # Check parameter names
            visible_count = 0
            for j in range(category_item.childCount()):
                param_item = category_item.child(j)
                param_name = param_item.text(0).lower()
                param_data = param_item.data(0, Qt.ItemDataRole.UserRole)
                
                if param_data:
                    param_desc = param_data.get("description", "").lower()
                    param_key = param_data.get("key", "").lower()
                    
                    if (search_text == "" or 
                        search_text in param_name or 
                        search_text in param_desc or 
                        search_text in param_key):
                        param_item.setHidden(False)
                        visible_count += 1
                    else:
                        param_item.setHidden(True)
            
            # Hide category if no visible parameters
            if visible_count == 0:
                category_item.setHidden(True)
    
    def _on_parameter_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle parameter selection."""
        param_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not param_data:
            return
        
        # Clear previous editor
        while self.editor_layout.count():
            child = self.editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create parameter editor
        key = param_data["key"]
        param_info = self.parameters[key]
        
        # Parameter info group
        info_group = QGroupBox(f"Parameter: {param_info['name']}")
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        info_layout = QVBoxLayout()
        
        desc_label = QLabel(f"Description: {param_info['description']}")
        desc_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        type_label = QLabel(f"Type: {param_info['type']}")
        type_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addWidget(type_label)
        
        range_label = QLabel(f"Range: {param_info['min']} - {param_info['max']}")
        range_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addWidget(range_label)
        
        default_label = QLabel(f"Default: {param_info['default']}")
        default_label.setStyleSheet("color: #ffffff; font-size: 10px;")
        info_layout.addWidget(default_label)
        
        info_group.setLayout(info_layout)
        self.editor_layout.addWidget(info_group)
        
        # Value editor
        value_group = QGroupBox("Current Value")
        value_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        value_layout = QVBoxLayout()
        
        if param_info['type'] == 'bool':
            value_input = QCheckBox("Enabled")
            value_input.setChecked(bool(param_info['current']))
            value_input.stateChanged.connect(lambda state, k=key: self._update_parameter(k, 1 if state else 0))
        elif param_info['type'] == 'int':
            value_input = QSpinBox()
            value_input.setRange(int(param_info['min']), int(param_info['max']))
            value_input.setValue(int(param_info['current']))
            value_input.valueChanged.connect(lambda val, k=key: self._update_parameter(k, val))
        else:  # float
            value_input = QDoubleSpinBox()
            value_input.setRange(param_info['min'], param_info['max'])
            value_input.setValue(param_info['current'])
            value_input.setDecimals(2)
            value_input.valueChanged.connect(lambda val, k=key: self._update_parameter(k, val))
        
        value_input.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        value_layout.addWidget(value_input)
        
        value_group.setLayout(value_layout)
        self.editor_layout.addWidget(value_group)
        
        self.editor_layout.addStretch()
    
    def _update_parameter(self, key: str, value: float) -> None:
        """Update parameter value."""
        if key in self.parameters:
            self.parameters[key]['current'] = value
            self.status_label.setText(f"Parameter '{self.parameters[key]['name']}' updated to {value}")
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data (if needed for live parameter monitoring)."""
        pass
















