#!/bin/bash
# Setup bidirectional sync between USB and Hard Drive
# This script sets up rsync-based synchronization

set -e

USB_PATH="/media/aituner/AITUNER/2025-AI-TUNER-AGENTV3"
HDD_PATH="/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3"
SYNC_LOG="/var/log/aituner_sync.log"
SYNC_SCRIPT="/usr/local/bin/aituner_sync.sh"

echo "=========================================="
echo "Setting up USB <-> HDD Sync"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Create sync script
create_sync_script() {
    echo "Step 1: Creating sync script..."
    
    cat > "$SYNC_SCRIPT" << 'SYNC_SCRIPT_EOF'
#!/bin/bash
# AI Tuner Agent - USB <-> HDD Sync Script
# Syncs changes between USB and Hard Drive

USB_PATH="/media/aituner/AITUNER/2025-AI-TUNER-AGENTV3"
HDD_PATH="/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3"
SYNC_LOG="/var/log/aituner_sync.log"
LOCK_FILE="/var/run/aituner_sync.lock"

# Exclude patterns
EXCLUDE_PATTERNS=(
    '--exclude=.git'
    '--exclude=__pycache__'
    '--exclude=*.pyc'
    '--exclude=.pytest_cache'
    '--exclude=*.log'
    '--exclude=logs/'
    '--exclude=data/logs/'
    '--exclude=node_modules'
    '--exclude=.venv'
    '--exclude=venv'
    '--exclude=.sync_lock'
)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SYNC_LOG"
}

# Check if sync is already running
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Sync already running (PID: $PID), skipping"
        exit 0
    else
        # Stale lock file
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Check if both paths exist
if [ ! -d "$HDD_PATH" ]; then
    log "ERROR: HDD path doesn't exist: $HDD_PATH"
    exit 1
fi

# Find USB device
USB_FOUND=""
for usb_path in "/media/aituner/AITUNER/2025-AI-TUNER-AGENTV3" "/media/$USER/AITUNER/2025-AI-TUNER-AGENTV3" "/mnt/usb/2025-AI-TUNER-AGENTV3"; do
    if [ -d "$usb_path" ]; then
        USB_FOUND="$usb_path"
        break
    fi
done

if [ -z "$USB_FOUND" ]; then
    log "USB device not found, syncing HDD -> USB skipped"
    USB_AVAILABLE=false
else
    USB_PATH="$USB_FOUND"
    USB_AVAILABLE=true
    log "USB device found at: $USB_PATH"
fi

# Sync HDD -> USB (if USB available)
if [ "$USB_AVAILABLE" = true ]; then
    log "Syncing HDD -> USB..."
    rsync -av --delete "${EXCLUDE_PATTERNS[@]}" \
        "$HDD_PATH/" "$USB_PATH/" >> "$SYNC_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        log "✅ HDD -> USB sync complete"
    else
        log "⚠️  HDD -> USB sync had errors (check log)"
    fi
fi

# Sync USB -> HDD (if USB available and newer files exist)
if [ "$USB_AVAILABLE" = true ]; then
    log "Syncing USB -> HDD (newer files only)..."
    rsync -av --update "${EXCLUDE_PATTERNS[@]}" \
        "$USB_PATH/" "$HDD_PATH/" >> "$SYNC_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        log "✅ USB -> HDD sync complete"
    else
        log "⚠️  USB -> HDD sync had errors (check log)"
    fi
fi

log "Sync cycle complete"
SYNC_SCRIPT_EOF

    chmod +x "$SYNC_SCRIPT"
    echo "   ✅ Sync script created: $SYNC_SCRIPT"
}

# Create systemd service for automatic syncing
create_systemd_service() {
    echo ""
    echo "Step 2: Creating systemd service..."
    
    cat > /etc/systemd/system/aituner-sync.service << SERVICE_EOF
[Unit]
Description=AI Tuner Agent USB/HDD Sync Service
After=network.target

[Service]
Type=oneshot
ExecStart=$SYNC_SCRIPT
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    # Create timer for periodic sync
    cat > /etc/systemd/system/aituner-sync.timer << TIMER_EOF
[Unit]
Description=AI Tuner Agent USB/HDD Sync Timer
Requires=aituner-sync.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=1min

[Install]
WantedBy=timers.target
TIMER_EOF

    # Enable and start timer
    systemctl daemon-reload
    systemctl enable aituner-sync.timer
    systemctl start aituner-sync.timer
    
    echo "   ✅ Systemd service created and enabled"
    echo "   Sync will run every 5 minutes automatically"
}

# Create manual sync script for user
create_manual_sync() {
    echo ""
    echo "Step 3: Creating manual sync script for user..."
    
    USER_SYNC_SCRIPT="$HDD_PATH/scripts/sync_usb_hdd.sh"
    cat > "$USER_SYNC_SCRIPT" << 'USER_SYNC_EOF'
#!/bin/bash
# Manual sync script - can be run by user

echo "Syncing USB <-> HDD..."
sudo /usr/local/bin/aituner_sync.sh
echo "Sync complete! Check /var/log/aituner_sync.log for details"
USER_SYNC_EOF

    chmod +x "$USER_SYNC_SCRIPT"
    chown aituner:aituner "$USER_SYNC_SCRIPT" 2>/dev/null || true
    echo "   ✅ Manual sync script created: $USER_SYNC_SCRIPT"
}

# Create log directory
mkdir -p "$(dirname "$SYNC_LOG")"
touch "$SYNC_LOG"
chmod 644 "$SYNC_LOG"

# Main execution
create_sync_script
create_systemd_service
create_manual_sync

echo ""
echo "=========================================="
echo "✅ Sync Setup Complete!"
echo "=========================================="
echo ""
echo "Sync Configuration:"
echo "  - Automatic sync: Every 5 minutes"
echo "  - Manual sync: scripts/sync_usb_hdd.sh"
echo "  - Log file: $SYNC_LOG"
echo ""
echo "Sync Behavior:"
echo "  - HDD -> USB: Full sync (HDD is source of truth)"
echo "  - USB -> HDD: Only newer files (USB updates)"
echo ""
echo "To check sync status:"
echo "  sudo systemctl status aituner-sync.timer"
echo "  tail -f $SYNC_LOG"
echo ""

