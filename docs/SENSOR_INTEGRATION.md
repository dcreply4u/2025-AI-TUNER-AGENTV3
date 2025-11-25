# Sensor Integration Guide

## Overview

The AI Tuner Agent supports multiple sensor types and connection methods. This guide explains how to connect external sensors to your hardware platform.

## Connection Methods

### 1. CAN Bus (Recommended for Automotive)

**Best for:** ECU data, most automotive sensors

**Hardware Required:**
- **reTerminal DM**: Built-in dual CAN FD interfaces (can0, can1)
- **Raspberry Pi**: CAN HAT (e.g., PiCAN2, MCP2515-based)
- **Jetson**: CAN expansion board

**Cables:**
- CAN-H and CAN-L wires (twisted pair recommended)
- 120Ω termination resistors (one at each end of bus)
- Power and ground connections

**Software:**
- Uses `python-can` library
- Auto-detects CAN vendor (Holley, Haltech, AEM, etc.)
- Supports DBC file decoding

**Example Sensors:**
- ECU telemetry (RPM, throttle, boost, etc.)
- Wideband O2 sensors (via CAN)
- Data loggers (RaceCapture, etc.)

### 2. Analog Sensors

**Best for:** Temperature, pressure, voltage sensors

**Hardware Required:**
- **reTerminal DM**: GPIO pins (some support ADC)
- **Raspberry Pi**: ADC HAT (e.g., ADS1115, MCP3008)
- **Jetson**: ADC expansion board

**Cables:**
- Sensor signal wire (0-5V or 0-3.3V typically)
- Power wire (5V or 12V depending on sensor)
- Ground wire

**Interface:**
- I2C or SPI ADC converters
- Direct GPIO (if platform supports ADC)

**Example Sensors:**
- Oil pressure sensors (0-5V output)
- Coolant temperature sensors
- Fuel pressure sensors
- Battery voltage monitors

### 3. Digital I/O

**Best for:** Switches, relays, on/off sensors

**Hardware Required:**
- GPIO pins on any platform
- Optional: Digital I/O expansion board

**Cables:**
- Signal wire
- Ground wire
- Optional: Pull-up/pull-down resistors

**Example Sensors:**
- Transbrake switch
- Nitrous solenoid status
- Methanol injection pump status
- Safety switches

### 4. Serial/UART

**Best for:** GPS modules, some sensors with serial output

**Hardware Required:**
- USB-to-Serial adapter OR
- Built-in UART pins (GPIO 14/15 on Pi)

**Cables:**
- USB cable (if USB device)
- Or: TX, RX, GND wires for UART

**Example Sensors:**
- GPS modules (USB or UART)
- Some wideband controllers
- Serial data loggers

### 5. I2C Sensors

**Best for:** Multiple sensors on same bus

**Hardware Required:**
- I2C bus (available on all platforms)
- Pull-up resistors (usually on board)

**Cables:**
- SDA (data) wire
- SCL (clock) wire
- Power and ground

**Example Sensors:**
- Temperature sensors (DS18B20, TMP102)
- Pressure sensors with I2C output
- Accelerometers
- Gyroscopes

### 6. SPI Sensors

**Best for:** High-speed sensor data

**Hardware Required:**
- SPI bus (available on all platforms)

**Cables:**
- MOSI, MISO, SCLK, CS wires
- Power and ground

**Example Sensors:**
- High-speed ADCs
- Some pressure sensors
- Digital sensors requiring SPI

## Hardware Platform Comparison

### reTerminal DM (Recommended)

**Built-in:**
- ✅ Dual CAN FD (can0, can1) - **No additional hardware needed!**
- ✅ GPIO pins (40-pin header)
- ✅ USB ports (for USB sensors)
- ✅ Serial ports
- ✅ I2C, SPI buses

**Additional Hardware Needed:**
- ADC board for analog sensors (if needed)
- Sensor-specific interfaces

**Best For:**
- Multiple CAN bus sensors
- Professional racing applications
- Industrial environments

### Raspberry Pi 5

**Built-in:**
- ✅ GPIO pins (40-pin header)
- ✅ USB ports
- ✅ I2C, SPI buses

**Additional Hardware Needed:**
- CAN HAT (for CAN bus)
- ADC HAT (for analog sensors)

**Best For:**
- Budget-conscious builds
- DIY projects
- Learning/development

### Jetson Nano

**Built-in:**
- ✅ GPIO pins
- ✅ USB ports
- ✅ I2C, SPI buses

**Additional Hardware Needed:**
- CAN expansion board
- ADC board

**Best For:**
- AI/ML applications
- Computer vision integration
- Advanced processing

## Sensor Interface Module

The software includes a sensor interface abstraction layer that handles:

```python
# Example: Analog sensor interface
from interfaces.analog_sensor import AnalogSensorInterface

# Configure sensor
sensor = AnalogSensorInterface(
    channel=0,  # ADC channel
    sensor_type="pressure",
    min_voltage=0.5,  # 0 PSI
    max_voltage=4.5,   # 100 PSI
    unit="psi"
)

# Read value
pressure = sensor.read()  # Returns PSI value
```

## Multi-Sensor Configuration

### Example: Racing Setup

**Sensors:**
1. **ECU Data** → CAN Bus (can0)
2. **Wideband O2** → CAN Bus (can0) or Serial
3. **Oil Pressure** → Analog (ADC channel 0)
4. **Fuel Pressure** → Analog (ADC channel 1)
5. **Transbrake** → Digital GPIO (pin 18)
6. **Nitrous Solenoid** → Digital GPIO (pin 19)
7. **GPS** → USB Serial
8. **Front Camera** → USB
9. **Rear Camera** → USB

**Configuration:**
```python
# sensors_config.json
{
    "can_sensors": {
        "can0": {
            "ecu": {"vendor": "holley", "dbc": "holley.dbc"},
            "wideband": {"id": 0x200, "type": "lambda"}
        }
    },
    "analog_sensors": {
        "oil_pressure": {"channel": 0, "type": "pressure", "range": [0, 100]},
        "fuel_pressure": {"channel": 1, "type": "pressure", "range": [0, 100]}
    },
    "digital_sensors": {
        "transbrake": {"pin": 18, "pull": "up"},
        "nitrous_solenoid": {"pin": 19, "pull": "up"}
    },
    "serial_sensors": {
        "gps": {"port": "/dev/ttyUSB0", "baud": 9600}
    }
}
```

## Wiring Diagrams

### CAN Bus Connection

```
Sensor/ECU          reTerminal DM
CAN-H ────────────── CAN-H (can0)
CAN-L ────────────── CAN-L (can0)
GND   ────────────── GND
+12V  ────────────── +12V (if sensor needs power)
```

**Termination:**
- 120Ω resistor between CAN-H and CAN-L at each end of bus

### Analog Sensor Connection

```
Pressure Sensor     ADC Board      reTerminal DM
Signal ──────────── ADC Input ──── I2C/SPI
+5V    ──────────── VCC
GND    ──────────── GND ─────────── GND
```

### Digital Sensor Connection

```
Switch              reTerminal DM
Signal ───────────── GPIO Pin (e.g., 18)
GND    ───────────── GND
(Optional pull-up resistor to 3.3V)
```

## Software Integration

### Adding a New Sensor Type

1. **Create sensor interface:**
```python
# interfaces/custom_sensor.py
class CustomSensorInterface:
    def __init__(self, config):
        self.config = config
    
    def read(self):
        # Read sensor value
        return value
```

2. **Register in data stream controller:**
```python
# The controller automatically polls all registered sensors
controller.register_sensor("custom_sensor", CustomSensorInterface(config))
```

3. **Add to telemetry mapping:**
```python
# Maps sensor readings to canonical metric names
CANONICAL_METRICS = {
    "CustomSensor_Value": "CustomMetric",
    # ...
}
```

## Recommended Sensor Setup

### Basic Setup (OBD-II Only)
- OBD-II adapter → USB
- GPS module → USB
- **Total:** 2 USB devices

### Intermediate Setup
- ECU → CAN Bus
- Wideband O2 → CAN Bus or Serial
- GPS → USB
- **Total:** CAN bus + 1 USB

### Advanced Setup (Racing)
- ECU → CAN Bus (can0)
- Secondary ECU/Logger → CAN Bus (can1)
- Analog sensors (pressure, temp) → ADC board → I2C
- Digital sensors (switches) → GPIO
- GPS → USB Serial
- Cameras → USB
- **Total:** 2 CAN buses + I2C + GPIO + USB

## Power Requirements

**reTerminal DM:**
- 12V DC input
- Can power sensors via GPIO (3.3V/5V) or external power supply

**Sensor Power:**
- Most sensors: 5V or 12V
- Use external power supply for high-current sensors
- Use voltage regulators for sensitive sensors

## Troubleshooting

### CAN Bus Issues
- Check termination resistors (120Ω at each end)
- Verify CAN-H and CAN-L are not swapped
- Check bitrate matches (typically 500kbps)
- Use `candump can0` to verify messages

### Analog Sensor Issues
- Verify voltage range (0-3.3V or 0-5V)
- Check ADC reference voltage
- Calibrate sensor (min/max values)
- Check for noise (use shielded cables)

### Digital Sensor Issues
- Verify pull-up/pull-down resistors
- Check GPIO pin configuration
- Verify voltage levels (3.3V vs 5V)

## Next Steps

1. Identify your sensors and their output types
2. Choose appropriate interface method
3. Configure in software
4. Test with demo mode first
5. Connect real hardware

For specific sensor integration help, refer to the sensor manufacturer's documentation and the AI Tuner Agent configuration files.

