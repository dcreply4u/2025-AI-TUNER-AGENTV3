#!/usr/bin/env python3
"""
Test script for USB camera detection on Raspberry Pi 5.

Run this on your Pi to verify USB camera is detected:
    python3 scripts/test_usb_camera.py
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from interfaces.camera_interface import CameraAutoDetector, CameraManager, CameraType
    print("✅ Camera Interface imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Camera Interface: {e}")
    sys.exit(1)

def test_usb_camera_detection():
    """Test USB camera detection."""
    print("\n" + "="*60)
    print("Testing USB Camera Detection")
    print("="*60 + "\n")
    
    # Test 1: Check for /dev/video* devices
    print("1. Checking for video devices in /dev...")
    video_devices = sorted(Path("/dev").glob("video*"))
    if video_devices:
        print(f"   ✅ Found {len(video_devices)} video device(s):")
        for dev in video_devices:
            print(f"      - {dev}")
    else:
        print("   ⚠️  No /dev/video* devices found")
        print("   💡 Make sure USB camera is connected and recognized by the system")
    
    # Test 2: Auto-detect cameras
    print("\n2. Running camera auto-detection...")
    try:
        detected = CameraAutoDetector.detect_all_cameras(include_network=False)
        print(f"   ✅ Detection complete: {len(detected)} camera(s) found")
        
        if detected:
            for i, cam in enumerate(detected, 1):
                print(f"\n   Camera {i}:")
                print(f"      Name: {cam.name}")
                print(f"      Type: {cam.camera_type.value}")
                print(f"      Source: {cam.source}")
                print(f"      Resolution: {cam.width}x{cam.height}")
                print(f"      FPS: {cam.fps}")
                print(f"      Position: {cam.position}")
                if cam.capabilities:
                    print(f"      Capabilities: {cam.capabilities}")
        else:
            print("   ⚠️  No cameras detected")
            print("   💡 Try:")
            print("      - Check USB connection")
            print("      - Run: lsusb (to see USB devices)")
            print("      - Run: ls /dev/video* (to see video devices)")
            print("      - Check permissions: sudo chmod 666 /dev/video0")
    except Exception as e:
        print(f"   ❌ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Initialize CameraManager with auto-detection
    print("\n3. Testing CameraManager with auto-detection...")
    try:
        manager = CameraManager(auto_detect=True, include_network=False)
        print(f"   ✅ CameraManager initialized")
        print(f"   📹 Cameras in manager: {len(manager.cameras)}")
        
        if manager.cameras:
            for name, camera in manager.cameras.items():
                print(f"\n   Camera: {name}")
                print(f"      Running: {camera.running}")
                print(f"      Config: {camera.config.width}x{camera.config.height} @ {camera.config.fps}fps")
                
                # Try to get a frame
                print(f"      Testing frame capture...")
                frame = camera.get_frame(timeout=2.0)
                if frame:
                    print(f"      ✅ Frame captured! Frame #{frame.frame_number}, timestamp: {frame.timestamp:.3f}")
                    print(f"         Image shape: {frame.image.shape if hasattr(frame.image, 'shape') else 'N/A'}")
                else:
                    print(f"      ⚠️  No frame received (camera may still be initializing)")
        else:
            print("   ⚠️  No cameras were added to manager")
            print("   💡 This could mean:")
            print("      - Camera detected but failed to open")
            print("      - Camera permissions issue")
            print("      - Camera already in use by another application")
    except Exception as e:
        print(f"   ❌ CameraManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Manual camera addition
    if detected and not manager.cameras:
        print("\n4. Attempting manual camera addition...")
        try:
            from interfaces.camera_interface import CameraAutoDetector, CameraConfig
            for det_cam in detected:
                config = CameraAutoDetector.auto_configure_camera(det_cam)
                print(f"   Trying to add: {config.name}...")
                if manager.add_camera(config):
                    print(f"   ✅ Successfully added: {config.name}")
                else:
                    print(f"   ❌ Failed to add: {config.name}")
        except Exception as e:
            print(f"   ❌ Manual addition failed: {e}")
    
    print("\n" + "="*60)
    if manager.cameras:
        print("✅ USB Camera is working! It will be automatically used by the application.")
    else:
        print("⚠️  USB Camera detected but not accessible.")
        print("💡 Troubleshooting:")
        print("   1. Check permissions: sudo chmod 666 /dev/video0")
        print("   2. Check if camera is in use: lsof /dev/video0")
        print("   3. Try: v4l2-ctl --list-devices")
        print("   4. Test camera: ffplay /dev/video0")
    print("="*60 + "\n")
    
    return len(manager.cameras) > 0

if __name__ == "__main__":
    success = test_usb_camera_detection()
    sys.exit(0 if success else 1)

