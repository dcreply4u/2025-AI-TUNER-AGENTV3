# Raspberry Pi 5 HAT Setup Guide

**For when your HATs arrive from Amazon!**

## Quick Start

When you receive your CAN bus HAT and other HATs:

### 1. Physical Installation

1. **Power down the Pi 5** (if running)
2. **Install the HAT** on the GPIO header
3. **Ensure proper alignment** (pin 1 to pin 1)
4. **Secure with standoffs** if provided
5. **Power on the Pi 5**

### 2. Run CAN HAT Setup Script

SSH into your Pi 5 and run:

```bash
cd ~/AITUNER/AI-TUNER-AGENT
chmod +x scripts/setup_can_hat_pi5.sh
./scripts/setup_can_hat_pi5.sh
```

The script will:
- ✅ Detect your CAN HAT type
- ✅ Configure device tree overlay
- ✅ Install CAN utilities
- ✅ Set up auto-start service
- ✅ Enable SPI interface

### 3. Reboot

```bash
sudo reboot
```

### 4. Test HAT Detection

After reboot:

```bash
cd ~/AITUNER/AI-TUNER-AGENT
chmod +x scripts/test_hats_pi5.sh
./scripts/test_hats_pi5.sh
```

## Supported CAN HATs

### MCP2515-based HATs
- **PiCAN** (Waveshare)
- **PiCAN2** (Waveshare)
- **PiCAN3** (Waveshare)
- **Any MCP2515-based HAT**

**Specifications:**
- CAN 2.0B standard
- Up to 1 Mbps bitrate
- SPI interface

### MCP2518FD-based HATs
- **Custom dual CAN FD HATs**
- **MCP2518FD-based HATs**

**Specifications:**
- CAN FD standard
- Up to 5 Mbps bitrate
- SPI interface

## Manual Configuration

If the setup script doesn't work, you can configure manually:

### 1. Enable SPI

Edit `/boot/firmware/config.txt` (or `/boot/config.txt`):

```bash
sudo nano /boot/firmware/config.txt
```

Add or uncomment:
```
dtparam=spi=on
```

### 2. Add CAN Overlay

For MCP2515:
```
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
```

For MCP2518FD:
```
dtoverlay=mcp2518fd-can0,oscillator=40000000,interrupt=25
```

### 3. Reboot

```bash
sudo reboot
```

### 4. Bring Up CAN Interface

After reboot:

```bash
sudo ip link set can0 up type can bitrate 500000
```

### 5. Verify

```bash
ip link show can0
```

Should show: `state UP`

## Testing CAN Bus

### Basic Test

```bash
# Monitor CAN bus (will show all messages)
candump can0

# Send a test message
cansend can0 123#DEADBEEF

# Monitor with specific ID
candump can0 | grep "123"
```

### Python Test

```python
import can

# Create bus
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# Send message
msg = can.Message(arbitration_id=0x123, data=[0xDE, 0xAD, 0xBE, 0xEF])
bus.send(msg)

# Receive message
msg = bus.recv(timeout=1.0)
if msg:
    print(f"Received: ID=0x{msg.arbitration_id:X}, Data={msg.data.hex()}")
```

## Multiple HATs

If you have multiple HATs (CAN + GPS + IMU):

### Stacking Order

1. **Bottom**: CAN HAT (needs direct SPI access)
2. **Top**: GPS/IMU HAT (uses I2C/UART)

### Configuration

Each HAT will be detected automatically. The system supports:
- Multiple CAN buses (can0, can1, etc.)
- GPS on UART
- IMU on I2C
- GPIO expanders on I2C
- ADC boards on I2C

## Troubleshooting

### CAN Interface Not Appearing

1. **Check device tree overlay**:
   ```bash
   cat /boot/firmware/config.txt | grep can
   ```

2. **Check kernel messages**:
   ```bash
   dmesg | grep -i can
   ```

3. **Check SPI is enabled**:
   ```bash
   lsmod | grep spi
   ```

4. **Check SPI devices**:
   ```bash
   ls /sys/bus/spi/devices/
   ```

### CAN Interface Shows But Won't Go UP

1. **Check bitrate** (must match your network):
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   ```

2. **Check for errors**:
   ```bash
   ip -s link show can0
   ```

3. **Try different bitrate**:
   ```bash
   sudo ip link set can0 down
   sudo ip link set can0 up type can bitrate 250000
   ```

### HAT Not Detected by Software

1. **Run detection test**:
   ```bash
   ./scripts/test_hats_pi5.sh
   ```

2. **Check I2C devices** (for GPS/IMU):
   ```bash
   i2cdetect -y 1
   ```

3. **Check UART devices** (for GPS):
   ```bash
   ls -l /dev/ttyAMA* /dev/ttyUSB*
   ```

### Permission Errors

Add user to dialout group (for UART access):
```bash
sudo usermod -a -G dialout $USER
```

Log out and back in for changes to take effect.

## Integration with AI-TUNER-AGENT

Once HATs are detected, the application will:

1. **Auto-detect CAN buses** at startup
2. **Configure CAN channels** automatically
3. **Enable GPS tracking** if GPS HAT detected
4. **Enable IMU sensors** if IMU detected
5. **Show HAT status** in the UI

### Verify Integration

```python
from core.hat_detector import HATDetector
from core.hardware_platform import HardwareDetector

# Check HATs
hat_config = HATDetector.detect_all_hats()
print(f"CAN Buses: {hat_config.total_can_buses}")

# Check hardware config
hw_config = HardwareDetector.detect()
print(f"CAN Channels: {hw_config.can_channels}")
```

## Next Steps After HAT Installation

1. ✅ **Install HAT physically**
2. ✅ **Run setup script**
3. ✅ **Reboot Pi**
4. ✅ **Test detection**
5. ✅ **Test CAN communication**
6. ✅ **Run AI-TUNER-AGENT** - it will auto-detect everything!

## Remote Setup (From Windows)

You can set up HATs remotely:

```powershell
# Run setup script
.\AI-TUNER-AGENT\scripts\run_pi5_command.ps1 -Command "cd ~/AITUNER/AI-TUNER-AGENT && chmod +x scripts/setup_can_hat_pi5.sh && ./scripts/setup_can_hat_pi5.sh"

# After reboot, test detection
.\AI-TUNER-AGENT\scripts\run_pi5_command.ps1 -Command "cd ~/AITUNER/AI-TUNER-AGENT && ./scripts/test_hats_pi5.sh"
```

## Common HAT Configurations

### Base Model
- 1x CAN HAT (MCP2515)
- GPS HAT (optional)
- IMU Sensor (optional)

### Pro Model
- 2x CAN HATs (stacked or dual CAN HAT)
- GPS HAT
- IMU Sensor

### Ultimate Model
- 2x CAN FD HATs
- GPS HAT
- IMU Sensor
- GPIO Expander
- ADC Board

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review kernel messages: `dmesg | tail -50`
3. Check system logs: `journalctl -u can0.service`
4. Verify wiring and power supply

## References

- [CAN Bus Guide](../docs/CAN_BUS_GUIDE.md)
- [HAT Detection Guide](../docs/PI_5_HAT_DETECTION.md)
- [Raspberry Pi 5 GPIO Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)






