#!/bin/bash
# Setup script for CAN Bus HAT on Raspberry Pi 5
# Run this after installing your CAN bus HAT

set -e

echo "=========================================="
echo "🔌 CAN Bus HAT Setup for Raspberry Pi 5"
echo "=========================================="
echo ""

# Detect HAT type
HAT_TYPE=""
CONFIG_FILE=""

# Check which config file exists
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
else
    echo "❌ Cannot find config.txt"
    exit 1
fi

echo "Step 1: Detecting CAN HAT type..."
echo ""

# Check for existing CAN interfaces
CAN_INTERFACES=$(ip link show 2>/dev/null | grep -o "can[0-9]*" || echo "")
if [ -n "$CAN_INTERFACES" ]; then
    echo "✅ Found existing CAN interfaces: $CAN_INTERFACES"
    echo "   HAT may already be configured"
    read -p "Continue with setup anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Ask user for HAT type
echo ""
echo "Select your CAN HAT type:"
echo "1) MCP2515-based (PiCAN, PiCAN2, PiCAN3) - CAN 2.0B, 1 Mbps"
echo "2) MCP2518FD-based - CAN FD, 5 Mbps"
echo "3) Other/Unknown"
echo ""
read -p "Enter choice (1-3): " hat_choice

case $hat_choice in
    1)
        HAT_TYPE="mcp2515"
        OVERLAY="mcp2515-can0"
        echo "✅ Selected: MCP2515-based HAT"
        ;;
    2)
        HAT_TYPE="mcp2518fd"
        OVERLAY="mcp2518fd-can0"
        echo "✅ Selected: MCP2518FD-based HAT"
        ;;
    3)
        echo "⚠️  Unknown HAT type - will attempt generic setup"
        HAT_TYPE="generic"
        OVERLAY=""
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Step 2: Configuring device tree overlay..."

# Backup config file
sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup created: ${CONFIG_FILE}.backup.*"

# Check if overlay already exists
if grep -q "dtoverlay=$OVERLAY" "$CONFIG_FILE" 2>/dev/null; then
    echo "⚠️  Overlay already configured in $CONFIG_FILE"
    read -p "Remove and reconfigure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo sed -i "/dtoverlay=$OVERLAY/d" "$CONFIG_FILE"
    else
        echo "Keeping existing configuration"
        OVERLAY_EXISTS=true
    fi
fi

# Add overlay if needed
if [ "$HAT_TYPE" != "generic" ] && [ -z "$OVERLAY_EXISTS" ]; then
    if [ "$HAT_TYPE" == "mcp2515" ]; then
        # MCP2515 overlay with common settings
        OVERLAY_LINE="dtoverlay=$OVERLAY,oscillator=16000000,interrupt=25"
    else
        # MCP2518FD overlay
        OVERLAY_LINE="dtoverlay=$OVERLAY,oscillator=40000000,interrupt=25"
    fi
    
    echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "# CAN Bus HAT Configuration" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "$OVERLAY_LINE" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "✅ Added overlay: $OVERLAY_LINE"
fi

echo ""
echo "Step 3: Installing CAN utilities..."
sudo apt-get update -qq
sudo apt-get install -y -qq can-utils python3-can > /dev/null 2>&1
echo "✅ CAN utilities installed"

echo ""
echo "Step 4: Configuring CAN interface..."

# Create systemd service for auto-starting CAN interface
SERVICE_FILE="/etc/systemd/system/can0.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Bring up CAN0 interface
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/ip link set can0 up type can bitrate 500000
ExecStop=/sbin/ip link set can0 down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created systemd service for can0"

echo ""
echo "Step 5: Enabling SPI (required for CAN HATs)..."
if ! grep -q "^dtparam=spi=on" "$CONFIG_FILE" 2>/dev/null; then
    echo "dtparam=spi=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "✅ SPI enabled"
else
    echo "✅ SPI already enabled"
fi

echo ""
echo "=========================================="
echo "✅ CAN HAT Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. REBOOT the Pi to activate the CAN HAT:"
echo "   sudo reboot"
echo ""
echo "2. After reboot, verify CAN interface:"
echo "   ip link show can0"
echo ""
echo "3. Test CAN bus (if you have another CAN device):"
echo "   candump can0"
echo ""
echo "4. Check HAT detection:"
echo "   cd ~/AITUNER/AI-TUNER-AGENT"
echo "   source ~/AITUNER/venv/bin/activate"
echo "   python3 -c 'from core.hat_detector import HATDetector; config = HATDetector.detect_all_hats(); print(f\"CAN HATs: {len(config.can_hats)}\")'"
echo ""
echo "⚠️  IMPORTANT: Reboot required for changes to take effect!"
echo ""






