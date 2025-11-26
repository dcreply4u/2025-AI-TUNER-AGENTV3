#!/bin/bash
# Setup Hard Drive for AI Tuner Agent
# This script detects, formats (if needed), and mounts a hard drive on Raspberry Pi 5

set -e

MOUNT_POINT="/mnt/aituner_hdd"
LABEL="AITUNER_HDD"
FILESYSTEM="ext4"

echo "=========================================="
echo "AI Tuner Agent - Hard Drive Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Function to find hard drive
find_hard_drive() {
    echo "Step 1: Detecting hard drive..."
    
    # Look for SATA/USB hard drives (not SD card)
    # SD card is usually /dev/mmcblk0, we want /dev/sda, /dev/sdb, etc.
    for device in /dev/sd[a-z] /dev/nvme[0-9]n[0-9]; do
        if [ -b "$device" ]; then
            # Check if it's not the boot device (SD card)
            if ! mountpoint -q / && ! lsblk -n -o MOUNTPOINT "$device" 2>/dev/null | grep -q "^/$"; then
                # Check if device has partitions
                if lsblk -n -o TYPE "$device" 2>/dev/null | grep -q "disk"; then
                    echo "   Found hard drive: $device"
                    echo "$device"
                    return 0
                fi
            fi
        fi
    done
    
    # Also check for partitions
    for device in /dev/sd[a-z][0-9] /dev/nvme[0-9]n[0-9]p[0-9]; do
        if [ -b "$device" ]; then
            if ! mountpoint -q / && ! lsblk -n -o MOUNTPOINT "$device" 2>/dev/null | grep -q "^/$"; then
                echo "   Found hard drive partition: $device"
                echo "$device"
                return 0
            fi
        fi
    done
    
    return 1
}

# Function to format hard drive
format_hard_drive() {
    local device=$1
    echo ""
    echo "Step 2: Formatting hard drive..."
    echo "   Device: $device"
    echo "   Filesystem: $FILESYSTEM"
    echo "   Label: $LABEL"
    echo ""
    read -p "WARNING: This will erase all data on $device. Continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 1
    fi
    
    # Unmount if mounted
    umount "$device" 2>/dev/null || true
    
    # Create filesystem
    if [ "$FILESYSTEM" = "ext4" ]; then
        mkfs.ext4 -F -L "$LABEL" "$device"
    elif [ "$FILESYSTEM" = "exfat" ]; then
        mkfs.exfat -n "$LABEL" "$device"
    else
        echo "ERROR: Unsupported filesystem: $FILESYSTEM"
        exit 1
    fi
    
    echo "   ✅ Hard drive formatted successfully"
}

# Function to mount hard drive
mount_hard_drive() {
    local device=$1
    echo ""
    echo "Step 3: Mounting hard drive..."
    
    # Create mount point
    mkdir -p "$MOUNT_POINT"
    
    # Mount the device
    mount "$device" "$MOUNT_POINT"
    
    # Set permissions
    chown -R aituner:aituner "$MOUNT_POINT" 2>/dev/null || chown -R $SUDO_USER:$SUDO_USER "$MOUNT_POINT"
    chmod 755 "$MOUNT_POINT"
    
    echo "   ✅ Hard drive mounted at: $MOUNT_POINT"
}

# Function to add to fstab for auto-mount
add_to_fstab() {
    local device=$1
    echo ""
    echo "Step 4: Adding to /etc/fstab for auto-mount..."
    
    # Get UUID
    UUID=$(blkid -s UUID -o value "$device")
    
    if [ -z "$UUID" ]; then
        echo "   ⚠️  Could not get UUID, skipping fstab entry"
        return
    fi
    
    # Check if already in fstab
    if grep -q "$MOUNT_POINT" /etc/fstab; then
        echo "   ⚠️  Mount point already in fstab, skipping"
        return
    fi
    
    # Add entry to fstab
    if [ "$FILESYSTEM" = "ext4" ]; then
        echo "UUID=$UUID $MOUNT_POINT ext4 defaults,noatime 0 2" >> /etc/fstab
    elif [ "$FILESYSTEM" = "exfat" ]; then
        echo "UUID=$UUID $MOUNT_POINT exfat defaults,uid=$(id -u $SUDO_USER),gid=$(id -g $SUDO_USER),umask=0000 0 0" >> /etc/fstab
    fi
    
    echo "   ✅ Added to /etc/fstab (will auto-mount on boot)"
}

# Main execution
echo "Detecting hard drive..."
DEVICE=$(find_hard_drive)

if [ -z "$DEVICE" ]; then
    echo "ERROR: No hard drive detected!"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check hard drive connection"
    echo "  2. Check power supply"
    echo "  3. Run: lsblk (to see all block devices)"
    echo "  4. Run: dmesg | tail (to see recent kernel messages)"
    exit 1
fi

echo "   ✅ Hard drive detected: $DEVICE"
echo ""

# Check if already formatted
if blkid "$DEVICE" >/dev/null 2>&1; then
    echo "Hard drive is already formatted"
    FILESYSTEM=$(blkid -s TYPE -o value "$DEVICE")
    echo "   Filesystem: $FILESYSTEM"
    read -p "Format anyway? (yes/no): " format_anyway
    if [ "$format_anyway" = "yes" ]; then
        format_hard_drive "$DEVICE"
    fi
else
    format_hard_drive "$DEVICE"
fi

# Mount the drive
if mountpoint -q "$MOUNT_POINT"; then
    echo "Hard drive is already mounted at $MOUNT_POINT"
else
    mount_hard_drive "$DEVICE"
fi

# Add to fstab
add_to_fstab "$DEVICE"

# Create directory structure
echo ""
echo "Step 5: Creating directory structure..."
mkdir -p "$MOUNT_POINT/AITUNER"
mkdir -p "$MOUNT_POINT/AITUNER/logs"
mkdir -p "$MOUNT_POINT/AITUNER/data"
mkdir -p "$MOUNT_POINT/AITUNER/sessions"
chown -R aituner:aituner "$MOUNT_POINT/AITUNER" 2>/dev/null || chown -R $SUDO_USER:$SUDO_USER "$MOUNT_POINT/AITUNER"
echo "   ✅ Directory structure created"

echo ""
echo "=========================================="
echo "✅ Hard Drive Setup Complete!"
echo "=========================================="
echo ""
echo "Mount point: $MOUNT_POINT"
echo "Device: $DEVICE"
echo ""
echo "Next steps:"
echo "  1. Run: scripts/copy_from_usb_to_hdd.sh"
echo "  2. Run: scripts/setup_hdd_sync.sh"
echo ""

