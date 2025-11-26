# VBOX 3i Feature Implementation Priority Plan

**Date:** November 26, 2025  
**Goal:** Implement all VBOX 3i features with matching sub-tabs/panels

---

## Implementation Priority

### Phase 1: Core GPS Features (Week 1-2) - HIGH PRIORITY
**Why:** Foundation for all other features

1. **GPS Sample Rates** - Configurable 1, 5, 10, 20, 50, 100 Hz
2. **GPS Optimization Modes** - High/Medium/Low dynamics
3. **Elevation Mask** - Configurable 10-25°
4. **Leap Second** - Configurable (18s default)
5. **GPS Coldstart** - Button/Software command
6. **GLONASS Support** - Add GLONASS to GPS tracking
7. **Solution Type** - GNSS/DGPS/RTK Float/Fixed status

**Sub-tab:** "GPS Features" panel

---

### Phase 2: Dual Antenna System (Week 2-3) - HIGH PRIORITY
**Why:** Core VBOX 3i differentiator

1. **Dual Antenna Mode** - Enable/Disable
2. **Antenna Separation** - Configurable distance
3. **Orientation Testing** - Separate roll/pitch from dual antenna
4. **Slip Angle Calculation** - From dual antenna positions
5. **Slip Angle Channels** - Front/Rear Left/Right, COG
6. **Dual Antenna Lock Status** - LED indicator

**Sub-tab:** "GPS Features" → "Dual Antenna" section

---

### Phase 3: RTK/DGPS (Week 3-4) - HIGH PRIORITY
**Why:** Critical for professional accuracy (2cm)

1. **DGPS Modes** - None/CMR/RTCMv3/NTRIP/MB-Base/MB-Rover/SBAS
2. **RTK 2cm Accuracy** - CMR or RTCMv3 format
3. **NTRIP Support** - SIM/Wi-Fi connection
4. **Base Station Support** - Radio link
5. **SBAS Support** - Satellite-based augmentation
6. **DGPS Baud Rates** - 19200/38400/115200 kbit/s
7. **RTK Float/Fixed Status** - Logged continuously
8. **Differential Age** - Quality assessment

**Sub-tab:** "GPS Features" → "RTK/DGPS" section

---

### Phase 4: IMU Kalman Filter (Week 4-5) - HIGH PRIORITY
**Why:** Essential for high-accuracy motion tracking

1. **IMU Integration Enable** - Enable/disable IMU
2. **IMU Initialization** - 30s stationary calibration
3. **IMU Calibration** - Full calibration procedure
4. **Roof Mount Mode** - Auto 1m Z offset
5. **In-Vehicle Mount** - Manual offset config
6. **Antenna to IMU Offset** - X/Y/Z configurable
7. **IMU to Reference Point** - Translation offsets
8. **Kalman Filter** - Enabled with IMU
9. **Robot Blend** - Safety feature
10. **ADAS Mode Filter** - Separate filter mode
11. **Filter Status** - Logged (KF Status)
12. **IMU Coast Mode** - Up to 5 min GPS-denied
13. **Pitch/Roll Offset Calibration** - Zero calibration
14. **IMU Channels** - Head_imu, Pitch_imu, Roll_imu, Jerk, etc.
15. **IMU Temperature** - Logged
16. **Wheel Speed Integration** - CAN-based with Kalman filter

**Sub-tab:** "IMU Features" panel

---

### Phase 5: ADAS Features (Week 5-6) - HIGH PRIORITY
**Why:** Complete ADAS testing suite

1. **ADAS Mode Selection** - Off/1 Target/2 Target/3 Target/Static Point/Lane Departure/Multi Static
2. **Subject Vehicle Mode** - Subject vehicle perspective
3. **Target Vehicle Mode** - 1/2/3 target tracking
4. **Static Point Mode** - Fixed point reference
5. **Lane Departure Mode** - Lane 1/2/3 detection
6. **Multi Static Point** - Multiple fixed references
7. **Moving Base Mode** - MB-Base/MB-Rover
8. **Data at Target** - Vehicle separation
9. **ADAS Smoothing** - Speed threshold, smoothing distance
10. **Set Points** - Contact point definition
11. **ADAS Channels** - ADAS 1 & 2 channel sets
12. **ADAS CAN Delay** - Mode-specific delays

**Sub-tab:** "ADAS Features" panel

---

### Phase 6: CAN Output (Week 6-7) - MEDIUM PRIORITY
**Why:** Required for robot control and external systems

1. **Motorola Format** - Messages 0x301-0x307, 0x308-0x32B
2. **Intel Format** - Messages 0x066, 0x06B, etc. (Stahle)
3. **Transmitted Identifiers** - Configurable CAN IDs
4. **Extended IDs (29-bit)** - Support for extended identifiers
5. **ADAS CAN Output** - Messages 0x30A-0x30F
6. **CAN Message Selection** - Per-message enable
7. **Data Byte Configuration** - Channel selection per byte
8. **CAN Termination** - Hardware termination control
9. **CAN Delay** - Fixed/Minimum delay modes
10. **CAN Port Swapping** - CAN/SER swap
11. **CAN Pass Through** - 6 messages, 12 channels
12. **CANVEL Channel** - Speed substitution
13. **Racelogic CAN** - Up to 32 channels
14. **.dbc File Export** - Export CAN database

**Sub-tab:** "CAN Features" panel

---

### Phase 7: Analog/Digital I/O (Week 7-8) - MEDIUM PRIORITY
**Why:** Hardware I/O for sensors and control

1. **Analog Input Channels** - 4 channels (24-bit, ±50V)
2. **500 Hz Analog Logging** - High-speed sampling option
3. **Sensor Power Output** - 5V (120mA) + Vbatt
4. **Digital Input 1** - Event marker/brake trigger (10ns resolution)
5. **Digital Input 2** - Remote logging switch
6. **Event Marker** - Handheld device support
7. **Trigger Event Time** - 10ns precision logging
8. **Brake Distance Correction** - To trigger point
9. **Analog Output 1 (AD1)** - 0-5V, configurable
10. **Analog Output 2 (AD2)** - 0-5V, configurable
11. **Digital Output 1 (AD1)** - 5V/0V, threshold-based
12. **Digital Output 2 (AD2)** - Frequency/pulse (velocity)
13. **Output Test Mode** - Source value testing
14. **Hysteresis/Tolerance** - For digital outputs
15. **Pulse Per Metre** - Configurable pulse rate

**Sub-tab:** "I/O Features" panel

---

### Phase 8: Communication Features (Week 8-9) - MEDIUM PRIORITY
**Why:** Wireless and voice capabilities

1. **Bluetooth Radio** - 100 Hz full rate
2. **SPP (Serial Port Profile)** - Standard Bluetooth serial
3. **Secure/Unsecure** - PIN protection (default: 1234)
4. **Bluetooth Antenna** - External antenna support
5. **Voice Tagging** - Audio recording (.wav)
6. **GNSS Timestamp Sync** - 0.5s accuracy
7. **Headset/Microphone** - With switch support
8. **Auto-stop (30s)** - Automatic recording stop
9. **Replay in Test Suite** - Audio replay with icons
10. **Secondary RS232** - DGPS/RTK correction
11. **Bandwidth Limitation** - Channel count limits

**Sub-tab:** "Communication Features" panel

---

### Phase 9: Logging Enhancements (Week 9-10) - LOW PRIORITY
**Why:** Enhanced logging capabilities

1. **Standard Log Rates** - 1, 5, 10, 20, 50, 100 Hz
2. **Advanced Log Conditions** - 8 conditions
3. **Stop Logging Delay** - 0-10 seconds
4. **Serial Output Rates** - 5/20/50/100 Hz standard
5. **Channel Usage Display** - Bus usage percentage
6. **Channel Limit** - 64 total channels maximum
7. **Module Rescan** - Dynamic module detection

**Sub-tab:** "Logging Features" panel

---

### Phase 10: Hardware Features (Week 10-11) - LOW PRIORITY
**Why:** Hardware indicators and controls

1. **LOG Button** - Start/stop, override thresholds
2. **FUNC Button** - Sample rate toggle (20/100 Hz)
3. **Coldstart Button** - 5s hold
4. **Default Setup** - 10s hold both buttons
5. **LED Indicators** - Complete LED set (CF, SATS, DUAL, DIFF, IMU, BLUETOOTH, D IN, CAN, SER)
6. **Power Warning Tone** - Low voltage warning

**Sub-tab:** "Hardware Features" panel

---

## UI Structure

### Main Tab: "VBOX Features" or "Advanced Features"
- Sub-tab 1: **GPS Features**
  - Basic GPS settings
  - Dual Antenna configuration
  - RTK/DGPS settings
  
- Sub-tab 2: **IMU Features**
  - IMU integration
  - Kalman filter settings
  - Calibration procedures
  - Wheel speed integration
  
- Sub-tab 3: **ADAS Features**
  - ADAS mode selection
  - Target tracking configuration
  - Lane departure settings
  - ADAS smoothing
  
- Sub-tab 4: **CAN Features**
  - CAN input configuration
  - CAN output formats (Motorola/Intel)
  - CAN pass-through
  - .dbc file management
  
- Sub-tab 5: **I/O Features**
  - Analog inputs
  - Digital inputs
  - Analog outputs
  - Digital outputs
  
- Sub-tab 6: **Communication Features**
  - Serial communication
  - Bluetooth configuration
  - Voice tagging
  
- Sub-tab 7: **Logging Features**
  - Log rates and conditions
  - Channel selection
  - Storage configuration
  
- Sub-tab 8: **Hardware Features**
  - Button controls
  - LED indicators
  - Power management

---

## Implementation Strategy

1. **Create Base UI Structure** - Sub-tabs matching VBOX 3i menu structure
2. **Implement Backend Services** - One service per feature category
3. **Add Configuration Storage** - Save/load settings
4. **Integrate with Existing Systems** - GPS, CAN, IMU interfaces
5. **Add Real-time Updates** - Live data display
6. **Testing & Validation** - Verify against VBOX 3i specifications

---

## Success Criteria

✅ All VBOX 3i features implemented  
✅ Sub-tabs match VBOX 3i menu structure  
✅ Features work with existing AI Tuner infrastructure  
✅ Configuration can be saved/loaded  
✅ Real-time data display functional  
✅ Documentation complete  

---

**Total Estimated Time:** 10-11 weeks  
**Start Date:** November 26, 2025  
**Target Completion:** February 2026

