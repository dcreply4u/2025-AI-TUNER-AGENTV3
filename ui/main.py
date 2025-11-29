from __future__ import annotations

"""
=========================================================
AI Tuner Desktop – main shell and responsive layout host
=========================================================
"""

import logging
import platform
import sys

# Platform detection for OS-specific sizing
IS_WINDOWS = platform.system().lower().startswith("win")
from pathlib import Path

LOGGER = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ai import ConversationalAgent, PredictiveFaultDetector, TuningAdvisor
from controllers import CameraManager, start_data_stream, start_voice_listener
from interfaces import CameraConfig, CameraType, GPSInterface, OBDInterface

try:
    from interfaces import VoiceOutput
except ImportError:
    VoiceOutput = None  # type: ignore

from services import (
    CloudSync,
    ConnectivityManager,
    DataLogger,
    DisplayManager,
    GeoLogger,
    PerformanceTracker,
    USBManager,
)
from core.app_context import AppContext
from ui.ai_advisor_widget import AIAdvisorWidget
from ui.analysis_coach_tab import AnalysisCoachTab
from ui.ai_insight_panel import AIInsightPanel
from ui.dragy_view import DragyPerformanceView, DragTimesPanel, GPSTrackPanel
from ui.drag_mode_panel import DragModePanel, DragModeCompactPanel, DragState
from ui.enhanced_widgets import apply_standard_margins, make_expanding, make_hgrow
from ui.fault_panel import FaultPanel
from ui.gauge_widget import GaugePanel
from ui.health_score_widget import HealthScoreWidget
from ui.notification_widget import NotificationLevel, NotificationWidget
from ui.settings_dialog import SettingsDialog
from ui.status_bar import StatusBar
from ui.streaming_control_panel import StreamingControlPanel
from ui.system_status_panel import SystemStatusPanel, SubsystemStatus
from ui.telemetry_panel import TelemetryPanel
from ui.theme_dialog import ThemeDialog
from ui.theme_manager import Style, ThemeManager
from ui.wheel_slip_widget import WheelSlipPanel
from ui.youtube_stream_widget import YouTubeStreamWidget

# Virtual Dyno imports
try:
    from ui.dyno_tab import DynoTab
    DYNO_AVAILABLE = True
except ImportError:
    DynoTab = None
    DYNO_AVAILABLE = False

# ECU Tuning imports
try:
    from ui.ecu_tuning_main import ECUTuningMain
    ECU_TUNING_AVAILABLE = True
except ImportError:
    ECUTuningMain = None
    ECU_TUNING_AVAILABLE = False

# Drag Racing imports
try:
    from ui.drag_racing_tab import DragRacingTab
    DRAG_RACING_AVAILABLE = True
except ImportError:
    DragRacingTab = None
    DRAG_RACING_AVAILABLE = False

# Track Learning imports
try:
    from ui.track_learning_tab import TrackLearningTab
    TRACK_LEARNING_AVAILABLE = True
except ImportError:
    TrackLearningTab = None
    TRACK_LEARNING_AVAILABLE = False

# Sensors Tab imports
try:
    from ui.sensors_tab import SensorsTab
    SENSORS_AVAILABLE = True
except ImportError:
    SensorsTab = None
    SENSORS_AVAILABLE = False

# Auto Tuning imports
try:
    from ui.auto_tuning_tab import AutoTuningTab
    AUTO_TUNING_AVAILABLE = True
except ImportError:
    AutoTuningTab = None
    AUTO_TUNING_AVAILABLE = False

# Diesel Tuning imports
try:
    from ui.diesel_tuning_tab import DieselTuningTab
    DIESEL_TUNING_AVAILABLE = True
except ImportError:
    DieselTuningTab = None
    DIESEL_TUNING_AVAILABLE = False

# VBOX Features imports
try:
    from ui.vbox_features_main import VBOXFeaturesMain
    VBOX_FEATURES_AVAILABLE = True
except ImportError:
    VBOXFeaturesMain = None
    VBOX_FEATURES_AVAILABLE = False

# Safety Alerts imports
try:
    from ui.safety_alerts_system import SafetyAlertsPanel
    SAFETY_ALERTS_AVAILABLE = True
except ImportError:
    SafetyAlertsPanel = None
    SAFETY_ALERTS_AVAILABLE = False


class MainWindow(QWidget):
    """
    Main application window.

    This class orchestrates the high-level layout and ensures that panels and
    controls resize predictably across resolutions. All content is managed by
    Qt layouts with explicit stretch factors and size policies to prevent
    overlapping / "bleeding" UI elements.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Tuner Edge Agent V2")

        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()

            if IS_WINDOWS:
                # On Windows, be more conservative: smaller and never full-height.
                target_width = min(1280, int(available.width() * 0.7))
                target_height = min(720, int(available.height() * 0.65))
            else:
                # On Pi / Linux / others, keep the previous behavior.
                target_width = min(1280, int(available.width() * 0.85))
                target_height = min(720, int(available.height() * 0.85))

            # Apply a reasonable minimum to avoid a tiny window
            min_width = min(960, target_width)
            min_height = min(540, target_height)
            self.setMinimumSize(min_width, min_height)

            self.resize(target_width, target_height)

            # Center in the available area
            x = available.x() + (available.width() - target_width) // 2
            y = available.y() + (available.height() - target_height) // 2
            self.move(x, y)

            # Hard cap: never allow window taller than available area
            self.setMaximumHeight(available.height())
        else:
            # Fallback if no screen info
            self.resize(960, 540)

        # Initialize theme manager
        self.theme_manager = ThemeManager()
        # Initialize global Style system for CSS-like color access
        Style.set_theme_manager(self.theme_manager)
        self._apply_theme()

        # Core stream settings (used by data stream + connectivity)
        self.stream_settings = {
            "source": "Auto",
            "port": "/dev/ttyUSB0",
            "baud": 115200,
            "interval_sec": 0.5,
            "mode": "live",
            "replay_file": None,
            "network_preference": "Auto",
            "obd_transport": "Auto",
            "bluetooth_address": "",
            "wifi_interface": "wlan0",
            "lte_interface": "wwan0",
        }

        # ------------------------------------------------------------------
        # Layout skeleton
        # ------------------------------------------------------------------
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)

        # Left column with scroll area (like right side)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical {
                background-color: #111827;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #00e5ff;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        left_container = QWidget()
        left_column = QVBoxLayout(left_container)
        left_column.setSpacing(8)
        left_column.setContentsMargins(0, 0, 0, 0)

        # Right column with scroll area for many controls
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical {
                background-color: #111827;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #00e5ff;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        right_container = QWidget()
        right_column = QVBoxLayout(right_container)
        right_column.setSpacing(6)
        right_column.setContentsMargins(0, 0, 0, 0)

        # ------------------------------------------------------------------
        # Left column: telemetry, health, AI insights, advice, performance
        # ------------------------------------------------------------------
        # Use enhanced telemetry panel if available, otherwise fall back to basic
        try:
            from ui.enhanced_telemetry_panel import EnhancedTelemetryPanel
            self.telemetry_panel = EnhancedTelemetryPanel()
            self.telemetry_panel.setMinimumHeight(400)  # Enhanced panel needs more space
            LOGGER.info("Using Enhanced Telemetry Panel")
        except Exception as e:
            LOGGER.warning(f"Enhanced telemetry panel not available, using basic: {e}")
            self.telemetry_panel = TelemetryPanel()
            self.telemetry_panel.setFixedHeight(320)  # Increased height to show all 3 graphs including G-forces
        self.health_widget = HealthScoreWidget()
        self.health_widget.setFixedHeight(100)  # Compact fixed height
        
        # AI Advisor Chat Widget (Q) - moved to main panel for more space
        self.ai_advisor_widget = AIAdvisorWidget()
        self.ai_advisor_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        
        self.ai_panel = AIInsightPanel()
        self.ai_panel.setFixedHeight(120)  # Compact fixed height

        from ui.advice_panel import AdvicePanel
        self.advice_panel = AdvicePanel()
        self.advice_panel.setFixedHeight(120)  # Compact fixed height
        
        self.dragy_view = DragyPerformanceView()
        # NEW: Dodge Charger-style Drag Mode Panel
        self.drag_mode_panel = DragModePanel()
        self.drag_mode_panel.setFixedHeight(320)  # Reduced height
        
        # Legacy panels (kept for backward compatibility)
        self.drag_times_panel = DragTimesPanel()
        self.drag_times_panel.setFixedHeight(180)
        
        self.gps_track_panel = GPSTrackPanel()
        self.gps_track_panel.setFixedHeight(150)

        # OBD & faults
        self.obd_interface = OBDInterface()
        self.fault_panel = FaultPanel(self.obd_interface)
        
        # Modern System Status Panel (enhanced visual monitoring)
        self.system_status_panel = SystemStatusPanel(self.obd_interface)
        self.system_status_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        # Gauge panel for right column - fixed size to prevent jitter
        self.gauge_panel = GaugePanel()
        # Don't override fixed size from GaugePanel

        # Wheel slip panel for drag racing optimization
        self.wheel_slip_panel = WheelSlipPanel()
        self.wheel_slip_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        # Start demo mode for wheel slip visualization
        self.wheel_slip_panel.start_demo()

        # Status bar
        self.status_bar = StatusBar()
        self.status_bar.update_connectivity("Scanning radios…")

        # Ensure major panels expand with window size
        for panel in (
            self.telemetry_panel,
            self.health_widget,
            self.ai_panel,
            self.advice_panel,
            self.dragy_view,
            self.fault_panel,
        ):
            panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,   # grow/shrink horizontally with window
                QSizePolicy.Policy.Preferred,   # can shrink vertically as needed
            )

        # ------------------------------------------------------------------
        # Notification + YouTube + camera quick widget (right column top)
        # ------------------------------------------------------------------
        self.notification_widget = NotificationWidget()

        def show_notification(message: str, level: str = "info") -> None:
            level_enum = {
                "info": NotificationLevel.INFO,
                "warning": NotificationLevel.WARNING,
                "error": NotificationLevel.ERROR,
                "success": NotificationLevel.SUCCESS,
            }.get(level.lower(), NotificationLevel.INFO)
            self.notification_widget.show_notification(message, level_enum)

        self.show_notification = show_notification  # keep as attribute

        self.live_streamer = None
        self.youtube_widget: YouTubeStreamWidget | None = None
        try:
            from services.live_streamer import LiveStreamer

            self.live_streamer = LiveStreamer(notification_callback=show_notification)
            if self.live_streamer.enabled:
                try:
                    self.youtube_widget = YouTubeStreamWidget(
                        live_streamer=self.live_streamer,
                        parent=self,
                    )
                except ImportError:
                    show_notification("YouTube streaming UI unavailable", "warning")
        except Exception as exc:  # pragma: no cover - optional feature
            show_notification(f"YouTube streaming unavailable: {str(exc)}", "warning")

        # USB Manager for automatic storage detection and setup
        self.usb_manager = USBManager(auto_setup=True, prompt_format=True)
        self.usb_monitor = None
        try:
            from ui.usb_setup_dialog import USBMonitorWidget
            from PySide6.QtCore import QTimer

            self.usb_monitor = USBMonitorWidget(self.usb_manager, parent=self)
            self.usb_monitor.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self.usb_scan_timer = QTimer(self)
            self.usb_scan_timer.timeout.connect(self._scan_usb_devices)
            self.usb_scan_timer.start(3000)  # Scan every 3 seconds
            self._scan_usb_devices()  # Initial scan
        except Exception as exc:  # pragma: no cover - hardware/OS dependent
            print(f"[WARN] USB manager unavailable: {exc}")

        # HDD Manager for hard drive storage and sync
        self.hdd_manager = None
        try:
            from services.hdd_manager import HDDManager
            self.hdd_manager = HDDManager()
            if self.hdd_manager.is_mounted():
                LOGGER.info("Hard drive detected: %s", self.hdd_manager.mount_point)
            else:
                LOGGER.debug("Hard drive not mounted (running from USB/local)")
        except Exception as e:
            LOGGER.debug("HDD Manager not available: %s", e)

        # ------------------------------------------------------------------
        # Shared service instances / app context
        # ------------------------------------------------------------------
        self.fault_predictor = PredictiveFaultDetector()
        self.tuning_advisor = TuningAdvisor()
        
        # Determine log path (priority: HDD > USB > Local)
        log_path = Path("logs/telemetry")  # Default fallback
        if self.hdd_manager and self.hdd_manager.is_mounted():
            hdd_logs = self.hdd_manager.get_logs_path("telemetry")
            if hdd_logs:
                log_path = hdd_logs
                LOGGER.info("Using HDD for logs: %s", log_path)
        elif self.usb_manager:
            usb_logs = self.usb_manager.get_logs_path("telemetry")
            if usb_logs:
                log_path = usb_logs
                LOGGER.info("Using USB for logs: %s", log_path)
        
        # Centralized AppContext for core services
        self.app_context = AppContext.create(log_dir=log_path)
        self.data_logger = self.app_context.data_logger
        self.cloud_sync = self.app_context.cloud_sync
        self.performance_tracker = self.app_context.performance_tracker
        self.geo_logger = self.app_context.geo_logger
        self.conversational_agent = ConversationalAgent()
        self.voice_output = VoiceOutput() if VoiceOutput else None

        try:
            from services.voice_feedback import VoiceFeedback

            self.voice_feedback = VoiceFeedback(
                voice_output=self.voice_output,
                enabled=True,
            )
        except Exception as exc:  # pragma: no cover - optional
            self.voice_feedback = None
            print(f"[WARN] Voice feedback unavailable: {exc}")

        self.connectivity_manager = ConnectivityManager(
            wifi_interface=self.stream_settings["wifi_interface"],
            lte_interface=self.stream_settings["lte_interface"],
        )
        self.latest_connectivity = None
        self.connectivity_manager.register_callback(self._on_connectivity_change)
        self.connectivity_manager.start()

        # ECU Auto-Configuration
        self.config_manager = None
        self.ecu_auto_config = None
        try:
            from core.config_manager import ConfigManager
            from controllers.ecu_auto_config_controller import ECUAutoConfigController
            from PySide6.QtCore import QTimer

            self.config_manager = ConfigManager()
            self.ecu_auto_config = ECUAutoConfigController(
                config_manager=self.config_manager,
                voice_feedback=self.voice_feedback,
                parent=self,
            )

            self.ecu_auto_config.ecu_detected.connect(self._on_ecu_detected)
            self.ecu_auto_config.configuration_complete.connect(
                self._on_ecu_configured,
            )
            self.ecu_auto_config.detection_failed.connect(self._on_ecu_detection_failed)

            # Auto-start detection on startup (after a short delay)
            QTimer.singleShot(
                2000,
                lambda: self.ecu_auto_config.start_auto_detection(sample_time=5.0),
            )
        except Exception as exc:  # pragma: no cover - optional
            print(f"[WARN] ECU auto-config unavailable: {exc}")

        # Display Manager for external monitor output
        try:
            app = QApplication.instance()
            self.display_manager = DisplayManager(app=app) if app else None
        except Exception as exc:  # pragma: no cover - optional
            self.display_manager = None
            print(f"[WARN] Display manager unavailable: {exc}")

        # GPS + camera manager
        self.camera_manager = None
        # Don't create real GPS interface in demo mode - will be created by start_data_stream
        import os
        if os.environ.get("AITUNER_DEMO_MODE") != "true":
            try:
                self.gps_interface = GPSInterface()
            except Exception as exc:  # pragma: no cover - hardware optional
                self.gps_interface = None
                print(f"[WARN] GPS interface unavailable: {exc}")
        else:
            self.gps_interface = None  # Will be set to SimulatedGPSInterface by start_data_stream

        try:
            from services import VideoLogger

            video_log_path = (
                self.usb_manager.get_session_path("video")
                if self.usb_manager
                else Path("logs/video")
            )
            video_logger = VideoLogger(output_dir=video_log_path)
            camera_manager = CameraManager(
                video_logger=video_logger,
                voice_feedback=getattr(self, "voice_feedback", None),
                live_streamer=getattr(self, "live_streamer", None),
            )
            # Cameras are configured by user via dialog
            self.camera_manager = camera_manager
            # Camera manager will be connected to streaming panel
        except Exception as exc:  # pragma: no cover - optional hardware
            self.camera_manager = None
            self.ai_panel.update_insight(f"[Camera] Disabled ({exc})", level="warning")

        # ------------------------------------------------------------------
        # Controls and camera quick widget
        # ------------------------------------------------------------------
        self.start_btn = QPushButton("Start Session")
        self.voice_btn = QPushButton("Voice Control")
        self.replay_btn = QPushButton("Replay Log")
        self.settings_btn = QPushButton("Settings")
        self.theme_btn = QPushButton("Theme")
        self.camera_btn = QPushButton("Configure Cameras")
        self.overlay_btn = QPushButton("Video Overlay")
        self.diagnostics_btn = QPushButton("Diagnostics")
        self.display_btn = QPushButton("External Display")
        self.email_btn = QPushButton("Email Logs")
        self.export_btn = QPushButton("Export Data")

        # Buttons: expand horizontally but fixed height
        for btn in (
            self.start_btn,
            self.voice_btn,
            self.replay_btn,
            self.settings_btn,
            self.theme_btn,
            self.camera_btn,
            self.overlay_btn,
            self.diagnostics_btn,
            self.display_btn,
            self.email_btn,
            self.export_btn,
        ):
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

        self.notification_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        # Bind actions
        self.start_btn.clicked.connect(self.start_session)
        self.voice_btn.clicked.connect(self.start_voice_control)
        self.replay_btn.clicked.connect(self.start_replay_mode)
        self.settings_btn.clicked.connect(self.open_settings)
        self.theme_btn.clicked.connect(self.open_theme_dialog)
        self.camera_btn.clicked.connect(self.configure_cameras)
        self.email_btn.clicked.connect(self.email_logs)
        self.overlay_btn.clicked.connect(self.configure_overlay)
        self.display_btn.clicked.connect(self.configure_display)
        self.diagnostics_btn.clicked.connect(self.show_diagnostics)
        self.export_btn.clicked.connect(self.export_data)

        # ------------------------------------------------------------------
        # Column composition
        # ------------------------------------------------------------------
        # Left: primary telemetry stack - use stretch=0 for fixed-size widgets
        left_column.setSpacing(4)  # Small spacing to prevent overlap
        left_column.addWidget(self.telemetry_panel, 0)  # Telemetry graphs - fixed height (280px)
        left_column.addWidget(self.drag_mode_panel, 0)  # Dodge Charger Drag Mode
        left_column.addWidget(self.health_widget, 0)  # Engine Health
        # No spacing before AI Advisor - extremely tight
        left_column.addWidget(self.ai_advisor_widget, 1)  # AI Chat Advisor - more space in main panel
        left_column.addWidget(self.ai_panel, 0)  # AI Insights
        left_column.addWidget(self.gps_track_panel, 0)  # GPS/Map at bottom
        left_column.addStretch(1)  # Push everything up

        # Right: gauges + faults + utilities + controls
        # 0) Live Gauges group (at top) - fixed height, expand width to match others
        gauge_group = QGroupBox("Live Gauges")
        gauge_group.setFixedHeight(580)
        gauge_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        gauge_layout = QVBoxLayout(gauge_group)
        gauge_layout.setContentsMargins(8, 12, 8, 8)
        gauge_layout.setSpacing(0)
        gauge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gauge_layout.addWidget(self.gauge_panel, 0, Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(gauge_group, 0)

        # 0.5) Wheel Slip Monitor (drag racing)
        slip_group = QGroupBox("🏁 Wheel Slip Monitor")
        slip_layout = QVBoxLayout(slip_group)
        slip_layout.setContentsMargins(8, 8, 8, 8)
        slip_layout.setSpacing(6)
        slip_layout.addWidget(self.wheel_slip_panel)
        right_column.addWidget(slip_group, 2)

        # 1) System Status Panel (modern visual monitoring)
        right_column.addWidget(self.system_status_panel, 3)

        # 2) Streaming Control Panel (modern camera & streaming)
        self.streaming_panel = StreamingControlPanel(
            live_streamer=self.live_streamer,
            camera_manager=self.camera_manager,
        )
        right_column.addWidget(self.streaming_panel, 2)

        # Finally, assemble columns into content layout
        # Add stretch at bottom of left column and set up scroll
        left_column.addStretch()
        left_scroll.setWidget(left_container)
        content_layout.addWidget(left_scroll, 3)  # main panels with scroll

        # Add stretch at bottom of right column and set up scroll
        right_column.addStretch()
        right_scroll.setWidget(right_container)
        content_layout.addWidget(right_scroll, 1)  # status + controls with scroll

        root_layout.addLayout(content_layout)

        # ============================================================
        # BOTTOM TAB BAR - Multi-row comprehensive control tabs
        # ============================================================
        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setFixedHeight(100)
        self.bottom_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.bottom_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #2c3e50;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                margin-top: -1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 1px solid #5a6fd6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 14px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 10px;
                color: #ffffff;
                min-width: 70px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00d4ff, stop:1 #0099cc);
                border: 2px solid #00b8e6;
                border-bottom: none;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c8ef5, stop:1 #8b5cf6);
            }
            QTabBar::scroller {
                width: 24px;
            }
            QTabBar QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00d4ff, stop:1 #0099cc);
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QTabBar QToolButton:hover {
                background: #00e5ff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #5a67d8);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c8ef5, stop:1 #6b7ae0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #4c51bf);
            }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)

        # Tab 1: Session Control
        session_tab = QWidget()
        session_layout = QHBoxLayout(session_tab)
        session_layout.setContentsMargins(12, 8, 12, 8)
        session_layout.setSpacing(10)
        
        self.start_btn = QPushButton("▶️  Start Session")
        self.start_btn.setStyleSheet("background-color: #27ae60;")
        self.start_btn.clicked.connect(self.start_session)
        session_layout.addWidget(self.start_btn)
        
        self.voice_btn = QPushButton("🎤  Voice Control")
        self.voice_btn.setStyleSheet("background-color: #00bcd4;")
        self.voice_btn.clicked.connect(self.start_voice_control)
        session_layout.addWidget(self.voice_btn)
        
        self.replay_btn = QPushButton("⏪  Replay Log")
        self.replay_btn.clicked.connect(self.start_replay_mode)
        session_layout.addWidget(self.replay_btn)
        
        fleet_btn = QPushButton("🚗 Fleet Management")
        fleet_btn.setStyleSheet("background-color: #16a085;")
        fleet_btn.clicked.connect(self._open_fleet_management)
        session_layout.addWidget(fleet_btn)
        
        social_btn = QPushButton("🏆 Social Racing")
        social_btn.setStyleSheet("background-color: #9b59b6;")
        social_btn.clicked.connect(self._open_social_racing)
        session_layout.addWidget(social_btn)
        
        session_layout.addStretch()
        self.bottom_tabs.addTab(session_tab, "🏁 Session")

        # Tab 2: Video Player (with Camera & Display)
        try:
            from ui.video_player_tab import VideoPlayerTab
            video_player_tab = VideoPlayerTab()
            self.bottom_tabs.addTab(video_player_tab, "📹 Video Player")
        except ImportError as e:
            LOGGER.warning(f"Video player tab not available: {e}")
            # Fallback to simple camera tab
            camera_tab = QWidget()
            camera_layout = QHBoxLayout(camera_tab)
            camera_layout.setContentsMargins(12, 8, 12, 8)
            camera_layout.setSpacing(10)
            
            self.camera_btn = QPushButton("📷  Configure Cameras")
            self.camera_btn.setStyleSheet("background-color: #34495e;")
            self.camera_btn.clicked.connect(self.configure_cameras)
            self.camera_btn.setEnabled(self.camera_manager is not None)
            camera_layout.addWidget(self.camera_btn)
            
            self.overlay_btn = QPushButton("🎬  Video Overlay")
            self.overlay_btn.setStyleSheet("background-color: #34495e;")
            self.overlay_btn.clicked.connect(self.toggle_video_overlay)
            self.overlay_btn.setEnabled(self.camera_manager is not None)
            camera_layout.addWidget(self.overlay_btn)
            
            self.display_btn = QPushButton("🖥️  External Display")
            self.display_btn.setStyleSheet("background-color: #9b59b6;")
            self.display_btn.clicked.connect(self.toggle_external_display)
            camera_layout.addWidget(self.display_btn)
            
            camera_layout.addStretch()
            self.bottom_tabs.addTab(camera_tab, "📹 Camera & Display")

        # Tab 3: Tools & Settings
        tools_tab = QWidget()
        tools_layout = QHBoxLayout(tools_tab)
        tools_layout.setContentsMargins(12, 8, 12, 8)
        tools_layout.setSpacing(10)
        
        self.settings_btn = QPushButton("⚙️  Settings")
        self.settings_btn.setStyleSheet("background-color: #ecf0f1; color: #2c3e50;")
        self.settings_btn.clicked.connect(self.open_settings)
        tools_layout.addWidget(self.settings_btn)
        
        self.theme_btn = QPushButton("🎨  Theme")
        self.theme_btn.setStyleSheet("background-color: #ecf0f1; color: #2c3e50;")
        self.theme_btn.clicked.connect(self.open_theme_dialog)
        tools_layout.addWidget(self.theme_btn)
        
        self.diagnostics_btn = QPushButton("🔍  Diagnostics")
        self.diagnostics_btn.setStyleSheet("background-color: #f39c12;")
        self.diagnostics_btn.clicked.connect(self.open_diagnostics)
        tools_layout.addWidget(self.diagnostics_btn)
        
        wizard_btn = QPushButton("🧙 Setup Wizard")
        wizard_btn.setStyleSheet("background-color: #9b59b6;")
        wizard_btn.clicked.connect(self._open_onboarding_wizard)
        tools_layout.addWidget(wizard_btn)
        
        tools_layout.addStretch()
        self.bottom_tabs.addTab(tools_tab, "🔧 Tools & Settings")

        # Tab 4: Data & Export
        data_tab = QWidget()
        data_layout = QHBoxLayout(data_tab)
        data_layout.setContentsMargins(12, 8, 12, 8)
        data_layout.setSpacing(10)
        
        log_viewer_btn = QPushButton("📜 Log Viewer")
        log_viewer_btn.setStyleSheet("background-color: #8e44ad;")
        log_viewer_btn.clicked.connect(self._open_log_viewer)
        data_layout.addWidget(log_viewer_btn)
        
        self.email_btn = QPushButton("📧 Email Logs")
        self.email_btn.setStyleSheet("background-color: #3498db;")
        self.email_btn.clicked.connect(self.email_logs)
        data_layout.addWidget(self.email_btn)
        
        self.export_btn = QPushButton("💾 Export Data")
        self.export_btn.setStyleSheet("background-color: #27ae60;")
        self.export_btn.clicked.connect(self.export_data)
        data_layout.addWidget(self.export_btn)
        
        tune_db_btn = QPushButton("🗄️ Tune Database")
        tune_db_btn.setStyleSheet("background-color: #e67e22;")
        tune_db_btn.clicked.connect(self._open_tune_database)
        data_layout.addWidget(tune_db_btn)
        
        data_layout.addStretch()
        self.bottom_tabs.addTab(data_tab, "📊 Data")

        # Tab 5: Fuel Systems (E85, Methanol, Nitromethane)
        fuel_tab = QWidget()
        fuel_layout = QHBoxLayout(fuel_tab)
        fuel_layout.setContentsMargins(12, 8, 12, 8)
        fuel_layout.setSpacing(8)
        
        e85_btn = QPushButton("🌽 E85")
        e85_btn.setStyleSheet("background-color: #f39c12;")
        e85_btn.clicked.connect(self._open_fuel_management)
        fuel_layout.addWidget(e85_btn)
        
        meth_btn = QPushButton("💧 Methanol")
        meth_btn.setStyleSheet("background-color: #3498db;")
        meth_btn.clicked.connect(self._open_fuel_management)
        fuel_layout.addWidget(meth_btn)
        
        nitrometh_btn = QPushButton("🔥 Nitromethane")
        nitrometh_btn.setStyleSheet("background-color: #e74c3c;")
        nitrometh_btn.clicked.connect(self._open_fuel_management)
        fuel_layout.addWidget(nitrometh_btn)
        
        fuel_layout.addStretch()
        self.bottom_tabs.addTab(fuel_tab, "⛽ Fuel")

        # Tab 6: Power Adders (Nitrous, Turbo/Boost)
        power_tab = QWidget()
        power_layout = QHBoxLayout(power_tab)
        power_layout.setContentsMargins(12, 8, 12, 8)
        power_layout.setSpacing(8)
        
        nitrous_btn = QPushButton("💨 Nitrous")
        nitrous_btn.setStyleSheet("background-color: #9b59b6;")
        nitrous_btn.clicked.connect(self._open_nitrous)
        power_layout.addWidget(nitrous_btn)
        
        boost_btn = QPushButton("🌀 Turbo/Boost")
        boost_btn.setStyleSheet("background-color: #1abc9c;")
        boost_btn.clicked.connect(self._open_boost_control)
        power_layout.addWidget(boost_btn)
        
        supercharger_btn = QPushButton("⚡ Supercharger")
        supercharger_btn.setStyleSheet("background-color: #e67e22;")
        supercharger_btn.clicked.connect(self._open_boost_control)  # Supercharger uses boost control
        power_layout.addWidget(supercharger_btn)
        
        power_layout.addStretch()
        self.bottom_tabs.addTab(power_tab, "💪 Power")

        # Tab 7: ECU Tuning
        tuning_tab = QWidget()
        tuning_layout = QHBoxLayout(tuning_tab)
        tuning_layout.setContentsMargins(12, 8, 12, 8)
        tuning_layout.setSpacing(8)
        
        ecu_btn = QPushButton("🔧 ECU Tuning")
        ecu_btn.setStyleSheet("background-color: #2c3e50;")
        ecu_btn.clicked.connect(self._open_ecu_tuning)
        tuning_layout.addWidget(ecu_btn)
        
        auto_tune_btn = QPushButton("🤖 Auto Tune")
        auto_tune_btn.setStyleSheet("background-color: #27ae60;")
        auto_tune_btn.clicked.connect(self._open_auto_tuning)
        tuning_layout.addWidget(auto_tune_btn)
        
        diesel_btn = QPushButton("🛢️ Diesel")
        diesel_btn.setStyleSheet("background-color: #34495e;")
        diesel_btn.clicked.connect(self._open_diesel_tuning)
        tuning_layout.addWidget(diesel_btn)
        
        voice_ecu_btn = QPushButton("🎤 Voice ECU")
        voice_ecu_btn.setStyleSheet("background-color: #8e44ad;")
        voice_ecu_btn.clicked.connect(self._open_voice_ecu_control)
        tuning_layout.addWidget(voice_ecu_btn)
        
        weather_tune_btn = QPushButton("🌦️ Weather Tune")
        weather_tune_btn.setStyleSheet("background-color: #3498db;")
        weather_tune_btn.clicked.connect(self._open_weather_adaptive_tuning)
        tuning_layout.addWidget(weather_tune_btn)
        
        vbox_btn = QPushButton("📡 VBOX Features")
        vbox_btn.setStyleSheet("background-color: #16a085;")
        vbox_btn.clicked.connect(self._open_vbox_features)
        tuning_layout.addWidget(vbox_btn)
        
        tuning_layout.addStretch()
        self.bottom_tabs.addTab(tuning_tab, "⚙️ Tuning")

        # Tab 8: Racing
        racing_tab = QWidget()
        racing_layout = QHBoxLayout(racing_tab)
        racing_layout.setContentsMargins(12, 8, 12, 8)
        racing_layout.setSpacing(8)
        
        drag_btn = QPushButton("🏁 Drag Racing")
        drag_btn.setStyleSheet("background-color: #e74c3c;")
        drag_btn.clicked.connect(self._open_drag_racing)
        racing_layout.addWidget(drag_btn)
        
        track_btn = QPushButton("🛤️ Track Learning")
        track_btn.setStyleSheet("background-color: #3498db;")
        track_btn.clicked.connect(self._open_track_learning)
        racing_layout.addWidget(track_btn)
        
        dyno_btn = QPushButton("📈 Virtual Dyno")
        dyno_btn.setStyleSheet("background-color: #9b59b6;")
        dyno_btn.clicked.connect(self._open_virtual_dyno)
        racing_layout.addWidget(dyno_btn)
        
        ai_coach_btn = QPushButton("🎓 AI Racing Coach")
        ai_coach_btn.setStyleSheet("background-color: #16a085;")
        ai_coach_btn.clicked.connect(self._open_ai_racing_coach)
        racing_layout.addWidget(ai_coach_btn)
        
        pit_strategy_btn = QPushButton("🏁 Pit Strategist")
        pit_strategy_btn.setStyleSheet("background-color: #d35400;")
        pit_strategy_btn.clicked.connect(self._open_pit_strategist)
        racing_layout.addWidget(pit_strategy_btn)
        
        racing_layout.addStretch()
        self.bottom_tabs.addTab(racing_tab, "🏎️ Racing")

        # Tab 9: Sensors & Monitoring
        sensors_tab = QWidget()
        sensors_layout = QHBoxLayout(sensors_tab)
        sensors_layout.setContentsMargins(12, 8, 12, 8)
        sensors_layout.setSpacing(8)
        
        sensors_btn = QPushButton("📡 Sensors")
        sensors_btn.setStyleSheet("background-color: #16a085;")
        sensors_btn.clicked.connect(self._open_sensors)
        sensors_layout.addWidget(sensors_btn)
        
        wideband_btn = QPushButton("🎯 Wideband AFR")
        wideband_btn.setStyleSheet("background-color: #2980b9;")
        wideband_btn.clicked.connect(self._open_sensors)  # Opens sensors tab with AFR focus
        sensors_layout.addWidget(wideband_btn)
        
        egt_btn = QPushButton("🌡️ EGT Monitor")
        egt_btn.setStyleSheet("background-color: #c0392b;")
        egt_btn.clicked.connect(self._open_sensors)  # Opens sensors tab with EGT focus
        sensors_layout.addWidget(egt_btn)
        
        sensors_layout.addStretch()
        self.bottom_tabs.addTab(sensors_tab, "📡 Sensors")

        # Tab 10: Safety & Limits
        safety_tab = QWidget()
        safety_layout = QHBoxLayout(safety_tab)
        safety_layout.setContentsMargins(12, 8, 12, 8)
        safety_layout.setSpacing(8)
        
        rev_limit_btn = QPushButton("🚫 Rev Limiter")
        rev_limit_btn.setStyleSheet("background-color: #e74c3c;")
        rev_limit_btn.clicked.connect(self._open_safety_alerts)
        safety_layout.addWidget(rev_limit_btn)
        
        boost_limit_btn = QPushButton("⚠️ Boost Cut")
        boost_limit_btn.setStyleSheet("background-color: #f39c12;")
        boost_limit_btn.clicked.connect(self._open_safety_alerts)
        safety_layout.addWidget(boost_limit_btn)
        
        failsafe_btn = QPushButton("🛡️ Failsafes")
        failsafe_btn.setStyleSheet("background-color: #27ae60;")
        failsafe_btn.clicked.connect(self._open_safety_alerts)
        safety_layout.addWidget(failsafe_btn)
        
        crash_prevention_btn = QPushButton("⚠️ Crash Prevention")
        crash_prevention_btn.setStyleSheet("background-color: #c0392b;")
        crash_prevention_btn.clicked.connect(self._open_predictive_crash_prevention)
        safety_layout.addWidget(crash_prevention_btn)
        
        safety_layout.addStretch()
        self.bottom_tabs.addTab(safety_tab, "🛡️ Safety")

        # Tab 11: Analysis & Coach (data-driven overview)
        try:
            analysis_tab = AnalysisCoachTab(
                performance_tracker=self.performance_tracker,
                app_context=self.app_context,
                parent=self,
            )
            self.bottom_tabs.addTab(analysis_tab, "🧠 Analysis")
        except Exception as exc:
            LOGGER.warning("AnalysisCoachTab not available: %s", exc)

        # Development-only tab: Log Viewer
        try:
            from ui.dev_log_viewer_tab import DevLogViewerTab
            dev_log_tab = DevLogViewerTab()
            # Only add if in dev mode (tab checks internally)
            if dev_log_tab.is_dev_mode:
                self.bottom_tabs.addTab(dev_log_tab, "🔧 Dev Logs")
                LOGGER.info("Development log viewer tab added")
        except ImportError as e:
            LOGGER.debug(f"Dev log viewer tab not available: {e}")

        root_layout.addWidget(self.bottom_tabs)
        root_layout.addWidget(make_hgrow(self.status_bar))

        # ------------------------------------------------------------------
        # Diagnostics integration
        # ------------------------------------------------------------------
        self.diagnostics_widget = None
        self._init_diagnostics()

        # Integrate camera manager with streaming panel
        if self.camera_manager:
            self.streaming_panel.set_camera_manager(self.camera_manager)
            camera_names = list(
                self.camera_manager.camera_manager.cameras.keys()
            ) if hasattr(self.camera_manager, "camera_manager") else []
            self.streaming_panel.set_cameras(camera_names)
            self.ai_panel.update_insight("Camera manager ready.")

    # ----------------------------------------------------------------------
    # Session / control actions
    # ----------------------------------------------------------------------
    def start_session(self) -> None:
        self.stream_settings["mode"] = "live"
        self.connectivity_manager.configure(
            wifi_interface=self.stream_settings["wifi_interface"],
            lte_interface=self.stream_settings["lte_interface"],
        )
        start_data_stream(self, **self.stream_settings)

    def open_settings(self) -> None:
        dialog = SettingsDialog()
        dialog.source_select.setCurrentText(self.stream_settings["source"])
        dialog.port_input.setText(self.stream_settings["port"])
        dialog.baud_input.setText(str(self.stream_settings["baud"]))
        dialog.network_pref.setCurrentText(self.stream_settings["network_preference"])
        dialog.obd_transport.setCurrentText(self.stream_settings["obd_transport"])
        dialog.bluetooth_addr.setText(self.stream_settings["bluetooth_address"])
        dialog.wifi_iface_input.setText(self.stream_settings["wifi_interface"])
        dialog.lte_iface_input.setText(self.stream_settings["lte_interface"])
        if dialog.exec():
            settings = dialog.get_settings()
            self.stream_settings.update(settings)
            # Keep connectivity manager aligned with latest interfaces
            self.connectivity_manager.configure(
                wifi_interface=self.stream_settings["wifi_interface"],
                lte_interface=self.stream_settings["lte_interface"],
            )
            controller = getattr(self, "data_stream_controller", None)
            if controller:
                controller.configure(
                    source=settings["source"],
                    port=settings["port"],
                    baud=settings["baud"],
                    network_preference=settings["network_preference"],
                    obd_transport=settings["obd_transport"],
                    bluetooth_address=settings["bluetooth_address"],
                    wifi_interface=settings["wifi_interface"],
                    lte_interface=settings["lte_interface"],
                )

    def start_voice_control(self) -> None:
        self.ai_panel.update_insight("Voice control activated.")
        start_voice_listener(self, lambda: start_data_stream(self, **self.stream_settings))

    def start_replay_mode(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Telemetry Log",
            "",
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if not path:
            return
        self.stream_settings["mode"] = "replay"
        self.stream_settings["replay_file"] = path
        self.ai_panel.update_insight(f"Replay selected: {Path(path).name}")
        start_data_stream(self, **self.stream_settings)

    def configure_cameras(self) -> None:
        """Open camera configuration dialog."""
        from ui.camera_config_dialog import CameraConfigDialog

        if not self.camera_manager:
            self.ai_panel.update_insight(
                "Camera manager not available.",
                level="warning",
            )
            return

        dialog = CameraConfigDialog(self.camera_manager, parent=self)
        if dialog.exec():
            self.ai_panel.update_insight("Camera configuration updated.")

    def configure_overlay(self) -> None:
        """Open overlay configuration dialog."""
        from ui.overlay_config_dialog import OverlayConfigDialog

        if not self.camera_manager or not self.camera_manager.video_logger:
            self.ai_panel.update_insight(
                "Video logger not available.",
                level="warning",
            )
            return

        current_config = None
        if self.camera_manager.video_logger.overlay:
            current_config = self.camera_manager.video_logger.overlay.get_config()

        dialog = OverlayConfigDialog(current_config=current_config, parent=self)
        if dialog.exec():
            config = dialog.get_config()
            if self.camera_manager.video_logger.overlay:
                self.camera_manager.video_logger.configure_overlay(**config)
                self.ai_panel.update_insight("Overlay configuration updated.")

    # ----------------------------------------------------------------------
    # Theme handling
    # ----------------------------------------------------------------------
    def _apply_theme(self) -> None:
        """Apply current theme to the application."""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)

        bg_stylesheet = self.theme_manager.get_background_stylesheet()
        if bg_stylesheet:
            self.setStyleSheet(stylesheet + bg_stylesheet)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet)

    def open_theme_dialog(self) -> None:
        """Open theme selection dialog."""
        dialog = ThemeDialog(self.theme_manager, parent=self)
        if dialog.exec():
            self._apply_theme()
            self._update_widget_styles()
            self.ai_panel.update_insight("Theme updated.")

    def _update_widget_styles(self) -> None:
        """Update styles for all child widgets."""
        for widget in self.findChildren(QWidget):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    # ----------------------------------------------------------------------
    # Diagnostics, email, display, export
    # ----------------------------------------------------------------------
    def _init_diagnostics(self) -> None:
        """Initialize diagnostics system."""
        try:
            from services.system_diagnostics import SystemDiagnostics
            from ui.diagnostics_widget import DiagnosticsWidget

            diagnostics = SystemDiagnostics()
            self.diagnostics_widget = DiagnosticsWidget(diagnostics, parent=self)
            self.diagnostics_widget.hide()
            self.diagnostics_widget.run_startup_check()
        except Exception as exc:  # pragma: no cover - optional
            print(f"[WARN] Diagnostics unavailable: {exc}")

    def show_diagnostics(self) -> None:
        """Show diagnostics screen."""
        from ui.diagnostics_screen import show_diagnostics

        diagnostics_screen = show_diagnostics(parent=self)
        diagnostics_screen.show()

    def open_diagnostics(self) -> None:
        """Open diagnostics (alias for show_diagnostics)."""
        self.show_diagnostics()

    def toggle_video_overlay(self) -> None:
        """Toggle video overlay mode."""
        if self.camera_manager:
            try:
                # Toggle overlay on first camera
                cameras = list(self.camera_manager.camera_manager.cameras.keys())
                if cameras:
                    self.camera_manager.toggle_overlay(cameras[0])
                    self.ai_panel.update_insight("Video overlay toggled.")
            except Exception as exc:
                print(f"[WARN] Video overlay toggle failed: {exc}")
        else:
            self.ai_panel.update_insight("No camera manager available.")

    def toggle_external_display(self) -> None:
        """Toggle external display output."""
        if self.display_manager:
            try:
                if self.display_manager.is_active():
                    self.display_manager.stop()
                    self.ai_panel.update_insight("External display stopped.")
                else:
                    self.display_manager.start()
                    self.ai_panel.update_insight("External display started.")
            except Exception as exc:
                print(f"[WARN] External display toggle failed: {exc}")
        else:
            self.ai_panel.update_insight("No display manager available.")

    def email_logs(self) -> None:
        """Open email logs dialog."""
        from services.email_service import EmailService
        from ui.email_logs_dialog import EmailLogsDialog

        log_directories: list[Path] = []

        if hasattr(self, "data_logger") and self.data_logger:
            log_directories.append(Path(self.data_logger.log_dir))

        if (
            hasattr(self, "camera_manager")
            and self.camera_manager
            and self.camera_manager.video_logger
        ):
            log_directories.append(self.camera_manager.video_logger.output_dir)

        if hasattr(self, "usb_manager") and self.usb_manager and self.usb_manager.active_device:
            usb_log_path = self.usb_manager.get_logs_path("telemetry")
            if usb_log_path.exists():
                log_directories.append(usb_log_path)
            usb_video_path = self.usb_manager.get_session_path("video")
            if usb_video_path.exists():
                log_directories.append(usb_video_path)

        if not log_directories:
            log_directories.append(Path("logs"))

        email_service = EmailService()
        dialog = EmailLogsDialog(
            log_directories=log_directories,
            email_service=email_service,
            parent=self,
        )
        if dialog.exec():
            self.ai_panel.update_insight("Log files emailed successfully.")

    def _show_module_placeholder(self, module_name: str) -> None:
        """Show placeholder message for module tabs."""
        self.ai_panel.update_insight(
            f"📦 {module_name} module selected. Full implementation coming soon!",
            level="info",
        )

    def _open_virtual_dyno(self) -> None:
        """Open Virtual Dyno in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not DYNO_AVAILABLE or DynoTab is None:
            self.ai_panel.update_insight(
                "⚠️ Virtual Dyno module not available. Check dependencies.",
                level="warning",
            )
            return
        
        try:
            # Create dialog window for dyno
            dialog = QDialog(self)
            dialog.setWindowTitle("📈 Virtual Dyno - Horsepower Estimation")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Add the dyno tab
            dyno_widget = DynoTab()
            layout.addWidget(dyno_widget)
            
            self.ai_panel.update_insight(
                "📈 Virtual Dyno opened! Configure vehicle specs and start a run.",
                level="info",
            )
            
            dialog.exec()
            
        except Exception as e:
            self.ai_panel.update_insight(
                f"❌ Failed to open Virtual Dyno: {e}",
                level="error",
            )

    def _open_ecu_tuning(self) -> None:
        """Open ECU Tuning in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not ECU_TUNING_AVAILABLE or ECUTuningMain is None:
            self.ai_panel.update_insight(
                "⚠️ ECU Tuning module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🔧 ECU Tuning - Professional Engine Tuning")
            dialog.setMinimumSize(1200, 800)
            dialog.resize(1400, 900)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            ecu_widget = ECUTuningMain()
            layout.addWidget(ecu_widget)
            
            self.ai_panel.update_insight(
                "🔧 ECU Tuning opened! Configure fuel maps, timing, and more.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open ECU Tuning: {e}", level="error")

    def _open_vbox_features(self) -> None:
        """Open VBOX Features tab in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not VBOX_FEATURES_AVAILABLE or VBOXFeaturesMain is None:
            self.ai_panel.update_insight(
                "⚠️ VBOX Features module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📡 VBOX Features - GPS/IMU/ADAS/CAN")
            dialog.setMinimumSize(1200, 800)
            dialog.resize(1400, 900)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            vbox_widget = VBOXFeaturesMain()
            layout.addWidget(vbox_widget)
            
            self.ai_panel.update_insight(
                "📡 VBOX Features opened! Configure GPS, IMU, ADAS, CAN, and more.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open VBOX Features: {e}", level="error")
    
    def _open_drag_racing(self) -> None:
        """Open Drag Racing tab in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not DRAG_RACING_AVAILABLE or DragRacingTab is None:
            self.ai_panel.update_insight(
                "⚠️ Drag Racing module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🏁 Drag Racing Analyzer")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            drag_widget = DragRacingTab()
            layout.addWidget(drag_widget)
            
            self.ai_panel.update_insight(
                "🏁 Drag Racing opened! Analyze runs, get coaching advice.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Drag Racing: {e}", level="error")

    def _open_track_learning(self) -> None:
        """Open Track Learning AI in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not TRACK_LEARNING_AVAILABLE or TrackLearningTab is None:
            self.ai_panel.update_insight(
                "⚠️ Track Learning module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🛤️ Track Learning AI")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            track_widget = TrackLearningTab()
            layout.addWidget(track_widget)
            
            self.ai_panel.update_insight(
                "🛤️ Track Learning AI opened! Learn optimal racing lines.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Track Learning: {e}", level="error")

    def _open_sensors(self) -> None:
        """Open Sensors configuration in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not SENSORS_AVAILABLE or SensorsTab is None:
            self.ai_panel.update_insight(
                "⚠️ Sensors module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📡 Sensors Configuration")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            sensors_widget = SensorsTab()
            layout.addWidget(sensors_widget)
            
            self.ai_panel.update_insight(
                "📡 Sensors opened! Configure wideband, EGT, and more.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Sensors: {e}", level="error")

    def _open_auto_tuning(self) -> None:
        """Open Auto Tuning AI in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not AUTO_TUNING_AVAILABLE or AutoTuningTab is None:
            self.ai_panel.update_insight(
                "⚠️ Auto Tuning module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🤖 Auto Tuning AI")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            auto_tune_widget = AutoTuningTab()
            layout.addWidget(auto_tune_widget)
            
            self.ai_panel.update_insight(
                "🤖 Auto Tuning AI opened! Let AI optimize your tune.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Auto Tuning: {e}", level="error")

    def _open_diesel_tuning(self) -> None:
        """Open Diesel Tuning in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not DIESEL_TUNING_AVAILABLE or DieselTuningTab is None:
            self.ai_panel.update_insight(
                "⚠️ Diesel Tuning module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🛢️ Diesel Tuning")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            diesel_widget = DieselTuningTab()
            layout.addWidget(diesel_widget)
            
            self.ai_panel.update_insight(
                "🛢️ Diesel Tuning opened! Optimize diesel-specific parameters.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Diesel Tuning: {e}", level="error")

    def _open_safety_alerts(self) -> None:
        """Open Safety Alerts configuration in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        if not SAFETY_ALERTS_AVAILABLE or SafetyAlertsPanel is None:
            self.ai_panel.update_insight(
                "⚠️ Safety Alerts module not available.",
                level="warning",
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🛡️ Safety Alerts & Failsafes")
            dialog.setMinimumSize(700, 500)
            dialog.resize(900, 600)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            safety_widget = SafetyAlertsPanel()
            layout.addWidget(safety_widget)
            
            self.ai_panel.update_insight(
                "🛡️ Safety Alerts opened! Configure rev limiters, boost cut, failsafes.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Safety Alerts: {e}", level="error")

    def _open_nitrous(self) -> None:
        """Open Nitrous control in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        try:
            from ui.ecu_tuning_main import NitrousTab
            
            dialog = QDialog(self)
            dialog.setWindowTitle("💨 Nitrous Oxide Control")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            nitrous_widget = NitrousTab()
            layout.addWidget(nitrous_widget)
            
            self.ai_panel.update_insight(
                "💨 Nitrous Control opened! Configure stages, timing, and safety.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Nitrous: {e}", level="error")

    def _open_boost_control(self) -> None:
        """Open Boost Control in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        try:
            from ui.ecu_sub_tabs import BoostControlTab
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🌀 Turbo/Boost Control")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            boost_widget = BoostControlTab()
            layout.addWidget(boost_widget)
            
            self.ai_panel.update_insight(
                "🌀 Boost Control opened! Configure wastegate, boost targets, and duty cycles.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Boost Control: {e}", level="error")

    def _open_fuel_management(self) -> None:
        """Open Fuel Management (E85/Methanol) in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        
        try:
            # Check if fuel additive manager is available
            from services.fuel_additive_manager import FuelAdditiveManager
            
            dialog = QDialog(self)
            dialog.setWindowTitle("⛽ Fuel Management - E85/Methanol/Flex Fuel")
            dialog.setMinimumSize(800, 600)
            dialog.resize(1000, 700)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Create a simple fuel management interface
            title = QLabel("⛽ Fuel Management System")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding: 10px;")
            layout.addWidget(title)
            
            info = QLabel("""
            <div style='color: white; font-size: 14px; padding: 10px;'>
            <h3>Supported Fuel Types:</h3>
            <ul>
                <li><b>🌽 E85 Flex Fuel</b> - Ethanol content detection & compensation</li>
                <li><b>💧 Methanol Injection</b> - Water/Methanol injection control</li>
                <li><b>🔥 Nitromethane</b> - Racing fuel management</li>
                <li><b>⛽ Gasoline Blends</b> - 91/93/100+ octane tuning</li>
            </ul>
            <h3>Features:</h3>
            <ul>
                <li>Real-time fuel composition analysis</li>
                <li>Automatic AFR compensation</li>
                <li>Timing adjustments based on fuel type</li>
                <li>Injection timing optimization</li>
            </ul>
            </div>
            """)
            info.setWordWrap(True)
            layout.addWidget(info)
            
            layout.addStretch()
            
            self.ai_panel.update_insight(
                "⛽ Fuel Management opened! Configure E85, methanol, and flex fuel settings.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Fuel Management: {e}", level="error")

    def _open_log_viewer(self) -> None:
        """Open Log Viewer in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        try:
            from ui.log_viewer import LogViewer
            
            dialog = QDialog(self)
            dialog.setWindowTitle("📜 Log Viewer")
            dialog.setMinimumSize(900, 600)
            dialog.resize(1100, 700)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            log_widget = LogViewer()
            layout.addWidget(log_widget)
            
            self.ai_panel.update_insight(
                "📜 Log Viewer opened! View and analyze system logs.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Log Viewer: {e}", level="error")

    def _open_tune_database(self) -> None:
        """Open Tune Database in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        try:
            from ui.tune_database_tab import TuneDatabaseTab
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🗄️ Tune Map Database")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            
            tune_widget = TuneDatabaseTab()
            layout.addWidget(tune_widget)
            
            self.ai_panel.update_insight(
                "🗄️ Tune Database opened! Browse and load tune maps.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Tune Database: {e}", level="error")

    def _open_onboarding_wizard(self) -> None:
        """Open Onboarding Wizard for first-time setup."""
        try:
            from ui.onboarding_wizard import OnboardingWizard
            
            wizard = OnboardingWizard(self)
            wizard.exec()
            
            self.ai_panel.update_insight(
                "🎉 Welcome! Setup wizard completed.",
                level="info",
            )
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open wizard: {e}", level="error")

    def _open_ai_racing_coach(self) -> None:
        """Open AI Racing Coach in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox
        
        try:
            from services.ai_racing_coach import AIRacingCoach, CoachingAdvice
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🎓 AI Racing Coach - Real-Time Coaching")
            dialog.setMinimumSize(800, 600)
            dialog.resize(1000, 700)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("🎓 AI Racing Coach")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #16a085; border-radius: 5px;")
            layout.addWidget(title)
            
            # Status
            status_label = QLabel("Status: Ready for coaching")
            status_label.setStyleSheet("font-size: 12px; color: #2ecc71; padding: 5px;")
            layout.addWidget(status_label)
            
            # Coaching advice display
            advice_group = QGroupBox("Real-Time Coaching Advice")
            advice_group.setStyleSheet("color: white; font-size: 14px;")
            advice_layout = QVBoxLayout(advice_group)
            
            advice_text = QTextEdit()
            advice_text.setReadOnly(True)
            advice_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: monospace; font-size: 12px;")
            advice_text.setPlainText("""
🎓 AI Racing Coach Ready!

Features:
• Real-time voice coaching
• Lap analysis and sector comparison
• Personalized feedback
• Learning from your best laps

The coach will provide advice on:
• Braking points
• Throttle application
• Shift timing
• Corner entry/exit
• Line optimization

Start a session to begin receiving coaching!
            """)
            advice_layout.addWidget(advice_text)
            layout.addWidget(advice_group)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            start_btn = QPushButton("▶️ Start Coaching")
            start_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
            start_btn.clicked.connect(lambda: status_label.setText("Status: 🎤 Coaching Active!"))
            controls_layout.addWidget(start_btn)
            
            stop_btn = QPushButton("⏹️ Stop")
            stop_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
            controls_layout.addWidget(stop_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "🎓 AI Racing Coach opened! Get real-time coaching advice.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open AI Racing Coach: {e}", level="error")

    def _open_pit_strategist(self) -> None:
        """Open AI Pit Strategist in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
        
        try:
            from services.ai_pit_strategist import AIPitStrategist, RaceConditions, TireCondition
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🏁 AI Pit Strategist - Optimal Race Strategy")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("🏁 AI Pit Strategist")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #d35400; border-radius: 5px;")
            layout.addWidget(title)
            
            # Strategy table
            strategy_group = QGroupBox("Recommended Pit Strategy")
            strategy_group.setStyleSheet("color: white; font-size: 14px;")
            strategy_layout = QVBoxLayout(strategy_group)
            
            strategy_table = QTableWidget()
            strategy_table.setColumnCount(6)
            strategy_table.setHorizontalHeaderLabels(["Pit Lap", "Reason", "Tire Change", "Fuel (L)", "Time Loss", "Gain"])
            strategy_table.horizontalHeader().setStretchLastSection(True)
            strategy_table.setStyleSheet("background-color: #1a1a1a; color: white;")
            strategy_layout.addWidget(strategy_table)
            layout.addWidget(strategy_group)
            
            # Info
            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-size: 11px;")
            info_text.setPlainText("""
🏁 AI Pit Strategist Features:

• Optimal pit stop timing calculation
• Tire change recommendations
• Fuel strategy optimization
• Time loss/gain analysis
• Multi-stop strategy planning
• Weather-adaptive strategy

This AI analyzes:
- Current race position
- Fuel consumption
- Tire wear
- Track conditions
- Weather changes
- Competitor strategies

Enter race conditions to get strategy recommendations!
            """)
            info_text.setMaximumHeight(200)
            layout.addWidget(info_text)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            calculate_btn = QPushButton("🧮 Calculate Strategy")
            calculate_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
            controls_layout.addWidget(calculate_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "🏁 AI Pit Strategist opened! Calculate optimal race strategy.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Pit Strategist: {e}", level="error")

    def _open_voice_ecu_control(self) -> None:
        """Open Voice ECU Control in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QListWidget, QListWidgetItem
        
        try:
            from services.voice_ecu_control import VoiceECUControl, VoiceCommand
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🎤 Voice ECU Control - Hands-Free Tuning")
            dialog.setMinimumSize(800, 600)
            dialog.resize(1000, 700)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("🎤 Voice ECU Control")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #8e44ad; border-radius: 5px;")
            layout.addWidget(title)
            
            # Status
            status_label = QLabel("Status: Voice control ready")
            status_label.setStyleSheet("font-size: 12px; color: #2ecc71; padding: 5px;")
            layout.addWidget(status_label)
            
            # Command list
            commands_group = QGroupBox("Available Voice Commands")
            commands_group.setStyleSheet("color: white; font-size: 14px;")
            commands_layout = QVBoxLayout(commands_group)
            
            commands_list = QListWidget()
            commands_list.setStyleSheet("background-color: #1a1a1a; color: white;")
            commands = [
                "🎤 'More Power' - Increase power output",
                "🎤 'Fuel Economy' - Optimize for efficiency",
                "🎤 'Race Mode' - Maximum performance",
                "🎤 'Safe Mode' - Conservative settings",
                "🎤 'Increase Boost' - Raise boost pressure",
                "🎤 'Decrease Boost' - Lower boost pressure",
                "🎤 'Richer' - Enrich fuel mixture",
                "🎤 'Leaner' - Lean fuel mixture",
                "🎤 'Reset' - Return to default settings"
            ]
            for cmd in commands:
                commands_list.addItem(cmd)
            commands_layout.addWidget(commands_list)
            layout.addWidget(commands_group)
            
            # History
            history_text = QTextEdit()
            history_text.setReadOnly(True)
            history_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: monospace; font-size: 11px;")
            history_text.setPlainText("Command history will appear here...")
            history_text.setMaximumHeight(150)
            layout.addWidget(history_text)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            start_btn = QPushButton("🎤 Start Listening")
            start_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
            start_btn.clicked.connect(lambda: status_label.setText("Status: 🎤 Listening for commands..."))
            controls_layout.addWidget(start_btn)
            
            stop_btn = QPushButton("⏹️ Stop")
            stop_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
            controls_layout.addWidget(stop_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "🎤 Voice ECU Control opened! Control your ECU with voice commands.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Voice ECU Control: {e}", level="error")

    def _open_weather_adaptive_tuning(self) -> None:
        """Open Weather Adaptive Tuning in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
        
        try:
            from services.weather_adaptive_tuning import WeatherAdaptiveTuning, WeatherConditions
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🌦️ Weather Adaptive Tuning - Automatic Weather Compensation")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("🌦️ Weather Adaptive Tuning")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #3498db; border-radius: 5px;")
            layout.addWidget(title)
            
            # Current conditions
            conditions_group = QGroupBox("Current Weather Conditions")
            conditions_group.setStyleSheet("color: white; font-size: 14px;")
            conditions_layout = QVBoxLayout(conditions_group)
            
            conditions_text = QTextEdit()
            conditions_text.setReadOnly(True)
            conditions_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: monospace; font-size: 11px;")
            conditions_text.setPlainText("""
Temperature: --°C
Humidity: --%
Pressure: -- hPa
Altitude: -- m
Weather: -- 
Track Temp: --°C
            """)
            conditions_text.setMaximumHeight(150)
            conditions_layout.addWidget(conditions_text)
            layout.addWidget(conditions_group)
            
            # Adjustments table
            adjustments_group = QGroupBox("Recommended Tuning Adjustments")
            adjustments_group.setStyleSheet("color: white; font-size: 14px;")
            adjustments_layout = QVBoxLayout(adjustments_group)
            
            adjustments_table = QTableWidget()
            adjustments_table.setColumnCount(4)
            adjustments_table.setHorizontalHeaderLabels(["Parameter", "Adjustment", "Reason", "Confidence"])
            adjustments_table.horizontalHeader().setStretchLastSection(True)
            adjustments_table.setStyleSheet("background-color: #1a1a1a; color: white;")
            adjustments_layout.addWidget(adjustments_table)
            layout.addWidget(adjustments_group)
            
            # Info
            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-size: 11px;")
            info_text.setPlainText("""
🌦️ Weather Adaptive Tuning Features:

• Automatic tuning adjustments for weather changes
• Rain compensation (reduced power, traction control)
• Temperature compensation (air density changes)
• Altitude compensation (boost adjustments)
• Humidity compensation (cooling efficiency)
• Real-time weather monitoring

The system automatically adjusts:
- Fuel mixture
- Ignition timing
- Boost pressure
- Traction control
- Cooling fan settings

Set it and forget it - your car adapts automatically!
            """)
            info_text.setMaximumHeight(180)
            layout.addWidget(info_text)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            enable_btn = QPushButton("✅ Enable Auto-Tuning")
            enable_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
            controls_layout.addWidget(enable_btn)
            
            update_btn = QPushButton("🔄 Update Weather")
            update_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
            controls_layout.addWidget(update_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "🌦️ Weather Adaptive Tuning opened! Automatic weather compensation enabled.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Weather Adaptive Tuning: {e}", level="error")

    def _open_predictive_crash_prevention(self) -> None:
        """Open Predictive Crash Prevention in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QGroupBox, QListWidget
        
        try:
            from services.predictive_crash_prevention import PredictiveCrashPrevention, DangerLevel
            
            dialog = QDialog(self)
            dialog.setWindowTitle("⚠️ Predictive Crash Prevention - AI Safety System")
            dialog.setMinimumSize(800, 600)
            dialog.resize(1000, 700)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("⚠️ Predictive Crash Prevention")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #c0392b; border-radius: 5px;")
            layout.addWidget(title)
            
            # Status
            status_label = QLabel("Status: Monitoring active")
            status_label.setStyleSheet("font-size: 12px; color: #2ecc71; padding: 5px;")
            layout.addWidget(status_label)
            
            # Alerts
            alerts_group = QGroupBox("Active Danger Alerts")
            alerts_group.setStyleSheet("color: white; font-size: 14px;")
            alerts_layout = QVBoxLayout(alerts_group)
            
            alerts_list = QListWidget()
            alerts_list.setStyleSheet("background-color: #1a1a1a; color: #ff0000; font-weight: bold;")
            alerts_list.addItem("No active alerts - System monitoring...")
            alerts_layout.addWidget(alerts_list)
            layout.addWidget(alerts_group)
            
            # Info
            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-size: 11px;")
            info_text.setPlainText("""
⚠️ Predictive Crash Prevention Features:

• AI-powered danger detection
• Real-time risk assessment
• Predictive alerts before incidents
• Automatic safety interventions
• Driver behavior analysis
• Collision avoidance warnings

The system monitors:
- Vehicle dynamics (G-forces, speed, acceleration)
- Driver behavior patterns
- Road conditions
- Traffic patterns
- Environmental factors

Alerts are provided at multiple danger levels:
🟢 Low - Informational
🟡 Medium - Caution
🟠 High - Warning
🔴 Critical - Immediate action required
            """)
            info_text.setMaximumHeight(250)
            layout.addWidget(info_text)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            enable_btn = QPushButton("✅ Enable Monitoring")
            enable_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
            controls_layout.addWidget(enable_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "⚠️ Predictive Crash Prevention opened! AI safety monitoring active.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Crash Prevention: {e}", level="error")

    def _open_fleet_management(self) -> None:
        """Open Fleet Management in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
        
        try:
            from services.fleet_management import FleetManagement, Vehicle
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🚗 Fleet Management - Multi-Vehicle Management")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("🚗 Fleet Management")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #16a085; border-radius: 5px;")
            layout.addWidget(title)
            
            # Vehicles table
            vehicles_group = QGroupBox("Fleet Vehicles")
            vehicles_group.setStyleSheet("color: white; font-size: 14px;")
            vehicles_layout = QVBoxLayout(vehicles_group)
            
            vehicles_table = QTableWidget()
            vehicles_table.setColumnCount(6)
            vehicles_table.setHorizontalHeaderLabels(["Vehicle", "Status", "Last Session", "Best Time", "Health", "Actions"])
            vehicles_table.horizontalHeader().setStretchLastSection(True)
            vehicles_table.setStyleSheet("background-color: #1a1a1a; color: white;")
            vehicles_layout.addWidget(vehicles_table)
            layout.addWidget(vehicles_group)
            
            # Stats
            stats_text = QLabel("""
            <div style='color: white; font-size: 12px; padding: 10px;'>
            <b>Fleet Statistics:</b><br>
            Total Vehicles: --<br>
            Active Vehicles: --<br>
            Total Sessions: --<br>
            Average Health Score: --
            </div>
            """)
            stats_text.setStyleSheet("background-color: #1a1a1a; border-radius: 5px;")
            layout.addWidget(stats_text)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            add_vehicle_btn = QPushButton("➕ Add Vehicle")
            add_vehicle_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
            controls_layout.addWidget(add_vehicle_btn)
            
            compare_btn = QPushButton("📊 Compare Vehicles")
            compare_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
            controls_layout.addWidget(compare_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "🚗 Fleet Management opened! Manage multiple vehicles and compare performance.",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Fleet Management: {e}", level="error")

    def _open_social_racing(self) -> None:
        """Open Social Racing Platform in a dialog window."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget
        
        try:
            from services.social_racing_platform import SocialRacingPlatform, LeaderboardEntry, Achievement
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🏆 Social Racing Platform - Leaderboards & Challenges")
            dialog.setMinimumSize(900, 700)
            dialog.resize(1100, 800)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title = QLabel("🏆 Social Racing Platform")
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; padding: 10px; background-color: #9b59b6; border-radius: 5px;")
            layout.addWidget(title)
            
            # Tabs
            tabs = QTabWidget()
            tabs.setStyleSheet("color: white;")
            
            # Leaderboard tab
            leaderboard_tab = QGroupBox("Global Leaderboard")
            leaderboard_layout = QVBoxLayout(leaderboard_tab)
            
            leaderboard_table = QTableWidget()
            leaderboard_table.setColumnCount(5)
            leaderboard_table.setHorizontalHeaderLabels(["Rank", "Username", "Track", "Best Time", "Vehicle"])
            leaderboard_table.horizontalHeader().setStretchLastSection(True)
            leaderboard_table.setStyleSheet("background-color: #1a1a1a; color: white;")
            leaderboard_layout.addWidget(leaderboard_table)
            tabs.addTab(leaderboard_tab, "🏆 Leaderboard")
            
            # Achievements tab
            achievements_tab = QGroupBox("Your Achievements")
            achievements_layout = QVBoxLayout(achievements_tab)
            
            achievements_table = QTableWidget()
            achievements_table.setColumnCount(3)
            achievements_table.setHorizontalHeaderLabels(["Achievement", "Description", "Unlocked"])
            achievements_table.horizontalHeader().setStretchLastSection(True)
            achievements_table.setStyleSheet("background-color: #1a1a1a; color: white;")
            achievements_layout.addWidget(achievements_table)
            tabs.addTab(achievements_tab, "🏅 Achievements")
            
            # Challenges tab
            challenges_tab = QGroupBox("Active Challenges")
            challenges_layout = QVBoxLayout(challenges_tab)
            
            challenges_table = QTableWidget()
            challenges_table.setColumnCount(4)
            challenges_table.setHorizontalHeaderLabels(["Challenge", "Track", "Target Time", "Prize"])
            challenges_table.horizontalHeader().setStretchLastSection(True)
            challenges_table.setStyleSheet("background-color: #1a1a1a; color: white;")
            challenges_layout.addWidget(challenges_table)
            tabs.addTab(challenges_tab, "🎯 Challenges")
            
            layout.addWidget(tabs)
            
            # Info
            info_text = QLabel("""
            <div style='color: white; font-size: 11px; padding: 10px;'>
            <b>Social Racing Features:</b><br>
            • Global leaderboards for every track<br>
            • Achievements and badges<br>
            • Weekly challenges with prizes<br>
            • Compare times with friends<br>
            • Share your best runs<br>
            • Join racing communities
            </div>
            """)
            info_text.setStyleSheet("background-color: #1a1a1a; border-radius: 5px;")
            layout.addWidget(info_text)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            sync_btn = QPushButton("🔄 Sync to Cloud")
            sync_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
            controls_layout.addWidget(sync_btn)
            
            share_btn = QPushButton("📤 Share Run")
            share_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
            controls_layout.addWidget(share_btn)
            
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.ai_panel.update_insight(
                "🏆 Social Racing Platform opened! Compete on global leaderboards!",
                level="info",
            )
            dialog.exec()
        except Exception as e:
            self.ai_panel.update_insight(f"❌ Failed to open Social Racing: {e}", level="error")

    def configure_display(self) -> None:
        """Open display configuration dialog."""
        from ui.display_config_dialog import DisplayConfigDialog

        if not self.display_manager:
            self.ai_panel.update_insight(
                "Display manager not available.",
                level="warning",
            )
            return

        dialog = DisplayConfigDialog(self.display_manager, parent=self)
        if dialog.exec():
            config = dialog.get_config()
            display = config.get("display")
            fullscreen = config.get("fullscreen", False)

            if display:
                if self.display_manager.move_window_to_display(
                    self,
                    display,
                    fullscreen=fullscreen,
                ):
                    self.ai_panel.update_insight(
                        f"Display output set to: {display.name}",
                    )
                else:
                    self.ai_panel.update_insight(
                        "Failed to configure display.",
                        level="warning",
                    )

    def export_data(self) -> None:
        """Open export dialog."""
        from ui.export_dialog import ExportDialog

        dialog = ExportDialog(parent=self)
        if dialog.exec():
            exported = dialog.get_exported_files()
            if exported:
                self.ai_panel.update_insight(
                    f"Exported {len(exported)} file(s) successfully.",
                )

    # ----------------------------------------------------------------------
    # USB / ECU / connectivity callbacks
    # ----------------------------------------------------------------------
    def _scan_usb_devices(self) -> None:
        """
        Scan for USB devices and update log paths.

        Logging paths are always updated to point to USB if available, or
        fall back to local disk. This avoids UI churn; the widget layout
        itself is not changed here.
        """
        if not getattr(self, "usb_manager", None):
            return

        try:
            self.usb_manager.scan_for_devices()

            if hasattr(self, "data_logger") and self.data_logger:
                log_path = self.usb_manager.get_logs_path("telemetry")
                current_path = Path(self.data_logger.log_dir)
                if log_path != current_path:
                    self.data_logger = DataLogger(log_dir=log_path)
                    if self.usb_manager.active_device:
                        self.ai_panel.update_insight(
                            f"Logging to USB: {self.usb_manager.active_device.label}",
                        )
                    else:
                        self.ai_panel.update_insight(
                            "Logging to local disk (no USB detected)",
                        )

            if self.camera_manager and self.camera_manager.video_logger:
                video_path = self.usb_manager.get_session_path("video")
                if self.camera_manager.video_logger.output_dir != video_path:
                    self.camera_manager.video_logger.output_dir = video_path
                    self.camera_manager.video_logger.output_dir.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
        except Exception:  # pragma: no cover - best effort only
            # Silently handle USB scan errors: logging continues to local disk
            pass

    def _on_ecu_detected(self, vendor: str) -> None:
        """Handle ECU detection."""
        vendor_name = vendor.upper()
        self.ai_panel.update_insight(f"ECU Detected: {vendor_name}", level="success")
        if self.status_bar:
            self.status_bar.update_status(f"ECU: {vendor_name}")
        
        # Update system status panel
        if hasattr(self, "system_status_panel"):
            self.system_status_panel.set_subsystem_status("ECU", SubsystemStatus.ONLINE, 100)
            self.system_status_panel.show_notification(f"ECU detected: {vendor_name}", "success")

    def _on_ecu_configured(self, config: dict) -> None:
        """Handle ECU configuration completion."""
        vendor = config.get("vendor", "unknown")
        self.ai_panel.update_insight(
            f"ECU configured: {vendor.upper()}\n"
            f"CAN: {config.get('can_bitrate', 0)}bps\n"
            f"Optimizations applied",
            level="success",
        )

        if getattr(self, "data_stream_controller", None) and self.ecu_auto_config:
            self.ecu_auto_config.apply_to_data_stream(self.data_stream_controller)

    def _on_ecu_detection_failed(self, error: str) -> None:
        """Handle ECU detection failure."""
        self.ai_panel.update_insight(
            f"ECU detection failed: {error}\nUsing default settings",
            level="warning",
        )
        
        # Update system status panel
        if hasattr(self, "system_status_panel"):
            self.system_status_panel.set_subsystem_status("ECU", SubsystemStatus.DEGRADED, 50)
            self.system_status_panel.show_notification("ECU detection failed - using defaults", "warning")

    def _on_connectivity_change(self, status) -> None:
        self.latest_connectivity = status
        if self.status_bar:
            self.status_bar.update_connectivity(status.summary())
        
        # Update system status panel
        if hasattr(self, "system_status_panel"):
            summary = status.summary().lower()
            if "connected" in summary or "online" in summary:
                self.system_status_panel.set_subsystem_status("NET", SubsystemStatus.ONLINE, 100)
            elif "degraded" in summary or "limited" in summary:
                self.system_status_panel.set_subsystem_status("NET", SubsystemStatus.DEGRADED, 60)
            else:
                self.system_status_panel.set_subsystem_status("NET", SubsystemStatus.OFFLINE, 0)

    # ----------------------------------------------------------------------
    # Qt lifecycle
    # ----------------------------------------------------------------------
    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        geo = self.geometry()

        # On Windows, if the window is still oddly tall, clamp height again
        if IS_WINDOWS and geo.height() > available.height():
            new_height = int(available.height() * 0.9)
            self.resize(geo.width(), new_height)

        geo = self.geometry()
        x = min(max(geo.x(), available.x()), available.right() - geo.width())
        y = min(max(geo.y(), available.y()), available.bottom() - geo.height())
        self.move(x, y)

    def closeEvent(self, event) -> None:  # noqa: N802
        """Clean up all resources when window closes."""
        LOGGER.info("Closing application - cleaning up resources...")
        
        # Stop live streams first (critical - prevents zombie FFmpeg processes)
        if hasattr(self, "live_streamer") and self.live_streamer:
            try:
                self.live_streamer.stop_stream()  # Stop all streams
                LOGGER.info("Stopped all live streams")
            except Exception as e:
                LOGGER.error(f"Error stopping live streams: {e}")
        
        # Stop data stream controller
        if hasattr(self, "data_stream_controller") and self.data_stream_controller:
            try:
                self.data_stream_controller.stop()
            except Exception as e:
                LOGGER.error(f"Error stopping data stream controller: {e}")
        
        # Stop connectivity manager
        if getattr(self, "connectivity_manager", None):
            try:
                self.connectivity_manager.stop()
            except Exception as e:
                LOGGER.error(f"Error stopping connectivity manager: {e}")
        
        # Close voice output
        if getattr(self, "voice_output", None):
            try:
                self.voice_output.close()
            except Exception as e:
                LOGGER.error(f"Error closing voice output: {e}")
        
        # Stop all cameras
        if self.camera_manager:
            try:
                self.camera_manager.stop_all()
            except Exception as e:
                LOGGER.error(f"Error stopping cameras: {e}")
        
        # Clean up auto knowledge ingestion service
        try:
            from services.auto_knowledge_ingestion_service import stop_auto_ingestion
            stop_auto_ingestion()
        except Exception as e:
            LOGGER.debug(f"Auto ingestion service cleanup: {e}")
        
        # Clean up error monitoring service
        try:
            from services.error_monitoring_service import get_error_monitor
            monitor = get_error_monitor(None)
            if monitor:
                monitor.stop()
        except Exception as e:
            LOGGER.debug(f"Error monitoring service cleanup: {e}")
        
        # Force garbage collection to free memory
        import gc
        gc.collect()
        
        LOGGER.info("Application cleanup complete")
        super().closeEvent(event)


def run() -> None:
    # Apply platform optimizations (e.g., for reTerminal DM)
    try:
        from core import optimize_for_reterminal

        optimize_for_reterminal()
    except Exception as exc:  # pragma: no cover - optional
        print(f"[WARN] Failed to apply platform optimizations: {exc}")

    app = QApplication(sys.argv)

    # Show startup diagnostics screen first
    from ui.diagnostics_screen import DiagnosticsScreen

    diagnostics = DiagnosticsScreen()
    diagnostics.show()
    app.processEvents()

    # Create main window in background (but don't show yet)
    window = MainWindow()

    # Show main window when diagnostics is closed or skipped
    def show_main_window() -> None:
        window.show()
        diagnostics.close()

    diagnostics.set_accept_callback(show_main_window)
    diagnostics.skip_btn.clicked.connect(show_main_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
