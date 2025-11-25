# ECU CAN Bus Integration Guide

**Integrate TelemetryIQ with existing ECU systems via CAN bus - no migration required!**

## Overview

TelemetryIQ can read sensor data from major ECU systems (Holley, MoTeC, AEM, Haltech, etc.) via their CAN bus outputs. This allows users to keep their existing ECU while adding our advanced analytics, AI features, and telemetry capabilities.

**Key Benefit:** Users don't need to replace their ECU - we work alongside it!

---

## ✅ Supported ECU Systems

### 1. Holley EFI Systems

**Models Supported:**
- Holley HP EFI
- Holley Dominator EFI
- Holley Terminator X
- Holley Terminator X Max

**CAN Bus Capabilities:**
- ✅ **Public CAN Protocol:** Holley publishes their "HEFI 3rd Party CAN Communications Protocol"
- ✅ **Sensor Data Broadcast:** RPM, boost, injector pulse width, throttle position, coolant temp, etc.
- ✅ **CAN I/O Module:** Additional 8 inputs/8 outputs via CAN bus
- ✅ **Real-time Data:** High-speed telemetry transmission

**CAN IDs (Common):**
- `0x180` - Engine RPM, Throttle Position
- `0x181` - Coolant Temp, Oil Pressure
- `0x182` - Boost Pressure, Fuel Pressure
- `0x183` - Injector Pulse Width, Ignition Timing
- (Full protocol available from Holley)

**Integration Method:**
1. Connect CAN bus from Holley ECU to TelemetryIQ hardware
2. Configure Holley to broadcast telemetry data
3. TelemetryIQ automatically detects and decodes Holley CAN messages
4. Data appears in our dashboard and analytics

**Documentation:**
- Holley EFI CAN Protocol (available from Holley)
- Racepak uses same protocol (reference implementation)

---

### 2. MoTeC Systems

**Models Supported:**
- MoTeC M1 Series
- MoTeC M150 Series
- MoTeC M800/M880
- MoTeC M130

**CAN Bus Capabilities:**
- ✅ **CAN Telemetry Output:** Comprehensive sensor data broadcast
- ✅ **Custom CAN Messages:** Configurable message definitions
- ✅ **High-Speed Data:** Up to 1 Mbps CAN bus
- ✅ **Multiple Channels:** Can broadcast on multiple CAN channels

**CAN Configuration:**
- MoTeC uses configurable CAN message definitions
- Users can export CAN configuration from MoTeC software
- TelemetryIQ can import MoTeC CAN definitions

**Integration Method:**
1. Export CAN configuration from MoTeC software
2. Import into TelemetryIQ (or use default MoTeC templates)
3. Connect CAN bus
4. TelemetryIQ decodes MoTeC messages automatically

---

### 3. AEM Systems

**Models Supported:**
- AEM Infinity Series
- AEM Series 2
- AEM CD-7/CD-8

**CAN Bus Capabilities:**
- ✅ **CAN Telemetry:** Sensor data broadcast
- ✅ **AEMNet Protocol:** AEM's proprietary CAN protocol
- ✅ **Wideband O2 Integration:** CAN-based wideband sensors
- ✅ **Dash Integration:** CAN dash support (we can read same data)

**Integration Method:**
1. Configure AEM to broadcast telemetry on CAN bus
2. Connect CAN bus to TelemetryIQ
3. Use AEM CAN definitions (or auto-detect)
4. Data automatically decoded and displayed

---

### 4. Haltech Systems

**Models Supported:**
- Haltech Elite Series
- Haltech Platinum Series
- Haltech Nexus

**CAN Bus Capabilities:**
- ✅ **CAN Telemetry Output:** Real-time sensor data
- ✅ **CAN Dash Support:** Same protocol used for dash displays
- ✅ **Configurable Messages:** User-defined CAN messages
- ✅ **High Update Rates:** Fast telemetry transmission

**Integration Method:**
1. Configure Haltech CAN telemetry output
2. Connect CAN bus
3. TelemetryIQ uses Haltech CAN definitions
4. Automatic data decoding

---

### 5. Other Supported Systems

- **Link ECU:** CAN telemetry support
- **MegaSquirt:** CAN broadcast available
- **FuelTech:** CAN output support
- **Emtron:** CAN telemetry
- **RaceCapture Pro:** CAN data logger (we can read their CAN output)
- **OBD-II:** Standard OBD-II CAN protocol

---

## 🔌 Hardware Connection

### Physical Connection

**Required:**
- CAN-H wire (typically green/yellow)
- CAN-L wire (typically white/green)
- 120Ω termination resistor (one at each end of bus)
- Ground connection

**Connection Diagram:**
```
ECU CAN Port          TelemetryIQ Hardware
     |                      |
  CAN-H ──────────────── CAN-H
  CAN-L ──────────────── CAN-L
  GND   ──────────────── GND
     |                      |
  [120Ω]                 [120Ω]
```

**Important:**
- Use twisted pair cable for CAN-H and CAN-L
- Terminate both ends of the bus (120Ω resistors)
- Keep CAN wires away from high-voltage wires
- Maximum bus length: ~40 meters at 500 kbps

### TelemetryIQ Hardware Options

**Option 1: reTerminal DM (Recommended)**
- ✅ Built-in dual CAN FD interfaces (can0, can1)
- ✅ No additional hardware needed
- ✅ Professional-grade reliability

**Option 2: Raspberry Pi 5**
- ✅ CAN HAT required (MCP2515 or MCP2518FD)
- ✅ Single or dual CAN support
- ✅ Cost-effective solution

**Option 3: Windows with Treehopper**
- ✅ CAN adapter required
- ✅ USB-to-CAN interface
- ✅ Good for development/testing

---

## ⚙️ Software Configuration

### Step 1: Configure ECU CAN Output

**Holley EFI:**
1. Open Holley EFI software
2. Go to "CAN Setup" or "3rd Party CAN"
3. Enable "Broadcast Telemetry"
4. Select data to broadcast (RPM, boost, temps, etc.)
5. Set CAN bitrate (typically 500 kbps)
6. Save configuration

**MoTeC:**
1. Open MoTeC software
2. Configure CAN channels
3. Define CAN messages with sensor data
4. Set transmission rates
5. Export CAN configuration (optional)

**AEM:**
1. Open AEM software
2. Configure CAN telemetry
3. Select sensors to broadcast
4. Set CAN parameters

### Step 2: Configure TelemetryIQ

**Automatic Detection:**
```python
from interfaces.can_interface import OptimizedCANInterface
from interfaces.ems_interface import EMSDataInterface

# Auto-detect ECU type
can_interface = OptimizedCANInterface(channel="can0", bitrate=500000)
ems_interface = EMSDataInterface(can_interface=can_interface)

# Auto-detect will identify Holley, MoTeC, AEM, etc.
detected_ecu = ems_interface.detect_ecu_type()
print(f"Detected ECU: {detected_ecu}")
```

**Manual Configuration:**
```python
# Specify ECU type
ems_interface = EMSDataInterface(
    can_interface=can_interface,
    ecu_type="holley",  # or "motec", "aem", "haltech", etc.
)
```

### Step 3: Read Sensor Data

```python
# Connect and start reading
ems_interface.connect()

# Read telemetry data
telemetry = ems_interface.read_telemetry()
print(f"RPM: {telemetry.get('rpm')}")
print(f"Boost: {telemetry.get('boost_psi')}")
print(f"Coolant Temp: {telemetry.get('coolant_temp_c')}")
```

---

## 📊 Data Available via CAN Bus

### Common Sensor Data (Most ECUs)

**Engine Parameters:**
- Engine RPM
- Throttle Position (%)
- Manifold Pressure / Boost (PSI/kPa)
- Coolant Temperature (°C/°F)
- Oil Temperature (°C/°F)
- Oil Pressure (PSI/kPa)
- Fuel Pressure (PSI/kPa)

**Air/Fuel:**
- Air/Fuel Ratio (AFR)
- Lambda
- Wideband O2 sensor readings
- Injector Pulse Width (ms)
- Injector Duty Cycle (%)

**Ignition:**
- Ignition Timing (degrees)
- Knock Sensor Activity
- Spark Advance

**Performance:**
- Vehicle Speed (MPH/kph)
- Acceleration (G-force)
- Torque (estimated)
- Horsepower (estimated)

**Additional (ECU-dependent):**
- Flex Fuel percentage
- Methanol injection status
- Nitrous system status
- Transmission data
- Launch control status

---

## 🎯 Use Cases

### 1. Data Logging & Analysis
- **Benefit:** Log all ECU sensor data with our advanced analytics
- **Use Case:** Track performance over time, identify trends
- **Value:** Better than basic ECU logging software

### 2. AI-Powered Diagnostics
- **Benefit:** Our AI analyzes ECU data for predictive maintenance
- **Use Case:** Get warnings before problems occur
- **Value:** Prevent costly engine damage

### 3. Real-Time Monitoring
- **Benefit:** Customizable dashboard with all ECU data
- **Use Case:** Track critical parameters during racing/tuning
- **Value:** Better visibility than basic ECU displays

### 4. Performance Analytics
- **Benefit:** Advanced performance metrics (0-60, lap times, etc.)
- **Use Case:** Track improvements over time
- **Value:** Data-driven tuning decisions

### 5. Video Overlay
- **Benefit:** Overlay ECU data on video recordings
- **Use Case:** Create professional racing videos
- **Value:** Better content for social media/sponsors

### 6. Cloud Sync & Sharing
- **Benefit:** Sync logs to cloud, share with tuner
- **Use Case:** Remote tuning support
- **Value:** Professional tuner access without being present

---

## 💡 Business Advantages

### For Users:
- ✅ **Keep Existing ECU:** No need to replace expensive ECU
- ✅ **Add Value:** Get advanced features without losing ECU investment
- ✅ **Easy Integration:** Simple CAN bus connection
- ✅ **Best of Both Worlds:** Professional ECU + Advanced Analytics

### For TelemetryIQ:
- ✅ **Lower Barrier to Entry:** Users don't need to switch ECUs
- ✅ **Broader Market:** Works with any CAN-capable ECU
- ✅ **Complementary Product:** Enhances existing systems
- ✅ **Competitive Advantage:** Unique value-add over basic ECU software

---

## 🔧 Technical Implementation

### CAN Message Decoding

TelemetryIQ includes decoders for major ECU systems:

```python
from interfaces.ems_interface import EMSDataInterface

# Holley decoder
holley_decoder = EMSDataInterface.get_decoder("holley")
rpm = holley_decoder.decode_rpm(can_message)

# MoTeC decoder
motec_decoder = EMSDataInterface.get_decoder("motec")
boost = motec_decoder.decode_boost(can_message)

# Auto-detect and decode
ems_interface = EMSDataInterface()
telemetry = ems_interface.read_telemetry()  # Auto-decodes based on ECU type
```

### Custom CAN Definitions

For custom ECU configurations:

```python
# Import custom CAN definition (DBC file or JSON)
from interfaces.can_interface import CANSignalMapper

mapper = CANSignalMapper()
mapper.load_dbc("custom_ecu.dbc")  # Load DBC file
# or
mapper.load_json("custom_ecu.json")  # Load JSON definition

# Use custom mapper
can_interface = OptimizedCANInterface(can_signal_mapper=mapper)
```

---

## 📋 Setup Checklist

### ECU Configuration:
- [ ] Enable CAN telemetry output on ECU
- [ ] Configure CAN bitrate (typically 500 kbps)
- [ ] Select sensors to broadcast
- [ ] Verify CAN messages are being transmitted

### Hardware Connection:
- [ ] Connect CAN-H wire
- [ ] Connect CAN-L wire
- [ ] Connect ground wire
- [ ] Install 120Ω termination resistors (both ends)
- [ ] Verify connections are secure

### TelemetryIQ Setup:
- [ ] Connect CAN interface to TelemetryIQ hardware
- [ ] Configure CAN channel in TelemetryIQ
- [ ] Select ECU type (or auto-detect)
- [ ] Verify data is being received
- [ ] Test all sensor readings

---

## 🚨 Troubleshooting

### No Data Received

**Check:**
1. CAN bus connections (CAN-H, CAN-L, GND)
2. Termination resistors installed (120Ω at both ends)
3. CAN bitrate matches (500 kbps typical)
4. ECU is broadcasting data
5. CAN interface is properly initialized

**Diagnostic:**
```python
# Check CAN bus activity
from interfaces.can_interface import OptimizedCANInterface

can = OptimizedCANInterface(channel="can0")
can.connect()
stats = can.get_statistics()
print(f"Messages/sec: {stats.messages_per_second}")
print(f"Unique IDs: {stats.unique_ids}")
```

### Incorrect Data Values

**Check:**
1. ECU type is correctly identified
2. CAN message definitions match ECU configuration
3. Scaling factors are correct
4. Units match (PSI vs kPa, °C vs °F)

**Fix:**
- Verify ECU CAN protocol documentation
- Check CAN message definitions
- Adjust scaling factors if needed

### Missing Sensors

**Check:**
1. ECU is configured to broadcast that sensor
2. Sensor is properly connected to ECU
3. CAN message includes that sensor data
4. TelemetryIQ decoder includes that sensor

**Fix:**
- Configure ECU to broadcast missing sensors
- Update CAN message definitions
- Add custom decoder if needed

---

## 📚 Resources

### ECU Documentation:
- **Holley:** HEFI 3rd Party CAN Communications Protocol
- **MoTeC:** MoTeC CAN Protocol Documentation
- **AEM:** AEMNet CAN Protocol
- **Haltech:** Haltech CAN Protocol

### TelemetryIQ Documentation:
- [CAN Bus Guide](CAN_BUS_GUIDE.md)
- [Sensor Integration Guide](SENSOR_INTEGRATION.md)
- [Hardware Connections](HARDWARE_CONNECTIONS.md)

---

## 🎯 Summary

**Yes!** Major ECU systems (Holley, MoTeC, AEM, Haltech, etc.) have CAN bus outputs that TelemetryIQ can read. This allows:

✅ **Easy Integration:** Simple CAN bus connection  
✅ **No Migration Required:** Users keep their existing ECU  
✅ **Value Addition:** Advanced analytics on top of professional ECU  
✅ **Broad Compatibility:** Works with any CAN-capable ECU  

**This is a key competitive advantage** - we complement existing systems rather than replace them!

---

**Last Updated:** December 2024



