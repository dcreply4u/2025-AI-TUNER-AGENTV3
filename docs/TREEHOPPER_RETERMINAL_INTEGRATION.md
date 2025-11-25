# Treehopper + reTerminal DM Integration Plan

## Overview

This document outlines the technical implementation for supporting both reTerminal DM and Treehopper simultaneously, creating a unified I/O system with maximum capabilities.

---

## Architecture

### **Unified I/O Manager**

```
┌─────────────────────────────────────────────────┐
│         AI Tuner Agent Software                 │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │     Unified I/O Manager                  │   │
│  │  - Combines I/O from all devices        │   │
│  │  - Presents unified interface           │   │
│  │  - Handles device communication         │   │
│  └──────────────────────────────────────────┘   │
│           │                    │                  │
│           ▼                    ▼                  │
│  ┌──────────────┐    ┌──────────────────┐       │
│  │ reTerminal DM│    │   Treehopper      │       │
│  │  Interface   │    │   Interface       │       │
│  └──────────────┘    └──────────────────┘       │
│           │                    │                  │
│           ▼                    ▼                  │
│  ┌──────────────┐    ┌──────────────────┐       │
│  │ reTerminal DM│    │   Treehopper     │       │
│  │  Hardware    │    │   USB Device     │       │
│  └──────────────┘    └──────────────────┘       │
└─────────────────────────────────────────────────┘
```

---

## Implementation Plan

### **Phase 1: Treehopper Detection & Basic I/O**

**File**: `interfaces/treehopper_adapter.py`

```python
class TreehopperAdapter:
    """Treehopper USB interface adapter."""
    
    def detect() -> bool:
        """Detect Treehopper USB device."""
        # USB HID detection
        # Check for Treehopper VID/PID
        
    def read_digital(pin: int) -> bool:
        """Read digital pin."""
        
    def write_digital(pin: int, value: bool):
        """Write digital pin."""
        
    def read_analog(pin: int) -> float:
        """Read analog pin (0-3.3V)."""
        
    def write_pwm(pin: int, duty_cycle: float):
        """Write PWM signal."""
        
    def i2c_scan() -> List[int]:
        """Scan I2C bus."""
        
    def spi_transfer(data: bytes) -> bytes:
        """SPI data transfer."""
```

### **Phase 2: Unified I/O Manager**

**File**: `interfaces/unified_io_manager.py`

```python
class UnifiedIOManager:
    """Manages I/O from multiple devices (reTerminal DM + Treehopper)."""
    
    def __init__(self):
        self.reterminal_io = None  # reTerminal DM I/O
        self.treehopper_io = None  # Treehopper I/O
        self.pin_map = {}  # Unified pin mapping
        
    def detect_devices(self):
        """Detect all available I/O devices."""
        # Detect reTerminal DM
        # Detect Treehopper
        # Create unified pin map
        
    def read_gpio(self, pin: int) -> bool:
        """Read GPIO from appropriate device."""
        device, local_pin = self._resolve_pin(pin)
        return device.read_digital(local_pin)
        
    def write_gpio(self, pin: int, value: bool):
        """Write GPIO to appropriate device."""
        device, local_pin = self._resolve_pin(pin)
        device.write_digital(local_pin, value)
        
    def read_analog(self, channel: int) -> float:
        """Read analog from appropriate device."""
        device, local_channel = self._resolve_analog(channel)
        return device.read_analog(local_channel)
        
    def _resolve_pin(self, pin: int) -> Tuple[Device, int]:
        """Resolve unified pin to device and local pin."""
        # Pins 0-39: reTerminal DM
        # Pins 40-59: Treehopper
        if pin < 40:
            return self.reterminal_io, pin
        else:
            return self.treehopper_io, pin - 40
```

### **Phase 3: Integration with Existing System**

**Update**: `interfaces/sensor_manager.py`

```python
class SensorManager:
    """Unified manager for all sensor types."""
    
    def __init__(self):
        # Existing managers
        self.analog_manager = AnalogSensorManager()
        self.digital_manager = DigitalSensorManager()
        
        # NEW: Unified I/O manager
        self.io_manager = UnifiedIOManager()
        self.io_manager.detect_devices()
        
    def add_analog_sensor(self, config: AnalogSensorConfig) -> bool:
        """Add analog sensor (can use reTerminal or Treehopper)."""
        # Check which device has available ADC
        # Assign to appropriate device
        return self.io_manager.add_analog_sensor(config)
        
    def add_digital_sensor(self, config: DigitalSensorConfig) -> bool:
        """Add digital sensor (can use reTerminal or Treehopper)."""
        # Check which device has available GPIO
        # Assign to appropriate device
        return self.io_manager.add_digital_sensor(config)
```

### **Phase 4: Hardware Platform Detection**

**Update**: `core/hardware_platform.py`

```python
class HardwareDetector:
    @staticmethod
    def detect() -> HardwareConfig:
        """Detect hardware platform and additional devices."""
        config = HardwareDetector._detect_base_platform()
        
        # Check for Treehopper
        if TreehopperAdapter.detect():
            config.has_treehopper = True
            config.total_gpio_pins = config.gpio_pins + 20  # Add Treehopper pins
            config.total_adc_channels = config.adc_channels + TreehopperAdapter.ADC_CHANNELS
            LOGGER.info("Treehopper detected - additional I/O available")
        
        return config
```

---

## Pin Mapping Strategy

### **Unified Pin Numbering**

| Pin Range | Device | Description |
|-----------|--------|-------------|
| **0-39** | reTerminal DM | 40-pin GPIO header |
| **40-59** | Treehopper | 20 GPIO pins |
| **Total** | **60 pins** | Unified GPIO interface |

### **ADC Channel Mapping**

| Channel Range | Device | Description |
|---------------|--------|-------------|
| **0-6** | reTerminal DM | 7 ADC channels (via HAT) |
| **7-14** | Treehopper | 8 ADC channels |
| **Total** | **15 channels** | Unified ADC interface |

### **Protocol Buses**

| Protocol | reTerminal DM | Treehopper | Combined |
|----------|---------------|------------|----------|
| **I2C** | ✅ 1 bus | ✅ 1 bus | ✅ 2 buses |
| **SPI** | ✅ 1 bus | ✅ 1 bus | ✅ 2 buses |
| **UART** | ✅ Multiple | ✅ 1 bus | ✅ Multiple |

---

## Software Features

### **1. Auto-Detection**

The software will automatically:
- ✅ Detect reTerminal DM (if present)
- ✅ Detect Treehopper (if present)
- ✅ Combine I/O capabilities
- ✅ Present unified interface

### **2. Device Status**

UI will show:
- ✅ reTerminal DM status (connected/disconnected)
- ✅ Treehopper status (connected/disconnected)
- ✅ Total available I/O (GPIO, ADC, etc.)
- ✅ Device capabilities

### **3. Sensor Assignment**

When adding sensors:
- ✅ Software suggests best device
- ✅ User can manually select device
- ✅ Automatic load balancing
- ✅ Conflict detection

### **4. Error Handling**

- ✅ Graceful degradation if Treehopper disconnected
- ✅ Automatic reconnection
- ✅ Fallback to reTerminal DM only
- ✅ Clear error messages

---

## Configuration Examples

### **Example 1: Maximum Sensors**

```json
{
  "io_devices": {
    "reterminal_dm": {
      "enabled": true,
      "gpio_pins": [0, 1, 2, 3, 4, 5, 6, 7],
      "adc_channels": [0, 1, 2, 3],
      "i2c_bus": 1,
      "spi_bus": 0
    },
    "treehopper": {
      "enabled": true,
      "gpio_pins": [40, 41, 42, 43, 44, 45],
      "adc_channels": [7, 8, 9, 10],
      "i2c_bus": 2,
      "spi_bus": 1
    }
  },
  "sensors": {
    "oil_pressure": {
      "device": "reterminal_dm",
      "adc_channel": 0
    },
    "fuel_pressure": {
      "device": "treehopper",
      "adc_channel": 7
    },
    "transbrake": {
      "device": "reterminal_dm",
      "gpio_pin": 18
    },
    "nitrous_solenoid": {
      "device": "treehopper",
      "gpio_pin": 40
    }
  }
}
```

### **Example 2: Budget Configuration (Treehopper Only)**

```json
{
  "io_devices": {
    "reterminal_dm": {
      "enabled": false
    },
    "treehopper": {
      "enabled": true,
      "gpio_pins": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
      "adc_channels": [0, 1, 2, 3, 4, 5],
      "i2c_bus": 1,
      "spi_bus": 0
    }
  },
  "can_bus": {
    "device": "usb_can_adapter",
    "channels": ["can0", "can1"]
  }
}
```

---

## Benefits of Combined System

### **1. Maximum I/O**
- **60 GPIO pins** (vs 40 or 20 alone)
- **15 ADC channels** (vs 7 or 8 alone)
- **Multiple I2C/SPI buses** (vs 1 alone)

### **2. Flexibility**
- **Redundancy**: Backup I/O if one device fails
- **Expansion**: Add more sensors without replacing hardware
- **Remote placement**: Treehopper can be placed remotely via USB

### **3. Professional + Portable**
- **reTerminal DM**: Fixed professional installation
- **Treehopper**: Can be used separately for portable logging
- **Best of both worlds**

### **4. Future-Proof**
- **Easy expansion**: Add more Treehoppers if needed
- **Modular design**: Upgrade components independently
- **Scalable**: From basic to maximum configuration

---

## Implementation Timeline

### **Week 1: Treehopper Adapter**
- ✅ Create `TreehopperAdapter` class
- ✅ Implement USB HID detection
- ✅ Implement basic I/O (digital, analog, PWM)
- ✅ Test with Treehopper hardware

### **Week 2: Unified I/O Manager**
- ✅ Create `UnifiedIOManager` class
- ✅ Implement pin mapping
- ✅ Implement device detection
- ✅ Test with both devices

### **Week 3: Integration**
- ✅ Update `SensorManager` to use unified I/O
- ✅ Update `HardwareDetector` for Treehopper
- ✅ Update UI to show device status
- ✅ Test sensor assignment

### **Week 4: Testing & Documentation**
- ✅ Comprehensive testing
- ✅ Error handling
- ✅ Documentation
- ✅ Setup guides for both configurations

---

## Testing Strategy

### **Test Scenarios**

1. **reTerminal DM Only**
   - ✅ All features work
   - ✅ No Treehopper errors
   - ✅ Graceful handling

2. **Treehopper Only**
   - ✅ All features work
   - ✅ USB-CAN adapter works
   - ✅ No reTerminal DM errors

3. **Both Devices**
   - ✅ Unified I/O works
   - ✅ Pin mapping correct
   - ✅ No conflicts
   - ✅ Maximum sensors supported

4. **Device Disconnection**
   - ✅ Treehopper disconnected gracefully
   - ✅ reTerminal DM disconnected gracefully
   - ✅ Automatic reconnection

---

## Next Steps

1. ✅ **Research Treehopper API** - Get USB HID protocol details
2. ✅ **Create TreehopperAdapter** - Basic I/O implementation
3. ✅ **Create UnifiedIOManager** - Combine I/O from both devices
4. ✅ **Update SensorManager** - Use unified I/O
5. ✅ **Update UI** - Show device status and capabilities
6. ✅ **Testing** - Comprehensive testing with both configurations
7. ✅ **Documentation** - Setup guides for both product tiers

---

**This integration enables the ultimate solution: reTerminal DM + Treehopper for maximum I/O capabilities!**









