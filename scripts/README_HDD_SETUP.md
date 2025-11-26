# Quick Start: Hard Drive Setup

**For Raspberry Pi 5**

---

## Complete Setup (Run in Order)

```bash
# 1. Setup hard drive (detect, format, mount)
sudo scripts/setup_hard_drive.sh

# 2. Copy files from USB to hard drive
scripts/copy_from_usb_to_hdd.sh

# 3. Setup automatic sync (USB <-> HDD)
sudo scripts/setup_hdd_sync.sh

# 4. Migrate to run from HDD
scripts/migrate_to_hdd.sh
```

---

## Run from Hard Drive

After setup, run from HDD:

```bash
# Option 1: Use launcher
/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3/run_from_hdd.sh

# Option 2: Use symlink
cd ~/AITUNER_HDD
python3 demo_safe.py

# Option 3: Direct path
cd /mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3
python3 demo_safe.py
```

---

## Manual Sync

```bash
# Sync USB <-> HDD manually
scripts/sync_usb_hdd.sh
```

---

## Check Status

```bash
# Check if HDD is mounted
mount | grep aituner_hdd

# Check sync service
sudo systemctl status aituner-sync.timer

# View sync logs
tail -f /var/log/aituner_sync.log
```

---

## Troubleshooting

**HDD not detected?**
```bash
lsblk  # List all block devices
sudo dmesg | tail  # Check kernel messages
```

**Permission issues?**
```bash
sudo chown -R aituner:aituner /mnt/aituner_hdd
```

**Sync not working?**
```bash
sudo systemctl restart aituner-sync.timer
sudo /usr/local/bin/aituner_sync.sh  # Manual test
```

---

**That's it!** Your application will now run from the hard drive with automatic sync to USB.

