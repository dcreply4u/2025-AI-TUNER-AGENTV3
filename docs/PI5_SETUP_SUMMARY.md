# Raspberry Pi 5 Setup - File Summary

This document lists all the setup files and scripts prepared for Raspberry Pi 5 setup.

## 📁 Files Created

### Setup Scripts

1. **`scripts/pi5_setup.sh`**
   - System-level setup script
   - Installs dependencies, enables I2C/SPI, configures SSH
   - Run with: `sudo ./scripts/pi5_setup.sh`
   - **Run this first!**

2. **`scripts/pi5_install.sh`**
   - Application installation script
   - Creates virtual environment, installs Python packages
   - Run with: `./scripts/pi5_install.sh`
   - **Run after system setup**

3. **`scripts/pi5_network_setup.sh`**
   - Network configuration helper
   - Configure WiFi, static IP, SSH, test connectivity
   - Run with: `sudo ./scripts/pi5_network_setup.sh`
   - **Optional - for network configuration**

4. **`scripts/test_hardware_detection.py`**
   - Comprehensive hardware detection test
   - Tests platform, HATs, I2C, SPI, CAN, GPIO, USB
   - Run with: `python scripts/test_hardware_detection.py`
   - **Use to verify everything works**

### Documentation

1. **`docs/RASPBERRY_PI_5_SETUP_GUIDE.md`**
   - Complete setup guide (detailed)
   - Step-by-step instructions
   - Troubleshooting section
   - HAT configuration examples

2. **`docs/PI5_QUICK_START.md`**
   - Quick start guide (15 minutes)
   - Fast setup for experienced users
   - Quick reference commands

3. **`docs/PI5_SETUP_SUMMARY.md`** (this file)
   - Overview of all setup files

## 🚀 Quick Setup Order

1. Flash Raspberry Pi OS with SSH enabled
2. Find Pi's IP address
3. SSH to Pi: `ssh pi@<ip-address>`
4. Clone repository: `cd /opt && git clone <repo> ai-tuner-agent`
5. Run system setup: `sudo ./scripts/pi5_setup.sh`
6. Reboot if needed: `sudo reboot`
7. Run app install: `./scripts/pi5_install.sh`
8. Test hardware: `python scripts/test_hardware_detection.py`
9. Run app: `python demo.py`

## 📋 What Each Script Does

### pi5_setup.sh
- Updates system packages
- Installs Python 3, pip, build tools
- Installs CAN utilities, I2C/SPI tools
- Enables I2C and SPI interfaces
- Enables SSH
- Creates application directory

### pi5_install.sh
- Creates Python virtual environment
- Installs all Python dependencies
- Creates necessary directories (logs, data, backups)
- Optionally creates systemd service

### pi5_network_setup.sh
- Configure WiFi connection
- Set static IP address
- Enable/configure SSH
- Show network information
- Test network connectivity

### test_hardware_detection.py
- Tests platform detection (should detect Pi 5)
- Tests HAT detection (CAN, GPS, GPIO)
- Tests I2C device detection
- Tests SPI device detection
- Tests CAN interface detection
- Tests GPIO access
- Tests USB device detection

## 🔧 Setting Execute Permissions

When you copy these files to the Pi, make them executable:

```bash
chmod +x scripts/pi5_setup.sh
chmod +x scripts/pi5_install.sh
chmod +x scripts/pi5_network_setup.sh
chmod +x scripts/test_hardware_detection.py
```

Or all at once:
```bash
chmod +x scripts/*.sh scripts/*.py
```

## 📝 Notes

- Scripts are designed for Raspberry Pi OS (64-bit)
- Some scripts require `sudo` (system setup)
- Virtual environment is created at `/opt/ai-tuner-agent/venv`
- Application directory is `/opt/ai-tuner-agent`
- All scripts include error handling and user feedback

## 🆘 Need Help?

- See `RASPBERRY_PI_5_SETUP_GUIDE.md` for detailed instructions
- See `PI5_QUICK_START.md` for fast setup
- Check troubleshooting sections in the guides
- Run `test_hardware_detection.py` to diagnose issues

---

**Ready to set up your Pi 5?** Start with `PI5_QUICK_START.md` for a fast setup, or `RASPBERRY_PI_5_SETUP_GUIDE.md` for detailed instructions.



