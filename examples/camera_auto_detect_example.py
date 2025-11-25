"""
Example: Automatic Camera Detection and Usage

This example demonstrates how the camera system automatically detects
and configures all available cameras (USB, CSI, RTSP, HTTP).
"""

from __future__ import annotations

import logging
import time

from interfaces.camera_interface import CameraManager, CameraAutoDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Demonstrate automatic camera detection."""
    print("=" * 60)
    print("AI Tuner Agent - Automatic Camera Detection Example")
    print("=" * 60)

    # Option 1: Auto-detect and add all cameras automatically
    print("\n[Option 1] Creating CameraManager with auto-detection...")
    manager = CameraManager(auto_detect=True)

    print(f"\nFound {len(manager.cameras)} cameras:")
    for name, camera in manager.cameras.items():
        print(f"  - {name}: {camera.config.camera_type.value} @ {camera.config.source}")
        print(f"    Resolution: {camera.config.width}x{camera.config.height} @ {camera.config.fps}fps")
        print(f"    Position: {camera.config.position}")

    # Option 2: Manual detection and configuration
    print("\n[Option 2] Manual detection...")
    detected = CameraAutoDetector.detect_all_cameras()
    print(f"Detected {len(detected)} cameras:")
    for cam in detected:
        print(f"  - {cam.name} ({cam.camera_type.value})")

    # Option 3: Get frames from all cameras
    print("\n[Option 3] Capturing frames for 5 seconds...")
    start_time = time.time()
    frame_count = {name: 0 for name in manager.cameras.keys()}

    while time.time() - start_time < 5.0:
        frames = manager.get_all_frames()
        for name, frame in frames.items():
            if frame:
                frame_count[name] += 1
        time.sleep(0.1)

    print("\nFrame capture statistics:")
    for name, count in frame_count.items():
        fps = count / 5.0
        print(f"  - {name}: {count} frames ({fps:.1f} fps)")

    # Health check
    print("\n[Health Check]")
    health = manager.health_check()
    for name, healthy in health.items():
        status = "✓ Healthy" if healthy else "✗ Unhealthy"
        print(f"  - {name}: {status}")

    # Cleanup
    print("\n[Cleanup] Stopping all cameras...")
    manager.stop_all()
    print("Done!")


if __name__ == "__main__":
    main()

