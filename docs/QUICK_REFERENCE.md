# AI Tuner Agent - Quick Reference

## Starting the Application

```bash
# Main UI
python start_ai_tuner.py

# With diagnostics
python start_ai_tuner.py --diagnostics

# Dragy mode only
python -m ui.dragy_main
```

## System Diagnostics

```bash
# Run full system diagnostics
python tools/system_diagnostics.py

# Validate configuration
python -c "from core.config_validator import ConfigValidator; ConfigValidator.print_validation_report(ConfigValidator.validate_all())"
```

## CAN Bus Setup (reTerminal DM)

```bash
# Run automated setup
sudo python tools/setup_can_reterminal.py

# Manual setup
sudo ip link set can0 up type can bitrate 500000
sudo ip link set can1 up type can bitrate 500000

# Test CAN
candump can0
cansend can0 123#DEADBEEF
```

## Common Commands

### Voice Commands
- "Start session"
- "Stop session"
- "Read fault codes"
- "How's coolant temperature?"
- "What's the engine health?"
- "Where is the car?"
- "Switch to OBD" / "Switch to RaceCapture"
- "Replay log"

### File Locations
- **Logs**: `logs/` directory
- **Video Logs**: `video_logs/` directory
- **Models**: `models/` directory
- **Configuration**: `config.py`

## Troubleshooting

### CAN Not Working
```bash
# Check interfaces
ip link show can0

# Check if up
ip -details link show can0

# Bring up manually
sudo ip link set can0 up type can bitrate 500000
```

### GPS Not Working
```bash
# Check serial devices
ls /dev/ttyUSB* /dev/ttyACM*

# Test GPS
python -c "from interfaces.gps_interface import GPSInterface; gps = GPSInterface(); print(gps.read_fix())"
```

### Camera Not Working
```bash
# List cameras
ls /dev/video*
v4l2-ctl --list-devices

# Test camera
ffplay /dev/video0
```

### Performance Issues
```bash
# Check system resources
python -c "from services.performance_monitor import PerformanceMonitor; pm = PerformanceMonitor(); print(pm.collect_system_metrics())"

# Check disk space
df -h

# Check temperature
vcgencmd measure_temp
```

## Configuration

### Environment Variables
```bash
# Override CAN channel
export CAN_CHANNEL="can1"

# Override CAN bitrate
export CAN_BITRATE="1000000"

# Set hardware platform
export HARDWARE_PLATFORM="reTerminal DM"

# Enable debug mode
export DEBUG_MODE="true"
```

### Settings Dialog
- Access via "Settings" button in main UI
- Configure data source (OBD-II, RaceCapture, Auto)
- Set port and baud rate
- Adjust poll interval

## Features

### Data Sources
- **OBD-II**: Standard OBD-II adapters
- **RaceCapture**: Autosport Labs RaceCapture
- **Auto**: Automatic detection

### Performance Tracking
- 0-60 mph times
- 1/8 mile times
- 1/4 mile times
- GPS lap tracking
- Best times tracking

### AI Features
- Predictive fault detection
- Health scoring
- Tuning advisor
- Conversational agent
- Voice control

### Logging
- CSV telemetry logs
- Video logs with telemetry sync
- GPS trace logs
- Cloud sync (optional)

## Hardware Support

### Supported Platforms
- **reTerminal DM**: Full support with dual CAN
- **Raspberry Pi**: Standard support
- **Jetson Nano**: Standard support
- **Generic Linux**: Basic support

### Required Hardware
- CAN interface (onboard or USB-CAN adapter)
- GPS module (USB/serial)
- Optional: USB/WiFi cameras
- Optional: Microphone for voice control

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-qt

# Run tests
pytest
```

### Code Structure
```
AI-TUNER-AGENT/
├── ai/              # AI modules (fault detection, tuning advisor)
├── interfaces/      # Hardware interfaces (CAN, GPS, OBD, cameras)
├── services/        # Services (logging, cloud sync, video)
├── controllers/     # Controllers (data stream, voice, dragy)
├── ui/              # UI components
├── core/             # Core utilities (hardware detection, error recovery)
├── tools/            # Utility scripts
└── docs/             # Documentation
```

## Support

For issues or questions:
1. Check system diagnostics: `python tools/system_diagnostics.py`
2. Review logs: `ai_tuner.log`
3. Check configuration: `python -c "from core.config_validator import ConfigValidator; ConfigValidator.print_validation_report(ConfigValidator.validate_all())"`

