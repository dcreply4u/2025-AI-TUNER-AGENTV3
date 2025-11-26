# Hard Drive Setup Guide for Raspberry Pi 5

**Date:** December 2025  
**Status:** ✅ Complete Setup Scripts

---

## Overview

This guide explains how to set up a hard drive on your Raspberry Pi 5 to run the AI Tuner Agent, with automatic synchronization between USB and hard drive.

---

## Setup Process

### Step 1: Setup Hard Drive

Run the setup script to detect, format (if needed), and mount your hard drive:

```bash
cd ~/AITUNER/2025-AI-TUNER-AGENTV3
sudo scripts/setup_hard_drive.sh
```

**What it does:**
- ✅ Detects your hard drive (SATA/USB)
- ✅ Formats it if needed (ext4 or exfat)
- ✅ Mounts it at `/mnt/aituner_hdd`
- ✅ Adds to `/etc/fstab` for auto-mount on boot
- ✅ Creates directory structure

**Default mount point:** `/mnt/aituner_hdd`  
**Project path:** `/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3`

---

### Step 2: Copy Files from USB to Hard Drive

Copy your project files from USB to the hard drive:

```bash
scripts/copy_from_usb_to_hdd.sh
```

**What it does:**
- ✅ Finds your USB device automatically
- ✅ Copies all project files to hard drive
- ✅ Preserves permissions and timestamps
- ✅ Excludes unnecessary files (.git, __pycache__, logs, etc.)
- ✅ Verifies the copy

**Note:** This script will find your USB device automatically. If it can't find it, you can specify the path:
```bash
USB_SOURCE=/media/your_usb/AITUNER scripts/copy_from_usb_to_hdd.sh
```

---

### Step 3: Setup Automatic Sync

Set up bidirectional sync between USB and hard drive:

```bash
sudo scripts/setup_hdd_sync.sh
```

**What it does:**
- ✅ Creates sync script at `/usr/local/bin/aituner_sync.sh`
- ✅ Creates systemd service and timer
- ✅ Syncs every 5 minutes automatically
- ✅ Creates manual sync script for user

**Sync Behavior:**
- **HDD → USB:** Full sync (HDD is source of truth)
- **USB → HDD:** Only newer files (USB updates are merged)

---

### Step 4: Migrate to Run from HDD

Set up the application to run from hard drive:

```bash
scripts/migrate_to_hdd.sh
```

**What it does:**
- ✅ Creates symlink for easy access: `~/AITUNER_HDD`
- ✅ Creates environment setup script
- ✅ Creates launcher script: `run_from_hdd.sh`
- ✅ Creates desktop shortcut (if desktop environment)

---

## Running from Hard Drive

### Method 1: Use Launcher Script

```bash
/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3/run_from_hdd.sh
```

### Method 2: Use Symlink

```bash
cd ~/AITUNER_HDD
python3 demo_safe.py
```

### Method 3: Direct Path

```bash
cd /mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3
python3 demo_safe.py
```

---

## Manual Sync

To manually sync USB and HDD:

```bash
# From the project directory
scripts/sync_usb_hdd.sh

# Or from anywhere
/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3/scripts/sync_usb_hdd.sh
```

---

## Sync Status

### Check Sync Timer Status

```bash
sudo systemctl status aituner-sync.timer
```

### View Sync Logs

```bash
tail -f /var/log/aituner_sync.log
```

### Enable/Disable Auto-Sync

```bash
# Enable
sudo systemctl enable aituner-sync.timer
sudo systemctl start aituner-sync.timer

# Disable
sudo systemctl stop aituner-sync.timer
sudo systemctl disable aituner-sync.timer
```

---

## Directory Structure

After setup, your hard drive will have this structure:

```
/mnt/aituner_hdd/
└── AITUNER/
    └── 2025-AI-TUNER-AGENTV3/    # Project files
        ├── demo_safe.py
        ├── controllers/
        ├── interfaces/
        ├── services/
        ├── ui/
        └── ...
    └── storage/                  # Data storage
        ├── logs/
        │   ├── telemetry/
        │   ├── video/
        │   └── gps/
        └── sessions/
```

---

## Application Integration

The application automatically detects and uses the hard drive:

### Storage Priority

1. **Hard Drive** (if mounted) - Primary storage
2. **USB Drive** (if available) - Backup/portable
3. **Local Disk** (fallback) - If neither available

### Automatic Detection

The `HDDManager` automatically:
- ✅ Detects if hard drive is mounted
- ✅ Provides storage paths for logs and sessions
- ✅ Falls back to USB/local if HDD unavailable
- ✅ Integrates with existing storage system

---

## Troubleshooting

### Hard Drive Not Detected

**Check 1: Device exists**
```bash
lsblk
# Should show your hard drive (sda, sdb, nvme0n1, etc.)
```

**Check 2: Permissions**
```bash
ls -l /mnt/aituner_hdd
# Should be owned by aituner user or your user
```

**Check 3: Mount status**
```bash
mount | grep aituner_hdd
# Should show the mount point
```

### Sync Not Working

**Check 1: Sync service status**
```bash
sudo systemctl status aituner-sync.timer
```

**Check 2: Sync logs**
```bash
sudo tail -f /var/log/aituner_sync.log
```

**Check 3: Manual sync test**
```bash
sudo /usr/local/bin/aituner_sync.sh
```

### Permission Issues

**Fix ownership:**
```bash
sudo chown -R aituner:aituner /mnt/aituner_hdd
# Or if using different user:
sudo chown -R $USER:$USER /mnt/aituner_hdd
```

**Fix permissions:**
```bash
sudo chmod -R 755 /mnt/aituner_hdd
```

---

## Benefits

### Performance
- ✅ **Faster I/O** - Hard drives are faster than USB for large files
- ✅ **Better for video** - Video logging works better on HDD
- ✅ **Lower latency** - Reduced write latency

### Reliability
- ✅ **Always available** - HDD is always connected (no unplugging)
- ✅ **Backup sync** - USB serves as backup/portable copy
- ✅ **Dual storage** - Data in two places

### Convenience
- ✅ **Auto-mount** - Mounts automatically on boot
- ✅ **Auto-sync** - Syncs every 5 minutes
- ✅ **Easy access** - Symlink for quick access

---

## Configuration

### Change Mount Point

Edit the scripts to use a different mount point:
- `setup_hard_drive.sh`: Change `MOUNT_POINT` variable
- `hdd_manager.py`: Change `DEFAULT_MOUNT_POINT`

### Change Sync Interval

Edit `/etc/systemd/system/aituner-sync.timer`:
```ini
[Timer]
OnUnitActiveSec=5min  # Change to desired interval
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart aituner-sync.timer
```

---

## Quick Reference

```bash
# Setup hard drive
sudo scripts/setup_hard_drive.sh

# Copy from USB
scripts/copy_from_usb_to_hdd.sh

# Setup sync
sudo scripts/setup_hdd_sync.sh

# Migrate to HDD
scripts/migrate_to_hdd.sh

# Run from HDD
/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3/run_from_hdd.sh

# Manual sync
scripts/sync_usb_hdd.sh

# Check status
sudo systemctl status aituner-sync.timer
tail -f /var/log/aituner_sync.log
```

---

**Status:** ✅ **Ready to Use!**

Your hard drive is now set up and the application will automatically use it for storage, with automatic sync to USB for backup.

