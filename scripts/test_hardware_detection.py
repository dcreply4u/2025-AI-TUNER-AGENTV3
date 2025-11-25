#!/usr/bin/env python3
"""
Hardware Detection Test Script for Raspberry Pi 5
Tests all hardware detection and HAT detection capabilities
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

def test_platform_detection():
    """Test hardware platform detection."""
    print("\n" + "="*60)
    print("Testing Platform Detection")
    print("="*60)
    
    try:
        from core.hardware_platform import detect_platform, get_platform_config
        
        platform = detect_platform()
        config = get_platform_config()
        
        print(f"Detected Platform: {platform}")
        print(f"Platform Config:")
        for key, value in config.items():
            if key != 'gpio_config':  # Skip detailed GPIO config
                print(f"  {key}: {value}")
        
        if platform == "raspberry_pi_5":
            print("✅ Raspberry Pi 5 detected correctly!")
        else:
            print(f"⚠️  Expected 'raspberry_pi_5', got '{platform}'")
        
        return True
    except Exception as e:
        print(f"❌ Platform detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hat_detection():
    """Test HAT detection."""
    print("\n" + "="*60)
    print("Testing HAT Detection")
    print("="*60)
    
    try:
        from core.hat_detector import HATDetector
        
        detector = HATDetector()
        hats = detector.detect_all_hats()
        
        print(f"Detected HATs: {len(hats)}")
        
        if not hats:
            print("ℹ️  No HATs detected (this is normal if no HATs are installed)")
        else:
            for hat in hats:
                print(f"\n  HAT: {hat['name']}")
                print(f"    Type: {hat['type']}")
                print(f"    Interface: {hat['interface']}")
                if 'address' in hat:
                    print(f"    Address: {hat['address']}")
                if 'channels' in hat:
                    print(f"    Channels: {hat['channels']}")
        
        # Test specific HAT types
        print("\nSpecific HAT Checks:")
        
        can_hats = detector.detect_can_hats()
        print(f"  CAN HATs: {len(can_hats)}")
        for hat in can_hats:
            print(f"    - {hat['name']} ({hat['interface']})")
        
        gps_hats = detector.detect_gps_hats()
        print(f"  GPS HATs: {len(gps_hats)}")
        for hat in gps_hats:
            print(f"    - {hat['name']} ({hat['interface']})")
        
        gpio_hats = detector.detect_gpio_hats()
        print(f"  GPIO HATs: {len(gpio_hats)}")
        for hat in gpio_hats:
            print(f"    - {hat['name']} ({hat['interface']})")
        
        return True
    except Exception as e:
        print(f"❌ HAT detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_i2c_devices():
    """Test I2C device detection."""
    print("\n" + "="*60)
    print("Testing I2C Devices")
    print("="*60)
    
    try:
        import subprocess
        
        # Try to use i2cdetect if available
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("I2C Bus 1 devices:")
            print(result.stdout)
        else:
            print("ℹ️  i2cdetect not available or I2C not enabled")
            print("   Enable I2C in raspi-config or /boot/config.txt")
        
        return True
    except FileNotFoundError:
        print("ℹ️  i2cdetect not installed. Install with: sudo apt-get install i2c-tools")
        return False
    except Exception as e:
        print(f"⚠️  I2C test error: {e}")
        return False

def test_spi_devices():
    """Test SPI device detection."""
    print("\n" + "="*60)
    print("Testing SPI Devices")
    print("="*60)
    
    try:
        import subprocess
        
        # Check if SPI devices exist
        spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1', '/dev/spidev1.0', '/dev/spidev1.1']
        found = []
        
        for device in spi_devices:
            if os.path.exists(device):
                found.append(device)
        
        if found:
            print(f"SPI devices found: {', '.join(found)}")
        else:
            print("ℹ️  No SPI devices found")
            print("   Enable SPI in raspi-config or /boot/config.txt")
        
        return True
    except Exception as e:
        print(f"⚠️  SPI test error: {e}")
        return False

def test_can_interfaces():
    """Test CAN interface detection."""
    print("\n" + "="*60)
    print("Testing CAN Interfaces")
    print("="*60)
    
    try:
        import subprocess
        
        # Check for CAN interfaces
        result = subprocess.run(['ip', 'link', 'show'], 
                              capture_output=True, text=True, timeout=5)
        
        can_interfaces = [line for line in result.stdout.split('\n') 
                         if 'can' in line.lower()]
        
        if can_interfaces:
            print("CAN interfaces found:")
            for iface in can_interfaces:
                print(f"  {iface.strip()}")
        else:
            print("ℹ️  No CAN interfaces found")
            print("   Install CAN HAT and configure overlay in /boot/config.txt")
            print("   Example: dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25")
        
        return True
    except Exception as e:
        print(f"⚠️  CAN test error: {e}")
        return False

def test_gpio():
    """Test GPIO access."""
    print("\n" + "="*60)
    print("Testing GPIO Access")
    print("="*60)
    
    try:
        # Try to import RPi.GPIO
        try:
            import RPi.GPIO as GPIO
            print("✅ RPi.GPIO available")
            
            # Try to set mode (this will fail if not on Pi, but that's OK)
            try:
                GPIO.setmode(GPIO.BCM)
                print("✅ GPIO mode set successfully")
                GPIO.cleanup()
            except Exception as e:
                print(f"⚠️  GPIO access test: {e}")
                print("   This may be normal if not running on a Pi")
            
            return True
        except ImportError:
            print("ℹ️  RPi.GPIO not installed")
            print("   Install with: pip install RPi.GPIO")
            return False
    except Exception as e:
        print(f"⚠️  GPIO test error: {e}")
        return False

def test_usb_devices():
    """Test USB device detection."""
    print("\n" + "="*60)
    print("Testing USB Devices")
    print("="*60)
    
    try:
        import subprocess
        
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            devices = result.stdout.strip().split('\n')
            print(f"USB devices found: {len(devices)}")
            for device in devices[:10]:  # Show first 10
                print(f"  {device}")
            if len(devices) > 10:
                print(f"  ... and {len(devices) - 10} more")
        else:
            print("ℹ️  lsusb not available")
        
        return True
    except FileNotFoundError:
        print("ℹ️  lsusb not installed")
        return False
    except Exception as e:
        print(f"⚠️  USB test error: {e}")
        return False

def main():
    """Run all hardware detection tests."""
    print("="*60)
    print("Raspberry Pi 5 Hardware Detection Test")
    print("="*60)
    
    results = {}
    
    results['platform'] = test_platform_detection()
    results['hats'] = test_hat_detection()
    results['i2c'] = test_i2c_devices()
    results['spi'] = test_spi_devices()
    results['can'] = test_can_interfaces()
    results['gpio'] = test_gpio()
    results['usb'] = test_usb_devices()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "⚠️  INFO/SKIP"
        print(f"{test.upper():15} {status}")
    
    print(f"\nTests completed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print("ℹ️  Some tests were informational or skipped (this is normal)")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())



