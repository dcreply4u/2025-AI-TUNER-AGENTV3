from __future__ import annotations

"""
=========================================================
AI Tuner Desktop – main shell and responsive layout host
=========================================================
"""

import platform
import sys

# Platform detection for OS-specific sizing
IS_WINDOWS = platform.system().lower().startswith("win")
from pathlib import Path

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
from ui.session_controls_panel import SessionControlsPanel
from ui.streaming_control_panel import StreamingControlPanel
from ui.system_status_panel import SystemStatusPanel, SubsystemStatus
from ui.telemetry_panel import TelemetryPanel
from ui.theme_dialog import ThemeDialog
from ui.theme_manager import ThemeManager
from ui.wheel_slip_widget import WheelSlipPanel
from ui.youtube_stream_widget import YouTubeStreamWidget


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
                background-color: #e0e0e0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #3498db;
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
                background-color: #1a1a1a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #00e0ff;
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
        self.telemetry_panel = TelemetryPanel()
        self.health_widget = HealthScoreWidget()
        self.health_widget.setFixedHeight(100)  # Compact fixed height
        
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

        # ------------------------------------------------------------------
        # Shared service instances
        # ------------------------------------------------------------------
        self.fault_predictor = PredictiveFaultDetector()
        self.tuning_advisor = TuningAdvisor()

        log_path = (
            self.usb_manager.get_logs_path("telemetry")
            if self.usb_manager
            else Path("logs/telemetry")
        )
        self.data_logger = DataLogger(log_dir=log_path)

        self.cloud_sync = CloudSync()
        self.performance_tracker = PerformanceTracker()
        self.geo_logger = GeoLogger()
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
        try:
            self.gps_interface = GPSInterface()
        except Exception as exc:  # pragma: no cover - hardware optional
            self.gps_interface = None
            print(f"[WARN] GPS interface unavailable: {exc}")

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
        left_column.setSpacing(8)
        left_column.addWidget(make_expanding(self.telemetry_panel), 3)  # Graphs get most space
        left_column.addWidget(self.drag_mode_panel, 0)  # Dodge Charger Drag Mode
        left_column.addSpacing(96)  # Extra gap before Engine Health
        left_column.addWidget(self.health_widget, 0)  # Engine Health
        left_column.addWidget(self.ai_panel, 0)  # AI Insights
        left_column.addWidget(self.gps_track_panel, 0)  # GPS/Map
        
        # ============================================================
        # CONTROL TABS - Visible tabs at bottom of left column
        # ============================================================
        self.control_tabs = QTabWidget()
        self.control_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
                color: #2c3e50;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #3498db;
                color: #3498db;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """)
        self.control_tabs.setMinimumHeight(300)
        
        # Tab 1: Wheel Slip Monitor
        slip_container = QWidget()
        slip_layout = QVBoxLayout(slip_container)
        slip_layout.setContentsMargins(8, 8, 8, 8)
        slip_layout.addWidget(self.wheel_slip_panel)
        self.control_tabs.addTab(slip_container, "🏁 Wheel Slip")
        
        # Tab 2: System Status
        self.control_tabs.addTab(self.system_status_panel, "📊 System Status")
        
        # Tab 3: Streaming Control
        self.streaming_panel = StreamingControlPanel(
            live_streamer=self.live_streamer,
            camera_manager=self.camera_manager,
        )
        self.control_tabs.addTab(self.streaming_panel, "📹 Streaming")
        
        # Tab 4: Session Controls
        self.session_controls = SessionControlsPanel()
        self.session_controls.start_session_clicked.connect(self.start_session)
        self.session_controls.voice_control_clicked.connect(self.start_voice_control)
        self.session_controls.replay_log_clicked.connect(self.start_replay_mode)
        self.session_controls.settings_clicked.connect(self.open_settings)
        self.session_controls.theme_clicked.connect(self.open_theme_dialog)
        self.session_controls.diagnostics_clicked.connect(self.open_diagnostics)
        self.session_controls.email_logs_clicked.connect(self.email_logs)
        self.session_controls.export_data_clicked.connect(self.export_data)
        self.session_controls.configure_cameras_clicked.connect(self.configure_cameras)
        self.session_controls.video_overlay_clicked.connect(self.toggle_video_overlay)
        self.session_controls.external_display_clicked.connect(self.toggle_external_display)
        self.session_controls.enable_camera_buttons(self.camera_manager is not None)
        self.control_tabs.addTab(self.session_controls, "⚙️ Controls")
        
        left_column.addWidget(self.control_tabs, 0)
        left_column.addStretch(1)

        # ============================================================
        # RIGHT COLUMN: Just Live Gauges
        # ============================================================
        gauge_group = QGroupBox("Live Gauges")
        gauge_group.setFixedHeight(580)
        gauge_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        gauge_layout = QVBoxLayout(gauge_group)
        gauge_layout.setContentsMargins(8, 12, 8, 8)
        gauge_layout.setSpacing(0)
        gauge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gauge_layout.addWidget(self.gauge_panel, 0, Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(gauge_group, 0)

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
        if getattr(self, "connectivity_manager", None):
            self.connectivity_manager.stop()
        if getattr(self, "voice_output", None):
            self.voice_output.close()
        if self.camera_manager:
            self.camera_manager.stop_all()
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
