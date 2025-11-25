# Raspberry Pi 5 Setup Guide for AI Tuner Agent

Complete guide for setting up a Raspberry Pi 5 to run the AI Tuner Agent application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Pi Setup](#initial-pi-setup)
3. [Network Configuration](#network-configuration)
4. [Application Installation](#application-installation)
5. [Hardware Detection Testing](#hardware-detection-testing)
6. [HAT Configuration](#hat-configuration)
7. [Remote Access Setup](#remote-access-setup)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Raspberry Pi 5
- MicroSD card (32GB+ recommended, Class 10 or better)
- Power supply (USB-C, 5V 5A recommended)
- Network connection (WiFi or Ethernet)
- Optional: HATs (CAN, GPS, GPIO expanders)

---

## Initial Pi Setup

### 1. Flash Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert microSD card into your computer
3. Open Raspberry Pi Imager
4. Choose OS: **Raspberry Pi OS (64-bit)** (recommended)
5. Click the gear icon to configure:
   - **Enable SSH**: ✅ (important for remote access)
   - **Set username and password**
   - **Configure WiFi** (optional, can do later)
   - **Set locale settings**
6. Click "Write" and wait for completion

### 2. First Boot

1. Insert microSD card into Pi 5
2. Connect power supply
3. Wait for boot (LED will indicate status)
4. If WiFi was configured, the Pi should connect automatically

### 3. Find Your Pi's IP Address

**Option A: From the Pi (if you have keyboard/monitor)**
```bash
hostname -I
```

**Option B: From your router**
- Log into your router's admin panel
- Look for device named "raspberrypi" or your hostname

**Option C: Network scan (from your computer)**
```bash
# Windows PowerShell
arp -a | findstr "192.168"

# Linux/Mac
nmap -sn 192.168.1.0/24
```

---

## Network Configuration

### Quick Setup Script

Run the network setup script on the Pi:

```bash
cd /path/to/AI-TUNER-AGENT
sudo chmod +x scripts/pi5_network_setup.sh
sudo ./scripts/pi5_network_setup.sh
```

### Manual WiFi Setup

1. **Edit wpa_supplicant:**
   ```bash
   sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
   ```

2. **Add network:**
   ```conf
   network={
       ssid="YourNetworkName"
       psk="YourPassword"
   }
   ```

3. **Restart networking:**
   ```bash
   sudo wpa_cli -i wlan0 reconfigure
   # or
   sudo systemctl restart networking
   ```

### Enable SSH (if not already enabled)

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Test Network Connection

```bash
ping -c 3 8.8.8.8  # Test internet
ping -c 3 google.com  # Test DNS
```

---

## Application Installation

### Step 1: System Setup

Run the system setup script (installs dependencies, enables interfaces):

```bash
cd /path/to/AI-TUNER-AGENT
sudo chmod +x scripts/pi5_setup.sh
sudo ./scripts/pi5_setup.sh
```

**What this does:**
- Updates system packages
- Installs Python 3, pip, and essential tools
- Installs CAN utilities, I2C/SPI tools
- Enables I2C and SPI interfaces
- Configures SSH
- Creates application directory

**Note:** You may need to reboot after enabling I2C/SPI:
```bash
sudo reboot
```

### Step 2: Clone Repository (if not already cloned)

```bash
cd /opt
sudo git clone <repository-url> ai-tuner-agent
sudo chown -R $USER:$USER ai-tuner-agent
cd ai-tuner-agent
```

### Step 3: Install Application

Run the installation script:

```bash
chmod +x scripts/pi5_install.sh
./scripts/pi5_install.sh
```

**For development mode:**
```bash
./scripts/pi5_install.sh --dev
```

**What this does:**
- Creates/activates Python virtual environment
- Installs all Python dependencies
- Creates necessary directories
- Optionally creates systemd service

### Step 4: Verify Installation

```bash
# Activate virtual environment
source /opt/ai-tuner-agent/venv/bin/activate

# Test import
python -c "from core.hardware_platform import detect_platform; print(detect_platform())"

# Should output: raspberry_pi_5
```

---

## Hardware Detection Testing

### Run Hardware Detection Test

```bash
cd /opt/ai-tuner-agent
source venv/bin/activate
python scripts/test_hardware_detection.py
```

**This will test:**
- ✅ Platform detection (should detect Pi 5)
- ✅ HAT detection (CAN, GPS, GPIO)
- ✅ I2C devices
- ✅ SPI devices
- ✅ CAN interfaces
- ✅ GPIO access
- ✅ USB devices

### Expected Output

```
============================================================
Raspberry Pi 5 Hardware Detection Test
============================================================

============================================================
Testing Platform Detection
============================================================
Detected Platform: raspberry_pi_5
Platform Config:
  platform: raspberry_pi_5
  has_gpio: True
  has_i2c: True
  has_spi: True
  can_interfaces: []
✅ Raspberry Pi 5 detected correctly!

============================================================
Testing HAT Detection
============================================================
Detected HATs: 0
ℹ️  No HATs detected (this is normal if no HATs are installed)
...
```

---

## HAT Configuration

### CAN HAT Setup

**For MCP2515 CAN HAT:**

1. **Edit config.txt:**
   ```bash
   sudo nano /boot/firmware/config.txt
   # or
   sudo nano /boot/config.txt
   ```

2. **Add overlay:**
   ```conf
   dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
   ```

3. **Enable CAN interface:**
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   ```

4. **Test:**
   ```bash
   # Send test message
   cansend can0 123#DEADBEEF
   
   # Monitor
   candump can0
   ```

**For MCP2518FD CAN HAT:**

```conf
dtoverlay=mcp2518fd-can0
```

### GPS HAT Setup

**For I2C GPS (e.g., NEO-6M with I2C adapter):**

1. **Enable I2C** (should already be enabled)
2. **Check I2C address:**
   ```bash
   sudo i2cdetect -y 1
   ```

3. **Install GPS libraries:**
   ```bash
   pip install pynmea2 gpsd-py3
   ```

### GPIO Expander HAT Setup

**For MCP23017 GPIO Expander:**

1. **Enable I2C** (should already be enabled)
2. **Check I2C address:**
   ```bash
   sudo i2cdetect -y 1
   # MCP23017 typically at 0x20-0x27
   ```

3. **Install library:**
   ```bash
   pip install adafruit-circuitpython-mcp230xx
   ```

---

## Remote Access Setup

### SSH Access

**From Windows:**
```powershell
ssh pi@<pi-ip-address>
# or
ssh username@<pi-ip-address>
```

**From Linux/Mac:**
```bash
ssh pi@<pi-ip-address>
```

### File Transfer (SCP)

**From Windows (PowerShell):**
```powershell
scp file.txt pi@<pi-ip>:/home/pi/
```

**From Linux/Mac:**
```bash
scp file.txt pi@<pi-ip>:/home/pi/
```

### VS Code Remote Development

1. Install "Remote - SSH" extension in VS Code
2. Press `F1` → "Remote-SSH: Connect to Host"
3. Enter: `pi@<pi-ip-address>`
4. Enter password when prompted
5. Open folder: `/opt/ai-tuner-agent`

### Running Commands Remotely

**Single command:**
```bash
ssh pi@<pi-ip> "cd /opt/ai-tuner-agent && python demo.py"
```

**Interactive session:**
```bash
ssh pi@<pi-ip>
cd /opt/ai-tuner-agent
source venv/bin/activate
python demo.py
```

---

## Running the Application

### Development Mode

```bash
cd /opt/ai-tuner-agent
source venv/bin/activate
python demo.py
```

### Production Mode (with systemd)

If you created the systemd service:

```bash
# Enable auto-start on boot
sudo systemctl enable ai-tuner-agent

# Start service
sudo systemctl start ai-tuner-agent

# Check status
sudo systemctl status ai-tuner-agent

# View logs
sudo journalctl -u ai-tuner-agent -f
```

### Manual Service Management

```bash
# Start
sudo systemctl start ai-tuner-agent

# Stop
sudo systemctl stop ai-tuner-agent

# Restart
sudo systemctl restart ai-tuner-agent

# Disable auto-start
sudo systemctl disable ai-tuner-agent
```

---

## Troubleshooting

### Pi 5 Not Detected

**Issue:** Platform detection returns wrong platform

**Solution:**
1. Check `/proc/device-tree/model`:
   ```bash
   cat /proc/device-tree/model
   # Should show: Raspberry Pi 5 Model B Rev 1.0
   ```

2. Verify hardware detection code is up to date

### HATs Not Detected

**Issue:** HATs not showing up in detection

**Solutions:**
1. **Check I2C/SPI are enabled:**
   ```bash
   lsmod | grep i2c
   lsmod | grep spi
   ```

2. **Check device tree overlays:**
   ```bash
   vcgencmd get_config int | grep -i can
   ```

3. **Check I2C devices:**
   ```bash
   sudo i2cdetect -y 1
   ```

4. **Check SPI devices:**
   ```bash
   ls -la /dev/spi*
   ```

### CAN Interface Not Working

**Issue:** CAN interface not appearing

**Solutions:**
1. **Verify overlay is loaded:**
   ```bash
   dtoverlay -l | grep can
   ```

2. **Check interface exists:**
   ```bash
   ip link show
   # Should see can0 or similar
   ```

3. **Manually bring up interface:**
   ```bash
   sudo ip link set can0 up type can bitrate 500000
   ```

4. **Check for errors:**
   ```bash
   dmesg | grep -i can
   ```

### Network Issues

**Issue:** Can't SSH to Pi

**Solutions:**
1. **Check SSH is running:**
   ```bash
   sudo systemctl status ssh
   ```

2. **Check firewall:**
   ```bash
   sudo ufw status
   # If enabled, allow SSH:
   sudo ufw allow ssh
   ```

3. **Check IP address:**
   ```bash
   hostname -I
   ```

4. **Test connectivity:**
   ```bash
   ping <pi-ip-address>
   ```

### Python Import Errors

**Issue:** Module not found errors

**Solutions:**
1. **Activate virtual environment:**
   ```bash
   source /opt/ai-tuner-agent/venv/bin/activate
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Python path:**
   ```bash
   python -c "import sys; print(sys.path)"
   ```

### Permission Issues

**Issue:** Permission denied errors

**Solutions:**
1. **Check file ownership:**
   ```bash
   ls -la /opt/ai-tuner-agent
   ```

2. **Fix ownership:**
   ```bash
   sudo chown -R $USER:$USER /opt/ai-tuner-agent
   ```

3. **Add user to groups:**
   ```bash
   sudo usermod -a -G gpio,i2c,spi $USER
   # Log out and back in for changes to take effect
   ```

---

## Quick Reference

### Useful Commands

```bash
# System info
cat /proc/device-tree/model  # Pi model
uname -a  # Kernel info
vcgencmd measure_temp  # CPU temperature

# Network
hostname -I  # IP address
ip addr show  # All interfaces
ping -c 3 8.8.8.8  # Test internet

# Hardware
i2cdetect -y 1  # I2C devices
ls -la /dev/spi*  # SPI devices
ip link show  # Network/CAN interfaces
lsusb  # USB devices

# Application
cd /opt/ai-tuner-agent
source venv/bin/activate
python demo.py  # Run app
python scripts/test_hardware_detection.py  # Test hardware
```

### File Locations

- Application: `/opt/ai-tuner-agent/`
- Virtual environment: `/opt/ai-tuner-agent/venv/`
- Logs: `/opt/ai-tuner-agent/logs/`
- Data: `/opt/ai-tuner-agent/data/`
- Config: `/boot/firmware/config.txt` or `/boot/config.txt`

---

## Next Steps

1. ✅ Pi 5 is set up and connected to network
2. ✅ Application is installed
3. ✅ Hardware detection is working
4. 🔄 Configure HATs (if applicable)
5. 🔄 Test CAN bus communication
6. 🔄 Test GPS functionality
7. 🔄 Configure GPIO pins
8. 🔄 Run full application test

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs: `/opt/ai-tuner-agent/logs/`
3. Run hardware detection test: `python scripts/test_hardware_detection.py`
4. Check system logs: `journalctl -xe`

For more help, refer to:
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [AI Tuner Agent Documentation](../README.md)

---

**Last Updated:** December 2024



