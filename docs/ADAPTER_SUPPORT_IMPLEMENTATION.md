# Adapter Support Implementation

## Overview

Comprehensive adapter detection and support system for GPIO, OBD2, and Serial adapters with auto-detection, health monitoring, and auto-configuration.

## Features

### ✅ GPIO Adapter Support

**Supported Adapters:**
- **Built-in GPIO:**
  - reTerminal DM (40 GPIO pins, I2C, SPI, UART)
  - Raspberry Pi (26/40 GPIO pins depending on model)
  - BeagleBone Black (65 GPIO pins, 7 ADC channels, CAN)

- **I2C GPIO Expanders:**
  - MCP23017 (16 GPIO pins)
  - PCF8574 (8 GPIO pins)

- **USB GPIO Adapters:**
  - FT232H (13 GPIO pins, I2C, SPI, PWM)
  - CH341 (8 GPIO pins)
  - Adafruit FT232H Breakout

**Auto-Detection:**
- Platform detection (reTerminal DM, Raspberry Pi, BeagleBone)
- I2C bus scanning for expanders
- USB device detection by VID:PID
- Automatic capability detection

### ✅ OBD2 Adapter Support

**Supported Adapters:**
- **ELM327-based (most common):**
  - ELM327 (USB, Bluetooth, WiFi)
  - OBDLink (USB, Bluetooth)
  - Carista
  - Veepeak
  - BAFX Products
  - And many more ELM327 clones

- **Connection Types:**
  - USB (wired)
  - Bluetooth (wireless)
  - WiFi (wireless)

**Auto-Detection:**
- USB VID:PID matching
- Serial port description matching
- Bluetooth device scanning
- WiFi SSID detection
- ELM327 protocol testing (ATZ command)

### ✅ Serial Adapter Support

**Supported Adapters:**
- **FTDI:**
  - FT232 (USB-to-Serial)
  - FT2232 (Dual port)
  - FT4232 (Quad port)
  - FT232H (High-speed with GPIO)
  - FT231X

- **WCH (CH340/CH341):**
  - CH340 (USB-to-Serial)
  - CH341 (USB-to-Serial with GPIO)

- **Silicon Labs (CP210x):**
  - CP2102
  - CP2103
  - CP2104
  - CP2105

- **Prolific (PL2303):**
  - PL2303 (USB-to-Serial)

- **Other:**
  - Arduino (Uno, Mega)
  - ESP32/ESP8266
  - Generic USB Serial

**Auto-Detection:**
- USB VID:PID matching
- Serial port enumeration
- Bluetooth serial device scanning
- WiFi serial device detection

## Database System

### Adapter Database

**File:** `services/adapter_database.py`

Stores:
- Adapter configurations
- Connection history
- Performance metrics
- Capabilities

**Tables:**
1. **adapters** - Adapter configurations
2. **connection_history** - Connection logs
3. **performance_metrics** - Performance data

**Usage:**
```python
from services.adapter_database import get_adapter_database, AdapterConfig, AdapterType

db = get_adapter_database()
adapters = db.list_adapters(adapter_type=AdapterType.OBD2)
```

## Auto-Detection System

### GPIO Adapter Detector

**File:** `interfaces/gpio_adapter_detector.py`

**Detection Methods:**
1. Platform detection (checking `/proc/device-tree/model`)
2. I2C bus scanning (`i2cdetect`)
3. USB device detection (checking `/sys/bus/usb/devices`)

**Usage:**
```python
from interfaces.gpio_adapter_detector import GPIOAdapterDetector

detector = GPIOAdapterDetector()
adapters = detector.detect_all()
```

### OBD2 Adapter Detector

**File:** `interfaces/obd2_adapter_detector.py`

**Detection Methods:**
1. USB VID:PID matching
2. Serial port description matching
3. Bluetooth device scanning (`bluetoothctl`)
4. WiFi SSID detection (`nmcli`)
5. ELM327 protocol testing (ATZ command)

**Usage:**
```python
from interfaces.obd2_adapter_detector import OBD2AdapterDetector

detector = OBD2AdapterDetector()
adapters = detector.detect_all()
```

### Serial Adapter Detector

**File:** `interfaces/serial_adapter_detector.py`

**Detection Methods:**
1. USB VID:PID matching
2. Serial port enumeration (`serial.tools.list_ports`)
3. Bluetooth device scanning
4. WiFi device detection

**Usage:**
```python
from interfaces.serial_adapter_detector import SerialAdapterDetector

detector = SerialAdapterDetector()
adapters = detector.detect_all()
```

## Unified Adapter Manager

**File:** `interfaces/unified_adapter_manager.py`

**Features:**
- Unified interface for all adapter types
- Health monitoring
- Auto-configuration
- Connection management
- Adapter recommendation

**Usage:**
```python
from interfaces.unified_adapter_manager import get_unified_adapter_manager

manager = get_unified_adapter_manager()

# Detect all adapters
all_adapters = manager.detect_all_adapters()

# Activate adapter
manager.activate_adapter("ELM327_COM3")

# Get adapter health
health = manager.get_adapter_health("ELM327_COM3")

# Auto-configure
manager.auto_configure_adapter("ELM327_COM3")

# Get recommended adapter
recommended = manager.get_recommended_adapter(
    AdapterType.OBD2,
    criteria={"max_baud_rate": 115200}
)
```

## Health Monitoring

### Adapter Health Monitor

**Features:**
- Error tracking
- Health score calculation (0.0 to 1.0)
- Status reporting (Healthy, Degraded, Warning, Critical)
- Performance metrics logging

**Health Score Calculation:**
- 1.0 = Perfect (no errors)
- 0.9-1.0 = Healthy
- 0.7-0.9 = Degraded
- 0.5-0.7 = Warning
- <0.5 = Critical

**Usage:**
```python
# Health monitoring is automatic when adapter is activated
health = manager.get_adapter_health("adapter_name")
print(f"Health: {health['health_score']:.2f}")
print(f"Status: {health['status']}")
```

## Auto-Configuration

**Features:**
- Automatic baud rate selection
- Protocol detection
- Optimal settings application
- Capability-based configuration

**Supported Auto-Configurations:**
- OBD2: ELM327 initialization, protocol selection
- Serial: Baud rate optimization, parity/stop bits
- GPIO: Pin mode configuration, voltage level selection

## Integration Examples

### Complete Workflow

```python
from interfaces.unified_adapter_manager import get_unified_adapter_manager
from services.adapter_database import AdapterType

# Initialize manager
manager = get_unified_adapter_manager()

# Detect all adapters
all_adapters = manager.detect_all_adapters()

# List available OBD2 adapters
obd2_adapters = manager.list_adapters(adapter_type=AdapterType.OBD2)

# Get recommended adapter
recommended = manager.get_recommended_adapter(AdapterType.OBD2)

# Activate and configure
if recommended:
    manager.activate_adapter(recommended.name)
    manager.auto_configure_adapter(recommended.name)
    
    # Monitor health
    health = manager.get_adapter_health(recommended.name)
    print(f"Adapter {recommended.name} is {health['status']}")
```

### Error Handling

```python
try:
    # Use adapter
    data = read_from_adapter(adapter_name)
    manager.log_adapter_success(adapter_name)
except Exception as e:
    manager.log_adapter_error(adapter_name, e)
    health = manager.get_adapter_health(adapter_name)
    if health['health_score'] < 0.5:
        # Switch to backup adapter
        backup = manager.get_recommended_adapter(AdapterType.OBD2)
        if backup:
            manager.activate_adapter(backup.name)
```

## Supported Adapter List

### GPIO Adapters
- ✅ reTerminal DM (built-in)
- ✅ Raspberry Pi (built-in)
- ✅ BeagleBone Black (built-in)
- ✅ MCP23017 (I2C)
- ✅ PCF8574 (I2C)
- ✅ FT232H (USB)
- ✅ CH341 (USB)
- ✅ Adafruit FT232H

### OBD2 Adapters
- ✅ ELM327 (USB/Bluetooth/WiFi)
- ✅ OBDLink (USB/Bluetooth)
- ✅ Carista
- ✅ Veepeak
- ✅ BAFX Products
- ✅ PLX Devices
- ✅ Kiwi
- ✅ Generic ELM327 clones

### Serial Adapters
- ✅ FTDI FT232/FT2232/FT4232/FT232H
- ✅ WCH CH340/CH341
- ✅ Silicon Labs CP2102/CP2103/CP2104/CP2105
- ✅ Prolific PL2303
- ✅ Arduino (Uno, Mega)
- ✅ ESP32/ESP8266
- ✅ Generic USB Serial

## Future Enhancements

1. **CAN Adapter Support:**
   - USB-CAN adapters
   - CAN bus analyzers
   - CAN FD support

2. **I2C/SPI Adapter Support:**
   - Dedicated I2C/SPI adapters
   - Multi-protocol adapters

3. **Network Adapters:**
   - Ethernet-based adapters
   - Network device discovery

4. **Advanced Health Monitoring:**
   - Predictive failure detection
   - Performance trend analysis
   - Automatic failover

5. **Configuration Profiles:**
   - Save/load adapter configurations
   - Profile templates
   - Quick setup wizards

## Summary

All requested adapter support features have been implemented:

✅ GPIO adapter detection and support
✅ OBD2 adapter detection and support (wired/wireless)
✅ Serial adapter detection and support
✅ Auto-detection for all adapter types
✅ Database for adapter configurations
✅ Health monitoring system
✅ Auto-configuration
✅ Unified adapter management
✅ Connection tracking
✅ Performance metrics

The system is ready for integration and provides a solid foundation for future adapter support.






