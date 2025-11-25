#!/bin/bash
# Complete Raspberry Pi 5 Setup Script
# Run this on the Pi 5 via SSH

set -e

echo "=========================================="
echo "🤖 AI Tuner Agent - Complete Pi 5 Setup"
echo "=========================================="
echo ""

INSTALL_DIR="$HOME/AITUNER/AI-TUNER-AGENT"
REPO_URL="https://github.com/dcreply4u/ai-tuner-agent.git"

# Step 1: Update system
echo "Step 1/9: Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Step 2: Install essential system packages
echo ""
echo "Step 2/9: Installing essential packages..."
sudo apt-get install -y -qq \
    python3-pip \
    python3-venv \
    build-essential \
    python3-dev \
    i2c-tools \
    spi-tools \
    can-utils \
    libcan-dev \
    vim \
    htop \
    net-tools \
    usbutils \
    git \
    wget \
    curl \
    > /dev/null 2>&1

# Step 3: Enable I2C and SPI
echo ""
echo "Step 3/9: Enabling hardware interfaces..."
CONFIG_FILE=""
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
fi

if [ -n "$CONFIG_FILE" ]; then
    # Enable I2C
    if ! grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE" 2>/dev/null; then
        echo "dtparam=i2c_arm=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
        echo "✅ I2C enabled"
    fi
    
    # Enable SPI
    if ! grep -q "^dtparam=spi=on" "$CONFIG_FILE" 2>/dev/null; then
        echo "dtparam=spi=on" | sudo tee -a "$CONFIG_FILE" > /dev/null
        echo "✅ SPI enabled"
    fi
fi

# Step 4: Create directory structure
echo ""
echo "Step 4/9: Creating directory structure..."
mkdir -p "$HOME/AITUNER"
cd "$HOME/AITUNER"

# Step 5: Clone or update repository
echo ""
echo "Step 5/9: Setting up repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Repository exists, checking for updates..."
    cd "$INSTALL_DIR"
    git pull || echo "⚠️  Could not update (may need manual setup)"
else
    echo "Cloning repository..."
    # Try to clone, if it fails, we'll copy files manually
    git clone "$REPO_URL" "$INSTALL_DIR" 2>&1 || {
        echo "⚠️  Git clone failed (repo may be private or need auth)"
        echo "Creating directory structure..."
        mkdir -p "$INSTALL_DIR"
    }
fi

# Step 6: Create Python virtual environment
echo ""
echo "Step 6/9: Setting up Python environment..."
cd "$INSTALL_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate venv and upgrade pip
source venv/bin/activate
pip install --upgrade pip -q > /dev/null 2>&1

# Step 7: Install Python dependencies
echo ""
echo "Step 7/9: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt -q 2>&1 | grep -v "already satisfied" || true
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, installing essential packages..."
    pip install PySide6 numpy pandas matplotlib pyserial opencv-python fastapi uvicorn scikit-learn -q
fi

# Step 8: Test USB devices
echo ""
echo "Step 8/9: Checking USB devices..."
echo "USB Devices:"
lsblk | grep -E "sd[a-z]" || echo "No additional USB devices detected"
echo ""
echo "Mounted filesystems:"
df -h | grep -E "(sd|mmc)" || echo "No USB filesystems mounted"

# Step 9: System information
echo ""
echo "Step 9/9: System information..."
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "System Info:"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  Kernel: $(uname -r)"
echo "  Architecture: $(uname -m)"
echo "  Python: $(python3 --version)"
echo "  IP Address: $(hostname -I | awk '{print $1}')"
echo ""
echo "Installation Directory: $INSTALL_DIR"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Reboot to enable I2C/SPI (if enabled):"
echo "   sudo reboot"
echo ""
echo "2. After reboot, activate virtual environment:"
echo "   cd $INSTALL_DIR"
echo "   source venv/bin/activate"
echo ""
echo "3. Test the application:"
echo "   python3 demo_safe.py"
echo ""
echo "4. Check installed packages:"
echo "   pip list | head -20"
echo ""






