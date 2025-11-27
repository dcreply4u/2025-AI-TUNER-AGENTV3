#!/usr/bin/env python3
"""
Simple CAN Hardware Test

Quick test to verify CAN hardware detection is working.
Run this on the Raspberry Pi.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*60)
print("CAN Hardware Detection Test")
print("="*60)

# Test 1: Import
print("\n1. Testing imports...")
try:
    from interfaces.can_hardware_detector import detect_can_hardware, is_waveshare_can
    from interfaces.can_interface import OptimizedCANInterface
    print("   ✓ Imports successful")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Detect hardware
print("\n2. Detecting CAN hardware...")
try:
    interfaces = detect_can_hardware()
    if interfaces:
        print(f"   ✓ Found {len(interfaces)} CAN interface(s):")
        for name, info in interfaces.items():
            waveshare = " (Waveshare)" if is_waveshare_can(name) else ""
            print(f"     - {name}: {info.hardware_type} - {info.state}{waveshare}")
    else:
        print("   ⚠️  No CAN interfaces detected")
        print("   (This is OK if CAN HAT is not installed/configured)")
except Exception as e:
    print(f"   ✗ Detection failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check system
print("\n3. Checking system CAN interfaces...")
import os
if os.path.exists("/sys/class/net"):
    can_ifaces = [f for f in os.listdir("/sys/class/net") if f.startswith("can")]
    if can_ifaces:
        print(f"   ✓ Found in /sys/class/net: {', '.join(can_ifaces)}")
    else:
        print("   ⚠️  No CAN interfaces in /sys/class/net")

# Test 4: Try connection (if can0 exists)
print("\n4. Testing CAN interface connection...")
if interfaces and "can0" in interfaces:
    try:
        can = OptimizedCANInterface(channel="can0", bitrate=500000)
        if can.connect():
            print("   ✓ Successfully connected to can0")
            stats = can.get_statistics()
            print(f"     Messages: {stats.total_messages}, Errors: {stats.error_frames}")
            can.disconnect()
        else:
            print("   ⚠️  Could not connect (interface may need to be brought up)")
    except Exception as e:
        print(f"   ⚠️  Connection test failed: {e}")
else:
    print("   ⚠️  Skipped (can0 not detected)")

print("\n" + "="*60)
print("Test complete!")
print("="*60)

