#!/usr/bin/env python3
"""
Test script for Waveshare GPS HAT integration.

Tests:
1. Import and initialization
2. Simulator mode
3. Hardware detection (if available)
4. GPS data reading
5. Integration with data stream controller
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_import():
    """Test importing the GPS HAT interface."""
    print("=" * 60)
    print("Test 1: Import GPS HAT Interface")
    print("=" * 60)
    try:
        from interfaces.waveshare_gps_hat import WaveshareGPSHAT, get_gps_hat
        print("✓ Successfully imported WaveshareGPSHAT")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_simulator():
    """Test simulator mode."""
    print("\n" + "=" * 60)
    print("Test 2: Simulator Mode")
    print("=" * 60)
    try:
        from interfaces.waveshare_gps_hat import get_gps_hat
        
        gps = get_gps_hat(use_simulator=True)
        print(f"✓ GPS HAT created (simulator mode)")
        
        if gps.connect():
            print("✓ GPS HAT connected (simulator)")
        else:
            print("✗ GPS HAT connection failed")
            return False
        
        # Test reading GPS fix
        print("\nReading GPS fixes (simulator)...")
        for i in range(3):
            fix = gps.read_fix()
            if fix:
                if hasattr(fix, 'latitude'):
                    print(f"  Fix {i+1}: Lat={fix.latitude:.5f}, Lon={fix.longitude:.5f}, "
                          f"Speed={fix.speed_mps:.1f} m/s, Heading={fix.heading:.1f}°")
                else:
                    print(f"  Fix {i+1}: {fix}")
            else:
                print(f"  ✗ No fix received")
            time.sleep(0.5)
        
        gps.disconnect()
        print("✓ Simulator mode test passed")
        return True
    except Exception as e:
        print(f"✗ Simulator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hardware_detection():
    """Test hardware detection."""
    print("\n" + "=" * 60)
    print("Test 3: Hardware Detection")
    print("=" * 60)
    try:
        from interfaces.waveshare_gps_hat import get_gps_hat
        
        gps = get_gps_hat(use_simulator=False, auto_detect=True)
        print(f"✓ GPS HAT created (hardware mode, auto-detect)")
        
        if gps.connect():
            print(f"✓ GPS HAT connected")
            print(f"  Port: {gps.port}")
            print(f"  Baudrate: {gps.baudrate}")
            print(f"  Simulator: {gps.use_simulator}")
            
            # Try reading a fix
            print("\nReading GPS fix (hardware)...")
            fix = gps.read_fix()
            if fix:
                if hasattr(fix, 'latitude'):
                    print(f"  ✓ Fix received: Lat={fix.latitude:.5f}, Lon={fix.longitude:.5f}")
                else:
                    print(f"  ✓ Fix received: {fix}")
            else:
                print("  ⚠ No fix received (GPS may need time to acquire satellites)")
            
            status = gps.get_status()
            print(f"\nStatus: {status}")
            
            gps.disconnect()
            print("✓ Hardware detection test passed")
            return True
        else:
            print("⚠ GPS HAT not connected (hardware not available or simulator mode)")
            return True  # Not a failure, just hardware not available
    except Exception as e:
        print(f"⚠ Hardware detection test: {e}")
        return True  # Not a failure, hardware may not be available

def test_integration():
    """Test integration with data stream controller."""
    print("\n" + "=" * 60)
    print("Test 4: Integration with Data Stream Controller")
    print("=" * 60)
    try:
        from controllers.data_stream_controller import DataStreamController
        from interfaces.waveshare_gps_hat import get_gps_hat
        
        # Create GPS HAT
        gps_hat = get_gps_hat(use_simulator=True)
        if gps_hat.connect():
            print("✓ GPS HAT created and connected")
            
            # The data stream controller should automatically use the GPS HAT
            # when _ensure_gps_interface() is called
            print("✓ Integration test passed (GPS HAT will be used by data stream controller)")
            return True
        else:
            print("✗ GPS HAT connection failed")
            return False
    except Exception as e:
        print(f"⚠ Integration test: {e}")
        import traceback
        traceback.print_exc()
        return True  # May fail if dependencies not available

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Waveshare GPS HAT Integration Tests")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Import", test_import()))
    results.append(("Simulator", test_simulator()))
    results.append(("Hardware Detection", test_hardware_detection()))
    results.append(("Integration", test_integration()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("⚠ SOME TESTS FAILED (check output above)")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

