# Raspberry Pi 5 HAT Detection Guide

## Overview

The AI Tuner Agent now automatically detects installed HATs on Raspberry Pi 5 and configures the system accordingly. This enables the modular hardware approach with different product tiers.

## Automatic Detection

The system detects HATs at startup and configures:

- **CAN Bus Channels**: Number of CAN interfaces available
- **GPS Availability**: GPS modules for location tracking
- **IMU Sensors**: Motion/acceleration sensors
- **GPIO Expansion**: Additional GPIO pins from expanders
- **ADC Channels**: Analog-to-digital converter channels

## Detected HAT Types

### CAN Bus HATs

**Supported HATs**:
- **MCP2515-based** (PiCAN, PiCAN2, PiCAN3)
  - CAN 2.0B, up to 1 Mbps
  - Detected via: Device tree, SPI bus, CAN interfaces
  
- **MCP2518FD-based** (Custom dual CAN FD HAT)
  - CAN FD, up to 5 Mbps
  - Detected via: Device tree, SPI bus

**Detection Methods**:
1. CAN interfaces in `/sys/class/net/can*`
2. Device tree overlays in `/boot/config.txt`
3. SPI devices in `/sys/bus/spi/devices`

### GPS HATs

**Supported Modules**:
- **MTK3339** (PiCAN with GPS)
- **L76K** (Waveshare)
- **MAX-7Q** (Waveshare)
- Generic GPS modules on UART

**Detection Methods**:
1. UART devices (`/dev/ttyAMA*`, `/dev/ttyUSB*`)
2. I2C scanning (for I2C-based GPS)

### IMU Sensors

**Supported Sensors**:
- **MPU6050/MPU9250** (I2C: 0x68, 0x69)
  - Accelerometer + Gyroscope
  - MPU9250 includes magnetometer
  
- **BNO085** (I2C: 0x4A, 0x4B)
  - 9-axis IMU (accel, gyro, mag)

**Detection Methods**:
- I2C bus scanning (`i2cdetect`)

### GPIO Expanders

**Supported Chips**:
- **MCP23017** (I2C: 0x20-0x27)
  - 16 GPIO pins per chip
  - Can stack multiple chips

**Detection Methods**:
- I2C bus scanning

### ADC Boards

**Supported Boards**:
- **ADS1115** (I2C: 0x48-0x4B)
  - 4 channels, 16-bit resolution

**Detection Methods**:
- I2C bus scanning

## Configuration Examples

### Base Model Configuration

**Hardware**:
- Raspberry Pi 5
- PiCAN with GPS, Gyro, Accelerometer HAT

**Detected**:
```
Platform: Raspberry Pi 5 (1x CAN, GPS, IMU)
CAN Channels: ['can0']
GPS: Available
IMU: Available
GPIO Pins: 40
ADC Channels: 0 (via separate ADC HAT if needed)
```

### Pro Model Configuration

**Hardware**:
- Raspberry Pi 5
- PiCAN3 CAN HAT (bottom)
- PiCAN with GPS/IMU HAT (top)

**Detected**:
```
Platform: Raspberry Pi 5 (2x CAN, GPS, IMU)
CAN Channels: ['can0', 'can1']
GPS: Available
IMU: Available
GPIO Pins: 40
ADC Channels: 0
```

### Ultimate Model Configuration

**Hardware**:
- Raspberry Pi 5
- Custom Dual CAN FD HAT
- GPS HAT
- IMU Sensor
- MCP23017 GPIO Expander
- ADS1115 ADC

**Detected**:
```
Platform: Raspberry Pi 5 (2x CAN, GPS, IMU)
CAN Channels: ['can0', 'can1']
CAN Bitrate: 5000000 (CAN FD)
GPS: Available
IMU: Available
GPIO Pins: 56 (40 base + 16 expander)
ADC Channels: 4
```

## Manual HAT Detection

You can manually check detected HATs:

```python
from core.hat_detector import HATDetector

hat_config = HATDetector.detect_all_hats()

print(f"CAN HATs: {len(hat_config.can_hats)}")
print(f"GPS HATs: {len(hat_config.gps_hats)}")
print(f"IMU Sensors: {len(hat_config.imu_sensors)}")
print(f"GPIO Expanders: {len(hat_config.gpio_expanders)}")
print(f"ADC Boards: {len(hat_config.adc_boards)}")
print(f"Total CAN Buses: {hat_config.total_can_buses}")
```

## Troubleshooting

### HAT Not Detected

1. **Check device tree overlay**:
   ```bash
   cat /boot/config.txt | grep dtoverlay
   ```

2. **Check CAN interfaces**:
   ```bash
   ip link show | grep can
   ```

3. **Check I2C devices**:
   ```bash
   i2cdetect -y 1
   ```

4. **Check SPI devices**:
   ```bash
   ls /sys/bus/spi/devices/
   ```

5. **Check kernel messages**:
   ```bash
   dmesg | grep -i can
   dmesg | grep -i i2c
   dmesg | grep -i spi
   ```

### CAN HAT Not Working

1. **Enable device tree overlay** in `/boot/config.txt`:
   ```
   dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
   ```

2. **Reboot**:
   ```bash
   sudo reboot
   ```

3. **Bring up CAN interface**:
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   ```

### GPS Not Detected

1. **Check UART device**:
   ```bash
   ls -l /dev/ttyAMA* /dev/ttyUSB*
   ```

2. **Test GPS communication**:
   ```bash
   cat /dev/ttyAMA0  # Replace with your GPS device
   ```

3. **Check permissions**:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

### IMU Not Detected

1. **Check I2C bus**:
   ```bash
   i2cdetect -y 1
   ```

2. **Verify I2C is enabled**:
   ```bash
   sudo raspi-config
   # Interface Options -> I2C -> Enable
   ```

3. **Check wiring** (SDA/SCL connections)

## Adding Support for New HATs

To add support for a new HAT:

1. **Identify detection method**:
   - Device tree overlay?
   - I2C address?
   - SPI device?
   - UART device?

2. **Update `hat_detector.py`**:
   - Add detection logic in appropriate method
   - Add HAT identification

3. **Update capabilities**:
   - Document HAT capabilities
   - Add to appropriate detection method

4. **Test**:
   - Verify detection works
   - Test functionality

## Best Practices

1. **Stack HATs carefully**:
   - Use different SPI/I2C buses
   - Ensure GPIO passthrough headers
   - Check power requirements

2. **Document your configuration**:
   - Note which HATs are installed
   - Document any custom wiring

3. **Test after changes**:
   - Reboot after adding HATs
   - Verify detection
   - Test functionality

## References

- [Raspberry Pi 5 GPIO Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Device Tree Overlays](https://www.raspberrypi.com/documentation/computers/configuration.html#device-tree-overlays)
- [I2C Configuration](https://www.raspberrypi.com/documentation/computers/configuration.html#enabling-i2c)
- [SPI Configuration](https://www.raspberrypi.com/documentation/computers/configuration.html#enabling-spi)



