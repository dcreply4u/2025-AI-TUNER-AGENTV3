#!/bin/bash
# Test script for splash screen and startup performance
# Run this on the Pi to test and debug startup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/test_splash_startup.log"
TIMEOUT=30

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Splash Screen & Startup Test"
echo "=========================================="
echo "Timestamp: $(date)"
echo "Project: $PROJECT_ROOT"
echo "Log file: $LOG_FILE"
echo ""

# Kill any existing instances
echo "[1/5] Killing existing instances..."
pkill -9 -f 'demo_safe.py' 2>/dev/null || true
pkill -9 -f 'python.*demo_safe' 2>/dev/null || true
sleep 2
echo "✓ Cleaned up"

# Check for splash image
echo ""
echo "[2/5] Checking for splash image..."
SPLASH_IMAGES=(
    "$PROJECT_ROOT/TelemetryIQgood9.jpg"
    "$PROJECT_ROOT/TelemetryIQgood9.png"
    "$PROJECT_ROOT/splash.jpg"
    "$PROJECT_ROOT/splash.png"
)

SPLASH_FOUND=""
for img in "${SPLASH_IMAGES[@]}"; do
    if [ -f "$img" ]; then
        SPLASH_FOUND="$img"
        echo "✓ Found splash image: $img"
        ls -lh "$img"
        break
    fi
done

if [ -z "$SPLASH_FOUND" ]; then
    echo "⚠ WARNING: No splash image found!"
    echo "  Checked: ${SPLASH_IMAGES[*]}"
fi

# Set display
echo ""
echo "[3/5] Setting up display..."
export DISPLAY=:0
xhost +local: 2>/dev/null || true
echo "✓ Display: $DISPLAY"

# Check Python and dependencies
echo ""
echo "[4/5] Checking Python environment..."
python3 --version
python3 -c "from PySide6.QtWidgets import QApplication; print('✓ PySide6 available')" 2>&1 || echo "⚠ PySide6 check failed"

# Run the demo with full logging
echo ""
echo "[5/5] Running demo_safe.py (timeout: ${TIMEOUT}s)..."
echo "----------------------------------------"
echo ""

# Clear old log
> "$LOG_FILE"

# Run with timeout and capture all output
timeout "$TIMEOUT" python3 demo_safe.py 2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?

echo ""
echo "----------------------------------------"
echo "Test completed. Exit code: ${EXIT_CODE:-0}"
echo ""

# Analyze the log
echo "=========================================="
echo "Log Analysis"
echo "=========================================="

if [ -f "$LOG_FILE" ]; then
    echo "Log file size: $(wc -l < "$LOG_FILE") lines"
    echo ""
    
    # Check for splash messages
    echo "Splash Screen Messages:"
    grep -i "\[SPLASH\]" "$LOG_FILE" || echo "  ⚠ No splash messages found"
    echo ""
    
    # Check for QApplication
    echo "QApplication Status:"
    grep -i "QApplication\|\[OK\]" "$LOG_FILE" | head -5 || echo "  ⚠ No QApplication messages"
    echo ""
    
    # Check for errors
    echo "Errors/Warnings:"
    grep -iE "error|warn|exception|traceback|failed" "$LOG_FILE" | head -10 || echo "  ✓ No errors found"
    echo ""
    
    # Check startup timing
    echo "Startup Sequence:"
    grep -E "\[STEP|\[OK\]|\[SUCCESS\]" "$LOG_FILE" || echo "  ⚠ No startup sequence messages"
    echo ""
    
    # Show last 20 lines
    echo "Last 20 lines of output:"
    tail -20 "$LOG_FILE"
    echo ""
else
    echo "⚠ Log file not created!"
fi

echo "=========================================="
echo "Full log available at: $LOG_FILE"
echo "=========================================="

exit ${EXIT_CODE:-0}

