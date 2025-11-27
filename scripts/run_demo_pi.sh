#!/bin/bash
# Run demo on Pi with proper display setup

cd ~/AITUNER/2025-AI-TUNER-AGENTV3

# Set display (use :0 for local display, or :1 if needed)
export DISPLAY=:0

# Check if display is available
if [ -z "$DISPLAY" ]; then
    echo "ERROR: No display set. Trying :0..."
    export DISPLAY=:0
fi

# Allow X server connections (if needed)
xhost +local: 2>/dev/null

echo "Starting AI Tuner Demo..."
echo "Display: $DISPLAY"
echo ""

# Run the demo
python3 demo_safe.py

