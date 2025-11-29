#!/usr/bin/env python3
"""Check what GPS data is currently being generated."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from interfaces.waveshare_gps_hat import get_gps_hat
import time

print("=" * 60)
print("Checking GPS Data Generation")
print("=" * 60)
print()

# Try hardware mode first
print("1. Testing hardware mode (auto-detect)...")
gps = get_gps_hat(use_simulator=False, auto_detect=True)
gps.connect()

status = gps.get_status()
print(f"   Status: {status}")
print(f"   Simulator mode: {gps.use_simulator}")
print(f"   Connected: {gps.connected}")
print(f"   Port: {gps.port}")

print("\n2. Reading GPS fixes...")
for i in range(3):
    fix = gps.read_fix()
    if fix:
        if hasattr(fix, 'latitude'):
            print(f"   Fix {i+1}:")
            print(f"     Latitude: {fix.latitude:.6f}")
            print(f"     Longitude: {fix.longitude:.6f}")
            print(f"     Speed: {fix.speed_mps:.2f} m/s ({fix.speed_mps * 2.237:.1f} mph)")
            print(f"     Heading: {fix.heading:.1f}°")
            print(f"     Altitude: {fix.altitude_m:.1f} m" if fix.altitude_m else "     Altitude: N/A")
            print(f"     Satellites: {fix.satellites}" if fix.satellites else "     Satellites: N/A")
            print(f"     Data source: {'SIMULATOR' if gps.use_simulator else 'HARDWARE'}")
        else:
            print(f"   Fix {i+1}: {fix}")
    else:
        print(f"   Fix {i+1}: No data")
    time.sleep(0.5)

print("\n3. Summary:")
if gps.use_simulator:
    print("   ✓ GPS is generating SIMULATED data")
    print("   ⚠ No real GPS data (antenna not connected or no satellites)")
else:
    print("   ✓ GPS is generating REAL data from hardware")
    print("   ✓ GPS hardware is working!")

gps.disconnect()

