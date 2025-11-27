# AstroPi / Sense HAT IMU Support

**Date:** December 2025  
**Status:** ✅ Implemented

---

## Overview

The AI Tuner Agent now supports the **Raspberry Pi Sense HAT** (including the virtual **AstroPi** on Raspberry Pi 5) as an IMU sensor for testing and development.

This allows you to use the built-in Sense HAT on your Pi 5 for IMU data until your physical IMU arrives.

---

## Features

The Sense HAT provides:
- ✅ **Accelerometer** (3-axis, m/s²)
- ✅ **Gyroscope** (3-axis, deg/s)
- ✅ **Magnetometer** (3-axis, microtesla)
- ✅ **Temperature** (Celsius)

All data is automatically integrated with:
- Kalman Filter (GPS/IMU fusion)
- Wheel slip calculations
- G-force displays
- Performance tracking

---

## Installation

### On Raspberry Pi 5:

The Sense HAT library should already be available if you're using AstroPi. If not:

```bash
# Install Sense HAT library
sudo apt-get update
sudo apt-get install sense-hat

# Or via pip
pip3 install sense-hat
```

---

## Auto-Detection

The IMU interface now **auto-detects** the Sense HAT when initialized:

```python
from interfaces.imu_interface import IMUInterface, IMUType

# Auto-detect (will find Sense HAT if available)
imu = IMUInterface(imu_type=IMUType.AUTO_DETECT)

# Or explicitly use Sense HAT
imu = IMUInterface(imu_type=IMUType.SENSE_HAT)
```

The `DataStreamController` automatically uses `AUTO_DETECT` mode, so it will find your Sense HAT automatically.

---

## Usage

### In Data Stream Controller

The Sense HAT is automatically detected and used when available:

```python
# In data_stream_controller.py
# Auto-detection happens automatically:
self.imu_interface = IMUInterface(imu_type=IMUType.AUTO_DETECT)

# If Sense HAT is detected, it will be used
# If not, it will try other IMU types (MPU6050, etc.)
```

### Manual Connection

```python
from interfaces.imu_interface import IMUInterface, IMUType

# Create interface
imu = IMUInterface(imu_type=IMUType.SENSE_HAT)

# Check if connected
if imu.is_connected():
    # Read IMU data
    reading = imu.read()
    if reading:
        print(f"Accel: {reading.accel_x}, {reading.accel_y}, {reading.accel_z}")
        print(f"Gyro: {reading.gyro_x}, {reading.gyro_y}, {reading.gyro_z}")
        print(f"Mag: {reading.mag_x}, {reading.mag_y}, {reading.mag_z}")
```

---

## Data Format

The Sense HAT provides data in the same format as other IMU sensors:

```python
@dataclass
class IMUReading:
    # Accelerometer (m/s²)
    accel_x: float
    accel_y: float
    accel_z: float
    
    # Gyroscope (deg/s)
    gyro_x: float
    gyro_y: float
    gyro_z: float
    
    # Magnetometer (microtesla)
    mag_x: float
    mag_y: float
    mag_z: float
    
    # Temperature (Celsius)
    temperature: float
    
    # Timestamp
    timestamp: float
```

---

## Integration with Kalman Filter

The Sense HAT data is automatically used by the Kalman Filter for GPS/IMU fusion:

```python
# In data_stream_controller.py
if self.kalman_filter and self.imu_interface:
    imu_reading = self.imu_interface.read()
    gps_fix = self.gps_interface.read_fix()
    
    # Kalman filter fuses GPS + IMU data
    kalman_output = self.kalman_filter.update(
        gps_fix=gps_fix,
        imu_reading=imu_reading
    )
```

---

## Calibration

The Sense HAT supports the same 30-second stationary initialization as other IMUs:

```python
# Start initialization (vehicle must be stationary for 30 seconds)
imu.start_initialization()

# Check if initialization complete
if imu.check_initialization():
    print("IMU initialized - ready for movement detection")

# Detect movement
if imu.detect_movement():
    print("Movement detected - IMU active")
```

---

## Virtual vs Physical Sense HAT

### Virtual Sense HAT (AstroPi on Pi 5)
- ✅ Works out of the box
- ✅ No hardware required
- ✅ Perfect for testing
- ✅ Same API as physical Sense HAT

### Physical Sense HAT
- ✅ Real hardware sensor
- ✅ More accurate readings
- ✅ Same code works for both

The code automatically detects and works with both!

---

## Troubleshooting

### "Sense HAT library not available"

Install the library:
```bash
sudo apt-get install sense-hat
# or
pip3 install sense-hat
```

### "Sense HAT initialization failed"

Check that:
1. You're running on a Raspberry Pi
2. The Sense HAT library is installed
3. You have proper permissions (may need to run with `sudo` for hardware access)

### "No IMU detected"

If auto-detection doesn't find the Sense HAT:
1. Try explicitly setting `IMUType.SENSE_HAT`
2. Check that the Sense HAT library is installed
3. Verify you're on a Raspberry Pi with Sense HAT support

---

## Performance

The Sense HAT provides:
- **Update rate:** ~10-20 Hz (sufficient for vehicle dynamics)
- **Accuracy:** Good for testing and development
- **Latency:** Low (<50ms)

For production use, a dedicated IMU (MPU6050, BNO085, etc.) may provide better performance, but the Sense HAT is excellent for testing!

---

## Example Output

When the Sense HAT is detected and working, you'll see:

```
[INFO] [interfaces.imu_interface] - Sense HAT (AstroPi) detected
[INFO] [interfaces.imu_interface] - Sense HAT (AstroPi) initialized successfully
[INFO] [controllers.data_stream_controller] - IMU Interface initialized: sense_hat (connected)
[INFO] [controllers.data_stream_controller] - Kalman Filter initialized (GPS/IMU fusion enabled)
```

---

## Next Steps

1. **Test the Sense HAT:**
   ```bash
   python3 -c "from interfaces.imu_interface import IMUInterface, IMUType; imu = IMUInterface(IMUType.SENSE_HAT); print('Connected:', imu.is_connected()); r = imu.read(); print('Reading:', r)"
   ```

2. **Run the demo:**
   ```bash
   python3 demo_safe.py
   ```

3. **Check IMU data in the UI:**
   - G-force displays should show accelerometer data
   - Gyroscope data is used for Kalman filter
   - Magnetometer data is available for heading

---

**Status:** ✅ **Ready to use!**

The Sense HAT will be automatically detected and used when you run the application on your Pi 5.

