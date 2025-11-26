# GPS, IMU, and ADAS Implementation Plan

**Date:** November 26, 2025  
**Purpose:** Implement VBOX 3i-compatible GPS, IMU, and ADAS features for hardware installation today

---

## Overview

This plan implements professional-grade GPS (dual antenna, RTK), IMU (Kalman filter integration), and ADAS (testing modes) features based on VBOX 3i specifications.

---

## Phase 1: GPS Enhancements

### 1.1 Dual Antenna Support
**Status:** ❌ Missing  
**Priority:** HIGH

**Implementation:**
- Extend `GPSInterface` to support dual antenna (A & B)
- Add antenna separation configuration
- Implement slip angle calculation from dual antenna
- Add dual antenna lock status tracking

**Files to Create/Modify:**
- `interfaces/gps_interface.py` - Add dual antenna support
- `services/dual_antenna_service.py` - NEW: Dual antenna calculations
- `ui/gps_status_widget.py` - NEW: GPS status display

**Key Features:**
- Primary antenna (A) and secondary antenna (B)
- Antenna separation distance configuration
- Slip angle calculation (front/rear left/right, COG)
- Dual antenna lock status
- Orientation testing (roll/pitch separation)

### 1.2 RTK/DGPS Support
**Status:** ❌ Missing  
**Priority:** HIGH

**Implementation:**
- Add RTK/DGPS mode selection (None/CMR/RTCMv3/NTRIP/SBAS)
- Implement RTK status tracking (Float/Fixed)
- Add DGPS correction data handling
- Support NTRIP client connection

**Files to Create/Modify:**
- `interfaces/gps_interface.py` - Add RTK/DGPS support
- `services/rtk_service.py` - NEW: RTK processing
- `services/ntrip_client.py` - NEW: NTRIP client

**Key Features:**
- RTK 2cm accuracy support
- NTRIP modem integration
- Base station radio link support
- SBAS differential corrections
- RTK Float/Fixed status
- Differential age tracking

### 1.3 GPS Configuration
**Status:** 🚧 Partial  
**Priority:** MEDIUM

**Implementation:**
- GPS optimization modes (High/Medium/Low dynamics)
- Elevation mask configuration (10-25°)
- Leap second configuration
- GPS coldstart command
- Sample rate configuration (1/5/10/20/50/100 Hz)

**Files to Modify:**
- `interfaces/gps_interface.py` - Add configuration options
- `ui/gps_config_widget.py` - NEW: GPS configuration UI

---

## Phase 2: IMU Integration

### 2.1 Kalman Filter Integration
**Status:** ❌ Missing  
**Priority:** HIGH

**Implementation:**
- Implement Kalman filter for GPS/IMU fusion
- Add IMU initialization (30s stationary)
- Implement calibration procedure
- Add IMU attitude channels (pitch, roll, yaw)
- Support roof mount and in-vehicle mount modes

**Files to Create/Modify:**
- `services/kalman_filter.py` - NEW: Kalman filter implementation
- `services/imu_integration_service.py` - NEW: IMU integration service
- `interfaces/imu_interface.py` - Enhance with Kalman filter support

**Key Features:**
- 30-second stationary initialization
- Full calibration procedure (figure-8, brake stops)
- Antenna to IMU offset configuration
- IMU to reference point translation
- Robot blend (safety feature)
- ADAS mode filter (separate filter for ADAS)

### 2.2 IMU Channels
**Status:** 🚧 Partial  
**Priority:** MEDIUM

**Implementation:**
- IMU Attitude channels (Head_imu, Pitch_imu, Roll_imu, Pos.Qual., Lng_Jerk, Lat_Jerk, Head_imu2)
- Serial IMU channels (x/y/z accel, temp, pitch/roll/yaw rate)
- IMU temperature logging
- Longitudinal/Lateral jerk calculation

**Files to Modify:**
- `interfaces/imu_interface.py` - Add all IMU channels
- `services/imu_integration_service.py` - Process IMU data

### 2.3 Wheel Speed Integration
**Status:** ❌ Missing  
**Priority:** MEDIUM

**Implementation:**
- CAN-based wheel speed input (2 channels)
- Antenna to wheel reference point offset
- Vehicle CAN database support
- Kalman filter with wheel speed

**Files to Create:**
- `services/wheel_speed_integration.py` - NEW: Wheel speed integration

---

## Phase 3: ADAS Enhancements

### 3.1 ADAS Modes
**Status:** 🚧 Basic implementation exists  
**Priority:** HIGH

**Enhancement:**
- Complete all ADAS modes (1/2/3 target, static point, lane departure, multi-static)
- Add moving base modes (MB-Base, MB-Rover)
- Implement ADAS smoothing
- Add set points functionality

**Files to Modify:**
- `services/adas_manager.py` - Enhance existing implementation
- `ui/adas_config_widget.py` - NEW: ADAS configuration UI

**Key Features:**
- Subject/Target vehicle modes
- Static point measurement
- Lane departure detection (3 lanes)
- Multi-static point mode
- Moving base support
- ADAS smoothing (speed threshold, smoothing distance)

### 3.2 ADAS Channels
**Status:** ❌ Missing  
**Priority:** MEDIUM

**Implementation:**
- ADAS 1 & 2 channel sets
- Vehicle separation parameters
- Time to collision (TTC)
- Relative position (X/Y/Z)
- Lane offset calculation

**Files to Modify:**
- `services/adas_manager.py` - Add channel output
- `ui/adas_display_widget.py` - NEW: ADAS data display

---

## Phase 4: Integration & UI

### 4.1 Data Stream Integration
**Status:** 🚧 Partial  
**Priority:** HIGH

**Implementation:**
- Integrate dual antenna GPS into data stream
- Integrate IMU Kalman filter into data stream
- Integrate ADAS calculations into data stream
- Add channel logging for all new features

**Files to Modify:**
- `controllers/data_stream_controller.py` - Add GPS/IMU/ADAS integration

### 4.2 UI Components
**Status:** ❌ Missing  
**Priority:** MEDIUM

**Implementation:**
- GPS status panel (dual antenna, RTK status, satellites)
- IMU status panel (initialization, calibration, status)
- ADAS display panel (separation, TTC, relative position)
- Configuration dialogs for GPS/IMU/ADAS

**Files to Create:**
- `ui/gps_status_panel.py` - NEW
- `ui/imu_status_panel.py` - NEW
- `ui/adas_display_panel.py` - NEW
- `ui/gps_config_dialog.py` - NEW
- `ui/imu_config_dialog.py` - NEW
- `ui/adas_config_dialog.py` - NEW

---

## Phase 5: Knowledge Base Ingestion

### 5.1 VBOX 3i Document Ingestion
**Status:** ❌ Missing  
**Priority:** HIGH

**Implementation:**
- Extract text from VBOX 3i PDF
- Chunk document into sections
- Ingest into vector knowledge store
- Tag with metadata (GPS, IMU, ADAS, etc.)

**Files to Create:**
- `scripts/ingest_vbox_document.py` - NEW: PDF ingestion script

**Key Sections to Ingest:**
- GPS/GNSS features
- Dual antenna system
- RTK/DGPS setup
- IMU integration
- Kalman filter calibration
- ADAS modes
- CAN bus configuration
- Setup menus

---

## Implementation Order

1. **GPS Dual Antenna** (Phase 1.1) - Core feature
2. **IMU Kalman Filter** (Phase 2.1) - Core feature
3. **ADAS Enhancements** (Phase 3.1) - Complete existing
4. **Data Stream Integration** (Phase 4.1) - Connect everything
5. **Knowledge Base Ingestion** (Phase 5.1) - Documentation
6. **UI Components** (Phase 4.2) - User interface
7. **RTK/DGPS** (Phase 1.2) - Advanced feature
8. **Wheel Speed Integration** (Phase 2.3) - Advanced feature

---

## Testing Checklist

- [ ] Dual antenna GPS reading both antennas
- [ ] Slip angle calculation from dual antenna
- [ ] RTK status tracking (Float/Fixed)
- [ ] IMU initialization (30s stationary)
- [ ] Kalman filter calibration procedure
- [ ] ADAS modes (1/2/3 target, static point, lane departure)
- [ ] Data stream integration (all channels logged)
- [ ] Knowledge base search (VBOX 3i features)
- [ ] UI displays (GPS/IMU/ADAS status)

---

## Notes

- Hardware installation today: GPS, IMU, ADAS modules
- Implementation should be modular and configurable
- Fallback to single antenna if dual not available
- Graceful degradation if RTK not available
- IMU can work without Kalman filter (basic mode)
- ADAS can work in basic mode without full features

---

**End of Plan**
