# VBOX 3i Dual Antenna (v5) vs AI Tuner Agent - Feature Comparison

**Document Date:** November 26, 2025  
**VBOX Reference:** VBOX 3i Dual Antenna (v5) with Firmware Version 2.8 - User Guide  
**AI Tuner Version:** 2025-AI-TUNER-AGENTV3

---

## Executive Summary

This document compares the features and capabilities of the VBOX 3i Dual Antenna (v5) data logger against the current AI Tuner Agent implementation. The goal is to identify missing features and sub-features that should be added to match or exceed VBOX 3i capabilities.

**Legend:**
- ✅ **Implemented** - Feature exists in AI Tuner
- 🚧 **Partial** - Feature partially implemented or needs enhancement
- ❌ **Missing** - Feature not yet implemented
- 🔄 **Different Approach** - Feature exists but implemented differently

---

## 1. GPS/GNSS Features

### 1.1 Basic GPS Functionality
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| GPS/GNSS Tracking | ✅ Dual antenna (A & B) | ✅ Single GPS | 🚧 | Need dual antenna support |
| GPS Sample Rates | 1, 5, 10, 20, 50, 100 Hz | Variable (10 Hz typical) | 🚧 | Need configurable rates |
| GPS Optimization Modes | High/Medium/Low dynamics | N/A | ❌ | Missing optimization modes |
| Elevation Mask | 10-25° configurable | N/A | ❌ | Missing elevation mask setting |
| Leap Second | Configurable (18s default) | N/A | ❌ | Missing leap second config |
| GPS Coldstart | ✅ Button/Software | N/A | ❌ | Missing coldstart capability |
| Satellite Tracking | GPS + GLONASS | GPS only | 🚧 | Need GLONASS support |
| Position Quality | ✅ Logged | ✅ Logged | ✅ | Implemented |
| Solution Type | GNSS/DGPS/RTK Float/Fixed | Basic GPS | 🚧 | Need RTK support |

### 1.2 Dual Antenna Features (VBOX 3i Dual Antenna Specific)
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Dual Antenna Mode | ✅ Enabled/Disabled | ❌ | ❌ | **MISSING** - Core feature |
| Antenna Separation | ✅ Configurable distance | ❌ | ❌ | **MISSING** |
| Orientation Testing | ✅ Separate roll/pitch | ❌ | ❌ | **MISSING** |
| Slip Angle Calculation | ✅ From dual antenna | 🚧 Wheel slip only | 🚧 | Different approach |
| Slip Angle Channels | Front/Rear Left/Right, COG | Wheel slip % | 🔄 | Different calculation |
| Dual Antenna Lock Status | ✅ LED indicator | ❌ | ❌ | **MISSING** |

### 1.3 DGPS/RTK Features
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| DGPS Modes | None/CMR/RTCMv3/NTRIP/MB-Base/MB-Rover/SBAS | ❌ | ❌ | **MISSING** - Critical for accuracy |
| RTK 2cm Accuracy | ✅ CMR or RTCMv3 | ❌ | ❌ | **MISSING** |
| NTRIP Support | ✅ SIM/Wi-Fi | ❌ | ❌ | **MISSING** |
| Base Station Support | ✅ Radio link | ❌ | ❌ | **MISSING** |
| SBAS Support | ✅ | ❌ | ❌ | **MISSING** |
| DGPS Baud Rates | 19200/38400/115200 kbit/s | N/A | ❌ | **MISSING** |
| RTK Float/Fixed Status | ✅ Logged | ❌ | ❌ | **MISSING** |
| Differential Age | ✅ Logged | ❌ | ❌ | **MISSING** |

---

## 2. IMU Integration Features

### 2.1 IMU Hardware Support
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| IMU Integration | ✅ IMU04/IMU03 | 🚧 Generic IMU | 🚧 | Need specific IMU support |
| IMU Connection | CAN/KF port (RLCAB119) | I2C/SPI | 🔄 | Different interface |
| IMU Initialization | ✅ 30s stationary | ❌ | ❌ | **MISSING** |
| IMU Calibration | ✅ Full calibration procedure | Basic | 🚧 | Need full calibration |
| Roof Mount Mode | ✅ Auto 1m Z offset | ❌ | ❌ | **MISSING** |
| In-Vehicle Mount | ✅ Manual offset config | ❌ | ❌ | **MISSING** |
| Antenna to IMU Offset | ✅ X/Y/Z configurable | ❌ | ❌ | **MISSING** |
| IMU to Reference Point | ✅ Translation offsets | ❌ | ❌ | **MISSING** |

### 2.2 IMU Kalman Filter
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Kalman Filter | ✅ Enabled with IMU | ❌ | ❌ | **MISSING** - Critical feature |
| Robot Blend | ✅ Safety feature | ❌ | ❌ | **MISSING** |
| ADAS Mode Filter | ✅ Separate filter mode | ❌ | ❌ | **MISSING** |
| Filter Status | ✅ Logged (KF Status) | ❌ | ❌ | **MISSING** |
| IMU Coast Mode | ✅ Up to 5 min | ❌ | ❌ | **MISSING** |
| Pitch/Roll Offset Calibration | ✅ Zero calibration | ❌ | ❌ | **MISSING** |

### 2.3 IMU Channels
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| IMU Attitude Channels | Head_imu, Pitch_imu, Roll_imu, Pos.Qual., Lng_Jerk, Lat_Jerk, Head_imu2 | Basic accel/gyro | 🚧 | Need full IMU channels |
| Serial IMU Channels | x/y/z accel, temp, pitch/roll/yaw rate | Basic | 🚧 | Need all channels |
| IMU Temperature | ✅ Logged | ❌ | ❌ | **MISSING** |
| Longitudinal/Lateral Jerk | ✅ Logged | ❌ | ❌ | **MISSING** |

### 2.4 Wheel Speed Integration
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Wheel Speed Input | ✅ 2 channels (CAN) | 🚧 Basic | 🚧 | Need CAN wheel speed |
| Antenna to Wheel Offset | ✅ X/Y/Z configurable | ❌ | ❌ | **MISSING** |
| Vehicle CAN Database | ✅ Pre-configured vehicles | ❌ | ❌ | **MISSING** |
| Wheel Speed CAN Config | ✅ .dbc file support | ❌ | ❌ | **MISSING** |
| Kalman Filter with Wheel Speed | ✅ Improved accuracy | ❌ | ❌ | **MISSING** |

---

## 3. Logging Features

### 3.1 Logging Configuration
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Log Rates | 1, 5, 10, 20, 50, 100 Hz | Variable | 🚧 | Need standard rates |
| Log Conditions | Only when moving/Continuous/Advanced (8 conditions) | Basic | 🚧 | Need advanced conditions |
| Stop Logging Delay | 0-10 seconds | ❌ | ❌ | **MISSING** |
| Serial Output Rate | 5, 20, 50, 100 Hz | Variable | 🚧 | Need configurable rates |
| 500 Hz Analog Logging | ✅ 4 channels | ❌ | ❌ | **MISSING** |
| Compact Flash Storage | ✅ CF card | SD card/SSD | 🔄 | Different media |
| File Format | .VBB (proprietary) | CSV/JSON | 🔄 | Different format |

### 3.2 Channel Logging
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Standard Channels | ✅ 50+ channels | ✅ Multiple | ✅ | Implemented |
| Channel Selection | ✅ Per-channel enable | ✅ | ✅ | Implemented |
| Log to Memory Card | ✅ Per-channel | ✅ | ✅ | Implemented |
| Send Over Serial | ✅ Per-channel | ✅ | ✅ | Implemented |
| Internal A/D Channels | ✅ 4 channels | ✅ | ✅ | Implemented |
| CAN Input Channels | ✅ Up to 16 VCI, 32 RL CAN | ✅ Multiple | ✅ | Implemented |
| Channel Usage Display | ✅ Bus usage % | ❌ | ❌ | **MISSING** |
| Channel Limit | ✅ 64 total channels | Variable | 🚧 | Need limit management |

---

## 4. CAN Bus Features

### 4.1 CAN Configuration
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Vehicle CAN (VCI) | ✅ SER port (default) | ✅ | ✅ | Implemented |
| Racelogic CAN | ✅ CAN port (default) | ❌ | ❌ | **MISSING** |
| CAN Baud Rates | 125/250/500/1000 kbit/s + custom | ✅ Configurable | ✅ | Implemented |
| CAN Termination | ✅ Enable/Disable | ❌ | ❌ | **MISSING** |
| CAN Delay | Fixed (15.5ms speed, 20ms position) / Minimum (4ms/8.5ms) | ❌ | ❌ | **MISSING** |
| CAN Port Swapping | ✅ CAN/SER swap | ❌ | ❌ | **MISSING** |
| CAN Pass Through | ✅ 6 messages, 12 channels | ❌ | ❌ | **MISSING** |
| CANVEL Channel | ✅ Speed substitution | ❌ | ❌ | **MISSING** |

### 4.2 CAN Input
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| VCI Channels | ✅ Up to 16 channels | ✅ Multiple | ✅ | Implemented |
| Racelogic CAN Channels | ✅ Up to 32 channels | ❌ | ❌ | **MISSING** |
| .dbc File Import | ✅ | ✅ | ✅ | Implemented |
| Vehicle Database | ✅ Pre-configured | ❌ | ❌ | **MISSING** |
| Manual CAN Setup | ✅ | ✅ | ✅ | Implemented |
| .dbc File Export | ✅ | ❌ | ❌ | **MISSING** |

### 4.3 CAN Output
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Motorola Format | ✅ 0x301-0x307, 0x308-0x32B | ❌ | ❌ | **MISSING** |
| Intel Format | ✅ 0x066, 0x06B, etc. (Stahle) | ❌ | ❌ | **MISSING** |
| Transmitted Identifiers | ✅ Configurable IDs | ❌ | ❌ | **MISSING** |
| Extended IDs (29-bit) | ✅ | ❌ | ❌ | **MISSING** |
| ADAS CAN Output | ✅ 0x30A-0x30F | ❌ | ❌ | **MISSING** |
| CAN Message Selection | ✅ Per-message enable | ❌ | ❌ | **MISSING** |
| Data Byte Configuration | ✅ Channel selection | ❌ | ❌ | **MISSING** |

---

## 5. ADAS Features

### 5.1 ADAS Modes
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| ADAS Mode Selection | ✅ Off/1 Target/2 Target/3 Target/Static Point/Lane Departure/Multi Static | ❌ | ❌ | **MISSING** - Entire feature set |
| Subject Vehicle Mode | ✅ | ❌ | ❌ | **MISSING** |
| Target Vehicle Mode | ✅ 1/2/3 targets | ❌ | ❌ | **MISSING** |
| Static Point Mode | ✅ | ❌ | ❌ | **MISSING** |
| Lane Departure Mode | ✅ Lane 1/2/3 | ❌ | ❌ | **MISSING** |
| Multi Static Point | ✅ | ❌ | ❌ | **MISSING** |
| Moving Base Mode | ✅ MB-Base/MB-Rover | ❌ | ❌ | **MISSING** |
| Data at Target | ✅ Vehicle separation | ❌ | ❌ | **MISSING** |

### 5.2 ADAS Configuration
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| ADAS Smoothing | ✅ Speed threshold, smoothing distance | ❌ | ❌ | **MISSING** |
| Set Points | ✅ Contact point definition | ❌ | ❌ | **MISSING** |
| ADAS Channels | ✅ ADAS 1 & 2 channel sets | ❌ | ❌ | **MISSING** |
| ADAS CAN Delay | ✅ Mode-specific delays | ❌ | ❌ | **MISSING** |

---

## 6. Analog/Digital I/O Features

### 6.1 Analog Inputs
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Analog Input Channels | ✅ 4 channels (24-bit, ±50V) | ✅ Multiple | ✅ | Implemented |
| Sample Rate | ✅ 500 Hz (optional) | Variable | 🚧 | Need 500 Hz option |
| Synchronous Sampling | ✅ All 4 channels | ✅ | ✅ | Implemented |
| Scale/Offset | ✅ Per-channel | ✅ | ✅ | Implemented |
| Sensor Power Output | ✅ 5V (120mA) + Vbatt | ❌ | ❌ | **MISSING** |
| Live Data View | ✅ During config | ✅ | ✅ | Implemented |
| Channel Naming | ✅ Custom names | ✅ | ✅ | Implemented |

### 6.2 Digital Inputs
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Digital Input 1 | ✅ Event marker/brake trigger (10ns resolution) | ❌ | ❌ | **MISSING** |
| Digital Input 2 | ✅ Remote logging switch | ❌ | ❌ | **MISSING** |
| Event Marker | ✅ Handheld device | ❌ | ❌ | **MISSING** |
| Trigger Event Time | ✅ Logged with 10ns precision | ❌ | ❌ | **MISSING** |
| Brake Distance Correction | ✅ To trigger point | ❌ | ❌ | **MISSING** |

### 6.3 Analog/Digital Outputs
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Analog Output 1 (AD1) | ✅ 0-5V, configurable source/range | ❌ | ❌ | **MISSING** |
| Analog Output 2 (AD2) | ✅ 0-5V, configurable source/range | ❌ | ❌ | **MISSING** |
| Digital Output 1 (AD1) | ✅ 5V/0V, threshold-based | ❌ | ❌ | **MISSING** |
| Digital Output 2 (AD2) | ✅ Frequency/pulse (velocity) | ❌ | ❌ | **MISSING** |
| Output Test Mode | ✅ Source value testing | ❌ | ❌ | **MISSING** |
| Hysteresis/Tolerance | ✅ For digital outputs | ❌ | ❌ | **MISSING** |
| Pulse Per Metre | ✅ Configurable | ❌ | ❌ | **MISSING** |

---

## 7. Setup & Configuration Features

### 7.1 General Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Load/Save Settings | ✅ .rcf file format | ✅ JSON/YAML | ✅ | Implemented (different format) |
| Configuration Overview | ✅ Quick view of settings | ❌ | ❌ | **MISSING** |
| Connection Status | ✅ COM port, refresh, disconnect | ✅ | ✅ | Implemented |
| VBOX Information | ✅ Serial, firmware, hardware code | ✅ | ✅ | Implemented |
| Time Sync | ✅ PC time sync | ✅ | ✅ | Implemented |
| Recent Configurations | ✅ Change history | ❌ | ❌ | **MISSING** |

### 7.2 Channels Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Standard Channels Tab | ✅ | ✅ | ✅ | Implemented |
| Internal A/D Tab | ✅ | ✅ | ✅ | Implemented |
| Internal CAN Input Tab | ✅ | ✅ | ✅ | Implemented |
| Internal Slip/Dual Antenna Tab | ✅ (Dual Antenna only) | ❌ | ❌ | **MISSING** |
| ADAS 1 Tab | ✅ (when ADAS enabled) | ❌ | ❌ | **MISSING** |
| ADAS 2 Tab | ✅ (when ADAS enabled) | ❌ | ❌ | **MISSING** |
| Module Rescan | ✅ | ❌ | ❌ | **MISSING** |
| Per-Channel Log/Serial | ✅ | ✅ | ✅ | Implemented |

### 7.3 GPS Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| GPS Information | ✅ Receiver info, coldstart | ❌ | ❌ | **MISSING** |
| GPS Settings | ✅ Leap second, elevation mask | ❌ | ❌ | **MISSING** |
| GPS Optimization | ✅ High/Medium/Low dynamics | ❌ | ❌ | **MISSING** |
| DGPS/RTK Settings | ✅ Mode, baud rate | ❌ | ❌ | **MISSING** |
| Dual Antenna Settings | ✅ Enable, separation, orientation, slip | ❌ | ❌ | **MISSING** |
| Engineering Diagnostics | ✅ Non-standard settings | ❌ | ❌ | **MISSING** |

### 7.4 IMU Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| IMU Integration Enable | ✅ | ❌ | ❌ | **MISSING** |
| Roof Mount Mode | ✅ | ❌ | ❌ | **MISSING** |
| Robot Blend | ✅ | ❌ | ❌ | **MISSING** |
| ADAS Mode Filter | ✅ | ❌ | ❌ | **MISSING** |
| Antenna to IMU Offset | ✅ | ❌ | ❌ | **MISSING** |
| IMU to Reference Point | ✅ | ❌ | ❌ | **MISSING** |
| Wheel Speed Input | ✅ | ❌ | ❌ | **MISSING** |
| Pitch/Roll Offset Calibration | ✅ | ❌ | ❌ | **MISSING** |

### 7.5 ADAS Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| ADAS Mode Selection | ✅ | ❌ | ❌ | **MISSING** |
| Submode Selection | ✅ | ❌ | ❌ | **MISSING** |
| ADAS Smoothing | ✅ | ❌ | ❌ | **MISSING** |

### 7.6 CAN Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| VCI Baud Rate | ✅ | ✅ | ✅ | Implemented |
| CAN Termination | ✅ | ❌ | ❌ | **MISSING** |
| CAN Delay | ✅ | ❌ | ❌ | **MISSING** |
| CAN/RS232 Port Assignment | ✅ | ❌ | ❌ | **MISSING** |
| .dbc File Export | ✅ | ❌ | ❌ | **MISSING** |
| Transmitted Identifiers | ✅ | ❌ | ❌ | **MISSING** |
| CAN Pass Through | ✅ | ❌ | ❌ | **MISSING** |

### 7.7 Output Menu
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Digital 1 Configuration | ✅ | ❌ | ❌ | **MISSING** |
| Analog 1 Configuration | ✅ | ❌ | ❌ | **MISSING** |
| Digital 2 (Frequency) | ✅ | ❌ | ❌ | **MISSING** |
| Analog 2 Configuration | ✅ | ❌ | ❌ | ❌ |
| Output Test | ✅ | ❌ | ❌ | **MISSING** |

---

## 8. Communication Features

### 8.1 Serial Communication
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Primary RS232 (SER) | ✅ 115200 max, 20/50/100 Hz | ✅ USB/Serial | ✅ | Implemented |
| Secondary RS232 (CAN) | ✅ DGPS/RTK | ❌ | ❌ | **MISSING** |
| USB 2.0 | ✅ 100 Hz full rate | ✅ | ✅ | Implemented |
| Serial Output Rates | ✅ 5/20/50/100 Hz | Variable | 🚧 | Need standard rates |
| Bandwidth Limitation | ✅ Channel count limits | ❌ | ❌ | **MISSING** |

### 8.2 Bluetooth
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Bluetooth Radio | ✅ 100 Hz full rate | ❌ | ❌ | **MISSING** |
| SPP (Serial Port Profile) | ✅ | ❌ | ❌ | **MISSING** |
| Secure/Unsecure | ✅ (PIN: 1234) | ❌ | ❌ | **MISSING** |
| Bluetooth Antenna | ✅ External | ❌ | ❌ | **MISSING** |

### 8.3 Voice Tagging
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Audio Recording | ✅ .wav files | ❌ | ❌ | **MISSING** |
| GNSS Timestamp Sync | ✅ 0.5s accuracy | ❌ | ❌ | **MISSING** |
| Headset/Microphone | ✅ With switch | ❌ | ❌ | **MISSING** |
| Auto-stop (30s) | ✅ | ❌ | ❌ | **MISSING** |
| Replay in Test Suite | ✅ Speaker icons | ❌ | ❌ | **MISSING** |

---

## 9. Hardware Features

### 9.1 Front Panel
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| LOG Button | ✅ Start/stop, override thresholds | ❌ | ❌ | **MISSING** |
| FUNC Button | ✅ Sample rate toggle (20/100 Hz) | ❌ | ❌ | **MISSING** |
| Coldstart (5s hold) | ✅ | ❌ | ❌ | **MISSING** |
| Default Setup (10s hold both) | ✅ | ❌ | ❌ | **MISSING** |
| LED Indicators | ✅ 10+ LEDs | ✅ Basic | 🚧 | Need full LED set |

### 9.2 LED Indicators
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| PWR LED | ✅ Green (ready) / Red (error) | ✅ | ✅ | Implemented |
| CF LED | ✅ Blue flash (writing) | ❌ | ❌ | **MISSING** |
| LOG LED | ✅ Green (logging) | ✅ | ✅ | Implemented |
| SATS LED | ✅ Red/Orange/Green sequences | ❌ | ❌ | **MISSING** |
| DUAL LED | ✅ Orange (enabled) / Green (locked) | ❌ | ❌ | **MISSING** |
| DIFF LED | ✅ Orange/Green (DGPS/RTK status) | ❌ | ❌ | **MISSING** |
| IMU LED | ✅ Orange/Green (status) | ❌ | ❌ | **MISSING** |
| BLUETOOTH LED | ✅ Blue flash/solid | ❌ | ❌ | **MISSING** |
| D IN LED | ✅ Green (triggered) | ❌ | ❌ | **MISSING** |
| CAN LED | ✅ Green flash (data decoded) | ❌ | ❌ | **MISSING** |
| SER LED | ✅ Yellow flash (traffic) | ❌ | ❌ | **MISSING** |

### 9.3 Power & Connectors
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Power Range | ✅ 7-30V DC | ✅ 5V/12V | ✅ | Implemented |
| Power Warning Tone | ✅ Low voltage | ❌ | ❌ | **MISSING** |
| Antenna Connectors | ✅ A (primary) + B (secondary) | ✅ Single | 🚧 | Need dual antenna |
| Analog Input (A IN) | ✅ 25-way D-type, 4 channels | ✅ | ✅ | Implemented |
| Digital Input (D IN) | ✅ 2 inputs | ❌ | ❌ | **MISSING** |
| Power (PWR) | ✅ 2-way LEMO | ✅ | ✅ | Implemented |
| AD1/AD2 Outputs | ✅ 3-pin LEMO | ❌ | ❌ | **MISSING** |
| CAN/SER Ports | ✅ 5-way LEMO | ✅ | ✅ | Implemented |
| USB | ✅ USB 2.0 | ✅ | ✅ | Implemented |
| Compact Flash | ✅ Type I CF card | SD/SSD | 🔄 | Different media |

---

## 10. Data Analysis Features

### 10.1 Performance Tracking
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| Dragy-Style Metrics | ❌ | ✅ 0-60, 0-100, 1/4 mile | ✅ | **AI Tuner Advantage** |
| GPS Breadcrumb Logging | ✅ | ✅ | ✅ | Implemented |
| Best Times Tracking | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| Performance History | ❌ | ✅ JSON storage | ✅ | **AI Tuner Advantage** |

### 10.2 Log Analysis
| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| VBOX Test Suite | ✅ Proprietary software | ❌ | ❌ | **MISSING** (different approach) |
| CSV Export | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| JSON Export | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| Advanced Graphing | ✅ | ✅ | ✅ | Implemented |
| Math Channels | ✅ | ✅ | ✅ | Implemented |
| Replay Mode | ✅ | ✅ | ✅ | Implemented |

---

## 11. AI/Expert Features (AI Tuner Unique)

| Feature | VBOX 3i | AI Tuner | Status | Notes |
|---------|---------|----------|--------|-------|
| AI Advisor | ❌ | ✅ RAG-based | ✅ | **AI Tuner Advantage** |
| Voice Interaction | ❌ | ✅ (planned) | 🚧 | **AI Tuner Advantage** |
| Real-time Analysis | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| Tuning Recommendations | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| Expert Telemetry Analysis | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| Cloud Sync | ❌ | ✅ | ✅ | **AI Tuner Advantage** |
| Web Search Integration | ❌ | ✅ | ✅ | **AI Tuner Advantage** |

---

## 12. Summary of Missing Critical Features

### High Priority (Core VBOX 3i Features)
1. **Dual Antenna Support** - Complete feature set missing
2. **DGPS/RTK Support** - Critical for accuracy (2cm RTK)
3. **IMU Kalman Filter Integration** - Complete IMU feature set
4. **ADAS Modes** - Entire ADAS feature set missing
5. **CAN Output** - Motorola/Intel format, configurable IDs
6. **Analog/Digital Outputs** - AD1/AD2 outputs missing
7. **Digital Inputs** - Event marker, brake trigger missing
8. **Voice Tagging** - Audio recording with GPS sync
9. **Bluetooth** - Full 100 Hz serial output
10. **LED Indicators** - Complete LED status system

### Medium Priority (Enhanced Features)
1. **GPS Optimization Modes** - High/Medium/Low dynamics
2. **Elevation Mask** - Configurable 10-25°
3. **Wheel Speed Integration** - CAN-based with Kalman filter
4. **CAN Termination** - Hardware termination control
5. **CAN Delay** - Fixed/Minimum delay modes
6. **500 Hz Analog Logging** - High-speed analog sampling
7. **Channel Usage Display** - Bus usage percentage
8. **Vehicle CAN Database** - Pre-configured vehicle support

### Low Priority (Nice to Have)
1. **Leap Second Configuration**
2. **GPS Coldstart** - Button/software command
3. **Configuration Overview** - Quick settings view
4. **Recent Configurations** - Change history
5. **Module Rescan** - Dynamic module detection

---

## 13. Recommendations

### Immediate Actions
1. **Implement Dual Antenna Support** - This is a core differentiator for VBOX 3i
2. **Add RTK/DGPS Support** - Critical for professional-grade accuracy
3. **Implement IMU Kalman Filter** - Essential for high-accuracy applications
4. **Add CAN Output** - Required for robot control and external systems
5. **Implement ADAS Modes** - Complete feature set for ADAS testing

### Architecture Considerations
- VBOX 3i uses a hardware-based approach with dedicated GPS engines and IMU processors
- AI Tuner uses software-based approach with Raspberry Pi - consider hardware acceleration for:
  - Kalman filter processing
  - High-speed CAN message handling
  - 500 Hz analog sampling
  - Real-time RTK processing

### Feature Parity Strategy
- **Match Core Features**: Dual antenna, RTK, IMU integration, ADAS
- **Enhance with AI**: Keep AI Tuner's unique AI advisor and analysis features
- **Hybrid Approach**: Use VBOX 3i hardware capabilities + AI Tuner software intelligence

---

## 14. Conclusion

The AI Tuner Agent has several unique advantages (AI advisor, cloud sync, modern data formats) but is missing many core VBOX 3i features, particularly:

- **Dual Antenna System** (complete feature set)
- **RTK/DGPS** (professional accuracy)
- **IMU Kalman Filter** (high-accuracy motion tracking)
- **ADAS Modes** (complete ADAS testing suite)
- **CAN Output** (robot control compatibility)
- **Hardware I/O** (analog/digital outputs, event markers)

To achieve feature parity, significant development effort is required, particularly in:
1. GPS/GNSS subsystem (dual antenna, RTK)
2. IMU integration (Kalman filter, calibration)
3. CAN bus (output formats, pass-through)
4. Hardware I/O (analog/digital outputs)
5. ADAS testing modes

The AI Tuner's software-based approach provides flexibility but may need hardware acceleration or dedicated modules to match VBOX 3i's performance in time-critical applications.

---

**Document End**



