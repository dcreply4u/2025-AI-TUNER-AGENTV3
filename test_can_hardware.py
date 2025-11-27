#!/usr/bin/env python3
"""
Test CAN Hardware Detection

Tests the CAN hardware detector to verify Waveshare CAN HAT detection
and CAN interface functionality.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

LOGGER = logging.getLogger(__name__)


def test_can_hardware_detection():
    """Test CAN hardware detection."""
    print("\n" + "="*60)
    print("TEST 1: CAN Hardware Detection")
    print("="*60)
    
    try:
        from interfaces.can_hardware_detector import (
            CANHardwareDetector,
            detect_can_hardware,
            is_waveshare_can,
            get_can_hardware_detector,
        )
        
        print("\n✓ CAN hardware detector module imported successfully")
        
        # Test detection
        print("\nDetecting CAN hardware...")
        interfaces = detect_can_hardware()
        
        if not interfaces:
            print("⚠️  No CAN interfaces detected")
            print("\nPossible reasons:")
            print("  - CAN HAT not installed")
            print("  - CAN interface not configured (run: sudo ip link set can0 up type can bitrate 500000)")
            print("  - CAN interface not in /sys/class/net")
            return False
        
        print(f"\n✓ Detected {len(interfaces)} CAN interface(s):")
        for name, info in interfaces.items():
            print(f"\n  Interface: {name}")
            print(f"    Hardware Type: {info.hardware_type}")
            print(f"    State: {info.state}")
            print(f"    Bitrate: {info.bitrate} bps" if info.bitrate else "    Bitrate: Not set")
        
        # Test Waveshare detection
        print("\n" + "-"*60)
        print("Testing Waveshare Detection:")
        print("-"*60)
        
        for interface_name in interfaces.keys():
            is_waveshare = is_waveshare_can(interface_name)
            status = "✓ YES" if is_waveshare else "✗ NO"
            print(f"  {interface_name}: {status} (Waveshare CAN HAT)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import CAN hardware detector: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during detection: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_can_interface_connection():
    """Test CAN interface connection."""
    print("\n" + "="*60)
    print("TEST 2: CAN Interface Connection")
    print("="*60)
    
    try:
        from interfaces.can_interface import OptimizedCANInterface
        
        print("\n✓ CAN interface module imported successfully")
        
        # Try to connect to can0
        print("\nAttempting to connect to can0...")
        can_interface = OptimizedCANInterface(
            channel="can0",
            bitrate=500000,
        )
        
        if can_interface.connect():
            print("✓ Successfully connected to can0")
            
            # Get statistics
            stats = can_interface.get_statistics()
            print(f"\nCAN Statistics:")
            print(f"  Total Messages: {stats.total_messages}")
            print(f"  Messages/sec: {stats.messages_per_second:.2f}")
            print(f"  Error Frames: {stats.error_frames}")
            print(f"  Unique IDs: {len(stats.unique_ids)}")
            
            # Disconnect
            can_interface.disconnect()
            print("\n✓ Disconnected from can0")
            return True
        else:
            print("✗ Failed to connect to can0")
            print("\nPossible reasons:")
            print("  - CAN interface not up (run: sudo ip link set can0 up type can bitrate 500000)")
            print("  - CAN HAT not properly installed")
            print("  - Hardware issue")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import CAN interface: {e}")
        print("  Install with: pip install python-can")
        return False
    except Exception as e:
        print(f"✗ Error during connection test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_can_interfaces():
    """Test system-level CAN interface detection."""
    print("\n" + "="*60)
    print("TEST 3: System CAN Interface Check")
    print("="*60)
    
    import subprocess
    import os
    
    # Check /sys/class/net for CAN interfaces
    print("\nChecking /sys/class/net for CAN interfaces...")
    sys_net_path = "/sys/class/net"
    
    if not os.path.exists(sys_net_path):
        print(f"✗ {sys_net_path} does not exist (not running on Linux?)")
        return False
    
    can_interfaces = []
    for item in os.listdir(sys_net_path):
        if item.startswith('can'):
            can_interfaces.append(item)
    
    if can_interfaces:
        print(f"✓ Found {len(can_interfaces)} CAN interface(s) in /sys/class/net:")
        for iface in can_interfaces:
            print(f"  - {iface}")
            
            # Check state
            operstate_path = os.path.join(sys_net_path, iface, "operstate")
            if os.path.exists(operstate_path):
                try:
                    with open(operstate_path, 'r') as f:
                        state = f.read().strip()
                    print(f"    State: {state}")
                except Exception:
                    pass
            
            # Check bitrate
            bitrate_path = os.path.join(sys_net_path, iface, "bitrate")
            if os.path.exists(bitrate_path):
                try:
                    with open(bitrate_path, 'r') as f:
                        bitrate = f.read().strip()
                    print(f"    Bitrate: {bitrate} bps")
                except Exception:
                    pass
    else:
        print("✗ No CAN interfaces found in /sys/class/net")
        return False
    
    # Check ip link command
    print("\nChecking 'ip link' for CAN interfaces...")
    try:
        result = subprocess.run(
            ["ip", "link", "show", "type", "can"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print("✓ CAN interfaces found via 'ip link':")
            print(result.stdout)
        else:
            print("⚠️  No CAN interfaces found via 'ip link'")
    except FileNotFoundError:
        print("⚠️  'ip' command not found")
    except Exception as e:
        print(f"⚠️  Error running 'ip link': {e}")
    
    return len(can_interfaces) > 0


def test_dmesg_detection():
    """Test dmesg for CAN hardware info."""
    print("\n" + "="*60)
    print("TEST 4: Kernel Messages (dmesg) Check")
    print("="*60)
    
    import subprocess
    
    try:
        result = subprocess.run(
            ["dmesg"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        
        if result.returncode == 0:
            dmesg_output = result.stdout.lower()
            
            # Check for MCP2515 (Waveshare)
            if 'mcp2515' in dmesg_output:
                print("✓ Found MCP2515 in kernel messages (likely Waveshare CAN HAT)")
                # Extract relevant lines
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'mcp2515' in line.lower():
                        print(f"  {line.strip()}")
            
            # Check for CAN
            if 'can' in dmesg_output:
                can_lines = [l for l in result.stdout.split('\n') if 'can' in l.lower() and len(l.strip()) > 0]
                if can_lines:
                    print(f"\n✓ Found {len(can_lines)} CAN-related kernel messages")
                    for line in can_lines[:5]:  # Show first 5
                        print(f"  {line.strip()}")
            
            # Check for Waveshare
            if 'waveshare' in dmesg_output:
                print("\n✓ Found 'Waveshare' in kernel messages")
                waveshare_lines = [l for l in result.stdout.split('\n') if 'waveshare' in l.lower()]
                for line in waveshare_lines[:3]:
                    print(f"  {line.strip()}")
        else:
            print("⚠️  Could not read dmesg")
            
    except FileNotFoundError:
        print("⚠️  'dmesg' command not found")
    except Exception as e:
        print(f"⚠️  Error reading dmesg: {e}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CAN Hardware Detection Test Suite")
    print("="*60)
    print("\nThis script tests:")
    print("  1. CAN hardware detection module")
    print("  2. CAN interface connection")
    print("  3. System CAN interface detection")
    print("  4. Kernel messages (dmesg) analysis")
    
    results = []
    
    # Run tests
    results.append(("CAN Hardware Detection", test_can_hardware_detection()))
    results.append(("System CAN Interfaces", test_system_can_interfaces()))
    test_dmesg_detection()  # Informational only
    results.append(("CAN Interface Connection", test_can_interface_connection()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! CAN hardware is properly detected and working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nTroubleshooting:")
        print("  1. Ensure CAN HAT is properly installed")
        print("  2. Configure CAN interface: sudo ip link set can0 up type can bitrate 500000")
        print("  3. Check hardware connections")
        print("  4. Verify SPI is enabled: sudo raspi-config -> Interface Options -> SPI")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

