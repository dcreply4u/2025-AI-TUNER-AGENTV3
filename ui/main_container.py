"""
Main Container Window
Container for all modules with tabbed interface
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QSizePolicy,
    QComboBox,
    QGroupBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QListWidget,
    QListWidgetItem,
    QDialog,
)
from PySide6.QtGui import QFont, QBrush, QColor

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet
from ui.racing_ui_theme import get_racing_theme, get_racing_stylesheet, RacingColor
from ui.contextual_modes import ContextualModeManager, RacingMode
from ui.advanced_theme_customizer import AdvancedThemeCustomizer
from ui.theme_manager import ThemeManager
from ui.safety_alerts_system import SafetyAlertsSystem, SafetyAlertsPanel
from ui.predictive_analytics_panel import PredictiveAnalyticsPanel
from ui.multi_row_tab_widget import MultiRowTabWidget

from ui.car_image_widget import CarImageWidget
from ui.ecu_tuning_main import (
    ECUTuningTab,
    NitrousTab,
    TurboTab,
    E85Tab,
    MethanolTab,
    NitroMethaneTab,
)

try:
    from ui.import_ecu_tab import ImportECUTab
except ImportError:
    ImportECUTab = None

try:
    from ui.domestic_ecu_tab import DomesticECUTab
except ImportError:
    DomesticECUTab = None

try:
    from ui.advanced_parameters_tab import AdvancedParametersTab
except ImportError:
    AdvancedParametersTab = None

try:
    from ui.cylinder_control_tab import CylinderControlTab
except ImportError:
    CylinderControlTab = None

try:
    from ui.advanced_features_tab import AdvancedFeaturesTab
except ImportError:
    AdvancedFeaturesTab = None

try:
    from ui.ai_intelligence_tab import AIIntelligenceTab
except ImportError:
    AIIntelligenceTab = None

try:
    from ui.auto_detection_tab import AutoDetectionTab
except ImportError:
    AutoDetectionTab = None

try:
    from ui.backup_manager_tab import BackupManagerTab
except ImportError:
    BackupManagerTab = None

try:
    from ui.hardware_interface_tab import HardwareInterfaceTab
except ImportError:
    HardwareInterfaceTab = None

try:
    from ui.auto_diagnostic_widget import AutoDiagnosticWidget
except ImportError:
    AutoDiagnosticWidget = None

try:
    from ui.diesel_tuning_tab import DieselTuningTab
except ImportError:
    DieselTuningTab = None

try:
    from ui.usb_camera_tab import USBCameraTab
except ImportError:
    USBCameraTab = None

try:
    from ui.ai_advisor_widget import AIAdvisorWidget
except ImportError:
    AIAdvisorWidget = None

# Import other UI modules
try:
    from ui.telemetry_panel import TelemetryPanel
except ImportError:
    TelemetryPanel = None

try:
    from ui.health_score_widget import HealthScoreWidget
except ImportError:
    HealthScoreWidget = None

try:
    from ui.ai_insight_panel import AIInsightPanel
except ImportError:
    AIInsightPanel = None

try:
    from ui.fault_panel import FaultPanel
except ImportError:
    FaultPanel = None

try:
    from ui.dragy_view import DragyPerformanceView
except ImportError:
    DragyPerformanceView = None

try:
    from ui.shift_light_widget import ShiftLightTab
except ImportError:
    ShiftLightTab = None

try:
    from ui.transbrake_widget import TransbrakeTab
except ImportError:
    TransbrakeTab = None

try:
    from ui.modern_racing_dashboard import ModernRacingDashboard
except ImportError:
    ModernRacingDashboard = None

try:
    from ui.floating_ai_advisor import FloatingAIAdvisorManager
except ImportError:
    FloatingAIAdvisorManager = None

try:
    from ui.voice_command_handler import VoiceCommandHandler
except ImportError:
    VoiceCommandHandler = None

try:
    from ui.haptic_feedback import get_haptic_feedback
except ImportError:
    get_haptic_feedback = None


class TelemetryTab(QWidget):
    """Telemetry monitoring module tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup telemetry tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Set background
        self.setStyleSheet("background-color: #e8e9ea;")
        
        # Title
        title = QLabel("Live Telemetry Monitoring")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Telemetry panel
        if TelemetryPanel:
            try:
                self.telemetry_panel = TelemetryPanel()
                layout.addWidget(self.telemetry_panel, stretch=1)
            except (ImportError, AttributeError, TypeError) as e:
                LOGGER.warning("Telemetry panel initialization failed: %s", e)
                placeholder = QLabel("Telemetry panel unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                layout.addWidget(placeholder, stretch=1)
            except Exception as e:
                LOGGER.error("Unexpected error initializing telemetry panel: %s", e)
                placeholder = QLabel("Telemetry panel unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                layout.addWidget(placeholder, stretch=1)
        else:
            placeholder = QLabel("Telemetry panel module not available")
            placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
            layout.addWidget(placeholder, stretch=1)
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update telemetry tab with data."""
        if hasattr(self, 'telemetry_panel') and self.telemetry_panel:
            # TelemetryPanel uses update_data method
            if hasattr(self.telemetry_panel, 'update_data'):
                # Convert dict to Mapping format expected by TelemetryPanel
                from typing import Mapping
                self.telemetry_panel.update_data(data)
            elif hasattr(self.telemetry_panel, 'add_data_point'):
                # Alternative method if available
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        self.telemetry_panel.add_data_point(key, value)


class DiagnosticsTab(QWidget):
    """Diagnostics and health monitoring module tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup diagnostics tab UI with trigger analysis, I/O management, CAN config, and sensor utilities."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGroupBox, QLineEdit, QListWidget, QListWidgetItem
        
        layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(margin)
        
        # Set background
        self.setStyleSheet("background-color: #e8e9ea;")
        
        # Title
        title = QLabel("Diagnostics & Logging")
        title_font = get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Sub-tabs for different diagnostic features
        self.diag_tabs = QTabWidget()
        tab_border = get_scaled_size(1)
        tab_padding_v = get_scaled_size(6)
        tab_padding_h = get_scaled_size(15)
        tab_font = get_scaled_font_size(10)
        # Use consistent light theme styling to match main window
        self.diag_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #bdc3c7;
                background-color: #2c3e50;
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: #ecf0f1;
                color: #34495e;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {get_scaled_size(2)}px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: {tab_font}px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: #3498db;
                color: white;
                border-bottom: none;
            }}
            QTabBar::tab:hover {{
                background-color: #d5dbdb;
            }}
        """)
        
        # Trigger Analysis tab
        trigger_tab = self._create_trigger_analysis_tab()
        self.diag_tabs.addTab(trigger_tab, "Trigger Analysis")
        
        # Data Logging tab
        logging_tab = self._create_data_logging_tab()
        self.diag_tabs.addTab(logging_tab, "Data Logging")
        
        # I/O Management tab
        io_tab = self._create_io_management_tab()
        self.diag_tabs.addTab(io_tab, "I/O Management")
        
        # CAN Bus Config tab
        can_tab = self._create_can_config_tab()
        self.diag_tabs.addTab(can_tab, "CAN Bus Config")
        
        # Sensor Utilities tab
        sensor_tab = self._create_sensor_utilities_tab()
        self.diag_tabs.addTab(sensor_tab, "Sensor Utilities")
        
        # Errors tab
        errors_tab = self._create_errors_tab()
        self.diag_tabs.addTab(errors_tab, "Errors")
        
        # Auto Diagnostic tab (beginner-friendly)
        self.auto_diag_widget = None
        if AutoDiagnosticWidget:
            try:
                self.auto_diag_widget = AutoDiagnosticWidget()
                self.diag_tabs.addTab(self.auto_diag_widget, "🔍 Auto Diagnostic")
            except Exception as e:
                LOGGER.warning("Failed to create Auto Diagnostic tab: %s", e)
        
        # Graphing tab
        graphing_tab = self._create_graphing_tab()
        self.diag_tabs.addTab(graphing_tab, "📊 Graphing")
        
        # Import/Export tab
        import_export_tab = self._create_import_export_tab()
        self.diag_tabs.addTab(import_export_tab, "Import/Export")
        
        layout.addWidget(self.diag_tabs, stretch=1)
    
    def _create_graphing_tab(self) -> QWidget:
        """Create graphing tab for diagnostics data visualization."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QLabel
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        try:
            from ui.advanced_log_graphing import AdvancedLogGraphingWidget
            self.diag_graph_widget = AdvancedLogGraphingWidget()
            layout.addWidget(self.diag_graph_widget, stretch=1)
        except ImportError:
            try:
                from ui.ecu_tuning_widgets import RealTimeGraph
                self.diag_graph_widget = RealTimeGraph()
                layout.addWidget(self.diag_graph_widget, stretch=1)
            except ImportError:
                placeholder = QLabel("Graphing widget not available")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #ffffff; border: 1px solid #bdc3c7; border-radius: 4px;")
                layout.addWidget(placeholder, stretch=1)
                self.diag_graph_widget = None
        
        return tab
    
    def _create_import_export_tab(self) -> QWidget:
        """Create import/export tab for diagnostics data."""
        from PySide6.QtWidgets import QVBoxLayout, QPushButton, QGroupBox, QFileDialog, QMessageBox
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        
        # Import
        import_group = QGroupBox("Import Diagnostics Data")
        import_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #ffffff;
            }}
        """)
        import_layout = QVBoxLayout()
        import_btn = QPushButton("📥 Import Diagnostics Data")
        import_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; border-radius: 5px;")
        import_btn.clicked.connect(lambda: self._import_diag_data())
        import_layout.addWidget(import_btn)
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Export
        export_group = QGroupBox("Export Diagnostics Data")
        export_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #ffffff;
            }}
        """)
        export_layout = QVBoxLayout()
        export_btn = QPushButton("📤 Export Diagnostics Data")
        export_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; border-radius: 5px;")
        export_btn.clicked.connect(lambda: self._export_diag_data())
        export_layout.addWidget(export_btn)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        return tab
    
    def _import_diag_data(self) -> None:
        """Import diagnostics data."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Diagnostics Data", "", "All Files (*.*)")
        if file_path:
            QMessageBox.information(self, "Import", f"Importing diagnostics data from: {file_path}")
    
    def _export_diag_data(self) -> None:
        """Export diagnostics data."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Diagnostics Data", "", "All Files (*.*)")
        if file_path:
            QMessageBox.information(self, "Export", f"Exporting diagnostics data to: {file_path}")
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update diagnostics tab with telemetry data."""
        # Pass telemetry to auto diagnostic widget if available
        if self.auto_diag_widget and hasattr(self.auto_diag_widget, 'set_telemetry_data'):
            # Convert float values to Any for compatibility
            telemetry_dict = {k: float(v) for k, v in data.items()}
            self.auto_diag_widget.set_telemetry_data(telemetry_dict)
        
        # Update graph widget if available
        if hasattr(self, 'diag_graph_widget') and self.diag_graph_widget:
            if hasattr(self.diag_graph_widget, 'update_data'):
                self.diag_graph_widget.update_data(data)
            elif hasattr(self.diag_graph_widget, 'add_data'):
                for key, value in data.items():
                    self.diag_graph_widget.add_data(key, value)
        
    def _create_trigger_analysis_tab(self) -> QWidget:
        """Create trigger analysis tab with oscilloscope and logger."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QComboBox, QSpinBox
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Use EnhancedGraphPanel which already has trigger oscilloscope and logger
        try:
            from ui.telemetryiq_widgets import EnhancedGraphPanel
            self.trigger_panel = EnhancedGraphPanel()
            layout.addWidget(self.trigger_panel, stretch=1)
        except (ImportError, AttributeError) as e:
            LOGGER.debug("EnhancedGraphPanel unavailable: %s", e)
            placeholder = QLabel("Trigger Analysis Panel (Oscilloscope & Logger)")
            placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
            layout.addWidget(placeholder, stretch=1)
        except Exception as e:
            LOGGER.warning("Error initializing trigger panel: %s", e)
            placeholder = QLabel("Trigger Analysis Panel (Oscilloscope & Logger)")
            placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
            layout.addWidget(placeholder, stretch=1)
        
        return tab
        
    def _create_data_logging_tab(self) -> QWidget:
        """Create data logging tab with internal and PC logging."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSpinBox, QTextEdit
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Logging settings
        settings_group = QGroupBox("Logging Settings")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        settings_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #2c3e50;
            }}
        """)
        settings_layout = QVBoxLayout()
        
        # Internal logging
        settings_layout.addWidget(QLabel("Internal Logging: Up to 1000Hz"))
        self.internal_log_enabled = QCheckBox("Internal Log Enabled")
        self.internal_log_enabled.setChecked(True)
        self.internal_log_enabled.setStyleSheet("color: #2c3e50;")
        settings_layout.addWidget(self.internal_log_enabled)
        
        # PC logging
        settings_layout.addWidget(QLabel("PC Logging: 20Hz"))
        self.pc_log_enabled = QCheckBox("PC Log Enabled")
        self.pc_log_enabled.setChecked(True)
        self.pc_log_enabled.setStyleSheet("color: #2c3e50;")
        settings_layout.addWidget(self.pc_log_enabled)
        
        # Auto-start/stop conditions
        auto_group = QGroupBox("Automatic Start/Stop Conditions")
        auto_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
                background-color: #2c3e50;
            }}
        """)
        auto_layout = QVBoxLayout()
        
        auto_layout.addWidget(QLabel("Start Condition:"))
        self.log_start_condition = QComboBox()
        self.log_start_condition.addItems(["Speed > 50 kph", "MAP > 100 kPa", "RPM > 3000", "Manual"])
        self.log_start_condition.setStyleSheet("color: #2c3e50; background-color: #2c3e50; border: 1px solid #bdc3c7;")
        auto_layout.addWidget(self.log_start_condition)
        
        auto_layout.addWidget(QLabel("Stop Condition:"))
        self.log_stop_condition = QComboBox()
        self.log_stop_condition.addItems(["Speed < 10 kph", "MAP < 50 kPa", "RPM < 1000", "Manual"])
        self.log_stop_condition.setStyleSheet("color: #2c3e50; background-color: #2c3e50; border: 1px solid #bdc3c7;")
        auto_layout.addWidget(self.log_stop_condition)
        
        auto_group.setLayout(auto_layout)
        settings_layout.addWidget(auto_group)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Log viewer
        log_viewer = QTextEdit()
        log_viewer.setReadOnly(True)
        log_viewer.setStyleSheet("background-color: #2c3e50; color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
        log_viewer.setPlainText("Log viewer - Internal up to 1000Hz, PC logging 20Hz\nUse zoom/scroll tools to analyze data.")
        layout.addWidget(log_viewer, stretch=1)
        
        return tab
        
    def _create_io_management_tab(self) -> QWidget:
        """Create I/O management tab with virtual inputs/outputs."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Virtual Inputs/Outputs table
        io_group = QGroupBox("Virtual Inputs/Internal Outputs")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        io_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #2c3e50;
            }}
        """)
        io_layout = QVBoxLayout()
        
        self.io_table = QTableWidget()
        self.io_table.setColumnCount(4)
        self.io_table.setHorizontalHeaderLabels(["Type", "Name", "Function", "Condition"])
        self.io_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.io_table.setMinimumHeight(get_scaled_size(300))
        self.io_table.setStyleSheet("""
            QTableWidget {
                background-color: #2c3e50;
                color: #2c3e50;
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 5px;
                border: 1px solid #bdc3c7;
            }
        """)
        
        # Add example virtual outputs
        examples = [
            ("Output", "Internal Out 1", "AC Request", "IF IAT > 50C"),
            ("Output", "Internal Out 2", "Fan Control", "IF Coolant > 90C"),
            ("Output", "Internal Out 3", "Boost Solenoid", "IF MAP > 100 kPa"),
            ("Input", "Virtual In 1", "Launch Button", "Digital Input 1"),
            ("Input", "Virtual In 2", "Rolling Launch", "Speed > 5 mph"),
        ]
        
        self.io_table.setRowCount(len(examples))
        for row, (io_type, name, function, condition) in enumerate(examples):
            self.io_table.setItem(row, 0, QTableWidgetItem(io_type))
            self.io_table.setItem(row, 1, QTableWidgetItem(name))
            self.io_table.setItem(row, 2, QTableWidgetItem(function))
            self.io_table.setItem(row, 3, QTableWidgetItem(condition))
        
        io_layout.addWidget(self.io_table)
        
        # Flexible user output functions
        user_outputs_group = QGroupBox("Flexible User Output Functions (GPOs)")
        user_outputs_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
                background-color: #2c3e50;
            }}
        """)
        user_outputs_layout = QVBoxLayout()
        
        user_outputs_layout.addWidget(QLabel("GPO 1:"))
        self.gpo1 = QComboBox()
        self.gpo1.addItems(["Disabled", "Fan Control", "AC Request", "Boost Solenoid", "Custom"])
        self.gpo1.setStyleSheet("color: #2c3e50; background-color: #2c3e50; border: 1px solid #bdc3c7;")
        user_outputs_layout.addWidget(self.gpo1)
        
        user_outputs_group.setLayout(user_outputs_layout)
        io_layout.addWidget(user_outputs_group)
        
        # Flexible PWM/FREQ outputs
        pwm_group = QGroupBox("Flexible User PWM/FREQ Output Functions")
        pwm_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {get_scaled_size(5)}px; padding-top: {get_scaled_size(5)}px;
                background-color: #2c3e50;
            }}
        """)
        pwm_layout = QVBoxLayout()
        
        pwm_layout.addWidget(QLabel("PWM Output 1:"))
        self.pwm1 = QComboBox()
        self.pwm1.addItems(["Disabled", "Idle Solenoid", "Wastegate", "Custom"])
        self.pwm1.setStyleSheet("color: #2c3e50; background-color: #2c3e50; border: 1px solid #bdc3c7;")
        pwm_layout.addWidget(self.pwm1)
        
        pwm_group.setLayout(pwm_layout)
        io_layout.addWidget(pwm_group)
        
        io_group.setLayout(io_layout)
        layout.addWidget(io_group, stretch=1)
        
        return tab
        
    def _create_can_config_tab(self) -> QWidget:
        """Create CAN bus configuration tab."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # CAN Inputs (Advanced)
        can_inputs_group = QGroupBox("CAN Inputs (Advanced)")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        can_inputs_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #2c3e50;
            }}
        """)
        can_inputs_layout = QVBoxLayout()
        
        can_inputs_layout.addWidget(QLabel("Receive CAN data from external electronics (e.g., OEM vehicle buttons)"))
        
        self.can_inputs_table = QTableWidget()
        self.can_inputs_table.setColumnCount(3)
        self.can_inputs_table.setHorizontalHeaderLabels(["CAN ID", "Data Field", "Function"])
        self.can_inputs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.can_inputs_table.setMaximumHeight(get_scaled_size(200))
        self.can_inputs_table.setStyleSheet("""
            QTableWidget {
                background-color: #2c3e50;
                color: #2c3e50;
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 5px;
                border: 1px solid #bdc3c7;
            }
        """)
        
        can_inputs_table_data = [
            ("0x123", "Button State", "Launch Control"),
            ("0x456", "Gear Position", "Shift Map"),
            ("0x789", "Sport Mode", "Boost Level"),
        ]
        
        self.can_inputs_table.setRowCount(len(can_inputs_table_data))
        for row, (can_id, data_field, function) in enumerate(can_inputs_table_data):
            self.can_inputs_table.setItem(row, 0, QTableWidgetItem(can_id))
            self.can_inputs_table.setItem(row, 1, QTableWidgetItem(data_field))
            self.can_inputs_table.setItem(row, 2, QTableWidgetItem(function))
        
        can_inputs_layout.addWidget(self.can_inputs_table)
        can_inputs_group.setLayout(can_inputs_layout)
        layout.addWidget(can_inputs_group)
        
        # CAN for OEM protocols, OBDII, and CAN modules
        can_protocols_group = QGroupBox("CAN for OEM Protocols, OBDII, and CAN Modules")
        can_protocols_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #2c3e50;
            }}
        """)
        can_protocols_layout = QVBoxLayout()
        
        can_protocols_layout.addWidget(QLabel("Protocol:"))
        self.can_protocol = QComboBox()
        self.can_protocol.addItems(["OEM Native", "OBDII", "CAN Module", "Custom"])
        self.can_protocol.setStyleSheet("color: #2c3e50; background-color: #2c3e50; border: 1px solid #bdc3c7;")
        can_protocols_layout.addWidget(self.can_protocol)
        
        self.can_enabled = QCheckBox("CAN Bus Enabled")
        self.can_enabled.setChecked(True)
        self.can_enabled.setStyleSheet("color: #2c3e50;")
        can_protocols_layout.addWidget(self.can_enabled)
        
        can_protocols_group.setLayout(can_protocols_layout)
        layout.addWidget(can_protocols_group)
        
        layout.addStretch()
        return tab
        
    def _create_sensor_utilities_tab(self) -> QWidget:
        """Create sensor utilities tab."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Measure Injector Resistance
        injector_group = QGroupBox("Measure Injector Resistance")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        injector_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #ffffff;
            }}
        """)
        injector_layout = QVBoxLayout()
        
        measure_btn = QPushButton("Measure Injector Resistance")
        measure_btn.setStyleSheet("background-color: #0080ff; color: #2c3e50; padding: 5px 15px;")
        measure_btn.clicked.connect(self._measure_injector_resistance)
        injector_layout.addWidget(measure_btn)
        
        self.injector_results = QLabel("Click button to measure resistance")
        self.injector_results.setStyleSheet("color: #2c3e50; padding: 10px;")
        injector_layout.addWidget(self.injector_results)
        
        injector_group.setLayout(injector_layout)
        layout.addWidget(injector_group)
        
        # TYPE-K sensor configuration
        typek_group = QGroupBox("TYPE-K Sensor Configuration")
        typek_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #ffffff;
            }}
        """)
        typek_layout = QVBoxLayout()
        
        typek_layout.addWidget(QLabel("Report IAT up to 350°C / 660°F"))
        typek_layout.addWidget(QLabel("High-Range Scale:"))
        self.typek_scale = QComboBox()
        self.typek_scale.addItems(["Standard (0-150°C)", "High Range (0-350°C)"])
        self.typek_scale.setStyleSheet("color: #2c3e50; background-color: #ffffff; border: 1px solid #bdc3c7;")
        typek_layout.addWidget(self.typek_scale)
        
        typek_group.setLayout(typek_layout)
        layout.addWidget(typek_group)
        
        # Speedometer/Tachometer outputs
        outputs_group = QGroupBox("Speedometer & Tachometer Outputs")
        outputs_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #ffffff;
            }}
        """)
        outputs_layout = QVBoxLayout()
        
        outputs_layout.addWidget(QLabel("Speedometer Output Function:"))
        self.speedo_output = QComboBox()
        self.speedo_output.addItems(["Disabled", "PWM", "Frequency", "CAN"])
        self.speedo_output.setStyleSheet("color: #2c3e50; background-color: #ffffff; border: 1px solid #bdc3c7;")
        outputs_layout.addWidget(self.speedo_output)
        
        outputs_layout.addWidget(QLabel("Tachometer Output:"))
        self.tach_output = QComboBox()
        self.tach_output.addItems(["5V", "12V", "External Flyback Coil"])
        self.tach_output.setStyleSheet("color: #2c3e50; background-color: #ffffff; border: 1px solid #bdc3c7;")
        outputs_layout.addWidget(self.tach_output)
        
        outputs_group.setLayout(outputs_layout)
        layout.addWidget(outputs_group)
        
        # Timers and distance counters
        counters_group = QGroupBox("Timers and Distance Counters")
        counters_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #ffffff;
            }}
        """)
        counters_layout = QVBoxLayout()
        
        self.timer_0_60 = QLabel("0-60 mph: --")
        self.timer_0_60.setStyleSheet("color: #2c3e50; font-size: 14px;")
        counters_layout.addWidget(self.timer_0_60)
        
        self.timer_quarter = QLabel("1/4 mile: --")
        self.timer_quarter.setStyleSheet("color: #2c3e50; font-size: 14px;")
        counters_layout.addWidget(self.timer_quarter)
        
        counters_group.setLayout(counters_layout)
        layout.addWidget(counters_group)
        
        layout.addStretch()
        return tab
        
    def _create_errors_tab(self) -> QWidget:
        """Create errors tab with built-in error diagnostics."""
        from ui.ui_scaling import get_scaled_size, get_scaled_font_size
        from PySide6.QtWidgets import QVBoxLayout, QLabel, QListWidget, QListWidgetItem
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Error diagnostics panel
        errors_group = QGroupBox("Built-in Error Diagnostics and Handling")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        errors_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #2c3e50;
                border: {group_border}px solid #bdc3c7; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
                background-color: #2c3e50;
            }}
        """)
        errors_layout = QVBoxLayout()
        
        self.errors_list = QListWidget()
        self.errors_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        
        # Add example DTCs
        example_dtcs = [
            "P0301 - Cylinder 1 Misfire Detected",
            "P0171 - System Too Lean (Bank 1)",
            "P0420 - Catalyst System Efficiency Below Threshold",
            "No current errors"
        ]
        
        for dtc in example_dtcs:
            item = QListWidgetItem(dtc)
            if "No current" in dtc:
                item.setForeground(QBrush(QColor("#00ff00")))
            else:
                item.setForeground(QBrush(QColor("#ff0000")))
            self.errors_list.addItem(item)
        
        errors_layout.addWidget(self.errors_list)
        errors_group.setLayout(errors_layout)
        layout.addWidget(errors_group, stretch=1)
        
        return tab
        
    def _measure_injector_resistance(self) -> None:
        """Measure injector resistance."""
        from PySide6.QtWidgets import QMessageBox
        # Simulate measurement
        results = "Injector 1: 12.5 Ω\nInjector 2: 12.3 Ω\nInjector 3: 12.7 Ω\nInjector 4: 12.4 Ω"
        self.injector_results.setText(results)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Injector Resistance")
        msg.setText("Injector Resistance Measurements:\n\n" + results)
        msg.exec()
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update diagnostics tab with data."""
        if hasattr(self, 'health_widget') and self.health_widget:
            if hasattr(self.health_widget, 'update_score'):
                # Extract health score from data or calculate
                health_score = data.get("health_score", 95.0)
                self.health_widget.update_score(health_score)
        
        if hasattr(self, 'ai_panel') and self.ai_panel:
            if hasattr(self.ai_panel, 'update_insight'):
                self.ai_panel.update_insight("System monitoring active")
        
        # Update auto diagnostic widget with telemetry
        if hasattr(self, 'auto_diag_widget') and self.auto_diag_widget:
            if hasattr(self.auto_diag_widget, 'set_telemetry_data'):
                # Convert float values to Any for compatibility
                telemetry_dict = {k: float(v) for k, v in data.items()}
                self.auto_diag_widget.set_telemetry_data(telemetry_dict)


class PerformanceTab(QWidget):
    """Performance tracking module tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup performance tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Set background
        self.setStyleSheet("background-color: #e8e9ea;")
        
        # Title
        title = QLabel("Performance Tracking")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Sub-tabs for performance features
        perf_tabs = QTabWidget()
        perf_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; background-color: #e8e9ea; }
            QTabBar::tab { background-color: #ffffff; color: #2c3e50; padding: 8px 15px; }
            QTabBar::tab:selected { background-color: #e8e9ea; border-bottom: 2px solid #0080ff; }
        """)
        
        # Performance tracking tab
        if DragyPerformanceView:
            try:
                self.dragy_view = DragyPerformanceView()
                perf_tabs.addTab(self.dragy_view, "Performance")
            except (ImportError, AttributeError) as e:
                LOGGER.debug("Performance tracking unavailable: %s", e)
                placeholder = QLabel("Performance tracking unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                perf_tabs.addTab(placeholder, "Performance")
            except Exception as e:
                LOGGER.warning("Error initializing performance tracking: %s", e)
                placeholder = QLabel("Performance tracking unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                perf_tabs.addTab(placeholder, "Performance")
        else:
            placeholder = QLabel("Performance tracking module not available")
            placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
            perf_tabs.addTab(placeholder, "Performance")
        
        # Graphing tab
        graphing_tab = self._create_perf_graphing_tab()
        perf_tabs.addTab(graphing_tab, "📊 Graphing")
        
        # Import/Export tab
        import_export_tab = self._create_perf_import_export_tab()
        perf_tabs.addTab(import_export_tab, "Import/Export")
        
        layout.addWidget(perf_tabs, stretch=1)
        
    def _create_perf_graphing_tab(self) -> QWidget:
        """Create graphing tab for performance."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        try:
            from ui.advanced_log_graphing import AdvancedLogGraphingWidget
            self.perf_graph_widget = AdvancedLogGraphingWidget()
            layout.addWidget(self.perf_graph_widget, stretch=1)
        except ImportError:
            try:
                from ui.ecu_tuning_widgets import RealTimeGraph
                self.perf_graph_widget = RealTimeGraph()
                layout.addWidget(self.perf_graph_widget, stretch=1)
            except ImportError:
                placeholder = QLabel("Graphing widget not available")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                layout.addWidget(placeholder, stretch=1)
                self.perf_graph_widget = None
        
        return tab
    
    def _create_perf_import_export_tab(self) -> QWidget:
        """Create import/export tab for performance."""
        from PySide6.QtWidgets import QVBoxLayout, QPushButton, QGroupBox, QFileDialog, QMessageBox
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Import
        import_group = QGroupBox("Import Performance Data")
        import_layout = QVBoxLayout()
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(lambda: self._import_perf_data())
        import_layout.addWidget(import_btn)
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Export
        export_group = QGroupBox("Export Performance Data")
        export_layout = QVBoxLayout()
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(lambda: self._export_perf_data())
        export_layout.addWidget(export_btn)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        return tab
    
    def _import_perf_data(self) -> None:
        """Import performance data."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Performance Data", "", "All Files (*.*)")
        if file_path:
            QMessageBox.information(self, "Import", f"Importing from: {file_path}")
    
    def _export_perf_data(self) -> None:
        """Export performance data."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Performance Data", "", "All Files (*.*)")
        if file_path:
            QMessageBox.information(self, "Export", f"Exporting to: {file_path}")
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update performance tab with data."""
        if hasattr(self, 'dragy_view') and self.dragy_view:
            if hasattr(self.dragy_view, 'update_data'):
                self.dragy_view.update_data(data)
        
        if hasattr(self, 'perf_graph_widget') and self.perf_graph_widget:
            if hasattr(self.perf_graph_widget, 'update_data'):
                self.perf_graph_widget.update_data(data)
            elif hasattr(self.perf_graph_widget, 'add_data'):
                for key, value in data.items():
                    self.perf_graph_widget.add_data(key, value)


class ConsoleLoggingTab(QWidget):
    """Console and logging module tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup console/logging tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Set background
        self.setStyleSheet("background-color: #e8e9ea;")
        
        # Title
        title = QLabel("Console & Logging")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Console output area
        from ui.console_log_viewer import ConsoleLogViewer
        try:
            self.console_viewer = ConsoleLogViewer()
            layout.addWidget(self.console_viewer, stretch=1)
        except (ImportError, AttributeError) as e:
            LOGGER.debug("Console log viewer unavailable: %s", e)
            placeholder = QLabel("Console log viewer will be displayed here")
            placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #ffffff;")
            layout.addWidget(placeholder, stretch=1)
        except Exception as e:
            LOGGER.warning("Error initializing console log viewer: %s", e)
            placeholder = QLabel("Console log viewer will be displayed here")
            placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #ffffff;")
            layout.addWidget(placeholder, stretch=1)
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update console/logging tab with telemetry data."""
        pass


class SettingsTab(QWidget):
    """Settings and configuration module tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup settings tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Set background
        self.setStyleSheet("background-color: #e8e9ea;")
        
        # Title
        title = QLabel("Settings & Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Settings content
        from PySide6.QtWidgets import QGroupBox, QPushButton
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            
                background-color: #ffffff;}
        """)
        conn_layout = QVBoxLayout()
        conn_btn = QPushButton("Configure ECU Connection")
        conn_btn.setStyleSheet("background-color: #404040; color: #2c3e50; padding: 8px;")
        conn_layout.addWidget(conn_btn)
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Display settings
        disp_group = QGroupBox("Display Settings")
        disp_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            
                background-color: #ffffff;}
        """)
        disp_layout = QVBoxLayout()
        theme_btn = QPushButton("Theme Settings")
        theme_btn.setStyleSheet("background-color: #404040; color: #2c3e50; padding: 8px;")
        theme_btn.clicked.connect(self._open_theme_customizer)
        disp_layout.addWidget(theme_btn)
        disp_group.setLayout(disp_layout)
        layout.addWidget(disp_group)
        
        layout.addStretch()
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update settings tab with data."""
        pass


class MainContainerWindow(QWidget):
    """Main container window with tabs for all modules."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Tuner Agent - Main Interface")
        
        # Initialize scaler
        self.scaler = UIScaler.get_instance()
        
        # Get screen size to ensure window fits
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                # Get both available and full geometry
                available_geometry = screen.availableGeometry()
                full_geometry = screen.geometry()
                # Use FULL geometry for max size (what Qt maximize actually uses)
                # This prevents window from exceeding screen when maximized
                screen_width = full_geometry.width()
                screen_height = full_geometry.height()
                # Use available for initial sizing (accounts for taskbars)
                available_width = available_geometry.width()
                available_height = available_geometry.height()
                screen_geometry = available_geometry  # Store for reference
            else:
                screen_width, screen_height = 1920, 1080  # Default fallback
                available_width, available_height = 1920, 1080
                screen_geometry = None
        else:
            screen_width, screen_height = 1920, 1080  # Default fallback
            available_width, available_height = 1920, 1080
            screen_geometry = None
        
        # Set scalable window size with proper constraints based on AVAILABLE screen size
        base_width, base_height = min(1600, available_width - 100), min(900, available_height - 100)
        min_width, min_height = 1000, 600
        
        # Calculate scaled sizes
        scaled_base_width = get_scaled_size(base_width)
        scaled_base_height = get_scaled_size(base_height)
        scaled_min_width = get_scaled_size(min_width)
        scaled_min_height = get_scaled_size(min_height)
        
        # CRITICAL: Clamp scaled sizes to available screen - scaling can make window too large
        final_width = min(scaled_base_width, available_width)
        final_height = min(scaled_base_height, available_height)
        final_min_width = min(scaled_min_width, available_width)
        final_min_height = min(scaled_min_height, available_height)
        
        self.setMinimumSize(final_min_width, final_min_height)
        # Set maximum size to available screen size to prevent window from exceeding screen
        # This is better than using MAX_WIDGET_SIZE because it prevents the window from
        # going off-screen while still allowing maximize to work properly
        self.setMaximumSize(available_width, available_height)
        self.resize(final_width, final_height)
        
        # Store screen geometry for reference
        self._screen_geometry = screen_geometry if app and screen else None
        self._available_width = available_width
        self._available_height = available_height
        self._full_width = screen_width
        self._full_height = screen_height
        self._maximized = False  # Track maximize state
        self._handling_maximize = False  # Flag to prevent recursion
        self._resizing = False  # Flag to prevent resize recursion
        
        # Ensure window is resizable with standard window flags including maximize
        from PySide6.QtCore import Qt
        # Use standard window flags that allow maximize
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Set size policy to allow resizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Allow window to maximize to full screen
        self.setWindowState(Qt.WindowState.WindowNoState)  # Ensure not in maximized state initially
        
        # Center window on screen
        if app and screen:
            frame_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            frame_geometry.moveCenter(center_point)
            self.move(frame_geometry.topLeft())
        
        self._telemetry_data: Dict[str, float] = {}
        self._connection_status = False
        self._connection_type = "USB"
        
        # Initialize global backup manager
        self.backup_manager = None
        try:
            from services.backup_manager import BackupManager
            self.backup_manager = BackupManager()
        except Exception as e:
            print(f"[WARN] Backup manager unavailable: {e}")
        
        # Initialize mobile API client (if server is running)
        self.mobile_api_client = None
        try:
            from api.mobile_api_integration import initialize_mobile_api
            self.mobile_api_client = initialize_mobile_api()
            # Start client in background (async will be handled by QTimer)
            print("[INFO] Mobile API client initialized (will start on first telemetry update)")
        except Exception as e:
            print(f"[WARN] Mobile API client unavailable: {e}")
        
        # Initialize floating AI advisor
        if FloatingAIAdvisorManager:
            try:
                self.ai_advisor_manager = FloatingAIAdvisorManager(self)
            except Exception as e:
                LOGGER.warning("Failed to initialize floating AI advisor: %s", e)
                self.ai_advisor_manager = None
        
        # Initialize voice command handler
        if VoiceCommandHandler:
            try:
                self.voice_handler = VoiceCommandHandler()
                if self.voice_handler.is_available():
                    self.voice_handler.command_received.connect(self._handle_voice_command)
                    LOGGER.info("Voice command handler initialized")
            except Exception as e:
                LOGGER.warning("Failed to initialize voice commands: %s", e)
                self.voice_handler = None
        
        # Initialize haptic feedback
        if get_haptic_feedback:
            try:
                self.haptic = get_haptic_feedback()
            except Exception as e:
                LOGGER.warning("Failed to initialize haptic feedback: %s", e)
                self.haptic = None
        
        self.setup_ui()
        self._start_update_timer()
        
    def setup_ui(self) -> None:
        """Setup main container with tabbed interface."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(5)  # Small margin to prevent edge-to-edge grabbing
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(get_scaled_size(5))
        
        # Set overall background - modern racing theme
        theme = get_racing_theme()
        self.setStyleSheet(get_racing_stylesheet("main_window"))
        
        # Top control bar with mode selector and status
        top_bar = QHBoxLayout()
        margin = get_scaled_size(10)
        top_bar.setContentsMargins(margin, margin, margin, margin)
        top_bar.setSpacing(get_scaled_size(15))
        
        # Car image widget (scaled)
        try:
            self.car_image = CarImageWidget()
            self.car_image.setMaximumWidth(get_scaled_size(200))
            top_bar.addWidget(self.car_image)
        except (ImportError, AttributeError) as e:
            LOGGER.debug("Car image widget unavailable: %s", e)
            # Continue without car image
        except Exception as e:
            LOGGER.warning("Error initializing car image widget: %s", e)
            # Continue without car image
        
        # Racing mode selector
        mode_group = QGroupBox("Racing Mode")
        mode_group.setStyleSheet(get_racing_stylesheet("group_box"))
        mode_layout = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Tuning", "Qualifying", "Race", "Wet Race", "Practice", "Street"
        ])
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.setStyleSheet(get_racing_stylesheet("input_field"))
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        mode_group.setLayout(mode_layout)
        top_bar.addWidget(mode_group)
        
        # Initialize contextual mode manager
        self.mode_manager = ContextualModeManager()
        
        # Safety alerts system
        self.safety_alerts = SafetyAlertsSystem(parent=self)
        self.safety_alerts_panel = SafetyAlertsPanel(self.safety_alerts)
        self.safety_alerts_panel.setMaximumHeight(get_scaled_size(250))
        top_bar.addWidget(self.safety_alerts_panel, stretch=1)
        
        # Predictive analytics panel
        self.analytics_panel = PredictiveAnalyticsPanel()
        self.analytics_panel.setMaximumWidth(get_scaled_size(300))
        top_bar.addWidget(self.analytics_panel)
        
        # License status indicator
        try:
            from core.license_manager import get_license_manager
            self.license_manager = get_license_manager()
            
            license_group = QGroupBox("License")
            license_group.setStyleSheet(get_racing_stylesheet("group_box"))
            license_layout = QVBoxLayout()
            license_layout.setContentsMargins(5, 5, 5, 5)
            
            self.license_status_label = QLabel()
            self.license_status_label.setStyleSheet("color: #2c3e50; font-size: 10px; font-weight: bold;")
            license_layout.addWidget(self.license_status_label)
            
            self.license_btn = QPushButton("Manage License")
            self.license_btn.setStyleSheet("background-color: #404040; color: #2c3e50; padding: 3px 8px; font-size: 9px;")
            self.license_btn.clicked.connect(self._show_license_dialog)
            license_layout.addWidget(self.license_btn)
            
            license_group.setLayout(license_layout)
            license_group.setMaximumWidth(get_scaled_size(150))
            top_bar.addWidget(license_group)
            
            # Update license status
            self._update_license_status()
        except Exception as e:
            print(f"[WARN] Could not load license manager: {e}")
            self.license_manager = None
        
        # AI Advisor "Q" widget
        if AIAdvisorWidget:
            try:
                self.ai_advisor_widget = AIAdvisorWidget()
                self.ai_advisor_widget.setMaximumWidth(get_scaled_size(350))
                self.ai_advisor_widget.setMaximumHeight(get_scaled_size(400))
                top_bar.addWidget(self.ai_advisor_widget)
            except Exception as e:
                print(f"[WARN] Could not load AI Advisor widget: {e}")
        
        # Configuration change notifier
        try:
            from ui.config_change_notifier import ConfigChangeNotifier
            from services.config_change_hook import ConfigChangeHook
            
            # Get config monitor from hook
            config_hook = ConfigChangeHook.get_instance()
            config_monitor = config_hook.get_monitor()
            
            self.config_notifier = ConfigChangeNotifier(config_monitor=config_monitor)
            self.config_notifier.setMaximumWidth(get_scaled_size(400))
            self.config_notifier.setMaximumHeight(get_scaled_size(250))
            
            # Register callback to show notifications
            def on_config_change(warnings, change_info):
                if warnings:
                    self.config_notifier.notify_change(
                        change_info["change_type"],
                        change_info["category"],
                        change_info["parameter"],
                        change_info["old_value"],
                        change_info["new_value"],
                        self._telemetry_data,
                    )
            
            config_hook.register_callback(on_config_change)
            
            # Add to layout (will show/hide as needed)
            top_bar.addWidget(self.config_notifier)
        except Exception as e:
            print(f"[WARN] Could not load config change notifier: {e}")
            self.config_notifier = None
        
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        
        # Main tab widget for all modules with racing theme - using multi-row layout
        self.tabs = MultiRowTabWidget()
        self.tabs.setStyleSheet(get_racing_stylesheet("tab_widget"))
        
        # Set size policy for tabs - use Preferred instead of Expanding to prevent forced expansion
        self.tabs.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Dashboard tab (first tab - customizable dashboard)
        # Try Modern Racing Dashboard first, fallback to DashboardTab
        self.dashboard_tab = None
        if ModernRacingDashboard:
            try:
                def get_telemetry():
                    return self._telemetry_data
                
                def panic_callback():
                    """Handle panic button - flash safe stock map to ECU."""
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        "Panic Button - Flash Safe Map",
                        "Flash safe stock map to ECU?\n\nThis will restore factory settings and may affect your current tune.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            # Try to use ECU control service to flash safe map
                            from services.ecu_control import ECUControl
                            ecu_control = ECUControl()
                            
                            # Get stock/safe backup if available
                            backups = ecu_control.list_backups()
                            safe_backup = None
                            for backup in backups:
                                if "stock" in backup.backup_id.lower() or "safe" in backup.backup_id.lower() or "factory" in backup.backup_id.lower():
                                    safe_backup = backup
                                    break
                            
                            if safe_backup:
                                success = ecu_control.restore_ecu(safe_backup.backup_id, validate=True)
                                if success:
                                    QMessageBox.information(self, "Safe Map Flashed", f"Safe stock map has been flashed to ECU.\n\nBackup: {safe_backup.backup_id}")
                                    LOGGER.info("Panic button activated - safe map flashed: %s", safe_backup.backup_id)
                                else:
                                    QMessageBox.warning(self, "Flash Failed", "Failed to flash safe map. Please check ECU connection.")
                            else:
                                QMessageBox.warning(self, "No Safe Map", "No stock/safe backup found. Please create a backup first.")
                        except Exception as e:
                            LOGGER.error("Error flashing safe map: %s", e)
                            QMessageBox.warning(self, "Error", f"Failed to flash safe map:\n{e}")
                
                def ai_advisor_callback():
                    """Open AI advisor."""
                    if hasattr(self, 'ai_advisor_manager') and self.ai_advisor_manager:
                        self.ai_advisor_manager._show_chat()
                
                self.dashboard_tab = ModernRacingDashboard(
                    telemetry_provider=get_telemetry,
                    panic_callback=panic_callback,
                    ai_advisor_callback=ai_advisor_callback
                )
                self.tabs.insertTab(0, self.dashboard_tab, "Dashboard")
            except Exception as e:
                LOGGER.warning("Failed to create Modern Racing Dashboard: %s", e)
                # Fallback to DashboardTab if available
                try:
                    from ui.dashboard_tab import DashboardTab
                    self.dashboard_tab = DashboardTab()
                    self.tabs.insertTab(0, self.dashboard_tab, "Dashboard")
                except Exception as e2:
                    LOGGER.warning("Could not load Dashboard tab: %s", e2)
        else:
            # Fallback to DashboardTab if ModernRacingDashboard not available
            try:
                from ui.dashboard_tab import DashboardTab
                self.dashboard_tab = DashboardTab()
                self.tabs.insertTab(0, self.dashboard_tab, "Dashboard")
            except Exception as e:
                LOGGER.warning("Could not load Dashboard tab: %s", e)
        
        # Sensors tab
        try:
            from ui.sensors_tab import SensorsTab
            self.sensors_tab = SensorsTab()
            self.tabs.addTab(self.sensors_tab, "Sensors")
        except Exception as e:
            print(f"[WARN] Could not load Sensors tab: {e}")
        
        # ECU Tuning tab (with sub-tabs for different ECU functions)
        self.ecu_tab = ECUTuningTab()
        self.tabs.addTab(self.ecu_tab, "Fuel Table")
        
        # Import ECU Support tab (Honda, Nissan, Toyota, etc.)
        try:
            if ImportECUTab:
                self.import_ecu_tab = ImportECUTab()
                self.tabs.addTab(self.import_ecu_tab, "Import ECU")
        except Exception as e:
            print(f"[WARN] Could not load Import ECU tab: {e}")
        
        # Domestic ECU Support tab (Ford, GM, Dodge)
        try:
            if DomesticECUTab:
                self.domestic_ecu_tab = DomesticECUTab()
                self.tabs.addTab(self.domestic_ecu_tab, "Domestic ECU")
        except Exception as e:
            print(f"[WARN] Could not load Domestic ECU tab: {e}")
        
        # Advanced Parameter Access tab
        try:
            if AdvancedParametersTab:
                self.advanced_params_tab = AdvancedParametersTab()
                self.tabs.addTab(self.advanced_params_tab, "Advanced Parameters")
        except Exception as e:
            print(f"[WARN] Could not load Advanced Parameters tab: {e}")
        
        # 3D Individual Cylinder Control tab
        try:
            if CylinderControlTab:
                self.cylinder_control_tab = CylinderControlTab()
                self.tabs.addTab(self.cylinder_control_tab, "Cylinder Control")
        except Exception as e:
            print(f"[WARN] Could not load Cylinder Control tab: {e}")
        
        # Advanced Features tab (Diagnostics, Control Strategies, Code Editor, etc.)
        try:
            if AdvancedFeaturesTab:
                self.advanced_features_tab = AdvancedFeaturesTab()
                self.tabs.addTab(self.advanced_features_tab, "Advanced Features")
        except Exception as e:
            print(f"[WARN] Could not load Advanced Features tab: {e}")
        
        # AI Intelligence tab (Advanced Diagnostics & Self-Learning)
        try:
            if AIIntelligenceTab:
                self.ai_intelligence_tab = AIIntelligenceTab()
                self.tabs.addTab(self.ai_intelligence_tab, "AI Intelligence")
        except Exception as e:
            print(f"[WARN] Could not load AI Intelligence tab: {e}")
        
        # Auto-Detection tab (Global auto-detection)
        try:
            if AutoDetectionTab:
                self.auto_detection_tab = AutoDetectionTab()
                self.tabs.addTab(self.auto_detection_tab, "Auto-Detection")
        except Exception as e:
            print(f"[WARN] Could not load Auto-Detection tab: {e}")
        
        # Backup Manager tab
        try:
            if BackupManagerTab:
                self.backup_manager_tab = BackupManagerTab()
                self.tabs.addTab(self.backup_manager_tab, "Backup Manager")
        except Exception as e:
            print(f"[WARN] Could not load Backup Manager tab: {e}")
        
        # Hardware Interface tab
        try:
            if HardwareInterfaceTab:
                self.hardware_interface_tab = HardwareInterfaceTab()
                self.tabs.addTab(self.hardware_interface_tab, "Hardware Interfaces")
        except Exception as e:
            print(f"[WARN] Could not load Hardware Interface tab: {e}")
        
        # USB Camera tab
        try:
            if USBCameraTab:
                self.usb_camera_tab = USBCameraTab()
                self.tabs.addTab(self.usb_camera_tab, "USB Cameras")
        except Exception as e:
            print(f"[WARN] Could not load USB Camera tab: {e}")
        
        # Import new telemetryIQ tabs
        from ui.telemetryiq_tabs import ProtectionsTab, MotorsportTab, TransmissionTab
        
        # Protections tab
        self.protections_tab = ProtectionsTab()
        self.tabs.addTab(self.protections_tab, "Protections")
        
        # Motorsport tab
        self.motorsport_tab = MotorsportTab()
        self.tabs.addTab(self.motorsport_tab, "Motorsport")
        
        # Racing Controls tab (Anti-Lag & Launch Control)
        try:
            from ui.racing_controls_tab import RacingControlsTab
            self.racing_controls_tab = RacingControlsTab()
            self.tabs.addTab(self.racing_controls_tab, "Racing Controls")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load Racing Controls tab: {e}", exc_info=True)
        
        # Shift Light tab
        try:
            if ShiftLightTab:
                from services.shift_light_manager import ShiftLightManager
                self.shift_light_manager = ShiftLightManager()
                self.shift_light_tab = ShiftLightTab()
                self.shift_light_tab.set_shift_light_manager(self.shift_light_manager)
                self.tabs.addTab(self.shift_light_tab, "Shift Light")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load Shift Light tab: {e}", exc_info=True)
        
        # Transbrake tab
        try:
            if TransbrakeTab:
                from services.transbrake_manager import TransbrakeManager
                self.transbrake_manager = TransbrakeManager()
                self.transbrake_tab = TransbrakeTab()
                self.transbrake_tab.set_transbrake_manager(self.transbrake_manager)
                self.tabs.addTab(self.transbrake_tab, "Transbrake")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load Transbrake tab: {e}", exc_info=True)
        
        # Transmission (TCU) tab
        self.transmission_tab = TransmissionTab()
        self.tabs.addTab(self.transmission_tab, "Transmission (TCU)")
        
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
        
        # Telemetry tab
        self.telemetry_tab = TelemetryTab()
        self.tabs.addTab(self.telemetry_tab, "Telemetry")
        
        # Diagnostics tab (enhanced)
        self.diagnostics_tab = DiagnosticsTab()
        self.tabs.addTab(self.diagnostics_tab, "Diagnostics")
        
        # Diesel Tuning tab
        if DieselTuningTab:
            try:
                self.diesel_tuning_tab = DieselTuningTab()
                self.tabs.addTab(self.diesel_tuning_tab, "Diesel Tuning")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load Diesel Tuning tab: {e}", exc_info=True)
        
        # Performance tab
        self.performance_tab = PerformanceTab()
        self.tabs.addTab(self.performance_tab, "Performance")
        
        # Console/Logging tab
        self.console_tab = ConsoleLoggingTab()
        self.tabs.addTab(self.console_tab, "Console & Logging")
        
        # Settings tab
        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Import and add new module tabs
        try:
            from ui.dyno_tab import DynoTab
            self.dyno_tab = DynoTab()
            self.tabs.addTab(self.dyno_tab, "Virtual Dyno")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load Virtual Dyno tab: {e}", exc_info=True)
            # Create a placeholder tab to show it exists but failed to load
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            error_label = QLabel(f"Virtual Dyno tab failed to load:\n{str(e)}")
            error_label.setStyleSheet("color: #ff0000; padding: 20px;")
            error_label.setWordWrap(True)
            placeholder_layout.addWidget(error_label)
            self.tabs.addTab(placeholder, "Virtual Dyno (Error)")
            
        try:
            from ui.drag_racing_tab import DragRacingTab
            self.drag_racing_tab = DragRacingTab()
            self.tabs.addTab(self.drag_racing_tab, "Drag Racing")
        except Exception:
            pass
            
        try:
            from ui.track_learning_tab import TrackLearningTab
            self.track_learning_tab = TrackLearningTab()
            self.tabs.addTab(self.track_learning_tab, "Track Learning")
        except Exception:
            pass
            
        try:
            from ui.auto_tuning_tab import AutoTuningTab
            self.auto_tuning_tab = AutoTuningTab()
            self.tabs.addTab(self.auto_tuning_tab, "Auto Tuning")
        except Exception:
            pass
            
        try:
            from ui.video_overlay_tab import VideoOverlayTab
            self.video_overlay_tab = VideoOverlayTab()
            self.tabs.addTab(self.video_overlay_tab, "Video/Overlay")
            
            # Lap Detection & Track Map tab
            try:
                from ui.lap_detection_tab import LapDetectionTab
                self.lap_detection_tab = LapDetectionTab()
                self.tabs.addTab(self.lap_detection_tab, "Lap Detection")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Lap Detection tab unavailable: {e}")
                placeholder = QLabel("Lap Detection tab unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                self.tabs.addTab(placeholder, "Lap Detection (Error)")
            
            # Session Management tab
            try:
                from ui.session_management_tab import SessionManagementTab
                self.session_management_tab = SessionManagementTab()
                self.tabs.addTab(self.session_management_tab, "Sessions")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Session Management tab unavailable: {e}")
                placeholder = QLabel("Session Management tab unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                self.tabs.addTab(placeholder, "Sessions (Error)")
            
            # Storage Management tab
            try:
                from ui.storage_management_tab import StorageManagementTab
                self.storage_management_tab = StorageManagementTab()
                self.tabs.addTab(self.storage_management_tab, "Storage")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Storage Management tab unavailable: {e}")
                placeholder = QLabel("Storage Management tab unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                self.tabs.addTab(placeholder, "Storage (Error)")
            
            # Network Diagnostics tab
            try:
                from ui.network_diagnostics_tab import NetworkDiagnosticsTab
                self.network_diagnostics_tab = NetworkDiagnosticsTab()
                self.tabs.addTab(self.network_diagnostics_tab, "Network")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Network Diagnostics tab unavailable: {e}")
                placeholder = QLabel("Network Diagnostics tab unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                self.tabs.addTab(placeholder, "Network (Error)")
            
            # Remote Access tab
            try:
                from ui.remote_access_tab import RemoteAccessTab
                self.remote_access_tab = RemoteAccessTab()
                self.tabs.addTab(self.remote_access_tab, "Remote Access")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Remote Access tab unavailable: {e}")
                placeholder = QLabel("Remote Access tab unavailable")
                placeholder.setStyleSheet("color: #2c3e50; padding: 20px; background-color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 4px;")
                self.tabs.addTab(placeholder, "Remote Access (Error)")
        except Exception:
            pass
        
        # Fleet Management Dashboard tab
        try:
            from ui.fleet_dashboard_tab import FleetDashboardTab
            self.fleet_dashboard_tab = FleetDashboardTab()
            self.tabs.addTab(self.fleet_dashboard_tab, "Fleet Management")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load Fleet Dashboard tab: {e}", exc_info=True)
        
        main_layout.addWidget(self.tabs, stretch=1)
        
    def _start_update_timer(self) -> None:
        """Start timer for telemetry updates."""
        # Initialize optimization manager
        try:
            from services.optimization_manager import get_optimization_manager
            self.opt_manager = get_optimization_manager()
        except Exception:
            self.opt_manager = None
        
        # Re-entrancy guard to prevent overlapping updates
        self._updating = False
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_all_tabs)
        self.update_timer.start(200)  # 5 Hz - reduced from 10 Hz to reduce CPU load
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update interface with new telemetry data."""
        self._telemetry_data = data
        
        # Push to remote access service if available
        try:
            from api.remote_access_api import remote_service
            if remote_service:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(remote_service.update_telemetry(data))
                    else:
                        loop.run_until_complete(remote_service.update_telemetry(data))
                except RuntimeError:
                    # No event loop, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(remote_service.update_telemetry(data))
                    loop.close()
        except Exception as e:
            # Silently fail if remote access is not available
            pass
        
        # Use batching if optimization manager is available
        if self.opt_manager:
            should_flush = self.opt_manager.telemetry_batcher.add_update(data)
            if should_flush:
                batched_data = self.opt_manager.telemetry_batcher.get_batch()
                if batched_data:
                    self._update_all_tabs()
        else:
            self._update_all_tabs()
        
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change event."""
        # This can be used for any tab change logic if needed
        pass
    
    def _on_industry_mode_changed(self, mode_text: str) -> None:
        """Handle industry mode change."""
        try:
            from core.industry_mode import IndustryMode, set_industry_mode
            mode = IndustryMode(mode_text.lower())
            set_industry_mode(mode)
            LOGGER.info("Industry mode changed to: %s", mode.value)
            
            # Update UI based on mode (hide/show racing-specific tabs)
            # This would be implemented to show/hide tabs based on mode
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error changing industry mode: {e}", exc_info=True)
    
    def _on_mode_changed(self, mode_text: str) -> None:
        """Handle racing mode change."""
        mode_map = {
            "Tuning": RacingMode.TUNING,
            "Qualifying": RacingMode.QUALIFYING,
            "Race": RacingMode.RACE,
            "Wet Race": RacingMode.WET_RACE,
            "Practice": RacingMode.PRACTICE,
            "Street": RacingMode.STREET,
        }
        mode = mode_map.get(mode_text, RacingMode.TUNING)
        self.mode_manager.set_mode(mode)
        
        # Update UI based on mode
        config = self.mode_manager.get_config()
        # Could hide/show tabs, change colors, etc. based on mode
    
    def _update_all_tabs(self) -> None:
        """Update all tabs with current telemetry."""
        # Re-entrancy guard - prevent overlapping updates
        if self._updating:
            return
        
        self._updating = True
        try:
            data = self._telemetry_data
            
            # Only update if we have data
            if not data:
                return
            
            # Get current visible tab index
            current_tab_index = self.tabs.currentIndex()
            
            # Check safety conditions (always update - important)
            try:
                if hasattr(self, 'safety_alerts'):
                    self.safety_alerts.check_conditions(data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Error updating safety alerts: {e}")
            
            # Update predictive analytics (always update - important)
            try:
                if hasattr(self, 'analytics_panel'):
                    self.analytics_panel.update_telemetry(data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Error updating analytics: {e}")
            
            # Update only visible tab and a few critical tabs to reduce CPU load
            # Always update ECU tab (most important)
            try:
                self.ecu_tab.update_telemetry(data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Error updating ECU tab: {e}")
            
            # Update current visible tab
            try:
                current_widget = self.tabs.currentWidget()
                if current_widget and hasattr(current_widget, 'update_telemetry'):
                    current_widget.update_telemetry(data)
                
                # Update dashboard connection status
                # Check if we have telemetry data (indicates connection)
                if data and len(data) > 0:
                    # If we have data, we're likely connected
                    if not self._connection_status:
                        self._connection_status = True
                        # Try to determine connection type from available interfaces
                        # This is a simple heuristic - could be enhanced
                        self._connection_type = "CAN"  # Default to CAN
                
                if hasattr(self, 'dashboard_tab') and self.dashboard_tab:
                    if hasattr(self.dashboard_tab, 'set_connection_status'):
                        self.dashboard_tab.set_connection_status(
                            self._connection_status,
                            self._connection_type
                        )
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Error updating current tab: {e}")
            
            # Update other tabs less frequently (every 5th call = 1 Hz)
            if not hasattr(self, '_update_counter'):
                self._update_counter = 0
            self._update_counter += 1
            
            if self._update_counter >= 5:
                self._update_counter = 0
                # Update all other tabs at lower frequency
                tabs_to_update = [
                    ('protections_tab', self.protections_tab),
                    ('motorsport_tab', self.motorsport_tab),
                    ('transmission_tab', self.transmission_tab),
                    ('nitrous_tab', self.nitrous_tab),
                    ('turbo_tab', self.turbo_tab),
                    ('e85_tab', self.e85_tab),
                    ('methanol_tab', self.methanol_tab),
                    ('nitro_tab', self.nitro_tab),
                    ('telemetry_tab', self.telemetry_tab),
                    ('diagnostics_tab', self.diagnostics_tab),
                    ('diesel_tuning_tab', self.diesel_tuning_tab if hasattr(self, 'diesel_tuning_tab') else None),
                    ('performance_tab', self.performance_tab),
                    ('console_tab', self.console_tab),
                ]
                
                for tab_name, tab_widget in tabs_to_update:
                    try:
                        if tab_widget and hasattr(tab_widget, 'update_telemetry'):
                            tab_widget.update_telemetry(data)
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"Error updating {tab_name}: {e}")
                
                # Update optional tabs
                optional_tabs = [
                    ('dashboard_tab', 'dashboard_tab'),
                    ('sensors_tab', 'sensors_tab'),
                    ('fleet_dashboard_tab', 'fleet_dashboard_tab'),
                    ('import_ecu_tab', 'import_ecu_tab'),
                    ('domestic_ecu_tab', 'domestic_ecu_tab'),
                    ('advanced_params_tab', 'advanced_params_tab'),
                    ('cylinder_control_tab', 'cylinder_control_tab'),
                    ('advanced_features_tab', 'advanced_features_tab'),
                    ('ai_intelligence_tab', 'ai_intelligence_tab'),
                    ('auto_detection_tab', 'auto_detection_tab'),
                    ('dyno_tab', 'dyno_tab'),
                    ('drag_racing_tab', 'drag_racing_tab'),
                    ('track_learning_tab', 'track_learning_tab'),
                    ('auto_tuning_tab', 'auto_tuning_tab'),
                    ('diesel_tuning_tab', 'diesel_tuning_tab'),
                    ('video_overlay_tab', 'video_overlay_tab'),
                    ('lap_detection_tab', 'lap_detection_tab'),
                    ('session_management_tab', 'session_management_tab'),
                    ('storage_management_tab', 'storage_management_tab'),
                    ('network_diagnostics_tab', 'network_diagnostics_tab'),
                ]
                
                # Update lap detection with GPS data if available
                try:
                    if hasattr(self, 'lap_detection_tab') and self.lap_detection_tab:
                        # Try to get GPS data from telemetry
                        gps_lat = data.get('gps_latitude') or data.get('gps_lat')
                        gps_lon = data.get('gps_longitude') or data.get('gps_lon')
                        gps_speed = data.get('gps_speed') or data.get('speed_mph', 0)
                        if gps_lat and gps_lon:
                            self.lap_detection_tab.update_gps(gps_lat, gps_lon, gps_speed)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug(f"Error updating lap detection GPS: {e}")
                
                for attr_name, tab_name in optional_tabs:
                    try:
                        if hasattr(self, attr_name):
                            tab_widget = getattr(self, attr_name, None)
                            if tab_widget and hasattr(tab_widget, 'update_telemetry'):
                                tab_widget.update_telemetry(data)
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"Error updating {tab_name}: {e}")
        finally:
            self._updating = False
    
    def showMaximized(self) -> None:
        """Override maximize to use available screen geometry instead of full."""
        # Use available geometry (accounts for taskbars) instead of full screen
        # DON'T call super() - we handle it ourselves to prevent Qt from using full screen
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        app = QApplication.instance()
        if app and app.primaryScreen():
            screen = app.primaryScreen()
            available_geometry = screen.availableGeometry()
            # Set geometry first
            self.setGeometry(available_geometry)
            # Then set the window state to maximized (this triggers changeEvent)
            self.setWindowState(Qt.WindowState.WindowMaximized)
            self._maximized = True
        else:
            # Fallback - but still don't use super() to avoid full screen
            self._maximized = True
    
    def showNormal(self) -> None:
        """Override showNormal to reset maximize state."""
        super().showNormal()
        self._maximized = False
    
    def changeEvent(self, event) -> None:
        """Handle window state changes - intercept maximize to enforce bounds."""
        from PySide6.QtCore import QEvent, Qt
        
        # Prevent recursion
        if getattr(self, '_handling_maximize', False):
            super().changeEvent(event)
            return
        
        # Check current state BEFORE calling super()
        was_maximized = bool(self.windowState() & Qt.WindowState.WindowMaximized)
        
        # Call parent to let Qt apply the state change
        super().changeEvent(event)
        
        # Check if NOW maximized (state just changed)
        is_now_maximized = bool(self.windowState() & Qt.WindowState.WindowMaximized)
        
        # If just became maximized, immediately enforce available geometry
        if event.type() == QEvent.Type.WindowStateChange and is_now_maximized and not was_maximized:
            self._handling_maximize = True
            try:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app and app.primaryScreen():
                    screen = app.primaryScreen()
                    available_geometry = screen.availableGeometry()
                    # Set geometry immediately (no timer delay) to prevent Qt from going past bounds
                    self.setGeometry(available_geometry)
                    self._maximized = True
                    # Force update
                    self.update()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error enforcing maximize bounds: {e}")
            finally:
                self._handling_maximize = False
        elif event.type() == QEvent.Type.WindowStateChange:
            # Window was restored
            self._maximized = False
    
    def resizeEvent(self, event) -> None:
        """Handle window resize - clamp to screen bounds with improved logic."""
        # Prevent recursion during resize handling
        if hasattr(self, '_resizing') and self._resizing:
            super().resizeEvent(event)
            return
        
        new_width = event.size().width()
        new_height = event.size().height()
        
        # Check if maximized - let Qt handle it naturally
        from PySide6.QtCore import Qt
        if self.windowState() & Qt.WindowState.WindowMaximized:
            # When maximized, Qt should handle size automatically
            # Just ensure we're not exceeding available geometry
            if hasattr(self, '_available_width') and hasattr(self, '_available_height'):
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app and app.primaryScreen():
                    screen = app.primaryScreen()
                    available_geometry = screen.availableGeometry()
                    # Only fix if significantly off (more than 10 pixels)
                    if (abs(new_width - available_geometry.width()) > 10 or 
                        abs(new_height - available_geometry.height()) > 10):
                        # Use QTimer to avoid recursion
                        self._resizing = True
                        QTimer.singleShot(0, lambda: self._fix_maximized_size())
                        super().resizeEvent(event)
                        return
        
        # For normal resize, clamp to available screen size
        if hasattr(self, '_available_width') and hasattr(self, '_available_height'):
            needs_clamp = False
            clamped_width = new_width
            clamped_height = new_height
            
            # Clamp width
            if new_width > self._available_width:
                clamped_width = self._available_width
                needs_clamp = True
            
            # Clamp height
            if new_height > self._available_height:
                clamped_height = self._available_height
                needs_clamp = True
            
            # Only clamp if necessary and not already handling resize
            if needs_clamp:
                self._resizing = True
                QTimer.singleShot(0, lambda: self._clamp_window_size(clamped_width, clamped_height))
                super().resizeEvent(event)
                return
        
        # Normal resize - no clamping needed
        super().resizeEvent(event)
    
    def _fix_maximized_size(self) -> None:
        """Fix maximized window size to match available geometry."""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app and app.primaryScreen():
                screen = app.primaryScreen()
                available_geometry = screen.availableGeometry()
                self.setGeometry(available_geometry)
        finally:
            self._resizing = False
    
    def _clamp_window_size(self, width: int, height: int) -> None:
        """Clamp window size to bounds - called via QTimer to avoid recursion."""
        try:
            current_pos = self.pos()
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            
            if app and app.primaryScreen():
                screen = app.primaryScreen()
                available_geometry = screen.availableGeometry()
                
                # Clamp size
                clamped_width = min(width, available_geometry.width())
                clamped_height = min(height, available_geometry.height())
                
                # Clamp position to keep window on screen
                x = max(available_geometry.x(), 
                       min(current_pos.x(), available_geometry.right() - clamped_width))
                y = max(available_geometry.y(), 
                       min(current_pos.y(), available_geometry.bottom() - clamped_height))
                
                # Set geometry
                self.setGeometry(x, y, clamped_width, clamped_height)
            else:
                # Fallback if screen info unavailable
                self.resize(width, height)
        finally:
            self._resizing = False
    
    def moveEvent(self, event) -> None:
        """Handle window move - let Qt handle it."""
        super().moveEvent(event)
    
    def _update_license_status(self) -> None:
        """Update license status display."""
        if not self.license_manager:
            return
        
        try:
            info = self.license_manager.get_license_info()
            if info['licensed']:
                license_type = info['type'].upper()
                self.license_status_label.setText(f"✓ {license_type}")
                self.license_status_label.setStyleSheet("color: #00ff00; font-size: 10px; font-weight: bold;")
                if hasattr(self, 'license_btn'):
                    self.license_btn.setText("Manage")
            else:
                self.license_status_label.setText("DEMO MODE")
                self.license_status_label.setStyleSheet("color: #ff8000; font-size: 10px; font-weight: bold;")
                if hasattr(self, 'license_btn'):
                    self.license_btn.setText("Activate")
        except Exception as e:
            LOGGER.debug(f"Error updating license status: {e}")
    
    def _show_license_dialog(self) -> None:
        """Show license entry dialog."""
        try:
            from ui.license_dialog import LicenseDialog
            dialog = LicenseDialog(self)
            dialog.exec()
            # Update status after dialog closes
            self._update_license_status()
        except Exception as e:
            LOGGER.error(f"Failed to show license dialog: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "License Dialog Error",
                f"Failed to open license dialog:\n{e}"
            )
    
    def _handle_voice_command(self, text: str) -> None:
        """
        Handle voice command.
        
        Args:
            text: Recognized voice command text (should be sanitized)
        """
        # Validate and sanitize input
        if not isinstance(text, str):
            LOGGER.warning("Invalid voice command type: %s", type(text))
            return
        
        text = text.strip()
        if not text:
            return
        
        # Limit length to prevent abuse
        if len(text) > 500:
            text = text[:500]
            LOGGER.warning("Voice command truncated to 500 characters")
        
        text_lower = text.lower()
        
        # Voice commands for AI advisor
        if "ai advisor" in text_lower or "q" in text_lower or "ask" in text_lower:
            if hasattr(self, 'ai_advisor_manager') and self.ai_advisor_manager:
                self.ai_advisor_manager._show_chat()
        
        # Voice commands for navigation
        elif "dashboard" in text_lower:
            self.tabs.setCurrentIndex(0)
        elif "telemetry" in text_lower:
            self.tabs.setCurrentIndex(1)
        elif "diagnostics" in text_lower:
            self.tabs.setCurrentIndex(2)
        
        # Voice commands for actions
        elif "panic" in text_lower or "safe map" in text_lower:
            if hasattr(self, 'dashboard_tab') and self.dashboard_tab:
                if hasattr(self.dashboard_tab, 'panic_btn'):
                    self.dashboard_tab.panic_btn.click()
        
        LOGGER.info("Voice command received: %s", text)
    
    def _open_theme_customizer(self) -> None:
        """Open advanced theme customization dialog."""
        try:
            customizer = AdvancedThemeCustomizer(self.theme_manager, self)
            customizer.theme_changed.connect(self._on_theme_changed)
            if customizer.exec() == QDialog.DialogCode.Accepted:
                # Apply theme to all widgets
                self._apply_theme_to_all()
        except Exception as e:
            LOGGER.error("Failed to open theme customizer: %s", e, exc_info=True)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to open theme customizer: {e}")
    
    def _on_theme_changed(self, theme) -> None:
        """Handle theme change signal."""
        self._apply_theme_to_all()
    
    def _apply_theme_to_all(self) -> None:
        """Apply current theme to all widgets."""
        try:
            # Apply to main window
            self.setStyleSheet(self.theme_manager.get_stylesheet())
            
            # Apply to all tabs
            for i in range(self.tabs.count()):
                tab = self.tabs.widget(i)
                if tab:
                    tab.setStyleSheet(self.theme_manager.get_stylesheet())
            
            # Update gauge customizations if dashboard exists
            # Note: Gauge customization is handled through theme manager
            # Individual gauges can be updated via their set_customization() method
        except Exception as e:
            LOGGER.error("Failed to apply theme: %s", e, exc_info=True)
    
    def closeEvent(self, event) -> None:
        """Clean up resources when window is closed."""
        # Stop update timer
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
            self.update_timer = None
        
        # Hide floating AI advisor
        if hasattr(self, 'ai_advisor_manager') and self.ai_advisor_manager:
            self.ai_advisor_manager.hide_all()
        
        # Stop voice handler
        if hasattr(self, 'voice_handler') and self.voice_handler:
            self.voice_handler.stop_listening()
        
        # Stop demo controller timer if it exists
        if hasattr(self, 'demo_controller') and self.demo_controller:
            if hasattr(self.demo_controller, 'stop'):
                self.demo_controller.stop()
        
        # Clean up mobile API client
        if hasattr(self, 'mobile_api_client') and self.mobile_api_client:
            try:
                # Mobile API client cleanup is async, but we'll try to stop it
                import asyncio
                if asyncio.iscoroutinefunction(self.mobile_api_client.stop):
                    # Schedule async cleanup
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(self.mobile_api_client.stop())
                    except Exception:
                        pass  # Ignore cleanup errors
            except Exception:
                pass  # Ignore cleanup errors
        
        # Clean up optimization manager
        if hasattr(self, 'opt_manager') and self.opt_manager:
            try:
                # Optimization manager should clean itself up
                pass
            except Exception:
                pass
        
        # Accept the close event
        event.accept()


__all__ = ["MainContainerWindow"]

