#!/bin/bash
# Migrate AI Tuner Agent to run from Hard Drive
# This script sets up the application to run from HDD instead of USB/home

set -e

HDD_PATH="/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3"
CURRENT_PATH="$HOME/AITUNER/2025-AI-TUNER-AGENTV3"
SYMLINK_PATH="$HOME/AITUNER_HDD"

echo "=========================================="
echo "Migrating AI Tuner Agent to Hard Drive"
echo "=========================================="
echo ""

# Check if HDD path exists
if [ ! -d "$HDD_PATH" ]; then
    echo "ERROR: Hard drive path doesn't exist: $HDD_PATH"
    echo ""
    echo "Please run first:"
    echo "  1. sudo scripts/setup_hard_drive.sh"
    echo "  2. scripts/copy_from_usb_to_hdd.sh"
    exit 1
fi

echo "Step 1: Creating symlink for easy access..."
# Create symlink in home directory for easy access
if [ -L "$SYMLINK_PATH" ]; then
    echo "   Symlink already exists: $SYMLINK_PATH"
    read -p "   Replace it? (yes/no): " replace
    if [ "$replace" = "yes" ]; then
        rm "$SYMLINK_PATH"
        ln -s "$HDD_PATH" "$SYMLINK_PATH"
        echo "   ✅ Symlink updated"
    fi
elif [ ! -e "$SYMLINK_PATH" ]; then
    ln -s "$HDD_PATH" "$SYMLINK_PATH"
    echo "   ✅ Symlink created: $SYMLINK_PATH -> $HDD_PATH"
else
    echo "   ⚠️  Path exists but is not a symlink: $SYMLINK_PATH"
fi

echo ""
echo "Step 2: Updating environment..."
# Create environment setup script
ENV_SCRIPT="$HDD_PATH/scripts/setup_hdd_env.sh"
cat > "$ENV_SCRIPT" << 'ENV_EOF'
#!/bin/bash
# Setup environment to run from HDD

export AITUNER_HDD_PATH="/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3"
export AITUNER_RUN_FROM_HDD="true"

# Add HDD path to PYTHONPATH
export PYTHONPATH="$AITUNER_HDD_PATH:$PYTHONPATH"

# Change to HDD directory
cd "$AITUNER_HDD_PATH"

echo "Environment set for HDD operation"
echo "Project path: $AITUNER_HDD_PATH"
ENV_EOF

chmod +x "$ENV_SCRIPT"
echo "   ✅ Environment script created: $ENV_SCRIPT"

echo ""
echo "Step 3: Creating HDD launcher script..."
# Create launcher script
LAUNCHER="$HDD_PATH/run_from_hdd.sh"
cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash
# Run AI Tuner Agent from Hard Drive

HDD_PATH="/mnt/aituner_hdd/AITUNER/2025-AI-TUNER-AGENTV3"

# Check if HDD is mounted
if [ ! -d "$HDD_PATH" ]; then
    echo "ERROR: Hard drive not mounted!"
    echo "Please run: sudo mount /dev/sdX1 /mnt/aituner_hdd"
    exit 1
fi

# Change to HDD directory
cd "$HDD_PATH"

# Source environment
if [ -f "scripts/setup_hdd_env.sh" ]; then
    source scripts/setup_hdd_env.sh
fi

# Run the demo
echo "Running AI Tuner Agent from Hard Drive..."
echo "Path: $HDD_PATH"
echo ""

python3 demo_safe.py "$@"
LAUNCHER_EOF

chmod +x "$LAUNCHER"
echo "   ✅ Launcher script created: $LAUNCHER"

echo ""
echo "Step 4: Creating desktop shortcut (if desktop environment)..."
# Create desktop shortcut if XDG directories exist
if [ -d "$HOME/Desktop" ] || [ -n "$XDG_DESKTOP_DIR" ]; then
    DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
    SHORTCUT="$DESKTOP_DIR/AI_Tuner_HDD.desktop"
    
    cat > "$SHORTCUT" << SHORTCUT_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AI Tuner Agent (HDD)
Comment=Run AI Tuner Agent from Hard Drive
Exec=$HDD_PATH/run_from_hdd.sh
Icon=applications-system
Terminal=true
Categories=Utility;
SHORTCUT_EOF

    chmod +x "$SHORTCUT"
    echo "   ✅ Desktop shortcut created: $SHORTCUT"
fi

echo ""
echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="
echo ""
echo "Hard Drive Setup:"
echo "  Project path: $HDD_PATH"
echo "  Symlink:      $SYMLINK_PATH"
echo ""
echo "To run from HDD:"
echo "  cd $HDD_PATH"
echo "  python3 demo_safe.py"
echo ""
echo "Or use launcher:"
echo "  $HDD_PATH/run_from_hdd.sh"
echo ""
echo "Sync Status:"
echo "  Automatic sync: Every 5 minutes (if setup_hdd_sync.sh was run)"
echo "  Manual sync:    scripts/sync_usb_hdd.sh"
echo ""

