# Waveshare GPS HAT Setup Guide

## Overview

This guide covers the setup and integration of Waveshare GPS HAT modules for Raspberry Pi 5. The GPS HAT provides location tracking, speed measurement, and route logging capabilities for the AI Tuner application.

## Supported Hardware

- **Waveshare L76K GPS Module**
- **Waveshare MAX-7Q GPS Module**
- **Generic NMEA GPS modules via UART**

## Hardware Setup

### 1. Physical Installation

1. **Attach the GPS HAT** to the Raspberry Pi 5's 40-pin GPIO header
2. **Connect the GPS antenna** to the module
3. **Position the antenna** with a clear view of the sky for best satellite reception

### 2. Enable UART Interface

The GPS HAT communicates via UART. Enable it on Raspberry Pi:

```bash
sudo raspi-config
```

Navigate to:
- **Interfacing Options** > **Serial**
- Select **No** to disable login shell over serial
- Select **Yes** to enable the hardware serial port

Reboot:
```bash
sudo reboot
```

### 3. Verify UART Device

After reboot, check for UART devices:

```bash
ls -l /dev/ttyAMA*
ls -l /dev/serial*
```

Common ports:
- `/dev/ttyAMA0` - Primary UART on Pi
- `/dev/ttyAMA1` - Secondary UART on Pi 5
- `/dev/serial0` - Alias for primary UART
- `/dev/serial1` - Alias for secondary UART

## Software Setup

### 1. Install Dependencies

```bash
pip install pyserial pynmea2
```

### 2. Test GPS Connection

Use the detection script:

```bash
python tools/detect_waveshare_gps.py
```

Or test manually with minicom:

```bash
sudo apt-get install minicom
sudo minicom -D /dev/ttyAMA0 -b 9600
```

You should see NMEA sentences like:
```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
```

## Integration

### Automatic Detection

The GPS HAT is automatically detected and integrated when the application starts. The system will:

1. **Auto-detect** the GPS port
2. **Try hardware connection** first
3. **Fall back to simulator** if hardware not available

### Manual Configuration

You can manually configure the GPS HAT:

```python
from interfaces.waveshare_gps_hat import get_gps_hat

# Auto-detect port
gps = get_gps_hat(auto_detect=True)

# Specify port manually
gps = get_gps_hat(port="/dev/ttyAMA0", baudrate=9600)

# Use simulator
gps = get_gps_hat(use_simulator=True)
```

### Environment Variables

Control GPS behavior with environment variables:

```bash
# Use simulator mode
export AITUNER_USE_GPS_SIMULATOR=true

# Use specific port (if auto-detect fails)
export GPS_PORT=/dev/ttyAMA0
```

## Usage

### Reading GPS Data

```python
from interfaces.waveshare_gps_hat import get_gps_hat

gps = get_gps_hat()
gps.connect()

fix = gps.read_fix()
if fix:
    print(f"Latitude: {fix.latitude}")
    print(f"Longitude: {fix.longitude}")
    print(f"Speed: {fix.speed_mps} m/s")
    print(f"Heading: {fix.heading}°")
    print(f"Altitude: {fix.altitude_m} m")
    print(f"Satellites: {fix.satellites}")
```

### Integration with Data Stream Controller

The GPS HAT is automatically integrated into the data stream controller. GPS data is:

- **Read automatically** during telemetry polling
- **Added to normalized data** for telemetry panel
- **Used for lap timing** and track mapping
- **Logged for route tracking**

## Troubleshooting

### GPS Not Detected

1. **Check UART is enabled:**
   ```bash
   sudo raspi-config
   # Interfacing Options > Serial > Enable
   ```

2. **Check device exists:**
   ```bash
   ls -l /dev/ttyAMA*
   ```

3. **Check permissions:**
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

### No GPS Data Received

1. **Wait for satellite acquisition** (30-60 seconds)
2. **Check antenna connection**
3. **Ensure clear view of sky**
4. **Try different baud rates** (9600 or 115200)

### Wrong Port

If auto-detection fails, specify the port manually:

```python
gps = get_gps_hat(port="/dev/ttyAMA0", baudrate=9600)
```

## Testing

Run the test script:

```bash
python tools/test_waveshare_gps.py
```

This will test:
- Import and initialization
- Simulator mode
- Hardware detection
- Integration with data stream controller

## Features

- ✅ **Automatic port detection**
- ✅ **Hardware and simulator modes**
- ✅ **NMEA sentence parsing**
- ✅ **GPS fix data (lat, lon, speed, heading, altitude)**
- ✅ **Satellite count and position quality**
- ✅ **Integration with data stream controller**
- ✅ **Fallback to simulator if hardware unavailable**

## API Reference

### WaveshareGPSHAT

```python
class WaveshareGPSHAT:
    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 9600,
        timeout: float = 0.3,
        use_simulator: bool = False,
        auto_detect: bool = True,
    )
    
    def connect() -> bool
    def disconnect() -> None
    def is_connected() -> bool
    def read_fix() -> Optional[GPSFix]
    def get_status() -> Dict[str, Any]
```

### get_gps_hat()

```python
def get_gps_hat(
    port: Optional[str] = None,
    baudrate: int = 9600,
    use_simulator: bool = False,
    auto_detect: bool = True,
) -> WaveshareGPSHAT
```

Returns a global GPS HAT instance (singleton pattern).

## Next Steps

- Configure GPS for lap timing
- Set up route logging
- Enable theft tracking with GPS
- Integrate with track mapping features

