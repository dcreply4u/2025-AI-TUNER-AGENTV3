from __future__ import annotations

"""\
=========================================================
Data Stream Controller – conductor for sensor symphonies
=========================================================
"""

import csv
import logging
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
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.telemetry_panel = telemetry_panel
        self.ai_panel = ai_panel
        self.gauge_panel = gauge_panel
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
            
            # Temperature provider (from weather API or sensors)
            def temperature_provider() -> Optional[float]:
                # Try to get from weather API
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
            
            # Pressure provider (from weather API or sensors)
            def pressure_provider() -> Optional[float]:
                # Try to get from weather API
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
            
            # Humidity provider (from weather API or sensors)
            def humidity_provider() -> Optional[float]:
                # Try to get from weather API
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

        # Set up telemetry sync for cameras
        if self.camera_manager:
            self.camera_manager.set_telemetry_sync(self._get_current_telemetry)

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
        if self.gps_interface:
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
        print(f"[DATA STREAM] Started: source={self.settings.source}, interval={interval_ms}ms, active={self.timer.isActive()}")
        
        # Force first poll immediately to get data flowing
        QTimer.singleShot(100, self._on_poll)
        print("[DATA STREAM] First poll scheduled in 100ms")

    def stop(self) -> None:
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
            self.can_vendor_detector.close()

    def _prepare_replay(self) -> None:
        if not self.settings.replay_file:
            raise ValueError("Replay mode enabled without a log file.")
        path = Path(self.settings.replay_file).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Replay log not found: {path}")
        with path.open("r", newline="") as handle:
            reader = csv.DictReader(handle)
            self._replay_buffer = list(reader)
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
            speed_mph = self._speed_from_data(self._latest_sample or {}) or 0.0
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
                
                industry_updates = self.industry_integration.update_telemetry(
                    telemetry=self._latest_sample,
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
        
        # Store latest sample for other methods
        self._latest_sample = data
        
        # Normalize data keys for telemetry panel
        normalized_data = {}
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
        }

        for canonical, keys in aliases.items():
            for key in keys:
                if key in data:
                    normalized_data[canonical] = float(data[key])
                    break

        # Keep originals for other consumers
        for key, value in data.items():
            normalized_data.setdefault(key, float(value))
        
        # Update telemetry panel with normalized data
        if self.telemetry_panel:
            self.telemetry_panel.update_data(normalized_data)
            # Print first few updates for verification
            if not hasattr(self, '_update_count'):
                self._update_count = 0
            self._update_count += 1
            if self._update_count <= 5:
                rpm = normalized_data.get('RPM', normalized_data.get('Engine_RPM', 0))
                speed = normalized_data.get('Speed', normalized_data.get('Vehicle_Speed', 0))
                print(f"[DATA FLOW] Update #{self._update_count}: {len(normalized_data)} values, RPM={rpm:.0f}, Speed={speed:.0f}")
            LOGGER.debug(f"Updated telemetry panel with {len(normalized_data)} values")
        
        # Update gauge panel with normalized data
        if self.gauge_panel:
            self.gauge_panel.update_data(normalized_data)

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
        
        state["last_speed"] = speed

    def _get_current_telemetry(self) -> dict:
        """Get current telemetry data for camera frame synchronization."""
        telemetry = dict(self._latest_sample)
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
            gps_interface=getattr(window, "gps_interface", None),
            performance_tracker=getattr(window, "performance_tracker", None),
            geo_logger=getattr(window, "geo_logger", None),
            voice_output=getattr(window, "voice_output", None),
            conversational_agent=getattr(window, "conversational_agent", None),
            connectivity_manager=getattr(window, "connectivity_manager", None),
            camera_manager=getattr(window, "camera_manager", None),
            voice_feedback=getattr(window, "voice_feedback", None),
            parent=window,
        )
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

