# Seeed reTerminal DM Setup Guide

This guide covers setting up the AI Tuner Agent on the Seeed reTerminal DM panel PC.

## Hardware Overview

The reTerminal DM features:
- **Raspberry Pi Compute Module 4** (CM4) with up to 8GB RAM
- **10.1" touchscreen display** (1280x800 resolution)
- **Dual CAN FD buses** (can0 and can1) - onboard, no HAT required!
- **Wide voltage input** (9-36V DC) with automotive-grade power supply
- **Industrial enclosure** with sealed connectors
- **Physical buttons** (Home, Back, Function)
- **GPIO header** for additional sensors

## Initial Setup

### 1. Flash CM4 with Raspberry Pi OS

The reTerminal DM uses a CM4 module. You'll need to:

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select "Raspberry Pi OS (64-bit)" or "Raspberry Pi OS Lite"
3. Configure WiFi and SSH if needed
4. Flash to a microSD card (or eMMC if your CM4 has it)
5. Insert the CM4 into the reTerminal DM carrier board

### 2. Enable CAN Interfaces

The reTerminal DM has dual CAN FD buses that need to be enabled in the device tree.

#### Option A: Using Seeed's Pre-configured Image

If Seeed provides a pre-configured image, CAN interfaces may already be enabled. Check with:

```bash
ip link show
```

You should see `can0` and `can1` interfaces.

#### Option B: Manual Configuration

If CAN interfaces aren't enabled, you may need to:

1. Edit `/boot/config.txt` and add:
   ```
   dtoverlay=mcp251xfd,spi0-0,interrupt=25
   dtoverlay=mcp251xfd,spi0-1,interrupt=24
   ```

2. Reboot:
   ```bash
   sudo reboot
   ```

3. After reboot, bring up CAN interfaces:
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   sudo ip link set can1 up type can bitrate 500000
   ```

4. Verify:
   ```bash
   ip link show can0
   ip link show can1
   ```

### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install CAN utilities
sudo apt install -y can-utils

# Install system dependencies for PySide6
sudo apt install -y libgl1-mesa-glx libegl1-mesa libxrandr2 libxss1 libasound2

# Install GPIO libraries (if needed)
sudo apt install -y python3-rpi.gpio
```

### 4. Install AI Tuner Agent

```bash
# Clone or copy the AI-TUNER-AGENT directory to the reTerminal DM
cd ~
git clone <your-repo-url> AITUNER
cd AITUNER/AI-TUNER-AGENT

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure CAN Interfaces

The AI Tuner Agent will automatically detect the reTerminal DM and use both CAN channels. You can verify detection:

```bash
python3 -c "from core import get_hardware_config; print(get_hardware_config())"
```

Expected output should show:
```
platform_name='reTerminal DM'
can_channels=['can0', 'can1']
has_onboard_can=True
```

### 6. Test CAN Communication

```bash
# Send a test message on can0
cansend can0 123#DEADBEEF

# Monitor can0 in another terminal
candump can0

# Test can1 similarly
cansend can1 456#CAFEBABE
candump can1
```

## Display Configuration

The reTerminal DM has a 10.1" touchscreen. The AI Tuner UI should automatically detect and use the full screen.

### Touchscreen Calibration (if needed)

If touch input is misaligned:

```bash
# Install calibration tool
sudo apt install -y xinput-calibrator

# Run calibration
xinput_calibrator
```

Follow the on-screen prompts to calibrate.

### Auto-start UI on Boot

To launch the AI Tuner UI automatically:

1. Create a systemd service:

```bash
sudo nano /etc/systemd/system/ai-tuner.service
```

2. Add this content (adjust paths as needed):

```ini
[Unit]
Description=AI Tuner Agent UI
After=graphical.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
WorkingDirectory=/home/pi/AITUNER/AI-TUNER-AGENT
ExecStart=/home/pi/AITUNER/AI-TUNER-AGENT/venv/bin/python -m ui.main
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
```

3. Enable and start:

```bash
sudo systemctl enable ai-tuner.service
sudo systemctl start ai-tuner.service
```

## Physical Buttons

The reTerminal DM has physical buttons that can be mapped:

- **Home button** (GPIO5) - Can be used to return to main screen
- **Back button** (GPIO6) - Can be used for navigation
- **Function button** (GPIO13) - Can be used for quick actions

Button handling can be added to the UI in future updates.

## Power Management

The reTerminal DM has built-in power management. The AI Tuner Agent can monitor:

- Input voltage (9-36V DC)
- Power consumption
- Battery backup status (if equipped)

## Troubleshooting

### CAN Interfaces Not Showing

1. Check if SPI is enabled:
   ```bash
   lsmod | grep spi
   ```

2. Check device tree overlays:
   ```bash
   vcgencmd get_config int | grep -i can
   ```

3. Check kernel messages:
   ```bash
   dmesg | grep -i can
   ```

### Display Not Working

1. Check if display is detected:
   ```bash
   xrandr
   ```

2. Check touchscreen:
   ```bash
   xinput list
   ```

### Performance Issues

The reTerminal DM uses a CM4, which has good performance. If you experience slowdowns:

1. Ensure adequate cooling (the reTerminal DM has built-in fan)
2. Check CPU temperature:
   ```bash
   vcgencmd measure_temp
   ```
3. Monitor resource usage:
   ```bash
   htop
   ```

## Next Steps

1. Connect your vehicle's CAN bus to the reTerminal DM's CAN0 or CAN1 port
2. Configure your DBC file in `config.py` or via environment variables
3. Launch the UI: `python -m ui.main`
4. Start logging telemetry and enjoy the AI-powered insights!

## Support

For reTerminal DM specific issues, check:
- [Seeed reTerminal DM Documentation](https://wiki.seeedstudio.com/reTerminal-DM/)
- [Seeed Community Forum](https://forum.seeedstudio.com/)

For AI Tuner Agent issues, check the main project documentation.

