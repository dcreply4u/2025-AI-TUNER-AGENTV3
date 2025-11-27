#!/usr/bin/env python3
"""
Quick test script for Sense HAT (AstroPi) IMU support.

Run this on your Raspberry Pi 5 to verify Sense HAT is working:
    python3 scripts/test_sense_hat.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from interfaces.imu_interface import IMUInterface, IMUType
    print("✅ IMU Interface imported successfully")
except ImportError as e:
    print(f"❌ Failed to import IMU Interface: {e}")
    sys.exit(1)

def test_sense_hat():
    """Test Sense HAT IMU."""
    print("\n" + "="*60)
    print("Testing Sense HAT (AstroPi) IMU")
    print("="*60 + "\n")
    
    # Try auto-detect first
    print("1. Testing auto-detection...")
    try:
        imu = IMUInterface(imu_type=IMUType.AUTO_DETECT)
        print(f"   ✅ Auto-detected IMU type: {imu.imu_type.value}")
    except Exception as e:
        print(f"   ❌ Auto-detection failed: {e}")
        return False
    
    # Try explicit Sense HAT
    print("\n2. Testing explicit Sense HAT initialization...")
    try:
        imu = IMUInterface(imu_type=IMUType.SENSE_HAT)
        if imu.is_connected():
            print("   ✅ Sense HAT connected successfully")
        else:
            print("   ⚠️  Sense HAT not connected (may need hardware or library)")
            return False
    except Exception as e:
        print(f"   ❌ Sense HAT initialization failed: {e}")
        print("   💡 Try: sudo apt-get install sense-hat")
        return False
    
    # Test reading data
    print("\n3. Testing data reading...")
    try:
        reading = imu.read()
        if reading:
            print("   ✅ Successfully read IMU data:")
            print(f"      Accelerometer: X={reading.accel_x:.2f}, Y={reading.accel_y:.2f}, Z={reading.accel_z:.2f} m/s²")
            print(f"      Gyroscope:     X={reading.gyro_x:.2f}, Y={reading.gyro_y:.2f}, Z={reading.gyro_z:.2f} deg/s")
            if reading.mag_x is not None:
                print(f"      Magnetometer:  X={reading.mag_x:.2f}, Y={reading.mag_y:.2f}, Z={reading.mag_z:.2f} μT")
            if reading.temperature is not None:
                print(f"      Temperature:   {reading.temperature:.1f} °C")
        else:
            print("   ❌ Failed to read IMU data")
            return False
    except Exception as e:
        print(f"   ❌ Read error: {e}")
        return False
    
    # Test multiple readings
    print("\n4. Testing continuous readings (5 samples)...")
    try:
        for i in range(5):
            reading = imu.read()
            if reading:
                accel_mag = (reading.accel_x**2 + reading.accel_y**2 + reading.accel_z**2)**0.5
                print(f"   Sample {i+1}: Accel magnitude = {accel_mag:.2f} m/s²")
            time.sleep(0.1)
        print("   ✅ Continuous readings working")
    except Exception as e:
        print(f"   ❌ Continuous read error: {e}")
        return False
    
    # Test status
    print("\n5. Testing status reporting...")
    try:
        status = imu.get_status()
        print(f"   ✅ Status: {status}")
    except Exception as e:
        print(f"   ❌ Status error: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ All tests passed! Sense HAT is working correctly.")
    print("="*60 + "\n")
    print("💡 The Sense HAT will be automatically detected when you run the demo.")
    print("💡 It will be used for Kalman filter GPS/IMU fusion.\n")
    
    return True

if __name__ == "__main__":
    success = test_sense_hat()
    sys.exit(0 if success else 1)

