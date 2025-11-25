# Hardware Connection Guide

## Quick Reference: How Sensors Connect

### reTerminal DM (Recommended Platform)

```
┌─────────────────────────────────────────────────────────┐
│              Seeed reTerminal DM                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  CAN0    │  │  CAN1    │  │   GPIO   │              │
│  │ (Built-in)│ │ (Built-in)│ │  Header  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│       │              │              │                    │
│       │              │              │                    │
│  ┌────┴────┐   ┌────┴────┐   ┌────┴────┐              │
│  │   USB   │   │   USB   │   │   I2C   │              │
│  │ Ports   │   │ Ports   │   │  /SPI   │              │
│  └─────────┘   └─────────┘   └─────────┘              │
└─────────────────────────────────────────────────────────┘
         │              │              │
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │  GPS     │   │ Camera  │   │  ADC    │
    │  Module  │   │  (USB)  │   │  Board  │
    └──────────┘   └─────────┘   └─────────┘
                                              │
                                         ┌────▼────┐
                                         │ Analog  │
                                         │ Sensors │
                                         └─────────┘
```

## Connection Methods by Sensor Type

### 1. CAN Bus Sensors (Best for Automotive)

**What connects:**
- ECU (Engine Control Unit)
- Wideband O2 controllers
- Data loggers (RaceCapture, etc.)
- CAN-enabled sensors

**Cables needed:**
- 2 wires: CAN-H (high) and CAN-L (low)
- Twisted pair cable recommended
- 120Ω termination resistors (one at each end)

**reTerminal DM:**
- ✅ **Built-in CAN0 and CAN1** - No additional hardware!
- Just connect CAN-H and CAN-L wires

**Raspberry Pi:**
- Need CAN HAT (e.g., PiCAN2, ~$30-50)
- Then connect CAN wires

**Example:**
```
ECU CAN-H ──────────────── CAN-H (can0)
ECU CAN-L ──────────────── CAN-L (can0)
ECU GND   ──────────────── GND
```

### 2. Analog Sensors (Pressure, Temperature, etc.)

**What connects:**
- Oil pressure sensors (0-5V output)
- Fuel pressure sensors
- Coolant temperature sensors
- Any sensor with voltage output

**Cables needed:**
- Signal wire (carries 0-5V)
- Power wire (5V or 12V)
- Ground wire

**Hardware needed:**
- ADC (Analog-to-Digital Converter) board
- Common: ADS1115 (I2C, ~$10-15)
- Connects via I2C bus

**Example:**
```
Pressure Sensor          ADC Board          reTerminal DM
Signal ──────────────── ADC Ch0 ────────── I2C (SDA/SCL)
+5V    ──────────────── VCC
GND    ──────────────── GND ────────────── GND
```

### 3. Digital Sensors (Switches, On/Off)

**What connects:**
- Transbrake switch
- Nitrous solenoid status
- Safety switches
- Any on/off sensor

**Cables needed:**
- Signal wire
- Ground wire
- Optional: Pull-up resistor

**Hardware needed:**
- ✅ **Built-in GPIO** on all platforms
- No additional hardware!

**Example:**
```
Switch                  reTerminal DM
Signal ──────────────── GPIO Pin 18
GND    ──────────────── GND
(3.3V pull-up via software)
```

### 4. Serial Sensors (GPS, Some Controllers)

**What connects:**
- GPS modules
- Some wideband controllers
- Serial data loggers

**Cables needed:**
- USB cable (if USB device)
- OR: TX, RX, GND wires (if UART)

**Hardware needed:**
- ✅ **Built-in USB ports** - No additional hardware!
- OR: UART pins on GPIO header

**Example:**
```
GPS Module (USB) ─────── USB Port
OR
GPS Module (UART) ────── TX/RX/GND on GPIO
```

### 5. I2C Sensors (Multiple Sensors on One Bus)

**What connects:**
- Temperature sensors (DS18B20, TMP102)
- Pressure sensors with I2C
- Accelerometers
- Multiple sensors (up to 127 devices)

**Cables needed:**
- SDA (data) wire
- SCL (clock) wire
- Power and ground

**Hardware needed:**
- ✅ **Built-in I2C bus** on all platforms
- Pull-up resistors (usually on sensor board)

**Example:**
```
Sensor 1 ────┬─── SDA ──── reTerminal DM
Sensor 2 ────┤
Sensor 3 ────┘
             └─── SCL ──── reTerminal DM
             └─── 3.3V ──── reTerminal DM
             └─── GND ──── reTerminal DM
```

## Complete Racing Setup Example

### Hardware Configuration

**reTerminal DM with:**
1. **CAN0** → Holley ECU
2. **CAN1** → Wideband O2 Controller
3. **GPIO Pin 18** → Transbrake switch
4. **GPIO Pin 19** → Nitrous solenoid status
5. **I2C ADC Board** → Oil pressure sensor (channel 0)
6. **I2C ADC Board** → Fuel pressure sensor (channel 1)
7. **USB** → GPS module
8. **USB** → Front camera
9. **USB** → Rear camera

### Wiring Summary

**CAN Bus (2 buses):**
- CAN0: ECU (CAN-H, CAN-L, GND)
- CAN1: Wideband (CAN-H, CAN-L, GND)
- 120Ω resistors at each end

**GPIO (Digital):**
- Pin 18: Transbrake (signal + GND)
- Pin 19: Nitrous (signal + GND)

**I2C (Analog via ADC):**
- ADS1115 board connected to I2C
- Channel 0: Oil pressure sensor
- Channel 1: Fuel pressure sensor

**USB:**
- GPS module
- Cameras (2x)

### Software Configuration

```python
# sensors_config.json
{
    "can_sensors": {
        "can0": {
            "ecu": {
                "vendor": "holley",
                "dbc_file": "holley.dbc"
            }
        },
        "can1": {
            "wideband": {
                "id": 0x200,
                "type": "lambda"
            }
        }
    },
    "analog_sensors": {
        "oil_pressure": {
            "channel": 0,
            "type": "pressure",
            "min_voltage": 0.5,
            "max_voltage": 4.5,
            "min_value": 0,
            "max_value": 100,
            "unit": "psi"
        },
        "fuel_pressure": {
            "channel": 1,
            "type": "pressure",
            "min_voltage": 0.5,
            "max_voltage": 4.5,
            "min_value": 0,
            "max_value": 100,
            "unit": "psi"
        }
    },
    "digital_sensors": {
        "transbrake": {
            "pin": 18,
            "pull": "up",
            "active_low": false
        },
        "nitrous_solenoid": {
            "pin": 19,
            "pull": "up",
            "active_low": false
        }
    }
}
```

## Cost Breakdown

### reTerminal DM Setup
- **reTerminal DM**: ~$300-400
- **ADC Board (ADS1115)**: ~$10-15
- **Cables/Connectors**: ~$20-30
- **Termination Resistors**: ~$5
- **Total**: ~$335-450

### Raspberry Pi Setup
- **Raspberry Pi 5**: ~$75
- **CAN HAT**: ~$30-50
- **ADC HAT**: ~$10-15
- **Cables/Connectors**: ~$20-30
- **Total**: ~$135-170

## Power Requirements

**reTerminal DM:**
- Input: 12V DC (2.5A recommended)
- Can power sensors via GPIO (3.3V/5V, limited current)
- Use external power supply for high-current sensors

**Sensor Power:**
- Most sensors: 5V or 12V
- Check sensor datasheet for current requirements
- Use voltage regulators for sensitive sensors

## Troubleshooting

### CAN Bus Not Working
1. Check termination resistors (120Ω at each end)
2. Verify CAN-H and CAN-L are not swapped
3. Check bitrate matches (usually 500kbps)
4. Test with: `candump can0`

### Analog Sensor Reading Wrong Values
1. Verify voltage range (0-3.3V or 0-5V)
2. Check ADC reference voltage
3. Calibrate sensor (use known values)
4. Check for electrical noise (use shielded cables)

### Digital Sensor Not Responding
1. Verify pull-up/pull-down configuration
2. Check GPIO pin number
3. Verify voltage levels (3.3V vs 5V)
4. Test with multimeter

## Next Steps

1. **Identify your sensors** - What type of output do they have?
2. **Choose connection method** - CAN, analog, digital, serial?
3. **Get required hardware** - ADC board, CAN HAT, etc.
4. **Wire everything up** - Follow wiring diagrams
5. **Configure in software** - Use sensor configuration files
6. **Test with demo mode** - Verify readings before real use

For detailed sensor-specific instructions, see the sensor manufacturer's documentation.

