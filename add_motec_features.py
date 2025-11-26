#!/usr/bin/env python3
"""
Add MoTeC ECU features and capabilities to the AI Chat Advisor knowledge base.
Based on MoTeC M400/M600/M800/M880 manual comparison.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from services.vector_knowledge_store import VectorKnowledgeStore
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    KB_AVAILABLE = True
except ImportError as e:
    KB_AVAILABLE = False
    LOGGER.error(f"Knowledge base modules not available: {e}")

# MoTeC ECU Features Knowledge
MOTEC_KNOWLEDGE = [
    {
        "question": "What are the different MoTeC ECU models and their capabilities?",
        "answer": """MoTeC offers several ECU models with different capabilities:

**M400:**
- 4 injector outputs
- 4 ignition outputs
- Waterproof plastic connector with gold plated contacts
- 512kByte logging memory (option)
- 1 wideband lambda input (option)
- Options: Traction Control, Boost Enhancement (Anti-lag), Hi/Lo Injection, Gear Change Ignition Cut, CAM Control, Drive by Wire

**M600:**
- 6 injector outputs
- 6 ignition outputs
- Waterproof plastic connector with gold plated contacts
- 512kByte logging memory (option)
- 2 wideband lambda inputs (option)
- Options: Traction Control, Boost Enhancement (Anti-lag), Hi/Lo Injection, Gear Change Ignition Cut, CAM Control, Drive by Wire

**M800:**
- 8 injector outputs standard
- 12 injector outputs (option, occupies 4 ignition outputs)
- 6 ignition outputs
- Waterproof plastic connector with gold plated contacts
- 1MByte logging memory (option)
- 2 wideband lambda inputs (option)
- Options: Traction Control, Boost Enhancement (Anti-lag), Hi/Lo Injection, Gear Change Ignition Cut, CAM Control, Drive by Wire, Pro Analysis, Telemetry, Multi Pulse Injection, Servo Motor Control

**M880:**
- 8 injector outputs standard
- 12 injector outputs (option, occupies 4 ignition outputs)
- 6 ignition outputs
- Military style Autosport connector
- 4MByte logging memory (option)
- 2 wideband lambda inputs (option)
- Options: Traction Control, Boost Enhancement (Anti-lag), Hi/Lo Injection, Gear Change Ignition Cut, CAM Control, Drive by Wire, Pro Analysis, Telemetry, Multi Pulse Injection, Servo Motor Control

**Key Differences:**
- M400/M600: Entry-level models with fewer outputs
- M800/M880: Advanced models with more outputs, larger logging memory, and advanced features
- M880: Military-grade connector for harsh environments""",
        "keywords": ["MoTeC", "M400", "M600", "M800", "M880", "ECU models", "injector outputs", "ignition outputs"],
        "topic": "MoTeC ECU - Models"
    },
    {
        "question": "What is Hi/Lo Injection in MoTeC ECUs?",
        "answer": """Hi/Lo Injection is a MoTeC ECU feature that allows dual injector staging per cylinder.

**How It Works:**
- Two injectors per cylinder (primary and secondary)
- Primary injector (Lo) operates at lower RPM/load
- Secondary injector (Hi) activates at higher RPM/load
- Allows precise fuel delivery across entire operating range
- Better atomization and distribution at different conditions

**Benefits:**
- Improved fuel distribution
- Better idle and low-speed operation
- Enhanced high-RPM performance
- More precise fuel control
- Can optimize injector sizing for different conditions

**Configuration:**
- Configured through ECU Manager software
- Set activation points based on RPM, load, or throttle position
- Can be used with staged turbo systems
- Works with sequential injection timing

**Use Cases:**
- High-performance engines requiring wide operating range
- Engines with large injectors that need better low-speed control
- Applications where fuel distribution is critical
- Racing applications requiring precise fuel delivery

**Note:** This feature is available as an option on all MoTeC ECU models (M400, M600, M800, M880).""",
        "keywords": ["Hi/Lo Injection", "dual injector", "staged injection", "MoTeC", "injector staging"],
        "topic": "MoTeC ECU - Hi/Lo Injection"
    },
    {
        "question": "What is Gear Change Ignition Cut in MoTeC ECUs?",
        "answer": """Gear Change Ignition Cut is a MoTeC ECU feature that cuts ignition during gear changes for faster shifts.

**How It Works:**
- Detects gear change events (via gear position sensor or clutch switch)
- Temporarily cuts ignition during shift
- Reduces engine load on transmission
- Allows faster, smoother gear changes
- Automatically restores ignition after shift

**Benefits:**
- Faster gear changes
- Reduced transmission wear
- Smoother shifts
- Better performance in racing applications
- Can reduce shift times significantly

**Configuration:**
- Configured through ECU Manager software
- Set cut duration and timing
- Can be RPM-dependent
- Works with manual and sequential transmissions
- Can be combined with flat shift features

**Use Cases:**
- Racing applications requiring fast shifts
- Manual transmissions with high power
- Sequential gearboxes
- Drag racing applications
- Track racing where shift speed is critical

**Safety Features:**
- Automatic restoration after shift
- Time limits to prevent extended cut
- Can be disabled if needed
- Works with other protection systems

**Note:** This feature is available as an option on all MoTeC ECU models.""",
        "keywords": ["Gear Change Ignition Cut", "shift cut", "gear change", "MoTeC", "ignition cut"],
        "topic": "MoTeC ECU - Gear Change Ignition Cut"
    },
    {
        "question": "What is Multi-Pulse Injection in MoTeC ECUs?",
        "answer": """Multi-Pulse Injection is an advanced MoTeC ECU feature (M800/M880 only) that allows multiple injection events per engine cycle.

**How It Works:**
- Multiple injection pulses per cylinder per cycle
- Can have 2, 3, or more injection events
- Each pulse can be timed independently
- Allows precise fuel delivery throughout intake stroke
- Better fuel atomization and mixing

**Benefits:**
- Improved fuel atomization
- Better air-fuel mixing
- Reduced emissions
- More complete combustion
- Better fuel distribution
- Can improve power and efficiency

**Configuration:**
- Configured through ECU Manager software
- Set number of pulses per cycle
- Configure timing for each pulse
- Adjust pulse width for each injection
- Can vary based on RPM and load

**Use Cases:**
- High-performance engines requiring optimal fuel delivery
- Engines with poor fuel distribution
- Applications requiring low emissions
- Engines with long intake runners
- Racing applications where every advantage counts

**Technical Details:**
- Available on M800 and M880 models only
- Requires appropriate injector drivers
- Can be combined with sequential injection
- Works with all fuel types
- Can be optimized for specific engine characteristics

**Note:** This is an advanced feature that requires understanding of injection timing and engine dynamics.""",
        "keywords": ["Multi-Pulse Injection", "multiple injection", "injection events", "MoTeC M800", "MoTeC M880"],
        "topic": "MoTeC ECU - Multi-Pulse Injection"
    },
    {
        "question": "What are Site Tables in MoTeC ECUs?",
        "answer": """Site Tables are MoTeC ECU calibration tables that provide altitude and weather compensation.

**Purpose:**
- Compensate for changes in atmospheric pressure (altitude)
- Adjust for changes in air temperature
- Account for humidity variations
- Maintain consistent performance regardless of conditions
- Essential for racing at different tracks and elevations

**How It Works:**
- Separate compensation tables for different conditions
- Adjusts fuel and ignition based on atmospheric conditions
- Uses barometric pressure sensor input
- Uses air temperature sensor input
- Automatically applies corrections to main fuel and ignition tables

**Benefits:**
- Consistent performance at different altitudes
- Automatic compensation for weather changes
- No need to retune for different tracks
- Maintains optimal air-fuel ratios
- Preserves ignition timing accuracy

**Configuration:**
- Configured through ECU Manager software
- Requires barometric pressure sensor
- Uses air temperature sensor
- Set compensation factors for different conditions
- Can be fine-tuned for specific applications

**Use Cases:**
- Racing at tracks with different elevations
- Applications where conditions vary significantly
- Engines sensitive to atmospheric changes
- Professional racing where consistency is critical
- Turbocharged engines requiring precise boost control

**Technical Details:**
- Works with main fuel and ignition tables
- Applies corrections automatically
- Can be enabled/disabled
- Requires appropriate sensors
- Essential for professional racing applications

**Note:** Site Tables are a standard feature in MoTeC ECUs and are essential for consistent performance.""",
        "keywords": ["Site Tables", "altitude compensation", "weather compensation", "barometric pressure", "MoTeC"],
        "topic": "MoTeC ECU - Site Tables"
    },
    {
        "question": "What is Fuel Injection Timing in MoTeC ECUs?",
        "answer": """Fuel Injection Timing is a MoTeC ECU feature that controls when fuel is injected during the engine cycle.

**Purpose:**
- Control injection angle relative to crank position
- Optimize fuel delivery timing
- Improve fuel atomization
- Enhance air-fuel mixing
- Maximize power and efficiency

**How It Works:**
- Separate table from main fuel table
- Controls injection start angle
- Can vary based on RPM and load
- Works with sequential injection
- Allows precise timing control

**Benefits:**
- Better fuel atomization
- Improved air-fuel mixing
- More complete combustion
- Reduced emissions
- Increased power potential
- Better fuel economy

**Configuration:**
- Configured through ECU Manager software
- Separate table from fuel quantity
- Set injection angle in degrees
- Can vary with RPM and load
- Works with sequential injection systems

**Technical Details:**
- Injection timing measured in degrees before/after TDC
- Can be optimized for different engine speeds
- Affects fuel distribution in cylinder
- Important for engines with long intake runners
- Can improve scavenging in some applications

**Use Cases:**
- High-performance engines
- Engines with variable intake geometry
- Applications requiring optimal fuel delivery
- Racing engines where every advantage counts
- Engines with poor fuel distribution

**Optimization:**
- Test different injection angles
- Monitor air-fuel ratio and power
- Consider intake runner length
- Account for valve timing
- Balance between early and late injection

**Note:** Fuel Injection Timing is a standard feature in MoTeC ECUs and is essential for optimal performance.""",
        "keywords": ["Fuel Injection Timing", "injection angle", "injection timing", "MoTeC", "fuel delivery"],
        "topic": "MoTeC ECU - Injection Timing"
    },
    {
        "question": "What is Cold Start Fuel Table in MoTeC ECUs?",
        "answer": """Cold Start Fuel Table is a MoTeC ECU feature that provides separate fuel calibration for cold engine starting.

**Purpose:**
- Separate fuel enrichment for cold starts
- Compensate for poor fuel vaporization when cold
- Ensure reliable starting in all conditions
- Prevent stalling during warm-up
- Maintain drivability when engine is cold

**How It Works:**
- Separate table from main fuel table
- Activates based on engine temperature
- Provides additional fuel when cold
- Gradually reduces enrichment as engine warms
- Works independently from main fuel calibration

**Benefits:**
- Reliable cold starting
- Smooth warm-up operation
- Prevents stalling when cold
- Maintains drivability during warm-up
- Can be optimized separately from main fuel table

**Configuration:**
- Configured through ECU Manager software
- Separate table from main fuel
- Set enrichment based on temperature
- Configure warm-up rate
- Can vary with RPM and load

**Technical Details:**
- Activates below set temperature threshold
- Enrichment amount decreases as temperature rises
- Can be RPM and load dependent
- Works with coolant temperature sensor
- Can be fine-tuned for specific applications

**Use Cases:**
- All engines requiring cold start capability
- Engines with poor cold starting characteristics
- Applications in cold climates
- Engines with large injectors
- Racing engines that need reliable starting

**Optimization:**
- Test starting at different temperatures
- Monitor air-fuel ratio during warm-up
- Adjust enrichment to prevent stalling
- Balance between too rich and too lean
- Ensure smooth transition to main fuel table

**Note:** Cold Start Fuel Table is a standard feature in MoTeC ECUs and is essential for reliable operation.""",
        "keywords": ["Cold Start Fuel", "cold start", "warm-up", "fuel enrichment", "MoTeC"],
        "topic": "MoTeC ECU - Cold Start"
    },
    {
        "question": "What input/output capabilities do MoTeC ECUs have?",
        "answer": """MoTeC ECUs have extensive input/output capabilities:

**Inputs:**
- **8 Analog Voltage Inputs:** For sensors like MAP, TPS, throttle position, etc.
- **6 Analog Temperature Inputs:** For coolant temp, air temp, oil temp, EGT, etc.
- **4 Digital Inputs:** For switches, gear position, clutch, etc.
- **2 Trigger Inputs:** REF (crank reference) and SYNC (cam sync) for engine position
- **1-2 Wideband Lambda Inputs:** For air-fuel ratio measurement (Bosch LSU or NTK sensors)

**Outputs:**
- **Injector Outputs:** 4-12 depending on model (M400: 4, M600: 6, M800/M880: 8-12)
- **Ignition Outputs:** 4-6 depending on model (M400: 4, M600/M800/M880: 6)
- **8 Auxiliary Outputs:** For fuel pump, fans, boost control, etc.
- **Lambda Heater Control:** Via auxiliary output

**Sensor Supplies:**
- **8V Engine Sensor Supply:** For engine sensors
- **5V Engine Sensor Supply:** For engine sensors
- **0V Engine Sensor Supply:** Sensor ground
- **8V Auxiliary Sensor Supply:** For auxiliary sensors and CAN bus
- **5V Auxiliary Sensor Supply:** For auxiliary sensors
- **0V Auxiliary Sensor Supply:** Auxiliary sensor ground

**Communication:**
- **RS232:** Serial communication for PC connection
- **CAN Bus:** For multiple device communication (dash, data loggers, etc.)
- **Telemetry:** Radio transmission to pits (M800/M880 only)

**Power:**
- **Battery Positive:** Main power input
- **Battery Negative:** Ground connections

**Key Features:**
- Waterproof connectors (M400/M600/M800) or military-style connectors (M880)
- Gold plated contacts for reliability
- Extensive sensor support
- Flexible I/O configuration
- Professional-grade reliability""",
        "keywords": ["MoTeC inputs", "MoTeC outputs", "sensor inputs", "analog inputs", "digital inputs", "ECU I/O"],
        "topic": "MoTeC ECU - I/O Capabilities"
    },
    {
        "question": "What is MoTeC Pro Analysis and Telemetry?",
        "answer": """MoTeC Pro Analysis and Telemetry are advanced features available on M800 and M880 ECUs.

**Pro Analysis:**
- Advanced data logging analysis software features
- Multiple graph overlays for comparison
- XY plots for correlation analysis
- Advanced math functions for data processing
- Track map analysis with GPS integration
- More sophisticated analysis than standard Interpreter software
- Enables professional-level data analysis

**Telemetry:**
- Real-time data transmission via radio to pits
- View live engine data from pit area
- Monitor performance during runs
- Real-time diagnostics and tuning support
- Graphical display using MoTeC Telemetry Monitor program
- Essential for professional racing teams
- Allows remote monitoring and support

**Benefits:**
- Real-time performance monitoring
- Immediate feedback during runs
- Remote tuning support
- Advanced data analysis capabilities
- Professional racing team features
- Better understanding of performance

**Requirements:**
- Available only on M800 and M880 models
- Requires option enablement
- Requires telemetry radio hardware
- Requires appropriate software
- Professional racing applications

**Use Cases:**
- Professional racing teams
- Applications requiring real-time monitoring
- Advanced data analysis needs
- Remote tuning support
- Performance optimization
- Racing strategy development

**Note:** These are premium features designed for professional racing applications.""",
        "keywords": ["Pro Analysis", "Telemetry", "MoTeC M800", "MoTeC M880", "data analysis", "real-time monitoring"],
        "topic": "MoTeC ECU - Advanced Features"
    },
    {
        "question": "What is Variable Cam Timing (CAM Control) in MoTeC ECUs?",
        "answer": """Variable Cam Timing (CAM Control) is a MoTeC ECU feature for controlling variable valve timing systems.

**Purpose:**
- Control variable cam timing actuators
- Optimize valve timing for different conditions
- Improve power and efficiency
- Enhance drivability
- Maximize performance across RPM range

**How It Works:**
- Controls cam timing actuators
- Adjusts cam position based on RPM and load
- Can control intake and exhaust cams independently
- Uses position feedback for closed-loop control
- Integrates with main fuel and ignition calibration

**Benefits:**
- Improved power across RPM range
- Better low-end torque
- Enhanced high-RPM power
- Improved fuel economy
- Better emissions control
- More flexible engine tuning

**Configuration:**
- Configured through ECU Manager software
- Set cam position maps based on RPM and load
- Configure actuator control parameters
- Set position feedback calibration
- Can be optimized for different conditions

**Technical Details:**
- Works with hydraulic and electric actuators
- Requires position feedback sensors
- Can control intake and exhaust separately
- Integrates with engine protection systems
- Can be RPM and load dependent

**Use Cases:**
- Engines with variable valve timing
- High-performance applications
- Applications requiring wide power band
- Engines with dual VVT systems
- Racing applications where flexibility is important

**Note:** CAM Control is available as an option on all MoTeC ECU models.""",
        "keywords": ["Variable Cam Timing", "VVT", "CAM Control", "valve timing", "MoTeC"],
        "topic": "MoTeC ECU - CAM Control"
    },
    {
        "question": "What is Servo Motor Control in MoTeC ECUs?",
        "answer": """Servo Motor Control is a MoTeC ECU feature (M800/M880 only) for controlling servo motors.

**Purpose:**
- Control servo motors for various applications
- Precise position control
- Closed-loop feedback control
- Multiple servo motor support
- Professional-grade control

**Applications:**
- Electronic throttle bodies
- Variable intake systems
- Boost control valves
- Wastegate control
- Any application requiring precise motor control

**How It Works:**
- Controls servo motor position
- Uses position feedback for closed-loop control
- Can be controlled based on various inputs
- Integrates with main ECU functions
- Precise positioning capability

**Benefits:**
- Precise control
- Closed-loop feedback
- Multiple applications
- Professional-grade performance
- Reliable operation

**Configuration:**
- Configured through ECU Manager software
- Set position maps
- Configure feedback calibration
- Set control parameters
- Can be optimized for specific applications

**Technical Details:**
- Available only on M800 and M880 models
- Requires position feedback sensors
- Works with standard servo motors
- Can control multiple servos
- Professional racing applications

**Use Cases:**
- Electronic throttle control
- Variable intake geometry
- Boost control systems
- Wastegate control
- Any application requiring servo control

**Note:** Servo Motor Control is available as an option on M800 and M880 models only.""",
        "keywords": ["Servo Motor Control", "servo control", "MoTeC M800", "MoTeC M880", "motor control"],
        "topic": "MoTeC ECU - Servo Control"
    }
]

ARTICLE_URL = "https://www.milspecwiring.com/DATA%20SHEETS/ECU/M400_M600_M800_M880_Manual_A5.pdf"
ARTICLE_SOURCE = "MoTeC M400/M600/M800/M880 ECU Manual"


def main():
    """Add MoTeC ECU features to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in MOTEC_KNOWLEDGE:
        try:
            LOGGER.info(f"Adding: {entry['question'][:60]}...")
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{entry['question']}\n\n{entry['answer']}",
                metadata={
                    "question": entry["question"],
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": ARTICLE_SOURCE,
                    "url": ARTICLE_URL,
                    "category": "MoTeC ECU",
                    "data_type": "technical_manual"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                source=ARTICLE_SOURCE,
                url=ARTICLE_URL,
                keywords=entry["keywords"],
                topic=entry["topic"],
                confidence=0.95,
                verified=True
            )
            
            added_count += 1
            LOGGER.info(f"  Successfully added")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add entry: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total entries: {len(MOTEC_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nMoTeC ECU features have been added to the knowledge base!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - MoTeC ECU models and capabilities")
    LOGGER.info(f"  - Hi/Lo Injection")
    LOGGER.info(f"  - Gear Change Ignition Cut")
    LOGGER.info(f"  - Multi-Pulse Injection")
    LOGGER.info(f"  - Site Tables (altitude/weather compensation)")
    LOGGER.info(f"  - Fuel Injection Timing")
    LOGGER.info(f"  - Cold Start Fuel Table")
    LOGGER.info(f"  - Input/Output capabilities")
    LOGGER.info(f"  - Pro Analysis and Telemetry")
    LOGGER.info(f"  - Variable Cam Timing (CAM Control)")
    LOGGER.info(f"  - Servo Motor Control")


if __name__ == "__main__":
    main()

