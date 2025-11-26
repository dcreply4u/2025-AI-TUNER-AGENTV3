"""
ECU Tuning Main Interface
Professional race car engine tuning software - replaces main window
"""

from __future__ import annotations

import time
import csv
import logging
from typing import Dict, Optional, List, Any
from collections import deque
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)

try:
    from services.backup_manager import BackupManager, BackupType, BackupEntry
    BACKUP_AVAILABLE = True
except ImportError:
    BACKUP_AVAILABLE = False
    BackupManager = None  # type: ignore
    BackupType = None  # type: ignore
    BackupEntry = None  # type: ignore

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QSizePolicy,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QDialog,
    QSlider,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet

from ui.ecu_tuning_widgets import (
    AnalogGauge,
    VETableWidget,
    RealTimeGraph,
    CellWeightingWidget,
    StatisticsPanel,
)
from ui.car_image_widget import CarImageWidget


@dataclass
class NitrousStageConfig:
    """Configuration for a progressive nitrous stage."""

    name: str
    enabled: bool = True
    shot_size_hp: int = 100
    start_trigger: str = "RPM"  # RPM, Time, Speed, TPS, Boost
    start_value: float = 3000.0
    end_trigger: str = "Time"  # Time, RPM, Speed, Boost
    end_value: float = 2.0
    ramp_in_time: float = 1.5
    ramp_out_time: float = 1.0
    frequency_hz: int = 18
    resume_behavior: str = "Resume"  # Resume, Restart, Auto


@dataclass
class NitrousRunLog:
    """Summary of a single nitrous pass."""

    run_id: int
    start_timestamp: float
    duration_s: float
    peak_duty: float
    peak_shot_hp: float
    start_rpm: float
    end_rpm: float
    min_lambda: float
    max_boost: float
    active_stages: str


class ECUTuningTab(QWidget):
    """Main ECU Tuning tab with sub-tabs for different ECU functions."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup ECU tuning tab with sub-tabs."""
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
        # Use Preferred instead of Expanding to allow proper resizing
        self.sub_tabs.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Import sub-tabs
        from ui.ecu_sub_tabs import (
            IgnitionTimingTab,
            IdleControlTab,
            BoostControlTab,
            FuelMapsTab,
        )
        from ui.tune_database_tab import TuneDatabaseTab
        from ui.motec_advanced_features import (
            HiLoInjectionTab,
            MultiPulseInjectionTab,
            InjectionTimingTab,
            ColdStartFuelTab,
            SiteTablesTab,
            GearChangeIgnitionCutTab,
            CAMControlTab,
            ServoMotorControlTab,
        )
        
        # Tune Database sub-tab (first tab for easy access)
        self.tune_database_tab = TuneDatabaseTab()
        self.tune_database_tab.tune_selected.connect(self._on_tune_selected)
        self.sub_tabs.addTab(self.tune_database_tab, "Tune Database")
        
        # Fuel VE Table sub-tab
        self.fuel_ve_tab = FuelVETab()
        self.sub_tabs.addTab(self.fuel_ve_tab, "Fuel VE Table")
        
        # Ignition Timing sub-tab
        self.ignition_tab = IgnitionTimingTab()
        self.sub_tabs.addTab(self.ignition_tab, "Ignition Timing")
        
        # Fuel Maps sub-tab
        self.fuel_maps_tab = FuelMapsTab()
        self.sub_tabs.addTab(self.fuel_maps_tab, "Fuel Maps")
        
        # Idle Control sub-tab
        self.idle_tab = IdleControlTab()
        self.sub_tabs.addTab(self.idle_tab, "Idle Control")
        
        # Boost Control sub-tab
        self.boost_tab = BoostControlTab()
        self.sub_tabs.addTab(self.boost_tab, "Boost Control")
        
        # MoTeC Advanced Features
        self.hi_lo_injection_tab = HiLoInjectionTab()
        self.sub_tabs.addTab(self.hi_lo_injection_tab, "Hi/Lo Injection")
        
        self.multi_pulse_injection_tab = MultiPulseInjectionTab()
        self.sub_tabs.addTab(self.multi_pulse_injection_tab, "Multi-Pulse Injection")
        
        self.injection_timing_tab = InjectionTimingTab()
        self.sub_tabs.addTab(self.injection_timing_tab, "Injection Timing")
        
        self.cold_start_fuel_tab = ColdStartFuelTab()
        self.sub_tabs.addTab(self.cold_start_fuel_tab, "Cold Start Fuel")
        
        self.site_tables_tab = SiteTablesTab()
        self.sub_tabs.addTab(self.site_tables_tab, "Site Tables")
        
        self.gear_change_cut_tab = GearChangeIgnitionCutTab()
        self.sub_tabs.addTab(self.gear_change_cut_tab, "Gear Change Cut")
        
        self.cam_control_tab = CAMControlTab()
        self.sub_tabs.addTab(self.cam_control_tab, "CAM Control")
        
        self.servo_control_tab = ServoMotorControlTab()
        self.sub_tabs.addTab(self.servo_control_tab, "Servo Control")
        
        main_layout.addWidget(self.sub_tabs, stretch=1)
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update all sub-tabs with telemetry data."""
        # Tune database tab doesn't need telemetry updates
        self.fuel_ve_tab.update_telemetry(data)
        self.ignition_tab.update_telemetry(data)
        self.fuel_maps_tab.update_telemetry(data)
        self.idle_tab.update_telemetry(data)
        self.boost_tab.update_telemetry(data)
        # MoTeC advanced features tabs don't require telemetry updates by default
        # but can be added if needed
    
    def _on_tune_selected(self, tune_id: str) -> None:
        """Handle tune selection from database."""
        try:
            from services.tune_map_database import TuneMapDatabase
            from services.ecu_control import ECUControl
            
            tune_db = TuneMapDatabase()
            tune = tune_db.get_tune(tune_id)
            
            if not tune:
                QMessageBox.warning(self, "Error", f"Tune not found: {tune_id}")
                return
            
            # Get ECU control instance (would need to be passed or retrieved)
            # For now, show a message
            QMessageBox.information(
                self,
                "Tune Selected",
                f"Tune '{tune.name}' selected.\n\n"
                f"To apply this tune, ensure your ECU is connected and use the 'Load Tune' button.",
            )
        except Exception as e:
            LOGGER.error("Failed to handle tune selection: %s", e)
            QMessageBox.warning(self, "Error", f"Failed to load tune: {e}")


class FuelVETab(QWidget):
    """Fuel VE Table sub-tab within ECU tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.current_file_path: Optional[str] = None
        self.setup_ui()
        self._setup_shortcuts()
        
        # Initialize backup manager access (use global or create local)
        if BACKUP_AVAILABLE and BackupManager:
            try:
                # Try to get from parent/main container first
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'backup_manager') and parent.backup_manager:
                        self.backup_manager = parent.backup_manager
                        break
                    parent = parent.parent()
                
                # Fallback to creating new instance
                if not self.backup_manager:
                    self.backup_manager = BackupManager()
                
                self.backup_type = BackupType.ECU_CALIBRATION if BackupType else None
            except (ImportError, AttributeError, TypeError) as e:
                LOGGER.warning("Backup manager initialization failed: %s", e)
                self.backup_manager = None
                self.backup_type = None
            except Exception as e:
                LOGGER.error("Unexpected error initializing backup manager: %s", e)
                self.backup_manager = None
                self.backup_type = None
        else:
            self.backup_manager = None
            self.backup_type = None
        
    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for Fuel VE tab."""
        try:
            from ui.keyboard_shortcuts import register_shortcut
            
            # Register shortcuts
            if hasattr(self, 've_table'):
                register_shortcut("V", self.ve_table._toggle_2d3d, self, "Toggle 2D/3D View")
                register_shortcut("Ctrl+H", self.ve_table.interpolate_horizontal, self, "Horizontal Interpolation")
                register_shortcut("Ctrl+V", self.ve_table.interpolate_vertical, self, "Vertical Interpolation")
                register_shortcut("Ctrl+S", self.ve_table.smooth_table, self, "Table Smoothing")
                register_shortcut("A", self._local_autotune, self, "Local Autotune")
        except (ImportError, AttributeError) as e:
            LOGGER.debug("Keyboard shortcuts unavailable: %s", e)
            # Shortcuts are optional, continue without them
        except Exception as e:
            LOGGER.warning("Error setting up keyboard shortcuts: %s", e)
            # Continue without shortcuts
            
    def _local_autotune(self) -> None:
        """Local autotune action."""
        print("Local Autotune activated (Shortcut: A)")
    
    def _create_backup(self) -> None:
        """Create backup of current tuning file."""
        if not self.backup_manager:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Backup Unavailable", "Backup manager not available.")
            return
        
        # Get current file path (if saved)
        if not self.current_file_path:
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Tuning File",
                "",
                "Tuning Files (*.cal *.tune);;All Files (*.*)"
            )
            if not file_path:
                return
            self.current_file_path = file_path
        
        # Create backup
        backup = self.backup_manager.create_backup(
            self.current_file_path,
            self.backup_type or BackupType.ECU_CALIBRATION,
            description="Manual backup from Fuel VE tab",
            force=True
        )
        
        if backup:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Backup Created", f"Backup created successfully:\n{backup.backup_id}")
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Backup Failed", "Failed to create backup.")
    
    def _show_revert_dialog(self) -> None:
        """Show revert to backup dialog."""
        if not self.backup_manager or not self.current_file_path:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No File", "No file loaded. Please save or load a tuning file first.")
            return
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel
        
        backups = self.backup_manager.get_backups(self.current_file_path)
        if not backups:
            QMessageBox.information(self, "No Backups", "No backups found for this file.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Revert to Previous Backup")
        dialog.setMinimumSize(get_scaled_size(600), get_scaled_size(400))
        dialog.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("Select backup to revert to:")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        list_widget = QListWidget()
        list_widget.setStyleSheet("background-color: #0a0a0a; color: #ffffff; border: 1px solid #404040;")
        
        for backup in backups:
            import time
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(backup.timestamp))
            item_text = f"{timestamp_str} - {backup.description}"
            list_widget.addItem(item_text)
        
        layout.addWidget(list_widget)
        
        buttons_layout = QHBoxLayout()
        
        revert_btn = QPushButton("Revert")
        revert_btn.setStyleSheet("background-color: #ff8000; color: #ffffff; padding: 5px 15px;")
        revert_btn.clicked.connect(lambda: self._revert_selected_backup(backups[list_widget.currentRow()], dialog))
        buttons_layout.addWidget(revert_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 15px;")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.exec()
    
    def _revert_selected_backup(self, backup: BackupEntry, dialog) -> None:
        """Revert to selected backup."""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Confirm Revert",
            f"Revert to backup from {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup.timestamp))}?\n\n"
            "A backup of the current file will be created first.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.backup_manager.revert_to_backup(backup, create_backup=True)
            if success:
                QMessageBox.information(self, "Revert Successful", "File has been reverted. Please reload the file.")
                dialog.accept()
            else:
                QMessageBox.critical(self, "Revert Failed", "Failed to revert file.")
    
    def _backup_before_burn(self) -> None:
        """Create backup before burn operation."""
        if not self.backup_manager or not self.current_file_path:
            return
        
        if self.backup_manager.settings.backup_before_burn:
            self.backup_manager.create_backup(
                self.current_file_path,
                self.backup_type or BackupType.ECU_CALIBRATION,
                description="Pre-burn backup",
                force=True
            )
    
    def _backup_before_send(self) -> None:
        """Create backup before send operation."""
        if not self.backup_manager or not self.current_file_path:
            return
        
        if self.backup_manager.settings.backup_before_apply:
            self.backup_manager.create_backup(
                self.current_file_path,
                self.backup_type or BackupType.ECU_CALIBRATION,
                description="Pre-send backup",
                force=True
            )
        
    def setup_ui(self) -> None:
        """Setup Fuel VE tab layout."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Top control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges column
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: VE Table and graph
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Weighting and change visualization
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Enhanced graph panel (with Live Logger, Oscilloscope, Trigger Logger)
        from ui.telemetryiq_widgets import EnhancedGraphPanel
        self.enhanced_graph = EnhancedGraphPanel()
        main_layout.addWidget(self.enhanced_graph, stretch=1)
        
        # Statistics panel and System Status
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        stats_panel = StatisticsPanel()
        stats_layout.addWidget(stats_panel, stretch=2)
        
        # System Status & Utilities Panel
        from ui.telemetryiq_widgets import SystemStatusPanel
        self.system_status = SystemStatusPanel()
        stats_layout.addWidget(self.system_status, stretch=1)
        
        main_layout.addLayout(stats_layout, stretch=0)
        
    def _create_control_bar(self) -> QWidget:
        """Create top control bar - industrial realism styling with autoscaling."""
        bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        layout = QHBoxLayout(bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        # TelemetryIQ branding
        branding = QLabel("TelemetryIQ")
        branding_font = get_scaled_font_size(12)
        branding.setStyleSheet(f"font-size: {branding_font}px; font-weight: bold; color: #00e0ff;")
        layout.addWidget(branding)
        
        # Live Tuning status indicator
        self.live_tuning_label = QLabel("INSTANT SAVE")
        live_font = get_scaled_font_size(11)
        self.live_tuning_label.setStyleSheet(f"font-size: {live_font}px; font-weight: bold; color: #00ff00; padding: 2px 8px; background-color: #1a3a1a; border: {get_scaled_size(1)}px solid #00ff00;")
        layout.addWidget(self.live_tuning_label)
        
        # Superfast USB connection status
        usb_layout = QHBoxLayout()
        self.usb_led = QLabel()
        usb_led_size = get_scaled_size(10)
        self.usb_led.setFixedSize(usb_led_size, usb_led_size)
        usb_led_radius = get_scaled_size(5)
        self.usb_led.setStyleSheet(f"background-color: #00ff00; border-radius: {usb_led_radius}px; border: {get_scaled_size(1)}px solid #00ff00;")
        usb_layout.addWidget(self.usb_led)
        
        usb_label = QLabel("USB")
        usb_label_font = get_scaled_font_size(9)
        usb_label.setStyleSheet(f"font-size: {usb_label_font}px; color: #9aa0a6;")
        usb_layout.addWidget(usb_label)
        layout.addLayout(usb_layout)
        
        layout.addStretch()
        
        # Title
        title = QLabel("Fuel VE Table 1 Control Panel")
        title_font_size = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font_size}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # FPS indicator
        fps_label = QLabel("21.6 fps")
        fps_font_size = get_scaled_font_size(10)
        fps_label.setStyleSheet(f"font-size: {fps_font_size}px; color: #ffffff;")
        layout.addWidget(fps_label)
        
        # Buttons with scaled padding
        buttons = [
            "Update Controller",
            "Send",
            "Burn",
            "Local Autotune",
            "Stop Auto Tune",
        ]
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font_size = get_scaled_font_size(11)
        
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            if btn_text == "Local Autotune":
                btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font_size}px;")
                btn.setToolTip("Local Autotune (Shortcut: A)")
            else:
                btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font_size}px;")
            
            # Connect backup triggers
            if btn_text == "Burn":
                btn.clicked.connect(lambda: self._backup_before_burn())
            elif btn_text == "Send":
                btn.clicked.connect(lambda: self._backup_before_send())
            
            layout.addWidget(btn)
        
        # Backup and Revert buttons
        backup_btn = QPushButton("Backup")
        backup_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font_size}px;")
        backup_btn.setToolTip("Create backup of current tuning file")
        backup_btn.clicked.connect(self._create_backup)
        layout.addWidget(backup_btn)
        
        revert_btn = QPushButton("Revert")
        revert_btn.setStyleSheet(f"background-color: #ff8000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font_size}px;")
        revert_btn.setToolTip("Revert to previous backup")
        revert_btn.clicked.connect(self._show_revert_dialog)
        layout.addWidget(revert_btn)
            
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create left gauges column - industrial realism with enhanced diagnostics."""
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
        
        # Engine RPM gauge
        self.rpm_gauge = AnalogGauge(
            "Engine RPM",
            min_value=0,
            max_value=8000,
            unit="RPM",
            warning_start=7500,
            warning_end=8000,
            warning_color="#ffaa00",
        )
        layout.addWidget(self.rpm_gauge)
        
        # Engine MAP gauge
        self.map_gauge = AnalogGauge(
            "Engine MAP",
            min_value=-80,
            max_value=240,
            unit="kPa",
            warning_start=200,
            warning_end=240,
            warning_color="#ff0000",
        )
        layout.addWidget(self.map_gauge)
        
        # Air:Fuel Ratio gauge
        self.afr_gauge = AnalogGauge(
            "Air:Fuel Ratio",
            min_value=10,
            max_value=18,
            unit="",
            warning_start=17,
            warning_end=18,
            warning_color="#ff0000",
        )
        layout.addWidget(self.afr_gauge)
        
        # Flex Fuel digital readout with Blending Table (scaled)
        flex_group = QGroupBox("Flex Fuel")
        flex_group_font = get_scaled_font_size(11)
        flex_group_border = get_scaled_size(1)
        flex_group_radius = get_scaled_size(3)
        flex_group_margin = get_scaled_size(5)
        flex_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {flex_group_font}px; font-weight: bold; color: #ffffff;
                border: {flex_group_border}px solid #404040; border-radius: {flex_group_radius}px;
                margin-top: {flex_group_margin}px; padding-top: {flex_group_margin}px;
            }}
        """)
        flex_layout = QVBoxLayout()
        self.ethanol_label = QLabel("E85%: 72.4%")
        ethanol_font = get_scaled_font_size(14)
        ethanol_padding = get_scaled_size(5)
        self.ethanol_label.setStyleSheet(f"font-size: {ethanol_font}px; font-weight: bold; color: #00ff00; padding: {ethanol_padding}px;")
        flex_layout.addWidget(self.ethanol_label)
        
        # Blending Table button/link
        from PySide6.QtWidgets import QPushButton
        blend_btn = QPushButton("Blending Table")
        blend_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 4px 8px; font-size: 10px;")
        blend_btn.clicked.connect(self._show_blending_table)
        flex_layout.addWidget(blend_btn)
        
        flex_group.setLayout(flex_layout)
        layout.addWidget(flex_group)
        
        # Store reference for blending table dialog
        self.blending_table_dialog = None
        
        # EGT digital readout (scaled)
        egt_group = QGroupBox("Exhaust Gas Temperature")
        egt_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {flex_group_font}px; font-weight: bold; color: #ffffff;
                border: {flex_group_border}px solid #404040; border-radius: {flex_group_radius}px;
                margin-top: {flex_group_margin}px; padding-top: {flex_group_margin}px;
            }}
        """)
        egt_layout = QVBoxLayout()
        self.egt_label = QLabel("EGT Cyl 1: 850 °C")
        self.egt_label.setStyleSheet(f"font-size: {ethanol_font}px; font-weight: bold; color: #ff8000; padding: {ethanol_padding}px;")
        egt_layout.addWidget(self.egt_label)
        egt_group.setLayout(egt_layout)
        layout.addWidget(egt_group)
        
        # Status Light Panel (scaled)
        status_group = QGroupBox("Engine Protections Status")
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {flex_group_font}px; font-weight: bold; color: #ffffff;
                border: {flex_group_border}px solid #404040; border-radius: {flex_group_radius}px;
                margin-top: {flex_group_margin}px; padding-top: {flex_group_margin}px;
            }}
        """)
        status_layout = QVBoxLayout()
        status_layout.setSpacing(5)
        
        # Status lights (store both widget and LED for updates)
        self.lean_cut_light, self.lean_cut_led = self._create_status_light("LEAN CUT", "#ff0000", False)
        status_layout.addWidget(self.lean_cut_light)
        
        self.egt_cut_light, self.egt_cut_led = self._create_status_light("EGT CUT", "#ff0000", False)
        status_layout.addWidget(self.egt_cut_light)
        
        self.rev_limit_light, self.rev_limit_led = self._create_status_light("REV LIMIT", "#ffaa00", False)
        status_layout.addWidget(self.rev_limit_light)
        
        self.lim_speed_light, self.lim_speed_led = self._create_status_light("LIM-SPEED", "#00ff00", True)
        status_layout.addWidget(self.lim_speed_light)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        return panel
        
    def _show_blending_table(self) -> None:
        """Show Flex Fuel Blending Table dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
        from PySide6.QtGui import QBrush, QColor
        from PySide6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Flex Fuel Blending Table (Ethanol % vs Load)")
        dialog.setMinimumSize(get_scaled_size(600), get_scaled_size(400))
        dialog.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Blending Table: Base Map to E85 Map")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Blending table (Ethanol % vs Load)
        blend_table = QTableWidget()
        blend_table.setRowCount(10)  # Load rows
        blend_table.setColumnCount(11)  # Ethanol % columns
        blend_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        blend_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        blend_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Ethanol % headers (0-100%)
        ethanol_values = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for col, ethanol in enumerate(ethanol_values):
            item = QTableWidgetItem(f"{ethanol}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            blend_table.setHorizontalHeaderItem(col, item)
        
        # Load headers
        load_values = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        for row, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            blend_table.setVerticalHeaderItem(row, item)
        
        # Fill with blend percentages (0-100% blend from base to E85)
        for row in range(10):
            for col in range(11):
                # Blend percentage = ethanol percentage
                blend_pct = ethanol_values[col]
                item = QTableWidgetItem(f"{blend_pct}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                # Color code: green (base), blue (mid), orange (E85)
                if blend_pct < 30:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Base map
                elif blend_pct < 70:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Mid blend
                else:
                    item.setBackground(QBrush(QColor("#ff8000")))  # E85 map
                
                blend_table.setItem(row, col, item)
        
        layout.addWidget(blend_table)
        
        # Close button
        from PySide6.QtWidgets import QPushButton
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 15px;")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        self.blending_table_dialog = dialog
        dialog.exec()
        
    def _create_status_light(self, label: str, color: str, active: bool) -> tuple[QWidget, QLabel]:
        """Create a status light indicator. Returns (widget, led_label) for easy updates."""
        widget = QWidget()
        border = get_scaled_size(1)
        padding = get_scaled_size(3)
        widget.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040; padding: {padding}px;")
        layout = QHBoxLayout(widget)
        margin_h = get_scaled_size(5)
        margin_v = get_scaled_size(3)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        # LED indicator (scaled)
        led = QLabel()
        led_size = get_scaled_size(12)
        led.setFixedSize(led_size, led_size)
        led_radius = get_scaled_size(6)
        led.setStyleSheet(f"background-color: {'#00ff00' if active else '#404040'}; border-radius: {led_radius}px; border: {border}px solid {color};")
        layout.addWidget(led)
        
        # Label (scaled)
        label_widget = QLabel(label)
        label_font = get_scaled_font_size(10)
        label_widget.setStyleSheet(f"font-size: {label_font}px; color: #ffffff;")
        layout.addWidget(label_widget)
        
        layout.addStretch()
        return widget, led
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with VE table - industrial realism."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Flexible axis selection
        axis_layout = QHBoxLayout()
        axis_layout.addWidget(QLabel("X-Axis:"))
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.addItems(["RPM", "Speed", "Load", "MAP", "TPS"])
        self.x_axis_combo.setCurrentIndex(0)
        self.x_axis_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 4px;")
        axis_layout.addWidget(self.x_axis_combo)
        
        axis_layout.addWidget(QLabel("Y-Axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.addItems(["MAP", "Load", "TPS", "RPM", "Speed"])
        self.y_axis_combo.setCurrentIndex(0)
        self.y_axis_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 4px;")
        axis_layout.addWidget(self.y_axis_combo)
        axis_layout.addStretch()
        layout.addLayout(axis_layout)
        
        # VE Table
        self.ve_table = VETableWidget()
        layout.addWidget(self.ve_table, stretch=1)
        
        # Connect interpolation and smoothing buttons
        if hasattr(self.ve_table, 'interp_h_btn'):
            self.ve_table.interp_h_btn.clicked.connect(self.ve_table.interpolate_horizontal)
        if hasattr(self.ve_table, 'interp_v_btn'):
            self.ve_table.interp_v_btn.clicked.connect(self.ve_table.interpolate_vertical)
        if hasattr(self.ve_table, 'smooth_btn'):
            self.ve_table.smooth_btn.clicked.connect(self.ve_table.smooth_table)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel with weighting and change visualization - industrial realism."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Cell Weighting
        self.weighting_widget = CellWeightingWidget("Cell Weighting")
        layout.addWidget(self.weighting_widget)
        
        # Cell Change
        self.change_widget = CellWeightingWidget("Cell Change")
        layout.addWidget(self.change_widget)
        
        layout.addStretch()
        return panel
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update all widgets with telemetry data."""
        # Update gauges
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = data.get("Boost_Pressure", data.get("boost_psi", 0)) * 6.895  # Convert psi to kPa
        if map_val < 0:
            map_val = 100 - abs(map_val)  # Convert to MAP
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 14.7)
        
        self.rpm_gauge.set_value(rpm)
        self.map_gauge.set_value(map_val)
        self.afr_gauge.set_value(afr)
        
        # Update VE table (simulate VE from MAP and RPM)
        ve_value = 50 + (rpm / 8000) * 50 + (map_val / 240) * 30
        self.ve_table.update_from_telemetry(rpm, map_val, ve_value)
        
        # Update enhanced graph panel
        lambda_val = data.get("lambda_value", afr / 14.7)
        boost_aim = data.get("Boost_Pressure", data.get("boost_psi", 0))
        ego = data.get("Throttle_Position", data.get("throttle", 0)) * 10  # Simulate ego correction
        self.enhanced_graph.update_live_logger(lambda_val, boost_aim, ego)
        
        # Update Flex Fuel
        ethanol = data.get("e85_percent", data.get("FlexFuelPercent", 72.4))
        self.ethanol_label.setText(f"E85%: {ethanol:.1f}%")
        
        # Update EGT
        egt = data.get("EGT", data.get("ExhaustTemp", 850))
        self.egt_label.setText(f"EGT Cyl 1: {egt:.0f} °C")
        
        # Update status lights
        if lambda_val > 1.2:
            self.lean_cut_led.setStyleSheet("background-color: #ff0000; border-radius: 6px; border: 1px solid #ff0000;")
        else:
            self.lean_cut_led.setStyleSheet("background-color: #404040; border-radius: 6px; border: 1px solid #ff0000;")
            
        if egt > 950:
            self.egt_cut_led.setStyleSheet("background-color: #ff0000; border-radius: 6px; border: 1px solid #ff0000;")
        else:
            self.egt_cut_led.setStyleSheet("background-color: #404040; border-radius: 6px; border: 1px solid #ff0000;")
            
        if rpm > 7500:
            self.rev_limit_led.setStyleSheet("background-color: #ffaa00; border-radius: 6px; border: 1px solid #ffaa00;")
        else:
            self.rev_limit_led.setStyleSheet("background-color: #404040; border-radius: 6px; border: 1px solid #ffaa00;")


class ModuleTab(QWidget):
    """Base class for module tabs with full ECU tuning interface layout."""
    
    def __init__(self, module_name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.module_name = module_name
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup module tab UI with full ECU tuning layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges column
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Main data table/visualization
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings and visualization
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Real-time graph
        self.realtime_graph = RealTimeGraph()
        main_layout.addWidget(self.realtime_graph, stretch=1)
        
    def _create_control_bar(self) -> QWidget:
        """Create top control bar."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # FPS indicator
        fps_label = QLabel("21.6 fps")
        fps_label.setStyleSheet("font-size: 10px; color: #ffffff;")
        layout.addWidget(fps_label)
        
        layout.addStretch()
        
        # Title
        title = QLabel(f"{self.module_name} Control Panel")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Buttons
        buttons = ["Update Controller", "Send", "Burn", "Active", "Stop"]
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            if btn_text == "Active":
                btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 5px 10px;")
            else:
                btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 5px 10px;")
            layout.addWidget(btn)
            
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create left gauges column - override in subclasses."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        layout.addStretch()
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel - override in subclasses."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Default: Settings grid
        settings_grid = QGridLayout()
        settings_grid.setSpacing(10)
        self._add_settings(settings_grid)
        layout.addLayout(settings_grid)
        layout.addStretch()
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel with settings and visualization."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        settings_layout = QVBoxLayout()
        self._add_right_settings(settings_layout)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Visualization
        self.visualization = CellWeightingWidget(f"{self.module_name} Status")
        layout.addWidget(self.visualization)
        
        layout.addStretch()
        return panel
        
    def _add_settings(self, grid: QGridLayout) -> None:
        """Override in subclasses to add module-specific settings."""
        pass
        
    def _add_right_settings(self, layout: QVBoxLayout) -> None:
        """Override in subclasses to add right panel settings."""
        pass
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update module with telemetry data."""
        pass


class NitrousTab(ModuleTab):
    """Nitrous system settings tab with full ECU tuning interface."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # Initialize stage_configs BEFORE calling super().__init__()
        # because setup_ui() will be called which needs this attribute
        # Multi-stage defaults
        self.stage_configs: List[NitrousStageConfig] = [
            NitrousStageConfig(
                name="Stage 1",
                shot_size_hp=100,
                start_trigger="RPM",
                start_value=3200,
                end_trigger="Time",
                end_value=2.0,
                ramp_in_time=1.0,
                ramp_out_time=0.8,
                frequency_hz=18,
                resume_behavior="Resume",
            ),
            NitrousStageConfig(
                name="Stage 2",
                shot_size_hp=200,
                start_trigger="Boost",
                start_value=5.0,
                end_trigger="Boost",
                end_value=18.0,
                ramp_in_time=0.6,
                ramp_out_time=1.2,
                frequency_hz=22,
                resume_behavior="Restart",
            ),
            NitrousStageConfig(
                name="Stage 3",
                enabled=False,
                shot_size_hp=50,
                start_trigger="TPS",
                start_value=85.0,
                end_trigger="Speed",
                end_value=130.0,
                ramp_in_time=1.2,
                ramp_out_time=1.5,
                frequency_hz=15,
                resume_behavior="Auto",
            ),
        ]
        self.stage_status_labels: List[QLabel] = []
        self._log_history: deque[NitrousRunLog] = deque(maxlen=120)
        self._run_active: bool = False
        self._run_start_time: float = 0.0
        self._run_start_rpm: float = 0.0
        
        # Now call super().__init__() after all attributes are initialized
        super().__init__("Nitrous", parent)
        self._current_run_samples: List[dict[str, float]] = []
        self._run_counter: int = 0
        self._last_run_end: float = 0.0
        self._resume_state: str = "Idle"
        self.touchscreen_dialog: Optional["TouchscreenNitrousDialog"] = None
    
    def setup_ui(self) -> None:
        """Override setup_ui to add comprehensive graphs panel."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges column
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Main data table/visualization
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings and visualization
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Comprehensive graphs panel
        graphs_panel = self._create_graphs_panel()
        main_layout.addWidget(graphs_panel, stretch=1)
        
        # Import/Export bar
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
    
    def _create_control_bar(self) -> QWidget:
        """Expanded control bar with nitrous-specific utilities."""
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 6px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Status + FPS
        self.fps_label = QLabel("Nitrous Controller • 21.6 fps")
        self.fps_label.setStyleSheet("font-size: 10px; color: #9aa0a6;")
        layout.addWidget(self.fps_label)
        
        self.resume_indicator = QLabel("Ramp Mode: Idle")
        self.resume_indicator.setStyleSheet("font-size: 11px; color: #00ffcc; font-weight: bold;")
        layout.addWidget(self.resume_indicator)
        
        layout.addStretch()
        
        title = QLabel("Progressive Nitrous Control Hub")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Control buttons
        self.touchscreen_btn = QPushButton("Touchscreen Mode")
        self.touchscreen_btn.setStyleSheet("background-color: #0066cc; color: #ffffff; padding: 6px 12px;")
        self.touchscreen_btn.clicked.connect(self._open_touchscreen_mode)
        layout.addWidget(self.touchscreen_btn)
        
        self.resume_ramp_btn = QPushButton("Resume Ramp")
        self.resume_ramp_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        self.resume_ramp_btn.clicked.connect(self._force_resume_ramp)
        layout.addWidget(self.resume_ramp_btn)
        
        self.restart_ramp_btn = QPushButton("Restart Ramp")
        self.restart_ramp_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        self.restart_ramp_btn.clicked.connect(self._force_restart_ramp)
        layout.addWidget(self.restart_ramp_btn)
        
        self.export_logs_btn = QPushButton("Export Logs")
        self.export_logs_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        self.export_logs_btn.clicked.connect(self._export_nitrous_logs)
        layout.addWidget(self.export_logs_btn)
        
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create nitrous-specific gauges."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Bottle Pressure gauge
        self.pressure_gauge = AnalogGauge(
            "Bottle Pressure",
            min_value=0,
            max_value=2000,
            unit="psi",
            warning_start=1800,
            warning_end=2000,
            warning_color="#ff0000",
        )
        layout.addWidget(self.pressure_gauge)
        
        # Flow Rate gauge
        self.flow_gauge = AnalogGauge(
            "Flow Rate",
            min_value=0,
            max_value=1000,
            unit="lb/hr",
        )
        layout.addWidget(self.flow_gauge)
        
        # Activation Status gauge
        self.status_gauge = AnalogGauge(
            "System Status",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.status_gauge)
        
        # Fuel Pressure gauge
        self.fuel_pressure_gauge = AnalogGauge(
            "Fuel Pressure",
            min_value=0,
            max_value=100,
            unit="psi",
            warning_start=0,
            warning_end=40,
            warning_color="#ff0000",
        )
        layout.addWidget(self.fuel_pressure_gauge)
        
        # AFR gauge
        self.afr_gauge = AnalogGauge(
            "AFR",
            min_value=10,
            max_value=18,
            unit="",
        )
        layout.addWidget(self.afr_gauge)
        
        # Solenoid Duty gauge
        self.solenoid_duty_gauge = AnalogGauge(
            "Solenoid Duty",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.solenoid_duty_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with tabbed nitrous maps."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabbed interface for different maps
        self.center_tabs = QTabWidget()
        self.center_tabs.setStyleSheet("""
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
        
        # Activation Map
        self.center_tabs.addTab(self._create_activation_map(), "Activation Map")
        
        # Fuel Offset Map
        self.center_tabs.addTab(self._create_fuel_offset_map(), "Fuel Offset")
        
        # Timing Retard Map
        self.center_tabs.addTab(self._create_timing_retard_map(), "Timing Retard")
        
        # Progressive Control Map
        self.center_tabs.addTab(self._create_progressive_map(), "Progressive Control")
        
        # Multi-stage configuration
        self.center_tabs.addTab(self._create_multistage_panel(), "Multi-Stage Control")
        
        # TelemetryIQ Pro Series Controller
        self.center_tabs.addTab(self._create_telemetryiq_panel(), "TelemetryIQ Pro Controller")
        
        layout.addWidget(self.center_tabs)
        return panel

    def _create_multistage_panel(self) -> QWidget:
        """Create multi-stage controller panel."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title = QLabel("Multi-Stage Progressive Controller")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        desc = QLabel("Control up to three stages with independent triggers, ramps, and safety windows.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        layout.addWidget(desc)
        
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
        self.stage_table = QTableWidget()
        # Ensure stage_configs exists (should be initialized in __init__, but check for safety)
        if not hasattr(self, 'stage_configs') or not self.stage_configs:
            self.stage_configs = []
        self.stage_table.setRowCount(len(self.stage_configs))
        self.stage_table.setColumnCount(10)
        self.stage_table.setHorizontalHeaderLabels([
            "Stage",
            "Enabled",
            "Shot (HP)",
            "Start Trigger",
            "Start Value",
            "End Trigger",
            "End Value",
            "Ramp In (s)",
            "Ramp Out (s)",
            "Freq (Hz)",
        ])
        self.stage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stage_table.verticalHeader().setVisible(False)
        self.stage_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        
        for row, cfg in enumerate(self.stage_configs):
            values = [
                cfg.name,
                "Enabled" if cfg.enabled else "Disabled",
                f"{cfg.shot_size_hp}",
                cfg.start_trigger,
                f"{cfg.start_value}",
                cfg.end_trigger,
                f"{cfg.end_value}",
                f"{cfg.ramp_in_time:.2f}",
                f"{cfg.ramp_out_time:.2f}",
                f"{cfg.frequency_hz}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 1:
                    color = "#00ff00" if cfg.enabled else "#ff4d4d"
                    item.setBackground(QBrush(QColor(color)))
                self.stage_table.setItem(row, col, item)
        
        layout.addWidget(self.stage_table)
        
        # Stage status indicators
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        self.stage_status_labels.clear()
        for cfg in self.stage_configs:
            lbl = QLabel(f"{cfg.name}: Idle")
            lbl.setStyleSheet("color: #ffaa00; font-weight: bold; border: 1px solid #404040; padding: 4px;")
            status_row.addWidget(lbl)
            self.stage_status_labels.append(lbl)
        status_row.addStretch()
        layout.addLayout(status_row)
        
        return tab
    
    def _create_telemetryiq_panel(self) -> QWidget:
        """Create TelemetryIQ Pro Series Controller panel."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Initialize TelemetryIQ controller
        try:
            from services.telemetryiq_nitrous_controller import (
                TelemetryIQNitrousController,
                StageMode,
                TimerBehavior,
            )
            if not hasattr(self, 'telemetryiq_controller'):
                self.telemetryiq_controller = TelemetryIQNitrousController(
                    num_stages=3,
                    num_timers=5,
                    enable_relay_controller=True,
                )
                self.telemetryiq_controller.start_monitoring()
                # Register status callback
                self.telemetryiq_controller.register_status_callback(self._on_telemetryiq_status_update)
        except Exception as e:
            LOGGER.error("Failed to initialize TelemetryIQ controller: %s", e)
            self.telemetryiq_controller = None
        
        # Title
        title = QLabel("TelemetryIQ Pro Series Nitrous Controller")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00d4ff;")
        layout.addWidget(title)
        
        desc = QLabel(
            "Complete 6-stage pro series nitrous system with 8 relay controller. "
            "Configurable 2-6 stages and 2-10 timers. Programmable on-device without laptop."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        layout.addWidget(desc)
        
        # Configuration section
        config_group = QGroupBox("System Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        config_layout = QGridLayout()
        
        # Number of stages (2-6)
        config_layout.addWidget(QLabel("Number of Stages:"), 0, 0)
        self.num_stages_spin = QSpinBox()
        self.num_stages_spin.setMinimum(2)
        self.num_stages_spin.setMaximum(6)
        self.num_stages_spin.setValue(3)
        self.num_stages_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.num_stages_spin.valueChanged.connect(self._update_stage_count)
        config_layout.addWidget(self.num_stages_spin, 0, 1)
        
        # Number of timers (2-10)
        config_layout.addWidget(QLabel("Number of Timers:"), 0, 2)
        self.num_timers_spin = QSpinBox()
        self.num_timers_spin.setMinimum(2)
        self.num_timers_spin.setMaximum(10)
        self.num_timers_spin.setValue(5)
        self.num_timers_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.num_timers_spin.valueChanged.connect(self._update_timer_count)
        config_layout.addWidget(self.num_timers_spin, 0, 3)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Stages configuration
        stages_group = QGroupBox("Stage Configuration")
        stages_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        stages_layout = QVBoxLayout()
        
        self.telemetryiq_stage_table = QTableWidget()
        self.telemetryiq_stage_table.setColumnCount(9)
        self.telemetryiq_stage_table.setHorizontalHeaderLabels([
            "Stage",
            "Enabled",
            "Mode",
            "Timer (s)",
            "Start Trigger",
            "Timer Behavior",
            "Hold on Pedal",
            "Relay",
            "Status",
        ])
        self.telemetryiq_stage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.telemetryiq_stage_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        stages_layout.addWidget(self.telemetryiq_stage_table)
        stages_group.setLayout(stages_layout)
        layout.addWidget(stages_group)
        
        # Timers configuration
        timers_group = QGroupBox("Timer Configuration")
        timers_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        timers_layout = QVBoxLayout()
        
        self.telemetryiq_timer_table = QTableWidget()
        self.telemetryiq_timer_table.setColumnCount(5)
        self.telemetryiq_timer_table.setHorizontalHeaderLabels([
            "Timer",
            "Enabled",
            "Duration (s)",
            "Start Trigger",
            "Shifter Gear",
        ])
        self.telemetryiq_timer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.telemetryiq_timer_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        timers_layout.addWidget(self.telemetryiq_timer_table)
        timers_group.setLayout(timers_layout)
        layout.addWidget(timers_group)
        
        # Relay status and purge controls
        relay_purge_layout = QHBoxLayout()
        
        # Relay status
        relay_group = QGroupBox("8-Relay Controller Status")
        relay_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        relay_layout = QVBoxLayout()
        
        self.relay_status_table = QTableWidget()
        self.relay_status_table.setColumnCount(4)
        self.relay_status_table.setHorizontalHeaderLabels([
            "Relay",
            "Status",
            "Fuse",
            "Current (A)",
        ])
        self.relay_status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.relay_status_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        relay_layout.addWidget(self.relay_status_table)
        relay_group.setLayout(relay_layout)
        relay_purge_layout.addWidget(relay_group, stretch=2)
        
        # Purge controls
        purge_group = QGroupBox("Line Purge Controls")
        purge_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        purge_layout = QVBoxLayout()
        
        self.purge_buttons = []
        purge_names = ["Motor Purge", "Line Purge 1", "Line Purge 2"]
        for i, name in enumerate(purge_names):
            purge_btn = QPushButton(f"Activate {name}")
            purge_btn.setStyleSheet("background-color: #0066cc; color: #ffffff; padding: 6px;")
            purge_btn.clicked.connect(lambda checked, pid=i+1: self._activate_purge(pid))
            purge_layout.addWidget(purge_btn)
            self.purge_buttons.append(purge_btn)
        
        purge_layout.addStretch()
        purge_group.setLayout(purge_layout)
        relay_purge_layout.addWidget(purge_group, stretch=1)
        
        layout.addLayout(relay_purge_layout)
        
        # Input status
        input_group = QGroupBox("Input Status")
        input_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        input_layout = QHBoxLayout()
        
        self.trans_brake_led = QLabel("Trans Brake: OFF")
        self.trans_brake_led.setStyleSheet("color: #ff0000; font-weight: bold; padding: 4px; border: 1px solid #404040;")
        input_layout.addWidget(self.trans_brake_led)
        
        self.clutch_led = QLabel("Clutch: OFF")
        self.clutch_led.setStyleSheet("color: #ff0000; font-weight: bold; padding: 4px; border: 1px solid #404040;")
        input_layout.addWidget(self.clutch_led)
        
        self.shifter_led = QLabel("Shifter: N/A")
        self.shifter_led.setStyleSheet("color: #ffaa00; font-weight: bold; padding: 4px; border: 1px solid #404040;")
        input_layout.addWidget(self.shifter_led)
        
        self.staging_interrupt_led = QLabel("Staging Interrupt: ACTIVE")
        self.staging_interrupt_led.setStyleSheet("color: #00ff00; font-weight: bold; padding: 4px; border: 1px solid #404040;")
        input_layout.addWidget(self.staging_interrupt_led)
        
        input_layout.addStretch()
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Update tables
        self._update_telemetryiq_tables()
        
        layout.addStretch()
        return tab
    
    def _update_stage_count(self, count: int) -> None:
        """Update number of stages."""
        if self.telemetryiq_controller:
            # Would need to recreate controller with new stage count
            LOGGER.info("Stage count changed to %d", count)
            self._update_telemetryiq_tables()
    
    def _update_timer_count(self, count: int) -> None:
        """Update number of timers."""
        if self.telemetryiq_controller:
            # Would need to recreate controller with new timer count
            LOGGER.info("Timer count changed to %d", count)
            self._update_telemetryiq_tables()
    
    def _update_telemetryiq_tables(self) -> None:
        """Update TelemetryIQ configuration tables."""
        if not self.telemetryiq_controller:
            return
        
        # Update stage table
        stages = self.telemetryiq_controller.stages
        self.telemetryiq_stage_table.setRowCount(len(stages))
        
        for row, stage in enumerate(stages):
            self.telemetryiq_stage_table.setItem(row, 0, QTableWidgetItem(f"Stage {stage.stage_number}"))
            
            enabled_item = QTableWidgetItem("Enabled" if stage.enabled else "Disabled")
            enabled_item.setBackground(QBrush(QColor("#00ff00" if stage.enabled else "#ff4d4d")))
            self.telemetryiq_stage_table.setItem(row, 1, enabled_item)
            
            self.telemetryiq_stage_table.setItem(row, 2, QTableWidgetItem(stage.mode.value))
            self.telemetryiq_stage_table.setItem(row, 3, QTableWidgetItem(
                f"{stage.activation_time:.2f}" if stage.activation_time else "N/A"
            ))
            self.telemetryiq_stage_table.setItem(row, 4, QTableWidgetItem(stage.start_trigger))
            self.telemetryiq_stage_table.setItem(row, 5, QTableWidgetItem(stage.timer_behavior.value))
            self.telemetryiq_stage_table.setItem(row, 6, QTableWidgetItem("Yes" if stage.hold_on_pedal else "No"))
            self.telemetryiq_stage_table.setItem(row, 7, QTableWidgetItem(f"Relay {stage.relay_channel + 1}"))
            
            status = "ACTIVE" if stage.stage_number in self.telemetryiq_controller.active_stages else "IDLE"
            status_item = QTableWidgetItem(status)
            status_item.setBackground(QBrush(QColor("#00ff00" if status == "ACTIVE" else "#404040")))
            self.telemetryiq_stage_table.setItem(row, 8, status_item)
        
        # Update timer table
        timers = self.telemetryiq_controller.timers
        self.telemetryiq_timer_table.setRowCount(len(timers))
        
        for row, timer in enumerate(timers):
            self.telemetryiq_timer_table.setItem(row, 0, QTableWidgetItem(f"Timer {timer.timer_id}"))
            
            enabled_item = QTableWidgetItem("Enabled" if timer.enabled else "Disabled")
            enabled_item.setBackground(QBrush(QColor("#00ff00" if timer.enabled else "#ff4d4d")))
            self.telemetryiq_timer_table.setItem(row, 1, enabled_item)
            
            self.telemetryiq_timer_table.setItem(row, 2, QTableWidgetItem(f"{timer.duration_seconds:.2f}"))
            self.telemetryiq_timer_table.setItem(row, 3, QTableWidgetItem(timer.start_trigger))
            self.telemetryiq_timer_table.setItem(row, 4, QTableWidgetItem(
                str(timer.shifter_gear) if timer.shifter_gear else "Any"
            ))
        
        # Update relay status table
        relays = self.telemetryiq_controller.relays
        self.relay_status_table.setRowCount(len(relays))
        
        for row, relay in enumerate(relays):
            self.relay_status_table.setItem(row, 0, QTableWidgetItem(f"Relay {relay.relay_id}"))
            
            status_item = QTableWidgetItem(relay.status.value.upper())
            if relay.status.value == "ok":
                status_item.setBackground(QBrush(QColor("#00ff00")))
            elif relay.status.value == "blown_fuse":
                status_item.setBackground(QBrush(QColor("#ff0000")))
            else:
                status_item.setBackground(QBrush(QColor("#ffaa00")))
            self.relay_status_table.setItem(row, 1, status_item)
            
            fuse_item = QTableWidgetItem(relay.fuse_status.value.upper())
            if relay.fuse_status.value == "ok":
                fuse_item.setBackground(QBrush(QColor("#00ff00")))
            elif relay.fuse_status.value == "blown_fuse":
                fuse_item.setBackground(QBrush(QColor("#ff0000")))
            else:
                fuse_item.setBackground(QBrush(QColor("#ffaa00")))
            self.relay_status_table.setItem(row, 2, fuse_item)
            
            self.relay_status_table.setItem(row, 3, QTableWidgetItem(f"{relay.current_amp:.1f}"))
    
    def _on_telemetryiq_status_update(self, status: Dict[str, Any]) -> None:
        """Handle TelemetryIQ status update."""
        # Update tables on status change
        if hasattr(self, 'telemetryiq_stage_table'):
            self._update_telemetryiq_tables()
    
    def _activate_purge(self, purge_id: int) -> None:
        """Activate line purge."""
        if self.telemetryiq_controller:
            self.telemetryiq_controller.activate_purge(purge_id)
            # Auto-deactivate after duration
            if purge_id <= len(self.telemetryiq_controller.purges):
                purge = self.telemetryiq_controller.purges[purge_id - 1]
                if purge.duration_seconds > 0:
                    # Schedule deactivation
                    QTimer.singleShot(int(purge.duration_seconds * 1000), 
                                    lambda: self.telemetryiq_controller.deactivate_purge(purge_id))
    
    def _create_activation_map(self) -> QWidget:
        """Create nitrous activation map."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Nitrous Activation Map (vs RPM & TPS)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        self.table = QTableWidget()
        self.table.setRowCount(8)
        self.table.setColumnCount(10)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet("""
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
        
        # Initialize table
        rpm_values = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)
            
        throttle_values = [50, 60, 70, 75, 80, 85, 90, 100]
        for row, throttle in enumerate(throttle_values):
            item = QTableWidgetItem(f"{throttle}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setVerticalHeaderItem(row, item)
            
        # Fill with activation status (ON/OFF or duty %)
        for row in range(8):
            for col in range(10):
                # Only activate at WOT (75%+) and above activation RPM
                if throttle_values[row] >= 75 and rpm_values[col] >= 3000:
                    duty = min(100, (throttle_values[row] - 75) * 4 + (rpm_values[col] - 3000) / 40)
                    item = QTableWidgetItem(f"{duty:.0f}%")
                    item.setBackground(QBrush(QColor("#00ff00")))
                else:
                    item = QTableWidgetItem("OFF")
                    item.setBackground(QBrush(QColor("#2a2a2a")))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                self.table.setItem(row, col, item)
        
        layout.addWidget(self.table)
        return tab
    
    def _create_fuel_offset_map(self) -> QWidget:
        """Create fuel offset map for nitrous operation."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Fuel Offset Map (Additional Fuel % vs RPM & Nitrous Shot Size)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)  # RPM
        table.setColumnCount(6)  # Shot sizes (50, 75, 100, 125, 150, 200 HP)
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
        
        shot_sizes = [50, 75, 100, 125, 150, 200]
        for col, shot in enumerate(shot_sizes):
            item = QTableWidgetItem(f"{shot}HP")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with fuel offset percentages (more fuel for larger shots)
        for row in range(8):
            for col in range(6):
                fuel_add = (shot_sizes[col] / 50) * 5 + (rpm_values[row] / 7000) * 3  # Base + RPM factor
                fuel_add = max(0, min(50, fuel_add))
                item = QTableWidgetItem(f"+{fuel_add:.1f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if fuel_add > 30:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very rich
                elif fuel_add > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Rich
                elif fuel_add > 10:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Lean
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_timing_retard_map(self) -> QWidget:
        """Create ignition timing retard map for nitrous operation."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Retard Map (Degrees Retard vs RPM & Nitrous Shot Size)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)  # RPM
        table.setColumnCount(6)  # Shot sizes
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
        
        shot_sizes = [50, 75, 100, 125, 150, 200]
        for col, shot in enumerate(shot_sizes):
            item = QTableWidgetItem(f"{shot}HP")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with timing retard values (2 degrees per 50 HP shot, more at higher RPM)
        for row in range(8):
            for col in range(6):
                base_retard = (shot_sizes[col] / 50) * 2.0  # 2 degrees per 50 HP
                rpm_factor = (rpm_values[row] / 7000) * 2.0  # Additional retard at high RPM
                retard = base_retard + rpm_factor
                retard = max(0, min(12, retard))  # Range: 0-12 degrees
                
                item = QTableWidgetItem(f"-{retard:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if retard > 8:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very retarded
                elif retard > 5:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Retarded
                elif retard > 3:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Minimal
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_progressive_map(self) -> QWidget:
        """Create progressive control map."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Progressive Control Map (Duty Cycle % vs Time/RPM/Speed)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # Time/RPM/Speed progression
        table.setColumnCount(8)  # Progression steps
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
        
        progression_steps = [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        for col, step in enumerate(progression_steps):
            item = QTableWidgetItem(f"{step:.2f}s")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        # Different progression bases
        bases = ["Time (s)", "RPM", "Speed (MPH)", "Boost (psi)", "Time (s)", "RPM", "Speed (MPH)", "Boost (psi)", "Time (s)", "RPM"]
        for row, base in enumerate(bases):
            item = QTableWidgetItem(base)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with progressive duty cycle values (ramp from start% to 100%)
        for row in range(10):
            for col in range(8):
                # Progressive ramp: start at initial%, ramp to 100%
                progress = progression_steps[col] / 2.0  # Normalize to 0-1
                progress = min(1.0, progress)
                duty = 20 + (progress * 80)  # Ramp from 20% to 100%
                duty = max(0, min(100, duty))
                
                item = QTableWidgetItem(f"{duty:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if duty > 80:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Full power
                elif duty > 50:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Ramping
                else:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Starting
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
        
    def _add_right_settings(self, layout: QVBoxLayout) -> None:
        """Add right panel settings."""
        from PySide6.QtWidgets import QGroupBox
        
        # Master Arming Switch
        arming_group = QGroupBox("Master Arming Switch")
        arming_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        arming_layout = QVBoxLayout()
        
        self.master_arm = QCheckBox("Master Arming Switch (Digital Input)")
        self.master_arm.setStyleSheet("color: #ffffff;")
        arming_layout.addWidget(self.master_arm)
        
        self.enabled_check = QCheckBox("Nitrous Enabled")
        self.enabled_check.setStyleSheet("color: #ffffff;")
        arming_layout.addWidget(self.enabled_check)
        
        arming_group.setLayout(arming_layout)
        layout.addWidget(arming_group)
        
        # Activation Conditions
        activation_group = QGroupBox("Activation Conditions")
        activation_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        activation_layout = QVBoxLayout()
        
        activation_layout.addWidget(QLabel("Min RPM (Enable):"))
        self.min_rpm = QSpinBox()
        self.min_rpm.setRange(0, 10000)
        self.min_rpm.setValue(3000)
        self.min_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        activation_layout.addWidget(self.min_rpm)
        
        activation_layout.addWidget(QLabel("Max RPM (Disable):"))
        self.max_rpm = QSpinBox()
        self.max_rpm.setRange(0, 10000)
        self.max_rpm.setValue(7500)
        self.max_rpm.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        activation_layout.addWidget(self.max_rpm)
        
        activation_layout.addWidget(QLabel("RPM Window (Min/Max):"))
        rpm_window_row = QHBoxLayout()
        self.window_rpm_low = QSpinBox()
        self.window_rpm_low.setRange(0, 10000)
        self.window_rpm_low.setValue(3200)
        self.window_rpm_low.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rpm_window_row.addWidget(self.window_rpm_low)
        self.window_rpm_high = QSpinBox()
        self.window_rpm_high.setRange(0, 10000)
        self.window_rpm_high.setValue(7200)
        self.window_rpm_high.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rpm_window_row.addWidget(self.window_rpm_high)
        activation_layout.addLayout(rpm_window_row)
        
        activation_layout.addWidget(QLabel("Min Throttle Position (%):"))
        self.min_tps = QDoubleSpinBox()
        self.min_tps.setRange(0, 100)
        self.min_tps.setValue(75.0)
        self.min_tps.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        activation_layout.addWidget(self.min_tps)
        
        activation_layout.addWidget(QLabel("Min Speed (MPH):"))
        self.min_speed = QDoubleSpinBox()
        self.min_speed.setRange(0, 300)
        self.min_speed.setValue(30.0)
        self.min_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        activation_layout.addWidget(self.min_speed)
        
        activation_layout.addWidget(QLabel("Max Speed (MPH):"))
        self.max_speed = QDoubleSpinBox()
        self.max_speed.setRange(0, 400)
        self.max_speed.setValue(180.0)
        self.max_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        activation_layout.addWidget(self.max_speed)
        
        activation_layout.addWidget(QLabel("Gear Lockout:"))
        self.gear_lockout = QComboBox()
        self.gear_lockout.addItems(["None", "1st Gear Only", "1st & 2nd Gear", "Custom"])
        self.gear_lockout.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        activation_layout.addWidget(self.gear_lockout)
        
        self.window_switch = QCheckBox("Enable RPM/MPH Window Switch")
        self.window_switch.setChecked(True)
        self.window_switch.setStyleSheet("color: #ffffff;")
        activation_layout.addWidget(self.window_switch)
        
        activation_group.setLayout(activation_layout)
        layout.addWidget(activation_group)
        
        # Progressive Control
        progressive_group = QGroupBox("Progressive Control")
        progressive_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        progressive_layout = QVBoxLayout()
        
        progressive_layout.addWidget(QLabel("Ramp-in Time (sec):"))
        self.ramp_in_time = QDoubleSpinBox()
        self.ramp_in_time.setRange(0.1, 10.0)
        self.ramp_in_time.setValue(2.0)
        self.ramp_in_time.setSingleStep(0.1)
        self.ramp_in_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.ramp_in_time)
        
        progressive_layout.addWidget(QLabel("Ramp-out Time (sec):"))
        self.ramp_out_time = QDoubleSpinBox()
        self.ramp_out_time.setRange(0.1, 10.0)
        self.ramp_out_time.setValue(1.0)
        self.ramp_out_time.setSingleStep(0.1)
        self.ramp_out_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.ramp_out_time)
        
        progressive_layout.addWidget(QLabel("Start Percentage (%):"))
        self.start_percentage = QDoubleSpinBox()
        self.start_percentage.setRange(0, 100)
        self.start_percentage.setValue(20.0)
        self.start_percentage.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.start_percentage)
        
        progressive_layout.addWidget(QLabel("End Percentage (%):"))
        self.end_percentage = QDoubleSpinBox()
        self.end_percentage.setRange(0, 100)
        self.end_percentage.setValue(100.0)
        self.end_percentage.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.end_percentage)
        
        progressive_layout.addWidget(QLabel("Progression Basis:"))
        self.progression_basis = QComboBox()
        self.progression_basis.addItems(["Time", "RPM", "Speed (MPH)", "Boost Pressure"])
        self.progression_basis.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.progression_basis)
        
        self.boost_progression_enabled = QCheckBox("Enable Boost-Based Assist (Anti-Lag)")
        self.boost_progression_enabled.setChecked(True)
        self.boost_progression_enabled.setStyleSheet("color: #ffffff;")
        progressive_layout.addWidget(self.boost_progression_enabled)
        
        boost_row = QHBoxLayout()
        self.boost_start = QDoubleSpinBox()
        self.boost_start.setRange(0, 50)
        self.boost_start.setValue(5.0)
        self.boost_start.setPrefix("Start ")
        self.boost_start.setSuffix(" psi")
        self.boost_start.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_row.addWidget(self.boost_start)
        self.boost_end = QDoubleSpinBox()
        self.boost_end.setRange(0, 60)
        self.boost_end.setValue(18.0)
        self.boost_end.setPrefix("End ")
        self.boost_end.setSuffix(" psi")
        self.boost_end.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_row.addWidget(self.boost_end)
        progressive_layout.addLayout(boost_row)
        
        progressive_layout.addWidget(QLabel("Resume / Restart Logic:"))
        self.resume_mode = QComboBox()
        self.resume_mode.addItems(["Resume", "Restart", "Auto"])
        self.resume_mode.setCurrentText("Auto")
        self.resume_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.resume_mode)
        
        progressive_layout.addWidget(QLabel("Solenoid Frequency (Hz):"))
        self.solenoid_frequency = QSpinBox()
        self.solenoid_frequency.setRange(10, 30)
        self.solenoid_frequency.setValue(20)
        self.solenoid_frequency.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        progressive_layout.addWidget(self.solenoid_frequency)
        
        progressive_group.setLayout(progressive_layout)
        layout.addWidget(progressive_group)
        
        # Fuel and Ignition Management
        fuel_ign_group = QGroupBox("Fuel & Ignition Management")
        fuel_ign_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        fuel_ign_layout = QVBoxLayout()
        
        fuel_ign_layout.addWidget(QLabel("System Type:"))
        self.system_type = QComboBox()
        self.system_type.addItems(["Wet System", "Dry System"])
        self.system_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_ign_layout.addWidget(self.system_type)
        
        fuel_ign_layout.addWidget(QLabel("Fuel Solenoid Control:"))
        self.fuel_solenoid = QComboBox()
        self.fuel_solenoid.addItems(["Automatic", "Manual", "Disabled"])
        self.fuel_solenoid.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_ign_layout.addWidget(self.fuel_solenoid)
        
        fuel_ign_layout.addWidget(QLabel("Base Timing Retard (deg/50HP):"))
        self.base_timing_retard = QDoubleSpinBox()
        self.base_timing_retard.setRange(0, 10)
        self.base_timing_retard.setValue(2.0)
        self.base_timing_retard.setSingleStep(0.5)
        self.base_timing_retard.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_ign_layout.addWidget(self.base_timing_retard)
        
        fuel_ign_group.setLayout(fuel_ign_layout)
        layout.addWidget(fuel_ign_group)
        
        # Safety Features
        safety_group = QGroupBox("Safety Features")
        safety_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        safety_layout = QVBoxLayout()
        
        safety_layout.addWidget(QLabel("Wideband O₂ Source:"))
        self.wideband_source = QComboBox()
        self.wideband_source.addItems(["Built-in Controller", "CAN Wideband", "External 0-5V"])
        self.wideband_source.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.wideband_source)
        
        safety_layout.addWidget(QLabel("MAP Sensor Input:"))
        self.map_source = QComboBox()
        self.map_source.addItems(["ECU MAP", "Standalone Sensor", "RaceCapture Stream"])
        self.map_source.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.map_source)
        
        safety_layout.addWidget(QLabel("Fuel Pressure Sensor:"))
        self.fuel_sensor = QComboBox()
        self.fuel_sensor.addItems(["Factory Sender", "0-5V Sensor", "CAN Analog"])
        self.fuel_sensor.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.fuel_sensor)
        
        safety_layout.addWidget(QLabel("Nitrous Pressure Sensor:"))
        self.nitrous_sensor = QComboBox()
        self.nitrous_sensor.addItems(["Internal", "Standalone 1500psi", "RaceCapture CAN"])
        self.nitrous_sensor.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.nitrous_sensor)
        
        safety_layout.addWidget(QLabel("Min Fuel Pressure (psi):"))
        self.min_fuel_pressure = QDoubleSpinBox()
        self.min_fuel_pressure.setRange(0, 100)
        self.min_fuel_pressure.setValue(40.0)
        self.min_fuel_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_fuel_pressure)
        
        safety_layout.addWidget(QLabel("Min Nitrous Pressure (psi):"))
        self.min_nitrous_pressure = QDoubleSpinBox()
        self.min_nitrous_pressure.setRange(0, 2000)
        self.min_nitrous_pressure.setValue(750.0)
        self.min_nitrous_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_nitrous_pressure)
        
        safety_layout.addWidget(QLabel("Target Nitrous Pressure (psi):"))
        self.target_nitrous_pressure = QDoubleSpinBox()
        self.target_nitrous_pressure.setRange(0, 2000)
        self.target_nitrous_pressure.setValue(950.0)
        self.target_nitrous_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.target_nitrous_pressure)
        
        self.bottle_heater_enabled = QCheckBox("Bottle Heater Auto Control")
        self.bottle_heater_enabled.setChecked(True)
        self.bottle_heater_enabled.setStyleSheet("color: #ffffff;")
        safety_layout.addWidget(self.bottle_heater_enabled)
        
        safety_layout.addWidget(QLabel("Min AFR (Lambda):"))
        self.min_afr = QDoubleSpinBox()
        self.min_afr.setRange(0.7, 1.0)
        self.min_afr.setValue(0.85)
        self.min_afr.setSingleStep(0.01)
        self.min_afr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_afr)
        
        self.afr_closed_loop = QCheckBox("AFR Closed-Loop Feedback")
        self.afr_closed_loop.setChecked(True)
        self.afr_closed_loop.setStyleSheet("color: #ffffff;")
        safety_layout.addWidget(self.afr_closed_loop)
        
        safety_layout.addWidget(QLabel("Closed-Loop Gain (%):"))
        self.closed_loop_gain = QDoubleSpinBox()
        self.closed_loop_gain.setRange(0, 50)
        self.closed_loop_gain.setValue(10.0)
        self.closed_loop_gain.setSingleStep(1.0)
        self.closed_loop_gain.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.closed_loop_gain)
        
        safety_layout.addWidget(QLabel("Min Coolant Temp (°C):"))
        self.min_coolant_temp = QSpinBox()
        self.min_coolant_temp.setRange(0, 100)
        self.min_coolant_temp.setValue(60)
        self.min_coolant_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_coolant_temp)
        
        safety_layout.addWidget(QLabel("Max Coolant Temp (°C):"))
        self.max_coolant_temp = QSpinBox()
        self.max_coolant_temp.setRange(80, 130)
        self.max_coolant_temp.setValue(110)
        self.max_coolant_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_coolant_temp)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        # Flow Rate (existing)
        layout.addWidget(QLabel("Flow Rate (lb/hr):"))
        self.flow_rate = QDoubleSpinBox()
        self.flow_rate.setRange(0, 1000)
        self.flow_rate.setValue(150)
        self.flow_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        layout.addWidget(self.flow_rate)
        
        # Data logging group
        logging_group = QGroupBox("Data Logging & Integration")
        logging_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        logging_layout = QVBoxLayout()
        self.log_count_label = QLabel("Logged Passes: 0 / 120")
        self.log_count_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        logging_layout.addWidget(self.log_count_label)
        self.last_log_label = QLabel("Last Event: None")
        self.last_log_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        logging_layout.addWidget(self.last_log_label)
        self.touchscreen_hint = QLabel("Touchscreen + PC interfaces stay in sync.")
        self.touchscreen_hint.setStyleSheet("color: #5f6368; font-size: 10px;")
        logging_layout.addWidget(self.touchscreen_hint)
        self.clear_logs_btn = QPushButton("Clear Session Logs")
        self.clear_logs_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 4px;")
        self.clear_logs_btn.clicked.connect(self._clear_nitrous_logs)
        logging_layout.addWidget(self.clear_logs_btn)
        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)
        
    def _create_graphs_panel(self) -> QWidget:
        """Create comprehensive real-time monitoring graphs panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Real-Time Monitoring & Datalogging")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Create tabbed graphs
        graph_tabs = QTabWidget()
        graph_tabs.setStyleSheet("""
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
        
        # Progressive Control Graph
        progressive_graph = RealTimeGraph()
        progressive_graph.setMinimumHeight(200)
        graph_tabs.addTab(progressive_graph, "Progressive Control")
        self.progressive_graph = progressive_graph
        
        # Sensor Data Graph
        sensor_graph = RealTimeGraph()
        sensor_graph.setMinimumHeight(200)
        graph_tabs.addTab(sensor_graph, "Sensor Data")
        self.sensor_graph = sensor_graph
        
        # AFR & Knock Graph
        afr_knock_graph = RealTimeGraph()
        afr_knock_graph.setMinimumHeight(200)
        graph_tabs.addTab(afr_knock_graph, "AFR & Knock")
        self.afr_knock_graph = afr_knock_graph
        
        # Pressure Monitoring Graph
        pressure_graph = RealTimeGraph()
        pressure_graph.setMinimumHeight(200)
        graph_tabs.addTab(pressure_graph, "Pressure Monitoring")
        self.pressure_graph = pressure_graph
        
        # Data log table
        from PySide6.QtWidgets import QTableWidgetItem
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(8)
        self.log_table.setHorizontalHeaderLabels([
            "Run",
            "Duration (s)",
            "Peak Duty (%)",
            "Peak Shot (HP)",
            "Start RPM",
            "End RPM",
            "Min λ",
            "Max Boost (psi)",
        ])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        graph_tabs.addTab(self.log_table, "Session Logs")
        
        layout.addWidget(graph_tabs)
        self._refresh_log_table()
        return panel
    
    # ---------------------------
    # Nitrous logging helpers
    # ---------------------------
    def _start_run_logging(self, rpm: float, speed: float) -> None:
        self._run_active = True
        self._run_start_time = time.time()
        self._run_start_rpm = rpm
        self._current_run_samples = []
        self._resume_state = "Active"
        self._update_resume_indicator()
    
    def _update_run_logging(self, sample: dict[str, float]) -> None:
        if not self._run_active:
            return
        self._current_run_samples.append(sample)
    
    def _finish_run_logging(self) -> None:
        if not self._run_active:
            return
        duration = time.time() - self._run_start_time
        peak_duty = max((s.get("duty", 0.0) for s in self._current_run_samples), default=0.0)
        min_lambda = min((s.get("lambda", 1.0) for s in self._current_run_samples), default=1.0)
        max_boost = max((s.get("boost", 0.0) for s in self._current_run_samples), default=0.0)
        end_rpm = self._current_run_samples[-1].get("rpm", self._run_start_rpm) if self._current_run_samples else self._run_start_rpm
        active_stages = ", ".join(cfg.name for cfg in self.stage_configs if cfg.enabled)
        total_shot = sum(cfg.shot_size_hp for cfg in self.stage_configs if cfg.enabled)
        peak_shot = total_shot * (peak_duty / 100.0)
        self._run_counter += 1
        log_entry = NitrousRunLog(
            run_id=self._run_counter,
            start_timestamp=self._run_start_time,
            duration_s=duration,
            peak_duty=peak_duty,
            peak_shot_hp=peak_shot,
            start_rpm=self._run_start_rpm,
            end_rpm=end_rpm,
            min_lambda=min_lambda,
            max_boost=max_boost,
            active_stages=active_stages or "None",
        )
        self._log_history.append(log_entry)
        self._run_active = False
        self._current_run_samples = []
        self._last_run_end = time.time()
        self._resume_state = "Complete"
        self._update_resume_indicator()
        self._refresh_log_table()
    
    def _refresh_log_table(self) -> None:
        if not hasattr(self, "log_table"):
            return
        rows = list(reversed(self._log_history))
        self.log_table.setRowCount(len(rows))
        for row_index, log_entry in enumerate(rows):
            values = [
                f"#{log_entry.run_id}",
                f"{log_entry.duration_s:.2f}",
                f"{log_entry.peak_duty:.1f}",
                f"{log_entry.peak_shot_hp:.0f}",
                f"{log_entry.start_rpm:.0f}",
                f"{log_entry.end_rpm:.0f}",
                f"{log_entry.min_lambda:.2f}",
                f"{log_entry.max_boost:.1f}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.log_table.setItem(row_index, col, item)
        self.log_count_label.setText(f"Logged Passes: {len(self._log_history)} / 120")
        if rows:
            last = rows[0]
            self.last_log_label.setText(
                f"Last Event: Run #{last.run_id} • {time.strftime('%H:%M:%S', time.localtime(last.start_timestamp))}"
            )
        else:
            self.last_log_label.setText("Last Event: None")
    
    def _clear_nitrous_logs(self) -> None:
        self._log_history.clear()
        self._run_counter = 0
        self._refresh_log_table()
    
    def _export_nitrous_logs(self) -> None:
        if not self._log_history:
            QMessageBox.information(self, "No Logs", "No nitrous runs to export yet.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Nitrous Logs",
            "nitrous_logs.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Run", "Start Time", "Duration (s)", "Peak Duty (%)", "Peak Shot (HP)", "Start RPM", "End RPM", "Min Lambda", "Max Boost (psi)", "Active Stages"]
                )
                for log_entry in self._log_history:
                    writer.writerow(
                        [
                            log_entry.run_id,
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(log_entry.start_timestamp)),
                            f"{log_entry.duration_s:.2f}",
                            f"{log_entry.peak_duty:.1f}",
                            f"{log_entry.peak_shot_hp:.0f}",
                            f"{log_entry.start_rpm:.0f}",
                            f"{log_entry.end_rpm:.0f}",
                            f"{log_entry.min_lambda:.2f}",
                            f"{log_entry.max_boost:.1f}",
                            log_entry.active_stages,
                        ]
                    )
            QMessageBox.information(self, "Export Complete", f"Logs exported to:\n{filename}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Unable to export logs:\n{exc}")
    
    def _open_touchscreen_mode(self) -> None:
        if self.touchscreen_dialog is None:
            self.touchscreen_dialog = TouchscreenNitrousDialog(self, self)
        self.touchscreen_dialog.show()
        self.touchscreen_dialog.raise_()
        self.touchscreen_dialog.activateWindow()
    
    def _force_resume_ramp(self) -> None:
        self._resume_state = "Resume (Manual)"
        self._update_resume_indicator()
    
    def _force_restart_ramp(self) -> None:
        self._resume_state = "Restart (Manual)"
        self._update_resume_indicator()
    
    def _update_resume_indicator(self) -> None:
        if hasattr(self, "resume_indicator"):
            self.resume_indicator.setText(f"Ramp Mode: {self._resume_state}")
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update nitrous tab with telemetry data."""
        # Sensor values
        pressure = data.get("nitrous_pressure", 900)
        flow = data.get("nitrous_flow", 0)
        fuel_pressure = data.get("Fuel_Pressure", 45)
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 14.7)
        solenoid_duty = data.get("nitrous_duty", 0)
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        tps = data.get("TPS", data.get("Throttle_Position", 0))
        speed = data.get("Vehicle_Speed", data.get("Speed", 0))
        knock = data.get("Knock_Sensor", 0)
        boost = data.get("Boost_Pressure", 0)
        map_val = boost * 6.895
        lambda_val = afr / 14.7 if afr else 1.0
        
        # Update TelemetryIQ controller inputs
        if hasattr(self, 'telemetryiq_controller') and self.telemetryiq_controller:
            # Trans brake input
            trans_brake = data.get("Transbrake_Active", data.get("trans_brake", 0))
            self.telemetryiq_controller.set_trans_brake_state(bool(trans_brake))
            
            # Clutch input
            clutch = data.get("Clutch_Active", data.get("clutch", 0))
            self.telemetryiq_controller.set_clutch_state(bool(clutch))
            
            # Shifter input
            shifter_gear = data.get("Shifter_Gear", data.get("gear", None))
            if shifter_gear is not None:
                self.telemetryiq_controller.set_shifter_gear(int(shifter_gear))
            else:
                self.telemetryiq_controller.set_shifter_gear(None)
            
            # Throttle pedaling detection
            throttle_pedaling = tps < 95.0 and tps > 10.0  # Partial throttle = pedaling
            self.telemetryiq_controller.set_throttle_pedaling(throttle_pedaling)
            
            # Update input status LEDs
            if hasattr(self, 'trans_brake_led'):
                self.trans_brake_led.setText(f"Trans Brake: {'ON' if trans_brake else 'OFF'}")
                self.trans_brake_led.setStyleSheet(
                    f"color: {'#00ff00' if trans_brake else '#ff0000'}; "
                    f"font-weight: bold; padding: 4px; border: 1px solid #404040;"
                )
            
            if hasattr(self, 'clutch_led'):
                self.clutch_led.setText(f"Clutch: {'ON' if clutch else 'OFF'}")
                self.clutch_led.setStyleSheet(
                    f"color: {'#00ff00' if clutch else '#ff0000'}; "
                    f"font-weight: bold; padding: 4px; border: 1px solid #404040;"
                )
            
            if hasattr(self, 'shifter_led'):
                gear_text = str(shifter_gear) if shifter_gear is not None else "N/A"
                self.shifter_led.setText(f"Shifter: {gear_text}")
                self.shifter_led.setStyleSheet(
                    f"color: {'#00ff00' if shifter_gear is not None else '#ffaa00'}; "
                    f"font-weight: bold; padding: 4px; border: 1px solid #404040;"
                )
        
        # Window switch logic
        window_allowed = True
        if hasattr(self, "window_switch") and self.window_switch.isChecked():
            rpm_ok = self.window_rpm_low.value() <= rpm <= self.window_rpm_high.value()
            speed_ok = self.min_speed.value() <= speed <= self.max_speed.value()
            window_allowed = rpm_ok and speed_ok
        
        nitrous_active = bool(data.get("nitrous_active", False) or solenoid_duty > 5)
        
        # Update gauges
        status_value = 100 if nitrous_active and window_allowed else 0
        self.pressure_gauge.set_value(pressure)
        self.flow_gauge.set_value(flow)
        self.status_gauge.set_value(status_value)
        if hasattr(self, "fuel_pressure_gauge"):
            self.fuel_pressure_gauge.set_value(fuel_pressure)
        if hasattr(self, "afr_gauge"):
            self.afr_gauge.set_value(afr)
        if hasattr(self, "solenoid_duty_gauge"):
            self.solenoid_duty_gauge.set_value(solenoid_duty)
        
        # Run logging / resume logic
        if nitrous_active and not self._run_active:
            resume_mode = getattr(self, "resume_mode", None)
            mode_text = resume_mode.currentText() if resume_mode else "Auto"
            time_since_last = time.time() - self._last_run_end if self._last_run_end else 999
            if mode_text == "Resume" or (mode_text == "Auto" and time_since_last < 3.0):
                self._resume_state = "Resume"
            else:
                self._resume_state = "Restart"
            self._update_resume_indicator()
            self._start_run_logging(rpm, speed)
        if nitrous_active:
            sample = {
                "rpm": rpm,
                "speed": speed,
                "duty": solenoid_duty,
                "lambda": lambda_val,
                "boost": boost,
            }
            self._update_run_logging(sample)
        elif self._run_active:
            self._finish_run_logging()
        
        # Update stage visual statuses
        self._update_stage_status_visuals(rpm, speed, tps, boost, solenoid_duty, nitrous_active)
        
        # Update graphs
        if hasattr(self, "progressive_graph"):
            self.progressive_graph.update_data(rpm, solenoid_duty, status_value, flow / 10)
        
        if hasattr(self, "sensor_graph"):
            self.sensor_graph.update_data(rpm, tps, solenoid_duty, status_value)
        
        if hasattr(self, "afr_knock_graph"):
            self.afr_knock_graph.update_data(rpm, lambda_val, afr, knock)
        
        if hasattr(self, "pressure_graph"):
            self.pressure_graph.update_data(rpm, fuel_pressure, pressure, map_val)
    
    def _update_stage_status_visuals(
        self,
        rpm: float,
        speed: float,
        tps: float,
        boost: float,
        duty: float,
        nitrous_active: bool,
    ) -> None:
        if not self.stage_status_labels:
            return
        run_time = time.time() - self._run_start_time if self._run_active else 0.0
        value_map = {
            "rpm": rpm,
            "time": run_time,
            "speed": speed,
            "mph": speed,
            "boost": boost,
            "tps": tps,
            "throttle": tps,
        }
        for cfg, label in zip(self.stage_configs, self.stage_status_labels):
            if not cfg.enabled:
                label.setText(f"{cfg.name}: Disabled")
                label.setStyleSheet("color: #5f6368; font-weight: bold; border: 1px solid #404040; padding: 4px;")
                continue
            start_val = value_map.get(cfg.start_trigger.lower(), 0.0)
            end_val = value_map.get(cfg.end_trigger.lower(), 0.0)
            start_met = start_val >= cfg.start_value
            ramp_out_reached = False
            if cfg.end_trigger.lower() in ("time", "rpm", "speed", "mph", "boost"):
                ramp_out_reached = end_val >= cfg.end_value
            status_text = "Idle"
            color = "#ffaa00"
            if nitrous_active and start_met and not ramp_out_reached:
                status_text = "Active"
                color = "#00ff80"
            elif nitrous_active and ramp_out_reached:
                status_text = "Ramping Out"
                color = "#0080ff"
            elif start_met:
                status_text = "Armed"
                color = "#ffd166"
            label.setText(f"{cfg.name}: {status_text}")
            label.setStyleSheet(f"color: {color}; font-weight: bold; border: 1px solid #404040; padding: 4px;")


class TouchscreenNitrousDialog(QDialog):
    """Touch-friendly overlay for trackside adjustments."""

    def __init__(self, parent: QWidget, nitrous_tab: NitrousTab) -> None:
        super().__init__(parent)
        self.nitrous_tab = nitrous_tab
        self.setWindowTitle("Touchscreen Nitrous Controller")
        self.setMinimumSize(480, 360)
        self.setStyleSheet("background-color: #0f0f0f; color: #ffffff;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        title = QLabel("Trackside Touch Interface")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00e0ff;")
        layout.addWidget(title)
        
        # Stage toggles
        grid = QGridLayout()
        grid.setSpacing(10)
        self.stage_buttons: list[QPushButton] = []
        for row, cfg in enumerate(self.nitrous_tab.stage_configs):
            btn = QPushButton(cfg.name)
            btn.setCheckable(True)
            btn.setChecked(cfg.enabled)
            btn.setMinimumHeight(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1f1f1f;
                    border: 2px solid #404040;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                    color: #ffffff;
                }
                QPushButton:checked {
                    background-color: #00c853;
                    border-color: #00ff80;
                }
            """)
            btn.clicked.connect(self._make_stage_toggle_handler(cfg))
            grid.addWidget(btn, row // 2, row % 2)
            self.stage_buttons.append(btn)
        layout.addLayout(grid)
        
        self.slider_label = QLabel("Start Percentage: 20%")
        self.slider_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.slider_label)
        
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setRange(0, 100)
        self.start_slider.setTickInterval(5)
        self.start_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.start_slider.valueChanged.connect(self._touch_slider_changed)
        layout.addWidget(self.start_slider)
        
        self.status_label = QLabel("Linked to desktop controller")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        layout.addWidget(self.status_label)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 10px 20px; border-radius: 6px;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self._sync_with_nitrous()
    
    def showEvent(self, event) -> None:  # type: ignore[override]
        self._sync_with_nitrous()
        super().showEvent(event)
    
    def _make_stage_toggle_handler(self, cfg: NitrousStageConfig):
        def handler(is_checked: bool) -> None:
            cfg.enabled = is_checked
            self.status_label.setText(f"{cfg.name} {'Enabled' if is_checked else 'Disabled'}")
        return handler
    
    def _touch_slider_changed(self, value: int) -> None:
        self.slider_label.setText(f"Start Percentage: {value}%")
        if hasattr(self.nitrous_tab, "start_percentage"):
            self.nitrous_tab.start_percentage.setValue(float(value))
    
    def _sync_with_nitrous(self) -> None:
        if hasattr(self.nitrous_tab, "start_percentage"):
            self.start_slider.setValue(int(self.nitrous_tab.start_percentage.value()))
        for btn, cfg in zip(self.stage_buttons, self.nitrous_tab.stage_configs):
            btn.setChecked(cfg.enabled)


class TurboTab(ModuleTab):
    """Turbo system settings tab with full ECU tuning interface."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Turbo", parent)
        
    def _create_gauges_panel(self) -> QWidget:
        """Create turbo-specific gauges."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Boost Pressure gauge
        self.boost_gauge = AnalogGauge(
            "Boost Pressure",
            min_value=0,
            max_value=50,
            unit="psi",
            warning_start=40,
            warning_end=50,
            warning_color="#ff0000",
        )
        layout.addWidget(self.boost_gauge)
        
        # Wastegate Duty gauge
        self.wastegate_gauge = AnalogGauge(
            "Wastegate Duty",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.wastegate_gauge)
        
        # Turbo Speed gauge
        self.turbo_speed_gauge = AnalogGauge(
            "Turbo Speed",
            min_value=0,
            max_value=200000,
            unit="RPM",
        )
        layout.addWidget(self.turbo_speed_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with boost control table."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Boost Control Map")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        self.table = QTableWidget()
        self.table.setRowCount(10)
        self.table.setColumnCount(8)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        
        # Initialize table
        rpm_values = [2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)
            
        throttle_values = [20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        for row, throttle in enumerate(throttle_values):
            item = QTableWidgetItem(f"{throttle}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setVerticalHeaderItem(row, item)
            
        # Fill with boost values
        for row in range(10):
            for col in range(8):
                boost_val = 10 + (row * 2) + (col * 0.5)
                item = QTableWidgetItem(f"{boost_val:.1f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                if boost_val > 40:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif boost_val > 30:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                self.table.setItem(row, col, item)
        
        layout.addWidget(self.table)
        return panel
        
    def _add_right_settings(self, layout: QVBoxLayout) -> None:
        """Add right panel settings."""
        layout.addWidget(QLabel("Boost Target (psi):"))
        self.boost_target = QDoubleSpinBox()
        self.boost_target.setRange(0, 50)
        self.boost_target.setValue(20)
        self.boost_target.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        layout.addWidget(self.boost_target)
        
        layout.addWidget(QLabel("Control Mode:"))
        self.control_mode = QComboBox()
        self.control_mode.addItems(["Manual", "Auto", "PID"])
        self.control_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        layout.addWidget(self.control_mode)
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update turbo tab with telemetry data."""
        boost = data.get("Boost_Pressure", data.get("boost_psi", 0))
        wastegate = data.get("wastegate_duty", 50)
        turbo_speed = data.get("turbo_speed", 100000)
        
        self.boost_gauge.set_value(boost)
        self.wastegate_gauge.set_value(wastegate)
        self.turbo_speed_gauge.set_value(turbo_speed)
        
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = boost * 6.895
        afr = data.get("AFR", 14.7)
        ego = wastegate
        self.realtime_graph.update_data(rpm, map_val, afr, ego)


class E85Tab(ModuleTab):
    """E85/FlexFuel settings tab with full ECU tuning interface."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("E85", parent)
    
    def setup_ui(self) -> None:
        """Override setup_ui to add comprehensive graphs panel."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges column
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Main data table/visualization
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings and visualization
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Comprehensive graphs panel
        graphs_panel = self._create_graphs_panel()
        main_layout.addWidget(graphs_panel, stretch=1)
        
        # Import/Export bar
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
        
    def _create_gauges_panel(self) -> QWidget:
        """Create E85-specific gauges."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # E85 Percentage gauge
        self.e85_gauge = AnalogGauge(
            "E85 Percentage",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.e85_gauge)
        
        # Fuel Compensation gauge
        self.comp_gauge = AnalogGauge(
            "Fuel Compensation",
            min_value=-50,
            max_value=50,
            unit="%",
        )
        layout.addWidget(self.comp_gauge)
        
        # Lambda/AFR gauge
        self.lambda_gauge = AnalogGauge(
            "Lambda/AFR",
            min_value=0.7,
            max_value=1.3,
            unit="",
        )
        layout.addWidget(self.lambda_gauge)
        
        # Fuel Temperature gauge
        self.fuel_temp_gauge = AnalogGauge(
            "Fuel Temp",
            min_value=-20,
            max_value=80,
            unit="°C",
        )
        layout.addWidget(self.fuel_temp_gauge)
        
        # Injector Duty Cycle gauge
        self.injector_duty_gauge = AnalogGauge(
            "Injector Duty",
            min_value=0,
            max_value=100,
            unit="%",
            warning_start=85,
            warning_end=100,
            warning_color="#ff0000",
        )
        layout.addWidget(self.injector_duty_gauge)
        
        # Knock Sensor gauge
        self.knock_gauge = AnalogGauge(
            "Knock Activity",
            min_value=0,
            max_value=100,
            unit="%",
            warning_start=50,
            warning_end=100,
            warning_color="#ff0000",
        )
        layout.addWidget(self.knock_gauge)
        
        # Fuel Pressure gauge
        self.fuel_pressure_gauge = AnalogGauge(
            "Fuel Pressure",
            min_value=0,
            max_value=100,
            unit="psi",
            warning_start=0,
            warning_end=40,
            warning_color="#ff0000",
        )
        layout.addWidget(self.fuel_pressure_gauge)
        
        layout.addStretch()
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with tabbed E85 maps."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabbed interface for different maps
        self.center_tabs = QTabWidget()
        self.center_tabs.setStyleSheet("""
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
        
        # VE Table
        self.center_tabs.addTab(self._create_ve_map(), "VE Table")
        
        # Ignition Timing Map
        self.center_tabs.addTab(self._create_ignition_timing_map(), "Ignition Timing")
        
        # Fuel Compensation Table
        self.center_tabs.addTab(self._create_fuel_compensation_map(), "Fuel Compensation")
        
        # Ignition Compensation Table
        self.center_tabs.addTab(self._create_ignition_compensation_map(), "Ignition Compensation")
        
        # Cold Start Enrichment
        self.center_tabs.addTab(self._create_cold_start_map(), "Cold Start Enrichment")
        
        # Boost Control Map
        self.center_tabs.addTab(self._create_boost_control_map(), "Boost Control")
        
        layout.addWidget(self.center_tabs)
        return panel
    
    def _create_ve_map(self) -> QWidget:
        """Create VE Table for E85."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Volumetric Efficiency Table (RPM vs Load) - E85 requires 30-40% more fuel")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Use VETableWidget for consistency
        self.ve_table = VETableWidget()
        layout.addWidget(self.ve_table, stretch=1)
        return tab
    
    def _create_ignition_timing_map(self) -> QWidget:
        """Create Ignition Timing Map optimized for E85."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Map (RPM vs Load) - E85 allows aggressive timing due to high knock resistance")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # RPM
        table.setColumnCount(10)  # Load
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
        
        load_values = [20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        for col, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with timing values (more advance for E85)
        for row in range(10):
            for col in range(10):
                base_timing = 32.0  # Higher base timing for E85
                # More advance at higher RPM and load
                timing = base_timing + (rpm_values[row] / 10000) * 12 + (load_values[col] / 100) * 8
                timing = max(10.0, min(45.0, timing))  # Range: 10-45 degrees
                
                item = QTableWidgetItem(f"{timing:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing > 38:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Very advanced
                elif timing > 30:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Advanced
                elif timing > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Retarded
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_fuel_compensation_map(self) -> QWidget:
        """Create Fuel Compensation Table based on ethanol percentage."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Fuel Compensation Map (vs Ethanol % & Load) - E85 requires 30-40% more fuel")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # Load
        table.setColumnCount(8)  # Ethanol %
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
        
        e85_values = [0, 10, 20, 30, 50, 70, 85, 100]
        for col, e85 in enumerate(e85_values):
            item = QTableWidgetItem(f"{e85}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        load_values = [20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        for row, load in enumerate(load_values):
            item = QTableWidgetItem(f"{load}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with compensation values (30-40% more fuel for E85)
        for row in range(10):
            for col in range(8):
                comp_val = (e85_values[col] / 100) * 35  # Scale: 0-35% compensation
                comp_val = max(0, min(40, comp_val))
                item = QTableWidgetItem(f"+{comp_val:.1f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if comp_val > 30:
                    item.setBackground(QBrush(QColor("#00ff00")))  # High compensation
                elif comp_val > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                elif comp_val > 10:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Low
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))  # Minimal
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_ignition_compensation_map(self) -> QWidget:
        """Create Ignition Compensation Table based on ethanol percentage."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Compensation Map (vs Ethanol % & RPM) - Advance timing with higher ethanol")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # RPM
        table.setColumnCount(8)  # Ethanol %
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
        
        e85_values = [0, 10, 20, 30, 50, 70, 85, 100]
        for col, e85 in enumerate(e85_values):
            item = QTableWidgetItem(f"{e85}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with timing advance values (more advance with higher ethanol)
        for row in range(10):
            for col in range(8):
                # Advance timing based on ethanol content (up to 8 degrees)
                timing_advance = (e85_values[col] / 100) * 8 + (rpm_values[row] / 10000) * 2
                timing_advance = max(0, min(10, timing_advance))
                
                item = QTableWidgetItem(f"+{timing_advance:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing_advance > 6:
                    item.setBackground(QBrush(QColor("#00ff00")))  # High advance
                elif timing_advance > 3:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#2a2a2a")))  # Minimal
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_cold_start_map(self) -> QWidget:
        """Create Cold Start Enrichment table."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Cold Start Enrichment (vs Coolant Temp & Time) - E85 vaporizes poorly in cold temps")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)  # Coolant temp ranges
        table.setColumnCount(10)  # Time after start
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
        
        time_values = [0, 5, 10, 15, 20, 30, 45, 60, 90, 120]
        for col, time_val in enumerate(time_values):
            item = QTableWidgetItem(f"{time_val}s")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        temp_values = [-20, -10, 0, 10, 20, 40, 60, 80]
        for row, temp in enumerate(temp_values):
            item = QTableWidgetItem(f"{temp}°C")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with enrichment values (more fuel at colder temps and immediately after start)
        for row in range(8):
            for col in range(10):
                # More enrichment at colder temps and right after start
                base_enrich = max(0, (temp_values[row] < 20) * (20 - temp_values[row]) * 2)
                time_factor = max(0, (time_values[col] < 30) * (30 - time_values[col]) / 3)
                enrich = base_enrich + time_factor
                enrich = max(0, min(100, enrich))
                
                item = QTableWidgetItem(f"+{enrich:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if enrich > 60:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very rich
                elif enrich > 40:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Rich
                elif enrich > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Normal
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_boost_control_map(self) -> QWidget:
        """Create Boost Control Map based on ethanol content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Boost Control Map (vs Ethanol % & RPM) - Higher boost with higher ethanol content")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # RPM
        table.setColumnCount(8)  # Ethanol %
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
        
        e85_values = [0, 10, 20, 30, 50, 70, 85, 100]
        for col, e85 in enumerate(e85_values):
            item = QTableWidgetItem(f"{e85}%")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with boost values (higher boost with higher ethanol)
        for row in range(10):
            for col in range(8):
                base_boost = 20.0
                # Increase boost with ethanol content (up to 15 psi more)
                boost = base_boost + (e85_values[col] / 100) * 15 + (rpm_values[row] / 11000) * 5
                boost = max(10.0, min(50.0, boost))
                
                item = QTableWidgetItem(f"{boost:.1f}psi")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if boost > 40:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very high
                elif boost > 30:
                    item.setBackground(QBrush(QColor("#ff8000")))  # High
                elif boost > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Low
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
        
    def _add_right_settings(self, layout: QVBoxLayout) -> None:
        """Add right panel settings."""
        # Flex Fuel Sensor Input
        sensor_group = QGroupBox("Flex Fuel Sensor Input")
        sensor_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        sensor_layout = QVBoxLayout()
        
        sensor_layout.addWidget(QLabel("Sensor Type:"))
        self.sensor_type = QComboBox()
        self.sensor_type.addItems(["GM Flex Fuel Sensor", "Continental Flex Fuel Sensor", "Custom Frequency"])
        self.sensor_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensor_layout.addWidget(self.sensor_type)
        
        sensor_layout.addWidget(QLabel("Current Ethanol %:"))
        self.e85_percent = QDoubleSpinBox()
        self.e85_percent.setRange(0, 100)
        self.e85_percent.setValue(85)
        self.e85_percent.setDecimals(1)
        self.e85_percent.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensor_layout.addWidget(self.e85_percent)
        
        sensor_layout.addWidget(QLabel("Fuel Temperature (°C):"))
        self.fuel_temp = QDoubleSpinBox()
        self.fuel_temp.setRange(-20, 80)
        self.fuel_temp.setValue(20.0)
        self.fuel_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensor_layout.addWidget(self.fuel_temp)
        
        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)
        
        # Stoichiometric Ratio Calculation
        stoich_group = QGroupBox("Stoichiometric Ratio Calculation")
        stoich_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        stoich_layout = QVBoxLayout()
        
        self.auto_stoich_enabled = QCheckBox("Auto-Adjust Stoichiometric Ratio")
        self.auto_stoich_enabled.setChecked(True)
        self.auto_stoich_enabled.setStyleSheet("color: #ffffff;")
        stoich_layout.addWidget(self.auto_stoich_enabled)
        
        stoich_layout.addWidget(QLabel("Current Stoich AFR:"))
        self.stoich_afr = QDoubleSpinBox()
        self.stoich_afr.setRange(9.0, 14.7)
        self.stoich_afr.setValue(9.8)
        self.stoich_afr.setDecimals(1)
        self.stoich_afr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        stoich_layout.addWidget(self.stoich_afr)
        
        stoich_layout.addWidget(QLabel("Tuning Mode:"))
        self.tuning_mode = QComboBox()
        self.tuning_mode.addItems(["Lambda (Recommended)", "AFR"])
        self.tuning_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        stoich_layout.addWidget(self.tuning_mode)
        
        stoich_group.setLayout(stoich_layout)
        layout.addWidget(stoich_group)
        
        # Fueling Adjustments
        fueling_group = QGroupBox("Fueling Adjustments")
        fueling_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        fueling_layout = QVBoxLayout()
        
        fueling_layout.addWidget(QLabel("Master Fuel Scaler (%):"))
        self.master_fuel_scaler = QDoubleSpinBox()
        self.master_fuel_scaler.setRange(0, 200)
        self.master_fuel_scaler.setValue(135.0)  # 35% increase for E85
        self.master_fuel_scaler.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fueling_layout.addWidget(self.master_fuel_scaler)
        
        fueling_layout.addWidget(QLabel("Fuel Compensation (%):"))
        self.fuel_comp = QDoubleSpinBox()
        self.fuel_comp.setRange(-50, 50)
        self.fuel_comp.setValue(30)
        self.fuel_comp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fueling_layout.addWidget(self.fuel_comp)
        
        fueling_group.setLayout(fueling_layout)
        layout.addWidget(fueling_group)
        
        # Injector Characterization
        injector_group = QGroupBox("Injector Characterization")
        injector_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        injector_layout = QVBoxLayout()
        
        injector_layout.addWidget(QLabel("Injector Size (cc/min):"))
        self.injector_size = QSpinBox()
        self.injector_size.setRange(100, 5000)
        self.injector_size.setValue(2000)  # Larger for E85
        self.injector_size.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        injector_layout.addWidget(self.injector_size)
        
        injector_layout.addWidget(QLabel("Dead Time (ms):"))
        self.dead_time = QDoubleSpinBox()
        self.dead_time.setRange(0.1, 5.0)
        self.dead_time.setValue(1.0)
        self.dead_time.setSingleStep(0.1)
        self.dead_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        injector_layout.addWidget(self.dead_time)
        
        injector_group.setLayout(injector_layout)
        layout.addWidget(injector_group)
        
        # Boost Control (for forced induction)
        boost_group = QGroupBox("Boost Control (Forced Induction)")
        boost_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        boost_layout = QVBoxLayout()
        
        boost_layout.addWidget(QLabel("Boost Control Mode:"))
        self.boost_mode = QComboBox()
        self.boost_mode.addItems(["By Ethanol %", "By Gear", "By Speed", "Fixed"])
        self.boost_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.boost_mode)
        
        boost_layout.addWidget(QLabel("Max Boost (psi):"))
        self.max_boost = QDoubleSpinBox()
        self.max_boost.setRange(0, 60)
        self.max_boost.setValue(35.0)
        self.max_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.max_boost)
        
        boost_group.setLayout(boost_layout)
        layout.addWidget(boost_group)
        
        # Safety Limiters/Fail-safes
        safety_group = QGroupBox("Safety Limiters / Fail-safes")
        safety_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        safety_layout = QVBoxLayout()
        
        self.sensor_failsafe = QCheckBox("Sensor Fail-Safe Enabled")
        self.sensor_failsafe.setChecked(True)
        self.sensor_failsafe.setStyleSheet("color: #ffffff;")
        safety_layout.addWidget(self.sensor_failsafe)
        
        safety_layout.addWidget(QLabel("Min Lambda (Lean Protection):"))
        self.min_lambda = QDoubleSpinBox()
        self.min_lambda.setRange(0.7, 1.0)
        self.min_lambda.setValue(0.85)
        self.min_lambda.setSingleStep(0.01)
        self.min_lambda.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_lambda)
        
        safety_layout.addWidget(QLabel("Fail-Safe Action:"))
        self.failsafe_action = QComboBox()
        self.failsafe_action.addItems(["Pull Timing", "Reduce Boost", "Pull Timing + Reduce Boost", "Switch to Safe Map"])
        self.failsafe_action.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.failsafe_action)
        
        safety_layout.addWidget(QLabel("Timing Pull Amount (°):"))
        self.timing_pull = QDoubleSpinBox()
        self.timing_pull.setRange(0, 20)
        self.timing_pull.setValue(5.0)
        self.timing_pull.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.timing_pull)
        
        safety_layout.addWidget(QLabel("Boost Reduction (%):"))
        self.boost_reduction = QDoubleSpinBox()
        self.boost_reduction.setRange(0, 100)
        self.boost_reduction.setValue(50.0)
        self.boost_reduction.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.boost_reduction)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
    def _create_graphs_panel(self) -> QWidget:
        """Create comprehensive real-time monitoring graphs panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Live Data Monitoring & Datalogging")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Create tabbed graphs
        graph_tabs = QTabWidget()
        graph_tabs.setStyleSheet("""
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
        
        # Ethanol Content & Fuel Temperature Graph
        ethanol_graph = RealTimeGraph()
        ethanol_graph.setMinimumHeight(200)
        graph_tabs.addTab(ethanol_graph, "Ethanol % & Fuel Temp")
        self.ethanol_graph = ethanol_graph
        
        # Wideband O2 / Lambda Graph
        lambda_graph = RealTimeGraph()
        lambda_graph.setMinimumHeight(200)
        graph_tabs.addTab(lambda_graph, "Wideband O2 / Lambda")
        self.lambda_graph = lambda_graph
        
        # Knock Sensor Activity Graph
        knock_graph = RealTimeGraph()
        knock_graph.setMinimumHeight(200)
        graph_tabs.addTab(knock_graph, "Knock Sensor Activity")
        self.knock_graph = knock_graph
        
        # Injector Duty Cycle Graph
        injector_graph = RealTimeGraph()
        injector_graph.setMinimumHeight(200)
        graph_tabs.addTab(injector_graph, "Injector Duty Cycle")
        self.injector_graph = injector_graph
        
        # Fuel Pressure & Temperature Graph
        fuel_pressure_graph = RealTimeGraph()
        fuel_pressure_graph.setMinimumHeight(200)
        graph_tabs.addTab(fuel_pressure_graph, "Fuel Pressure & Temp")
        self.fuel_pressure_graph = fuel_pressure_graph
        
        layout.addWidget(graph_tabs)
        return panel
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update E85 tab with telemetry data."""
        e85 = data.get("e85_percent", data.get("FlexFuelPercent", 85))
        comp = data.get("fuel_compensation", 30)
        lambda_val = data.get("lambda_value", 1.0)
        fuel_temp = data.get("Fuel_Temp", 20.0)
        injector_duty = data.get("Injector_Duty", 60.0)
        knock = data.get("Knock_Sensor", 0)
        fuel_pressure = data.get("Fuel_Pressure", 45.0)
        
        self.e85_gauge.set_value(e85)
        self.comp_gauge.set_value(comp)
        self.lambda_gauge.set_value(lambda_val)
        if hasattr(self, 'fuel_temp_gauge'):
            self.fuel_temp_gauge.set_value(fuel_temp)
        if hasattr(self, 'injector_duty_gauge'):
            self.injector_duty_gauge.set_value(injector_duty)
        if hasattr(self, 'knock_gauge'):
            self.knock_gauge.set_value(knock)
        if hasattr(self, 'fuel_pressure_gauge'):
            self.fuel_pressure_gauge.set_value(fuel_pressure)
        
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = data.get("Boost_Pressure", 0) * 6.895
        afr = lambda_val * 9.8  # E85 stoich AFR (adjusts based on ethanol %)
        
        # Update graphs
        if hasattr(self, 'ethanol_graph'):
            self.ethanol_graph.update_data(rpm, e85, fuel_temp, 0)
        
        if hasattr(self, 'lambda_graph'):
            self.lambda_graph.update_data(rpm, lambda_val, afr, 0)
        
        if hasattr(self, 'knock_graph'):
            self.knock_graph.update_data(rpm, knock, 0, 0)
        
        if hasattr(self, 'injector_graph'):
            self.injector_graph.update_data(rpm, injector_duty, 0, 0)
        
        if hasattr(self, 'fuel_pressure_graph'):
            self.fuel_pressure_graph.update_data(rpm, fuel_pressure, fuel_temp, 0)
        
        # Update base realtime graph
        if hasattr(self, 'realtime_graph'):
            self.realtime_graph.update_data(rpm, map_val, afr, comp)


class MethanolTab(ModuleTab):
    """Methanol injection settings tab with full ECU tuning interface."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.current_mode = "Street"
        self.available_modes = ["Street", "Race", "Kill"]
        self.failsafe_triggered = False
        self._fault_log: deque[str] = deque(maxlen=32)
        self._session_logs: deque[dict[str, float]] = deque(maxlen=240)
        self.fault_table = None
        self.log_table = None
        self.mode_status_label = None
        self.failsafe_label = None
        self.environment_summary = None
        self.env_inputs: List[QDoubleSpinBox] = []
        super().__init__("Methanol", parent)
    
    def _create_control_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background-color: #2a2a2a; padding: 6px; border: 1px solid #404040;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(self.available_modes)
        self.mode_combo.currentTextChanged.connect(self._change_mode)
        self.mode_combo.setStyleSheet("color: #ffffff; background-color: #1a1a1a; padding: 4px;")
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(self.mode_combo)
        
        self.mode_status_label = QLabel("Street mode • balanced cooling")
        self.mode_status_label.setStyleSheet("color: #9aa0a6;")
        layout.addWidget(self.mode_status_label)
        
        layout.addStretch()
        
        self.failsafe_label = QLabel("Failsafe: Armed")
        self.failsafe_label.setStyleSheet("color: #00ff80; font-weight: bold;")
        layout.addWidget(self.failsafe_label)
        
        self.clear_faults_btn = QPushButton("Clear Faults")
        self.clear_faults_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        self.clear_faults_btn.clicked.connect(self._clear_faults)
        layout.addWidget(self.clear_faults_btn)
        
        export_btn = QPushButton("Export Logs")
        export_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        export_btn.clicked.connect(self._export_session_logs)
        layout.addWidget(export_btn)
        
        return bar
        
    def _create_gauges_panel(self) -> QWidget:
        """Create methanol-specific gauges."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Injection Duty gauge
        self.duty_gauge = AnalogGauge(
            "Injection Duty",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.duty_gauge)
        
        # Tank Level gauge
        self.level_gauge = AnalogGauge(
            "Tank Level",
            min_value=0,
            max_value=100,
            unit="%",
            warning_start=0,
            warning_end=20,
            warning_color="#ff0000",
        )
        layout.addWidget(self.level_gauge)
        
        # Flow Rate gauge
        self.flow_gauge = AnalogGauge(
            "Flow Rate",
            min_value=0,
            max_value=500,
            unit="ml/min",
        )
        layout.addWidget(self.flow_gauge)
        
        # Fuel Pressure gauge
        self.fuel_pressure_gauge = AnalogGauge(
            "Fuel Pressure",
            min_value=0,
            max_value=100,
            unit="psi",
            warning_start=0,
            warning_end=40,
            warning_color="#ff0000",
        )
        layout.addWidget(self.fuel_pressure_gauge)
        
        # AFR/Lambda gauge
        self.afr_gauge = AnalogGauge(
            "AFR / Lambda",
            min_value=3.5,
            max_value=6.5,
            unit="",
        )
        layout.addWidget(self.afr_gauge)
        
        # EGT gauge (per cylinder average)
        self.egt_gauge = AnalogGauge(
            "EGT Avg",
            min_value=400,
            max_value=1200,
            unit="°C",
            warning_start=1100,
            warning_end=1200,
            warning_color="#ff0000",
        )
        layout.addWidget(self.egt_gauge)
        
        self.boost_gauge = AnalogGauge(
            "Boost",
            min_value=0,
            max_value=45,
            unit="psi",
            warning_start=35,
            warning_end=45,
            warning_color="#ff0000",
        )
        layout.addWidget(self.boost_gauge)
        
        self.coolant_gauge = AnalogGauge(
            "Coolant Temp",
            min_value=60,
            max_value=240,
            unit="°F",
            warning_start=210,
            warning_end=240,
            warning_color="#ff0000",
        )
        layout.addWidget(self.coolant_gauge)
        
        self.diagnostics_indicator = QLabel("Diagnostics: All sensors nominal")
        self.diagnostics_indicator.setStyleSheet("color: #00ff80; font-weight: bold;")
        layout.addWidget(self.diagnostics_indicator)
        
        layout.addStretch()
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with tabbed methanol maps."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabbed interface for different maps
        self.center_tabs = QTabWidget()
        self.center_tabs.setStyleSheet("""
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
        
        # VE Map / Base Fuel Map
        self.center_tabs.addTab(self._create_ve_map(), "VE / Base Fuel Map")
        
        # Target AFR/Lambda Map
        self.center_tabs.addTab(self._create_afr_lambda_map(), "Target AFR/Lambda")
        
        # Ignition Timing Map
        self.center_tabs.addTab(self._create_ignition_timing_map(), "Ignition Timing")
        
        # Methanol Injection Trigger/Flow Map
        self.center_tabs.addTab(self._create_injection_flow_map(), "Injection Flow Map")
        
        # Temperature Correction Maps
        self.center_tabs.addTab(self._create_temp_correction_maps(), "Temp Corrections")
        
        # Dynamic Control (RPM/Load strategy)
        self.center_tabs.addTab(self._create_dynamic_control_tab(), "Dynamic Control")
        
        # Diagnostics / Faults
        self.center_tabs.addTab(self._create_diagnostics_tab(), "Diagnostics")
        
        # Environment Compensation
        self.center_tabs.addTab(self._create_environment_tab(), "Environment")
        
        # Data Logging
        self.center_tabs.addTab(self._create_logging_tab(), "Data Logging")
        
        layout.addWidget(self.center_tabs)
        return panel
    
    def _create_ve_map(self) -> QWidget:
        """Create VE / Base Fuel Map for methanol."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Volumetric Efficiency / Base Fuel Map (vs RPM & MAP) - Methanol requires ~2.3x more fuel")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Use VETableWidget for consistency
        self.ve_table = VETableWidget()
        layout.addWidget(self.ve_table, stretch=1)
        return tab
    
    def _create_afr_lambda_map(self) -> QWidget:
        """Create Target AFR/Lambda Map for methanol."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Target AFR/Lambda Map (Methanol Stoich: 6.4:1, Lambda 1.0) - Racing: 3.5-5.0:1 (0.5-0.78 lambda)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # RPM
        table.setColumnCount(10)  # MAP/Load
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
        
        map_values = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
        for col, map_val in enumerate(map_values):
            item = QTableWidgetItem(f"{map_val}kPa")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with methanol AFR targets (richer for high power, stoichiometric at idle)
        for row in range(10):
            for col in range(10):
                # Methanol: Stoich 6.4:1, Racing 3.5-5.0:1
                if rpm_values[row] < 2000 or map_values[col] < 60:
                    afr = 6.4  # Stoichiometric at idle/low load
                else:
                    # Richer at high load/RPM for cooling
                    afr = 6.4 - (map_values[col] / 200) * 2.5 - (rpm_values[row] / 10000) * 0.5
                    afr = max(3.5, min(6.4, afr))  # Range: 3.5-6.4
                
                item = QTableWidgetItem(f"{afr:.2f}:1")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if afr < 4.0:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very rich
                elif afr < 5.0:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Rich
                elif afr < 6.0:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Stoich
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_ignition_timing_map(self) -> QWidget:
        """Create Ignition Timing Map optimized for methanol."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Map (vs RPM & MAP) - Methanol allows more advance due to high octane")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # RPM
        table.setColumnCount(10)  # MAP
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
        
        map_values = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
        for col, map_val in enumerate(map_values):
            item = QTableWidgetItem(f"{map_val}kPa")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        rpm_values = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with timing values (more advance for methanol due to high octane)
        for row in range(10):
            for col in range(10):
                base_timing = 35.0  # Higher base timing for methanol
                # More advance at higher RPM, slight retard at very high MAP
                timing = base_timing + (rpm_values[row] / 10000) * 15 - ((map_values[col] - 100) / 100) * 3
                timing = max(10.0, min(50.0, timing))  # Range: 10-50 degrees
                
                item = QTableWidgetItem(f"{timing:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing > 40:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Very advanced
                elif timing > 30:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Advanced
                elif timing > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Retarded
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_injection_flow_map(self) -> QWidget:
        """Create Methanol Injection Trigger/Flow Map."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Methanol Injection Trigger/Flow Map (vs Boost/EGT/TPS) - Pulsing vs Full Spray")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(8)  # Trigger basis (Boost, EGT, TPS)
        table.setColumnCount(10)  # Values
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
        
        # Columns: Boost (psi) or EGT (°C) or TPS (%)
        boost_values = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        for col, boost in enumerate(boost_values):
            item = QTableWidgetItem(f"{boost}psi")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        trigger_bases = ["Boost (psi)", "EGT (°C)", "TPS (%)", "Boost (psi)", "EGT (°C)", "TPS (%)", "Boost (psi)", "EGT (°C)"]
        for row, base in enumerate(trigger_bases):
            item = QTableWidgetItem(base)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with flow rates (ml/min) or duty cycle (%)
        for row in range(8):
            for col in range(10):
                # Progressive flow based on trigger value
                flow = (boost_values[col] / 50) * 500 + (row * 50)  # 0-500 ml/min
                flow = max(0, min(500, flow))
                
                item = QTableWidgetItem(f"{flow:.0f}ml/min")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if flow > 400:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Full spray
                elif flow > 250:
                    item.setBackground(QBrush(QColor("#ff8000")))  # High flow
                elif flow > 100:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Low flow
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_temp_correction_maps(self) -> QWidget:
        """Create Temperature Correction Maps (Coolant and Air Temp)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for Coolant and Air Temp corrections
        temp_tabs = QTabWidget()
        temp_tabs.setStyleSheet("""
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
        
        # Coolant Temperature Correction
        coolant_tab = self._create_coolant_correction_table()
        temp_tabs.addTab(coolant_tab, "Coolant Temp Correction")
        
        # Air Temperature Correction
        air_temp_tab = self._create_air_temp_correction_table()
        temp_tabs.addTab(air_temp_tab, "Air Temp Correction")
        
        layout.addWidget(temp_tabs)
        return tab
    
    def _create_dynamic_control_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Dynamic Methanol Control (Duty % vs RPM & Load)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)
        table.setColumnCount(8)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(320)
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
        rpm_values = ["2k", "3k", "4k", "5k", "6k", "7k", "8k", "9k"]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(rpm)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        load_values = ["20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%", "Overrun"]
        for row, load in enumerate(load_values):
            item = QTableWidgetItem(load)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        for row in range(10):
            for col in range(8):
                duty = min(100, max(0, (row * 8) + (col * 6)))
                item = QTableWidgetItem(f"{duty:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if duty > 80:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif duty > 50:
                    item.setBackground(QBrush(QColor("#ff8000")))
                elif duty > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))
                table.setItem(row, col, item)
        layout.addWidget(table)
        return tab
    
    def _create_diagnostics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Diagnostics & Fault Codes")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.fault_table = QTableWidget()
        self.fault_table.setColumnCount(2)
        self.fault_table.setHorizontalHeaderLabels(["Timestamp", "Message"])
        self.fault_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.fault_table.verticalHeader().setVisible(False)
        self.fault_table.setMinimumHeight(220)
        self.fault_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(self.fault_table)
        
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Codes")
        clear_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        clear_btn.clicked.connect(self._clear_faults)
        btn_row.addWidget(clear_btn)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        refresh_btn.clicked.connect(self._refresh_fault_table)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        return tab
    
    def _create_environment_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Environmental Compensation")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        labels = ["Ambient Temp (°C):", "Humidity (%):", "Baro (kPa):", "Density Altitude (ft):"]
        self.env_inputs = []
        defaults = [25.0, 40.0, 101.3, 500.0]
        for idx, label in enumerate(labels):
            grid.addWidget(QLabel(label), idx, 0)
            spin = QDoubleSpinBox()
            spin.setRange(-40, 2000 if idx == 3 else 150)
            spin.setValue(defaults[idx])
            spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
            spin.valueChanged.connect(self._update_environment_summary)
            grid.addWidget(spin, idx, 1)
            self.env_inputs.append(spin)
        layout.addLayout(grid)
        
        self.environment_summary = QLabel("Density Correction: 0.0% | Suggested Trim: 0.0° timing / +0% fuel")
        self.environment_summary.setWordWrap(True)
        self.environment_summary.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        layout.addWidget(self.environment_summary)
        self._update_environment_summary()
        return tab
    
    def _create_logging_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Session Data Logging")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels(["Time", "RPM", "Boost", "AFR", "Duty", "Fault"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setMinimumHeight(220)
        self.log_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(self.log_table)
        
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Logs")
        clear_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 6px 12px;")
        clear_btn.clicked.connect(self._clear_session_logs)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)
        return tab
    
    def _change_mode(self, mode: str) -> None:
        self.current_mode = mode
        descriptions = {
            "Street": "Street mode • balanced cooling",
            "Race": "Race mode • aggressive spray and timing",
            "Kill": "Kill mode • max flow & timing, requires race fuel",
        }
        if self.mode_status_label:
            self.mode_status_label.setText(descriptions.get(mode, mode))
        # Adjust defaults subtly
        if hasattr(self, "req_fuel_mult"):
            base = 2.3 if mode == "Street" else 2.5 if mode == "Race" else 2.7
            self.req_fuel_mult.setValue(base)
        if hasattr(self, "base_timing"):
            timing = 32 if mode == "Street" else 36 if mode == "Race" else 38
            self.base_timing.setValue(timing)
    
    def _clear_faults(self) -> None:
        self._fault_log.clear()
        self.failsafe_triggered = False
        if self.diagnostics_indicator:
            self.diagnostics_indicator.setText("Diagnostics: All sensors nominal")
            self.diagnostics_indicator.setStyleSheet("color: #00ff80; font-weight: bold;")
        if self.failsafe_label:
            self.failsafe_label.setText("Failsafe: Armed")
            self.failsafe_label.setStyleSheet("color: #00ff80; font-weight: bold;")
        self._refresh_fault_table()
    
    def _refresh_fault_table(self) -> None:
        if not self.fault_table:
            return
        self.fault_table.setRowCount(len(self._fault_log))
        for row, entry in enumerate(reversed(self._fault_log)):
            timestamp, message = entry.split("|", 1)
            time_item = QTableWidgetItem(timestamp)
            msg_item = QTableWidgetItem(message)
            self.fault_table.setItem(row, 0, time_item)
            self.fault_table.setItem(row, 1, msg_item)
    
    def _record_fault(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self._fault_log.append(f"{timestamp}|{message}")
        self._refresh_fault_table()
        if self.diagnostics_indicator:
            self.diagnostics_indicator.setText(f"Diagnostics: {message}")
            self.diagnostics_indicator.setStyleSheet("color: #ffaa00; font-weight: bold;")
    
    def _log_session_sample(self, data: Dict[str, float], fault_text: str = "") -> None:
        sample = {
            "time": time.strftime("%H:%M:%S"),
            "rpm": data.get("RPM", data.get("Engine_RPM", 0)),
            "boost": data.get("Boost_Pressure", 0),
            "afr": data.get("AFR", data.get("lambda_value", 1.0) * 6.4),
            "duty": data.get("meth_duty", data.get("MethInjectionDuty", 0)),
            "fault": fault_text,
        }
        self._session_logs.append(sample)
        if self.log_table:
            self.log_table.setRowCount(len(self._session_logs))
            for row, entry in enumerate(reversed(self._session_logs)):
                self.log_table.setItem(row, 0, QTableWidgetItem(entry["time"]))
                self.log_table.setItem(row, 1, QTableWidgetItem(f"{entry['rpm']:.0f}"))
                self.log_table.setItem(row, 2, QTableWidgetItem(f"{entry['boost']:.1f}"))
                self.log_table.setItem(row, 3, QTableWidgetItem(f"{entry['afr']:.2f}"))
                self.log_table.setItem(row, 4, QTableWidgetItem(f"{entry['duty']:.0f}%"))
                self.log_table.setItem(row, 5, QTableWidgetItem(entry["fault"]))
    
    def _export_session_logs(self) -> None:
        if not self._session_logs:
            QMessageBox.information(self, "No Logs", "No methanol session logs available.")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Methanol Logs",
            "methanol_logs.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["Time", "RPM", "Boost (psi)", "AFR", "Duty (%)", "Fault"])
                for entry in self._session_logs:
                    writer.writerow([
                        entry["time"],
                        f"{entry['rpm']:.0f}",
                        f"{entry['boost']:.1f}",
                        f"{entry['afr']:.2f}",
                        f"{entry['duty']:.0f}",
                        entry["fault"],
                    ])
            QMessageBox.information(self, "Export Complete", f"Logs exported to:\n{filename}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Unable to export logs:\n{exc}")
    
    def _clear_session_logs(self) -> None:
        self._session_logs.clear()
        if self.log_table:
            self.log_table.setRowCount(0)
    
    def _update_environment_summary(self) -> None:
        if not self.env_inputs or not self.environment_summary:
            return
        temp, humidity, baro, density_alt = [spin.value() for spin in self.env_inputs]
        density_correction = (density_alt / 1000.0) * 1.5 + max(0, (temp - 25) * 0.2)
        trim_timing = max(-2.0, min(2.0, density_correction * 0.05))
        fuel_trim = max(-5.0, min(10.0, density_correction * 0.5))
        self.environment_summary.setText(
            f"Density Correction: {density_correction:.1f}% | Suggested Trim: {trim_timing:+.2f}° timing / {fuel_trim:+.1f}% fuel"
        )
    
    def _create_coolant_correction_table(self) -> QWidget:
        """Create coolant temperature correction table."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Coolant Temperature Correction (Fuel & Timing vs Coolant Temp)")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(2)  # Fuel correction, Timing correction
        table.setColumnCount(10)  # Temperature ranges
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(200)
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
        
        temp_values = [-20, -10, 0, 10, 20, 40, 60, 80, 90, 110]
        for col, temp in enumerate(temp_values):
            item = QTableWidgetItem(f"{temp}°C")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        correction_types = ["Fuel Correction (%)", "Timing Correction (°)"]
        for row, corr_type in enumerate(correction_types):
            item = QTableWidgetItem(corr_type)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with correction values (more fuel/timing at cold temps)
        for row in range(2):
            for col in range(10):
                if row == 0:  # Fuel correction
                    # More fuel at cold temps (methanol difficult to start cold)
                    fuel_corr = max(0, (temp_values[col] < 20) * (20 - temp_values[col]) * 2)
                    fuel_corr = min(100, fuel_corr)
                    item = QTableWidgetItem(f"+{fuel_corr:.0f}%")
                else:  # Timing correction
                    # Retard timing at very cold temps
                    timing_corr = max(-10, (temp_values[col] < 0) * (temp_values[col] * 0.5))
                    item = QTableWidgetItem(f"{timing_corr:.1f}°")
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if abs(float(item.text().replace('+', '').replace('%', '').replace('°', ''))) > 50:
                    item.setBackground(QBrush(QColor("#ff0000")))
                elif abs(float(item.text().replace('+', '').replace('%', '').replace('°', ''))) > 20:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_air_temp_correction_table(self) -> QWidget:
        """Create air temperature correction table."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Air Temperature Correction (Fuel & Timing vs IAT)")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(2)  # Fuel correction, Timing correction
        table.setColumnCount(10)  # Temperature ranges
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(200)
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
        
        iat_values = [-10, 0, 10, 20, 30, 40, 50, 60, 70, 80]
        for col, iat in enumerate(iat_values):
            item = QTableWidgetItem(f"{iat}°C")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        correction_types = ["Fuel Correction (%)", "Timing Correction (°)"]
        for row, corr_type in enumerate(correction_types):
            item = QTableWidgetItem(corr_type)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with correction values
        for row in range(2):
            for col in range(10):
                if row == 0:  # Fuel correction
                    # Slight enrichment at high IAT
                    fuel_corr = max(0, (iat_values[col] - 30) * 0.5)
                    fuel_corr = min(20, fuel_corr)
                    item = QTableWidgetItem(f"+{fuel_corr:.1f}%")
                else:  # Timing correction
                    # Retard timing at high IAT
                    timing_corr = max(-5, (iat_values[col] - 50) * 0.2)
                    item = QTableWidgetItem(f"{timing_corr:.1f}°")
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if abs(float(item.text().replace('+', '').replace('%', '').replace('°', ''))) > 10:
                    item.setBackground(QBrush(QColor("#ff8000")))
                else:
                    item.setBackground(QBrush(QColor("#0080ff")))
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
        
    def _add_right_settings(self, layout: QVBoxLayout) -> None:
        """Add right panel settings."""
        # Fuel Strategy
        fuel_strategy_group = QGroupBox("Fuel Strategy")
        fuel_strategy_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        fuel_strategy_layout = QVBoxLayout()
        
        fuel_strategy_layout.addWidget(QLabel("Target AFR (Methanol Stoich: 6.4:1):"))
        self.target_afr = QDoubleSpinBox()
        self.target_afr.setRange(3.5, 6.5)
        self.target_afr.setValue(5.0)
        self.target_afr.setSingleStep(0.1)
        self.target_afr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_strategy_layout.addWidget(self.target_afr)
        
        fuel_strategy_layout.addWidget(QLabel("Target Lambda:"))
        self.target_lambda = QDoubleSpinBox()
        self.target_lambda.setRange(0.5, 1.0)
        self.target_lambda.setValue(0.78)
        self.target_lambda.setSingleStep(0.01)
        self.target_lambda.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_strategy_layout.addWidget(self.target_lambda)
        
        fuel_strategy_layout.addWidget(QLabel("Req_Fuel Multiplier (Methanol ~2.3x):"))
        self.req_fuel_mult = QDoubleSpinBox()
        self.req_fuel_mult.setRange(1.0, 5.0)
        self.req_fuel_mult.setValue(2.3)
        self.req_fuel_mult.setSingleStep(0.1)
        self.req_fuel_mult.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_strategy_layout.addWidget(self.req_fuel_mult)
        
        fuel_strategy_group.setLayout(fuel_strategy_layout)
        layout.addWidget(fuel_strategy_group)
        
        # Injector Characterization
        injector_group = QGroupBox("Injector Characterization")
        injector_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        injector_layout = QVBoxLayout()
        
        injector_layout.addWidget(QLabel("Injector Size (cc/min):"))
        self.injector_size = QSpinBox()
        self.injector_size.setRange(100, 5000)
        self.injector_size.setValue(2000)
        self.injector_size.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        injector_layout.addWidget(self.injector_size)
        
        injector_layout.addWidget(QLabel("Dead Time (ms):"))
        self.dead_time = QDoubleSpinBox()
        self.dead_time.setRange(0.1, 5.0)
        self.dead_time.setValue(1.2)
        self.dead_time.setSingleStep(0.1)
        self.dead_time.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        injector_layout.addWidget(self.dead_time)
        
        injector_layout.addWidget(QLabel("Fuel Pressure (psi):"))
        self.fuel_pressure_setting = QDoubleSpinBox()
        self.fuel_pressure_setting.setRange(0, 100)
        self.fuel_pressure_setting.setValue(43.5)
        self.fuel_pressure_setting.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        injector_layout.addWidget(self.fuel_pressure_setting)
        
        injector_group.setLayout(injector_layout)
        layout.addWidget(injector_group)
        
        # Ignition Timing
        timing_group = QGroupBox("Ignition Timing")
        timing_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        timing_layout = QVBoxLayout()
        
        timing_layout.addWidget(QLabel("Base Timing Advance (°):"))
        self.base_timing = QDoubleSpinBox()
        self.base_timing.setRange(0, 50)
        self.base_timing.setValue(35.0)
        self.base_timing.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        timing_layout.addWidget(self.base_timing)
        
        self.transition_timing_enabled = QCheckBox("Fuel Transition Timing Trim")
        self.transition_timing_enabled.setStyleSheet("color: #ffffff;")
        timing_layout.addWidget(self.transition_timing_enabled)
        
        timing_layout.addWidget(QLabel("Transition Trim Range (°):"))
        self.transition_trim = QDoubleSpinBox()
        self.transition_trim.setRange(-10, 10)
        self.transition_trim.setValue(0.0)
        self.transition_trim.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        timing_layout.addWidget(self.transition_trim)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # Boost Control (for forced induction)
        boost_group = QGroupBox("Boost Control (Forced Induction)")
        boost_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        boost_layout = QVBoxLayout()
        
        boost_layout.addWidget(QLabel("Boost Control Basis:"))
        self.boost_basis = QComboBox()
        self.boost_basis.addItems(["By Gear", "By Speed (MPH)", "By Time", "Fixed"])
        self.boost_basis.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.boost_basis)
        
        boost_layout.addWidget(QLabel("Max Boost (psi):"))
        self.max_boost = QDoubleSpinBox()
        self.max_boost.setRange(0, 60)
        self.max_boost.setValue(40.0)
        self.max_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        boost_layout.addWidget(self.max_boost)
        
        boost_group.setLayout(boost_layout)
        layout.addWidget(boost_group)
        
        # Sensors and Failsafes
        sensors_group = QGroupBox("Sensors & Failsafes")
        sensors_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        sensors_layout = QVBoxLayout()
        
        sensors_layout.addWidget(QLabel("Wideband O2 Sensor Type:"))
        self.wideband_type = QComboBox()
        self.wideband_type.addItems(["Methanol-Compatible", "Gasoline (Lambda Only)", "Custom"])
        self.wideband_type.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensors_layout.addWidget(self.wideband_type)
        
        sensors_layout.addWidget(QLabel("Min Fuel Pressure (psi):"))
        self.min_fuel_pressure = QDoubleSpinBox()
        self.min_fuel_pressure.setRange(0, 100)
        self.min_fuel_pressure.setValue(40.0)
        self.min_fuel_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensors_layout.addWidget(self.min_fuel_pressure)
        
        sensors_layout.addWidget(QLabel("Min Fuel Flow (L/min):"))
        self.min_fuel_flow = QDoubleSpinBox()
        self.min_fuel_flow.setRange(0, 50)
        self.min_fuel_flow.setValue(2.0)
        self.min_fuel_flow.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensors_layout.addWidget(self.min_fuel_flow)
        
        sensors_layout.addWidget(QLabel("Min Tank Level (%):"))
        self.min_tank_level = QDoubleSpinBox()
        self.min_tank_level.setRange(0, 50)
        self.min_tank_level.setValue(10.0)
        self.min_tank_level.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensors_layout.addWidget(self.min_tank_level)
        
        sensors_layout.addWidget(QLabel("Max EGT (°C):"))
        self.max_egt = QSpinBox()
        self.max_egt.setRange(800, 1400)
        self.max_egt.setValue(1100)
        self.max_egt.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        sensors_layout.addWidget(self.max_egt)
        
        self.failsafe_enabled = QCheckBox("Failsafe: Switch to Safe Map")
        self.failsafe_enabled.setChecked(True)
        self.failsafe_enabled.setStyleSheet("color: #ffffff;")
        sensors_layout.addWidget(self.failsafe_enabled)
        
        sensors_group.setLayout(sensors_layout)
        layout.addWidget(sensors_group)
        
        # Methanol Injection (existing)
        injection_group = QGroupBox("Methanol Injection")
        injection_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        injection_layout = QVBoxLayout()
        
        self.injection_enabled = QCheckBox("Injection Enabled")
        self.injection_enabled.setStyleSheet("color: #ffffff;")
        injection_layout.addWidget(self.injection_enabled)
        
        injection_layout.addWidget(QLabel("Activation Boost (psi):"))
        self.activation_boost = QDoubleSpinBox()
        self.activation_boost.setRange(0, 50)
        self.activation_boost.setValue(10)
        self.activation_boost.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        injection_layout.addWidget(self.activation_boost)
        
        injection_group.setLayout(injection_layout)
        layout.addWidget(injection_group)
        
    def setup_ui(self) -> None:
        """Override setup_ui to add comprehensive graphs panel."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges column
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Main data table/visualization
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings and visualization
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Comprehensive graphs panel
        graphs_panel = self._create_graphs_panel()
        main_layout.addWidget(graphs_panel, stretch=1)
        
        # Import/Export bar
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
    
    def _create_graphs_panel(self) -> QWidget:
        """Create comprehensive real-time monitoring graphs panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Real-Time Monitoring & Datalogging")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Create tabbed graphs
        graph_tabs = QTabWidget()
        graph_tabs.setStyleSheet("""
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
        
        # VE / Fuel Map Graph
        ve_graph = RealTimeGraph()
        ve_graph.setMinimumHeight(200)
        graph_tabs.addTab(ve_graph, "VE / Fuel Map")
        self.ve_graph = ve_graph
        
        # AFR / Lambda Graph
        afr_graph = RealTimeGraph()
        afr_graph.setMinimumHeight(200)
        graph_tabs.addTab(afr_graph, "AFR / Lambda")
        self.afr_graph = afr_graph
        
        # Ignition Timing Graph
        timing_graph = RealTimeGraph()
        timing_graph.setMinimumHeight(200)
        graph_tabs.addTab(timing_graph, "Ignition Timing")
        self.timing_graph = timing_graph
        
        # Pressure & Flow Graph
        pressure_graph = RealTimeGraph()
        pressure_graph.setMinimumHeight(200)
        graph_tabs.addTab(pressure_graph, "Pressure & Flow")
        self.pressure_graph = pressure_graph
        
        # EGT per Cylinder Graph
        egt_graph = RealTimeGraph()
        egt_graph.setMinimumHeight(200)
        graph_tabs.addTab(egt_graph, "EGT per Cylinder")
        self.egt_graph = egt_graph
        
        layout.addWidget(graph_tabs)
        return panel
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update methanol tab with telemetry data."""
        duty = data.get("meth_duty", data.get("MethInjectionDuty", 0))
        level = data.get("methanol_level", 75)
        flow = data.get("methanol_flow", 0)
        fuel_pressure = data.get("Fuel_Pressure", 45)
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 6.4)  # Methanol AFR
        egt = data.get("EGT", data.get("EGT_Avg", 800))
        coolant = data.get("Coolant_Temp", 180)
        boost = data.get("Boost_Pressure", 0)
        
        self.duty_gauge.set_value(duty)
        self.level_gauge.set_value(level)
        self.flow_gauge.set_value(flow)
        if hasattr(self, 'fuel_pressure_gauge'):
            self.fuel_pressure_gauge.set_value(fuel_pressure)
        if hasattr(self, 'afr_gauge'):
            self.afr_gauge.set_value(afr)
        if hasattr(self, 'egt_gauge'):
            self.egt_gauge.set_value(egt)
        if hasattr(self, "boost_gauge"):
            self.boost_gauge.set_value(boost)
        if hasattr(self, "coolant_gauge"):
            self.coolant_gauge.set_value(coolant)
        
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = data.get("Boost_Pressure", 0) * 6.895
        lambda_val = afr / 6.4  # Convert methanol AFR to lambda
        timing = data.get("Ignition_Timing", 35)
        faults: List[str] = []
        min_level = getattr(self, "min_tank_level", None)
        if min_level and level < min_level.value():
            faults.append("Tank level low")
        min_pressure = getattr(self, "min_fuel_pressure", None)
        if min_pressure and fuel_pressure < min_pressure.value():
            faults.append("Fuel pressure low")
        min_flow = getattr(self, "min_fuel_flow", None)
        if min_flow and duty > 25 and flow < min_flow.value() * 100:
            faults.append("Flow below target")
        if coolant > 220:
            faults.append("Coolant high")
        fault_text = " | ".join(faults)
        if faults:
            self._record_fault(fault_text)
            if self.failsafe_enabled.isChecked():
                self.failsafe_triggered = True
                if self.failsafe_label:
                    self.failsafe_label.setText("Failsafe: Safe map active")
                    self.failsafe_label.setStyleSheet("color: #ff3b30; font-weight: bold;")
        else:
            if self.diagnostics_indicator:
                self.diagnostics_indicator.setText("Diagnostics: All sensors nominal")
                self.diagnostics_indicator.setStyleSheet("color: #00ff80; font-weight: bold;")
            if self.failsafe_label and not self.failsafe_triggered:
                self.failsafe_label.setText("Failsafe: Armed")
                self.failsafe_label.setStyleSheet("color: #00ff80; font-weight: bold;")
            self.failsafe_triggered = False
        self._log_session_sample(data, fault_text)
        
        # Update graphs
        if hasattr(self, 've_graph'):
            ve = data.get("VE", 80)
            self.ve_graph.update_data(rpm, map_val, ve, duty)
        
        if hasattr(self, 'afr_graph'):
            self.afr_graph.update_data(rpm, lambda_val, afr, 0)
        
        if hasattr(self, 'timing_graph'):
            self.timing_graph.update_data(rpm, timing, map_val, 0)
        
        if hasattr(self, 'pressure_graph'):
            self.pressure_graph.update_data(rpm, fuel_pressure, flow, duty)
        
        if hasattr(self, 'egt_graph'):
            # EGT per cylinder (simulated as average + variation)
            egt_cyl1 = egt + data.get("EGT_Cyl1_Offset", 0)
            egt_cyl2 = egt + data.get("EGT_Cyl2_Offset", 0)
            egt_cyl3 = egt + data.get("EGT_Cyl3_Offset", 0)
            egt_cyl4 = egt + data.get("EGT_Cyl4_Offset", 0)
            self.egt_graph.update_data(rpm, egt_cyl1, egt_cyl2, egt_cyl3)
        
        # Update base realtime graph
        if hasattr(self, 'realtime_graph'):
            self.realtime_graph.update_data(rpm, map_val, afr, duty)


class NitroMethaneTab(ModuleTab):
    """Nitro Methane settings tab with full ECU tuning interface."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self._afr_history: deque[float] = deque(maxlen=120)
        self._damage_score: float = 15.0
        self._soft_rev_state: str = "Idle"
        self.mix_sim_slider = None
        self.mix_power_label = None
        self.mix_timing_label = None
        self.mix_status_label = None
        super().__init__("Nitro Methane", parent)
    
    def setup_ui(self) -> None:
        """Override setup_ui to add comprehensive graphs panel."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left: Gauges column
        left_panel = self._create_gauges_panel()
        content_layout.addWidget(left_panel, stretch=0)
        
        # Center: Main data table/visualization
        center_panel = self._create_center_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Settings and visualization
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Comprehensive graphs panel
        graphs_panel = self._create_graphs_panel()
        main_layout.addWidget(graphs_panel, stretch=1)
        
        # Import/Export bar
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
        
    def _create_gauges_panel(self) -> QWidget:
        """Create nitro methane-specific gauges."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Nitro Percentage gauge
        self.nitro_gauge = AnalogGauge(
            "Nitro Percentage",
            min_value=0,
            max_value=100,
            unit="%",
            warning_start=80,
            warning_end=100,
            warning_color="#ff0000",
        )
        layout.addWidget(self.nitro_gauge)
        
        # Timing Adjustment gauge
        self.timing_gauge = AnalogGauge(
            "Timing Adjustment",
            min_value=-20,
            max_value=20,
            unit="deg",
        )
        layout.addWidget(self.timing_gauge)
        
        # System Status gauge
        self.status_gauge = AnalogGauge(
            "System Status",
            min_value=0,
            max_value=100,
            unit="%",
        )
        layout.addWidget(self.status_gauge)
        
        # Nitro Boost / Pressure simulator
        self.nitro_boost_gauge = AnalogGauge(
            "Nitro Boost",
            min_value=0,
            max_value=80,
            unit="psi",
            warning_start=60,
            warning_end=80,
            warning_color="#ff4500",
        )
        layout.addWidget(self.nitro_boost_gauge)
        
        # Engine Damage / Stress gauge
        self.damage_gauge = AnalogGauge(
            "Engine Stress",
            min_value=0,
            max_value=100,
            unit="%",
            warning_start=70,
            warning_end=100,
            warning_color="#ff0000",
        )
        layout.addWidget(self.damage_gauge)
        
        # Lambda gauge
        self.lambda_gauge = AnalogGauge(
            "Lambda",
            min_value=0.7,
            max_value=1.0,
            unit="",
        )
        layout.addWidget(self.lambda_gauge)
        
        # Fuel Pressure gauge
        self.fuel_pressure_gauge = AnalogGauge(
            "Fuel Pressure",
            min_value=0,
            max_value=150,
            unit="psi",
            warning_start=0,
            warning_end=80,
            warning_color="#ff0000",
        )
        layout.addWidget(self.fuel_pressure_gauge)
        
        # Peak Cylinder Pressure gauge
        self.peak_pressure_gauge = AnalogGauge(
            "Peak Cyl Pressure",
            min_value=0,
            max_value=5000,
            unit="psi",
            warning_start=4000,
            warning_end=5000,
            warning_color="#ff0000",
        )
        layout.addWidget(self.peak_pressure_gauge)
        
        # EGT gauge
        self.egt_gauge = AnalogGauge(
            "EGT",
            min_value=800,
            max_value=1600,
            unit="°C",
            warning_start=1400,
            warning_end=1600,
            warning_color="#ff0000",
        )
        layout.addWidget(self.egt_gauge)
        
        # CHT gauge
        self.cht_gauge = AnalogGauge(
            "CHT",
            min_value=100,
            max_value=300,
            unit="°C",
            warning_start=250,
            warning_end=300,
            warning_color="#ff0000",
        )
        layout.addWidget(self.cht_gauge)
        
        # Soft limiter + audio cue labels
        self.soft_rev_label = QLabel("Soft Rev Limiter: Idle")
        self.soft_rev_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
        layout.addWidget(self.soft_rev_label)
        
        self.audio_indicator = QLabel("Nitro Cue: ---")
        self.audio_indicator.setStyleSheet("color: #5f6368; font-size: 11px;")
        layout.addWidget(self.audio_indicator)
        
        layout.addStretch()
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with tabbed nitro methane maps and calculator."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabbed interface for different maps and calculator
        self.center_tabs = QTabWidget()
        self.center_tabs.setStyleSheet("""
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
        
        # VE Tables (Alpha-N or MAP/TPS)
        self.center_tabs.addTab(self._create_ve_map(), "VE Tables")
        
        # Lambda Map (Lambda-based tuning)
        self.center_tabs.addTab(self._create_lambda_map(), "Lambda Map")
        
        # Ignition Timing Map
        self.center_tabs.addTab(self._create_ignition_timing_map(), "Ignition Timing")
        
        # Multi-Stage Fueling/Timing
        self.center_tabs.addTab(self._create_multi_stage_map(), "Multi-Stage")
        
        # Nitro Methane Calculator
        self.center_tabs.addTab(self._create_nitro_calculator(), "Nitro Calculator")
        
        layout.addWidget(self.center_tabs)
        return panel
    
    def _create_ve_map(self) -> QWidget:
        """Create high-resolution VE tables for nitromethane."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for Alpha-N and MAP/TPS
        ve_tabs = QTabWidget()
        ve_tabs.setStyleSheet("""
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
        
        # Alpha-N VE Table
        alpha_n_tab = QWidget()
        alpha_n_layout = QVBoxLayout(alpha_n_tab)
        alpha_n_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Alpha-N VE Table (vs RPM & TPS) - High Resolution for Nitromethane")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        alpha_n_layout.addWidget(title)
        
        self.ve_alpha_n = VETableWidget()
        alpha_n_layout.addWidget(self.ve_alpha_n, stretch=1)
        ve_tabs.addTab(alpha_n_tab, "Alpha-N")
        
        # MAP/TPS VE Table
        map_tps_tab = QWidget()
        map_tps_layout = QVBoxLayout(map_tps_tab)
        map_tps_layout.setContentsMargins(10, 10, 10, 10)
        
        title2 = QLabel("MAP/TPS VE Table (vs RPM & MAP) - High Resolution for Nitromethane")
        title2.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        map_tps_layout.addWidget(title2)
        
        self.ve_map_tps = VETableWidget()
        map_tps_layout.addWidget(self.ve_map_tps, stretch=1)
        ve_tabs.addTab(map_tps_tab, "MAP/TPS")
        
        layout.addWidget(ve_tabs)
        return tab
    
    def _create_lambda_map(self) -> QWidget:
        """Create Lambda-based fuel map (Lambda 1.0 = stoichiometric for any fuel)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Lambda Map (vs RPM & Load) - Lambda 1.0 = Stoichiometric (Nitromethane ~1.7:1 AFR)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
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
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with lambda values (richer for cooling, stoichiometric at idle)
        for row in range(12):
            for col in range(12):
                if rpm_values[row] < 3000 or load_values[col] < 30:
                    lambda_val = 1.0  # Stoichiometric at idle/low load
                else:
                    # Richer at high load/RPM for cooling (nitromethane runs very rich)
                    lambda_val = 1.0 - (load_values[col] / 100) * 0.3 - (rpm_values[row] / 13000) * 0.1
                    lambda_val = max(0.7, min(1.0, lambda_val))  # Range: 0.7-1.0 (very rich)
                
                item = QTableWidgetItem(f"{lambda_val:.3f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if lambda_val < 0.75:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Very rich
                elif lambda_val < 0.85:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Rich
                elif lambda_val < 0.95:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Stoich
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_ignition_timing_map(self) -> QWidget:
        """Create ignition timing map with large advance curves for nitromethane."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Ignition Timing Map (vs RPM & Load) - Nitromethane burns slower, allows large advance")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
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
        
        rpm_values = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]
        for row, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with timing values (large advance curves for nitromethane)
        for row in range(12):
            for col in range(12):
                base_timing = 40.0  # High base timing for nitromethane
                # Large advance at higher RPM, slight retard at very high load
                timing = base_timing + (rpm_values[row] / 13000) * 25 - ((load_values[col] - 50) / 50) * 5
                timing = max(15.0, min(65.0, timing))  # Range: 15-65 degrees (large advance)
                
                item = QTableWidgetItem(f"{timing:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing > 55:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Very advanced
                elif timing > 45:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Advanced
                elif timing > 35:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Retarded
                
                table.setItem(row, col, item)
        
        layout.addWidget(table)
        return tab
    
    def _create_multi_stage_map(self) -> QWidget:
        """Create multi-stage fueling/timing map."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for Fueling and Timing stages
        stage_tabs = QTabWidget()
        stage_tabs.setStyleSheet("""
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
        
        # Primary/Secondary Injector Staging
        fueling_tab = QWidget()
        fueling_layout = QVBoxLayout(fueling_tab)
        fueling_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Injector Staging (Primary & Secondary) vs Boost/Time")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        fueling_layout.addWidget(title)
        
        table = QTableWidget()
        table.setRowCount(10)  # Boost/Time
        table.setColumnCount(8)  # RPM ranges
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
        
        rpm_ranges = ["2-4k", "4-6k", "6-8k", "8-10k", "10-12k", "12-14k", "14-16k", "16k+"]
        for col, rpm_range in enumerate(rpm_ranges):
            item = QTableWidgetItem(rpm_range)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setHorizontalHeaderItem(col, item)
        
        boost_values = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]
        for row, boost in enumerate(boost_values):
            item = QTableWidgetItem(f"{boost}psi")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setVerticalHeaderItem(row, item)
        
        # Fill with staging percentages
        for row in range(10):
            for col in range(8):
                # Secondary injectors activate at higher boost/RPM
                if boost_values[row] > 20:
                    secondary_pct = min(100, (boost_values[row] - 20) * 4 + col * 5)
                else:
                    secondary_pct = 0
                
                item = QTableWidgetItem(f"Sec: {secondary_pct:.0f}%")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if secondary_pct > 80:
                    item.setBackground(QBrush(QColor("#ff0000")))  # Full secondary
                elif secondary_pct > 50:
                    item.setBackground(QBrush(QColor("#ff8000")))  # High secondary
                elif secondary_pct > 20:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Moderate
                else:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Primary only
                
                table.setItem(row, col, item)
        
        fueling_layout.addWidget(table)
        stage_tabs.addTab(fueling_tab, "Fueling Stages")
        
        # Timing Stages
        timing_tab = QWidget()
        timing_layout = QVBoxLayout(timing_tab)
        timing_layout.setContentsMargins(10, 10, 10, 10)
        
        title2 = QLabel("Timing Stages vs Boost/Time")
        title2.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        timing_layout.addWidget(title2)
        
        table2 = QTableWidget()
        table2.setRowCount(10)
        table2.setColumnCount(8)
        table2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table2.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table2.setMinimumHeight(300)
        table2.setStyleSheet("""
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
        
        for col, rpm_range in enumerate(rpm_ranges):
            item = QTableWidgetItem(rpm_range)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table2.setHorizontalHeaderItem(col, item)
        
        for row, boost in enumerate(boost_values):
            item = QTableWidgetItem(f"{boost}psi")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table2.setVerticalHeaderItem(row, item)
        
        # Fill with timing adjustments
        for row in range(10):
            for col in range(8):
                timing_adj = 40 + (boost_values[row] / 45) * 10 - col * 2
                timing_adj = max(30, min(50, timing_adj))
                
                item = QTableWidgetItem(f"{timing_adj:.1f}°")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(QColor("#ffffff")))
                
                if timing_adj > 45:
                    item.setBackground(QBrush(QColor("#00ff00")))  # Very advanced
                elif timing_adj > 40:
                    item.setBackground(QBrush(QColor("#0080ff")))  # Advanced
                else:
                    item.setBackground(QBrush(QColor("#ff8000")))  # Moderate
                
                table2.setItem(row, col, item)
        
        timing_layout.addWidget(table2)
        stage_tabs.addTab(timing_tab, "Timing Stages")
        
        layout.addWidget(stage_tabs)
        return tab
    
    def _create_nitro_calculator(self) -> QWidget:
        """Create Nitro Methane Calculator with multiple tools."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-tabs for different calculator tools
        calc_tabs = QTabWidget()
        calc_tabs.setStyleSheet("""
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
        
        # Fuel Mixture Management
        calc_tabs.addTab(self._create_fuel_mixture_calculator(), "Fuel Mixture")
        
        # AFR/Jetting Calculator
        calc_tabs.addTab(self._create_afr_jetting_calculator(), "AFR & Jetting")
        
        # Performance Prediction
        calc_tabs.addTab(self._create_performance_prediction(), "Performance")
        
        # Fuel Mix Simulator
        calc_tabs.addTab(self._create_mix_simulator(), "Mix Simulator")
        
        # Data Logging Analysis
        calc_tabs.addTab(self._create_data_logging_analysis(), "Data Analysis")
        
        layout.addWidget(calc_tabs)
        return tab
    
    def _create_fuel_mixture_calculator(self) -> QWidget:
        """Create fuel mixture management calculator."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Fuel Mixture Management - Calculate precise mixing by weight or volume")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Input section
        input_group = QGroupBox("Input Parameters")
        input_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        input_layout = QVBoxLayout()
        
        input_layout.addWidget(QLabel("Total Quantity:"))
        quantity_layout = QHBoxLayout()
        self.total_quantity = QDoubleSpinBox()
        self.total_quantity.setRange(0.1, 1000.0)
        self.total_quantity.setValue(10.0)
        self.total_quantity.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        quantity_layout.addWidget(self.total_quantity)
        
        self.quantity_unit = QComboBox()
        self.quantity_unit.addItems(["Gallons", "Liters", "Pounds", "Kilograms"])
        self.quantity_unit.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        quantity_layout.addWidget(self.quantity_unit)
        input_layout.addLayout(quantity_layout)
        
        input_layout.addWidget(QLabel("Target Nitromethane %:"))
        self.target_nitro_pct = QDoubleSpinBox()
        self.target_nitro_pct.setRange(0, 100)
        self.target_nitro_pct.setValue(90.0)
        self.target_nitro_pct.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.target_nitro_pct)
        
        input_layout.addWidget(QLabel("Target Methanol %:"))
        self.target_methanol_pct = QDoubleSpinBox()
        self.target_methanol_pct.setRange(0, 100)
        self.target_methanol_pct.setValue(9.0)
        self.target_methanol_pct.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.target_methanol_pct)
        
        input_layout.addWidget(QLabel("Target Oil %:"))
        self.target_oil_pct = QDoubleSpinBox()
        self.target_oil_pct.setRange(0, 20)
        self.target_oil_pct.setValue(1.0)
        self.target_oil_pct.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.target_oil_pct)
        
        calculate_btn = QPushButton("Calculate Mixture")
        calculate_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 8px; font-weight: bold;")
        input_layout.addWidget(calculate_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Calculated Components")
        output_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        output_layout = QVBoxLayout()
        
        self.nitro_result = QLabel("Nitromethane: --")
        self.nitro_result.setStyleSheet("font-size: 11px; color: #00ff00;")
        output_layout.addWidget(self.nitro_result)
        
        self.methanol_result = QLabel("Methanol: --")
        self.methanol_result.setStyleSheet("font-size: 11px; color: #0080ff;")
        output_layout.addWidget(self.methanol_result)
        
        self.oil_result = QLabel("Oil: --")
        self.oil_result.setStyleSheet("font-size: 11px; color: #ff8000;")
        output_layout.addWidget(self.oil_result)
        
        self.specific_gravity = QLabel("Specific Gravity: --")
        self.specific_gravity.setStyleSheet("font-size: 11px; color: #ffffff;")
        output_layout.addWidget(self.specific_gravity)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Connect calculate button
        calculate_btn.clicked.connect(self._calculate_fuel_mixture)
        
        layout.addStretch()
        return tab
    
    def _calculate_fuel_mixture(self) -> None:
        """Calculate fuel mixture components."""
        total = self.total_quantity.value()
        nitro_pct = self.target_nitro_pct.value() / 100.0
        methanol_pct = self.target_methanol_pct.value() / 100.0
        oil_pct = self.target_oil_pct.value() / 100.0
        
        # Normalize percentages
        total_pct = nitro_pct + methanol_pct + oil_pct
        if total_pct > 0:
            nitro_pct = nitro_pct / total_pct
            methanol_pct = methanol_pct / total_pct
            oil_pct = oil_pct / total_pct
        
        nitro_qty = total * nitro_pct
        methanol_qty = total * methanol_pct
        oil_qty = total * oil_pct
        
        unit = self.quantity_unit.currentText()
        self.nitro_result.setText(f"Nitromethane: {nitro_qty:.3f} {unit}")
        self.methanol_result.setText(f"Methanol: {methanol_qty:.3f} {unit}")
        self.oil_result.setText(f"Oil: {oil_qty:.3f} {unit}")
        
        # Calculate specific gravity (approximate)
        # Nitromethane: ~1.14, Methanol: ~0.79, Oil: ~0.9
        sg = (nitro_pct * 1.14) + (methanol_pct * 0.79) + (oil_pct * 0.9)
        self.specific_gravity.setText(f"Specific Gravity: {sg:.3f}")
    
    def _create_afr_jetting_calculator(self) -> QWidget:
        """Create AFR and jetting calculator."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("AFR & Jetting Calculator - Nitromethane Stoich: ~1.7:1 (runs very rich for cooling)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Input section
        input_group = QGroupBox("Engine & System Parameters")
        input_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        input_layout = QVBoxLayout()
        
        input_layout.addWidget(QLabel("Engine Displacement (cubic inches):"))
        self.displacement = QDoubleSpinBox()
        self.displacement.setRange(100, 2000)
        self.displacement.setValue(500.0)
        self.displacement.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.displacement)
        
        input_layout.addWidget(QLabel("Blower Size (cubic inches):"))
        self.blower_size = QDoubleSpinBox()
        self.blower_size.setRange(0, 1000)
        self.blower_size.setValue(0)
        self.blower_size.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.blower_size)
        
        input_layout.addWidget(QLabel("Blower Overdrive (%):"))
        self.blower_overdrive = QDoubleSpinBox()
        self.blower_overdrive.setRange(0, 200)
        self.blower_overdrive.setValue(0)
        self.blower_overdrive.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.blower_overdrive)
        
        input_layout.addWidget(QLabel("Air Temperature (°F):"))
        self.air_temp = QDoubleSpinBox()
        self.air_temp.setRange(-20, 150)
        self.air_temp.setValue(70.0)
        self.air_temp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.air_temp)
        
        input_layout.addWidget(QLabel("Barometric Pressure (inHg):"))
        self.baro_pressure = QDoubleSpinBox()
        self.baro_pressure.setRange(20, 32)
        self.baro_pressure.setValue(29.92)
        self.baro_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.baro_pressure)
        
        input_layout.addWidget(QLabel("Target AFR (Nitromethane ~1.2-1.5:1 for racing):"))
        self.target_afr = QDoubleSpinBox()
        self.target_afr.setRange(1.0, 2.0)
        self.target_afr.setValue(1.35)
        self.target_afr.setSingleStep(0.05)
        self.target_afr.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.target_afr)
        
        calculate_btn = QPushButton("Calculate Fuel Flow & Jetting")
        calculate_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 8px; font-weight: bold;")
        input_layout.addWidget(calculate_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Recommended Settings")
        output_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        output_layout = QVBoxLayout()
        
        self.fuel_flow_result = QLabel("Fuel Flow Rate: --")
        self.fuel_flow_result.setStyleSheet("font-size: 11px; color: #00ff00;")
        output_layout.addWidget(self.fuel_flow_result)
        
        self.jet_size_result = QLabel("Recommended Jet Size: --")
        self.jet_size_result.setStyleSheet("font-size: 11px; color: #0080ff;")
        output_layout.addWidget(self.jet_size_result)
        
        self.pill_size_result = QLabel("Recommended Pill Size: --")
        self.pill_size_result.setStyleSheet("font-size: 11px; color: #ff8000;")
        output_layout.addWidget(self.pill_size_result)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Connect calculate button
        calculate_btn.clicked.connect(self._calculate_afr_jetting)
        
        layout.addStretch()
        return tab
    
    def _calculate_afr_jetting(self) -> None:
        """Calculate AFR and jetting requirements."""
        # Simplified calculation (real calculation would be more complex)
        displacement = self.displacement.value()
        blower_size = self.blower_size.value()
        overdrive = self.blower_overdrive.value() / 100.0
        air_temp = self.air_temp.value()
        baro = self.baro_pressure.value()
        target_afr = self.target_afr.value()
        
        # Calculate air flow (simplified)
        if blower_size > 0:
            air_flow = blower_size * (1 + overdrive) * (displacement / 100) * (baro / 29.92) * ((460 + 70) / (460 + air_temp))
        else:
            air_flow = displacement * 0.5  # NA approximation
        
        # Calculate fuel flow (lbs/hr)
        fuel_flow = air_flow / target_afr
        
        self.fuel_flow_result.setText(f"Fuel Flow Rate: {fuel_flow:.1f} lbs/hr ({fuel_flow * 0.125:.2f} gal/min)")
        
        # Estimate jet/pill sizes (simplified - would need actual jet charts)
        if fuel_flow < 50:
            jet_size = "0.080\" - 0.090\""
            pill_size = "0.040\" - 0.050\""
        elif fuel_flow < 100:
            jet_size = "0.090\" - 0.100\""
            pill_size = "0.050\" - 0.060\""
        elif fuel_flow < 150:
            jet_size = "0.100\" - 0.110\""
            pill_size = "0.060\" - 0.070\""
        else:
            jet_size = "0.110\" - 0.120\""
            pill_size = "0.070\" - 0.080\""
        
        self.jet_size_result.setText(f"Recommended Jet Size: {jet_size}")
        self.pill_size_result.setText(f"Recommended Pill Size: {pill_size}")
    
    def _create_performance_prediction(self) -> QWidget:
        """Create performance prediction calculator."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Performance Prediction - Estimate power gains from fuel mix changes")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Input section
        input_group = QGroupBox("Current Performance Data")
        input_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        input_layout = QVBoxLayout()
        
        input_layout.addWidget(QLabel("Current Peak Torque (ft-lb):"))
        self.current_torque = QDoubleSpinBox()
        self.current_torque.setRange(0, 10000)
        self.current_torque.setValue(2000.0)
        self.current_torque.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.current_torque)
        
        input_layout.addWidget(QLabel("Current Peak HP:"))
        self.current_hp = QDoubleSpinBox()
        self.current_hp.setRange(0, 20000)
        self.current_hp.setValue(3000.0)
        self.current_hp.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.current_hp)
        
        input_layout.addWidget(QLabel("Current Nitromethane %:"))
        self.current_nitro_pct = QDoubleSpinBox()
        self.current_nitro_pct.setRange(0, 100)
        self.current_nitro_pct.setValue(90.0)
        self.current_nitro_pct.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.current_nitro_pct)
        
        input_layout.addWidget(QLabel("Target Nitromethane %:"))
        self.target_nitro_pct_perf = QDoubleSpinBox()
        self.target_nitro_pct_perf.setRange(0, 100)
        self.target_nitro_pct_perf.setValue(95.0)
        self.target_nitro_pct_perf.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        input_layout.addWidget(self.target_nitro_pct_perf)
        
        calculate_btn = QPushButton("Predict Performance")
        calculate_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 8px; font-weight: bold;")
        input_layout.addWidget(calculate_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Predicted Performance")
        output_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        output_layout = QVBoxLayout()
        
        self.predicted_torque = QLabel("Predicted Peak Torque: --")
        self.predicted_torque.setStyleSheet("font-size: 11px; color: #00ff00;")
        output_layout.addWidget(self.predicted_torque)
        
        self.predicted_hp = QLabel("Predicted Peak HP: --")
        self.predicted_hp.setStyleSheet("font-size: 11px; color: #00ff00;")
        output_layout.addWidget(self.predicted_hp)
        
        self.predicted_speed = QLabel("Estimated Speed Change: --")
        self.predicted_speed.setStyleSheet("font-size: 11px; color: #0080ff;")
        output_layout.addWidget(self.predicted_speed)
        
        self.predicted_et = QLabel("Estimated ET Change: --")
        self.predicted_et.setStyleSheet("font-size: 11px; color: #ff8000;")
        output_layout.addWidget(self.predicted_et)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Connect calculate button
        calculate_btn.clicked.connect(self._calculate_performance)
        
        layout.addStretch()
        return tab
    
    def _calculate_performance(self) -> None:
        """Calculate performance prediction."""
        current_torque = self.current_torque.value()
        current_hp = self.current_hp.value()
        current_nitro = self.current_nitro_pct.value()
        target_nitro = self.target_nitro_pct_perf.value()
        
        # Simplified prediction (each 1% nitro increase ≈ 1-2% power increase)
        nitro_change = target_nitro - current_nitro
        power_multiplier = 1.0 + (nitro_change * 0.015)  # 1.5% per 1% nitro
        
        predicted_torque = current_torque * power_multiplier
        predicted_hp = current_hp * power_multiplier
        
        self.predicted_torque.setText(f"Predicted Peak Torque: {predicted_torque:.0f} ft-lb (+{predicted_torque - current_torque:.0f})")
        self.predicted_hp.setText(f"Predicted Peak HP: {predicted_hp:.0f} HP (+{predicted_hp - current_hp:.0f})")
        
        # Estimate speed/ET changes (simplified)
        speed_change = (power_multiplier - 1.0) * 5  # ~5 MPH per 10% power
        et_change = -(power_multiplier - 1.0) * 0.1  # ~0.1s per 10% power
        
        self.predicted_speed.setText(f"Estimated Speed Change: {speed_change:+.1f} MPH")
        self.predicted_et.setText(f"Estimated ET Change: {et_change:+.3f} seconds")
    
    def _create_mix_simulator(self) -> QWidget:
        """Create lean/rich fuel mix simulator with AFR guidance."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Fuel Mix Simulator - Lean/Rich Adjustments vs Power")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.mix_status_label = QLabel("Nitromethane %: --")
        self.mix_status_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(self.mix_status_label)
        
        self.mix_base_ratio = QDoubleSpinBox()
        self.mix_base_ratio.setRange(1.0, 2.0)
        self.mix_base_ratio.setValue(1.35)
        self.mix_base_ratio.setSingleStep(0.05)
        self.mix_base_ratio.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.mix_base_ratio.valueChanged.connect(self._update_mix_simulator)
        
        base_layout = QHBoxLayout()
        base_layout.addWidget(QLabel("Base AFR (gasoline equivalent):"))
        base_layout.addWidget(self.mix_base_ratio)
        layout.addLayout(base_layout)
        
        self.mix_sim_slider = QSlider(Qt.Orientation.Horizontal)
        self.mix_sim_slider.setRange(0, 100)
        self.mix_sim_slider.setValue(90)
        self.mix_sim_slider.setTickInterval(5)
        self.mix_sim_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.mix_sim_slider.valueChanged.connect(self._update_mix_simulator)
        layout.addWidget(self.mix_sim_slider)
        
        btn_row = QHBoxLayout()
        lean_btn = QPushButton("Lean Out")
        lean_btn.setStyleSheet("background-color: #ff8000; color: #ffffff; padding: 6px;")
        lean_btn.clicked.connect(lambda: self._nudge_mix_simulator(-2))
        btn_row.addWidget(lean_btn)
        
        rich_btn = QPushButton("Rich Up")
        rich_btn.setStyleSheet("background-color: #00aa00; color: #ffffff; padding: 6px;")
        rich_btn.clicked.connect(lambda: self._nudge_mix_simulator(2))
        btn_row.addWidget(rich_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        self.mix_power_label = QLabel("Predicted Power Gain: --")
        self.mix_power_label.setStyleSheet("color: #00ff00; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.mix_power_label)
        
        self.mix_timing_label = QLabel("Recommended Timing Offset: --")
        self.mix_timing_label.setStyleSheet("color: #0080ff; font-size: 12px;")
        layout.addWidget(self.mix_timing_label)
        
        guidance = QLabel("Tip: Nitromethane stoich ≈ 1.7:1. Richer mixtures cool the engine but raise detonation risk.")
        guidance.setWordWrap(True)
        guidance.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(guidance)
        
        layout.addStretch()
        self._update_mix_simulator()
        return tab
    
    def _create_data_logging_analysis(self) -> QWidget:
        """Create data logging analysis tool."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Data Logging Analysis - Analyze historical runs and conditions")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        info_label = QLabel("Import data logs to analyze how changes in conditions or tune-up affected performance.")
        info_label.setStyleSheet("font-size: 11px; color: #888888;")
        layout.addWidget(info_label)
        
        # File import section
        import_group = QGroupBox("Import Data Log")
        import_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        import_layout = QVBoxLayout()
        
        import_btn = QPushButton("Browse Data Log File...")
        import_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 8px;")
        import_layout.addWidget(import_btn)
        
        self.log_file_path = QLabel("No file selected")
        self.log_file_path.setStyleSheet("font-size: 10px; color: #888888;")
        import_layout.addWidget(self.log_file_path)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Analysis results
        analysis_group = QGroupBox("Analysis Results")
        analysis_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        analysis_layout = QVBoxLayout()
        
        self.analysis_results = QLabel("No analysis data available. Import a data log file to begin.")
        self.analysis_results.setStyleSheet("font-size: 11px; color: #888888;")
        self.analysis_results.setWordWrap(True)
        analysis_layout.addWidget(self.analysis_results)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Unit conversion section
        unit_group = QGroupBox("Unit Conversion")
        unit_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        unit_layout = QVBoxLayout()
        
        unit_layout.addWidget(QLabel("Temperature:"))
        temp_layout = QHBoxLayout()
        self.temp_input = QDoubleSpinBox()
        self.temp_input.setRange(-50, 200)
        self.temp_input.setValue(70.0)
        self.temp_input.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        temp_layout.addWidget(self.temp_input)
        
        self.temp_unit = QComboBox()
        self.temp_unit.addItems(["°F", "°C"])
        self.temp_unit.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        temp_layout.addWidget(self.temp_unit)
        
        self.temp_result = QLabel("= --")
        self.temp_result.setStyleSheet("font-size: 11px; color: #00ff00;")
        temp_layout.addWidget(self.temp_result)
        unit_layout.addLayout(temp_layout)
        
        # Connect temperature conversion
        self.temp_input.valueChanged.connect(self._convert_temperature)
        self.temp_unit.currentIndexChanged.connect(self._convert_temperature)
        
        unit_group.setLayout(unit_layout)
        layout.addWidget(unit_group)
        
        # Safety guidelines
        safety_group = QGroupBox("Safety Guidelines")
        safety_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        safety_layout = QVBoxLayout()
        
        safety_text = QLabel(
            "⚠️ WARNING: Nitromethane tuning operates on a fine line between power and engine failure.\n\n"
            "• Extreme cylinder pressures (potentially over 4000 psi)\n"
            "• Highly volatile fuel - handle with extreme care\n"
            "• Monitor all sensors continuously\n"
            "• Always have emergency shutdown procedures ready\n"
            "• Use proper safety equipment and procedures"
        )
        safety_text.setStyleSheet("font-size: 10px; color: #ff0000;")
        safety_text.setWordWrap(True)
        safety_layout.addWidget(safety_text)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        layout.addStretch()
        return tab
    
    def _convert_temperature(self) -> None:
        """Convert temperature between Fahrenheit and Celsius."""
        temp = self.temp_input.value()
        if self.temp_unit.currentText() == "°F":
            # Convert to Celsius
            celsius = (temp - 32) * 5 / 9
            self.temp_result.setText(f"= {celsius:.1f}°C")
        else:
            # Convert to Fahrenheit
            fahrenheit = (temp * 9 / 5) + 32
            self.temp_result.setText(f"= {fahrenheit:.1f}°F")
    
    def _nudge_mix_simulator(self, delta: int) -> None:
        if self.mix_sim_slider is None:
            return
        new_value = max(0, min(100, self.mix_sim_slider.value() + delta))
        self.mix_sim_slider.setValue(new_value)
    
    def _update_mix_simulator(self) -> None:
        if self.mix_sim_slider is None or self.mix_power_label is None:
            return
        nitro_pct = self.mix_sim_slider.value()
        base_afr = self.mix_base_ratio.value()
        recommended_lambda = self._recommended_lambda(nitro_pct)
        afr_equiv = recommended_lambda * 1.7
        power_multiplier = 1.0 + ((nitro_pct - 80) * 0.012)
        mixture_offset = base_afr - afr_equiv
        power_multiplier -= max(0.0, (abs(mixture_offset) - 0.1) * 0.05)
        timing_offset = (nitro_pct - 90) * 0.2
        self.mix_status_label.setText(f"Nitromethane %: {nitro_pct}% • Recommended AFR: {afr_equiv:.2f}:1")
        self.mix_power_label.setText(f"Predicted Power Gain: {(power_multiplier - 1.0) * 100:+.1f}%")
        self.mix_timing_label.setText(f"Recommended Timing Offset: {timing_offset:+.1f}°")
    
    def _recommended_lambda(self, nitro_pct: float) -> float:
        base_lambda = 0.95 - (nitro_pct / 100.0) * 0.2
        return max(0.70, min(0.95, base_lambda))
    
    def _detonation_risk(self, lambda_val: float, timing_adv: float, boost: float, egt: float) -> float:
        lambda_over = max(0.0, lambda_val - 0.9)
        timing_over = max(0.0, (timing_adv - 50.0) / 20.0)
        boost_penalty = max(0.0, boost / 60.0)
        temp_penalty = max(0.0, (egt - 1350.0) / 400.0)
        risk = lambda_over * 2.0 + timing_over + boost_penalty + temp_penalty
        return max(0.0, min(1.0, risk))
    
    def _update_detonation_indicator(self, risk: float) -> None:
        if not hasattr(self, "det_status_label"):
            return
        if risk < 0.3:
            color = "#00ff80"
            text = "Detonation Risk: Low"
        elif risk < 0.6:
            color = "#ffaa00"
            text = "Detonation Risk: Moderate"
        else:
            color = "#ff3b30"
            text = "Detonation Risk: HIGH"
        self.det_status_label.setText(text)
        self.det_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def _update_boost_indicator(self, nitro_boost: float) -> None:
        if hasattr(self, "audio_indicator"):
            if nitro_boost > 60:
                self.audio_indicator.setText("Nitro Cue: SIREN - Overboost!")
                self.audio_indicator.setStyleSheet("color: #ff5555; font-weight: bold;")
            elif nitro_boost > 40:
                self.audio_indicator.setText("Nitro Cue: Rising howl")
                self.audio_indicator.setStyleSheet("color: #ffaa00;")
            else:
                self.audio_indicator.setText("Nitro Cue: Idle hum")
                self.audio_indicator.setStyleSheet("color: #5f6368;")
    
    def _update_power_prediction(self, base_hp: float, nitro_pct: float, lambda_val: float, recommended_lambda: float) -> None:
        if not hasattr(self, "power_predict_label"):
            return
        lambda_delta = recommended_lambda - lambda_val
        multiplier = 1.0 + ((nitro_pct - 80.0) * 0.012) + (max(0.0, -lambda_delta) * 0.5)
        predicted_hp = max(0.0, base_hp * multiplier)
        self.power_predict_label.setText(f"Predicted Power: {predicted_hp:.0f} HP ({(multiplier - 1.0) * 100:+.1f}%)")
    
    def _update_engine_damage(self, risk: float, lambda_val: float) -> None:
        self._damage_score = min(100.0, max(0.0, self._damage_score * 0.92 + risk * 15 + max(0.0, (lambda_val - 0.95) * 50)))
        if hasattr(self, "damage_gauge"):
            self.damage_gauge.set_value(self._damage_score)
    
    def _update_soft_rev_status(self, rpm: float) -> None:
        if not hasattr(self, "soft_rev_label"):
            return
        soft_limit = getattr(self, "soft_rev_limit", None)
        hard_limit = getattr(self, "hard_rev_limit", None)
        if not soft_limit or not hard_limit:
            return
        if rpm >= hard_limit.value():
            self._soft_rev_state = "HARD CUT"
            color = "#ff3b30"
        elif rpm >= soft_limit.value():
            self._soft_rev_state = "Soft Limiting"
            color = "#ffaa00"
        else:
            self._soft_rev_state = "Idle"
            color = "#00ff80"
        self.soft_rev_label.setText(f"Soft Rev Limiter: {self._soft_rev_state}")
        self.soft_rev_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
    def _add_right_settings(self, layout: QVBoxLayout) -> None:
        """Add right panel settings."""
        # Fuel Strategy (Lambda-based)
        fuel_strategy_group = QGroupBox("Fuel Strategy (Lambda-based)")
        fuel_strategy_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        fuel_strategy_layout = QVBoxLayout()
        
        fuel_strategy_layout.addWidget(QLabel("Target Lambda (1.0 = Stoich):"))
        self.target_lambda = QDoubleSpinBox()
        self.target_lambda.setRange(0.7, 1.0)
        self.target_lambda.setValue(0.85)
        self.target_lambda.setSingleStep(0.01)
        self.target_lambda.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_strategy_layout.addWidget(self.target_lambda)
        
        self.recommended_lambda_label = QLabel("Recommended Lambda: --")
        self.recommended_lambda_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        fuel_strategy_layout.addWidget(self.recommended_lambda_label)
        
        fuel_strategy_layout.addWidget(QLabel("Nitro Percentage (%):"))
        self.nitro_percent = QDoubleSpinBox()
        self.nitro_percent.setRange(0, 100)
        self.nitro_percent.setValue(90.0)
        self.nitro_percent.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        fuel_strategy_layout.addWidget(self.nitro_percent)
        
        fuel_strategy_group.setLayout(fuel_strategy_layout)
        layout.addWidget(fuel_strategy_group)
        
        # Sequential Injection and Ignition
        sequential_group = QGroupBox("Sequential Injection & Ignition")
        sequential_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        sequential_layout = QVBoxLayout()
        
        self.sequential_injection = QCheckBox("Full Sequential Injection")
        self.sequential_injection.setChecked(True)
        self.sequential_injection.setStyleSheet("color: #ffffff;")
        sequential_layout.addWidget(self.sequential_injection)
        
        self.sequential_ignition = QCheckBox("Full Sequential Ignition")
        self.sequential_ignition.setChecked(True)
        self.sequential_ignition.setStyleSheet("color: #ffffff;")
        sequential_layout.addWidget(self.sequential_ignition)
        
        sequential_group.setLayout(sequential_layout)
        layout.addWidget(sequential_group)
        
        # Fuel Pump Control
        pump_group = QGroupBox("Fuel Pump Control")
        pump_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        pump_layout = QVBoxLayout()
        
        pump_layout.addWidget(QLabel("Pump Control Mode:"))
        self.pump_mode = QComboBox()
        self.pump_mode.addItems(["Variable Speed", "Staged (Primary/Secondary)", "Fixed Speed"])
        self.pump_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        pump_layout.addWidget(self.pump_mode)
        
        pump_layout.addWidget(QLabel("Primary Pump Speed (%):"))
        self.primary_pump_speed = QDoubleSpinBox()
        self.primary_pump_speed.setRange(0, 100)
        self.primary_pump_speed.setValue(100.0)
        self.primary_pump_speed.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        pump_layout.addWidget(self.primary_pump_speed)
        
        pump_layout.addWidget(QLabel("Secondary Pump Activation (psi):"))
        self.secondary_pump_activation = QDoubleSpinBox()
        self.secondary_pump_activation.setRange(0, 100)
        self.secondary_pump_activation.setValue(50.0)
        self.secondary_pump_activation.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        pump_layout.addWidget(self.secondary_pump_activation)
        
        pump_group.setLayout(pump_layout)
        layout.addWidget(pump_group)
        
        # Boost & Power Simulation
        boost_group = QGroupBox("Boost & Power Simulation")
        boost_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        boost_layout = QVBoxLayout()
        self.boost_state_label = QLabel("Nitro Boost State: Idle")
        self.boost_state_label.setStyleSheet("color: #9aa0a6; font-size: 11px;")
        boost_layout.addWidget(self.boost_state_label)
        self.power_predict_label = QLabel("Predicted Power: --")
        self.power_predict_label.setStyleSheet("color: #00ff80; font-weight: bold;")
        boost_layout.addWidget(self.power_predict_label)
        boost_group.setLayout(boost_layout)
        layout.addWidget(boost_group)
        
        # Rev Limits & Shift Points
        rev_shift_group = QGroupBox("Rev Limits & Shift Points")
        rev_shift_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        rev_shift_layout = QVBoxLayout()
        
        rev_shift_layout.addWidget(QLabel("Hard Rev Limit (RPM):"))
        self.hard_rev_limit = QSpinBox()
        self.hard_rev_limit.setRange(5000, 20000)
        self.hard_rev_limit.setValue(12000)
        self.hard_rev_limit.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rev_shift_layout.addWidget(self.hard_rev_limit)
        
        rev_shift_layout.addWidget(QLabel("Soft Rev Limit (RPM):"))
        self.soft_rev_limit = QSpinBox()
        self.soft_rev_limit.setRange(5000, 20000)
        self.soft_rev_limit.setValue(11500)
        self.soft_rev_limit.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rev_shift_layout.addWidget(self.soft_rev_limit)
        
        rev_shift_layout.addWidget(QLabel("Shift Point (RPM):"))
        self.shift_point = QSpinBox()
        self.shift_point.setRange(5000, 20000)
        self.shift_point.setValue(11000)
        self.shift_point.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        rev_shift_layout.addWidget(self.shift_point)
        
        rev_shift_group.setLayout(rev_shift_layout)
        layout.addWidget(rev_shift_group)
        
        # Safety Features
        safety_group = QGroupBox("Safety & Feedback Loops")
        safety_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        safety_layout = QVBoxLayout()
        
        self.closed_loop_o2 = QCheckBox("Closed-Loop O2 Correction (Wideband Lambda)")
        self.closed_loop_o2.setChecked(True)
        self.closed_loop_o2.setStyleSheet("color: #ffffff;")
        safety_layout.addWidget(self.closed_loop_o2)
        
        safety_layout.addWidget(QLabel("Max EGT (°C):"))
        self.max_egt = QSpinBox()
        self.max_egt.setRange(1000, 1800)
        self.max_egt.setValue(1400)
        self.max_egt.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_egt)
        
        safety_layout.addWidget(QLabel("Max CHT (°C):"))
        self.max_cht = QSpinBox()
        self.max_cht.setRange(150, 350)
        self.max_cht.setValue(250)
        self.max_cht.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_cht)
        
        safety_layout.addWidget(QLabel("Min Fuel Pressure (psi):"))
        self.min_fuel_pressure = QDoubleSpinBox()
        self.min_fuel_pressure.setRange(0, 200)
        self.min_fuel_pressure.setValue(80.0)
        self.min_fuel_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_fuel_pressure)
        
        safety_layout.addWidget(QLabel("Min Oil Pressure (psi):"))
        self.min_oil_pressure = QDoubleSpinBox()
        self.min_oil_pressure.setRange(0, 200)
        self.min_oil_pressure.setValue(60.0)
        self.min_oil_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.min_oil_pressure)
        
        safety_layout.addWidget(QLabel("Max Peak Cylinder Pressure (psi):"))
        self.max_peak_pressure = QSpinBox()
        self.max_peak_pressure.setRange(2000, 6000)
        self.max_peak_pressure.setValue(4000)
        self.max_peak_pressure.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.max_peak_pressure)
        
        self.knock_detection = QCheckBox("Advanced Knock Detection")
        self.knock_detection.setChecked(True)
        self.knock_detection.setStyleSheet("color: #ffffff;")
        safety_layout.addWidget(self.knock_detection)
        
        safety_layout.addWidget(QLabel("Knock Retard Rate (°/event):"))
        self.knock_retard_rate = QDoubleSpinBox()
        self.knock_retard_rate.setRange(0.5, 5.0)
        self.knock_retard_rate.setValue(2.0)
        self.knock_retard_rate.setSingleStep(0.5)
        self.knock_retard_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        safety_layout.addWidget(self.knock_retard_rate)
        
        self.emergency_shutdown = QCheckBox("Emergency Shutdown Enabled")
        self.emergency_shutdown.setChecked(True)
        self.emergency_shutdown.setStyleSheet("color: #ffffff;")
        safety_layout.addWidget(self.emergency_shutdown)
        
        self.det_status_label = QLabel("Detonation Risk: --")
        self.det_status_label.setStyleSheet("color: #9aa0a6; font-weight: bold;")
        safety_layout.addWidget(self.det_status_label)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        # System Enable
        self.system_enabled = QCheckBox("Nitro System Enabled")
        self.system_enabled.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.system_enabled)
        
        # High-Speed Datalogger
        datalogger_group = QGroupBox("High-Speed Datalogger")
        datalogger_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        datalogger_layout = QVBoxLayout()
        
        datalogger_layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.sample_rate = QComboBox()
        self.sample_rate.addItems(["100", "200", "500", "1000", "2000"])
        self.sample_rate.setCurrentIndex(3)  # 1000 Hz
        self.sample_rate.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        datalogger_layout.addWidget(self.sample_rate)
        
        self.auto_logging = QCheckBox("Auto Start/Stop Logging")
        self.auto_logging.setChecked(True)
        self.auto_logging.setStyleSheet("color: #ffffff;")
        datalogger_layout.addWidget(self.auto_logging)
        
        datalogger_group.setLayout(datalogger_layout)
        layout.addWidget(datalogger_group)
        
        layout.addStretch()
        
    def _create_graphs_panel(self) -> QWidget:
        """Create comprehensive real-time monitoring graphs panel."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("High-Speed Datalogging & Analysis")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Create tabbed graphs
        graph_tabs = QTabWidget()
        graph_tabs.setStyleSheet("""
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
        
        # Lambda/AFR vs RPM/Load
        lambda_graph = RealTimeGraph()
        lambda_graph.setMinimumHeight(200)
        graph_tabs.addTab(lambda_graph, "Lambda/AFR vs RPM/Load")
        self.lambda_graph = lambda_graph
        
        # Ignition Timing vs RPM/Load
        timing_graph = RealTimeGraph()
        timing_graph.setMinimumHeight(200)
        graph_tabs.addTab(timing_graph, "Ignition Timing")
        self.timing_graph = timing_graph
        
        # EGT/CHT vs Time/RPM
        temp_graph = RealTimeGraph()
        temp_graph.setMinimumHeight(200)
        graph_tabs.addTab(temp_graph, "EGT/CHT vs Time/RPM")
        self.temp_graph = temp_graph
        
        # Fuel Flow/Pressure vs RPM/Load
        fuel_graph = RealTimeGraph()
        fuel_graph.setMinimumHeight(200)
        graph_tabs.addTab(fuel_graph, "Fuel Flow/Pressure")
        self.fuel_graph = fuel_graph
        
        # Peak Cylinder Pressure vs Time/RPM
        pressure_graph = RealTimeGraph()
        pressure_graph.setMinimumHeight(200)
        graph_tabs.addTab(pressure_graph, "Peak Cylinder Pressure")
        self.pressure_graph = pressure_graph
        
        # Boost Pressure vs Time/RPM
        boost_graph = RealTimeGraph()
        boost_graph.setMinimumHeight(200)
        graph_tabs.addTab(boost_graph, "Boost Pressure")
        self.boost_graph = boost_graph
        
        # Injector Duty Cycle/Pulse Width
        injector_graph = RealTimeGraph()
        injector_graph.setMinimumHeight(200)
        graph_tabs.addTab(injector_graph, "Injector Duty/Pulse")
        self.injector_graph = injector_graph
        
        layout.addWidget(graph_tabs)
        return panel
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update nitro methane tab with telemetry data."""
        nitro = data.get("nitro_percent", 90)
        timing = data.get("nitro_timing_adj", 0)
        status = 100 if data.get("nitro_active", False) else 0
        lambda_val = data.get("Lambda", data.get("lambda_value", 0.85))
        fuel_pressure = data.get("Fuel_Pressure", 100)
        peak_pressure = data.get("Peak_Cylinder_Pressure", 3000)
        egt = data.get("EGT", data.get("EGT_Avg", 1200))
        cht = data.get("CHT", data.get("Cylinder_Head_Temp", 200))
        boost = data.get("Boost_Pressure", 0)
        injector_duty = data.get("Injector_Duty", 80)
        injector_pulse = data.get("Injector_Pulse_Width", 15.0)
        recommended_lambda = self._recommended_lambda(nitro)
        if hasattr(self, "recommended_lambda_label"):
            self.recommended_lambda_label.setText(f"Recommended Lambda: {recommended_lambda:.3f}")
        
        self.nitro_gauge.set_value(nitro)
        self.timing_gauge.set_value(timing)
        self.status_gauge.set_value(status)
        if hasattr(self, 'lambda_gauge'):
            self.lambda_gauge.set_value(lambda_val)
        if hasattr(self, 'fuel_pressure_gauge'):
            self.fuel_pressure_gauge.set_value(fuel_pressure)
        if hasattr(self, 'peak_pressure_gauge'):
            self.peak_pressure_gauge.set_value(peak_pressure)
        if hasattr(self, 'egt_gauge'):
            self.egt_gauge.set_value(egt)
        if hasattr(self, 'cht_gauge'):
            self.cht_gauge.set_value(cht)
        if hasattr(self, "nitro_boost_gauge"):
            nitro_boost = min(80.0, boost * 1.2 + (nitro * 0.25) + (status * 0.1) + max(0.0, fuel_pressure - 80) * 0.2)
            self.nitro_boost_gauge.set_value(nitro_boost)
            if hasattr(self, "boost_state_label"):
                self.boost_state_label.setText(f"Nitro Boost State: {nitro_boost:.1f} psi eqv.")
            self._update_boost_indicator(nitro_boost)
        
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        map_val = data.get("Boost_Pressure", 0) * 6.895
        load = data.get("Engine_Load", 80)
        base_hp = data.get("Horsepower", data.get("nitro_base_hp", 3500))
        self._update_power_prediction(base_hp, nitro, lambda_val, recommended_lambda)
        risk = self._detonation_risk(lambda_val, data.get("Ignition_Timing", 40), boost, egt)
        self._update_detonation_indicator(risk)
        self._update_engine_damage(risk, lambda_val)
        self._update_soft_rev_status(rpm)
        if self.mix_sim_slider and not self.mix_sim_slider.isSliderDown():
            self.mix_sim_slider.setValue(int(nitro))
            self._update_mix_simulator()
        
        # Update graphs
        if hasattr(self, 'lambda_graph'):
            afr = lambda_val * 1.7  # Nitromethane stoich
            self.lambda_graph.update_data(rpm, lambda_val, afr, load)
        
        if hasattr(self, 'timing_graph'):
            timing_advance = data.get("Ignition_Timing", 40)
            self.timing_graph.update_data(rpm, timing_advance, load, 0)
        
        if hasattr(self, 'temp_graph'):
            self.temp_graph.update_data(rpm, egt, cht, 0)
        
        if hasattr(self, 'fuel_graph'):
            fuel_flow = data.get("Fuel_Flow", 100)
            self.fuel_graph.update_data(rpm, fuel_pressure, fuel_flow, load)
        
        if hasattr(self, 'pressure_graph'):
            self.pressure_graph.update_data(rpm, peak_pressure, map_val, 0)
        
        if hasattr(self, 'boost_graph'):
            self.boost_graph.update_data(rpm, boost, map_val, 0)
        
        if hasattr(self, 'injector_graph'):
            self.injector_graph.update_data(rpm, injector_duty, injector_pulse, load)
        
        # Update base realtime graph
        if hasattr(self, 'realtime_graph'):
            self.realtime_graph.update_data(rpm, map_val, lambda_val, timing)


class ECUTuningMainWindow(QWidget):
    """Main ECU Tuning Interface - replaces standard main window."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Tuner Agent - ECU Tuning Interface")
        self.resize(1600, 1000)
        self._telemetry_data: Dict[str, float] = {}
        self.setup_ui()
        self._start_update_timer()
        
    def setup_ui(self) -> None:
        """Setup main ECU tuning interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Set overall background - industrial realism (deep black/charcoal)
        self.setStyleSheet("background-color: #0a0a0a;")
        
        # Top bar with car image
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 10)
        
        # Car image widget
        try:
            self.car_image = CarImageWidget()
            self.car_image.setMaximumWidth(200)
            top_bar.addWidget(self.car_image)
        except Exception:
            pass
            
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
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
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                border-bottom: 2px solid #0080ff;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #333333;
            }
        """)
        
        # Main Fuel VE tab
        self.fuel_tab = FuelVETab()
        self.tabs.addTab(self.fuel_tab, "Fuel VE")
        
        # Module tabs
        self.nitrous_tab = NitrousTab()
        self.tabs.addTab(self.nitrous_tab, "Nitrous")
        
        self.turbo_tab = TurboTab()
        self.tabs.addTab(self.turbo_tab, "Turbo")
        
        self.e85_tab = E85Tab()
        self.tabs.addTab(self.e85_tab, "E85")
        
        self.methanol_tab = MethanolTab()
        self.tabs.addTab(self.methanol_tab, "Methanol")
        
        self.nitro_tab = NitroMethaneTab()
        self.tabs.addTab(self.nitro_tab, "Nitro Methane")
        
        main_layout.addWidget(self.tabs, stretch=1)
        
    def _start_update_timer(self) -> None:
        """Start timer for telemetry updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_all_tabs)
        self.update_timer.start(100)  # 10 Hz
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update interface with new telemetry data."""
        self._telemetry_data = data
        self._update_all_tabs()
        
    def _update_all_tabs(self) -> None:
        """Update all tabs with current telemetry."""
        data = self._telemetry_data
        
        # Update main fuel tab
        self.fuel_tab.update_telemetry(data)
        
        # Update module tabs
        self.nitrous_tab.update_telemetry(data)
        self.turbo_tab.update_telemetry(data)
        self.e85_tab.update_telemetry(data)
        self.methanol_tab.update_telemetry(data)
        self.nitro_tab.update_telemetry(data)


__all__ = ["ECUTuningMainWindow"]

