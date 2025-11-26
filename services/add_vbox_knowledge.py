"""
Add VBOX 3i knowledge to AI advisor knowledge base.
This script processes the VBOX 3i feature comparison document and adds it to the vector store.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Any

from services.vector_knowledge_store import VectorKnowledgeStore

LOGGER = logging.getLogger(__name__)


def add_vbox_knowledge_to_store(vector_store: VectorKnowledgeStore) -> int:
    """
    Add VBOX 3i knowledge to the vector knowledge store.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        
    Returns:
        Number of knowledge entries added
    """
    count = 0
    
    # VBOX 3i knowledge entries organized by category
    knowledge_entries = [
        # GPS/GNSS Features
        {
            "text": """GPS/GNSS Features - VBOX 3i Dual Antenna System

The VBOX 3i Dual Antenna (v5) supports dual GPS antenna configuration for advanced orientation testing and slip angle calculation.

Basic GPS Functionality:
- Dual antenna tracking (Antenna A & B)
- GPS sample rates: 1, 5, 10, 20, 50, 100 Hz (configurable)
- GPS optimization modes: High/Medium/Low dynamics
- Elevation mask: 10-25° configurable
- Leap second: Configurable (18s default)
- GPS coldstart: Button/Software command
- Satellite tracking: GPS + GLONASS support
- Position quality: Logged continuously
- Solution type: GNSS/DGPS/RTK Float/Fixed

Dual Antenna Features:
- Dual Antenna Mode: Enabled/Disabled
- Antenna Separation: Configurable distance between antennas
- Orientation Testing: Separate roll/pitch calculation from dual antenna
- Slip Angle Calculation: Calculated from dual antenna positions
- Slip Angle Channels: Front/Rear Left/Right, COG (Center of Gravity)
- Dual Antenna Lock Status: LED indicator for lock status

DGPS/RTK Features:
- DGPS Modes: None/CMR/RTCMv3/NTRIP/MB-Base/MB-Rover/SBAS
- RTK 2cm Accuracy: Achieved with CMR or RTCMv3 format
- NTRIP Support: SIM/Wi-Fi connection
- Base Station Support: Radio link for RTK correction
- SBAS Support: Satellite-based augmentation system
- DGPS Baud Rates: 19200/38400/115200 kbit/s
- RTK Float/Fixed Status: Logged continuously
- Differential Age: Logged for quality assessment""",
            "metadata": {
                "topic": "VBOX 3i GPS/GNSS Features",
                "category": "gps_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "GPS, GNSS, dual antenna, RTK, DGPS, GLONASS, slip angle, orientation"
            }
        },
        
        # IMU Integration
        {
            "text": """IMU Integration Features - VBOX 3i

The VBOX 3i integrates with IMU04/IMU03 inertial measurement units for high-accuracy motion tracking.

IMU Hardware Support:
- IMU Integration: IMU04/IMU03 compatible
- IMU Connection: CAN/KF port (RLCAB119)
- IMU Initialization: 30s stationary calibration required
- IMU Calibration: Full calibration procedure with pitch/roll offset
- Roof Mount Mode: Automatic 1m Z offset for roof-mounted systems
- In-Vehicle Mount: Manual offset configuration
- Antenna to IMU Offset: X/Y/Z configurable offsets
- IMU to Reference Point: Translation offsets for reference point

IMU Kalman Filter:
- Kalman Filter: Enabled with IMU integration
- Robot Blend: Safety feature for robot control
- ADAS Mode Filter: Separate filter mode for ADAS testing
- Filter Status: Logged as KF Status channel
- IMU Coast Mode: Up to 5 minutes of GPS-denied operation
- Pitch/Roll Offset Calibration: Zero calibration procedure

IMU Channels:
- IMU Attitude Channels: Head_imu, Pitch_imu, Roll_imu, Pos.Qual., Lng_Jerk, Lat_Jerk, Head_imu2
- Serial IMU Channels: x/y/z acceleration, temperature, pitch/roll/yaw rate
- IMU Temperature: Logged continuously
- Longitudinal/Lateral Jerk: Calculated and logged

Wheel Speed Integration:
- Wheel Speed Input: 2 channels via CAN bus
- Antenna to Wheel Offset: X/Y/Z configurable
- Vehicle CAN Database: Pre-configured vehicle support
- Wheel Speed CAN Config: .dbc file support
- Kalman Filter with Wheel Speed: Improved accuracy with wheel speed fusion""",
            "metadata": {
                "topic": "VBOX 3i IMU Integration",
                "category": "imu_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "IMU, Kalman filter, inertial measurement, wheel speed, calibration, attitude"
            }
        },
        
        # ADAS Features
        {
            "text": """ADAS Features - VBOX 3i Advanced Driver-Assistance Systems Testing

The VBOX 3i provides comprehensive ADAS testing modes for vehicle safety system validation.

ADAS Modes:
- ADAS Mode Selection: Off/1 Target/2 Target/3 Target/Static Point/Lane Departure/Multi Static
- Subject Vehicle Mode: Testing from subject vehicle perspective
- Target Vehicle Mode: 1/2/3 target vehicle tracking
- Static Point Mode: Fixed point reference testing
- Lane Departure Mode: Lane 1/2/3 detection and testing
- Multi Static Point: Multiple fixed reference points
- Moving Base Mode: MB-Base/MB-Rover for mobile base stations
- Data at Target: Vehicle separation and relative positioning

ADAS Configuration:
- ADAS Smoothing: Speed threshold and smoothing distance configuration
- Set Points: Contact point definition for testing
- ADAS Channels: ADAS 1 & 2 channel sets
- ADAS CAN Delay: Mode-specific delay configuration

ADAS Testing Applications:
- AEB (Autonomous Emergency Braking) testing
- ACC (Adaptive Cruise Control) validation
- Lane departure warning system testing
- Forward collision warning testing
- Pedestrian detection system validation""",
            "metadata": {
                "topic": "VBOX 3i ADAS Features",
                "category": "adas_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "ADAS, autonomous, safety, testing, target tracking, lane departure, AEB, ACC"
            }
        },
        
        # CAN Bus Features
        {
            "text": """CAN Bus Features - VBOX 3i

The VBOX 3i provides comprehensive CAN bus input and output capabilities.

CAN Configuration:
- Vehicle CAN (VCI): SER port (default) for vehicle CAN bus
- Racelogic CAN: CAN port (default) for Racelogic devices
- CAN Baud Rates: 125/250/500/1000 kbit/s + custom rates
- CAN Termination: Enable/Disable hardware termination
- CAN Delay: Fixed (15.5ms speed, 20ms position) / Minimum (4ms/8.5ms)
- CAN Port Swapping: CAN/SER port swap capability
- CAN Pass Through: 6 messages, 12 channels pass-through

CAN Input:
- VCI Channels: Up to 16 vehicle CAN input channels
- Racelogic CAN Channels: Up to 32 Racelogic CAN channels
- .dbc File Import: Import CAN database files
- Vehicle Database: Pre-configured vehicle support
- Manual CAN Setup: Manual message and channel configuration
- .dbc File Export: Export CAN database configuration

CAN Output:
- Motorola Format: Standard messages 0x301-0x307, 0x308-0x32B
- Intel Format: Alternative format 0x066, 0x06B, etc. (Stahle)
- Transmitted Identifiers: Configurable CAN message IDs
- Extended IDs (29-bit): Support for extended CAN identifiers
- ADAS CAN Output: Messages 0x30A-0x30F for ADAS systems
- CAN Message Selection: Per-message enable/disable
- Data Byte Configuration: Channel selection per byte

CAN Applications:
- Robot control system integration
- External data acquisition systems
- ECU communication and control
- Real-time telemetry output
- ADAS system integration""",
            "metadata": {
                "topic": "VBOX 3i CAN Bus Features",
                "category": "can_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "CAN bus, CAN output, Motorola, Intel, .dbc, vehicle CAN, Racelogic CAN, robot control"
            }
        },
        
        # Analog/Digital I/O
        {
            "text": """Analog/Digital I/O Features - VBOX 3i

The VBOX 3i provides comprehensive analog and digital input/output capabilities.

Analog Inputs:
- Analog Input Channels: 4 channels (24-bit, ±50V range)
- Sample Rate: 500 Hz (optional high-speed sampling)
- Synchronous Sampling: All 4 channels sampled simultaneously
- Scale/Offset: Per-channel scaling and offset configuration
- Sensor Power Output: 5V (120mA) + Vbatt for sensor power
- Live Data View: Real-time data display during configuration
- Channel Naming: Custom channel names for identification

Digital Inputs:
- Digital Input 1: Event marker/brake trigger (10ns resolution)
- Digital Input 2: Remote logging switch
- Event Marker: Handheld device for marking events
- Trigger Event Time: Logged with 10ns precision
- Brake Distance Correction: Correction to trigger point

Analog/Digital Outputs:
- Analog Output 1 (AD1): 0-5V, configurable source/range
- Analog Output 2 (AD2): 0-5V, configurable source/range
- Digital Output 1 (AD1): 5V/0V, threshold-based switching
- Digital Output 2 (AD2): Frequency/pulse output (velocity)
- Output Test Mode: Source value testing for verification
- Hysteresis/Tolerance: For digital output stability
- Pulse Per Metre: Configurable pulse rate for velocity output

Applications:
- Sensor data acquisition (analog inputs)
- Event marking and trigger capture (digital inputs)
- External system control (analog/digital outputs)
- Robot control signals (outputs)
- High-speed data logging (500 Hz analog)""",
            "metadata": {
                "topic": "VBOX 3i Analog/Digital I/O",
                "category": "io_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "analog input, digital input, analog output, digital output, event marker, sensor, trigger"
            }
        },
        
        # Logging Features
        {
            "text": """Logging Features - VBOX 3i

The VBOX 3i provides comprehensive data logging capabilities with flexible configuration.

Logging Configuration:
- Log Rates: 1, 5, 10, 20, 50, 100 Hz (standard rates)
- Log Conditions: Only when moving/Continuous/Advanced (8 conditions)
- Stop Logging Delay: 0-10 seconds configurable delay
- Serial Output Rate: 5, 20, 50, 100 Hz configurable
- 500 Hz Analog Logging: 4 channels at 500 Hz (optional)
- Compact Flash Storage: CF card for data storage
- File Format: .VBB proprietary format

Channel Logging:
- Standard Channels: 50+ standard channels available
- Channel Selection: Per-channel enable/disable
- Log to Memory Card: Per-channel logging control
- Send Over Serial: Per-channel serial output control
- Internal A/D Channels: 4 channels available
- CAN Input Channels: Up to 16 VCI, 32 RL CAN channels
- Channel Usage Display: Bus usage percentage display
- Channel Limit: 64 total channels maximum

Channel Categories:
- GPS/GNSS channels (position, speed, heading, quality)
- IMU channels (attitude, acceleration, jerk)
- CAN input channels (vehicle data)
- Analog input channels (sensor data)
- Calculated channels (slip angle, distance, etc.)
- ADAS channels (target tracking, separation)""",
            "metadata": {
                "topic": "VBOX 3i Logging Features",
                "category": "logging_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "logging, data logging, channels, sample rate, CF card, .VBB format"
            }
        },
        
        # Communication Features
        {
            "text": """Communication Features - VBOX 3i

The VBOX 3i provides multiple communication interfaces for data transfer and configuration.

Serial Communication:
- Primary RS232 (SER): 115200 max baud, 20/50/100 Hz output rates
- Secondary RS232 (CAN): DGPS/RTK correction data
- USB 2.0: 100 Hz full rate data transfer
- Serial Output Rates: 5/20/50/100 Hz configurable
- Bandwidth Limitation: Channel count limits for serial output

Bluetooth:
- Bluetooth Radio: 100 Hz full rate wireless data transfer
- SPP (Serial Port Profile): Standard Bluetooth serial profile
- Secure/Unsecure: PIN protection (default: 1234)
- Bluetooth Antenna: External antenna for extended range

Voice Tagging:
- Audio Recording: .wav file format audio recording
- GNSS Timestamp Sync: 0.5s accuracy GPS synchronization
- Headset/Microphone: Support for headset with switch
- Auto-stop (30s): Automatic recording stop after 30 seconds
- Replay in Test Suite: Audio replay with speaker icons

Applications:
- Real-time telemetry streaming (serial/USB/Bluetooth)
- Configuration and setup (USB/serial)
- Voice notes synchronized with GPS data
- Wireless data acquisition (Bluetooth)
- RTK correction data (secondary serial)""",
            "metadata": {
                "topic": "VBOX 3i Communication Features",
                "category": "communication_features",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "serial, USB, Bluetooth, voice tagging, audio recording, wireless, RTK"
            }
        },
        
        # Setup & Configuration
        {
            "text": """Setup & Configuration - VBOX 3i

The VBOX 3i provides comprehensive setup and configuration menus organized by feature category.

General Menu:
- Load/Save Settings: .rcf file format for configuration
- Configuration Overview: Quick view of all settings
- Connection Status: COM port, refresh, disconnect
- VBOX Information: Serial number, firmware version, hardware code
- Time Sync: PC time synchronization
- Recent Configurations: Change history tracking

Channels Menu:
- Standard Channels Tab: GPS, IMU, calculated channels
- Internal A/D Tab: Analog input channels
- Internal CAN Input Tab: Vehicle CAN channels
- Internal Slip/Dual Antenna Tab: Dual antenna channels (Dual Antenna only)
- ADAS 1 Tab: ADAS channel set 1 (when ADAS enabled)
- ADAS 2 Tab: ADAS channel set 2 (when ADAS enabled)
- Module Rescan: Dynamic module detection
- Per-Channel Log/Serial: Individual channel control

GPS Menu:
- GPS Information: Receiver info, coldstart command
- GPS Settings: Leap second, elevation mask
- GPS Optimization: High/Medium/Low dynamics modes
- DGPS/RTK Settings: Mode, baud rate configuration
- Dual Antenna Settings: Enable, separation, orientation, slip angle
- Engineering Diagnostics: Non-standard settings

IMU Menu:
- IMU Integration Enable: Enable/disable IMU
- Roof Mount Mode: Automatic offset configuration
- Robot Blend: Safety feature enable
- ADAS Mode Filter: ADAS-specific filter mode
- Antenna to IMU Offset: X/Y/Z offset configuration
- IMU to Reference Point: Translation offset
- Wheel Speed Input: CAN wheel speed configuration
- Pitch/Roll Offset Calibration: Zero calibration

ADAS Menu:
- ADAS Mode Selection: Mode and submode selection
- ADAS Smoothing: Speed threshold and distance

CAN Menu:
- VCI Baud Rate: Vehicle CAN baud rate
- CAN Termination: Hardware termination control
- CAN Delay: Fixed/Minimum delay modes
- CAN/RS232 Port Assignment: Port swap configuration
- .dbc File Export: Export CAN database
- Transmitted Identifiers: CAN output message IDs
- CAN Pass Through: Pass-through configuration

Output Menu:
- Digital 1 Configuration: Digital output 1 setup
- Analog 1 Configuration: Analog output 1 setup
- Digital 2 (Frequency): Digital output 2 frequency setup
- Analog 2 Configuration: Analog output 2 setup
- Output Test: Test mode for outputs""",
            "metadata": {
                "topic": "VBOX 3i Setup & Configuration",
                "category": "configuration",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "setup, configuration, menu, GPS menu, IMU menu, ADAS menu, CAN menu, output menu"
            }
        },
        
        # Hardware Features
        {
            "text": """Hardware Features - VBOX 3i

The VBOX 3i provides comprehensive hardware interfaces and indicators.

Front Panel:
- LOG Button: Start/stop logging, override thresholds
- FUNC Button: Sample rate toggle (20/100 Hz)
- Coldstart: 5 second hold for GPS coldstart
- Default Setup: 10 second hold both buttons for factory reset

LED Indicators:
- PWR LED: Green (ready) / Red (error)
- CF LED: Blue flash (writing to card)
- LOG LED: Green (logging active)
- SATS LED: Red/Orange/Green sequences (satellite status)
- DUAL LED: Orange (enabled) / Green (locked) - dual antenna
- DIFF LED: Orange/Green (DGPS/RTK status)
- IMU LED: Orange/Green (IMU status)
- BLUETOOTH LED: Blue flash/solid (Bluetooth status)
- D IN LED: Green (digital input triggered)
- CAN LED: Green flash (CAN data decoded)
- SER LED: Yellow flash (serial traffic)

Power & Connectors:
- Power Range: 7-30V DC input
- Power Warning Tone: Low voltage warning
- Antenna Connectors: A (primary) + B (secondary) for dual antenna
- Analog Input (A IN): 25-way D-type, 4 channels
- Digital Input (D IN): 2 digital inputs
- Power (PWR): 2-way LEMO connector
- AD1/AD2 Outputs: 3-pin LEMO connectors
- CAN/SER Ports: 5-way LEMO connectors
- USB: USB 2.0 connector
- Compact Flash: Type I CF card slot""",
            "metadata": {
                "topic": "VBOX 3i Hardware Features",
                "category": "hardware",
                "source": "VBOX_3i_User_Guide",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "hardware, LED, buttons, connectors, power, antenna, CF card, LEMO"
            }
        }
    ]
    
    # Add all knowledge entries to the vector store
    for entry in knowledge_entries:
        try:
            doc_id = vector_store.add_knowledge(
                text=entry["text"],
                metadata=entry["metadata"]
            )
            count += 1
            LOGGER.info(f"Added VBOX 3i knowledge: {entry['metadata']['topic']}")
        except Exception as e:
            LOGGER.error(f"Failed to add VBOX 3i knowledge '{entry['metadata']['topic']}': {e}")
            continue
    
    LOGGER.info(f"VBOX 3i knowledge addition complete: {count} entries added")
    return count


def main():
    """Main function to add VBOX 3i knowledge."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize vector store
    vector_store = VectorKnowledgeStore()
    
    # Add VBOX 3i knowledge
    count = add_vbox_knowledge_to_store(vector_store)
    
    print(f"Added {count} VBOX 3i knowledge entries to AI advisor knowledge base")
    return count


if __name__ == "__main__":
    main()

