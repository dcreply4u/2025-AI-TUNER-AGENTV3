# NUCLEO-H755ZI-Q Quick Start Guide

## Quick Integration Steps

### 1. Hardware Setup (UART - Simplest)

**Wiring:**
```
NUCLEO-H755ZI-Q    →    Raspberry Pi 5
─────────────────        ────────────────
PD8 (USART3_TX)    →    GPIO 15 (UART0_RX)
PD9 (USART3_RX)    ←    GPIO 14 (UART0_TX)
GND                →    GND
```

**Power:**
- NUCLEO: USB-C power (or external 5V)
- Pi 5: Standard power supply
- **Important**: Connect GND between boards!

### 2. Install Python Dependencies

```bash
pip install pyserial
# Optional for SPI:
pip install spidev
# Optional for I2C:
pip install smbus
```

### 3. Flash STM32 Firmware

1. Download STM32CubeMX
2. Configure USART3 at 921600 baud
3. Generate code and add communication handlers
4. Flash to NUCLEO board

See `NUCLEO_STM32_FIRMWARE_TEMPLATE.md` for details.

### 4. Test Connection

```python
from interfaces.nucleo_interface import NucleoInterface, NucleoConnectionType

# Create interface
nucleo = NucleoInterface(
    connection_type=NucleoConnectionType.UART,
    baudrate=921600,
    auto_detect=True
)

# Connect
if nucleo.connect():
    print("✅ Connected to NUCLEO!")
    
    # Read sensors
    sensors = nucleo.read_sensors()
    print(f"Sensors: {sensors}")
    
    # Get status
    status = nucleo.get_status()
    print(f"Status: {status}")
    
    # Disconnect
    nucleo.disconnect()
else:
    print("❌ Failed to connect")
```

### 5. Integrate into Application

Add to `controllers/data_stream_controller.py`:

```python
from interfaces.nucleo_interface import (
    NucleoInterface,
    NucleoConnectionType,
    NucleoSensorConfig,
    NucleoSensorType,
)

# In __init__:
self.nucleo_interface = None
try:
    from interfaces.nucleo_interface import NucleoInterface, NucleoConnectionType
    
    # Configure sensors
    sensor_configs = [
        NucleoSensorConfig(
            name="engine_temp",
            sensor_type=NucleoSensorType.TEMPERATURE,
            channel=0,
            unit="°C",
            min_value=-40.0,
            max_value=150.0,
        ),
        NucleoSensorConfig(
            name="oil_pressure",
            sensor_type=NucleoSensorType.PRESSURE,
            channel=1,
            unit="psi",
            min_value=0.0,
            max_value=100.0,
        ),
    ]
    
    self.nucleo_interface = NucleoInterface(
        connection_type=NucleoConnectionType.UART,
        baudrate=921600,
        auto_detect=True,
        sensor_configs=sensor_configs,
    )
    
    if self.nucleo_interface.connect():
        LOGGER.info("NUCLEO interface connected")
        
        # Set callback for continuous updates
        self.nucleo_interface.set_data_callback(self._on_nucleo_data)
    else:
        LOGGER.warning("NUCLEO interface not available")
        self.nucleo_interface = None
except Exception as e:
    LOGGER.warning(f"NUCLEO interface not available: {e}")
    self.nucleo_interface = None

# Add callback method:
def _on_nucleo_data(self, data: Dict[str, float]) -> None:
    """Handle sensor data from NUCLEO."""
    # Merge into telemetry data
    if self.nucleo_interface:
        for key, value in data.items():
            self._latest_sample[f"nucleo_{key}"] = value
```

### 6. Access in UI

The sensor data will automatically appear in:
- Telemetry graphs
- Gauge panels
- AI advisor context
- Data logging

Use prefix `nucleo_` to identify NUCLEO sensors (e.g., `nucleo_engine_temp`).

---

## Communication Protocol

### Request Format (JSON):
```json
{
  "cmd": "read_sensors",
  "sensors": ["engine_temp", "oil_pressure"],
  "timestamp": 1234567890.123
}
```

### Response Format (JSON):
```json
{
  "status": "ok",
  "data": {
    "engine_temp": 85.5,
    "oil_pressure": 45.2
  },
  "timestamp": 1234567890.123
}
```

---

## Troubleshooting

### "NUCLEO board not detected"
- Check USB connection
- Verify STM32 firmware is flashed
- Check serial port permissions: `sudo chmod 666 /dev/ttyUSB0`
- List ports: `python -m serial.tools.list_ports`

### "Connection timeout"
- Verify baudrate matches (921600)
- Check wiring (TX→RX, RX→TX, GND)
- Verify UART is enabled on Pi: `sudo raspi-config` → Interface Options → Serial Port

### "No response from board"
- Check STM32 firmware is running
- Verify USART3 is configured correctly
- Test with simple echo firmware first

### "Permission denied"
- Add user to dialout group: `sudo usermod -a -G dialout $USER`
- Log out and back in

---

## Next Steps

1. **Add More Sensors**: Configure additional sensors in `NucleoSensorConfig`
2. **Upgrade to SPI**: For higher data rates, switch to SPI interface
3. **Add CAN**: Integrate CAN bus for direct ECU communication
4. **Real-Time Control**: Use NUCLEO for closed-loop control (boost, fuel, etc.)

---

## Example Use Cases

### 1. High-Speed Analog Sampling
- Use NUCLEO's ADC for high-rate sampling (1MHz+)
- Stream data via SPI to Pi
- Offload processing from Pi CPU

### 2. CAN Bus Gateway
- NUCLEO reads multiple CAN buses
- Filters and forwards to Pi
- Reduces Pi CAN processing load

### 3. Real-Time Control
- NUCLEO runs control loops (PID, etc.)
- Pi provides setpoints and monitoring
- Deterministic timing on NUCLEO

### 4. Sensor Expansion
- Connect multiple I2C sensors to NUCLEO
- Aggregate and send to Pi
- Simplifies wiring

---

## Performance Benchmarks

| Interface | Max Speed | Latency | Use Case |
|-----------|-----------|---------|----------|
| UART      | 115 KB/s  | ~10ms   | Control, status |
| SPI       | 6 MB/s    | ~1ms    | High-speed data |
| I2C       | 50 KB/s   | ~5ms    | Multi-sensor |
| CAN       | 125 KB/s  | ~2ms    | Automotive |

---

**Ready to integrate!** Start with UART for simplicity, then expand as needed.

