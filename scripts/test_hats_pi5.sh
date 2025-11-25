#!/bin/bash
# Test script for HAT detection on Raspberry Pi 5
# Run this after installing HATs to verify detection

set -e

echo "=========================================="
echo "🔍 HAT Detection Test - Raspberry Pi 5"
echo "=========================================="
echo ""

INSTALL_DIR="$HOME/AITUNER/AI-TUNER-AGENT"

# Check if repository exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ AI-TUNER-AGENT not found at $INSTALL_DIR"
    exit 1
fi

cd "$INSTALL_DIR"

# Activate virtual environment
if [ -d "$HOME/AITUNER/venv" ]; then
    source "$HOME/AITUNER/venv/bin/activate"
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

echo "Step 1: Checking system interfaces..."
echo ""

# Check CAN interfaces
echo "CAN Interfaces:"
CAN_IFS=$(ip link show 2>/dev/null | grep -o "can[0-9]*" || echo "None")
if [ "$CAN_IFS" != "None" ] && [ -n "$CAN_IFS" ]; then
    for iface in $CAN_IFS; do
        STATUS=$(ip link show $iface 2>/dev/null | grep -o "state [A-Z]*" || echo "unknown")
        echo "  ✅ $iface - $STATUS"
    done
else
    echo "  ❌ No CAN interfaces found"
fi

echo ""
echo "I2C Devices:"
if command -v i2cdetect &> /dev/null; then
    echo "Scanning I2C bus 1..."
    i2cdetect -y 1 2>/dev/null | tail -n +2 || echo "  ⚠️  i2cdetect failed (I2C may not be enabled)"
else
    echo "  ⚠️  i2cdetect not installed"
fi

echo ""
echo "SPI Devices:"
if [ -d /sys/bus/spi/devices ]; then
    SPI_DEVICES=$(ls /sys/bus/spi/devices/ 2>/dev/null | wc -l)
    if [ "$SPI_DEVICES" -gt 0 ]; then
        echo "  ✅ Found $SPI_DEVICES SPI device(s):"
        ls /sys/bus/spi/devices/ | head -5
    else
        echo "  ❌ No SPI devices found"
    fi
else
    echo "  ❌ SPI bus not available"
fi

echo ""
echo "UART Devices:"
UART_DEVICES=$(ls /dev/ttyAMA* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "")
if [ -n "$UART_DEVICES" ]; then
    echo "  ✅ Found UART devices:"
    for dev in $UART_DEVICES; do
        echo "    - $dev"
    done
else
    echo "  ❌ No UART devices found"
fi

echo ""
echo "Step 2: Running HAT Detection..."
echo ""

python3 << 'PYTHON_SCRIPT'
import sys
import os

# Add project to path
sys.path.insert(0, os.getcwd())

try:
    from core.hat_detector import HATDetector
    
    print("Detecting HATs...")
    config = HATDetector.detect_all_hats()
    
    print("")
    print("==========================================")
    print("HAT Detection Results")
    print("==========================================")
    print("")
    
    print(f"CAN HATs: {len(config.can_hats)}")
    for hat in config.can_hats:
        print(f"  ✅ {hat.name}")
        print(f"     Type: {hat.type}")
        print(f"     Detected via: {hat.detected_via}")
        if 'can_standard' in hat.capabilities:
            print(f"     CAN Standard: {hat.capabilities['can_standard']}")
        if 'max_bitrate' in hat.capabilities:
            print(f"     Max Bitrate: {hat.capabilities['max_bitrate']} bps")
        print("")
    
    print(f"GPS HATs: {len(config.gps_hats)}")
    for hat in config.gps_hats:
        print(f"  ✅ {hat.name}")
        print(f"     Detected via: {hat.detected_via}")
        print("")
    
    print(f"IMU Sensors: {len(config.imu_sensors)}")
    for hat in config.imu_sensors:
        print(f"  ✅ {hat.name}")
        print(f"     I2C Address: 0x{hat.i2c_address:X}" if hat.i2c_address else "     I2C Address: N/A")
        print("")
    
    print(f"GPIO Expanders: {len(config.gpio_expanders)}")
    for hat in config.gpio_expanders:
        print(f"  ✅ {hat.name}")
        print(f"     I2C Address: 0x{hat.i2c_address:X}" if hat.i2c_address else "     I2C Address: N/A")
        print("")
    
    print(f"ADC Boards: {len(config.adc_boards)}")
    for hat in config.adc_boards:
        print(f"  ✅ {hat.name}")
        print(f"     I2C Address: 0x{hat.i2c_address:X}" if hat.i2c_address else "     I2C Address: N/A")
        print("")
    
    print(f"Combined HATs: {len(config.combined_hats)}")
    for hat in config.combined_hats:
        print(f"  ✅ {hat.name}")
        print("")
    
    print("==========================================")
    print(f"Total CAN Buses: {config.total_can_buses}")
    print(f"GPS Available: {'Yes' if config.has_gps else 'No'}")
    print(f"IMU Available: {'Yes' if config.has_imu else 'No'}")
    print("==========================================")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're in the AI-TUNER-AGENT directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "Step 3: Testing CAN Interface (if available)..."
if ip link show can0 &>/dev/null; then
    echo "Testing can0..."
    if ip link show can0 | grep -q "UP"; then
        echo "  ✅ can0 is UP"
        if command -v candump &> /dev/null; then
            echo "  Running candump test (5 seconds)..."
            timeout 5 candump can0 2>/dev/null && echo "  ✅ CAN bus is receiving messages" || echo "  ⚠️  No CAN messages received (this is normal if no devices connected)"
        else
            echo "  ⚠️  candump not installed"
        fi
    else
        echo "  ⚠️  can0 is DOWN - bring it up with:"
        echo "     sudo ip link set can0 up type can bitrate 500000"
    fi
else
    echo "  ❌ can0 interface not found"
fi

echo ""
echo "=========================================="
echo "✅ HAT Detection Test Complete"
echo "=========================================="






