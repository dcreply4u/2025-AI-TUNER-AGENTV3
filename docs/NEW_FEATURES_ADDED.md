# New Features Added

## 🚀 Latest Enhancements (TelemetryIQ 2025.11)

### 1. **Advanced Virtual Dyno Logger** ✅
- **Files**: `services/virtual_dyno.py`, `ui/dyno_tab.py`, `ui/dyno_view.py`, `docs/DYNO_ENHANCEMENTS_SUMMARY.md`
- **Highlights**:
  - Start/Stop logging buttons with live HP preview (20 Hz capture)
  - Savitzky–Golay smoothing + `np.gradient` acceleration batch processor
  - Torque overlays derived from HP/RPM, live during capture
  - Enhanced air-density model (temperature + altitude + humidity + barometric pressure)
  - Run summary dialog (peak HP/TQ, RPM, data-point count)
  - Session manager with automatic run names (`Run_1`, `Run_2`, …) and combined CSV export

### 2. **Windows Laptop Edition + Installer** ✅
- **Files**: `interfaces/windows_hardware_adapter.py`, `core/hardware_platform.py`, `setup_windows.bat`, `installer/windows_installer.iss`, `docs/WINDOWS_*.md`
- **Highlights**:
  - Hardware abstraction for Arduino/USB GPIO/CAN adapters on Windows
  - Platform auto-detection and driver hints inside `HardwarePlatform`
  - Inno Setup installer + batch bootstrap to provision Python, drivers, and requirements
  - Documentation covering laptop SKUs, pricing tiers, and deployment flow

### 3. **Methanol Control Suite** ✅
- **Files**: `ui/ecu_tuning_main.py`, `docs/METHANOL_MODULE.md`
- **Highlights**:
  - Street/Race/Kill mode switching with automatic timing/fuel adjustments
  - Real-time diagnostics indicator, failsafe banners, and sensor-driven fault logging
  - Dynamic RPM/load duty maps, environmental compensation, and custom tabs for diagnostics/data logging
  - CSV export of methanol session logs plus boost/coolant gauges for live monitoring

### 3. **TelemetryIQ Mobile Stack (Flutter + PWA + FastAPI)** ✅
- **Files**: `api/mobile_api_server.py`, `api/mobile_api_integration.py`, `mobile_apps/flutter_telemetryiq_mobile/`, `mobile_apps/pwa_telemetryiq_mobile/`
- **Highlights**:
  - FastAPI REST + WebSocket gateway with JWT-ready scaffolding
  - Flutter TelemetryIQ Mobile (matching desktop UI, real-time telemetry, AI advisor, config sync)
  - PWA TelemetryIQ Mobile (offline-ready, service worker, same theme/components)
  - Mobile API quick-start + runtime docs for third-party integrators

### 4. **Advanced Tuning Logic Engine** ✅
- **Files**: `services/advanced_tuning_engine.py`, `services/closed_loop_tuning.py`, `docs/ADVANCED_TUNING_LOGIC.md`
- **Highlights**:
  - Multi-objective optimization (Performance, Efficiency, Balanced, Safety modes)
  - Predictive ML models (Gradient Boosting, Random Forest) for HP/efficiency/safety prediction
  - Reinforcement learning concepts (Q-learning) for learning optimal actions
  - Closed-loop PID control for real-time lambda and timing adjustments
  - Safety validation with interlocks and threshold-based filtering
  - Continuous learning from historical tuning results

### 5. **Desktop UX & Stability Upgrades** ✅
- Multi-row tab widget with consistent sizing for 30+ modules
- Main window sizing/maximize fixes with safe clamping and screen-awareness
- Console log viewer, debug tooling docs, and dyno-tab safety guards

## 🕰 Earlier Additions (Still Available)

### 1. **Anti-Lag Control System** ✅
- **File**: `controllers/racing_controls.py`
- **Features**:
  - Configurable anti-lag modes (OFF, SOFT, AGGRESSIVE, AUTO)
  - RPM-based activation (configurable min/max RPM)
  - Boost target control
  - Safety limits (max RPM, max EGT)
  - CAN message integration for ECU control
  - Real-time monitoring and warnings

### 2. **Launch Control System** ✅
- **File**: `controllers/racing_controls.py`
- **Features**:
  - RPM limiter with configurable launch RPM
  - Transbrake detection and requirement
  - Launch timer with maximum duration
  - Speed-based auto-disable
  - Multiple modes (RPM_LIMIT, TRACTION, AUTO)
  - CAN message integration for ECU control

### 3. **Lap Detection Service** ✅
- **File**: `services/lap_detector.py`
- **Features**:
  - Automatic lap detection via GPS start/finish line
  - Configurable detection radius
  - Sector time tracking (configurable number of sectors)
  - Lap statistics (duration, max speed, avg speed, distance)
  - Best lap tracking
  - Track point recording for visualization

### 4. **Telemetry Overlay on Video** ✅
- **File**: `services/video_overlay.py`
- **Features**:
  - Real-time telemetry rendering on video frames
  - Configurable overlay position (top, bottom, corners)
  - Customizable fonts, colors, and transparency
  - Multiple telemetry fields (RPM, speed, boost, lambda, temps, etc.)
  - Custom field support
  - Background with transparency

### 5. **Camera Interface** ✅
- **File**: `interfaces/camera_interface.py`
- **Features**:
  - Support for USB cameras (UVC)
  - RTSP/HTTP stream support (WiFi cameras)
  - CSI camera support (Raspberry Pi)
  - Multi-camera management
  - Frame callback system
  - Telemetry synchronization
  - Health monitoring

### 6. **Video Logging Service** ✅
- **File**: `services/video_logger.py`
- **Features**:
  - Multi-camera video recording
  - Telemetry synchronization with video
  - Session management
  - Metadata storage (JSON)
  - Disk usage monitoring
  - Automatic cleanup of old sessions

## 📋 Integration Notes

### Racing Controls Integration
To use anti-lag and launch control:

```python
from controllers.racing_controls import RacingControls, AntiLagMode, LaunchControlMode

# Initialize with CAN sender function
def send_can(arb_id, data):
    # Your CAN sending logic
    pass

controls = RacingControls(can_sender=send_can, telemetry_callback=get_telemetry)
controls.start()

# Enable anti-lag
controls.set_anti_lag(True, mode=AntiLagMode.AGGRESSIVE)

# Enable launch control
controls.set_launch_control(True, launch_rpm=4000, mode=LaunchControlMode.RPM_LIMIT)
```

### Lap Detection Integration
To use lap detection:

```python
from services.lap_detector import LapDetector

# Initialize with start/finish line coordinates
detector = LapDetector(
    start_finish_lat=37.7749,
    start_finish_lon=-122.4194,
    detection_radius=50.0,  # meters
    min_lap_time=30.0,  # seconds
    sector_count=3
)

# Update with GPS data
completed_lap = detector.update(lat, lon, speed, timestamp)
if completed_lap:
    print(f"Lap {completed_lap.lap_number}: {completed_lap.duration:.2f}s")

# Get best lap
best = detector.get_best_lap()
```

### Video Overlay Integration
To add telemetry overlay to video:

```python
from services.video_overlay import VideoOverlay, OverlayConfig
from interfaces.camera_interface import Frame

# Configure overlay
config = OverlayConfig(
    position="bottom",
    show_rpm=True,
    show_speed=True,
    show_boost=True,
    font_color=(0, 255, 0),  # Green
    bg_alpha=0.7
)

overlay = VideoOverlay(config)

# Render overlay on frame
frame_with_overlay = overlay.render(frame, telemetry_data)
```

## 🔗 Next Steps for Full Integration

1. **Integrate racing controls into main UI**:
   - Add anti-lag toggle button
   - Add launch control settings dialog
   - Display racing control status

2. **Integrate lap detection into data stream controller**:
   - Auto-detect start/finish line from GPS track
   - Display lap times in Dragy view
   - Log lap data to CSV/JSON

3. **Integrate video overlay into video logger**:
   - Render overlay during recording
   - Option to export with/without overlay
   - Real-time preview with overlay

4. **Add session management**:
   - Named sessions with metadata
   - Session comparison tools
   - Export/import sessions

5. **Add data export tools**:
   - JSON export with full metadata
   - Video-telemetry sync export
   - Comparison tools for multiple runs

## 📝 Configuration Examples

### Anti-Lag Configuration
```python
from controllers.racing_controls import AntiLagConfig, AntiLagMode

config = AntiLagConfig(
    enabled=True,
    mode=AntiLagMode.AGGRESSIVE,
    min_rpm=2000,
    max_rpm=4000,
    boost_target=15.0,  # PSI
    safety_max_rpm=5000,
    safety_max_egt=1650.0,  # Fahrenheit
    activation_delay=0.5
)
```

### Launch Control Configuration
```python
from controllers.racing_controls import LaunchControlConfig, LaunchControlMode

config = LaunchControlConfig(
    enabled=True,
    mode=LaunchControlMode.RPM_LIMIT,
    launch_rpm=4000,
    rpm_tolerance=200,
    max_launch_time=5.0,  # seconds
    min_speed=5.0,  # mph
    transbrake_required=True
)
```

## ⚠️ Important Notes

1. **CAN Message Format**: The racing controls use example CAN message formats. You'll need to adjust the `arb_id` and data format to match your specific ECU protocol.

2. **GPS Accuracy**: Lap detection accuracy depends on GPS precision. Consider using a high-precision GPS module for best results.

3. **Video Performance**: Video overlay rendering adds processing overhead. Consider reducing frame rate or resolution if performance is an issue.

4. **Safety**: Anti-lag and launch control can be dangerous if misconfigured. Always test in a safe environment and set appropriate safety limits.

