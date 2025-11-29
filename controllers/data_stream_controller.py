from __future__ import annotations

"""\
=========================================================
Data Stream Controller – conductor for sensor symphonies
=========================================================
"""

import csv
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer

from advanced_capabilities import HealthScoringEngine
from ai.conversational_agent import ConversationalAgent
from ai.intelligent_advisor import AdvicePriority, IntelligentAdvisor
from ai.predictive_fault_detector import PredictiveFaultDetector
from ai.tuning_advisor import TuningAdvisor
from interfaces.gps_interface import GPSInterface
from interfaces.obd_interface import OBDInterface
from interfaces.racecapture_interface import RaceCaptureInterface
from interfaces.voice_output import VoiceOutput
from services import (
    CloudSync,
    ConnectivityManager,
    DataLogger,
    GeoLogger,
    LoggingHealthMonitor,
    PerformanceSnapshot,
    PerformanceTracker,
)
try:
    from services import FuelAdditiveManager
except ImportError:
    FuelAdditiveManager = None  # type: ignore
from ui.ai_insight_panel import AIInsightPanel
from ui.dragy_view import DragyPerformanceView
from ui.gauge_widget import GaugePanel
from ui.health_score_widget import HealthScoreWidget
from ui.status_bar import StatusBar
from ui.telemetry_panel import TelemetryPanel
from ui.wheel_slip_widget import WheelSlipPanel
from services.wheel_slip_service import WheelSlipService

if TYPE_CHECKING:  # pragma: no cover - imported for type hints only
    from controllers.camera_manager import CameraManager
    from services.can_vendor_detector import CANVendorDetector
    from services.voice_feedback import VoiceFeedback
    from ui.advice_panel import AdvicePanel

LOGGER = logging.getLogger(__name__)


@dataclass
class StreamSettings:
    source: str = "Auto"
    port: str = "/dev/ttyUSB0"
    baud: int = 115200
    interval_sec: float = 0.5
    mode: str = "live"  # live | replay
    replay_file: str | None = None
    network_preference: str = "Auto"
    obd_transport: str = "Auto"
    bluetooth_address: str | None = None
    wifi_interface: str = "wlan0"
    lte_interface: str = "wwan0"


class DataStreamController(QObject):
    """Qt-friendly controller for polling telemetry sources."""

    def __init__(
        self,
        telemetry_panel: TelemetryPanel,
        ai_panel: AIInsightPanel,
        predictor: PredictiveFaultDetector | None = None,
        health_widget: HealthScoreWidget | None = None,
        dragy_view: DragyPerformanceView | None = None,
        gauge_panel: GaugePanel | None = None,
        advisor: TuningAdvisor | None = None,
        advice_panel: "AdvicePanel | None" = None,
        logger: DataLogger | None = None,
        cloud_sync: CloudSync | None = None,
        status_bar: StatusBar | None = None,
        gps_interface: GPSInterface | None = None,
        performance_tracker: PerformanceTracker | None = None,
        geo_logger: GeoLogger | None = None,
        voice_output: VoiceOutput | None = None,
        conversational_agent: ConversationalAgent | None = None,
        connectivity_manager: ConnectivityManager | None = None,
        camera_manager: "CameraManager" | None = None,
        voice_feedback: "VoiceFeedback | None" = None,
        wheel_slip_panel: WheelSlipPanel | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.telemetry_panel = telemetry_panel
        self.ai_panel = ai_panel
        self.gauge_panel = gauge_panel
        self.wheel_slip_panel = wheel_slip_panel
        self.predictor = predictor or PredictiveFaultDetector()
        self.health_engine = HealthScoringEngine()
        self.health_widget = health_widget
        self.dragy_view = dragy_view
        self.advisor = advisor or TuningAdvisor()
        self.advice_panel = advice_panel
        
        # Intelligent advisor with historical learning
        from services.advanced_analytics import AdvancedAnalytics
        analytics = AdvancedAnalytics()
        self.intelligent_advisor = IntelligentAdvisor(analytics=analytics)
        self.logger = logger or DataLogger()
        self.cloud_sync = cloud_sync or CloudSync()
        self.status_bar = status_bar
        self.performance_tracker = performance_tracker or PerformanceTracker()
        self.geo_logger = geo_logger or GeoLogger()
        self.gps_interface = gps_interface
        self.voice_output = voice_output
        self.conversational_agent = conversational_agent
        self.connectivity_manager = connectivity_manager
        self.camera_manager = camera_manager
        self.voice_feedback = voice_feedback
        self._main_window = None  # Will be set if parent is MainWindow

        # Wheel Slip Service for drag racing optimization
        self.wheel_slip_service = WheelSlipService(
            tire_type="drag_radial",  # Default to drag radial, can be configured
            tire_diameter_inches=28.0,
            final_drive_ratio=3.73,
        )
        # Connect wheel slip warnings to voice feedback
        if self.voice_feedback and self.wheel_slip_panel:
            self.wheel_slip_service.slip_warning.connect(
                lambda msg, slip: self._speak(msg, channel="warning", throttle=5)
            )

        # Fuel/Additive Manager (comprehensive fuel system management)
        self.fuel_additive_manager = None
        if FuelAdditiveManager:
            self.fuel_additive_manager = FuelAdditiveManager(
                voice_feedback=voice_feedback,
                auto_control_enabled=False,  # Can be enabled via settings
            )

        # Industry Integration (driver behavior, fuel efficiency, maintenance, ELD, etc.)
        self.industry_integration = None
        try:
            from services.industry_integration import IndustryIntegration
            from core.industry_mode import get_industry_mode
            vehicle_id = getattr(self, "vehicle_id", "vehicle_1")
            driver_id = getattr(self, "driver_id", None)
            industry_mode = get_industry_mode()
            self.industry_integration = IndustryIntegration(
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                industry_mode=industry_mode,
            )
            LOGGER.info("Industry integration initialized for mode: %s", industry_mode.value)
        except Exception as e:
            LOGGER.warning("Industry integration not available: %s", e)
        
        # Density Altitude Calculator (auto-updates on startup)
        self.density_altitude_calculator = None
        try:
            from services.density_altitude_calculator import DensityAltitudeCalculator
            from services.external_data_integration import ExternalDataIntegration
            
            # Create weather data provider
            external_data = ExternalDataIntegration()
            
            # GPS provider function
            def gps_provider() -> Optional[dict]:
                if self.gps_interface:
                    fix = self.gps_interface.read_fix()
                    if fix and fix.altitude_ft is not None:
                        return {"altitude_ft": fix.altitude_ft, "altitude_m": fix.altitude_m}
                return None
            
            # Initialize Waveshare Environmental HAT (if available)
            self.environmental_hat = None
            try:
                from interfaces.waveshare_environmental_hat import get_environmental_hat
                # Check if simulator mode is enabled
                use_simulator = os.getenv("AITUNER_USE_ENV_SIMULATOR", "false").lower() in {"1", "true", "yes"}
                self.environmental_hat = get_environmental_hat(use_simulator=use_simulator)
                if self.environmental_hat.connect():
                    LOGGER.info("Waveshare Environmental HAT connected")
                else:
                    LOGGER.warning("Waveshare Environmental HAT connection failed")
            except Exception as e:
                LOGGER.debug(f"Waveshare Environmental HAT not available: {e}")
            
            # Temperature provider (priority: HAT > weather API)
            def temperature_provider() -> Optional[float]:
                # Try Waveshare HAT first
                if self.environmental_hat:
                    reading = self.environmental_hat.read()
                    if reading:
                        return reading.temperature_c
                
                # Fallback to weather API
                if self.gps_interface:
                    fix = self.gps_interface.read_fix()
                    if fix:
                        weather = external_data.get_weather(
                            location=f"{fix.latitude},{fix.longitude}",
                            lat=fix.latitude,
                            lon=fix.longitude,
                        )
                        if weather:
                            # Convert Fahrenheit to Celsius
                            return (weather.temperature_f - 32.0) * 5.0 / 9.0
                return None
            
            # Pressure provider (priority: HAT > weather API)
            def pressure_provider() -> Optional[float]:
                # Try Waveshare HAT first
                if self.environmental_hat:
                    reading = self.environmental_hat.read()
                    if reading:
                        # Return in millibars (hPa)
                        return reading.pressure_hpa
                
                # Fallback to weather API
                if self.gps_interface:
                    fix = self.gps_interface.read_fix()
                    if fix:
                        weather = external_data.get_weather(
                            location=f"{fix.latitude},{fix.longitude}",
                            lat=fix.latitude,
                            lon=fix.longitude,
                        )
                        if weather:
                            # Convert inHg to millibars
                            return weather.pressure_inhg * 33.8639
                return None
            
            # Humidity provider (priority: HAT > weather API)
            def humidity_provider() -> Optional[float]:
                # Try Waveshare HAT first
                if self.environmental_hat:
                    reading = self.environmental_hat.read()
                    if reading:
                        return reading.humidity_percent
                
                # Fallback to weather API
                if self.gps_interface:
                    fix = self.gps_interface.read_fix()
                    if fix:
                        weather = external_data.get_weather(
                            location=f"{fix.latitude},{fix.longitude}",
                            lat=fix.latitude,
                            lon=fix.longitude,
                        )
                        if weather:
                            return weather.humidity_percent
                return None
            
            # Create DA calculator
            self.density_altitude_calculator = DensityAltitudeCalculator(
                gps_provider=gps_provider,
                temperature_provider=temperature_provider,
                pressure_provider=pressure_provider,
                humidity_provider=humidity_provider,
            )
            
            # Calculate initial DA
            self.density_altitude_calculator.update()
            LOGGER.info("Density Altitude Calculator initialized - DA: %.0f ft", 
                       self.density_altitude_calculator.get_density_altitude_ft())
        except Exception as e:
            LOGGER.warning("Density Altitude Calculator not available: %s", e)

        # Logging health monitor
        self.logging_health_monitor = LoggingHealthMonitor(
            on_status_change=self._on_logging_status_change,
            voice_alert=self._voice_alert_logging,
        )
        if self.logger:
            self.logging_health_monitor.set_storage_path(Path(self.logger.log_dir))

        # CAN vendor detector
        self.can_vendor_detector: Optional["CANVendorDetector"] = None
        self.detected_vendor: Optional[str] = None

        # Health check timer
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self._check_logging_health)
        self.health_timer.start(2000)  # Check every 2 seconds

        self.settings = StreamSettings()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_poll)
        self.interface: OBDInterface | RaceCaptureInterface | None = None
        self._last_health_status: str | None = None
        self._predictor_aliases: Dict[str, tuple[str, ...]] = {
            "Engine_RPM": ("Engine_RPM", "RPM"),
            "Throttle_Position": ("Throttle_Position", "Throttle"),
            "Coolant_Temp": ("Coolant_Temp", "CoolantTemp"),
            "Vehicle_Speed": ("Vehicle_Speed", "Speed"),
        }
        self._last_location_publish = 0.0
        self._location_publish_interval = 15.0
        self._replay_buffer: List[dict[str, str]] | None = None
        self._replay_index: int = 0
        self._latest_sample: dict[str, float] = {}
        self._last_warning_spoken = 0.0
        self._spoken_tips: Dict[str, float] = {}
        self._session_id: Optional[str] = None
        self._update_count = 0  # Track number of data updates for debugging
        self._cameras_active = False
        self._best_announcements: Dict[str, float] = {}
        
        # Thread lock for thread-safe data access
        import threading
        self._data_lock = threading.Lock()
        
        # Run detection for intelligent advice
        self._run_detection_state = {
            "in_run": False,
            "run_start_time": None,
            "run_start_speed": None,
            "run_number": 0,
            "last_speed": 0.0,
            "run_metrics": {},
            "run_max_speed": 0.0,
        }

        # Advanced Algorithm Integration (correlation analysis, anomaly detection, limit monitoring)
        self.advanced_algorithms = None
        try:
            from services.advanced_algorithm_integration import AdvancedAlgorithmIntegration
            self.advanced_algorithms = AdvancedAlgorithmIntegration()
            LOGGER.info("Advanced Algorithm Integration initialized (correlation, anomaly detection, limit monitoring)")
        except Exception as e:
            LOGGER.warning("Advanced Algorithm Integration not available: %s", e)

        # IMU Interface (optional - for accelerometer, gyroscope, magnetometer)
        # Supports: MPU6050, MPU9250, BNO085, Sense HAT (AstroPi), IMU04
        self.imu_interface = None
        # Thread lock for thread-safe IMU access
        import threading
        self._imu_lock = threading.Lock()
        try:
            from interfaces.imu_interface import IMUInterface, IMUType
            # Auto-detect IMU (will detect Sense HAT/AstroPi on Pi 5)
            self.imu_interface = IMUInterface(imu_type=IMUType.AUTO_DETECT)
            if self.imu_interface.is_connected():
                LOGGER.info(f"IMU Interface initialized: {self.imu_interface.imu_type.value} (connected)")
            else:
                LOGGER.info(f"IMU Interface initialized: {self.imu_interface.imu_type.value} (not connected yet)")
        except Exception as e:
            LOGGER.debug("IMU Interface not available: %s", e)

        # Kalman Filter (GPS/IMU fusion - requires both GPS and IMU)
        self.kalman_filter = None
        if self.gps_interface and self.imu_interface:
            try:
                from services.kalman_filter import KalmanFilter
                # Initialize with default offsets (can be configured)
                self.kalman_filter = KalmanFilter(
                    antenna_to_imu_offset=(0.0, 0.0, 0.0),  # X, Y, Z meters
                    imu_to_reference_offset=(0.0, 0.0, 0.0),  # X, Y, Z meters
                    roof_mount=False,
                    adas_mode=False,
                )
                LOGGER.info("Kalman Filter initialized (GPS/IMU fusion enabled)")
            except Exception as e:
                LOGGER.warning("Kalman Filter not available: %s", e)

        # Dual Antenna GPS (optional - for slip angle, roll, pitch)
        self.dual_antenna_gps = None
        try:
            from interfaces.dual_antenna_gps import DualAntennaGPS
            # Only initialize if dual antenna GPS is configured
            # For now, we'll leave it None until explicitly configured
            LOGGER.debug("Dual Antenna GPS available but not configured")
        except Exception as e:
            LOGGER.debug("Dual Antenna GPS not available: %s", e)

        # Set up telemetry sync for cameras
        if self.camera_manager:
            self.camera_manager.set_telemetry_sync(self._get_current_telemetry)
            # Auto-detect and add any USB cameras that weren't detected at startup
            # This allows cameras connected after initialization to be detected
            try:
                added_cameras = self.camera_manager.auto_detect_and_add_cameras(include_network=False)
                if added_cameras:
                    LOGGER.info("Detected %d additional camera(s) after initialization: %s", 
                               len(added_cameras), ", ".join(added_cameras))
            except Exception as e:
                LOGGER.debug("Camera auto-detection check failed (non-critical): %s", e)
        
        # HDD Manager (for hard drive storage and sync)
        self.hdd_manager = None
        try:
            from services.hdd_manager import HDDManager
            self.hdd_manager = HDDManager()
            if self.hdd_manager.is_mounted():
                LOGGER.info("Hard drive detected and mounted: %s", self.hdd_manager.mount_point)
                project_path = self.hdd_manager.get_project_path()
                if project_path:
                    LOGGER.info("Project available on HDD: %s", project_path)
            else:
                LOGGER.debug("Hard drive not mounted (running from USB/local)")
        except Exception as e:
            LOGGER.debug("HDD Manager not available: %s", e)

    def configure(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        if self.connectivity_manager:
            self.connectivity_manager.configure(
                wifi_interface=self.settings.wifi_interface,
                lte_interface=self.settings.lte_interface,
            )

    def _update_status(self, text: str) -> None:
        if self.status_bar:
            self.status_bar.update_status(text)

    def _speak(self, text: str, channel: str = "generic", throttle: float = 5.0) -> None:
        if not self.voice_output or not text:
            return
        now = time.time()
        if channel == "warning":
            if now - self._last_warning_spoken < throttle:
                return
            self._last_warning_spoken = now
        elif channel == "tip":
            last = self._spoken_tips.get(text, 0.0)
            if now - last < throttle:
                return
            self._spoken_tips[text] = now
        self.voice_output.speak(text)

    def _start_cameras(self) -> None:
        if not self.camera_manager or self._cameras_active:
            return
        session_id = self._session_id or time.strftime("%Y%m%d_%H%M%S")
        try:
            self.camera_manager.start_recording(session_id)
            self._cameras_active = True
            self.ai_panel.update_insight(f"[Camera] Recording started ({session_id}).")
            # Camera manager will handle voice feedback
        except Exception as exc:
            self.ai_panel.update_insight(f"[Camera] Failed to start recording: {exc}", level="warning")
            if self.voice_feedback:
                self.voice_feedback.announce_camera_status(f"Failed to start recording: {exc}")

    def _stop_cameras(self, announce: bool = False) -> None:
        if not self.camera_manager or not self._cameras_active:
            return
        self.camera_manager.stop_recording()
        self._cameras_active = False
        if announce:
            self.ai_panel.update_insight("[Camera] Recording stopped.")

    def _network_ready(self) -> bool:
        if not self.connectivity_manager:
            return True
        if self.connectivity_manager.status.primary_link_ok(self.settings.network_preference):
            return True
        message = f"{self.settings.network_preference} link unavailable"
        self._update_status(message)
        self._speak(message, channel="warning", throttle=30)
        return False

    def _connect_obd(self) -> OBDInterface:
        port = self.settings.port
        transport = (self.settings.obd_transport or "auto").lower()
        if transport == "bluetooth":
            if not port or not port.startswith("/dev/"):
                port = "/dev/rfcomm0"
        interface = OBDInterface(port_str=port)
        interface.connect()
        return interface

    def _connect_racecapture(self) -> RaceCaptureInterface:
        interface = RaceCaptureInterface(
            port=self.settings.port,
            baud=self.settings.baud,
            poll_interval=self.settings.interval_sec,
        )
        interface.connect()
        return interface

    def _ensure_gps_interface(self) -> None:
        # Don't override existing GPS interface (e.g., SimulatedGPSInterface in demo mode)
        if self.gps_interface:
            LOGGER.info("GPS interface already set: %s (type: %s)", 
                       type(self.gps_interface).__name__, 
                       "SimulatedGPSInterface" if "Simulated" in type(self.gps_interface).__name__ else "Real GPS")
            return
        
        # Skip creating real GPS interface in simulated mode
        source = (self.settings.source or "auto").lower()
        import os
        if source == "simulated" or os.environ.get("AITUNER_DEMO_MODE") == "true":
            LOGGER.info("Skipping real GPS interface creation in simulated/demo mode - using SimulatedGPSInterface")
            # Try to get from window if it was set there
            parent = self.parent()
            if parent and hasattr(parent, 'gps_interface') and parent.gps_interface:
                self.gps_interface = parent.gps_interface
                LOGGER.info("Retrieved SimulatedGPSInterface from parent window")
            return
        
        try:
            self.gps_interface = GPSInterface()
            LOGGER.info("GPS interface initialized.")
        except Exception as exc:
            LOGGER.warning("GPS interface unavailable: %s", exc)
            self.gps_interface = None

    def _ensure_interface(self) -> None:
        # Check if interface is already set (e.g., by demo mode)
        if self.interface and hasattr(self.interface, 'is_connected') and self.interface.is_connected():
            LOGGER.info("Interface already connected")
            return
        source = (self.settings.source or "auto").lower()
        try:
            if source == "simulated":
                # Simulated interface should already be set by demo mode
                if not self.interface:
                    from interfaces.simulated_interface import SimulatedInterface
                    self.interface = SimulatedInterface(mode="demo")
                    self.interface.connect()
                    LOGGER.info("Created and connected simulated interface")
                elif not self.interface.is_connected():
                    self.interface.connect()
                    LOGGER.info("Reconnected simulated interface")
                return
            elif source == "racecapture":
                self.interface = self._connect_racecapture()
            elif source in ("obd", "obd-ii"):
                self.interface = self._connect_obd()
            else:
                try:
                    self.interface = self._connect_racecapture()
                except Exception as exc:
                    LOGGER.warning("RaceCapture unavailable (%s); falling back to OBD.", exc)
                    self.interface = self._connect_obd()
        except Exception as exc:
            self.interface = None
            self._update_status("Connection Failed")
            LOGGER.error("Failed to connect to telemetry source: %s", exc)
            raise

    def start(self) -> None:
        mode = (self.settings.mode or "live").lower()
        if mode == "replay":
            self._prepare_replay()
            self.timer.start(int(self.settings.interval_sec * 1000))
            self._update_status("Replaying Log")
            LOGGER.info("Replaying telemetry log: %s", self.settings.replay_file)
            self._stop_cameras()
            return

        self._replay_buffer = None
        self._replay_index = 0
        self._session_id = time.strftime("%Y%m%d_%H%M%S")
        self._update_status("Connecting...")
        
        # Skip network check for simulated mode
        source = (self.settings.source or "auto").lower()
        if source != "simulated":
            if not self._network_ready():
                return
        
        self._ensure_interface()
        self._ensure_gps_interface()
        
        # Skip camera start for simulated mode to avoid network scanning
        if source != "simulated":
            self._start_cameras()
        
        # Update logging health monitor storage path
        if self.logger:
            self.logging_health_monitor.set_storage_path(Path(self.logger.log_dir))
        
        # Try to detect CAN vendor if using CAN source
        if "can" in self.settings.source.lower() or self.settings.source == "Auto":
            # Start vendor detection in background (non-blocking)
            detect_timer = QTimer(self)
            detect_timer.setSingleShot(True)
            detect_timer.timeout.connect(self.detect_can_vendor)
            detect_timer.start(1000)  # Start detection after 1 second
        
        interval_ms = int(self.settings.interval_sec * 1000)
        self.timer.start(interval_ms)
        self.health_timer.start(2000)  # Start health monitoring
        self._update_status("Streaming Data")
        LOGGER.info("Data stream started: source=%s, interval=%dms, timer_active=%s", 
                   self.settings.source, interval_ms, self.timer.isActive())
        LOGGER.info("Telemetry panel available: %s", self.telemetry_panel is not None)
        
        # Force first poll immediately to get data flowing
        QTimer.singleShot(100, self._on_poll)
        LOGGER.info("First poll scheduled in 100ms - data should start flowing soon")

    def stop(self) -> None:
        """Stop data stream and clean up all resources."""
        if self.timer.isActive():
            self.timer.stop()
        if self.health_timer.isActive():
            self.health_timer.stop()
        self._replay_buffer = None
        self._replay_index = 0
        self._update_status("Idle")
        LOGGER.info("Data stream stopped.")
        self.performance_tracker.reset_session()
        self._stop_cameras(announce=True)
        
        # Close CAN vendor detector
        if self.can_vendor_detector:
            try:
                self.can_vendor_detector.close()
            except Exception as e:
                LOGGER.warning("Error closing CAN vendor detector: %s", e)
        
        # Close IMU interface
        if self.imu_interface:
            try:
                if self.imu_interface.is_connected():
                    self.imu_interface.close()
                    LOGGER.debug("IMU interface closed")
            except Exception as e:
                LOGGER.warning("Error closing IMU interface: %s", e)
        
        # Close GPS interface (if it has a close method)
        if self.gps_interface and hasattr(self.gps_interface, 'close'):
            try:
                self.gps_interface.close()
                LOGGER.debug("GPS interface closed")
            except Exception as e:
                LOGGER.warning("Error closing GPS interface: %s", e)
        
        # Clear advanced algorithms buffer
        if self.advanced_algorithms:
            try:
                self.advanced_algorithms.log_buffer.clear()
                LOGGER.debug("Advanced algorithms buffer cleared")
            except Exception as e:
                LOGGER.warning("Error clearing algorithms buffer: %s", e)
        
        # Reset Kalman filter state (optional - keeps state for next session)
        # if self.kalman_filter:
        #     self.kalman_filter.status = KalmanFilterStatus.NOT_INITIALIZED

    def _prepare_replay(self) -> None:
        if not self.settings.replay_file:
            raise ValueError("Replay mode enabled without a log file.")
        path = Path(self.settings.replay_file).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Replay log not found: {path}")
        
        # Check file size to prevent memory issues with very large log files
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 500:  # Warn if file is > 500MB
            LOGGER.warning(f"Replay file is large ({file_size_mb:.1f}MB). Consider using a smaller log file for replay.")
        
        # Load replay buffer with memory-efficient approach
        # For very large files, we could implement streaming, but for now we'll load it
        # and warn if it's too large
        with path.open("r", newline="") as handle:
            reader = csv.DictReader(handle)
            self._replay_buffer = list(reader)
        
        # Log buffer size for monitoring
        LOGGER.info(f"Loaded {len(self._replay_buffer)} samples from replay file ({file_size_mb:.1f}MB)")
        
        self._replay_index = 0
        self.interface = None

    def _next_replay_sample(self) -> dict[str, float] | None:
        if not self._replay_buffer:
            return None
        if self._replay_index >= len(self._replay_buffer):
            self.stop()
            self._update_status("Replay Complete")
            return None
        row = self._replay_buffer[self._replay_index]
        self._replay_index += 1
        sample: dict[str, float] = {}
        for key, value in row.items():
            if value in (None, ""):
                continue
            try:
                sample[key] = float(value)
            except (TypeError, ValueError):
                continue
        return sample

    def _normalized_sample(self, data: dict[str, float]) -> dict[str, float]:
        sample: dict[str, float] = {}
        for canonical, aliases in self._predictor_aliases.items():
            for alias in aliases:
                if alias in data:
                    sample[canonical] = data[alias]
                    break
        return sample

    def _update_health(self, data: dict[str, float]) -> Optional[dict]:
        HEALTH_METRIC_MAP = {
            "CoolantTemp": "Coolant_Temp",
            "Coolant_Temp": "Coolant_Temp",
            "Oil_Pressure": "Oil_Pressure",
            "OilPressure": "Oil_Pressure",
            "Knock_Count": "Knock_Count",
            "KnockCount": "Knock_Count",
            "Boost_Pressure": "Boost_Pressure",
            "BoostPressure": "Boost_Pressure",
            "Fuel_Pressure": "Fuel_Pressure",
            "FuelPressure": "Fuel_Pressure",
            "Lambda": "Lambda",
            "AFR": "Lambda",
        }

        for key, value in data.items():
            canonical = HEALTH_METRIC_MAP.get(key)
            if canonical is None:
                continue
            self.health_engine.update(canonical, float(value))

        score_payload = self.health_engine.score()
        if self.health_widget:
            self.health_widget.update_score(score_payload)

        if score_payload:
            status = score_payload.get("status")
            score = score_payload.get("score", 0.0)
            warnings = score_payload.get("warnings", [])

            # Update voice feedback
            if self.voice_feedback:
                self.voice_feedback.update_health_status(score, status or "unknown", warnings)

            if status and status != self._last_health_status:
                if status in {"poor", "critical"}:
                    message = (
                        f"Health status changed to {status.upper()} "
                        f"(score {score:.2f})"
                    )
                    self.ai_panel.update_insight(message, level="warning")
                    self._speak(message, channel="warning", throttle=20)
                self._last_health_status = status
        return score_payload

    def _speed_from_data(self, data: dict[str, float]) -> Optional[float]:
        for key in ("Speed", "Vehicle_Speed", "speed"):
            if key in data:
                value = float(data[key])
                if value > 320:  # assume value reported in km/h
                    value *= 0.621371
                return value
        return None

    def _push_dragy_snapshot(self, update_track: bool = False) -> PerformanceSnapshot:
        snapshot = self.performance_tracker.snapshot()
        if self.dragy_view:
            self.dragy_view.update_metrics(snapshot)
            if update_track:
                self.dragy_view.update_track(snapshot.track_points)
        if self.conversational_agent:
            self.conversational_agent.update_context(performance=snapshot)
        self._announce_performance(snapshot)
        return snapshot

    def _announce_performance(self, snapshot: PerformanceSnapshot) -> None:
        interesting = ("0-60 mph", "0-100 mph", "1/4 mile")
        for key in interesting:
            best_value = snapshot.best_metrics.get(key)
            if not best_value:
                continue
            previous = self._best_announcements.get(key)
            if previous is None or best_value < previous - 0.05:
                message = f"New best {key}: {best_value:0.2f} seconds"
                self.ai_panel.update_insight(f"[Performance] {message}")
                self._speak(message, channel="tip", throttle=30)

                # Voice feedback announcement
                if self.voice_feedback:
                    self.voice_feedback.announce_performance(key, best_value, "seconds", is_best=True)

                self._best_announcements[key] = best_value

        # Update voice feedback with all performance metrics
        if self.voice_feedback:
            self.voice_feedback.update_performance_metrics(snapshot.metrics, snapshot.best_metrics)

    def _poll_gps(self, mode: str) -> None:
        if mode != "live" or not self.gps_interface:
            return
        fix = self.gps_interface.read_fix()
        if not fix:
            return
        payload = fix.to_payload()
        if self.geo_logger:
            self.geo_logger.log(payload)
        self.performance_tracker.update_gps(payload["lat"], payload["lon"])
        self._push_dragy_snapshot(update_track=True)
        if self.conversational_agent:
            self.conversational_agent.update_context(gps_fix=payload)
        
        # Update Density Altitude calculator
        if self.density_altitude_calculator:
            da_data = self.density_altitude_calculator.update()
            if da_data and self.gauge_panel:
                # Update DA gauge
                self.gauge_panel.update_data({
                    "DensityAltitude": da_data.density_altitude_ft,
                    "DA": da_data.density_altitude_ft,
                })
        
        # Update lap detector if available
        if hasattr(self, "lap_detector") and self.lap_detector:
            with self._data_lock:
                latest_sample = dict(self._latest_sample) if self._latest_sample else {}
            speed_mph = self._speed_from_data(latest_sample) or 0.0
            completed_lap = self.lap_detector.update(
                lat=payload["lat"],
                lon=payload["lon"],
                speed=speed_mph,
                timestamp=fix.timestamp,
            )
            if completed_lap:
                LOGGER.info("Lap %d completed: %.2f seconds", completed_lap.lap_number, completed_lap.duration)
                # Update session if available
                if hasattr(self, "session_manager") and self.session_manager:
                    current_session = self.session_manager.get_current_session()
                    if current_session:
                        self.session_manager.update_session(
                            current_session.session_id,
                            lap_count=len(self.lap_detector.completed_laps),
                            best_lap_time=(
                                self.lap_detector.get_best_lap().duration
                                if self.lap_detector.get_best_lap()
                                else None
                            ),
                        )
                # Announce lap completion
                if self.voice_feedback:
                    self.voice_feedback.announce(
                        f"Lap {completed_lap.lap_number} completed: {completed_lap.duration:.2f} seconds",
                        channel="performance",
                    )
        
        now = time.time()
        if now - self._last_location_publish >= self._location_publish_interval:
            try:
                self.cloud_sync.upload({"type": "gps_fix", **payload})
            except Exception:
                LOGGER.warning("Failed to sync GPS fix to cloud.", exc_info=True)
            self._last_location_publish = now

    def _update_performance(self) -> None:
        mode = (self.settings.mode or "live").lower()
        if mode == "replay" and not self.dragy_view:
            return
        speed_mph = self._speed_from_data(self._latest_sample or {})
        if speed_mph is None:
            return
        self.performance_tracker.update_speed(speed_mph, timestamp=time.time())
        self._push_dragy_snapshot(update_track=False)

    def _on_poll(self) -> None:
        """Poll interface for new telemetry data."""
        # Update Density Altitude periodically (auto-updates on startup and continuously)
        if self.density_altitude_calculator:
            da_data = self.density_altitude_calculator.update()
            if da_data and self.gauge_panel:
                # Update DA gauge
                self.gauge_panel.update_data({
                    "DensityAltitude": da_data.density_altitude_ft,
                    "DA": da_data.density_altitude_ft,
                })
        
        # Update industry integration services
        if self.industry_integration:
            try:
                location = None
                if self.gps_interface:
                    fix = self.gps_interface.read_fix()
                    if fix:
                        location = (fix.latitude, fix.longitude)
                
                # Get latest sample thread-safely
                with self._data_lock:
                    latest_telemetry = dict(self._latest_sample) if self._latest_sample else {}
                industry_updates = self.industry_integration.update_telemetry(
                    telemetry=latest_telemetry,
                    location=location,
                )
                
                # Handle industry-specific updates
                if "crash_detected" in industry_updates:
                    crash_event = industry_updates["crash_detected"]
                    LOGGER.critical("CRASH DETECTED: %s", crash_event.severity.value)
                    if self.voice_feedback:
                        self.voice_feedback.announce(
                            f"CRASH DETECTED - {crash_event.severity.value.upper()}",
                            channel="safety",
                        )
                
                if "driver_events" in industry_updates:
                    for event in industry_updates["driver_events"]:
                        if event.severity > 0.7:  # High severity
                            LOGGER.warning("Driver behavior event: %s", event.description)
                
                if "maintenance_due" in industry_updates:
                    due_items = industry_updates["maintenance_due"]
                    if due_items:
                        LOGGER.info("%d maintenance items due", len(due_items))
            except Exception as e:
                LOGGER.error("Error updating industry integration: %s", e, exc_info=True)
        mode = (self.settings.mode or "live").lower()
        if mode == "replay":
            data = self._next_replay_sample()
        else:
            if not self.interface:
                LOGGER.warning("No interface available for polling")
                return
            if not self.interface.is_connected():
                LOGGER.warning("Interface not connected - attempting reconnect")
                try:
                    self.interface.connect()
                except Exception as e:
                    LOGGER.error(f"Failed to connect interface: {e}")
                    return
            try:
                data = self.interface.read_data()
            except Exception as e:
                LOGGER.error(f"Error reading data from interface: {e}")
                return
                
        if not data:
            LOGGER.debug("No data received from interface")
            return
        
        # Store latest sample for other methods (thread-safe)
        with self._data_lock:
            self._latest_sample = data
        
        # Normalize data keys for telemetry panel (optimized with reverse lookup)
        normalized_data = {}
        
        # Build reverse lookup map if not already built (optimization - O(n*m) -> O(n))
        if not hasattr(self, '_key_to_canonical'):
            self._key_to_canonical = {}
            aliases = {
                "RPM": ("Engine_RPM", "RPM", "rpm"),
                "Throttle": ("Throttle_Position", "Throttle", "throttle"),
                "CoolantTemp": ("Coolant_Temp", "CoolantTemp", "coolant_temp"),
                "Speed": ("Vehicle_Speed", "Speed", "speed"),
                "Boost": ("Boost_Pressure", "Boost", "MAP"),
                "OilPressure": ("Oil_Pressure", "OilPressure"),
                "BrakePressure": ("Brake_Pressure", "BrakePressure"),
                "BatteryVoltage": ("Battery_Voltage", "BatteryVoltage"),
                "GForce_Lateral": ("GForce_Lateral", "LatG"),
                "GForce_Longitudinal": ("GForce_Longitudinal", "LongG"),
                "GPS_Speed": ("GPS_Speed", "gps_speed", "GPS_Speed_mps", "speed_mps"),
                "GPS_Heading": ("GPS_Heading", "gps_heading", "heading", "GPS_Heading_deg"),
                "GPS_Altitude": ("GPS_Altitude", "gps_altitude", "altitude_m", "GPS_Altitude_m"),
            }
            for canonical, keys in aliases.items():
                for key in keys:
                    if key not in self._key_to_canonical:  # First match wins
                        self._key_to_canonical[key] = canonical
        
        # Use reverse lookup for O(n) normalization instead of O(n*m)
        seen_canonicals = set()
        for key, value in data.items():
            # Add original key
            normalized_data[key] = float(value)
            
            # Add canonical name if mapping exists and not already added
            canonical = self._key_to_canonical.get(key)
            if canonical and canonical not in seen_canonicals:
                normalized_data[canonical] = float(value)
                seen_canonicals.add(canonical)
        
        # Read environmental data from Waveshare HAT if available
        if hasattr(self, 'environmental_hat') and self.environmental_hat:
            try:
                env_reading = self.environmental_hat.read()
                if env_reading:
                    # Add to normalized_data for telemetry
                    normalized_data["ambient_temp_c"] = env_reading.temperature_c
                    normalized_data["ambient_temp_f"] = env_reading.temperature_c * 9/5 + 32
                    normalized_data["humidity_percent"] = env_reading.humidity_percent
                    normalized_data["barometric_pressure_kpa"] = env_reading.pressure_kpa
                    normalized_data["barometric_pressure_hpa"] = env_reading.pressure_hpa
                    normalized_data["barometric_pressure_psi"] = env_reading.pressure_kpa * 0.145038
                    # Add optional sensors if available
                    if env_reading.light_lux is not None:
                        normalized_data["light_lux"] = env_reading.light_lux
                    if env_reading.noise_db is not None:
                        normalized_data["noise_db"] = env_reading.noise_db
            except Exception as e:
                LOGGER.debug(f"Error reading environmental HAT: {e}")
        
        # Read GPS data EARLY and add to normalized_data BEFORE updating telemetry panel
        gps_fix = None
        if self.gps_interface:
            try:
                gps_fix = self.gps_interface.read_fix()
                if gps_fix:
                    # Add GPS data to normalized_data for telemetry panel
                    normalized_data["GPS_Speed"] = gps_fix.speed_mps * 2.237  # Convert m/s to mph
                    normalized_data["GPS_Heading"] = gps_fix.heading
                    if gps_fix.altitude_m is not None:
                        normalized_data["GPS_Altitude"] = gps_fix.altitude_m
                    # Also add raw GPS data
                    normalized_data["GPS_Latitude"] = gps_fix.latitude
                    normalized_data["GPS_Longitude"] = gps_fix.longitude
                    normalized_data["gps_speed"] = gps_fix.speed_mps
                    normalized_data["gps_heading"] = gps_fix.heading
                    if gps_fix.altitude_m is not None:
                        normalized_data["gps_altitude"] = gps_fix.altitude_m
                    
                    # Debug logging for first few GPS reads
                    if not hasattr(self, '_gps_read_count'):
                        self._gps_read_count = 0
                    self._gps_read_count += 1
                    if self._gps_read_count <= 5:
                        LOGGER.info("GPS data read: Lat=%.5f, Lon=%.5f, Speed=%.1f mph, Heading=%.1f", 
                                   gps_fix.latitude, gps_fix.longitude, 
                                   gps_fix.speed_mps * 2.237, gps_fix.heading)
            except Exception as e:
                LOGGER.warning("Error reading GPS (early): %s", e, exc_info=True)
        else:
            # Debug: log if GPS interface is missing
            if not hasattr(self, '_gps_missing_logged'):
                LOGGER.warning("GPS interface is None - cannot read GPS data")
                self._gps_missing_logged = True
        
        # Update telemetry panel with normalized data (now includes GPS)
        if self.telemetry_panel:
            self.telemetry_panel.update_data(normalized_data)
            # Print first few updates for verification
            if not hasattr(self, '_update_count'):
                self._update_count = 0
            self._update_count += 1
            if self._update_count <= 10:  # Log first 10 updates
                rpm = normalized_data.get('RPM', normalized_data.get('Engine_RPM', 0))
                speed = normalized_data.get('Speed', normalized_data.get('Vehicle_Speed', 0))
                LOGGER.info("Data flow update #%d: %d values, RPM=%.0f, Speed=%.0f", 
                           self._update_count, len(normalized_data), rpm, speed)
            elif self._update_count == 11:
                LOGGER.info("Telemetry updates continuing (logging reduced)")
        
        # Update gauge panel with normalized data
        if self.gauge_panel:
            self.gauge_panel.update_data(normalized_data)

        # Advanced Algorithm Integration - Process telemetry through all algorithms
        if self.advanced_algorithms:
            try:
                algorithm_results = self.advanced_algorithms.process_telemetry(
                    telemetry_data=normalized_data,
                    timestamp=time.time()
                )
                
                # Display anomalies (using Enum instead of string comparison)
                if algorithm_results.anomalies:
                    from algorithms.enhanced_anomaly_detector import AnomalySeverity
                    for anomaly in algorithm_results.anomalies:
                        if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                            message = f"[Anomaly] {anomaly.description}"
                            self.ai_panel.update_insight(message, level="warning")
                            self._speak(f"Anomaly detected: {anomaly.description}", channel="warning", throttle=30)
                
                # Display limit violations (using Enum instead of string comparison)
                if algorithm_results.limit_violations and algorithm_results.limit_violations.violations:
                    from algorithms.parameter_limit_monitor import LimitSeverity
                    for violation in algorithm_results.limit_violations.violations:
                        if violation.severity in [LimitSeverity.CRITICAL]:
                            message = f"[Limit] {violation.parameter}: {violation.value:.1f} (limit: {violation.limit:.1f})"
                            self.ai_panel.update_insight(message, level="error")
                            self._speak(f"Parameter limit exceeded: {violation.parameter}", channel="warning", throttle=20)
                        elif violation.severity == LimitSeverity.WARNING:
                            message = f"[Limit] {violation.parameter}: {violation.value:.1f} (approaching limit: {violation.limit:.1f})"
                            self.ai_panel.update_insight(message, level="warning")
                
                # Display correlation insights periodically (CORRELATION_INSIGHT_INTERVAL samples to avoid spam)
                CORRELATION_INSIGHT_INTERVAL = 100  # Display insights every N samples
                if self._update_count % CORRELATION_INSIGHT_INTERVAL == 0:
                    try:
                        correlations = self.advanced_algorithms.get_correlations()
                        if correlations and correlations.correlations:
                            # Find unexpected correlations
                            unexpected = []
                            for (s1, s2), corr in correlations.correlations.items():
                                if abs(corr.correlation_coefficient) > 0.7:  # Strong correlation
                                    # Check if it's expected
                                    if s1 != s2 and corr.relationship_type != "none":
                                        unexpected.append(f"{s1} ↔ {s2}: {corr.correlation_coefficient:.2f}")
                            
                            if unexpected and len(unexpected) <= 3:  # Limit to 3 insights
                                insight = f"[Correlation] Strong relationships: {', '.join(unexpected[:3])}"
                                self.ai_panel.update_insight(insight, level="success")
                    except (ValueError, AttributeError) as e:
                        LOGGER.debug("Error getting correlations: %s", e)
                    except Exception as e:
                        LOGGER.warning("Unexpected error getting correlations: %s", e, exc_info=True)
            except (ValueError, AttributeError) as e:
                LOGGER.debug("Error processing advanced algorithms: %s", e)
            except Exception as e:
                LOGGER.warning("Unexpected error processing advanced algorithms: %s", e, exc_info=True)

        # Read IMU data if available (with thread safety)
        imu_reading = None
        if self.imu_interface:
            with self._imu_lock:
                try:
                    if not self.imu_interface.is_connected():
                        # Try to connect (non-blocking)
                        try:
                            self.imu_interface.connect()
                        except (ConnectionError, TimeoutError, OSError) as e:
                            LOGGER.debug("IMU connection failed (expected if not available): %s", e)
                            # IMU not available, continue without it
                        except Exception as e:
                            LOGGER.warning("Unexpected error connecting to IMU: %s", e, exc_info=True)
                    
                    if self.imu_interface.is_connected():
                        imu_reading = self.imu_interface.read()
                        if imu_reading:
                            # Add IMU data to normalized_data for display
                            normalized_data["GForce_X"] = imu_reading.accel_x / 9.81  # Convert m/s² to G
                            normalized_data["GForce_Y"] = imu_reading.accel_y / 9.81
                            normalized_data["GForce_Z"] = imu_reading.accel_z / 9.81
                            normalized_data["Gyro_X"] = imu_reading.gyro_x
                            normalized_data["Gyro_Y"] = imu_reading.gyro_y
                            normalized_data["Gyro_Z"] = imu_reading.gyro_z
                except (ConnectionError, TimeoutError, OSError) as e:
                    LOGGER.debug("Error reading IMU (connection issue): %s", e)
                except Exception as e:
                    LOGGER.warning("Unexpected error reading IMU: %s", e, exc_info=True)

        # GPS data was already read earlier and added to normalized_data
        # Now update performance tracker and GPS track panels with GPS coordinates
        if gps_fix:
            try:
                # Update performance tracker with GPS coordinates for track display
                if self.performance_tracker and gps_fix.latitude and gps_fix.longitude:
                        self.performance_tracker.update_gps(gps_fix.latitude, gps_fix.longitude)
                        snapshot = self.performance_tracker.snapshot()
                        
                        # Update dragy view GPS track panel (if it exists)
                        if self.dragy_view:
                            self.dragy_view.update_track(snapshot.track_points)
                            # Update distance
                            miles = snapshot.total_distance_m / 1609.34
                            self.dragy_view.gps_panel.set_distance(miles)
                            # Update status
                            status_text = f"Lat {gps_fix.latitude:.5f}, Lon {gps_fix.longitude:.5f}, {gps_fix.speed_mps * 2.237:.1f} mph"
                            self.dragy_view.gps_panel.set_status(status_text)
                        
                        # Also update standalone GPS track panel (if it exists)
                        # This is the one actually displayed in the UI
                        try:
                            # Check if we have a direct reference
                            if hasattr(self, '_gps_track_panel') and self._gps_track_panel:
                                gps_panel = self._gps_track_panel
                                # Update track points
                                gps_panel.set_track(snapshot.track_points)
                                # Update distance
                                miles = snapshot.total_distance_m / 1609.34
                                gps_panel.set_distance(miles)
                                # Update status
                                status_text = f"Lat {gps_fix.latitude:.5f}, Lon {gps_fix.longitude:.5f}, {gps_fix.speed_mps * 2.237:.1f} mph"
                                gps_panel.set_status(status_text)
                                if not hasattr(self, '_gps_panel_log_count'):
                                    self._gps_panel_log_count = 0
                                self._gps_panel_log_count += 1
                                if self._gps_panel_log_count <= 5:
                                    LOGGER.info("Updated standalone GPS track panel: %d points, %.2f miles, status=%s", 
                                               len(snapshot.track_points), miles, status_text)
                            else:
                                # Fallback: try to get from parent window
                                parent = self.parent()
                                if parent and hasattr(parent, 'gps_track_panel'):
                                    gps_panel = parent.gps_track_panel
                                    if gps_panel:
                                        gps_panel.set_track(snapshot.track_points)
                                        miles = snapshot.total_distance_m / 1609.34
                                        gps_panel.set_distance(miles)
                                        status_text = f"Lat {gps_fix.latitude:.5f}, Lon {gps_fix.longitude:.5f}, {gps_fix.speed_mps * 2.237:.1f} mph"
                                        gps_panel.set_status(status_text)
                                        # Cache the reference for next time
                                        self._gps_track_panel = gps_panel
                                        LOGGER.info("Found and updated GPS track panel via parent: %d points, %.2f miles", 
                                                   len(snapshot.track_points), miles)
                                else:
                                    if not hasattr(self, '_gps_panel_missing_logged'):
                                        LOGGER.warning("GPS track panel not found - parent=%s, has gps_track_panel=%s", 
                                                      parent, hasattr(parent, 'gps_track_panel') if parent else "no parent")
                                        self._gps_panel_missing_logged = True
                        except Exception as e:
                            LOGGER.warning("Could not update standalone GPS track panel: %s", e, exc_info=True)
            except Exception as e:
                LOGGER.debug("Error reading GPS: %s", e)

        # Update Kalman Filter with GPS + IMU data
        kalman_output = None
        if self.kalman_filter:
            try:
                # Update Kalman filter
                if gps_fix or imu_reading:
                    kalman_output = self.kalman_filter.update(
                        gps_fix=gps_fix,
                        imu_reading=imu_reading
                    )
                    
                    if kalman_output:
                        # Use Kalman filter output for more accurate position/velocity
                        # Add to normalized_data for display
                        normalized_data["KF_X_Velocity"] = kalman_output.x_velocity
                        normalized_data["KF_Y_Velocity"] = kalman_output.y_velocity
                        normalized_data["KF_Heading"] = kalman_output.heading
                        normalized_data["KF_Roll"] = kalman_output.roll
                        normalized_data["KF_Pitch"] = kalman_output.pitch
                        normalized_data["KF_Position_Quality"] = kalman_output.position_quality
                        
                        # Use Kalman filter velocity if available (more accurate)
                        if kalman_output.x_velocity and kalman_output.y_velocity:
                            kf_speed_mps = (kalman_output.x_velocity**2 + kalman_output.y_velocity**2)**0.5
                            normalized_data["KF_Speed"] = kf_speed_mps * 2.237  # Convert m/s to mph
                            
                            # Use KF speed for GPS_Speed if GPS not available or KF is more accurate
                            if "GPS_Speed" not in normalized_data or normalized_data.get("GPS_Speed", 0) == 0:
                                normalized_data["GPS_Speed"] = kf_speed_mps * 2.237
            except (ValueError, AttributeError) as e:
                LOGGER.debug("Error updating Kalman filter (validation/attribute): %s", e)
            except Exception as e:
                LOGGER.warning("Unexpected error updating Kalman filter: %s", e, exc_info=True)

        # Update wheel slip calculation for drag racing (wrapped in try-except to prevent breaking data flow)
        if self.wheel_slip_panel and self.wheel_slip_service:
            try:
                # Get required speeds for slip calculation
                # Driven wheel speed from driveshaft/rear wheel sensors
                driveshaft_rpm = normalized_data.get("Driveshaft_RPM", 0)
                driven_speed = normalized_data.get("Driven_Wheel_Speed", 0)
                
                # Get best available speed source (priority: KF Speed > GPS Speed > Vehicle Speed)
                kf_speed = normalized_data.get("KF_Speed", 0.0)
                if kf_speed > 0:
                    actual_speed = kf_speed
                else:
                    gps_speed = normalized_data.get("GPS_Speed", 0.0)
                    if gps_speed > 0:
                        actual_speed = gps_speed
                    else:
                        actual_speed = normalized_data.get("Vehicle_Speed", normalized_data.get("Speed", 0.0))
                
                # Calculate wheel slip
                if driveshaft_rpm > 0 and actual_speed > 0:
                    # Use driveshaft RPM for driven wheel speed calculation
                    reading = self.wheel_slip_service.update_from_driveshaft(
                        driveshaft_rpm=driveshaft_rpm,
                        actual_vehicle_speed=actual_speed,
                        gear_ratio=1.0,  # Assume post-transmission measurement
                    )
                elif driven_speed > 0 and actual_speed > 0:
                    # Use direct driven wheel speed
                    reading = self.wheel_slip_service.update(
                        driven_wheel_speed=driven_speed,
                        actual_vehicle_speed=actual_speed,
                    )
                else:
                    # Estimate slip from RPM and speed (simplified)
                    rpm = normalized_data.get("RPM", normalized_data.get("Engine_RPM", 0))
                    if rpm > 500 and actual_speed > 5:
                        # Simple estimation: compare expected speed from RPM to actual
                        # This is a rough approximation for demo/estimation purposes
                        # Assume some gear/final drive combo gives ~3500 RPM at 60 mph
                        estimated_driven = (rpm / 3500.0) * 60.0
                        reading = self.wheel_slip_service.update(
                            driven_wheel_speed=estimated_driven,
                            actual_vehicle_speed=actual_speed,
                        )
                    else:
                        reading = None
                
                # Update UI if we have a reading
                if reading:
                    status_text = reading.status.value.upper()
                    rec = ""
                    if reading.status.value in ("excessive", "critical"):
                        rec = "Reduce throttle to optimize traction!"
                    elif reading.status.value == "low":
                        rec = "Room for more throttle"
                    
                    self.wheel_slip_panel.update_slip(
                        reading.slip_percentage,
                        status_text,
                        rec,
                    )
            except Exception as e:
                LOGGER.debug("Error updating wheel slip (non-critical): %s", e)

        health_payload = self._update_health(data)

        if mode != "replay":
            self.logger.log(data)
            # Update logging health monitor
            self.logging_health_monitor.update_log_timestamp()
            payload = {"timestamp": time.time(), **data}
            self.cloud_sync.upload(payload)
            self._poll_gps(mode)

        if self.conversational_agent:
            self.conversational_agent.update_context(telemetry=data, health=health_payload)

        sample = self._normalized_sample(data)
        if len(sample) == len(self._predictor_aliases):
            insight = None
            try:
                insight = self.predictor.update(sample)
            except Exception as error:
                LOGGER.debug("Predictive fault detector skipped: %s", error)
            if insight:
                message = f"[AI Warning] {insight}"
                self.ai_panel.update_insight(message, level="warning")
                self._speak(message, channel="warning", throttle=20)

        suggestions = self.advisor.evaluate(data)
        for suggestion in suggestions:
            tip = f"[Tuning Tip] {suggestion}"
            self.ai_panel.update_insight(tip, level="success")
            self._speak(suggestion, channel="tip", throttle=45)

        # Fuel/Additive Management (Nitrous, Nitro, Methanol, E85)
        if self.fuel_additive_manager:
            from services.voice_feedback import FeedbackPriority
            fuel_recs = self.fuel_additive_manager.analyze_and_advise(data)
            for rec in fuel_recs:
                if rec.safety_critical:
                    level = "error"
                    throttle = 5  # Immediate announcement
                elif rec.priority in [FeedbackPriority.HIGH, FeedbackPriority.CRITICAL]:
                    level = "warning"
                    throttle = 10
                else:
                    level = "success"
                    throttle = 30
                
                icon = "🔥" if rec.additive_type.value in ["nitrous_oxide", "nitromethane"] else "💧" if rec.additive_type.value == "methanol" else "⛽"
                message = f"{icon} [{rec.additive_type.value.upper()}] {rec.message}"
                self.ai_panel.update_insight(message, level=level)
                if rec.priority in [FeedbackPriority.HIGH, FeedbackPriority.CRITICAL]:
                    self._speak(rec.message, channel="warning" if rec.safety_critical else "tip", throttle=throttle)

        # Store latest sample (thread-safe)
        with self._data_lock:
            self._latest_sample = data
        self._update_performance()
        self._detect_and_analyze_run(data, health_payload)

    def _check_logging_health(self) -> None:
        """Check logging health status."""
        if self.logging_health_monitor:
            health = self.logging_health_monitor.check_health()
            # Update status bar with logging status
            if self.status_bar:
                status_msg = self.logging_health_monitor.get_status_message()
                self.status_bar.update_status(status_msg)

    def _on_logging_status_change(self, health) -> None:
        """Handle logging status changes."""
        status_msg = self.logging_health_monitor.get_status_message()
        color = self.logging_health_monitor.get_status_color()

        # Update AI panel with status
        if health.status.value == "stopped":
            self.ai_panel.update_insight(f"[LOGGING] {status_msg}", level="error")
        elif health.status.value == "storage_full":
            self.ai_panel.update_insight(f"[STORAGE] {status_msg}", level="error")
        elif health.status.value == "storage_error":
            self.ai_panel.update_insight(f"[STORAGE] {status_msg}", level="error")
        elif health.status.value == "active":
            if health.storage_usage_percent >= 90:
                self.ai_panel.update_insight(f"[STORAGE] {status_msg}", level="warning")
            else:
                self.ai_panel.update_insight(f"[LOGGING] {status_msg}", level="success")

    def _voice_alert_logging(self, message: str) -> None:
        """Voice alert for logging issues."""
        if self.voice_output:
            self.voice_output.speak(message)
        if self.voice_feedback:
            from services.voice_feedback import FeedbackPriority

            self.voice_feedback.announce(message, priority=FeedbackPriority.HIGH, channel="logging")

    def detect_can_vendor(self) -> Optional[str]:
        """Detect CAN bus vendor."""
        try:
            from services.can_vendor_detector import CANVendorDetector

            if not self.can_vendor_detector:
                self.can_vendor_detector = CANVendorDetector(can_channel="can0", bitrate=500000)

            vendor = self.can_vendor_detector.detect_vendor(sample_time=5.0)
            if vendor:
                self.detected_vendor = vendor.value
                # Load DBC file
                self.can_vendor_detector.load_dbc()
                # Update logging health monitor with vendor info
                if self.logging_health_monitor and self.logging_health_monitor.current_health:
                    self.logging_health_monitor.current_health.vendor = self.detected_vendor
                self.ai_panel.update_insight(f"[CAN] Detected vendor: {self.detected_vendor}", level="success")
                return self.detected_vendor
        except Exception as e:
            LOGGER.error("Error detecting CAN vendor: %s", e)
        return None

    def _detect_and_analyze_run(self, data: Dict[str, float], health_payload: Dict) -> None:
        """Detect when a run/pass completes and analyze it."""
        speed = self._speed_from_data(data) or 0.0
        with self._data_lock:
            state = self._run_detection_state
        
        # Detect run start (speed increases from low to high)
        if not state["in_run"] and speed > 30 and state["last_speed"] < 20:
            # Run started
            state["in_run"] = True
            state["run_start_time"] = time.time()
            state["run_start_speed"] = speed
            state["run_number"] += 1
            state["run_metrics"] = {}
            state["run_max_speed"] = speed
            LOGGER.info("Run %d started", state["run_number"])
        
        # Track run metrics while in run
        if state["in_run"]:
            state["run_max_speed"] = max(state["run_max_speed"], speed)
            # Collect key metrics during run
            for key in ["Engine_RPM", "Boost_Pressure", "Coolant_Temp", "Lambda", "Throttle_Position"]:
                if key in data:
                    if key not in state["run_metrics"]:
                        state["run_metrics"][key] = []
                    state["run_metrics"][key].append(data[key])
        
        # Detect run end (speed decreases from high to low, or stopped)
        if state["in_run"] and speed < 10 and state["last_speed"] > 30:
            # Run completed
            run_duration = time.time() - (state["run_start_time"] or time.time())
            
            # Calculate average metrics for the run
            avg_metrics = {}
            for key, values in state["run_metrics"].items():
                if values:
                    avg_metrics[key] = sum(values) / len(values)
            
            # Get performance snapshot
            snapshot = self.performance_tracker.snapshot()
            run_time = None
            if snapshot:
                # Try to get lap time or 0-60 time
                run_time = snapshot.metrics.get("lap_time") or snapshot.metrics.get("0-60 mph")
                avg_metrics.update(snapshot.metrics)
            
            # Get health score
            health_score = health_payload.get("score", 85.0) if health_payload else 85.0
            
            # Get best metrics
            best_metrics = snapshot.best_metrics if snapshot else {}
            if run_time:
                best_metrics["lap_time"] = run_time
            
            # Analyze the run
            previous_runs = self.intelligent_advisor.run_history[-5:] if len(self.intelligent_advisor.run_history) > 0 else None
            analysis = self.intelligent_advisor.analyze_run(
                run_number=state["run_number"],
                run_time=run_time or run_duration,
                metrics=avg_metrics,
                best_metrics=best_metrics,
                health_score=health_score,
                previous_runs=previous_runs,
            )
            
            # Display advice
            if analysis.advice:
                # Update AI panel with top advice
                top_advice = sorted(analysis.advice, key=lambda a: (a.priority.value, -a.confidence), reverse=True)[:3]
                for advice in top_advice:
                    priority_icon = "🔴" if advice.priority == AdvicePriority.CRITICAL else "🟠" if advice.priority == AdvicePriority.HIGH else "🟡"
                    message = f"{priority_icon} {advice.title}: {advice.suggested_action}"
                    self.ai_panel.update_insight(message, level="warning" if advice.priority in [AdvicePriority.CRITICAL, AdvicePriority.HIGH] else "success")
                
                # Voice announcement for critical advice
                critical_advice = [a for a in analysis.advice if a.priority == AdvicePriority.CRITICAL]
                if critical_advice:
                    self._speak(f"Critical: {critical_advice[0].title}. {critical_advice[0].suggested_action}", channel="warning", throttle=10)
            
            # Update advice panel if available
            if self.advice_panel:
                self.advice_panel.display_advice(analysis.advice)
            
            # Reset run state
            state["in_run"] = False
            state["run_start_time"] = None
            state["run_metrics"] = {}
            state["run_max_speed"] = 0.0
            
            LOGGER.info("Run %d completed. Generated %d pieces of advice", state["run_number"], len(analysis.advice))
        
        # Update last_speed thread-safely
        with self._data_lock:
            state["last_speed"] = speed

    def _get_current_telemetry(self) -> dict:
        """Get current telemetry data for camera frame synchronization."""
        with self._data_lock:
            telemetry = dict(self._latest_sample) if self._latest_sample else {}
        # Add GPS data if available
        if self.gps_interface:
            try:
                fix = self.gps_interface.read_fix()
                if fix:
                    telemetry.update({
                        "gps_lat": fix.latitude,
                        "gps_lon": fix.longitude,
                        "gps_speed": fix.speed_mps,
                        "gps_heading": fix.heading,
                    })
            except Exception:
                pass
        # Add performance metrics
        snapshot = self.performance_tracker.snapshot()
        if snapshot:
            telemetry.update(snapshot.metrics)
        return telemetry


def start_data_stream(window: QObject, **settings) -> DataStreamController:
    """Start data stream with optional GPS interface setup for demo mode."""
    import os
    
    # In demo/simulated mode, create SimulatedGPSInterface if GPS not available
    gps_interface = getattr(window, "gps_interface", None)
    if not gps_interface and (settings.get("source") == "simulated" or os.environ.get("AITUNER_DEMO_MODE") == "true"):
        try:
            from interfaces.simulated_interface import SimulatedGPSInterface
            from services.data_simulator import DataSimulator
            
            # Get or create simulator
            simulator = None
            if hasattr(window, "demo_controller") and hasattr(window.demo_controller, "simulator"):
                simulator = window.demo_controller.simulator
            else:
                # Create a temporary simulator for GPS
                simulator = DataSimulator(mode="demo")
            
            gps_interface = SimulatedGPSInterface(simulator)
            LOGGER.info("Using SimulatedGPSInterface for demo mode (simulator=%s)", type(simulator).__name__)
            # Store on window so it persists
            window.gps_interface = gps_interface
            # Test that GPS data can be read
            test_fix = gps_interface.read_fix()
            if test_fix:
                LOGGER.info("SimulatedGPSInterface test read successful: Lat=%.5f, Lon=%.5f, Speed=%.1f m/s", 
                           test_fix.latitude, test_fix.longitude, test_fix.speed_mps)
            else:
                LOGGER.warning("SimulatedGPSInterface test read returned None")
        except Exception as e:
            LOGGER.warning("Could not create SimulatedGPSInterface: %s", e, exc_info=True)
    controller: Optional[DataStreamController] = getattr(window, "data_stream_controller", None)
    if not controller:
        controller = DataStreamController(
            telemetry_panel=window.telemetry_panel,
            ai_panel=window.ai_panel,
            predictor=getattr(window, "fault_predictor", None),
            health_widget=getattr(window, "health_widget", None),
            dragy_view=getattr(window, "dragy_view", None),
            gauge_panel=getattr(window, "gauge_panel", None),
            advisor=getattr(window, "tuning_advisor", None),
            advice_panel=getattr(window, "advice_panel", None),
            logger=getattr(window, "data_logger", None),
            cloud_sync=getattr(window, "cloud_sync", None),
            status_bar=getattr(window, "status_bar", None),
            gps_interface=gps_interface,
            performance_tracker=getattr(window, "performance_tracker", None),
            geo_logger=getattr(window, "geo_logger", None),
            voice_output=getattr(window, "voice_output", None),
            conversational_agent=getattr(window, "conversational_agent", None),
            connectivity_manager=getattr(window, "connectivity_manager", None),
            camera_manager=getattr(window, "camera_manager", None),
            voice_feedback=getattr(window, "voice_feedback", None),
            wheel_slip_panel=getattr(window, "wheel_slip_panel", None),
            parent=window,
        )
        # Store reference to GPS track panel if it exists
        if hasattr(window, "gps_track_panel"):
            controller._gps_track_panel = window.gps_track_panel
        window.data_stream_controller = controller
        
        # Connect telemetry sync to camera manager
        if controller.camera_manager:
            controller.camera_manager.set_telemetry_sync(controller._get_current_telemetry)
            LOGGER.info("Telemetry sync connected to camera manager")
    else:
        controller.stop()

    if settings:
        controller.configure(**settings)
    controller.start()
    return controller


__all__ = [
    "DataStreamController",
    "StreamSettings",
    "start_data_stream",
]

