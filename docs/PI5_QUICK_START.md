# Raspberry Pi 5 Quick Start Guide

**Fast setup guide to get AI Tuner Agent running on your Pi 5 in 15 minutes.**

## Prerequisites Checklist

- [ ] Raspberry Pi 5
- [ ] MicroSD card (32GB+)
- [ ] Power supply (USB-C, 5V 5A)
- [ ] Network connection (WiFi or Ethernet)
- [ ] Computer with SSH client (or keyboard/monitor for Pi)

---

## Step 1: Flash OS (5 minutes)

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS (64-bit)**
3. **IMPORTANT:** Click gear icon and:
   - ✅ Enable SSH
   - ✅ Set username/password
   - ✅ Configure WiFi (optional)
4. Insert SD card into Pi 5 and power on

---

## Step 2: Connect to Pi (2 minutes)

**Find Pi's IP address:**

**Option A:** From router admin panel (look for "raspberrypi")

**Option B:** From Pi (if you have keyboard/monitor):
```bash
hostname -I
```

**Option C:** Network scan from your computer:
```bash
# Windows
arp -a | findstr "192.168"

# Linux/Mac
nmap -sn 192.168.1.0/24
```

**SSH to Pi:**
```bash
ssh pi@<pi-ip-address>
# or
ssh <your-username>@<pi-ip-address>
```

---

## Step 3: Clone Repository (1 minute)

```bash
cd /opt
sudo git clone <your-repo-url> ai-tuner-agent
sudo chown -R $USER:$USER ai-tuner-agent
cd ai-tuner-agent
```

---

## Step 4: Run Setup Scripts (5 minutes)

**System setup (installs dependencies, enables interfaces):**
```bash
sudo chmod +x scripts/pi5_setup.sh
sudo ./scripts/pi5_setup.sh
```

**Reboot if I2C/SPI were enabled:**
```bash
sudo reboot
```

**After reboot, SSH back in and install application:**
```bash
cd /opt/ai-tuner-agent
chmod +x scripts/pi5_install.sh
./scripts/pi5_install.sh
```

---

## Step 5: Test Hardware Detection (2 minutes)

```bash
cd /opt/ai-tuner-agent
source venv/bin/activate
python scripts/test_hardware_detection.py
```

**Expected output:**
```
Detected Platform: raspberry_pi_5
✅ Raspberry Pi 5 detected correctly!
```

---

## Step 6: Run Application (1 minute)

```bash
cd /opt/ai-tuner-agent
source venv/bin/activate
python demo.py
```

**If you get "No display" error**, you can run in headless mode or use X11 forwarding:
```bash
# Headless mode (if supported)
python demo.py --headless

# Or with X11 forwarding (from your computer)
ssh -X pi@<pi-ip> "cd /opt/ai-tuner-agent && source venv/bin/activate && python demo.py"
```

---

## ✅ You're Done!

Your Pi 5 is now set up and running AI Tuner Agent!

---

## Quick Commands Reference

```bash
# Activate environment
source /opt/ai-tuner-agent/venv/bin/activate

# Run app
python demo.py

# Test hardware
python scripts/test_hardware_detection.py

# Check IP
hostname -I

# View logs
tail -f logs/ai_tuner.log
```

---

## Troubleshooting

### Can't SSH to Pi
- Check SSH is enabled: `sudo systemctl status ssh`
- Check IP address: `hostname -I`
- Check firewall: `sudo ufw status`

### Hardware not detected
- Run test script: `python scripts/test_hardware_detection.py`
- Check I2C/SPI enabled: `lsmod | grep i2c`
- Reboot after enabling interfaces

### Import errors
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### Permission errors
- Fix ownership: `sudo chown -R $USER:$USER /opt/ai-tuner-agent`
- Add to groups: `sudo usermod -a -G gpio,i2c,spi $USER`

---

## Next Steps

1. **Configure HATs** (if you have CAN/GPS/GPIO HATs)
   - See [RASPBERRY_PI_5_SETUP_GUIDE.md](RASPBERRY_PI_5_SETUP_GUIDE.md#hat-configuration)

2. **Set up remote access**
   - See [RASPBERRY_PI_5_SETUP_GUIDE.md](RASPBERRY_PI_5_SETUP_GUIDE.md#remote-access-setup)

3. **Configure for production**
   - Create systemd service for auto-start
   - Set up logging
   - Configure backups

---

**For detailed setup, see:** [RASPBERRY_PI_5_SETUP_GUIDE.md](RASPBERRY_PI_5_SETUP_GUIDE.md)



