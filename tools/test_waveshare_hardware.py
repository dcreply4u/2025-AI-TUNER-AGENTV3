#!/usr/bin/env python3
"""
Test Waveshare Environmental Sensor HAT hardware connection.

This script tests the actual hardware connection (not simulator).
"""

import sys
import time
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*80)
print("WAVESHARE ENVIRONMENTAL HAT - HARDWARE CONNECTION TEST")
print("="*80)

# Test hardware connection (not simulator)
print("\n[1] Attempting hardware connection...")
try:
    from interfaces.waveshare_environmental_hat import get_environmental_hat
    
    # Try hardware mode (not simulator)
    hat = get_environmental_hat(use_simulator=False)
    print("✅ HAT instance created (hardware mode)")
    
    # Try to connect
    print("\n[2] Connecting to hardware...")
    if hat.connect():
        print("✅ Hardware connection successful!")
        print(f"   Connection method: {'Adafruit library' if hat.bme280 else 'smbus2' if hat.bus else 'Simulator (fallback)'}")
        
        # Read multiple samples to verify stability
        print("\n[3] Reading hardware data (5 samples)...")
        readings = []
        for i in range(5):
            reading = hat.read()
            if reading:
                readings.append(reading)
                print(f"   Sample {i+1}: {reading.temperature_c:.2f}°C, {reading.humidity_percent:.1f}%, {reading.pressure_kpa:.2f} kPa")
                time.sleep(0.5)
            else:
                print(f"   Sample {i+1}: ❌ Failed to read")
        
        if readings:
            print(f"\n✅ Successfully read {len(readings)} samples")
            
            # Calculate averages
            avg_temp = sum(r.temperature_c for r in readings) / len(readings)
            avg_humidity = sum(r.humidity_percent for r in readings) / len(readings)
            avg_pressure = sum(r.pressure_kpa for r in readings) / len(readings)
            
            print(f"\n📊 Average Values:")
            print(f"   Temperature: {avg_temp:.2f}°C ({avg_temp * 9/5 + 32:.2f}°F)")
            print(f"   Humidity: {avg_humidity:.1f}%")
            print(f"   Pressure: {avg_pressure:.2f} kPa ({avg_pressure * 0.145038:.2f} PSI)")
            
            # Verify values are reasonable
            temp_ok = -40 <= avg_temp <= 85  # BME280 operating range
            humidity_ok = 0 <= avg_humidity <= 100
            pressure_ok = 30 <= avg_pressure <= 120  # Reasonable atmospheric pressure
            
            print(f"\n✅ Value Validation:")
            print(f"   Temperature in range: {temp_ok} ({avg_temp:.2f}°C)")
            print(f"   Humidity in range: {humidity_ok} ({avg_humidity:.1f}%)")
            print(f"   Pressure in range: {pressure_ok} ({avg_pressure:.2f} kPa)")
            
            if temp_ok and humidity_ok and pressure_ok:
                print("\n🎉 HARDWARE IS WORKING CORRECTLY!")
                print("   All sensor readings are within expected ranges.")
            else:
                print("\n⚠️  Some values outside expected range - may need calibration")
            
            # Test integration format
            print("\n[4] Testing integration format...")
            conditions = hat.get_environmental_conditions()
            if conditions:
                print("✅ get_environmental_conditions() works")
                print(f"   Format: {list(conditions.keys())}")
                if all(k in conditions for k in ['temperature_c', 'humidity_percent', 'barometric_pressure_kpa']):
                    print("✅ Format matches VirtualDyno requirements")
                else:
                    print("❌ Missing required keys")
        else:
            print("❌ Failed to read any samples")
            sys.exit(1)
            
    else:
        print("❌ Hardware connection failed")
        print("\nTroubleshooting:")
        print("  1. Check I2C is enabled: sudo raspi-config → Interface Options → I2C")
        print("  2. Check device is detected: sudo i2cdetect -y 1")
        print("  3. Check library is installed: pip install adafruit-circuitpython-bme280")
        print("  4. Check permissions: sudo usermod -a -G i2c $USER")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTroubleshooting:")
    print("  - Install library: pip install adafruit-circuitpython-bme280")
    print("  - Or fallback: pip install smbus2")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ HARDWARE VALIDATION COMPLETE")
print("="*80)


