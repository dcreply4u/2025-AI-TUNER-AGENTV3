# Sensor Connection Quick Reference

## TL;DR - How to Connect Sensors

### reTerminal DM (Easiest - Built-in CAN!)

**CAN Bus Sensors (ECU, Wideband, etc.):**
```
Sensor CAN-H ──── CAN-H (can0 or can1)
Sensor CAN-L ──── CAN-L (can0 or can1)
Sensor GND   ──── GND
+ 120Ω resistor at each end
```

**Analog Sensors (Pressure, Temp):**
```
Sensor Signal ──── ADC Board ──── I2C ──── reTerminal DM
Sensor Power  ──── ADC Board
Sensor GND    ──── ADC Board ──── GND
```

**Digital Sensors (Switches):**
```
Switch Signal ──── GPIO Pin (e.g., 18)
Switch GND    ──── GND
```

**USB Sensors (GPS, Cameras):**
```
Just plug into USB port!
```

## Sensor Types → Connection Method

| Sensor Type | Connection Method | Hardware Needed | Cost |
|------------|------------------|-----------------|------|
| ECU Data | CAN Bus | None (built-in on reTerminal DM) | $0 |
| Wideband O2 | CAN Bus or Serial | None (CAN) or USB adapter | $0-10 |
| Oil Pressure | Analog → ADC | ADC board (ADS1115) | $10-15 |
| Fuel Pressure | Analog → ADC | ADC board (ADS1115) | $10-15 |
| Transbrake Switch | Digital GPIO | None (built-in) | $0 |
| Nitrous Solenoid | Digital GPIO | None (built-in) | $0 |
| GPS | USB Serial | None (USB) | $0 |
| Camera | USB | None (USB) | $0 |

## reTerminal DM Advantages

✅ **Dual CAN FD built-in** - No CAN HAT needed!  
✅ **GPIO header** - Direct digital sensor connection  
✅ **USB ports** - Plug-and-play for GPS, cameras  
✅ **I2C/SPI buses** - For ADC boards and I2C sensors  
✅ **Industrial grade** - Rugged for automotive use  

## Minimum Setup (Just ECU)

**Hardware:**
- reTerminal DM
- CAN wires (2 wires)
- 120Ω resistors (2x)

**Connection:**
```
ECU ──CAN── reTerminal DM (can0)
```

**That's it!** The software auto-detects the ECU vendor.

## Typical Racing Setup

**Hardware:**
- reTerminal DM
- ADC board (ADS1115) - $15
- CAN wires
- GPIO wires
- USB devices (GPS, cameras)

**Connections:**
- CAN0: ECU
- CAN1: Wideband
- ADC: Oil pressure, Fuel pressure
- GPIO: Transbrake, Nitrous
- USB: GPS, 2x Cameras

**Total Additional Cost:** ~$15-20 (just the ADC board)

## Software Configuration

All sensors are configured in `sensors_config.json`:

```json
{
    "can_sensors": { ... },
    "analog_sensors": { ... },
    "digital_sensors": { ... }
}
```

The software automatically:
- Detects CAN vendor
- Reads all configured sensors
- Combines data into unified telemetry stream
- Logs everything
- Displays in GUI

## Need Help?

1. Check sensor datasheet for output type
2. Choose appropriate connection method
3. Wire according to diagrams
4. Configure in software
5. Test with demo mode first

See `SENSOR_INTEGRATION.md` for detailed instructions.

