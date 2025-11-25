# Raspberry Pi 5 Fresh Install Guide

**Complete guide for setting up a brand new Raspberry Pi 5 with no OS**

## Step 1: Download Raspberry Pi Imager

1. Go to: https://www.raspberrypi.com/software/
2. Download **Raspberry Pi Imager** for Windows
3. Install it on your Windows computer

---

## Step 2: Prepare SD Card

1. Insert your microSD card into your computer (via adapter if needed)
2. **IMPORTANT:** Make sure it's at least 32GB (64GB+ recommended)
3. Format it if needed (Windows will prompt you)

---

## Step 3: Flash Raspberry Pi OS

1. **Open Raspberry Pi Imager**

2. **Click "Choose OS"** and select:
   - **Raspberry Pi OS (64-bit)** ← Recommended
   - Or **Raspberry Pi OS Lite (64-bit)** if you don't need desktop

3. **Click "Choose Storage"** and select your microSD card

4. **Click the gear icon (⚙️)** to configure settings:

   **IMPORTANT SETTINGS:**
   
   - ✅ **Enable SSH** - Check this box!
   - ✅ **Set username and password** - Remember these!
   - ✅ **Configure WiFi** (if using WiFi):
     - SSID: Your WiFi network name
     - Password: Your WiFi password
     - Country: Your country code
   - ✅ **Set locale settings**:
     - Timezone: Your timezone
     - Keyboard layout: Your keyboard

5. **Click "Save"**

6. **Click "Write"** and wait for it to complete (5-10 minutes)

7. **Click "Continue"** when done

---

## Step 4: Insert SD Card and Boot Pi

1. **Safely eject** the SD card from your computer
2. **Insert SD card** into your Raspberry Pi 5 (slot on bottom)
3. **Connect power supply** (USB-C, 5V 5A recommended)
4. **Wait for boot** - Green LED will flash, then stay on when ready
5. **Wait 1-2 minutes** for first boot to complete

---

## Step 5: Find Your Pi's IP Address

### Option A: From Router (Easiest)

1. Log into your router's admin panel (usually http://192.168.1.1)
2. Look for device named "raspberrypi" or your hostname
3. Note the IP address (e.g., 192.168.1.100)

### Option B: Network Scan from Windows

Open PowerShell and run:

```powershell
# Scan your local network
arp -a | findstr "192.168"

# Or use nmap if installed
nmap -sn 192.168.1.0/24
```

### Option C: From Pi Directly (if you have keyboard/monitor)

Connect keyboard and monitor to Pi, then:

```bash
hostname -I
```

---

## Step 6: Connect via SSH

From your Windows PowerShell:

```powershell
# Replace with your Pi's IP address
ssh pi@192.168.1.100

# Or if you set a custom username:
ssh yourusername@192.168.1.100
```

**First time connection:**
- Type "yes" when asked about host key
- Enter your password (the one you set in Imager)

---

## Step 7: Update System

Once connected via SSH:

```bash
# Update package list
sudo apt update

# Upgrade system
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git python3 python3-pip python3-venv
```

---

## Step 8: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/dcreply4u/ai-tuner-agent.git AI-TUNER-AGENT

# Navigate into it
cd AI-TUNER-AGENT
```

---

## Step 9: Run Setup Script

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run Pi 5 setup (this will take a few minutes)
sudo ./scripts/pi5_setup.sh
```

**This script will:**
- Install all dependencies
- Enable I2C/SPI interfaces (needed for HATs)
- Install CAN utilities
- Set up Python environment
- Configure system settings

**After setup completes, reboot:**
```bash
sudo reboot
```

**Wait 30 seconds, then SSH back in:**
```bash
ssh pi@<pi-ip-address>
cd ~/AI-TUNER-AGENT
```

---

## Step 10: Test USB Drive

```bash
# Check if USB drive is detected
lsblk

# Check mounted drives
df -h

# List USB mount points
ls -la /media/
```

**If USB drive is not mounted automatically:**
```bash
# Create mount point
sudo mkdir -p /media/usb

# Find your USB device (usually /dev/sda1)
sudo fdisk -l

# Mount it (replace /dev/sda1 with your device)
sudo mount /dev/sda1 /media/usb

# Set permissions
sudo chown -R $USER:$USER /media/usb
```

---

## Step 11: Test Hardware Detection

```bash
cd ~/AI-TUNER-AGENT

# Activate virtual environment (if created)
source venv/bin/activate

# Test Pi 5 detection
python3 scripts/test_hardware_detection.py
```

**Expected output:**
```
Detected Platform: raspberry_pi_5
✅ Raspberry Pi 5 detected correctly!
```

---

## Step 12: Test USB Manager

```bash
python3 -c "
from services.usb_manager import USBManager

manager = USBManager(auto_setup=True)
devices = manager.scan_for_devices()

print(f'Found {len(devices)} USB device(s):')
for dev in devices:
    print(f'  - {dev.label} at {dev.mount_point} ({dev.size_gb:.1f}GB)')
    
if devices:
    session_path = manager.get_session_path()
    print(f'\nSession directory created: {session_path}')
"
```

---

## Step 13: Run Application

```bash
cd ~/AI-TUNER-AGENT
source venv/bin/activate  # If using venv

# Run demo
python3 demo.py

# Or run main application
python3 start_ai_tuner.py
```

---

## Troubleshooting

### Can't Find Pi IP Address

1. **Check if Pi is connected to network:**
   - WiFi: Check if WiFi LED is on
   - Ethernet: Check if cable is connected

2. **Try connecting keyboard/monitor:**
   ```bash
   hostname -I
   ```

3. **Check router DHCP table** for new device

### SSH Connection Refused

1. **Enable SSH on Pi:**
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

2. **Check if SSH is running:**
   ```bash
   sudo systemctl status ssh
   ```

### USB Drive Not Detected

1. **Check if USB is plugged in securely**

2. **Check kernel messages:**
   ```bash
   dmesg | tail -20
   ```

3. **Manually mount:**
   ```bash
   sudo mkdir -p /media/usb
   sudo mount /dev/sda1 /media/usb
   sudo chown -R $USER:$USER /media/usb
   ```

### Import Errors

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Quick Reference Commands

```bash
# Check Pi model
cat /proc/cpuinfo | grep Model

# Check IP address
hostname -I

# Check USB devices
lsblk
df -h

# Check CAN interfaces (if HAT installed)
ip link show

# View logs
tail -f logs/ai_tuner.log

# Check system info
uname -a
```

---

## Next Steps After Setup

1. **Configure CAN HAT** (if you have one)
   - See [RASPBERRY_PI_5_SETUP_GUIDE.md](RASPBERRY_PI_5_SETUP_GUIDE.md#hat-configuration)

2. **Set up auto-start on boot**
   - Create systemd service

3. **Configure remote access**
   - Set up VPN or port forwarding if needed

4. **Test data logging to USB drive**
   - Run a test session and verify files are saved

---

**For detailed setup, see:** [RASPBERRY_PI_5_SETUP_GUIDE.md](RASPBERRY_PI_5_SETUP_GUIDE.md)

