# Waveshare Environmental Sensor HAT Setup Guide

## Overview

The Waveshare Environmental Sensor HAT provides real-time environmental data including:
- **Temperature** (BME280)
- **Humidity** (BME280)
- **Barometric Pressure** (BME280)
- **Light Level** (optional)
- **Noise Level** (optional)
- **3-axis Accelerometer/Gyroscope** (LSM6DS3, optional)

This data is automatically used for:
- Virtual dyno corrections (SAE J1349, DIN 70020)
- Density altitude calculations
- Weather-adaptive tuning
- Environmental telemetry logging

---

## Hardware Setup

### 1. Physical Installation

1. **Mount the HAT** on your Raspberry Pi GPIO header
2. **Enable I2C** on your Raspberry Pi:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → I2C → Enable
   ```
3. **Reboot** the Raspberry Pi:
   ```bash
   sudo reboot
   ```

### 2. Verify I2C Connection

Check if the BME280 is detected:
```bash
sudo i2cdetect -y 1
```

You should see device `0x76` or `0x77` (BME280 address).

---

## Software Installation

### Option 1: Adafruit Library (Recommended)

```bash
pip install adafruit-circuitpython-bme280
```

This library provides the best support and is automatically detected by the application.

### Option 2: smbus2 (Alternative)

```bash
pip install smbus2
```

This is a fallback option if Adafruit library is not available.

---

## Configuration

### Environment Variables

The application automatically detects the HAT. You can force simulator mode:

```bash
export AITUNER_USE_ENV_SIMULATOR=true
```

### I2C Bus Configuration

By default, the interface uses I2C bus 1. If your HAT is on a different bus:

```python
from interfaces.waveshare_environmental_hat import get_environmental_hat

hat = get_environmental_hat(i2c_bus=0)  # Use bus 0 instead
```

### BME280 Address

The default address is `0x76`. If your HAT uses `0x77`:

```python
hat = get_environmental_hat(bme280_address=0x77)
```

---

## Integration

### Automatic Integration

The HAT is **automatically integrated** into the application:

1. **Data Stream Controller** reads environmental data every poll cycle
2. **Virtual Dyno** uses environmental data for SAE/DIN corrections
3. **Density Altitude Calculator** uses real-time temperature, pressure, humidity
4. **Telemetry Logging** includes all environmental parameters

### Manual Access

You can also access the HAT directly:

```python
from interfaces.waveshare_environmental_hat import get_environmental_hat

# Get HAT instance
hat = get_environmental_hat()

# Connect
if hat.connect():
    # Read environmental data
    reading = hat.read()
    if reading:
        print(f"Temperature: {reading.temperature_c}°C")
        print(f"Humidity: {reading.humidity_percent}%")
        print(f"Pressure: {reading.pressure_kpa} kPa")
```

---

## Simulator Mode

The simulator is **always available** as a fallback:

1. **Automatic Fallback**: If hardware connection fails, simulator is used automatically
2. **Manual Simulator**: Set `AITUNER_USE_ENV_SIMULATOR=true`
3. **Simulator Values**: Can be set programmatically:

```python
hat = get_environmental_hat(use_simulator=True)
hat.set_simulator_values(
    temperature_c=25.0,
    humidity_percent=60.0,
    pressure_kpa=101.325
)
```

---

## Data Flow

```
Waveshare HAT
    ↓
Data Stream Controller (reads every poll cycle)
    ↓
Normalized Telemetry Data
    ↓
├─→ Virtual Dyno (environmental corrections)
├─→ Density Altitude Calculator
├─→ Telemetry Panel (display)
├─→ Gauge Panel (display)
└─→ Data Logger (logging)
```

---

## Troubleshooting

### HAT Not Detected

1. **Check I2C is enabled:**
   ```bash
   lsmod | grep i2c
   ```

2. **Check device is present:**
   ```bash
   sudo i2cdetect -y 1
   ```

3. **Check permissions:**
   ```bash
   sudo usermod -a -G i2c $USER
   # Log out and back in
   ```

### Connection Errors

- **"Permission denied"**: Add user to `i2c` group (see above)
- **"Device not found"**: Check I2C address (try 0x77 if 0x76 doesn't work)
- **"Bus not available"**: Check I2C bus number (usually 1, sometimes 0)

### Simulator Always Used

- Check logs for connection errors
- Verify I2C is enabled and device is detected
- Check library installation (`pip list | grep bme280`)

---

## Telemetry Channels

The following telemetry channels are automatically added:

| Channel | Description | Unit |
|---------|-------------|------|
| `ambient_temp_c` | Ambient temperature | Celsius |
| `ambient_temp_f` | Ambient temperature | Fahrenheit |
| `humidity_percent` | Relative humidity | Percent (0-100) |
| `barometric_pressure_kpa` | Barometric pressure | kPa |
| `barometric_pressure_hpa` | Barometric pressure | hPa |
| `barometric_pressure_psi` | Barometric pressure | PSI |
| `light_lux` | Light level | Lux (if available) |
| `noise_db` | Noise level | dB (if available) |

---

## Virtual Dyno Integration

The environmental data is **automatically used** for dyno corrections:

1. **SAE J1349 Correction**: Uses temperature, pressure, humidity
2. **DIN 70020 Correction**: Uses temperature, pressure, humidity
3. **Real-time Updates**: Environmental conditions update continuously
4. **Accuracy**: More accurate HP/torque calculations with real environmental data

---

## Density Altitude Integration

The HAT provides **priority data** for density altitude:

1. **HAT Data** (first priority): Real-time, local measurements
2. **Weather API** (fallback): If HAT unavailable, uses GPS + weather API

This ensures the most accurate density altitude calculations possible.

---

## Testing

### Test Hardware Connection

```python
from interfaces.waveshare_environmental_hat import get_environmental_hat

hat = get_environmental_hat()
if hat.connect():
    reading = hat.read()
    if reading:
        print("✅ HAT connected and reading data")
        print(f"   Temperature: {reading.temperature_c:.1f}°C")
        print(f"   Humidity: {reading.humidity_percent:.1f}%")
        print(f"   Pressure: {reading.pressure_kpa:.2f} kPa")
    else:
        print("❌ HAT connected but failed to read")
else:
    print("❌ HAT connection failed")
```

### Test Simulator

```python
from interfaces.waveshare_environmental_hat import get_environmental_hat

hat = get_environmental_hat(use_simulator=True)
hat.set_simulator_values(temperature_c=30.0, humidity_percent=70.0, pressure_kpa=100.0)
reading = hat.read()
print(f"Simulator: {reading.temperature_c}°C, {reading.humidity_percent}%, {reading.pressure_kpa}kPa")
```

---

## Status

✅ **Fully Integrated** - The Waveshare Environmental Sensor HAT is fully integrated into the application with:
- Automatic hardware detection
- Simulator fallback
- Virtual dyno integration
- Density altitude integration
- Telemetry logging
- Real-time updates

---

**Last Updated:** January 2025


