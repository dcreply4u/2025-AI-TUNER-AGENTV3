# Raspberry Pi 5 Immediate Setup Guide

**Quick setup for Pi 5 with USB drive connected**

## Step 1: Connect to Your Pi 5

### Option A: SSH from Windows (Recommended)

1. **Find your Pi's IP address:**
   - If Pi is connected to WiFi/Ethernet, check your router's admin panel
   - Or from Pi directly (if you have keyboard/monitor): `hostname -I`

2. **Open PowerShell on Windows:**
   ```powershell
   ssh pi@<pi-ip-address>
   # or
   ssh <your-username>@<pi-ip-address>
   ```

3. **If SSH is not enabled**, enable it:
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

### Option B: Direct Access (Keyboard/Monitor)

If you have keyboard and monitor connected to Pi:
- Just open terminal on the Pi

---

## Step 2: Check USB Drive

Once connected to Pi, check if USB drive is detected:

```bash
# List USB devices
lsblk

# Check mounted drives
df -h

# Check USB mount points
ls -la /media/
```

**Expected output:** You should see your USB drive listed (usually as `/dev/sda1` or similar, mounted at `/media/pi/...`)

---

## Step 3: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/dcreply4u/ai-tuner-agent.git AI-TUNER-AGENT

# Or if you already have it, navigate to it
cd AI-TUNER-AGENT
```

---

## Step 4: Quick Setup Script

Run the automated setup:

```bash
cd ~/AI-TUNER-AGENT

# Make scripts executable
chmod +x scripts/*.sh

# Run Pi 5 setup (installs dependencies, enables interfaces)
sudo ./scripts/pi5_setup.sh
```

**This will:**
- Update system packages
- Install Python 3 and pip
- Install CAN utilities
- Enable I2C/SPI interfaces
- Install Python dependencies

---

## Step 5: Test USB Drive Detection

```bash
cd ~/AI-TUNER-AGENT
source venv/bin/activate  # If virtual environment was created

# Test USB detection
python3 -c "
from services.usb_manager import USBManager
manager = USBManager()
devices = manager.scan_for_devices()
print(f'Found {len(devices)} USB device(s):')
for dev in devices:
    print(f'  - {dev.label} at {dev.mount_point} ({dev.size_gb:.1f}GB)')
"
```

---

## Step 6: Test Hardware Detection

```bash
# Test Pi 5 detection
python3 scripts/test_hardware_detection.py
```

**Expected output:**
```
Detected Platform: raspberry_pi_5
✅ Raspberry Pi 5 detected correctly!
```

---

## Step 7: Configure USB Drive for Logging

The USB manager will automatically detect and set up your USB drive. To manually configure:

```bash
python3 -c "
from services.usb_manager import USBManager
from pathlib import Path

manager = USBManager(auto_setup=True)

# Scan for devices
devices = manager.scan_for_devices()
if devices:
    print(f'USB drive detected: {devices[0].label}')
    print(f'Mount point: {devices[0].mount_point}')
    
    # Get session path (creates directory structure)
    session_path = manager.get_session_path()
    print(f'Session directory: {session_path}')
    
    # Get logs path
    logs_path = manager.get_logs_path('telemetry')
    print(f'Telemetry logs: {logs_path}')
else:
    print('No USB drive detected')
"
```

---

## Step 8: Run the Application

```bash
cd ~/AI-TUNER-AGENT
source venv/bin/activate  # If using venv

# Run demo
python3 demo.py

# Or run main application
python3 start_ai_tuner.py
```

---

## Quick Commands Reference

```bash
# Check Pi 5 hardware info
cat /proc/cpuinfo | grep Model

# Check USB devices
lsblk
df -h

# Check CAN interfaces (if HAT installed)
ip link show

# Check network
hostname -I

# View logs
tail -f logs/ai_tuner.log

# Check if USB drive is mounted
mount | grep /media
```

---

## Troubleshooting

### USB Drive Not Detected

1. **Check if mounted:**
   ```bash
   lsblk
   df -h
   ```

2. **Manually mount (if needed):**
   ```bash
   sudo mkdir -p /media/usb
   sudo mount /dev/sda1 /media/usb
   ```

3. **Check permissions:**
   ```bash
   sudo chown -R $USER:$USER /media/usb
   ```

### Can't SSH to Pi

1. **Enable SSH:**
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

2. **Check IP address:**
   ```bash
   hostname -I
   ```

3. **Check firewall:**
   ```bash
   sudo ufw status
   ```

### Import Errors

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Next Steps

1. **Configure CAN HAT** (if you have one)
2. **Set up auto-start** on boot
3. **Configure remote access**
4. **Test data logging to USB drive**

See full guide: [RASPBERRY_PI_5_SETUP_GUIDE.md](RASPBERRY_PI_5_SETUP_GUIDE.md)

