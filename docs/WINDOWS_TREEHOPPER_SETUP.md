# Windows + Treehopper Setup Guide

This guide covers setting up the AI Tuner Agent on Windows with Treehopper USB device support.

## Overview

The AI Tuner Agent can run on Windows and use Treehopper USB devices to provide GPIO, ADC, PWM, I2C, SPI, and UART capabilities that are normally only available on embedded Linux platforms.

## Hardware Requirements

### Required
- **Windows 10/11** (64-bit)
- **Treehopper USB device** - Provides GPIO, ADC, PWM, I2C, SPI, UART
- **USB-CAN adapter** (optional, for CAN bus communication)

### Optional
- **USB-CAN adapter** - For connecting to vehicle CAN bus
- **Display** - Any Windows-compatible monitor

## Software Setup

### 1. Install Python

Download and install Python 3.9 or later from [python.org](https://www.python.org/downloads/).

Verify installation:
```powershell
python --version
```

### 2. Install Dependencies

Navigate to the project directory and install required packages:

```powershell
cd AI-TUNER-AGENT
pip install -r requirements.txt
```

### 3. Install Treehopper USB Driver

The Treehopper device uses USB HID (Human Interface Device) protocol, which is typically supported natively on Windows. However, you may need to install the `hidapi` Python library:

```powershell
pip install hidapi
```

**Note:** On some systems, you may also need to install the `hidapi` C library. Check the [hidapi documentation](https://github.com/apache/hidapi) for Windows installation instructions.

### 4. Verify Treehopper Connection

Run the hardware check:

```powershell
python launch_windows.py --check-hardware
```

You should see:
```
[✓] Treehopper USB device detected
    - GPIO Pins: 20
    - ADC Channels: 8
    - PWM Channels: 8
```

If Treehopper is not detected:
1. Check that the device is connected via USB
2. Verify the device appears in Device Manager
3. Try unplugging and reconnecting the device
4. Check Windows Device Manager for any driver issues

## Running the Application

### Demo Mode (No Hardware Required)

Test the application with simulated data:

```powershell
python launch_windows.py --demo
```

### Full Mode (With Treehopper)

Run the full application:

```powershell
python launch_windows.py
```

The application will automatically detect Treehopper if connected and enable GPIO/ADC features.

### Debug Mode

Enable verbose logging:

```powershell
python launch_windows.py --debug
```

## Features Available on Windows

### With Treehopper Connected

✅ **GPIO** - 20 digital I/O pins  
✅ **ADC** - 8 analog input channels  
✅ **PWM** - 8 PWM output channels  
✅ **I2C** - I2C bus communication  
✅ **SPI** - SPI bus communication  
✅ **UART** - Serial communication  

### Without Treehopper

❌ GPIO/ADC/PWM features disabled  
✅ CAN bus (via USB-CAN adapter)  
✅ GUI and telemetry display  
✅ Data logging and analysis  
✅ Cloud sync  

## Pin Mapping

When using Treehopper on Windows, GPIO pins are mapped as follows:

- **Pins 0-19**: Treehopper GPIO pins
- **ADC Channels 0-7**: Treehopper ADC channels

The unified I/O manager automatically handles pin routing to Treehopper.

## CAN Bus Support

Windows does not have native CAN bus support. To use CAN bus on Windows:

1. **Connect USB-CAN adapter** (e.g., Peak PCAN, Kvaser, etc.)
2. **Install adapter drivers** (provided by manufacturer)
3. **Configure adapter** - The system will attempt to auto-detect CAN interfaces

Common USB-CAN adapters:
- Peak PCAN-USB
- Kvaser USBcan
- Vector CANcase
- Lawicel CANUSB

## Troubleshooting

### Treehopper Not Detected

1. **Check USB connection**: Ensure Treehopper is properly connected
2. **Install hidapi**: `pip install hidapi`
3. **Check Device Manager**: Verify device appears without errors
4. **Try different USB port**: Some USB ports may have power/connectivity issues
5. **Check permissions**: On some systems, you may need administrator privileges

### CAN Bus Not Working

1. **Verify adapter drivers**: Check Device Manager for driver issues
2. **Check adapter compatibility**: Ensure adapter is supported by `python-can`
3. **Test with adapter software**: Use manufacturer's software to verify adapter works
4. **Check bitrate settings**: Ensure CAN bitrate matches vehicle/ECU settings

### Application Won't Start

1. **Check Python version**: Ensure Python 3.9+ is installed
2. **Verify dependencies**: Run `pip install -r requirements.txt`
3. **Check logs**: Review `logs/windows.log` for errors
4. **Run with debug**: `python launch_windows.py --debug`

## Example Usage

### Reading a Digital Sensor

```python
from interfaces.unified_io_manager import UnifiedIOManager

io = UnifiedIOManager()
# Configure pin 0 as input
io.configure_pin(0, "input")
# Read pin value
value = io.read_digital(0)
```

### Reading an Analog Sensor

```python
from interfaces.unified_io_manager import UnifiedIOManager

io = UnifiedIOManager()
# Read ADC channel 0 (0-3.3V)
voltage = io.read_analog(0)
```

### Writing to a Digital Output

```python
from interfaces.unified_io_manager import UnifiedIOManager

io = UnifiedIOManager()
# Configure pin 1 as output
io.configure_pin(1, "output")
# Set pin high
io.write_digital(1, True)
```

## Performance Considerations

- **Treehopper USB latency**: ~1-5ms per operation
- **Suitable for**: Sensor reading, relay control, basic I/O
- **Not suitable for**: High-frequency PWM (>1kHz), real-time critical operations

For high-performance applications, consider using embedded platforms (reTerminal DM, Raspberry Pi) instead of Windows.

## Next Steps

- See [SENSOR_INTEGRATION.md](SENSOR_INTEGRATION.md) for sensor connection details
- See [HARDWARE_CONNECTIONS.md](HARDWARE_CONNECTIONS.md) for wiring diagrams
- See [QUICK_START_WINDOWS.md](../QUICK_START_WINDOWS.md) for general Windows setup

## Support

For issues specific to:
- **Treehopper**: Check [Treehopper documentation](https://treehopper.io/)
- **Windows setup**: Check Windows logs in `logs/windows.log`
- **Application issues**: Run with `--debug` flag and check logs




