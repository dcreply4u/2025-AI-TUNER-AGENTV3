# Raspberry Pi 5 - What's Next?

## ✅ Current Status: FULLY SET UP

Your Raspberry Pi 5 is **completely configured** and ready to use:

- ✅ SSH connection working
- ✅ System updated and packages installed
- ✅ AI-TUNER-AGENT repository copied
- ✅ Python environment configured
- ✅ I2C/SPI interfaces enabled
- ✅ USB drive detected and working
- ✅ All dependencies installed

## 🎯 What Can Be Done Next

### 1. **Test the Application** (Ready Now)

```bash
cd ~/AITUNER/AI-TUNER-AGENT
source ~/AITUNER/venv/bin/activate
python3 demo_safe.py
```

### 2. **When Your HATs Arrive** (Today!)

#### Quick Setup Process:

1. **Install HAT physically** on the Pi 5 GPIO header
2. **SSH into Pi** and run:
   ```bash
   cd ~/AITUNER/AI-TUNER-AGENT
   ./scripts/setup_can_hat_pi5.sh
   ```
3. **Reboot**: `sudo reboot`
4. **Test detection**: `./scripts/test_hats_pi5.sh`

#### What the Setup Script Does:
- ✅ Detects your CAN HAT type (MCP2515 or MCP2518FD)
- ✅ Configures device tree overlay
- ✅ Installs CAN utilities (can-utils, python-can)
- ✅ Sets up auto-start service for CAN interface
- ✅ Enables SPI interface
- ✅ Creates backup of config files

#### After HAT Installation:
- The application will **automatically detect** your HATs
- CAN buses will be **auto-configured**
- GPS/IMU sensors will be **auto-detected**
- Everything will work **out of the box**!

### 3. **Additional Configurations** (Optional)

#### Enable Auto-Start on Boot
```bash
# Create systemd service
sudo nano /etc/systemd/system/ai-tuner.service
```

Add:
```ini
[Unit]
Description=AI Tuner Agent
After=network.target

[Service]
Type=simple
User=aituner
WorkingDirectory=/home/aituner/AITUNER/AI-TUNER-AGENT
Environment="PATH=/home/aituner/AITUNER/venv/bin"
ExecStart=/home/aituner/AITUNER/venv/bin/python3 demo_safe.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable ai-tuner.service
sudo systemctl start ai-tuner.service
```

#### Configure Network (if needed)
```bash
sudo raspi-config
# System Options -> Network Options
```

#### Set Up Remote Access
- SSH is already enabled ✅
- You can access via: `ssh aituner@192.168.1.214`

### 4. **Testing & Verification**

#### Test Hardware Detection
```bash
cd ~/AITUNER/AI-TUNER-AGENT
source ~/AITUNER/venv/bin/activate
python3 scripts/test_hardware_detection.py
```

#### Test CAN Bus (after HAT installation)
```bash
# Monitor CAN bus
candump can0

# Send test message
cansend can0 123#DEADBEEF
```

#### Test HAT Detection
```bash
./scripts/test_hats_pi5.sh
```

### 5. **Development & Customization**

#### Update Code
```bash
cd ~/AITUNER/AI-TUNER-AGENT
# Make changes, then test
source ~/AITUNER/venv/bin/activate
python3 demo_safe.py
```

#### Install Additional Packages
```bash
source ~/AITUNER/venv/bin/activate
pip install package_name
```

#### View Logs
```bash
tail -f ~/AITUNER/AI-TUNER-AGENT/logs/demo.log
```

## 📋 HAT Installation Checklist

When your HATs arrive:

- [ ] Power down Pi 5
- [ ] Install CAN HAT on GPIO header
- [ ] Ensure proper alignment (pin 1 to pin 1)
- [ ] Secure with standoffs (if provided)
- [ ] Power on Pi 5
- [ ] SSH into Pi
- [ ] Run `./scripts/setup_can_hat_pi5.sh`
- [ ] Reboot: `sudo reboot`
- [ ] Run `./scripts/test_hats_pi5.sh`
- [ ] Verify CAN interface: `ip link show can0`
- [ ] Test CAN bus: `candump can0`
- [ ] Run AI-TUNER-AGENT: `python3 demo_safe.py`

## 🔧 Useful Commands

### System Information
```bash
# Hardware info
cat /proc/device-tree/model

# Python version
python3 --version

# Installed packages
pip list

# Disk space
df -h

# Memory
free -h

# Network
hostname -I
```

### CAN Bus Commands
```bash
# List CAN interfaces
ip link show | grep can

# Bring up CAN interface
sudo ip link set can0 up type can bitrate 500000

# Bring down CAN interface
sudo ip link set can0 down

# Monitor CAN bus
candump can0

# Send CAN message
cansend can0 123#DEADBEEF

# CAN statistics
ip -s link show can0
```

### HAT Detection
```bash
# Run detection test
cd ~/AITUNER/AI-TUNER-AGENT
./scripts/test_hats_pi5.sh

# Python detection
python3 -c "from core.hat_detector import HATDetector; config = HATDetector.detect_all_hats(); print(f'CAN HATs: {len(config.can_hats)}')"
```

## 📚 Documentation

- **HAT Setup Guide**: `docs/PI5_HAT_SETUP_GUIDE.md`
- **HAT Detection**: `docs/PI_5_HAT_DETECTION.md`
- **CAN Bus Guide**: `docs/CAN_BUS_GUIDE.md`
- **Setup Complete**: `docs/PI5_SETUP_COMPLETE.md`

## 🚀 Ready to Go!

Your Pi 5 is **100% ready**. When your HATs arrive:

1. Install them physically
2. Run the setup script
3. Reboot
4. Start using the application!

Everything else is already configured and waiting! 🎉






