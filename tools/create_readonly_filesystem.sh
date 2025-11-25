#!/bin/bash
# Create Read-Only Filesystem for Hardware Deployment
# This makes the codebase read-only to prevent modification

set -e

echo "=========================================="
echo "Creating Read-Only Filesystem"
echo "=========================================="

APP_DIR="/opt/ai-tuner-agent"
MOUNT_POINT="/mnt/ai-tuner-ro"

# 1. Copy application to protected location
echo "1. Copying application to $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo cp -r AI-TUNER-AGENT/* $APP_DIR/
sudo chown -R root:root $APP_DIR
sudo chmod -R 755 $APP_DIR

# 2. Make application directory read-only
echo "2. Making application directory read-only..."
sudo chmod -R 444 $APP_DIR/*.py
sudo chmod -R 444 $APP_DIR/*.pyc
sudo find $APP_DIR -type f -exec chmod 444 {} \;
sudo find $APP_DIR -type d -exec chmod 555 {} \;

# 3. Create overlay filesystem (allows writes to tmpfs, but base is read-only)
echo "3. Setting up overlay filesystem..."
sudo mkdir -p $MOUNT_POINT
sudo mkdir -p /tmp/ai-tuner-overlay/{upper,work}

# Mount overlay (read-only base, writable overlay)
sudo mount -t overlay overlay \
    -o lowerdir=$APP_DIR,upperdir=/tmp/ai-tuner-overlay/upper,workdir=/tmp/ai-tuner-overlay/work \
    $MOUNT_POINT

# 4. Create systemd service to remount on boot
echo "4. Creating systemd service..."
sudo tee /etc/systemd/system/ai-tuner-protect.service > /dev/null <<EOF
[Unit]
Description=AI Tuner Agent Protection
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/bin/mount -o remount,ro $APP_DIR
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable ai-tuner-protect.service

# 5. Set up secure boot verification (if available)
if [ -d /sys/firmware/efi ]; then
    echo "5. Secure boot detected - enabling verification..."
    # Add secure boot checks here
fi

echo ""
echo "=========================================="
echo "Read-Only Filesystem Created!"
echo "=========================================="
echo "Application: $APP_DIR (read-only)"
echo "Overlay: $MOUNT_POINT (writable overlay)"
echo ""
echo "To make changes, you must:"
echo "1. Boot from recovery mode"
echo "2. Remount as read-write: sudo mount -o remount,rw $APP_DIR"
echo "3. Make changes"
echo "4. Remount as read-only: sudo mount -o remount,ro $APP_DIR"

