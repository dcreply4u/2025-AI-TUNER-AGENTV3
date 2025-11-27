# USB Camera Integration Guide

**Date:** December 2025  
**Status:** ✅ Auto-Detection Enabled

---

## Overview

The AI Tuner Agent now **automatically detects and integrates USB cameras** on Raspberry Pi 5. When you connect a USB camera, it will be automatically detected and used for video logging, telemetry overlay, and live streaming.

---

## Auto-Detection

USB cameras are automatically detected when:
1. **Application starts** - All USB cameras are scanned and added
2. **Camera connected after startup** - Periodic checks detect newly connected cameras
3. **Manual trigger** - You can manually trigger detection via the API or UI

---

## How It Works

### Detection Process

1. **Scan `/dev/video*` devices** - Finds all video devices on Linux
2. **Probe each device** - Tests if device is accessible and can capture frames
3. **Get capabilities** - Reads resolution, FPS, and other capabilities
4. **Auto-configure** - Sets optimal settings based on camera capabilities
5. **Add to manager** - Camera is ready to use immediately

### Integration Points

Once detected, USB cameras are automatically used for:
- ✅ **Video Logging** - Records video with telemetry overlay
- ✅ **Live Streaming** - Streams to YouTube/RTMP if configured
- ✅ **Telemetry Sync** - Each frame is synchronized with telemetry data
- ✅ **Multi-Camera Support** - Multiple USB cameras can be used simultaneously

---

## Testing Your USB Camera

### Quick Test Script

Run this on your Pi 5 to verify USB camera detection:

```bash
cd ~/AITUNER/2025-AI-TUNER-AGENTV3
python3 scripts/test_usb_camera.py
```

This will:
1. Check for `/dev/video*` devices
2. Run auto-detection
3. Test camera initialization
4. Capture a test frame
5. Show camera status

### Manual System Check

```bash
# List video devices
ls /dev/video*

# Get detailed camera info
v4l2-ctl --list-devices

# Test camera with ffplay
ffplay /dev/video0

# Check USB devices
lsusb
```

---

## Expected Output

When a USB camera is detected, you'll see:

```
[INFO] Starting camera auto-detection (include_network=False)
[INFO] Detecting USB cameras...
[INFO] Found 1 USB camera(s)
[INFO] Auto-detected and added: USB Camera 0 (usb, front, source: 0)
[INFO] Camera started successfully: USB Camera 0 (0) - 1920x1080 @ 30fps
[INFO] Auto-detection complete: 1 cameras found, 1 added, 0 failed
```

---

## Troubleshooting

### Camera Not Detected

**Check 1: Device exists**
```bash
ls /dev/video*
# Should show: /dev/video0 (or video1, etc.)
```

**Check 2: Permissions**
```bash
# Check permissions
ls -l /dev/video0
# Should be: crw-rw---- or crw-rw-rw-

# Fix permissions if needed
sudo chmod 666 /dev/video0
# Or add user to video group:
sudo usermod -a -G video $USER
# Then logout and login again
```

**Check 3: Camera in use**
```bash
# Check if another process is using the camera
lsof /dev/video0
# If something is using it, close that application
```

**Check 4: USB connection**
```bash
# Verify USB camera is recognized
lsusb
# Should show your camera in the list
```

### Camera Detected But Won't Open

**Issue:** Camera appears in detection but fails to start

**Solutions:**
1. **Check OpenCV installation:**
   ```bash
   python3 -c "import cv2; print(cv2.__version__)"
   ```

2. **Test with OpenCV directly:**
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   if cap.isOpened():
       ret, frame = cap.read()
       print("Camera works!" if ret else "Camera opened but can't read")
       cap.release()
   else:
       print("Camera failed to open")
   ```

3. **Try different device index:**
   - Some systems use `/dev/video0` for the first camera
   - Others may use `/dev/video1` or higher
   - The detection script will try all available devices

### Multiple USB Cameras

If you have multiple USB cameras:
- Each will be detected automatically
- They'll be named: "USB Camera 0", "USB Camera 1", etc.
- All can be used simultaneously
- Each can have different settings (resolution, FPS)

---

## Manual Camera Addition

If auto-detection doesn't work, you can manually add a camera:

```python
from interfaces.camera_interface import CameraConfig, CameraType
from controllers.camera_manager import CameraManager

# Create camera config
config = CameraConfig(
    name="My USB Camera",
    camera_type=CameraType.USB,
    source="0",  # Device index or "/dev/video0"
    width=1920,
    height=1080,
    fps=30,
    enabled=True,
    position="front"
)

# Add to manager
camera_manager.add_camera(config)
```

---

## Camera Features

### Supported Features

- ✅ **Auto-detection** - Automatically finds USB cameras
- ✅ **Multiple cameras** - Supports multiple USB cameras simultaneously
- ✅ **Resolution detection** - Automatically detects max resolution
- ✅ **FPS detection** - Detects supported frame rates
- ✅ **Telemetry overlay** - Syncs video with telemetry data
- ✅ **Video logging** - Records video with timestamps
- ✅ **Live streaming** - Streams to YouTube/RTMP
- ✅ **Health monitoring** - Monitors camera health

### Camera Settings

Cameras are auto-configured with optimal settings:
- **Resolution:** Highest supported (typically 1920x1080)
- **FPS:** 30 FPS (or camera's max)
- **Format:** MJPEG or YUYV (auto-selected)
- **Buffer:** Minimal (1 frame) for low latency

---

## Integration with Application

### In Data Stream Controller

The USB camera is automatically integrated when detected:

```python
# In data_stream_controller.py
if self.camera_manager:
    # Camera manager auto-detects USB cameras
    # Telemetry sync is automatically set up
    # Cameras are ready to use immediately
```

### Video Logging

When recording starts, all detected USB cameras automatically start recording:

```python
# Start recording session
camera_manager.start_recording(session_id="session_001")

# All USB cameras automatically start recording
# Video files saved with telemetry overlay
```

### Telemetry Overlay

Each video frame is synchronized with telemetry data:
- GPS coordinates
- Speed, RPM, throttle
- G-forces
- Lap times
- And more...

---

## Performance

### Resource Usage

- **CPU:** ~5-10% per camera (depends on resolution)
- **Memory:** ~50-100MB per camera
- **Disk I/O:** ~10-20 MB/s per camera (1080p @ 30fps)

### Optimization Tips

1. **Lower resolution** for multiple cameras:
   ```python
   config.width = 1280
   config.height = 720
   ```

2. **Lower FPS** if CPU is constrained:
   ```python
   config.fps = 15
   ```

3. **Disable unused cameras:**
   ```python
   config.enabled = False
   ```

---

## API Access

### List Detected Cameras

```python
# Get all cameras
cameras = camera_manager.camera_manager.cameras
for name, camera in cameras.items():
    print(f"{name}: {camera.config.width}x{camera.config.height} @ {camera.config.fps}fps")
```

### Get Camera Status

```python
status = camera_manager.get_status()
print(status)
# {
#     "recording": True,
#     "session_id": "session_001",
#     "cameras": {"USB Camera 0": True},
#     "active_recordings": ["USB Camera 0"]
# }
```

### Health Check

```python
health = camera_manager.camera_manager.health_check()
print(health)
# {"USB Camera 0": True}  # True = healthy, False = not receiving frames
```

---

## Next Steps

1. **Test detection:**
   ```bash
   python3 scripts/test_usb_camera.py
   ```

2. **Run the demo:**
   ```bash
   python3 demo_safe.py
   ```

3. **Check camera in UI:**
   - Look for "USB Cameras" tab
   - Camera should appear in the list
   - Status should show "Connected"

4. **Start recording:**
   - Camera will automatically record when session starts
   - Video files saved with telemetry overlay

---

## Troubleshooting Commands

```bash
# Check video devices
ls -l /dev/video*

# Get camera info
v4l2-ctl --device /dev/video0 --all

# Test camera
ffplay /dev/video0

# Check USB devices
lsusb

# Check camera processes
ps aux | grep -i camera

# Check camera in use
lsof /dev/video0

# Fix permissions
sudo chmod 666 /dev/video0
```

---

**Status:** ✅ **USB Camera Auto-Detection Enabled**

Your USB camera will be automatically detected and integrated when you run the application!

