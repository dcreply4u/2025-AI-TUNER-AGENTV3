#!/usr/bin/env python3
"""
Add comprehensive drag racing data logging concepts and techniques to knowledge base.
Covers all essential parameters, analysis techniques, and best practices.
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

# Comprehensive drag racing data logging knowledge
DRAG_LOGGING_KNOWLEDGE = [
    {
        "question": "What are the core parameters to log in drag racing data acquisition?",
        "answer": """Core parameters for drag racing data logging include essential engine and vehicle data:

**Engine Parameters:**
- Engine RPM - Critical for shift points and power band analysis
- Coolant temperature - Engine health and cooling system performance
- Air temperature (IAT) - Air density and power calculations
- Throttle position - Driver input and power delivery
- Vehicle speed - Overall performance metric

**Individual Cylinder Monitoring:**
- Exhaust gas temperature (EGT) per cylinder
- Wideband oxygen sensor per cylinder
- Cylinder pressure (if equipped)
- Spark plug condition correlation with data

**Critical Performance Metrics:**
- Driveshaft speed - Essential for understanding power delivery and transmission performance
- Torque converter line pressure (automatic transmissions) - Analyzes torque converter function
- Clutch speed (manual transmissions) - Analyzes clutch engagement and performance
- Fuel pressure - Ensures adequate fuel delivery
- Oil pressure - Engine health indicator

**Chassis and Suspension:**
- Shock travel (shock pots) - Measures suspension movement and weight transfer
- G-forces (G-meters) - Longitudinal and lateral forces during launch and braking
- Wheel speed sensors - Individual wheel speed for traction analysis

**Driver Inputs:**
- Steering angle - Driver technique and car control
- Brake pressure - Braking technique and consistency
- Gear selection - Shift timing and technique
- Launch RPM - Starting line technique

These core parameters provide the foundation for comprehensive data analysis and performance optimization.""",
        "keywords": ["data logging", "core parameters", "RPM", "temperature", "throttle", "driveshaft", "sensors"],
        "topic": "Drag Racing Data Logging - Core Parameters"
    },
    {
        "question": "Why is driveshaft speed critical in drag racing data logging?",
        "answer": """Driveshaft speed is one of the most critical parameters in drag racing data logging because:

**Power Delivery Analysis:**
- Driveshaft speed directly reflects power being delivered to the rear wheels
- Shows how effectively the engine power is being transferred through the drivetrain
- Reveals power delivery characteristics throughout the run

**Transmission Performance:**
- Analyzes transmission function and efficiency
- Identifies slippage or inefficiencies in the drivetrain
- Helps optimize transmission tuning

**Overall Performance Understanding:**
- Provides insight into the complete power delivery chain from engine to wheels
- Can reveal issues that might not be apparent from engine RPM alone
- Essential for understanding the relationship between engine output and vehicle acceleration

**Comparison Tool:**
- Allows comparison between runs to see if power delivery is consistent
- Helps identify when drivetrain components are wearing or failing
- Critical for diagnosing drivetrain-related performance issues

Driveshaft speed data, when combined with engine RPM, vehicle speed, and other parameters, provides a complete picture of how power flows through the entire vehicle system.""",
        "keywords": ["driveshaft speed", "power delivery", "transmission", "drivetrain", "performance analysis"],
        "topic": "Drag Racing Data Logging - Driveshaft Analysis"
    },
    {
        "question": "What transmission-specific data should be logged for automatic vs manual transmissions?",
        "answer": """Transmission-specific data logging differs between automatic and manual transmissions:

**Automatic Transmissions:**
- **Torque Converter Line Pressure** - Critical for understanding torque converter function
  * Shows converter lockup characteristics
  * Reveals converter efficiency and slippage
  * Helps optimize converter selection and tuning
  * Indicates when converter is working properly vs slipping excessively

- **Transmission Line Pressure** - Overall transmission health
- **Converter Slip RPM** - Difference between engine RPM and transmission input RPM
- **Shift Solenoid Data** - Shift timing and quality
- **Transmission Temperature** - Prevents overheating and damage

**Manual Transmissions:**
- **Clutch Speed** - Analyzes clutch engagement and performance
  * Shows clutch slip during engagement
  * Reveals clutch release characteristics
  * Helps optimize clutch tuning and selection
  * Identifies when clutch is wearing or needs adjustment

- **Clutch Pedal Position** - Driver technique and engagement timing
- **Gear Selection** - Shift timing and gear choice
- **Transmission Temperature** - Clutch and gear health

**Both Transmission Types:**
- Shift points (RPM and vehicle speed)
- Shift duration/time
- Power interruption during shifts
- Post-shift recovery (RPM and acceleration)

This transmission-specific data is essential for optimizing shift points, improving shift quality, and diagnosing transmission-related performance issues.""",
        "keywords": ["automatic transmission", "manual transmission", "torque converter", "clutch speed", "transmission pressure", "shift points"],
        "topic": "Drag Racing Data Logging - Transmission Data"
    },
    {
        "question": "How do you use chassis and suspension data logging in drag racing?",
        "answer": """Chassis and suspension data logging uses specialized sensors to measure suspension movement and forces:

**Shock Pots (Shock Travel Sensors):**
- Measure suspension travel and movement
- Show weight transfer during launch
- Reveal suspension behavior under acceleration and braking
- Help optimize shock tuning and spring rates
- Identify suspension binding or bottoming out
- Critical for understanding how the chassis is working

**G-Meters (Accelerometers):**
- Measure longitudinal G-forces (acceleration and deceleration)
- Measure lateral G-forces (side-to-side movement)
- Show launch characteristics and traction
- Reveal braking forces and efficiency
- Help analyze weight transfer patterns

**Chassis Tuning Applications:**
- Optimize launch characteristics by analyzing weight transfer
- Fine-tune shock settings based on actual travel data
- Identify suspension issues that affect traction
- Optimize chassis setup for different track conditions
- Improve consistency by understanding suspension behavior

**Data Analysis:**
- Compare shock travel between runs to ensure consistency
- Analyze G-forces to understand traction and braking
- Use data to make informed chassis adjustments
- Identify when suspension components need attention

Chassis and suspension data, combined with engine and drivetrain data, provides a complete picture of vehicle performance and helps optimize the entire package.""",
        "keywords": ["shock pots", "G-meters", "suspension", "chassis tuning", "weight transfer", "traction"],
        "topic": "Drag Racing Data Logging - Chassis and Suspension"
    },
    {
        "question": "How do you use air/fuel ratio data to optimize shift points?",
        "answer": """Air/fuel ratio (AFR) data is critical for optimizing shift points in drag racing:

**Shift Point Optimization Process:**
1. Log AFR throughout the entire run, especially during and after shifts
2. Analyze AFR at different RPM points in each gear
3. Identify the RPM where AFR is optimal (typically 12.5:1 to 13.2:1 for naturally aspirated, 11.5:1 to 12.5:1 for forced induction)
4. Set shift points to occur when AFR is in the optimal range

**Key Analysis Points:**
- **Pre-Shift AFR** - Ensure engine is in optimal AFR range before shifting
- **Post-Shift AFR** - Verify AFR recovers quickly after shift
- **AFR Recovery Time** - Time it takes for AFR to stabilize after shift
- **AFR Consistency** - Ensure AFR is consistent across multiple runs

**Optimization Benefits:**
- Shifts occur when engine is making optimal power
- Prevents shifting when AFR is too lean (power loss) or too rich (power loss)
- Ensures fuel delivery is adequate for the power being made
- Helps maintain consistent power delivery throughout the run

**Integration with Other Data:**
- Combine AFR with engine RPM to find optimal shift RPM
- Use AFR with driveshaft speed to understand power delivery
- Correlate AFR with vehicle speed to optimize overall performance

**Safety Considerations:**
- AFR that goes too lean can cause engine damage
- AFR that stays too rich wastes fuel and power
- Proper AFR at shift points protects the engine and maximizes performance

By analyzing AFR data, you can fine-tune shift points to occur at the exact RPM where the engine is making optimal power with proper fuel delivery.""",
        "keywords": ["air fuel ratio", "AFR", "shift points", "optimization", "fuel delivery", "power"],
        "topic": "Drag Racing Data Logging - Shift Optimization"
    },
    {
        "question": "What is speed trace analysis and how do you interpret it?",
        "answer": """Speed trace analysis examines the speed-versus-distance graph to identify areas where time is being lost:

**Understanding the Speed Trace:**
- **Speed Trace Graph** - Plots vehicle speed against distance down the track
- Shows acceleration characteristics throughout the run
- Reveals where the car is gaining or losing speed
- Identifies inefficiencies in acceleration and braking

**Desirable Patterns:**
- **"Sawtooth" Pattern During Acceleration** - Indicates good traction and power delivery
  * Sharp increases in speed (acceleration)
  * Brief plateaus or slight decreases (shifts or traction events)
  * Overall upward trend showing consistent acceleration

- **"Sawtooth" Pattern During Braking** - Shows effective braking technique
  * Sharp decreases in speed (braking)
  * Brief plateaus (coasting or weight transfer)
  * Controlled deceleration

**Problem Patterns:**
- **Curves Instead of Sawtooth** - Can indicate:
  * Rolling out of the throttle early
  * Gradual acceleration instead of aggressive acceleration
  * Inefficient power delivery
  * Driver technique issues

- **Flat Spots** - Indicate:
  * Time lost during shifts
  * Traction loss
  * Power delivery issues
  * Driver hesitation

**Analysis Techniques:**
1. Compare speed traces between runs to identify inconsistencies
2. Look for areas where speed increase slows down
3. Identify where time is being lost (early braking, slow acceleration)
4. Use trace to optimize shift points and driving technique
5. Correlate with other data (RPM, AFR, G-forces) to understand causes

**Optimization Applications:**
- Identify where to improve acceleration
- Optimize braking points
- Improve shift timing
- Enhance driver technique
- Diagnose performance issues

Speed trace analysis is one of the most powerful tools for identifying where time is being lost and how to improve overall performance.""",
        "keywords": ["speed trace", "speed vs distance", "acceleration", "braking", "performance analysis", "driver technique"],
        "topic": "Drag Racing Data Logging - Speed Trace Analysis"
    },
    {
        "question": "How do you analyze driver technique using data logs?",
        "answer": """Driver technique analysis uses data logs to identify and correct driver habits:

**Key Driver Inputs to Log:**
- **Steering Angle** - Shows car control and steering corrections
- **Brake Pressure** - Reveals braking technique and consistency
- **Throttle Position** - Shows throttle application and modulation
- **Gear Selection** - Indicates shift timing and gear choice
- **Launch RPM** - Starting line technique

**Common Driver Issues Identified:**
- **Double Braking** - Applying brakes multiple times instead of one smooth application
  * Shows up as multiple brake pressure spikes in the data
  * Wastes time and can cause inconsistency

- **Coasting** - Letting off throttle before necessary
  * Shows as throttle position dropping when it should stay at 100%
  * Speed trace shows gradual deceleration instead of maintained speed
  * Wastes significant time

- **Early Braking** - Beginning to brake too early
  * Speed trace shows deceleration starting before optimal point
  * Can be identified by comparing to optimal braking point data

- **Inconsistent Launch** - Varying launch technique
  * Launch RPM varies between runs
  * Throttle application timing differs
  * Results in inconsistent 60-foot times

**Analysis Process:**
1. Compare driver inputs between runs to identify inconsistencies
2. Correlate driver inputs with performance results
3. Identify patterns that correlate with good vs poor runs
4. Use data to provide specific feedback to driver
5. Track improvement over time

**Improvement Techniques:**
- Use data to show driver exactly what they're doing wrong
- Provide visual feedback (graphs) that drivers can understand
- Set targets based on data from best runs
- Practice with data logging to develop muscle memory
- Use data to build consistency

**Consistency Analysis:**
- Compare multiple runs to identify driver consistency
- Identify which inputs vary the most
- Focus improvement efforts on most variable inputs
- Track consistency metrics over time

By analyzing driver technique with data logs, you can identify specific habits that are costing time and provide targeted feedback to improve performance.""",
        "keywords": ["driver technique", "braking", "throttle", "steering", "consistency", "driver inputs"],
        "topic": "Drag Racing Data Logging - Driver Analysis"
    },
    {
        "question": "How do you use data logging for product development and quantifying changes?",
        "answer": """Data logging is essential for product development and quantifying the results of vehicle setup changes:

**Quantifying Changes:**
- **Before and After Comparison** - Log data before making a change, then after
- **Measurable Results** - Use data to confirm changes are yielding desired performance gains
- **Objective Analysis** - Remove guesswork and subjective opinions
- **Statistical Validation** - Multiple runs provide statistical confidence in results

**Product Development Process:**
1. Establish baseline with comprehensive data logging
2. Make one change at a time (isolate variables)
3. Log multiple runs with the change
4. Compare data to baseline
5. Quantify the improvement (or lack thereof)
6. Document results for future reference

**Key Metrics for Quantification:**
- **Elapsed Time (ET)** - Overall performance improvement
- **Trap Speed** - Power and efficiency gains
- **60-Foot Time** - Launch and traction improvements
- **Incremental Times** - 330, 660, 1000 foot times show where improvements occurred
- **Power Delivery** - Driveshaft speed, RPM curves
- **Consistency** - Standard deviation of times

**Applications:**
- **Component Testing** - Test different parts (converters, gears, shocks) and quantify results
- **Tuning Changes** - Measure impact of tuning adjustments
- **Setup Optimization** - Quantify effects of chassis and suspension changes
- **Driver Development** - Measure improvement from driver training

**Data Visualization:**
- Plot data as graphs and charts to make trends and patterns apparent
- Overlay multiple runs to see differences clearly
- Use color coding to identify different configurations
- Create comparison charts showing before/after results

**Overcoming Information Overload:**
- Focus on most critical metrics for the specific change being tested
- Don't try to analyze everything at once
- Use data analysis to identify which metrics matter most
- Build a library of successful changes and their quantified results

**Best Practices:**
- Always log baseline data before making changes
- Make one change at a time to isolate effects
- Log multiple runs to account for track and weather variations
- Document all changes and their quantified results
- Build a knowledge base of what works and what doesn't

By using data logging to quantify changes, you can make informed decisions about what modifications actually improve performance and avoid wasting time and money on changes that don't work.""",
        "keywords": ["product development", "quantifying changes", "before after", "baseline", "performance gains", "data visualization"],
        "topic": "Drag Racing Data Logging - Product Development"
    },
    {
        "question": "How do you use failsafes with a standalone ECU and data logging?",
        "answer": """Failsafes with standalone ECUs use data logs to help protect the engine and drivetrain:

**Failsafe Types:**
- **Oil Pressure Failsafe** - Kills engine or pulls timing if oil pressure drops below threshold
- **Fuel Pressure Failsafe** - Protects engine if fuel pressure drops (indicates pump failure)
- **Air/Fuel Ratio Failsafe** - Pulls timing or adds fuel if AFR goes too lean
- **Coolant Temperature Failsafe** - Protects engine from overheating
- **RPM Limiter** - Prevents over-revving the engine
- **Boost/Vacuum Failsafe** - Protects from over-boost or vacuum issues

**Data Logging Integration:**
- **Log Failsafe Events** - Record when and why failsafes activate
- **Pre-Failsafe Data** - Log data leading up to failsafe activation to diagnose issues
- **Post-Failsafe Analysis** - Review data to understand what caused the failsafe
- **Trend Analysis** - Use data to identify trends that might lead to failsafe activation

**Setting Up Failsafes:**
1. Log baseline data to understand normal operating parameters
2. Identify safe operating ranges for each parameter
3. Set failsafe thresholds based on data (not guesswork)
4. Test failsafes in controlled conditions
5. Log failsafe activations to refine thresholds

**Using Data to Refine Failsafes:**
- Analyze data to determine optimal failsafe thresholds
- Identify false alarms (failsafes activating when they shouldn't)
- Adjust thresholds based on actual data from runs
- Use data to understand what conditions trigger failsafes

**Protection Benefits:**
- Prevents catastrophic engine failure
- Saves expensive components
- Provides early warning of problems
- Allows proactive maintenance

**Data Analysis for Failsafes:**
- Review logs after each run to check for near-failsafe conditions
- Identify trends that might indicate impending problems
- Use data to schedule preventive maintenance
- Correlate failsafe events with other data to diagnose root causes

**Best Practices:**
- Set failsafes conservatively at first, then refine based on data
- Log all failsafe events with full context
- Review failsafe data regularly to identify patterns
- Use data to optimize failsafe thresholds for maximum protection without false alarms
- Document failsafe settings and their rationale

By combining failsafes with comprehensive data logging, you can protect your engine while also learning from the data to prevent future issues.""",
        "keywords": ["failsafes", "ECU", "engine protection", "safety", "oil pressure", "fuel pressure", "AFR"],
        "topic": "Drag Racing Data Logging - Failsafes and Safety"
    }
]


def main():
    """Add comprehensive drag racing data logging knowledge."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in DRAG_LOGGING_KNOWLEDGE:
        try:
            LOGGER.info(f"Adding: {entry['question'][:60]}...")
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{entry['question']}\n\n{entry['answer']}",
                metadata={
                    "question": entry["question"],
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": "comprehensive_drag_logging_knowledge",
                    "category": "Drag Racing Data Logging"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                source="comprehensive_drag_logging_knowledge",
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
    LOGGER.info(f"Total entries: {len(DRAG_LOGGING_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nComprehensive drag racing data logging knowledge has been added!")
    LOGGER.info(f"The AI Chat Advisor can now answer detailed questions about:")
    LOGGER.info(f"  - Core logging parameters")
    LOGGER.info(f"  - Driveshaft speed analysis")
    LOGGER.info(f"  - Transmission-specific data")
    LOGGER.info(f"  - Chassis and suspension logging")
    LOGGER.info(f"  - Shift point optimization")
    LOGGER.info(f"  - Speed trace analysis")
    LOGGER.info(f"  - Driver technique analysis")
    LOGGER.info(f"  - Product development and quantification")
    LOGGER.info(f"  - Failsafes and ECU protection")


if __name__ == "__main__":
    main()

