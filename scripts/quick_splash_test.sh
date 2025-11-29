#!/bin/bash
# Quick test for splash screen - captures key output

cd ~/AITUNER/2025-AI-TUNER-AGENTV3

# Kill existing
pkill -9 -f 'demo_safe.py' 2>/dev/null || true
sleep 1

# Setup display
export DISPLAY=:0
xhost +local: 2>/dev/null || true

# Run and capture output
echo "Starting demo_safe.py..."
timeout 15 python3 demo_safe.py 2>&1 | tee /tmp/splash_test.log &
DEMO_PID=$!

# Wait a bit for startup
sleep 5

# Check for splash messages
echo ""
echo "=== SPLASH SCREEN STATUS ==="
grep -i "SPLASH" /tmp/splash_test.log || echo "No splash messages found"
echo ""

# Check positioning
echo "=== POSITIONING INFO ==="
grep -iE "Positioned|Scaled|Screen:" /tmp/splash_test.log || echo "No positioning info"
echo ""

# Show last 15 lines
echo "=== LAST 15 LINES ==="
tail -15 /tmp/splash_test.log
echo ""

# Cleanup
wait $DEMO_PID 2>/dev/null || true
pkill -9 -f 'demo_safe.py' 2>/dev/null || true

