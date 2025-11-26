#!/bin/bash
# Manual sync script for USB <-> HDD synchronization
# Can be run by user (with sudo for system sync script)

set -e

echo "=========================================="
echo "USB <-> HDD Sync"
echo "=========================================="
echo ""

# Check if system sync script exists
if [ -f "/usr/local/bin/aituner_sync.sh" ]; then
    echo "Running system sync script..."
    sudo /usr/local/bin/aituner_sync.sh
    echo ""
    echo "✅ Sync complete!"
    echo "Check /var/log/aituner_sync.log for details"
    exit 0
fi

# Fallback: Manual sync if system script doesn't exist
echo "System sync script not found, running manual sync..."
echo ""

USB_PATH=""
HDD_PATH="/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3"

# Find USB device
for usb_path in "/media/aituner/AITUNER/2025-AI-TUNER-AGENTV3" "/media/$USER/AITUNER/2025-AI-TUNER-AGENTV3" "/mnt/usb/2025-AI-TUNER-AGENTV3"; do
    if [ -d "$usb_path" ]; then
        USB_PATH="$usb_path"
        break
    fi
done

if [ -z "$USB_PATH" ]; then
    echo "ERROR: USB device not found!"
    echo "Please connect USB drive and try again"
    exit 1
fi

if [ ! -d "$HDD_PATH" ]; then
    echo "ERROR: Hard drive path doesn't exist: $HDD_PATH"
    echo "Please run: sudo scripts/setup_hard_drive.sh first"
    exit 1
fi

echo "USB Path: $USB_PATH"
echo "HDD Path: $HDD_PATH"
echo ""

# Exclude patterns
EXCLUDE=(
    --exclude='.git'
    --exclude='__pycache__'
    --exclude='*.pyc'
    --exclude='.pytest_cache'
    --exclude='*.log'
    --exclude='logs/'
    --exclude='data/logs/'
    --exclude='node_modules'
    --exclude='.venv'
    --exclude='venv'
)

# Sync HDD -> USB
echo "Syncing HDD -> USB..."
rsync -av --delete "${EXCLUDE[@]}" "$HDD_PATH/" "$USB_PATH/"

# Sync USB -> HDD (newer files only)
echo ""
echo "Syncing USB -> HDD (newer files only)..."
rsync -av --update "${EXCLUDE[@]}" "$USB_PATH/" "$HDD_PATH/"

echo ""
echo "✅ Sync complete!"

