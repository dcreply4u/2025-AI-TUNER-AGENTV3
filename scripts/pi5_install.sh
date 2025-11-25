#!/bin/bash
#
# Raspberry Pi 5 Installation Script for AI Tuner Agent
# Installs the application and dependencies
#
# Usage: ./pi5_install.sh [--dev]
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="/opt/ai-tuner-agent/venv"

echo "=========================================="
echo "AI Tuner Agent Installation for Pi 5"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo ""
echo "Installing Python dependencies..."
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    echo "Warning: requirements.txt not found"
    echo "Installing common dependencies..."
    pip install \
        PySide6 \
        python-can \
        isotp \
        pyserial \
        numpy \
        scipy \
        matplotlib \
        requests \
        psutil
fi

# Install development dependencies if requested
if [[ "$*" == *"--dev"* ]]; then
    echo ""
    echo "Installing development dependencies..."
    pip install pytest pytest-cov black flake8 mypy
fi

# Create necessary directories
echo ""
echo "Creating application directories..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/data/tune_map_database"
mkdir -p "$PROJECT_DIR/backups"

# Set permissions
chmod -R 755 "$PROJECT_DIR/logs"
chmod -R 755 "$PROJECT_DIR/data"

# Create systemd service file (optional)
echo ""
read -p "Create systemd service for auto-start? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/ai-tuner-agent.service"
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=AI Tuner Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/demo.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo "Service file created at $SERVICE_FILE"
    echo "To enable: sudo systemctl enable ai-tuner-agent"
    echo "To start: sudo systemctl start ai-tuner-agent"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Virtual environment: $VENV_DIR"
echo "Project directory: $PROJECT_DIR"
echo ""
echo "To activate the environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To run the application:"
echo "  cd $PROJECT_DIR"
echo "  python demo.py"
echo ""
echo "To test hardware detection:"
echo "  python scripts/test_hardware_detection.py"
echo ""



