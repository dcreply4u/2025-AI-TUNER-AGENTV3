# Camera Integration Guide

This guide explains how to integrate USB and WiFi cameras with the AI Tuner Agent for racing telemetry and video logging.

## Overview

The camera system supports:
- **USB Cameras** (UVC-compatible)
- **WiFi Cameras** (RTSP/HTTP streams)
- **CSI Cameras** (Raspberry Pi camera modules)
- **Multiple simultaneous cameras** (front/rear)
- **Telemetry synchronization** (video frames tagged with telemetry data)
- **Automatic video logging** with metadata

## Quick Start

### 1. Basic Camera Setup

```python
from interfaces.camera_interface import CameraManager, CameraConfig, CameraType

# Create camera manager
manager = CameraManager()

# Add front USB camera
front_config = CameraConfig(
    name="front",
    camera_type=CameraType.USB,
    source="0",  # USB device index or /dev/video0
    width=1920,
    height=1080,
    fps=30,
    position="front",
)

manager.add_camera(front_config)

# Add rear WiFi camera (RTSP)
rear_config = CameraConfig(
    name="rear",
    camera_type=CameraType.RTSP,
    source="rtsp://192.168.1.100:554/stream",
    width=1920,
    height=1080,
    fps=30,
    position="rear",
)

manager.add_camera(rear_config)
```

### 2. Video Logging

```python
from services.video_logger import VideoLogger

# Create video logger
logger = VideoLogger(log_dir="video_logs")

# Start recording session
session_id = logger.start_session(
    cameras=["front", "rear"],
    resolution=(1920, 1080),
    fps=30,
)

# In your capture loop
while running:
    frames = manager.get_all_frames()
    for camera_name, frame in frames.items():
        if frame:
            logger.log_frame(frame, session_id)

# Stop recording
logger.stop_session(session_id)
```

### 3. Telemetry Synchronization

```python
# Set telemetry sync function
def get_current_telemetry():
    return {
        "rpm": current_rpm,
        "speed": current_speed,
        "throttle": current_throttle,
        # ... other telemetry
    }

manager.set_telemetry_sync(get_current_telemetry)

# Frames will now include telemetry_sync data
```

## Integration with Data Stream Controller

To integrate cameras into the main data stream:

```python
from controllers.data_stream_controller import DataStreamController
from interfaces.camera_interface import CameraManager, CameraConfig, CameraType
from services.video_logger import VideoLogger

# In your main window initialization
camera_manager = CameraManager()
video_logger = VideoLogger()

# Add cameras
front_camera = CameraConfig(
    name="front",
    camera_type=CameraType.USB,
    source="0",
    position="front",
)
camera_manager.add_camera(front_camera)

# Start video session when data stream starts
def on_stream_start():
    session_id = video_logger.start_session(cameras=["front", "rear"])
    # Store session_id for later use

# In data stream poll loop
def on_poll():
    # Get frames and log them
    frames = camera_manager.get_all_frames()
    for name, frame in frames.items():
        if frame:
            video_logger.log_frame(frame, session_id)
```

## Camera Types

### USB Camera
```python
CameraConfig(
    name="usb_cam",
    camera_type=CameraType.USB,
    source="0",  # or "/dev/video0"
    width=1920,
    height=1080,
    fps=30,
)
```

### RTSP Stream (WiFi Camera)
```python
CameraConfig(
    name="wifi_cam",
    camera_type=CameraType.RTSP,
    source="rtsp://username:password@192.168.1.100:554/stream",
    width=1920,
    height=1080,
    fps=30,
)
```

### HTTP/MJPEG Stream
```python
CameraConfig(
    name="http_cam",
    camera_type=CameraType.HTTP,
    source="http://192.168.1.100:8080/video",
    width=1280,
    height=720,
    fps=15,
)
```

### CSI Camera (Raspberry Pi)
```python
CameraConfig(
    name="csi_cam",
    camera_type=CameraType.CSI,
    source="0",  # Sensor ID
    width=1920,
    height=1080,
    fps=30,
)
```

## Finding Camera Devices

### List USB Cameras
```bash
ls /dev/video*
v4l2-ctl --list-devices
```

### Test Camera
```bash
# Test USB camera
ffplay /dev/video0

# Test RTSP stream
ffplay rtsp://192.168.1.100:554/stream
```

## Performance Considerations

1. **Resolution**: Lower resolution (1280x720) uses less CPU and disk space
2. **FPS**: 30 FPS is standard, 60 FPS for high-speed racing
3. **Multiple Cameras**: Each camera uses CPU and memory. Limit to 2-3 simultaneous cameras on Raspberry Pi
4. **Disk Space**: Video files are large. Monitor disk usage with `video_logger.get_disk_usage()`

## Troubleshooting

### Camera Not Opening
- Check device permissions: `sudo chmod 666 /dev/video0`
- Verify camera is detected: `v4l2-ctl --list-devices`
- Try different device index: `source="1"` instead of `"0"`

### RTSP Stream Not Working
- Verify network connectivity
- Check RTSP URL format
- Test with VLC or ffplay first

### High CPU Usage
- Reduce resolution or FPS
- Use hardware-accelerated encoding if available
- Limit number of simultaneous cameras

### Out of Disk Space
- Use `video_logger.cleanup_old_sessions(max_age_days=7)` to remove old recordings
- Monitor with `video_logger.get_disk_usage()`
- Consider external storage for video logs

## Example: Complete Integration

```python
from interfaces.camera_interface import CameraManager, CameraConfig, CameraType
from services.video_logger import VideoLogger

class RacingSession:
    def __init__(self):
        self.camera_manager = CameraManager()
        self.video_logger = VideoLogger()
        self.session_id = None

    def start(self):
        # Setup cameras
        front = CameraConfig(
            name="front",
            camera_type=CameraType.USB,
            source="0",
            position="front",
        )
        rear = CameraConfig(
            name="rear",
            camera_type=CameraType.RTSP,
            source="rtsp://192.168.1.100:554/stream",
            position="rear",
        )

        self.camera_manager.add_camera(front)
        self.camera_manager.add_camera(rear)

        # Start video session
        self.session_id = self.video_logger.start_session(
            cameras=["front", "rear"],
        )

        # Set telemetry sync
        self.camera_manager.set_telemetry_sync(self.get_telemetry)

    def get_telemetry(self):
        # Return current telemetry data
        return {
            "rpm": self.current_rpm,
            "speed": self.current_speed,
            # ...
        }

    def update(self):
        # Get frames and log them
        frames = self.camera_manager.get_all_frames()
        for name, frame in frames.items():
            if frame:
                self.video_logger.log_frame(frame, self.session_id)

    def stop(self):
        # Stop cameras
        self.camera_manager.stop_all()
        # Stop video session
        if self.session_id:
            self.video_logger.stop_session(self.session_id)
```

## Next Steps

- Integrate camera manager into `DataStreamController`
- Add camera preview widgets to UI
- Implement automatic camera detection
- Add camera settings to settings dialog

