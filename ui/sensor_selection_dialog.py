"""
Sensor Selection Dialog - Add/remove sensors from graphs
"""

from __future__ import annotations

from typing import Dict, List, Set, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QMessageBox,
)


class SensorSelectionDialog(QDialog):
    """Dialog for selecting which sensors to display on graphs."""
    
    sensors_selected = Signal(list)  # Emitted with list of selected sensor names
    
    # Sensor categories for organization
    SENSOR_CATEGORIES = {
        "Powertrain": [
            "Engine_RPM", "RPM", "Throttle_Position", "Throttle", "Vehicle_Speed", "Speed",
            "Boost_Pressure", "Boost", "MAP", "Timing_Advance", "Lambda", "AFR"
        ],
        "Thermal": [
            "Coolant_Temp", "CoolantTemp", "Oil_Pressure", "OilPressure", "Oil_Temp",
            "Intake_Temp", "IAT", "EGT", "Exhaust_Gas_Temp", "Fuel_Pressure", "FuelPressure"
        ],
        "Forced Induction": [
            "Boost_Pressure", "Boost", "Turbo_RPM", "Wastegate_Position", "Intercooler_Temp",
            "Compressor_Outlet_Temp", "Turbine_Inlet_Temp"
        ],
        "Nitrous": [
            "NitrousBottlePressure", "NitrousSolenoidState", "NitrousFlowRate",
            "NitrousTemperature", "NitrousActivationTime"
        ],
        "Methanol/Water Injection": [
            "MethInjectionDuty", "MethTankLevel", "MethFlowRate", "MethPressure",
            "MethPumpSpeed", "MethNozzleSize"
        ],
        "Fuel System": [
            "FlexFuelPercent", "Fuel_Pressure", "FuelPressure", "FuelFlowRate",
            "FuelLevel", "InjectorDutyCycle", "FuelTemp"
        ],
        "Transmission": [
            "TransBrakeActive", "Gear", "Current_Gear", "Clutch_Position", "Torque_Converter_Slip",
            "TransTemp", "TransPressure"
        ],
        "Suspension": [
            "Suspension_FL", "Suspension_FR", "Suspension_RL", "Suspension_RR",
            "Shock_Position_FL", "Shock_Position_FR", "Shock_Position_RL", "Shock_Position_RR"
        ],
        "G-Forces & Motion": [
            "GForce_Lateral", "GForce_Longitudinal", "GForce_X", "GForce_Y", "GForce_Z",
            "Gyro_X", "Gyro_Y", "Gyro_Z", "Accel_X", "Accel_Y", "Accel_Z"
        ],
        "GPS": [
            "GPS_Speed", "GPS_Heading", "GPS_Altitude", "GPS_Latitude", "GPS_Longitude",
            "KF_Speed", "KF_Heading", "KF_X_Velocity", "KF_Y_Velocity"
        ],
        "Electrical": [
            "Battery_Voltage", "BatteryVoltage", "Alternator_Voltage", "Current_Draw",
            "Voltage_12V", "Voltage_5V"
        ],
        "Braking": [
            "Brake_Pressure", "BrakePressure", "Brake_Temp_FL", "Brake_Temp_FR",
            "Brake_Temp_RL", "Brake_Temp_RR"
        ],
        "Other": [
            "Knock_Count", "KnockCount", "Density_Altitude", "Barometric_Pressure",
            "Humidity", "Air_Temp", "Track_Temp"
        ]
    }
    
    def __init__(self, available_sensors: List[str], current_sensors: List[str], parent=None):
        super().__init__(parent)
        self.available_sensors = available_sensors
        self.current_sensors = set(current_sensors)
        self.setWindowTitle("Select Sensors for Graphing")
        self.setMinimumSize(700, 600)
        self.setup_ui()
        self.populate_sensors()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("<h2>Select Sensors to Graph</h2>")
        layout.addWidget(header)
        
        # Filter/search
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Search sensors...")
        self.filter_edit.textChanged.connect(self._filter_sensors)
        filter_layout.addWidget(self.filter_edit)
        
        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.addItems(list(self.SENSOR_CATEGORIES.keys()))
        self.category_combo.currentTextChanged.connect(self._filter_sensors)
        filter_layout.addWidget(self.category_combo)
        
        layout.addLayout(filter_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Available sensors list
        available_group = QGroupBox("Available Sensors")
        available_layout = QVBoxLayout()
        
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.available_list.itemDoubleClicked.connect(self._add_selected)
        available_layout.addWidget(self.available_list)
        
        add_btn = QPushButton("Add →")
        add_btn.clicked.connect(self._add_selected)
        available_layout.addWidget(add_btn)
        
        available_group.setLayout(available_layout)
        content_layout.addWidget(available_group)
        
        # Selected sensors list
        selected_group = QGroupBox("Selected Sensors")
        selected_layout = QVBoxLayout()
        
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.selected_list.itemDoubleClicked.connect(self._remove_selected)
        selected_layout.addWidget(self.selected_list)
        
        remove_btn = QPushButton("← Remove")
        remove_btn.clicked.connect(self._remove_selected)
        selected_layout.addWidget(remove_btn)
        
        selected_group.setLayout(selected_layout)
        content_layout.addWidget(selected_group)
        
        layout.addLayout(content_layout)
        
        # Quick add buttons
        quick_group = QGroupBox("Quick Add Categories")
        quick_layout = QHBoxLayout()
        
        for category in ["Powertrain", "Thermal", "Forced Induction", "Nitrous", "Methanol/Water Injection"]:
            btn = QPushButton(category)
            btn.clicked.connect(lambda checked, c=category: self._add_category(c))
            quick_layout.addWidget(btn)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        select_all_btn = QPushButton("Select All Available")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_all)
        button_layout.addWidget(clear_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._ok_clicked)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def populate_sensors(self):
        """Populate the sensor lists."""
        # Get all unique sensors from categories and available
        all_sensors = set()
        for sensors in self.SENSOR_CATEGORIES.values():
            all_sensors.update(sensors)
        all_sensors.update(self.available_sensors)
        
        # Sort sensors
        sorted_sensors = sorted(all_sensors)
        
        # Add to available list (excluding already selected)
        for sensor in sorted_sensors:
            if sensor not in self.current_sensors:
                item = QListWidgetItem(sensor)
                item.setData(Qt.ItemDataRole.UserRole, sensor)
                self.available_list.addItem(item)
        
        # Add to selected list
        for sensor in sorted(self.current_sensors):
            item = QListWidgetItem(sensor)
            item.setData(Qt.ItemDataRole.UserRole, sensor)
            self.selected_list.addItem(item)
    
    def _filter_sensors(self):
        """Filter sensors based on search text and category."""
        filter_text = self.filter_edit.text().lower()
        category = self.category_combo.currentText()
        
        # Filter available list
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            sensor = item.data(Qt.ItemDataRole.UserRole)
            
            # Check category
            in_category = category == "All Categories"
            if not in_category:
                category_sensors = self.SENSOR_CATEGORIES.get(category, [])
                in_category = sensor in category_sensors
            
            # Check text filter
            matches_text = filter_text in sensor.lower()
            
            item.setHidden(not (in_category and matches_text))
    
    def _add_selected(self):
        """Add selected sensors from available to selected."""
        selected_items = self.available_list.selectedItems()
        for item in selected_items:
            sensor = item.data(Qt.ItemDataRole.UserRole)
            if sensor not in self.current_sensors:
                self.current_sensors.add(sensor)
                new_item = QListWidgetItem(sensor)
                new_item.setData(Qt.ItemDataRole.UserRole, sensor)
                self.selected_list.addItem(new_item)
                self.available_list.takeItem(self.available_list.row(item))
    
    def _remove_selected(self):
        """Remove selected sensors from selected list."""
        selected_items = self.selected_list.selectedItems()
        for item in selected_items:
            sensor = item.data(Qt.ItemDataRole.UserRole)
            self.current_sensors.discard(sensor)
            new_item = QListWidgetItem(sensor)
            new_item.setData(Qt.ItemDataRole.UserRole, sensor)
            self.available_list.addItem(new_item)
            self.selected_list.takeItem(self.selected_list.row(item))
    
    def _add_category(self, category: str):
        """Add all sensors from a category."""
        category_sensors = self.SENSOR_CATEGORIES.get(category, [])
        added = 0
        for sensor in category_sensors:
            if sensor not in self.current_sensors and sensor in self.available_sensors:
                self.current_sensors.add(sensor)
                item = QListWidgetItem(sensor)
                item.setData(Qt.ItemDataRole.UserRole, sensor)
                self.selected_list.addItem(item)
                # Remove from available
                for i in range(self.available_list.count()):
                    avail_item = self.available_list.item(i)
                    if avail_item.data(Qt.ItemDataRole.UserRole) == sensor:
                        self.available_list.takeItem(i)
                        break
                added += 1
        if added > 0:
            QMessageBox.information(self, "Added", f"Added {added} sensors from {category}")
    
    def _select_all(self):
        """Select all available sensors."""
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            if not item.isHidden():
                sensor = item.data(Qt.ItemDataRole.UserRole)
                if sensor not in self.current_sensors:
                    self.current_sensors.add(sensor)
                    new_item = QListWidgetItem(sensor)
                    new_item.setData(Qt.ItemDataRole.UserRole, sensor)
                    self.selected_list.addItem(new_item)
                    self.available_list.takeItem(i)
    
    def _clear_all(self):
        """Clear all selected sensors."""
        while self.selected_list.count() > 0:
            item = self.selected_list.item(0)
            sensor = item.data(Qt.ItemDataRole.UserRole)
            self.current_sensors.discard(sensor)
            new_item = QListWidgetItem(sensor)
            new_item.setData(Qt.ItemDataRole.UserRole, sensor)
            self.available_list.addItem(new_item)
            self.selected_list.takeItem(0)
    
    def _ok_clicked(self):
        """Return selected sensors."""
        selected = [self.selected_list.item(i).data(Qt.ItemDataRole.UserRole) 
                   for i in range(self.selected_list.count())]
        self.sensors_selected.emit(selected)
        self.accept()
    
    def get_selected_sensors(self) -> List[str]:
        """Get list of selected sensor names."""
        return [self.selected_list.item(i).data(Qt.ItemDataRole.UserRole) 
                for i in range(self.selected_list.count())]

