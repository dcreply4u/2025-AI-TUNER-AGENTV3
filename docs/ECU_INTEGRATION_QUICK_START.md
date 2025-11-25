# ECU CAN Bus Integration - Quick Start

**Connect TelemetryIQ to your existing ECU via CAN bus in 5 minutes!**

## ✅ Yes, Major ECUs Have CAN Bus Output!

All major ECU systems can broadcast sensor data over CAN bus:

- ✅ **Holley EFI** - HEFI 3rd Party CAN Protocol (public)
- ✅ **MoTeC** - CAN telemetry output
- ✅ **AEM Infinity** - AEMNet CAN protocol
- ✅ **Haltech** - CAN telemetry
- ✅ **Link ECU** - CAN output
- ✅ **MegaSquirt** - CAN broadcast
- ✅ **OBD-II** - Standard protocol

**You don't need to replace your ECU - we read their data!**

---

## 🔌 Quick Setup (3 Steps)

### Step 1: Connect CAN Bus (2 minutes)

**Physical Connection:**
```
ECU CAN Port    →    TelemetryIQ Hardware
CAN-H (green)   →    CAN-H
CAN-L (white)   →    CAN-L
GND            →    GND
```

**Important:**
- Add 120Ω termination resistor at each end
- Use twisted pair cable
- Typical bitrate: 500 kbps

### Step 2: Configure ECU (2 minutes)

**Holley EFI:**
1. Open Holley EFI software
2. Go to "CAN Setup" → "3rd Party CAN"
3. Enable "Broadcast Telemetry"
4. Select sensors to broadcast
5. Save

**MoTeC:**
1. Configure CAN channels
2. Define telemetry messages
3. Enable broadcast

**AEM/Haltech:**
1. Enable CAN telemetry output
2. Configure message definitions

### Step 3: Start TelemetryIQ (1 minute)

```python
from interfaces.ems_interface import EMSDataInterface

# Auto-detect ECU type
ems = EMSDataInterface(
    can_interface="can0",
    bitrate=500000,
    auto_detect_ecu=True,  # Automatically detects Holley, MoTeC, etc.
)

# Or specify ECU type manually
ems = EMSDataInterface(
    can_interface="can0",
    ecu_type="holley",  # or "motec", "aem", "haltech"
)

# Connect and start reading
ems.setup_can_interface()

# Add callback for data
def on_telemetry(data):
    print(f"RPM: {data.get('rpm')}")
    print(f"Boost: {data.get('boost_psi')} PSI")
    print(f"Coolant: {data.get('coolant_temp')}°C")

ems.add_listener(on_telemetry)
ems.run()  # Starts reading in background thread
```

---

## 📊 What Data You Get

**From ECU CAN Bus:**
- Engine RPM
- Throttle Position
- Boost Pressure
- Coolant Temperature
- Oil Pressure/Temperature
- Fuel Pressure
- Air/Fuel Ratio
- Ignition Timing
- Vehicle Speed
- And more (ECU-dependent)

**Plus TelemetryIQ Features:**
- ✅ AI-powered diagnostics
- ✅ Performance analytics
- ✅ Video overlay
- ✅ Cloud sync
- ✅ Advanced logging
- ✅ Predictive maintenance

---

## 💡 Why This Is Great

### For Users:
- ✅ **Keep Your ECU:** No need to replace expensive Holley/MoTeC/AEM
- ✅ **Add Value:** Get advanced features without losing ECU investment
- ✅ **Easy Setup:** Just connect CAN bus
- ✅ **Best of Both Worlds:** Professional ECU + Advanced Analytics

### For TelemetryIQ:
- ✅ **Lower Barrier:** Users don't need to switch ECUs
- ✅ **Broader Market:** Works with any CAN-capable ECU
- ✅ **Complementary:** Enhances existing systems
- ✅ **Competitive Edge:** Unique value-add

---

## 🎯 Use Cases

1. **Data Logging:** Log all ECU data with advanced analytics
2. **AI Diagnostics:** Get predictive warnings from ECU data
3. **Performance Tracking:** Track improvements over time
4. **Video Overlay:** Overlay ECU data on racing videos
5. **Remote Tuning:** Share logs with tuner via cloud

---

## 🔧 Troubleshooting

**No Data?**
- Check CAN connections (CAN-H, CAN-L, GND)
- Verify termination resistors (120Ω at both ends)
- Check CAN bitrate matches (500 kbps typical)
- Verify ECU is broadcasting data

**Wrong Data?**
- Verify ECU type is correct
- Check CAN message definitions match
- Adjust scaling factors if needed

---

## 📚 Full Documentation

See [ECU_CAN_BUS_INTEGRATION.md](ECU_CAN_BUS_INTEGRATION.md) for:
- Detailed setup instructions
- ECU-specific configurations
- Advanced features
- Troubleshooting guide

---

**Bottom Line:** Yes, you can connect TelemetryIQ to Holley, MoTeC, AEM, and other ECUs via CAN bus - no migration required! 🚀



