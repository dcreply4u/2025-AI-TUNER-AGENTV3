# Sense HAT Emulator Setup

## Status: ✅ Configured and Ready

The AI Tuner Agent application is already configured to automatically detect and use the Sense HAT emulator when it's running.

## How It Works

1. **Auto-Detection**: The `DataStreamController` uses `IMUType.AUTO_DETECT` which will:
   - First check for Sense HAT (physical or emulator)
   - Then check for other IMU sensors on I2C
   - Fall back to simulation if nothing is found

2. **Sense HAT Emulator**: When `sense_emu_gui` is running, the `sense_hat` library automatically connects to it instead of physical hardware.

3. **No Configuration Needed**: The application will automatically use the emulator if it's running.

## Verification

To verify the Sense HAT emulator is working:

1. **Check emulator is running**:
   ```bash
   ps aux | grep sense_emu_gui
   ```

2. **Check application logs** for IMU initialization:
   ```bash
   grep -i "sense\|imu" logs/demo.log | tail -20
   ```

3. **The application should show**:
   - IMU data in the sensor panels
   - Accelerometer, gyroscope, and magnetometer readings
   - Temperature readings
   - Integration with the Kalman filter

## What the Emulator Provides

- **Accelerometer**: 3-axis acceleration (m/s²)
- **Gyroscope**: 3-axis rotation rate (deg/s)
- **Magnetometer**: 3-axis magnetic field (microtesla)
- **Temperature**: Ambient temperature (°C)

## Using the Emulator GUI

The Sense HAT emulator GUI allows you to:
- Simulate movement by dragging the virtual Sense HAT
- Adjust temperature
- Test different orientations
- Visualize sensor data in real-time

## Troubleshooting

If the IMU is not being detected:

1. **Ensure emulator is running**:
   ```bash
   sense_emu_gui &
   ```

2. **Check Python packages**:
   ```bash
   pip3 list | grep sense
   ```
   Should show: `sense-emu` and `sense-hat`

3. **Test manually**:
   ```python
   from sense_hat import SenseHat
   s = SenseHat()
   s.set_imu_config(True, True, True)
   accel = s.get_accelerometer_raw()
   print(accel)
   ```

4. **Restart the demo** if needed to pick up the emulator

## Integration

The Sense HAT emulator data is used by:
- **Kalman Filter**: GPS/IMU fusion for accurate position and velocity
- **Wheel Slip Calculation**: Uses IMU acceleration for slip detection
- **Advanced Algorithms**: Sensor correlation and anomaly detection
- **Data Logging**: All IMU data is logged for analysis

## Next Steps

The emulator is ready to use! The application will automatically detect it when:
- The emulator GUI is running
- The demo application is started
- The DataStreamController initializes

No additional configuration is needed.

