"""
Virtual Dyno Tab
Dedicated tab for Virtual Dyno Session Horsepower Estimation with settings and controls
"""

from __future__ import annotations

from typing import Dict, Optional, List, Tuple
import time
import threading

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    from ui.dyno_view import VirtualDynoView
    from services.virtual_dyno import VirtualDyno, VehicleSpecs, EnvironmentalConditions
    from ui.dyno_calibration_dialog import DynoCalibrationDialog
except ImportError:
    VirtualDynoView = None
    VirtualDyno = None
    VehicleSpecs = None
    EnvironmentalConditions = None
    DynoCalibrationDialog = None


class DynoTab(QWidget):
    """Virtual Dyno tab with horsepower estimation, settings, and calibration."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.virtual_dyno: Optional[VirtualDyno] = None
        
        # Data logging state
        self.logging_active = False
        self.logged_data: List[Tuple[float, float, Optional[float]]] = []  # (time, speed_mps, rpm)
        self.log_start_time: Optional[float] = None
        
        self.setup_ui()
        self._start_update_timer()
        
    def setup_ui(self) -> None:
        """Setup dyno tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Set background
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Settings panel
        left_panel = self._create_settings_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Dyno view
        center_panel = self._create_dyno_view_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Vehicle specs and environment
        right_panel = self._create_specs_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        layout = QHBoxLayout(bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        title = QLabel("Virtual Dyno - Horsepower Estimation")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Button styling constants
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        
        # Logging controls
        self.logging_status_label = QLabel("Not Logging")
        self.logging_status_label.setStyleSheet("color: #9aa0a6; font-size: 11px; padding: 0 10px;")
        layout.addWidget(self.logging_status_label)
        
        self.start_logging_btn = QPushButton("Start Logging")
        self.start_logging_btn.setStyleSheet(
            f"background-color: #2d7d32; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; "
            f"font-size: {btn_font}px; font-weight: bold;"
        )
        self.start_logging_btn.clicked.connect(self._start_logging)
        layout.addWidget(self.start_logging_btn)
        
        self.stop_logging_btn = QPushButton("Stop Logging")
        self.stop_logging_btn.setStyleSheet(
            f"background-color: #c62828; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; "
            f"font-size: {btn_font}px; font-weight: bold;"
        )
        self.stop_logging_btn.clicked.connect(self._stop_logging)
        self.stop_logging_btn.setEnabled(False)
        layout.addWidget(self.stop_logging_btn)
        
        # Calibration button
        self.calibrate_btn = QPushButton("Calibrate")
        self.calibrate_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        self.calibrate_btn.clicked.connect(self._open_calibration)
        layout.addWidget(self.calibrate_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset Session")
        self.reset_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        self.reset_btn.clicked.connect(self._reset_session)
        layout.addWidget(self.reset_btn)
        
        # Export button
        self.export_btn = QPushButton("Export Data")
        self.export_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        self.export_btn.clicked.connect(self._export_data)
        layout.addWidget(self.export_btn)
        
        # Export Session button
        self.export_session_btn = QPushButton("Export Session")
        self.export_session_btn.setStyleSheet(f"background-color: #0066cc; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        self.export_session_btn.clicked.connect(self._export_session)
        layout.addWidget(self.export_session_btn)
        
        return bar
        
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Session controls
        session_group = QGroupBox("Session Controls")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        session_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        session_layout = QVBoxLayout()
        session_layout.setSpacing(get_scaled_size(10))
        
        # Method selection
        session_layout.addWidget(QLabel("Calculation Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Acceleration Based", "Torque Based", "Speed Delta", "Coast Down"])
        self.method_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        session_layout.addWidget(self.method_combo)
        
        # Smoothing
        session_layout.addWidget(QLabel("Data Smoothing:"))
        self.smoothing = QSpinBox()
        self.smoothing.setRange(0, 10)
        self.smoothing.setValue(3)
        self.smoothing.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        session_layout.addWidget(self.smoothing)
        
        # Auto-start
        from PySide6.QtWidgets import QCheckBox
        self.auto_start = QCheckBox("Auto-Start on Acceleration")
        self.auto_start.setChecked(True)
        self.auto_start.setStyleSheet("color: #ffffff;")
        session_layout.addWidget(self.auto_start)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # Accuracy indicator
        accuracy_group = QGroupBox("Accuracy Estimate")
        accuracy_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        accuracy_layout = QVBoxLayout()
        
        self.accuracy_label = QLabel("Not Calibrated")
        accuracy_font = get_scaled_font_size(14)
        self.accuracy_label.setStyleSheet(f"font-size: {accuracy_font}px; font-weight: bold; color: #ffaa00; padding: {get_scaled_size(5)}px;")
        accuracy_layout.addWidget(self.accuracy_label)
        
        self.accuracy_desc = QLabel("Calibrate with known dyno run for ±3-5% accuracy")
        desc_font = get_scaled_font_size(10)
        self.accuracy_desc.setStyleSheet(f"font-size: {desc_font}px; color: #9aa0a6;")
        self.accuracy_desc.setWordWrap(True)
        accuracy_layout.addWidget(self.accuracy_desc)
        
        accuracy_group.setLayout(accuracy_layout)
        layout.addWidget(accuracy_group)
        
        layout.addStretch()
        return panel
        
    def _create_dyno_view_panel(self) -> QWidget:
        """Create dyno view panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        if VirtualDynoView:
            try:
                self.dyno_view = VirtualDynoView()
                layout.addWidget(self.dyno_view, stretch=1)
            except Exception:
                placeholder = QLabel("Virtual Dyno View unavailable")
                placeholder.setStyleSheet("color: #ffffff; padding: 20px;")
                layout.addWidget(placeholder, stretch=1)
        else:
            placeholder = QLabel("Virtual Dyno module not available")
            placeholder.setStyleSheet("color: #ffffff; padding: 20px;")
            layout.addWidget(placeholder, stretch=1)
        
        return panel
        
    def _create_specs_panel(self) -> QWidget:
        """Create vehicle specs and environment panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Vehicle Specs
        specs_group = QGroupBox("Vehicle Specifications")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        specs_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        specs_layout = QVBoxLayout()
        specs_layout.setSpacing(get_scaled_size(8))
        
        # Curb weight
        specs_layout.addWidget(QLabel("Curb Weight (kg):"))
        self.curb_weight = QDoubleSpinBox()
        self.curb_weight.setRange(500, 5000)
        self.curb_weight.setValue(1500)
        self.curb_weight.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        specs_layout.addWidget(self.curb_weight)
        
        # Driver weight
        specs_layout.addWidget(QLabel("Driver Weight (kg):"))
        self.driver_weight = QDoubleSpinBox()
        self.driver_weight.setRange(0, 200)
        self.driver_weight.setValue(80)
        self.driver_weight.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        specs_layout.addWidget(self.driver_weight)
        
        # Frontal area
        specs_layout.addWidget(QLabel("Frontal Area (m²):"))
        self.frontal_area = QDoubleSpinBox()
        self.frontal_area.setRange(1.0, 5.0)
        self.frontal_area.setValue(2.0)
        self.frontal_area.setDecimals(2)
        self.frontal_area.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        specs_layout.addWidget(self.frontal_area)
        
        # Drag coefficient
        specs_layout.addWidget(QLabel("Drag Coefficient (Cd):"))
        self.drag_coef = QDoubleSpinBox()
        self.drag_coef.setRange(0.1, 1.0)
        self.drag_coef.setValue(0.30)
        self.drag_coef.setDecimals(2)
        self.drag_coef.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        specs_layout.addWidget(self.drag_coef)
        
        # Drivetrain type
        specs_layout.addWidget(QLabel("Drivetrain Type:"))
        self.drivetrain = QComboBox()
        self.drivetrain.addItems(["FWD", "RWD", "AWD"])
        self.drivetrain.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        specs_layout.addWidget(self.drivetrain)
        
        specs_group.setLayout(specs_layout)
        layout.addWidget(specs_group)
        
        # Environmental Conditions
        env_group = QGroupBox("Environmental Conditions")
        env_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        env_layout = QVBoxLayout()
        env_layout.setSpacing(get_scaled_size(8))
        
        # Temperature
        env_layout.addWidget(QLabel("Temperature (°C):"))
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-40, 60)
        self.temperature.setValue(20)
        self.temperature.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        env_layout.addWidget(self.temperature)
        
        # Altitude
        env_layout.addWidget(QLabel("Altitude (m):"))
        self.altitude = QDoubleSpinBox()
        self.altitude.setRange(0, 5000)
        self.altitude.setValue(0)
        self.altitude.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        env_layout.addWidget(self.altitude)
        
        # Humidity
        env_layout.addWidget(QLabel("Humidity (%):"))
        self.humidity = QDoubleSpinBox()
        self.humidity.setRange(0, 100)
        self.humidity.setValue(50)
        self.humidity.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        env_layout.addWidget(self.humidity)
        
        env_group.setLayout(env_layout)
        layout.addWidget(env_group)
        
        layout.addStretch()
        return panel
        
    def _open_calibration(self) -> None:
        """Open calibration dialog."""
        if DynoCalibrationDialog:
            try:
                dialog = DynoCalibrationDialog(self)
                dialog.exec()
            except Exception as e:
                print(f"Error opening calibration dialog: {e}")
        else:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("Calibration")
            msg.setText("Calibration dialog not available")
            msg.exec()
            
    def _start_logging(self) -> None:
        """Start data logging session."""
        if self.logging_active:
            return
        
        # Check license and demo restrictions
        try:
            from core.license_manager import get_license_manager
            from core.demo_restrictions import get_demo_restrictions
            
            license_manager = get_license_manager()
            if license_manager.is_demo_mode():
                demo_restrictions = get_demo_restrictions()
                allowed, reason = demo_restrictions.can_use_feature('logging')
                if not allowed:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "Demo Mode - Feature Restricted",
                        f"{reason}\n\nEnter a license key to unlock unlimited logging."
                    )
                    return
                # Start logging session tracking
                demo_restrictions.start_logging()
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"License check failed: {e}")
        
        # Initialize dyno if needed
        if not self.virtual_dyno:
            self._initialize_virtual_dyno()
        
        if not self.virtual_dyno:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Cannot start logging: Virtual dyno not initialized.\nPlease check vehicle specs.")
            return
        
        # Reset previous data
        self.logged_data = []
        self.log_start_time = time.time()
        self.logging_active = True
        
        # Reset dyno curve for new run
        self.virtual_dyno.reset_curve()
        
        # Update UI (check if buttons exist first)
        if hasattr(self, 'start_logging_btn'):
            self.start_logging_btn.setEnabled(False)
        if hasattr(self, 'stop_logging_btn'):
            self.stop_logging_btn.setEnabled(True)
        if hasattr(self, 'logging_status_label'):
            self.logging_status_label.setText("Logging... (Recording data)")
            self.logging_status_label.setStyleSheet("color: #4caf50; font-size: 11px; font-weight: bold;")
        
        # Clear speed history for fresh calculation
        if hasattr(self, '_speed_history'):
            self._speed_history.clear()
    
    def _stop_logging(self) -> None:
        """Stop data logging and process results."""
        if not self.logging_active:
            return
        
        self.logging_active = False
        
        # Update UI (check if buttons exist first)
        if hasattr(self, 'start_logging_btn'):
            self.start_logging_btn.setEnabled(True)
        if hasattr(self, 'stop_logging_btn'):
            self.stop_logging_btn.setEnabled(False)
        if hasattr(self, 'logging_status_label'):
            self.logging_status_label.setText("Processing data...")
            self.logging_status_label.setStyleSheet("color: #ff9800; font-size: 11px;")
        
        # Process logged data using improved batch calculation
        if len(self.logged_data) >= 2:
            try:
                self._process_logged_data()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error processing logged data: {e}", exc_info=True)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", f"Error processing data: {e}")
        
        if hasattr(self, 'logging_status_label'):
            self.logging_status_label.setText("Logging stopped")
            self.logging_status_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
    
    def _process_logged_data(self) -> None:
        """Process logged data using improved batch calculation method."""
        if not self.virtual_dyno or not self.logged_data:
            return
        
        import numpy as np
        
        # Extract data arrays
        time_s = np.array([d[0] for d in self.logged_data])
        speed_mps = np.array([d[1] for d in self.logged_data])
        rpm_array = np.array([d[2] if d[2] is not None else 0.0 for d in self.logged_data])
        rpm_array = rpm_array if np.any(rpm_array > 0) else None
        
        # Use improved batch calculation method
        readings = self.virtual_dyno.calculate_horsepower_from_timeseries(
            time_s=time_s,
            speed_mps=speed_mps,
            rpm=rpm_array if rpm_array is not None else None,
            smooth_window=11,
            smooth_poly=3,
        )
        
        # Update curve with processed data
        if self.virtual_dyno.current_curve:
            self.virtual_dyno.current_curve.readings = readings
            # Update peak values
            if readings:
                hp_values = [r.horsepower_crank for r in readings]
                torque_values = [r.torque_ftlb for r in readings if r.torque_ftlb is not None]
                rpm_values = [r.rpm for r in readings if r.rpm is not None]
                
                if hp_values:
                    max_idx = np.argmax(hp_values)
                    self.virtual_dyno.current_curve.peak_hp_crank = hp_values[max_idx]
                    self.virtual_dyno.current_curve.peak_hp_wheel = readings[max_idx].horsepower_wheel
                    if rpm_values:
                        self.virtual_dyno.current_curve.peak_hp_rpm = rpm_values[max_idx]
                
                if torque_values:
                    max_torque_idx = np.argmax(torque_values)
                    self.virtual_dyno.current_curve.peak_torque_ftlb = torque_values[max_torque_idx]
                    if rpm_values:
                        self.virtual_dyno.current_curve.peak_torque_rpm = rpm_values[max_torque_idx]
        
        # Update UI
        if hasattr(self, 'dyno_view') and self.dyno_view:
            self.dyno_view.update_curve(self.virtual_dyno.current_curve)
        
        # Show results summary
        self._show_run_summary()
    
    def _show_run_summary(self) -> None:
        """Show summary window with peak HP and torque."""
        if not self.virtual_dyno or not self.virtual_dyno.current_curve.readings:
            return
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        
        curve = self.virtual_dyno.current_curve
        peak_hp = curve.peak_hp_crank
        peak_torque = curve.peak_torque_ftlb or 0.0
        peak_hp_rpm = curve.peak_hp_rpm or 0.0
        peak_torque_rpm = curve.peak_torque_rpm or 0.0
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Run Summary")
        dialog.setMinimumWidth(get_scaled_size(300))
        dialog.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(get_scaled_size(15))
        layout.setContentsMargins(get_scaled_size(20), get_scaled_size(20), get_scaled_size(20), get_scaled_size(20))
        
        title = QLabel("Last Run Summary")
        title_font = get_scaled_font_size(16)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #00ff00;")
        layout.addWidget(title)
        
        run_name = QLabel(f"Run: {curve.run_name or 'Current Run'}")
        run_name.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: #9aa0a6;")
        layout.addWidget(run_name)
        
        hp_label = QLabel(f"Peak HP: {peak_hp:.1f} @ {peak_hp_rpm:.0f} RPM")
        hp_label.setStyleSheet(f"font-size: {get_scaled_font_size(14)}px; font-weight: bold; color: #00ff00;")
        layout.addWidget(hp_label)
        
        torque_label = QLabel(f"Peak Torque: {peak_torque:.1f} ft-lb @ {peak_torque_rpm:.0f} RPM")
        torque_label.setStyleSheet(f"font-size: {get_scaled_font_size(14)}px; font-weight: bold; color: #00ff00;")
        layout.addWidget(torque_label)
        
        data_points = QLabel(f"Data Points: {len(curve.readings)}")
        data_points.setStyleSheet(f"font-size: {get_scaled_font_size(11)}px; color: #9aa0a6;")
        layout.addWidget(data_points)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 8px;")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _reset_session(self) -> None:
        """Reset dyno session."""
        # Stop logging if active
        if self.logging_active:
            self._stop_logging()
        
        if self.virtual_dyno:
            self.virtual_dyno.reset_curve()
        if hasattr(self, 'dyno_view') and self.dyno_view:
            self.dyno_view.clear_comparisons()
        
        # Clear logged data
        self.logged_data = []
        self.log_start_time = None
        if hasattr(self, '_speed_history'):
            self._speed_history.clear()
            
    def _export_data(self) -> None:
        """Export current dyno run data."""
        if not self.virtual_dyno or not self.virtual_dyno.current_curve.readings:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Data", "No dyno data to export. Please run a logging session first.")
            return
        
        # Check license and demo restrictions
        try:
            from core.license_manager import get_license_manager
            from core.demo_restrictions import get_demo_restrictions
            
            license_manager = get_license_manager()
            if license_manager.is_demo_mode():
                demo_restrictions = get_demo_restrictions()
                allowed, reason = demo_restrictions.can_use_feature('export')
                if not allowed:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self,
                        "Demo Mode - Feature Restricted",
                        f"{reason}\n\nEnter a license key to unlock unlimited exports."
                    )
                    return
                # Record export
                demo_restrictions.record_export()
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"License check failed: {e}")
        
        from PySide6.QtWidgets import QFileDialog
        import pandas as pd
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Dyno Data",
            "dyno_run.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if filename:
            try:
                # Export current run
                curve = self.virtual_dyno.current_curve
                data = []
                for reading in curve.readings:
                    rel_time = reading.timestamp - curve.run_timestamp if curve.run_timestamp > 0 else 0
                    data.append({
                        'time_s': rel_time,
                        'rpm': reading.rpm or 0.0,
                        'speed_mph': reading.speed_mph,
                        'speed_mps': reading.speed_mps,
                        'acceleration_mps2': reading.acceleration_mps2,
                        'wheel_hp': reading.horsepower_wheel,
                        'engine_hp': reading.horsepower_crank,
                        'torque_ftlb': reading.torque_ftlb or 0.0,
                        'confidence': reading.confidence,
                        'method': reading.method.value,
                    })
                
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False)
                
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Export Successful", f"Dyno data exported to:\n{filename}")
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Failed", f"Failed to export data:\n{str(e)}")
    
    def _export_session(self) -> None:
        """Export all session runs to a single CSV file."""
        if not self.virtual_dyno:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Dyno", "Virtual Dyno not initialized.")
            return
        
        try:
            runs = self.virtual_dyno.get_session_runs()
            if not runs:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "No Data", "No session runs to export. Please run logging sessions first.")
                return
            
            from PySide6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Session Summary",
                "session_summary.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            if filename:
                exported_path = self.virtual_dyno.export_session(filename)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Exported {len(runs)} runs to:\n{exported_path}"
                )
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export Failed", f"Failed to export session:\n{str(e)}")
            
    def _start_update_timer(self) -> None:
        """Start timer for dyno updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_dyno)
        self.update_timer.start(100)  # 10 Hz
        
    def _update_dyno(self) -> None:
        """Update dyno with current telemetry."""
        # This will be called by update_telemetry
        pass
        
    def _initialize_virtual_dyno(self) -> None:
        """Initialize virtual dyno with current settings."""
        if not VehicleSpecs or not VirtualDyno:
            return
            
        try:
            if hasattr(self, 'curb_weight') and hasattr(self, 'driver_weight'):
                specs = VehicleSpecs(
                    curb_weight_kg=self.curb_weight.value(),
                    driver_weight_kg=self.driver_weight.value(),
                    frontal_area_m2=self.frontal_area.value(),
                    drag_coefficient=self.drag_coef.value(),
                    drivetrain_type=self.drivetrain.currentText(),
                )
                
                if EnvironmentalConditions:
                    env = EnvironmentalConditions(
                        temperature_c=self.temperature.value(),
                        altitude_m=self.altitude.value(),
                        humidity_percent=self.humidity.value(),
                    )
                
                self.virtual_dyno = VirtualDyno(vehicle_specs=specs)
        except Exception as e:
            print(f"Error initializing virtual dyno: {e}")
            
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update dyno tab with telemetry data."""
        # Initialize if needed
        if not self.virtual_dyno:
            self._initialize_virtual_dyno()
            
        if not self.virtual_dyno or not hasattr(self, 'dyno_view') or not self.dyno_view:
            return
            
        # Get required data
        speed_mph = data.get("Speed", data.get("Vehicle_Speed", 0))
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        
        # Calculate acceleration using improved method
        # Store speed history for better acceleration calculation
        if not hasattr(self, '_speed_history'):
            self._speed_history = []  # List of (timestamp, speed_mps)
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = None
        
        import time
        current_time = time.time()
        speed_mps = speed_mph * 0.44704  # Convert to m/s
        
        # Calculate acceleration from speed change (more accurate than throttle estimate)
        acceleration_mps2 = 0.0
        if len(self._speed_history) >= 2:
            # Use last two points for acceleration
            dt = current_time - self._speed_history[-1][0]
            if dt > 0 and dt < 5.0:  # Valid time delta (avoid huge jumps)
                dv = speed_mps - self._speed_history[-1][1]
                acceleration_mps2 = dv / dt
        elif len(self._speed_history) == 1:
            # First calculation - use small time window
            dt = current_time - self._speed_history[0][0]
            if dt > 0 and dt < 5.0:
                dv = speed_mps - self._speed_history[0][1]
                acceleration_mps2 = dv / dt
        
        # Fallback: if no speed history, try to use acceleration sensor or throttle
        if acceleration_mps2 == 0.0:
            # Try acceleration sensor first
            accel_sensor = data.get("Acceleration", data.get("Accel_X", None))
            if accel_sensor is not None:
                acceleration_mps2 = accel_sensor
            else:
                # Last resort: use throttle as rough estimate (less accurate)
                throttle = data.get("Throttle_Position", data.get("throttle", 0)) / 100.0
                if throttle > 0.1:
                    acceleration_mps2 = throttle * 2.5  # Conservative estimate
        
        # Store current speed for next calculation
        if len(self._speed_history) >= 10:  # Keep last 10 points
            self._speed_history.pop(0)
        self._speed_history.append((current_time, speed_mps))
        self._last_update_time = current_time
        
        # Log data if logging is active
        if self.logging_active and speed_mph > 0:
            elapsed_time = current_time - self.log_start_time if self.log_start_time else 0.0
            self.logged_data.append((elapsed_time, speed_mps, rpm if rpm > 0 else None))
        
        # Only calculate if we have meaningful data
        if speed_mph > 5.0 and rpm > 500:  # Minimum thresholds
            try:
                # Calculate horsepower using improved method
                # The VirtualDyno now uses Savitzky-Golay smoothing automatically
                reading = self.virtual_dyno.calculate_horsepower(
                    speed_mph=speed_mph,
                    acceleration_mps2=acceleration_mps2,
                    rpm=rpm if rpm > 0 else None,
                )
                
                # Update view
                self.dyno_view.update_reading(reading)
                
                # Update curve
                if self.virtual_dyno.current_curve:
                    self.dyno_view.update_curve(self.virtual_dyno.current_curve)
                    
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error updating dyno: {e}")


__all__ = ["DynoTab"]

