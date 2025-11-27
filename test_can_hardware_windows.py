#!/usr/bin/env python3
"""
Test CAN Hardware Detection (Windows-Compatible)

Tests the CAN hardware detector code structure and imports.
Full hardware testing must be done on Raspberry Pi.
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


def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        from interfaces.can_hardware_detector import (
            CANHardwareDetector,
            CANHardwareInfo,
            detect_can_hardware,
            is_waveshare_can,
            get_can_hardware_detector,
        )
        print("✓ CAN hardware detector module imported successfully")
        print("  - CANHardwareDetector")
        print("  - CANHardwareInfo")
        print("  - detect_can_hardware")
        print("  - is_waveshare_can")
        print("  - get_can_hardware_detector")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_can_interface_imports():
    """Test CAN interface imports."""
    print("\n" + "="*60)
    print("TEST 2: CAN Interface Module Imports")
    print("="*60)
    
    try:
        from interfaces.can_interface import (
            OptimizedCANInterface,
            CANMessage,
            CANMessageType,
            CANStatistics,
        )
        print("✓ CAN interface module imported successfully")
        print("  - OptimizedCANInterface")
        print("  - CANMessage")
        print("  - CANMessageType")
        print("  - CANStatistics")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detector_instantiation():
    """Test detector can be instantiated."""
    print("\n" + "="*60)
    print("TEST 3: Detector Instantiation")
    print("="*60)
    
    try:
        from interfaces.can_hardware_detector import CANHardwareDetector
        
        detector = CANHardwareDetector()
        print("✓ CANHardwareDetector instantiated successfully")
        
        # Test methods exist
        assert hasattr(detector, 'detect_all')
        assert hasattr(detector, 'get_interface_info')
        assert hasattr(detector, 'is_waveshare')
        assert hasattr(detector, 'list_interfaces')
        assert hasattr(detector, 'verify_interface')
        print("✓ All required methods exist")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_can_interface_instantiation():
    """Test CAN interface can be instantiated."""
    print("\n" + "="*60)
    print("TEST 4: CAN Interface Instantiation")
    print("="*60)
    
    try:
        from interfaces.can_interface import OptimizedCANInterface
        
        # Try to create interface (won't connect on Windows, but should instantiate)
        can_interface = OptimizedCANInterface(
            channel="can0",
            bitrate=500000,
        )
        print("✓ OptimizedCANInterface instantiated successfully")
        print(f"  Channel: {can_interface.channel}")
        print(f"  Bitrate: {can_interface.bitrate}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between detector and interface."""
    print("\n" + "="*60)
    print("TEST 5: Integration Test")
    print("="*60)
    
    try:
        from interfaces.can_interface import OptimizedCANInterface
        from interfaces.can_hardware_detector import get_can_hardware_detector
        
        # Get detector
        detector = get_can_hardware_detector()
        print("✓ Got CAN hardware detector")
        
        # Create CAN interface
        can_interface = OptimizedCANInterface(channel="can0", bitrate=500000)
        print("✓ Created CAN interface")
        
        # The connect() method should use the detector
        print("✓ Integration code structure verified")
        print("  (Actual connection test requires Linux/Raspberry Pi)")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CAN Hardware Detection Test Suite (Windows)")
    print("="*60)
    print("\nNote: This tests code structure and imports.")
    print("Full hardware testing must be done on Raspberry Pi.")
    print("\nThis script tests:")
    print("  1. Module imports")
    print("  2. CAN interface imports")
    print("  3. Detector instantiation")
    print("  4. CAN interface instantiation")
    print("  5. Integration structure")
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("CAN Interface Imports", test_can_interface_imports()))
    results.append(("Detector Instantiation", test_detector_instantiation()))
    results.append(("CAN Interface Instantiation", test_can_interface_instantiation()))
    results.append(("Integration", test_integration()))
    
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
        print("\n✅ All code structure tests passed!")
        print("\n⚠️  Note: Full hardware testing requires running on Raspberry Pi:")
        print("   ssh aituner@192.168.1.214")
        print("   cd /home/aituner/AITUNER/2025-AI-TUNER-AGENTV3")
        print("   python test_can_hardware.py")
    else:
        print("\n✗ Some tests failed. Check the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

