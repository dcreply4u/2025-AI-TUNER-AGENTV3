#!/usr/bin/env python3
"""
Compare MoTeC ECU features with our existing ECU knowledge base.
Analyze gaps and create comparison document.
"""

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
LOGGER = logging.getLogger(__name__)

# MoTeC M400/M600/M800/M880 Features from the manual
MOTEC_FEATURES = {
    "ECU_Models": {
        "M400": {
            "injector_outputs": 4,
            "ignition_outputs": 4,
            "connector": "Waterproof plastic connector with gold plated contacts",
            "logging_memory": "512kByte (option)",
            "wideband_lambda": "1 input (option)",
            "options": [
                "Traction Control",
                "Boost Enhancement (Anti-lag)",
                "Hi/Lo Injection",
                "Gear Change Ignition Cut",
                "CAM Control",
                "Drive by Wire"
            ]
        },
        "M600": {
            "injector_outputs": 6,
            "ignition_outputs": 6,
            "connector": "Waterproof plastic connector with gold plated contacts",
            "logging_memory": "512kByte (option)",
            "wideband_lambda": "2 inputs (option)",
            "options": [
                "Traction Control",
                "Boost Enhancement (Anti-lag)",
                "Hi/Lo Injection",
                "Gear Change Ignition Cut",
                "CAM Control",
                "Drive by Wire"
            ]
        },
        "M800": {
            "injector_outputs": "8 standard, 12 (option, occupies 4 ignition outputs)",
            "ignition_outputs": 6,
            "connector": "Waterproof plastic connector with gold plated contacts",
            "logging_memory": "1MByte (option)",
            "wideband_lambda": "2 inputs (option)",
            "options": [
                "Traction Control",
                "Boost Enhancement (Anti-lag)",
                "Hi/Lo Injection",
                "Gear Change Ignition Cut",
                "CAM Control",
                "Drive by Wire",
                "Pro Analysis",
                "Telemetry",
                "Multi Pulse Injection",
                "Servo Motor Control"
            ]
        },
        "M880": {
            "injector_outputs": "8 standard, 12 (option, occupies 4 ignition outputs)",
            "ignition_outputs": 6,
            "connector": "Military style Autosport connector",
            "logging_memory": "4MByte (option)",
            "wideband_lambda": "2 inputs (option)",
            "options": [
                "Traction Control",
                "Boost Enhancement (Anti-lag)",
                "Hi/Lo Injection",
                "Gear Change Ignition Cut",
                "CAM Control",
                "Drive by Wire",
                "Pro Analysis",
                "Telemetry",
                "Multi Pulse Injection",
                "Servo Motor Control"
            ]
        }
    },
    "Inputs": {
        "Main_Engine_Sensors": [
            "REF trigger sensor (RPM)",
            "SYNC trigger sensor (synchronization)",
            "Throttle Position",
            "Manifold Pressure (MAP)",
            "Air Temperature",
            "Engine Temperature (Coolant)"
        ],
        "Analog_Voltage_Inputs": 8,
        "Analog_Temperature_Inputs": 6,
        "Digital_Inputs": 4,
        "Trigger_Inputs": ["REF (Crank Reference)", "SYNC (Cam Sync)"],
        "Lambda_Inputs": "1-2 wideband lambda inputs (Bosch LSU or NTK compatible)"
    },
    "Outputs": {
        "Injector_Outputs": "4-12 depending on model",
        "Ignition_Outputs": "4-6 depending on model",
        "Auxiliary_Outputs": "8 auxiliary outputs",
        "Fuel_Pump_Control": "Yes",
        "Lambda_Heater_Control": "Via auxiliary output"
    },
    "Options": {
        "Data_Logging": "Internal memory logging (512KB to 4MB depending on model)",
        "Pro_Analysis": "Advanced data logging analysis (M800/M880 only)",
        "Wideband_Lambda": "Single or dual wideband lambda support",
        "Telemetry": "Radio telemetry to pits (M800/M880 only)",
        "Traction_Control": "Available on all models",
        "Boost_Enhancement": "Anti-lag system",
        "Hi_Lo_Injection": "Dual injector staging",
        "Gear_Change_Ignition_Cut": "Ignition cut during gear changes",
        "CAM_Control": "Variable cam timing control",
        "Drive_by_Wire": "Electronic throttle control",
        "Multi_Pulse_Injection": "Multiple injection events per cycle (M800/M880)",
        "Servo_Motor_Control": "Servo motor control (M800/M880)"
    },
    "Calibration_Tables": [
        "Fuel Tables (Main)",
        "Ignition Tables (Main)",
        "Fuel Injection Timing",
        "Cold Start Fuel",
        "Site Tables (altitude/weather compensation)"
    ],
    "Communication": {
        "RS232": "Serial communication",
        "CAN_Bus": "CAN bus support for multiple devices",
        "OBD_II": "Not mentioned (racing/off-highway use)"
    },
    "Software": {
        "ECU_Manager": "Main calibration software",
        "Interpreter": "Free data logging analysis software",
        "Telemetry_Monitor": "Real-time telemetry viewing (M800/M880)"
    },
    "Safety_Features": [
        "Warning alarms",
        "Sensor validation",
        "On-site engine requirement for calibration"
    ]
}

# Our existing ECU features (from ECU_CONTROL_FEATURES.md and knowledge base)
OUR_FEATURES = {
    "Core_Features": {
        "Read_Write_Operations": [
            "Read ECU files and current settings",
            "Write/change any ECU parameter",
            "Support for multiple ECU vendors (Holley, Haltech, AEM, Link, MegaSquirt, MoTec, etc.)",
            "Real-time parameter updates"
        ],
        "Backup_Restore": [
            "Automatic backups before any changes",
            "Manual backup creation with descriptions",
            "File hash validation for integrity",
            "Backup validation before restore",
            "Multiple backup management",
            "Quick restore from any backup"
        ],
        "Safety_System": [
            "5-level safety classification (SAFE, CAUTION, WARNING, DANGEROUS, CRITICAL)",
            "Automatic safety analysis before each change",
            "Safety warnings for potentially harmful changes",
            "Parameter limits enforcement (min/max values)",
            "Change percentage limits (e.g., max 20% fuel map change)",
            "Dependency checking (warns about related parameters)"
        ],
        "Validation_System": [
            "Pre-change validation",
            "Backup file validation",
            "File hash verification",
            "Parameter structure validation",
            "ECU file format validation"
        ],
        "Change_Tracking": [
            "Complete change history",
            "Rollback capability",
            "Change comparison",
            "Timestamp tracking",
            "User attribution"
        ]
    },
    "ECU_Tuning_Features": [
        "Fuel VE Table: Main volumetric efficiency map for fuel calibration",
        "Ignition Timing: Spark advance control with knock protection",
        "Boost Control: Closed/open loop boost management",
        "Idle Control: E-throttle, stepper motor, or timing-based idle",
        "Flex Fuel: E85 blending with automatic map switching",
        "Individual Cylinder Correction: Per-cylinder fuel/ignition trim",
        "Injector Staging: Primary/secondary injector control",
        "Trailing Ignition: Secondary ignition event (for rotary engines)"
    ],
    "Protection_Features": [
        "Rev Limit: Fuel cut, spark cut, or blended with soft/hard cut",
        "EGT Protection: Exhaust gas temperature monitoring and power cut",
        "Lean Power Cut: Lambda-based fuel cut protection",
        "Signal Filters: TPS, RPM, MAP signal filtering",
        "Speed Limiters: Pit lane and road speed limiters"
    ],
    "Motorsport_Features": [
        "Launch Control",
        "Flat Shift",
        "Anti-lag",
        "Traction Control"
    ]
}

def compare_features():
    """Compare MoTeC features with our features."""
    
    print("="*80)
    print("MoTeC ECU vs Our ECU Features Comparison")
    print("="*80)
    
    print("\n## FEATURES WE HAVE THAT MoTeC HAS:")
    print("-" * 80)
    
    # Features in common
    common_features = []
    
    # Tuning tables
    if "Fuel Tables" in str(MOTEC_FEATURES["Calibration_Tables"]):
        common_features.append("✓ Fuel Tables/VE Tables")
    if "Ignition Tables" in str(MOTEC_FEATURES["Calibration_Tables"]):
        common_features.append("✓ Ignition Timing Tables")
    
    # Boost control
    if "Boost Enhancement" in str(MOTEC_FEATURES["Options"]):
        common_features.append("✓ Boost Control / Anti-lag")
    
    # Traction control
    if "Traction Control" in str(MOTEC_FEATURES["Options"]):
        common_features.append("✓ Traction Control")
    
    # Wideband lambda
    if "Wideband_Lambda" in MOTEC_FEATURES["Options"]:
        common_features.append("✓ Wideband Lambda Support")
    
    # Data logging
    if "Data_Logging" in MOTEC_FEATURES["Options"]:
        common_features.append("✓ Data Logging")
    
    # Multi-vendor support
    common_features.append("✓ Multi-vendor ECU support (including MoTeC)")
    
    for feature in common_features:
        print(f"  {feature.replace('✓', '[X]')}")
    
    print("\n## FEATURES MoTeC HAS THAT WE SHOULD ADD:")
    print("-" * 80)
    
    missing_features = []
    
    # MoTeC specific features we might be missing
    if "Hi/Lo Injection" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Hi/Lo Injection (dual injector staging per cylinder)")
    
    if "Gear Change Ignition Cut" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Gear Change Ignition Cut (for faster shifts)")
    
    if "CAM Control" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Variable Cam Timing (VVT/VCT) Control")
    
    if "Drive by Wire" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Drive by Wire (Electronic Throttle Control)")
    
    if "Multi Pulse Injection" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Multi-Pulse Injection (multiple injection events per cycle)")
    
    if "Servo Motor Control" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Servo Motor Control (for throttle bodies, etc.)")
    
    if "Pro Analysis" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Advanced Data Analysis (multiple graph overlays, XY plots, track map analysis)")
    
    if "Telemetry" in str(MOTEC_FEATURES["Options"]):
        missing_features.append("• Real-time Telemetry (radio transmission to pits)")
    
    if "Site Tables" in str(MOTEC_FEATURES["Calibration_Tables"]):
        missing_features.append("• Site Tables (altitude/weather compensation)")
    
    if "Fuel Injection Timing" in str(MOTEC_FEATURES["Calibration_Tables"]):
        missing_features.append("• Fuel Injection Timing Table (injection angle control)")
    
    if "Cold Start Fuel" in str(MOTEC_FEATURES["Calibration_Tables"]):
        missing_features.append("• Cold Start Fuel Table (separate from main fuel table)")
    
    for feature in missing_features:
        print(f"  {feature}")
    
    print("\n## INPUT/OUTPUT CAPABILITIES:")
    print("-" * 80)
    print("MoTeC Models:")
    print("  • M400: 4 injectors, 4 ignition, 8 aux outputs")
    print("  • M600: 6 injectors, 6 ignition, 8 aux outputs")
    print("  • M800: 8-12 injectors, 6 ignition, 8 aux outputs")
    print("  • M880: 8-12 injectors, 6 ignition, 8 aux outputs")
    print("\nInputs:")
    print("  • 8 Analog Voltage Inputs")
    print("  • 6 Analog Temperature Inputs")
    print("  • 4 Digital Inputs")
    print("  • 2 Trigger Inputs (REF/SYNC)")
    print("  • 1-2 Wideband Lambda Inputs")
    
    print("\n## CALIBRATION FEATURES:")
    print("-" * 80)
    print("MoTeC Calibration Tables:")
    for table in MOTEC_FEATURES["Calibration_Tables"]:
        print(f"  • {table}")
    
    print("\n## RECOMMENDATIONS:")
    print("-" * 80)
    print("1. Add documentation for advanced features:")
    print("   - Multi-pulse injection")
    print("   - Variable cam timing control")
    print("   - Fuel injection timing tables")
    print("   - Site tables (altitude/weather compensation)")
    print("   - Cold start fuel tables")
    print()
    print("2. Consider adding support for:")
    print("   - Gear change ignition cut")
    print("   - Servo motor control")
    print("   - Real-time telemetry")
    print("   - Advanced data analysis features")
    print()
    print("3. Document input/output capabilities:")
    print("   - Analog voltage inputs (8 channels)")
    print("   - Analog temperature inputs (6 channels)")
    print("   - Digital inputs (4 channels)")
    print("   - Auxiliary outputs (8 channels)")
    print()
    print("4. Add MoTeC-specific knowledge:")
    print("   - Model differences (M400/M600/M800/M880)")
    print("   - Option enablement system")
    print("   - CAN bus integration")
    print("   - Wideband lambda sensor setup")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    compare_features()

