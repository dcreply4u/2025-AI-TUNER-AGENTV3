#!/bin/bash
# Automated Complete Setup for Raspberry Pi 5
# Run this script ON the Pi 5 after SSH is enabled
# Usage: curl -sSL https://raw.githubusercontent.com/dcreply4u/ai-tuner-agent/v2/scripts/automated_pi5_setup.sh | bash
# Or: wget -qO- ... | bash

set -e

PI_USER="${SUDO_USER:-$USER}"
REPO_URL="https://github.com/dcreply4u/ai-tuner-agent.git"
INSTALL_DIR="$HOME/AI-TUNER-AGENT"

echo "=========================================="
echo "🤖 AI Tuner Agent - Automated Pi 5 Setup"
echo "=========================================="
echo ""
echo "User: $PI_USER"
echo "Install directory: $INSTALL_DIR"
echo ""

# Check if running on Pi 5
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "📱 Detected: $MODEL"
    if [[ "$MODEL" != *"Raspberry Pi 5"* ]]; then
        echo "⚠️  Warning: This script is designed for Raspberry Pi 5"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "⚠️  Cannot detect hardware model"
fi

echo ""
echo "Step 1/8: Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

echo ""
echo "Step 2/8: Installing essential packages..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    python3-dev \
    i2c-tools \
    spi-tools \
    can-utils \
    libcan-dev \
    python3-can \
    python3-serial \
    python3-numpy \
    python3-scipy \
    python3-matplotlib \
    vim \
    htop \
    net-tools \
    usbutils \
    > /dev/null 2>&1

echo ""
echo "Step 3/8: Enabling hardware interfaces..."
# Enable I2C
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
else
    CONFIG_FILE=""
fi

if [ -n "$CONFIG_FILE" ]; then
    if ! grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE" 2>/dev/null; then
        echo "dtparam=i2c_arm=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
        echo "✅ Enabled I2C"
    fi
    
    if ! grep -q "^dtparam=spi=on" "$CONFIG_FILE" 2>/dev/null; then
        echo "dtparam=spi=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
        echo "✅ Enabled SPI"
    fi
fi

echo ""
echo "Step 4/8: Enabling SSH..."
sudo systemctl enable ssh > /dev/null 2>&1
sudo systemctl start ssh > /dev/null 2>&1
echo "✅ SSH enabled"

echo ""
echo "Step 5/8: Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "📁 Repository already exists, updating..."
    cd "$INSTALL_DIR"
    git pull origin v2 || git pull origin main
else
    cd "$HOME"
    git clone -b v2 "$REPO_URL" "$INSTALL_DIR" || git clone "$REPO_URL" "$INSTALL_DIR"
    echo "✅ Repository cloned"
fi

echo ""
echo "Step 6/8: Setting up Python environment..."
cd "$INSTALL_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

source venv/bin/activate
pip install --upgrade pip -q
echo "✅ Python environment ready"

echo ""
echo "Step 7/8: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, installing basic packages..."
    pip install fastapi uvicorn pydantic pyqt6 pyside6 -q
fi

echo ""
echo "Step 8/8: Testing setup..."
# Test hardware detection
if [ -f "scripts/test_hardware_detection.py" ]; then
    python3 scripts/test_hardware_detection.py || echo "⚠️  Hardware test had issues (may be normal)"
fi

# Check USB devices
echo ""
echo "📦 USB Devices:"
lsblk | grep -E "sd[a-z]" || echo "No USB devices detected"

# Show IP address
echo ""
echo "🌐 Network Information:"
hostname -I

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Reboot to enable I2C/SPI (if enabled):"
echo "   sudo reboot"
echo ""
echo "2. After reboot, activate virtual environment:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo ""
echo "3. Test the application:"
echo "   python3 demo.py"
echo ""
echo "4. Check USB drive (if connected):"
echo "   lsblk"
echo "   df -h"
echo ""
echo "5. Test hardware detection:"
echo "   python3 scripts/test_hardware_detection.py"
echo ""
echo "📍 Your IP address: $(hostname -I | awk '{print $1}')"
echo ""







