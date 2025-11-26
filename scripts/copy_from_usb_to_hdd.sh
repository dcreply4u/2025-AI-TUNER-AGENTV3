#!/bin/bash
# Copy AI Tuner Agent files from USB to Hard Drive
# This script copies the application from USB to hard drive

set -e

USB_PATH="/media/aituner/AITUNER"  # Default USB mount point (adjust if needed)
HDD_PATH="/mnt/aituner_hdd/AITUNER"
PROJECT_NAME="2025-AI-TUNER-AGENTV3"

echo "=========================================="
echo "Copying AI Tuner Agent from USB to HDD"
echo "=========================================="
echo ""

# Check if running as root (for permissions)
if [ "$EUID" -ne 0 ]; then 
    echo "WARNING: Not running as root - may have permission issues"
    SUDO=""
else
    SUDO=""
fi

# Function to find USB device
find_usb_device() {
    echo "Step 1: Finding USB device..."
    
    # Check common USB mount points
    for usb_path in "/media/aituner/AITUNER" "/media/$USER/AITUNER" "/mnt/usb" "/media/usb"; do
        if [ -d "$usb_path/$PROJECT_NAME" ]; then
            echo "   ✅ Found USB device at: $usb_path"
            echo "$usb_path"
            return 0
        fi
    done
    
    # Try to find any mounted USB device
    for mount_point in $(mount | grep -E "(usb|media)" | awk '{print $3}'); do
        if [ -d "$mount_point/$PROJECT_NAME" ]; then
            echo "   ✅ Found USB device at: $mount_point"
            echo "$mount_point"
            return 0
        fi
    done
    
    # Check if USB is in home directory (if copied there)
    if [ -d "$HOME/AITUNER/$PROJECT_NAME" ]; then
        echo "   ✅ Found project in home directory: $HOME/AITUNER"
        echo "$HOME/AITUNER"
        return 0
    fi
    
    return 1
}

# Function to verify hard drive is mounted
verify_hdd() {
    if [ ! -d "$HDD_PATH" ]; then
        echo "ERROR: Hard drive not mounted or directory doesn't exist: $HDD_PATH"
        echo ""
        echo "Please run: sudo scripts/setup_hard_drive.sh first"
        exit 1
    fi
    
    if ! mountpoint -q "$(dirname "$HDD_PATH")"; then
        echo "ERROR: Hard drive mount point is not a mount point: $(dirname "$HDD_PATH")"
        echo ""
        echo "Please run: sudo scripts/setup_hard_drive.sh first"
        exit 1
    fi
    
    echo "   ✅ Hard drive verified: $HDD_PATH"
}

# Function to copy files
copy_files() {
    local source=$1
    local dest=$2
    
    echo ""
    echo "Step 2: Copying files..."
    echo "   Source: $source/$PROJECT_NAME"
    echo "   Destination: $dest/$PROJECT_NAME"
    echo ""
    
    # Check if source exists
    if [ ! -d "$source/$PROJECT_NAME" ]; then
        echo "ERROR: Source directory not found: $source/$PROJECT_NAME"
        echo ""
        echo "Available directories in $source:"
        ls -la "$source" 2>/dev/null || echo "   (directory doesn't exist)"
        exit 1
    fi
    
    # Create destination directory
    mkdir -p "$dest"
    
    # Use rsync for efficient copying (preserves permissions, timestamps, etc.)
    echo "   Copying files (this may take a while)..."
    rsync -av --progress \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='*.log' \
        --exclude='logs/' \
        --exclude='data/logs/' \
        --exclude='node_modules' \
        --exclude='.venv' \
        --exclude='venv' \
        "$source/$PROJECT_NAME/" "$dest/$PROJECT_NAME/"
    
    # Set ownership
    if [ -n "$SUDO" ]; then
        chown -R aituner:aituner "$dest/$PROJECT_NAME" 2>/dev/null || chown -R $SUDO_USER:$SUDO_USER "$dest/$PROJECT_NAME"
    fi
    
    echo ""
    echo "   ✅ Files copied successfully"
}

# Function to verify copy
verify_copy() {
    echo ""
    echo "Step 3: Verifying copy..."
    
    local source="$1/$PROJECT_NAME"
    local dest="$2/$PROJECT_NAME"
    
    # Check key files
    key_files=(
        "demo_safe.py"
        "requirements.txt"
        "controllers/data_stream_controller.py"
        "interfaces/camera_interface.py"
    )
    
    missing_files=()
    for file in "${key_files[@]}"; do
        if [ ! -f "$dest/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "   ✅ All key files present"
    else
        echo "   ⚠️  Missing files:"
        for file in "${missing_files[@]}"; do
            echo "      - $file"
        done
    fi
    
    # Check directory sizes
    source_size=$(du -sh "$source" 2>/dev/null | cut -f1)
    dest_size=$(du -sh "$dest" 2>/dev/null | cut -f1)
    
    echo "   Source size: $source_size"
    echo "   Destination size: $dest_size"
}

# Main execution
USB_SOURCE=$(find_usb_device)

if [ -z "$USB_SOURCE" ]; then
    echo "ERROR: Could not find USB device with project!"
    echo ""
    echo "Please:"
    echo "  1. Connect USB drive"
    echo "  2. Mount it (usually auto-mounted)"
    echo "  3. Verify project is at: /media/*/AITUNER/$PROJECT_NAME"
    echo ""
    echo "Or specify source path manually:"
    echo "  USB_SOURCE=/path/to/usb scripts/copy_from_usb_to_hdd.sh"
    exit 1
fi

verify_hdd
copy_files "$USB_SOURCE" "$HDD_PATH"
verify_copy "$USB_SOURCE" "$HDD_PATH"

echo ""
echo "=========================================="
echo "✅ Copy Complete!"
echo "=========================================="
echo ""
echo "Files copied from: $USB_SOURCE/$PROJECT_NAME"
echo "Files copied to:   $HDD_PATH/$PROJECT_NAME"
echo ""
echo "Next steps:"
echo "  1. Run: scripts/setup_hdd_sync.sh (to set up sync)"
echo "  2. Update PATH or create symlink to run from HDD"
echo ""

