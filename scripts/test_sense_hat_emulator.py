#!/usr/bin/env python3
"""Test script to verify Sense HAT emulator is working."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sense_hat import SenseHat
    print("✓ sense_hat library imported")
    
    sense = SenseHat()
    print("✓ SenseHat object created")
    
    sense.set_imu_config(True, True, True)
    print("✓ IMU config set (Compass, Gyro, Accel)")
    
    accel = sense.get_accelerometer_raw()
    print(f"✓ Accelerometer: x={accel['x']:.3f}, y={accel['y']:.3f}, z={accel['z']:.3f}")
    
    gyro = sense.get_gyroscope_raw()
    print(f"✓ Gyroscope: x={gyro['x']:.3f}, y={gyro['y']:.3f}, z={gyro['z']:.3f}")
    
    mag = sense.get_compass_raw()
    print(f"✓ Magnetometer: x={mag['x']:.3f}, y={mag['y']:.3f}, z={mag['z']:.3f}")
    
    temp = sense.get_temperature()
    print(f"✓ Temperature: {temp:.2f}°C")
    
    print("\n✓✓✓ Sense HAT emulator is working! ✓✓✓")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

