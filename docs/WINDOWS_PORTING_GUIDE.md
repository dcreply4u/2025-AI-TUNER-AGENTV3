# Windows Porting Guide

## Overview

This guide explains how the TelemetryIQ codebase has been ported to run on Windows with affordable hardware adapters.

## Porting Strategy

### 1. Python is Cross-Platform

**Good News:** Most of the code already works on Windows! Python is cross-platform, so:
- ✅ All Python code runs on Windows
- ✅ Most libraries work on Windows
- ✅ Path handling uses `pathlib` (cross-platform)

### 2. Platform-Specific Code

The codebase uses platform detection to handle differences:

```python
import platform

if platform.system() == "Windows":
    # Windows-specific code
elif platform.system() == "Linux":
    # Linux-specific code
```

### 3. Hardware Interface Abstraction

Instead of direct GPIO access (Linux-only), Windows uses:
- **USB GPIO Adapters** (FTDI, CH340)
- **Arduino via Serial** (USB connection)
- **USB-CAN Adapters** (for ECU communication)
- **OBD-II Adapters** (for standard vehicles)

## Changes Made

### 1. Hardware Platform Detection

**File:** `core/hardware_platform.py`

Added Windows detection:
```python
if platform.system() == "Windows":
    return HardwareDetector._windows_config()
```

Windows config:
- No native GPIO (uses USB adapters)
- No native CAN (uses USB-CAN adapters)
- USB serial for Arduino communication

### 2. Windows Hardware Adapter

**File:** `interfaces/windows_hardware_adapter.py` (NEW)

Provides Windows-compatible hardware interfaces:
- Arduino detection and communication
- USB GPIO adapter support
- Serial port management
- USB device detection

### 3. Digital Sensor Interface

**File:** `interfaces/digital_sensor.py`

Updated to support Windows:
```python
if platform.system() == "Windows" and WINDOWS_ADAPTER:
    self._init_windows_gpio()
```

### 4. Path Handling

Already cross-platform using `pathlib.Path`:
```python
from pathlib import Path
config_file = Path("config") / "settings.json"  # Works on Windows and Linux
```

## What Works on Windows

### ✅ Already Works

1. **Core Application**
   - All Python code
   - GUI (PySide6 works on Windows)
   - Data processing
   - AI features
   - Configuration management

2. **Communication**
   - OBD-II (via python-OBD)
   - Serial communication (pyserial)
   - USB devices (pyusb)
   - Network communication

3. **File Operations**
   - All file I/O
   - Configuration files
   - Logging
   - Data export/import

### ⚠️ Needs Adapters

1. **GPIO** → USB GPIO adapter or Arduino
2. **CAN Bus** → USB-CAN adapter
3. **Analog Sensors** → USB ADC board or Arduino

## Installation Process

### Option 1: Automated Installer

1. Run `TelemetryIQ-Setup.exe`
2. Installer will:
   - Install Python (if needed)
   - Install dependencies
   - Install drivers
   - Create shortcuts

### Option 2: Manual Setup

1. **Install Python 3.11+**
   - Download from python.org
   - Check "Add Python to PATH"

2. **Run Setup Script**
   ```batch
   setup_windows.bat
   ```

3. **Install Drivers** (if using USB adapters)
   - FTDI: Run `drivers\FTDI\CDM21228_Setup.exe`
   - CH340: Run `drivers\CH340\CH341SER.EXE`

4. **Connect Hardware**
   - Plug in Arduino/USB adapters
   - Windows should detect them

5. **Run Application**
   ```batch
   python demo.py
   ```

## Hardware Setup

### Arduino Setup

1. **Upload Firmware**
   - Use Arduino IDE
   - Upload `hardware/arduino_gpio_breakout.ino`
   - Note the COM port (e.g., COM3)

2. **Configure in App**
   - Go to Settings → Hardware Interfaces
   - Select Arduino
   - Choose COM port
   - Test connection

### USB-CAN Adapter Setup

1. **Install Driver**
   - Driver depends on adapter model
   - Usually provided by manufacturer

2. **Configure in App**
   - Go to Settings → CAN Bus
   - Select USB-CAN adapter
   - Set bitrate (usually 500000)

### OBD-II Setup

1. **Connect Adapter**
   - Plug ELM327 adapter into OBD-II port
   - Connect via Bluetooth or USB

2. **Configure in App**
   - Go to Settings → OBD-II
   - Select adapter type
   - Auto-connect should work

## Testing on Windows

### Test Hardware Detection

```python
from interfaces.windows_hardware_adapter import WindowsHardwareAdapter

adapter = WindowsHardwareAdapter()
devices = adapter.detect_adapters()
for device in devices:
    print(f"Found: {device.name} on {device.port}")
```

### Test Arduino Connection

```python
from interfaces.windows_hardware_adapter import WindowsHardwareAdapter

adapter = WindowsHardwareAdapter()
ser = adapter.connect_arduino("COM3")
if ser:
    value = adapter.read_arduino_pin("COM3", 13)
    print(f"Pin 13: {value}")
```

## Troubleshooting

### Python Not Found

**Problem:** `python` command not recognized

**Solution:**
1. Reinstall Python
2. Check "Add Python to PATH"
3. Or use full path: `C:\Python311\python.exe`

### Driver Issues

**Problem:** USB device not recognized

**Solution:**
1. Install correct driver
2. Check Device Manager
3. Try different USB port
4. Update Windows

### COM Port Issues

**Problem:** Can't connect to Arduino

**Solution:**
1. Check COM port in Device Manager
2. Make sure no other program is using it
3. Try different baud rate
4. Check Arduino firmware is uploaded

### Permission Errors

**Problem:** Can't access USB devices

**Solution:**
1. Run as Administrator
2. Check USB permissions
3. Install drivers as Admin

## Performance Considerations

### USB Latency

- USB communication has higher latency than native GPIO
- Batch sensor readings when possible
- Use async I/O for better performance

### Serial Communication

- Arduino serial is slower than native GPIO
- Use higher baud rates (115200+)
- Minimize command frequency

### Windows-Specific Optimizations

- Use Windows-specific serial libraries if available
- Consider USB HID for faster communication
- Cache frequently accessed data

## Building the Installer

### Requirements

- Inno Setup 6+ (free)
- Python runtime (optional - can bundle)
- Driver files

### Build Steps

1. **Prepare Files**
   - Ensure all code is in `AI-TUNER-AGENT/`
   - Place drivers in `drivers/windows/`
   - Create `LICENSE.txt`

2. **Run Inno Setup**
   - Open `installer/windows_installer.iss`
   - Click "Build" → "Compile"
   - Installer will be in `dist/`

3. **Test Installer**
   - Run on clean Windows machine
   - Test all features
   - Verify drivers install correctly

## Distribution

### Installer Package

Include:
- `TelemetryIQ-Setup.exe` (main installer)
- `README-Windows.txt` (setup instructions)
- Hardware compatibility list
- Driver download links

### Optional: Portable Version

Create portable version:
- No installer needed
- Python bundled
- Run from USB drive
- Good for demos

## Next Steps

1. **Test on Windows 10/11**
2. **Test with various hardware**
3. **Create user documentation**
4. **Build installer package**
5. **Test installation process**

## Summary

The porting is straightforward because:
- ✅ Python is cross-platform
- ✅ Most libraries work on Windows
- ✅ Hardware abstraction layer handles differences
- ✅ USB adapters provide same functionality

The main work is:
- Hardware adapter implementation (DONE)
- Driver management (DONE)
- Installer creation (DONE)
- Testing and documentation (IN PROGRESS)











