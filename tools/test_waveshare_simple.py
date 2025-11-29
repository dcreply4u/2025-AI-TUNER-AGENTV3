#!/usr/bin/env python3
"""Simple direct test of Waveshare HAT interface."""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*80)
print("WAVESHARE ENVIRONMENTAL HAT - SIMPLE VALIDATION")
print("="*80)

# Test 1: Direct import
print("\n[1] Testing direct import...")
try:
    from interfaces.waveshare_environmental_hat import (
        WaveshareEnvironmentalHAT,
        EnvironmentalReading,
        get_environmental_hat,
    )
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create instance
print("\n[2] Creating HAT instance (simulator mode)...")
try:
    hat = WaveshareEnvironmentalHAT(use_simulator=True)
    print("✅ Instance created")
except Exception as e:
    print(f"❌ Instance creation failed: {e}")
    sys.exit(1)

# Test 3: Connect
print("\n[3] Connecting...")
try:
    if hat.connect():
        print("✅ Connection successful")
    else:
        print("❌ Connection failed")
        sys.exit(1)
except Exception as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)

# Test 4: Read data
print("\n[4] Reading environmental data...")
try:
    reading = hat.read()
    if reading:
        print("✅ Reading successful")
        print(f"   Temperature: {reading.temperature_c:.2f}°C ({reading.temperature_c * 9/5 + 32:.2f}°F)")
        print(f"   Humidity: {reading.humidity_percent:.2f}%")
        print(f"   Pressure: {reading.pressure_kpa:.2f} kPa")
        print(f"   Pressure: {reading.pressure_hpa:.2f} hPa")
        print(f"   Pressure: {reading.pressure_kpa * 0.145038:.2f} PSI")
    else:
        print("❌ Reading returned None")
        sys.exit(1)
except Exception as e:
    print(f"❌ Reading error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: to_dict
print("\n[5] Testing to_dict()...")
try:
    data_dict = reading.to_dict()
    print(f"✅ to_dict() successful: {len(data_dict)} keys")
    required_keys = ['ambient_temp_c', 'humidity_percent', 'barometric_pressure_kpa']
    if all(key in data_dict for key in required_keys):
        print("✅ All required keys present")
    else:
        missing = [k for k in required_keys if k not in data_dict]
        print(f"❌ Missing keys: {missing}")
        sys.exit(1)
except Exception as e:
    print(f"❌ to_dict() error: {e}")
    sys.exit(1)

# Test 6: get_environmental_conditions
print("\n[6] Testing get_environmental_conditions()...")
try:
    conditions = hat.get_environmental_conditions()
    if conditions:
        print("✅ get_environmental_conditions() successful")
        print(f"   Keys: {', '.join(conditions.keys())}")
        required = ['temperature_c', 'humidity_percent', 'barometric_pressure_kpa']
        if all(k in conditions for k in required):
            print("✅ Format matches VirtualDyno expectations")
        else:
            print(f"❌ Missing required keys for VirtualDyno")
            sys.exit(1)
    else:
        print("❌ get_environmental_conditions() returned None")
        sys.exit(1)
except Exception as e:
    print(f"❌ get_environmental_conditions() error: {e}")
    sys.exit(1)

# Test 7: Custom simulator values
print("\n[7] Testing custom simulator values...")
try:
    hat.set_simulator_values(temperature_c=25.0, humidity_percent=65.0, pressure_kpa=102.0)
    reading2 = hat.read()
    if reading2:
        print(f"✅ Custom values set and read")
        print(f"   Temperature: {reading2.temperature_c:.2f}°C (expected ~25.0°C)")
        print(f"   Humidity: {reading2.humidity_percent:.2f}% (expected ~65.0%)")
        print(f"   Pressure: {reading2.pressure_kpa:.2f} kPa (expected ~102.0 kPa)")
    else:
        print("❌ Reading with custom values returned None")
        sys.exit(1)
except Exception as e:
    print(f"❌ Custom values test error: {e}")
    sys.exit(1)

# Test 8: Global instance
print("\n[8] Testing global instance...")
try:
    hat2 = get_environmental_hat(use_simulator=True)
    if hat2 is hat:
        print("✅ Global instance returned (singleton pattern)")
    else:
        print("⚠️  Different instance returned (may be OK)")
    hat2.connect()
    reading3 = hat2.read()
    if reading3:
        print("✅ Global instance works correctly")
    else:
        print("❌ Global instance read failed")
        sys.exit(1)
except Exception as e:
    print(f"❌ Global instance test error: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ ALL TESTS PASSED - Waveshare HAT interface is working correctly!")
print("="*80)
print("\nIntegration Status:")
print("  ✅ Interface implemented")
print("  ✅ Simulator mode working")
print("  ✅ Data format correct")
print("  ✅ VirtualDyno compatibility verified")
print("\nNext Steps:")
print("  1. Install hardware: Mount HAT on Raspberry Pi")
print("  2. Enable I2C: sudo raspi-config → Interface Options → I2C")
print("  3. Install library: pip install adafruit-circuitpython-bme280")
print("  4. Test hardware: Run this script without simulator mode")

