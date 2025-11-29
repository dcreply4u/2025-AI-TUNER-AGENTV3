#!/usr/bin/env python3
"""
Waveshare GPS HAT Detection Script

Detects and tests Waveshare GPS HAT on Raspberry Pi 5.
Checks for UART devices and GPS NMEA data.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_uart_devices():
    """Check for available UART devices."""
    uart_devices = []
    common_ports = [
        "/dev/ttyAMA0",  # Primary UART on Pi
        "/dev/ttyAMA1",  # Secondary UART on Pi 5
        "/dev/ttyUSB0",  # USB serial
        "/dev/ttyUSB1",  # USB serial
        "/dev/serial0",  # Alias for primary UART
        "/dev/serial1",  # Alias for secondary UART
    ]
    
    print("Checking for UART devices...")
    for port in common_ports:
        if os.path.exists(port):
            uart_devices.append(port)
            print(f"  ✓ Found: {port}")
    
    return uart_devices

def test_gps_connection(port: str, baudrate: int = 9600, timeout: float = 2.0):
    """Test GPS connection and read NMEA data."""
    try:
        import serial
    except ImportError:
        print("  ✗ pyserial not installed. Install with: pip install pyserial")
        return False
    
    try:
        print(f"\nTesting GPS on {port} at {baudrate} baud...")
        ser = serial.Serial(port, baudrate, timeout=timeout)
        
        # Try to read NMEA sentences
        print("  Reading GPS data (waiting for NMEA sentences)...")
        start_time = time.time()
        nmea_count = 0
        
        while time.time() - start_time < 5.0:  # 5 second timeout
            try:
                line = ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$'):
                    nmea_count += 1
                    print(f"  ✓ Received: {line[:50]}...")
                    if nmea_count >= 3:  # Got enough data
                        ser.close()
                        print(f"\n✓ GPS is working! Received {nmea_count} NMEA sentences")
                        return True
            except Exception as e:
                print(f"  ⚠ Error reading: {e}")
                break
        
        ser.close()
        
        if nmea_count > 0:
            print(f"\n✓ GPS detected! Received {nmea_count} NMEA sentence(s)")
            return True
        else:
            print("\n⚠ GPS port exists but no NMEA data received")
            print("  - Check antenna connection")
            print("  - Wait for GPS to acquire satellites (may take 30-60 seconds)")
            return False
            
    except serial.SerialException as e:
        print(f"  ✗ Serial error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_i2c_gps():
    """Check for I2C-based GPS (less common)."""
    try:
        import subprocess
        result = subprocess.run(
            ['i2cdetect', '-y', '1'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("\nI2C devices detected:")
            print(result.stdout)
            return True
    except Exception:
        pass
    return False

def main():
    print("=" * 60)
    print("Waveshare GPS HAT Detection")
    print("=" * 60)
    print()
    
    # Check UART devices
    uart_devices = check_uart_devices()
    
    if not uart_devices:
        print("\n✗ No UART devices found")
        print("\nTroubleshooting:")
        print("  1. Check if GPS HAT is properly connected to Pi")
        print("  2. Enable UART in raspi-config:")
        print("     sudo raspi-config -> Interfacing Options -> Serial")
        print("  3. Reboot after enabling UART")
        return 1
    
    # Test each UART device
    gps_found = False
    for port in uart_devices:
        if test_gps_connection(port):
            gps_found = True
            print(f"\n✓ Recommended GPS port: {port}")
            break
    
    # Check I2C (less common for GPS)
    print("\nChecking I2C bus...")
    check_i2c_gps()
    
    print("\n" + "=" * 60)
    if gps_found:
        print("✓ GPS HAT DETECTED AND WORKING")
        print("=" * 60)
        return 0
    else:
        print("⚠ GPS HAT DETECTED BUT NOT RECEIVING DATA")
        print("=" * 60)
        print("\nPossible issues:")
        print("  - GPS needs time to acquire satellites (30-60 seconds)")
        print("  - Antenna not connected or not in clear view of sky")
        print("  - Wrong baud rate (try 115200 for some modules)")
        print("  - UART not properly enabled")
        return 1

if __name__ == "__main__":
    sys.exit(main())

