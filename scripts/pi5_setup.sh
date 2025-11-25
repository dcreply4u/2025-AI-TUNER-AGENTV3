#!/bin/bash
#
# Raspberry Pi 5 Setup Script for AI Tuner Agent
# This script prepares a fresh Raspberry Pi 5 for running the AI Tuner Agent
#
# Usage: sudo ./pi5_setup.sh
#

set -e  # Exit on error

echo "=========================================="
echo "Raspberry Pi 5 Setup for AI Tuner Agent"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Detect Pi 5
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: Cannot detect hardware model"
else
    MODEL=$(cat /proc/device-tree/model)
    echo "Detected: $MODEL"
    
    if [[ "$MODEL" != *"Raspberry Pi 5"* ]]; then
        echo "Warning: This script is designed for Raspberry Pi 5"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

echo ""
echo "Step 1: Updating system packages..."
apt-get update
apt-get upgrade -y

echo ""
echo "Step 2: Installing essential packages..."
apt-get install -y \
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
    wireless-tools \
    usbutils

echo ""
echo "Step 3: Enabling hardware interfaces..."
# Enable I2C
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null && ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
    if [ -f /boot/firmware/config.txt ]; then
        echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
    elif [ -f /boot/config.txt ]; then
        echo "dtparam=i2c_arm=on" >> /boot/config.txt
    fi
    echo "Enabled I2C"
fi

# Enable SPI
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null && ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    if [ -f /boot/firmware/config.txt ]; then
        echo "dtparam=spi=on" >> /boot/firmware/config.txt
    elif [ -f /boot/config.txt ]; then
        echo "dtparam=spi=on" >> /boot/config.txt
    fi
    echo "Enabled SPI"
fi

# Enable CAN (if available)
if ! grep -q "^dtoverlay=vc4-kms-v3d" /boot/firmware/config.txt 2>/dev/null && ! grep -q "^dtoverlay=vc4-kms-v3d" /boot/config.txt 2>/dev/null; then
    # Check for CAN HAT overlays
    echo "Note: CAN interface configuration depends on your HAT"
    echo "Common CAN overlays:"
    echo "  - dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25"
    echo "  - dtoverlay=mcp2518fd-can0"
fi

echo ""
echo "Step 4: Setting up Python environment..."
# Create virtual environment if it doesn't exist
if [ ! -d "/opt/ai-tuner-agent/venv" ]; then
    mkdir -p /opt/ai-tuner-agent
    python3 -m venv /opt/ai-tuner-agent/venv
    echo "Created Python virtual environment"
fi

echo ""
echo "Step 5: Configuring network..."
# Enable SSH if not already enabled
systemctl enable ssh
systemctl start ssh
echo "SSH enabled"

# Show network interfaces
echo ""
echo "Network interfaces:"
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "No IPv4 addresses found"

echo ""
echo "Step 6: Creating application directory..."
mkdir -p /opt/ai-tuner-agent
chown -R $SUDO_USER:$SUDO_USER /opt/ai-tuner-agent 2>/dev/null || true

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Reboot if I2C/SPI were enabled: sudo reboot"
echo "2. Clone the repository to /opt/ai-tuner-agent"
echo "3. Run: ./scripts/pi5_install.sh"
echo ""
echo "To find your IP address:"
echo "  hostname -I"
echo "  or"
echo "  ip addr show"
echo ""
echo "To test hardware detection:"
echo "  python3 scripts/test_hardware_detection.py"
echo ""



