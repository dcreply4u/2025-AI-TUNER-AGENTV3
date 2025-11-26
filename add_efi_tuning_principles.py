#!/usr/bin/env python3
"""
Add EFI Tuning Principles and Best Practices to the AI Chat Advisor knowledge base.
Extracted from general tuning guide - excludes product-specific information.
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

# EFI Tuning Principles and Best Practices
EFI_TUNING_KNOWLEDGE = [
    {
        "question": "What are the fundamental parameters for tuning an EFI system?",
        "answer": """The most fundamental parameters for tuning an EFI system are:

**Core Tuning Tables:**
- **Volumetric Efficiency (VE) Table:** 12×12 table that determines how much fuel to inject based on engine load (MAP) and RPM
- **Air/Fuel Ratio (AFR) Table:** 12×12 table that sets target air/fuel ratios across different load and RPM conditions
- **Spark Advance Table:** 12×12 table that controls ignition timing based on load and RPM

**Supporting Parameters:**
- **Cold Start Pulse Widths:** Fuel enrichment for starting at different temperatures
- **Acceleration Enrichment:** Additional fuel during throttle opening
- **Warm-Up Enrichment:** Fuel compensation during engine warm-up
- **Idle Control:** Idle speed and fuel delivery at idle

**Tuning Order:**
1. Tune VE table first (base fuel delivery)
2. Tune AFR table (target air/fuel ratios)
3. Tune spark advance table (ignition timing)
4. Tune acceleration enrichment (after base tables are set)
5. Fine-tune cold start and warm-up

**Key Principle:**
These tables work together to control fuel delivery, air/fuel ratio, and ignition timing across all engine operating conditions. Proper tuning requires systematic adjustment of each parameter in the correct order.

**Bottom Line:**
The fundamental tuning parameters are the VE table (fuel), AFR table (air/fuel ratio), and spark advance table (timing), with supporting parameters for special conditions like cold start and acceleration.""",
        "keywords": ["EFI tuning", "VE table", "AFR table", "spark advance", "tuning parameters", "fuel injection tuning"],
        "topic": "EFI Tuning - Fundamentals"
    },
    {
        "question": "What are the best practices and safety procedures for EFI tuning?",
        "answer": """Proper safety procedures and best practices are essential for safe and effective EFI tuning:

**Safety Procedures:**
- **Fire Extinguishers:** Have two fully charged fire extinguishers on hand
- **Fuel System Inspection:** Check entire fuel system (tank to injectors and back) for leaks while running fuel pump
- **NO LEAKS POLICY:** DO NOT attempt to start engine if there are ANY leaks whatsoever - fix all leaks before proceeding
- **Fuel Pressure Check:** Verify fuel pressure is appropriate (usually 42-45 PSI for port injection, 12-15 PSI for throttle body systems)
- **Power Supply:** Ensure ECU is powered from +12V source that supplies current while cranking (not just in 'run' position)

**Tuning Best Practices:**
- **One Change at a Time:** Do not change more than one thing at a time
- **Always Have Backup:** Always be able to get back to where you started
- **Fix Idle First:** Do not try to drive the car if you cannot get it to idle properly - fix the idle first
- **Proper Tuning Order:** Do not try to tune acceleration enrichment before you have tuned the VE, AFR, and spark tables
- **Documentation:** When reporting problems, supply details (datalogs, configuration files, processor and code version) - do not just say "it does not work"

**Pre-Start Checks:**
- Verify all sensors give reasonable values (MAP ~100 kPa, temperatures match ambient, TPS reads 0-100%)
- Check fuel system for leaks
- Verify fuel pressure
- Confirm power supply works during cranking
- Verify ignition settings are correct

**Bottom Line:**
Safety first - check for leaks, verify fuel pressure, ensure proper power supply. Then tune systematically, one parameter at a time, with proper backups and documentation.""",
        "keywords": ["EFI tuning safety", "tuning best practices", "fuel system safety", "tuning procedures", "EFI safety"],
        "topic": "EFI Tuning - Safety"
    },
    {
        "question": "How do you tune the volumetric efficiency (VE) table?",
        "answer": """The VE table is the foundation of EFI tuning and determines base fuel delivery.

**What the VE Table Does:**
- Controls how much fuel is injected based on engine load (MAP) and RPM
- Typically a 12×12 table with MAP on one axis and RPM on the other
- Values represent volumetric efficiency percentage (how efficiently engine fills cylinders)

**Tuning Process:**
1. **Start with Idle:** Get engine idling properly first
2. **Steady State Tuning:** Tune at steady RPM and load conditions
3. **Use Wideband O2 Sensor:** Monitor actual air/fuel ratio while tuning
4. **Adjust Values:** Increase VE values if too lean, decrease if too rich
5. **Work Systematically:** Tune one cell at a time, moving through the table methodically

**Tuning Strategy:**
- **Idle Region:** Start with idle MAP and RPM, adjust until AFR is correct
- **Cruise Region:** Tune light load, mid-RPM conditions for fuel economy
- **WOT Region:** Tune high load, high RPM for maximum power
- **Transitions:** Smooth transitions between cells prevent hesitation

**Important Considerations:**
- **MAP Bins:** May want to use lower MAP value than actual idle vacuum for street use (allows leaner cruise and decel)
- **RPM Bins:** Ensure RPM bins cover your operating range
- **Smooth Transitions:** Avoid large jumps between adjacent cells
- **Load Conditions:** Tune under actual load conditions when possible

**Common Techniques:**
- Use lower MAP bin than idle vacuum to run leaner on overrun deceleration
- Increase VE values just above and to left of idle to prevent stalling
- Make transitions rich (double idle VE) to prevent stumbling
- Work with RPM and MAP bins to run lean at cruise but rich when stalling

**Bottom Line:**
Tune the VE table systematically, starting with idle, then cruise, then WOT. Use wideband O2 sensor feedback and adjust values to achieve target AFR at each load/RPM point.""",
        "keywords": ["VE table", "volumetric efficiency", "fuel map tuning", "VE tuning", "fuel delivery"],
        "topic": "EFI Tuning - VE Table"
    },
    {
        "question": "How do you tune the air/fuel ratio (AFR) table?",
        "answer": """The AFR table sets target air/fuel ratios across different engine operating conditions.

**What the AFR Table Does:**
- Sets target air/fuel ratios based on engine load (MAP) and RPM
- Typically a 12×12 table matching the VE table structure
- Works with VE table to achieve desired air/fuel ratios

**Target AFR Values:**
- **Idle:** Typically 13.5-14.5:1 (slightly rich for stability)
- **Cruise:** 14.5-15.5:1 (leaner for fuel economy)
- **WOT (Wide Open Throttle):** 12.0-13.0:1 (richer for power and safety)
- **Boost:** 11.0-12.0:1 (richer to prevent detonation)

**Tuning Process:**
1. **Set Target Values:** Enter desired AFR for each load/RPM condition
2. **Monitor Actual AFR:** Use wideband O2 sensor to see actual air/fuel ratio
3. **Adjust VE Table:** Fine-tune VE table to achieve target AFR
4. **Verify Under Load:** Check AFR under actual driving conditions

**Tuning Strategy:**
- **Idle:** Set for smooth, stable idle (typically 13.5-14.5:1)
- **Cruise:** Set leaner for fuel economy (14.5-15.5:1)
- **WOT:** Set richer for power and safety (12.0-13.0:1)
- **Boost:** Set even richer to prevent detonation (11.0-12.0:1)

**Important Considerations:**
- **VE Table Interaction:** AFR table sets targets, VE table delivers fuel to meet targets
- **Wideband O2 Sensor:** Essential for accurate AFR monitoring
- **Load Conditions:** Tune under actual load, not just static conditions
- **Safety Margins:** Keep WOT and boost AFRs rich enough to prevent detonation

**Open Loop vs. Closed Loop:**
- **Closed Loop:** O2 sensor feedback adjusts fuel delivery (set O2 step to non-zero)
- **Open Loop:** No O2 sensor feedback (set O2 step to 0)
- **Best Practice:** Use closed loop for cruise, open loop for WOT and boost

**Bottom Line:**
Set target AFR values in the AFR table based on operating conditions (leaner for cruise, richer for WOT/boost), then adjust VE table to achieve those targets.""",
        "keywords": ["AFR table", "air fuel ratio", "target AFR", "AFR tuning", "stoichiometric"],
        "topic": "EFI Tuning - AFR Table"
    },
    {
        "question": "How do you tune ignition timing (spark advance)?",
        "answer": """The spark advance table controls ignition timing based on engine load and RPM.

**What the Spark Advance Table Does:**
- Sets ignition timing advance based on engine load (MAP) and RPM
- Typically a 12×12 table matching VE and AFR table structure
- Controls when spark plug fires relative to piston position

**Timing Principles:**
- **Low Load, Low RPM:** More advance (better efficiency)
- **High Load, High RPM:** Less advance (prevent detonation)
- **Boost:** Less advance (prevent detonation under pressure)
- **Idle:** Moderate advance for stability

**Tuning Process:**
1. **Set Base Timing:** Verify and set base timing before tuning
2. **Enter Base Timing:** Enter base timing value into advance offset field
3. **Start Conservative:** Begin with conservative timing values
4. **Gradually Increase:** Add timing gradually while monitoring for knock
5. **Verify with Timing Light:** Compare indicated timing to actual timing with timing light
6. **Test at Multiple RPMs:** Verify timing at idle, 1500, 2000, 3000 RPM

**Timing Verification:**
- **Timing Light:** Use timing light to verify actual timing matches indicated timing
- **Multiple RPMs:** Check at idle, ~1500 RPM, ~2000 RPM, ~3000 RPM
- **Consistency:** Timing should match across wide RPM range
- **If Mismatch:** Either input capture or spark output setting is incorrect

**Timing Strategy:**
- **Idle:** Moderate advance for smooth idle
- **Cruise:** More advance for fuel economy
- **WOT:** Less advance to prevent detonation
- **Boost:** Even less advance under boost pressure

**Important Considerations:**
- **Base Timing:** Must be set correctly before tuning advance table
- **Trigger Offset:** Must be calibrated correctly for accurate timing
- **Input Capture:** Must be set correctly for your ignition system
- **Spark Output:** Must be set correctly for your ignition module
- **Knock Monitoring:** Always monitor for detonation when advancing timing

**Safety:**
- **Conservative Start:** Begin with conservative timing
- **Gradual Changes:** Make small changes and test
- **Knock Detection:** Stop advancing if knock is detected
- **Safety Margin:** Leave safety margin, don't push to absolute limit

**Bottom Line:**
Tune spark advance table starting with base timing, then gradually increase advance while monitoring for knock. Verify timing with timing light at multiple RPMs to ensure accuracy.""",
        "keywords": ["spark advance", "ignition timing", "timing table", "spark timing", "timing advance"],
        "topic": "EFI Tuning - Ignition Timing"
    },
    {
        "question": "How do you tune cold start and warm-up enrichment?",
        "answer": """Cold start and warm-up enrichment provide additional fuel when the engine is cold.

**Cold Start Enrichment:**
- **Purpose:** Provides extra fuel for starting at different temperatures
- **Temperature-Based:** Different pulse widths for different coolant temperatures
- **Cranking Pulse Widths:** Fuel delivered during engine cranking
- **Prime Pulse:** Small initial fuel squirt when ECU is powered (NOT meant for starting fuel)

**Tuning Cold Start:**
- **Start Conservative:** Begin with moderate cranking pulse widths
- **Temperature Ranges:** Tune for different temperature ranges (-40°F to operating temperature)
- **Typical Process:** Start engine, adjust cranking pulse widths until it starts reliably
- **Prime Pulse:** Keep as short as possible (typically ~2.0 milliseconds), tune starting with cranking pulses

**Warm-Up Enrichment:**
- **Purpose:** Provides extra fuel as engine warms up
- **Temperature-Based:** Enrichment decreases as temperature increases
- **Range:** Typically goes up to 160°F
- **Above 160°F:** Uses 160°F bin value (should be 100% = no enrichment) at all higher temperatures

**Tuning Warm-Up:**
- **Start Rich:** Begin with higher enrichment values
- **Gradually Reduce:** Reduce enrichment as you tune
- **Target:** 100% (no enrichment) at 160°F and above
- **Smooth Transition:** Ensure smooth transition from cold to warm

**Important Considerations:**
- **Cranking vs. Prime:** Cranking pulse widths provide starting fuel, prime pulse is just initial squirt
- **Temperature Compensation:** Enrichment must decrease smoothly as engine warms
- **Starting Issues:** If engine won't start, check cranking pulse widths, not prime pulse
- **Warm-Up Behavior:** Engine should run smoothly as it warms, without stumbling

**Common Issues:**
- **Too Rich:** Engine floods, won't start
- **Too Lean:** Engine won't start or starts then dies
- **Rough Warm-Up:** Enrichment dropping too quickly or too slowly

**Bottom Line:**
Tune cold start with cranking pulse widths for different temperatures. Tune warm-up enrichment to provide smooth transition from cold to operating temperature, reaching 100% (no enrichment) at 160°F.""",
        "keywords": ["cold start", "warm-up enrichment", "cranking pulse width", "prime pulse", "cold start tuning"],
        "topic": "EFI Tuning - Cold Start"
    },
    {
        "question": "How do you tune acceleration enrichment?",
        "answer": """Acceleration enrichment provides additional fuel when the throttle is opened quickly.

**What Acceleration Enrichment Does:**
- **Purpose:** Prevents lean condition when throttle opens quickly
- **Trigger:** Activated by rapid throttle position (TPS) or manifold pressure (MAP) changes
- **Duration:** Provides extra fuel for short duration during acceleration
- **Prevents Hesitation:** Keeps engine from stumbling during throttle opening

**Tuning Process:**
1. **Tune Base Tables First:** Must have VE, AFR, and spark tables tuned before tuning acceleration
2. **Start Conservative:** Begin with moderate acceleration enrichment
3. **Test Under Load:** Test acceleration under actual driving conditions
4. **Adjust Based on Feel:** Increase if hesitation, decrease if too rich/bogging
5. **Monitor AFR:** Use wideband O2 sensor to see if enrichment is appropriate

**Acceleration Enrichment Types:**
- **TPS-Based:** Triggered by throttle position sensor rate of change
- **MAP-Based:** Triggered by manifold pressure rate of change
- **Combined:** Can use both TPS and MAP acceleration enrichment

**Tuning Strategy:**
- **Too Little:** Engine hesitates or stumbles when throttle opens
- **Too Much:** Engine bogs down or runs too rich during acceleration
- **Just Right:** Smooth, responsive acceleration without hesitation or bogging

**Important Considerations:**
- **Timing:** Only tune acceleration enrichment AFTER base tables are set
- **Load Conditions:** Test under actual driving conditions, not just static
- **AFR Monitoring:** Monitor air/fuel ratio during acceleration events
- **Smooth Response:** Goal is smooth, responsive acceleration

**Common Issues:**
- **Hesitation:** Not enough enrichment - increase values
- **Bogging:** Too much enrichment - decrease values
- **Inconsistent:** May need to adjust trigger thresholds

**Bottom Line:**
Tune acceleration enrichment only after base tables are set. Start conservative and adjust based on actual driving feel and AFR monitoring. Goal is smooth, responsive acceleration without hesitation or bogging.""",
        "keywords": ["acceleration enrichment", "TPS acceleration", "MAP acceleration", "throttle enrichment", "acceleration tuning"],
        "topic": "EFI Tuning - Acceleration"
    },
    {
        "question": "How do you tune idle on an EFI system?",
        "answer": """Idle tuning is critical and must be done before attempting to drive the vehicle.

**Idle Tuning Principles:**
- **Fix Idle First:** Do not try to drive the car if you cannot get it to idle properly
- **Steady State:** Engine must idle smoothly and consistently
- **Target AFR:** Typically 13.5-14.5:1 for stable idle
- **Idle Speed:** Set appropriate idle speed for your application

**Idle Tuning Process:**
1. **Get Engine Started:** Use cranking pulse widths to get engine started
2. **Let Engine Warm:** Allow engine to reach operating temperature
3. **Adjust VE Table:** Tune VE values at idle MAP and RPM
4. **Adjust Timing:** Fine-tune spark advance at idle for smoothness
5. **Adjust Idle Speed:** Use idle control to set desired idle speed
6. **Verify Stability:** Engine should idle smoothly without surging or stalling

**Idle Control Methods:**
- **Idle Solenoid:** Bypass air around throttle plates
- **Timing-Based:** Adjust timing to control idle speed
- **Throttle Position:** Set throttle plates for baseline idle speed

**Important Considerations:**
- **MAP Value:** Engine idles at certain vacuum - use this for VE table tuning
- **Lower MAP Bin:** For street use, may want to use lower MAP bin than idle vacuum (allows leaner cruise/decel)
- **VE Values Above Idle:** Can increase VE values just above and to left of idle to prevent stalling
- **Rich Transition:** Make transitions rich (double idle VE) to keep engine from stalling if it starts to stumble

**Idle Stability:**
- **Smooth Idle:** Engine should idle smoothly without surging
- **No Stalling:** Engine should not stall when returning to idle
- **Consistent Speed:** Idle speed should be consistent
- **Quick Recovery:** Engine should return to idle quickly after throttle blip

**Common Issues:**
- **Surging:** Usually too lean or timing too advanced
- **Stalling:** Usually too lean or not enough fuel
- **Rough Idle:** May need to adjust VE, timing, or idle speed
- **High Idle:** Idle control may need adjustment

**Bottom Line:**
Tune idle first before attempting to drive. Adjust VE table at idle MAP/RPM, fine-tune timing, and set idle speed. Engine must idle smoothly and consistently before proceeding with other tuning.""",
        "keywords": ["idle tuning", "idle control", "idle speed", "idle AFR", "idle stability"],
        "topic": "EFI Tuning - Idle"
    },
    {
        "question": "How do you use datalogging for EFI tuning?",
        "answer": """Datalogging is essential for effective EFI tuning and problem diagnosis.

**What Datalogging Does:**
- **Records Data:** Creates running record of real-time engine variables
- **File Format:** Typically comma-separated value (CSV) format
- **Time-Based:** Records data over time as engine runs
- **Analysis Tool:** Allows review of engine behavior after the fact

**What to Log:**
- **Engine Parameters:** RPM, MAP, TPS, coolant temp, air temp
- **Fuel Parameters:** Injector pulse width, fuel pressure, AFR
- **Ignition Parameters:** Spark advance, dwell time
- **Sensor Data:** All sensor readings
- **Calculated Values:** Derived parameters like load, efficiency

**Using Datalogging:**
1. **Enable Logging:** Start datalogging before driving/testing
2. **Drive/Test:** Perform driving or dyno testing
3. **Review Logs:** Analyze logged data to identify issues
4. **Make Adjustments:** Adjust tuning based on logged data
5. **Re-Test:** Test again and compare logs

**Data Analysis:**
- **Graph View:** View data in graphical format for easier analysis
- **Overlay Graphs:** Compare multiple parameters simultaneously
- **Zoom:** Zoom in on specific time periods or RPM ranges
- **Calculated Fields:** Calculate derived values (RPM/sec, vacuum, etc.)

**Engine Status Bits:**
Datalogs often include engine status bits that indicate engine state:
- **Running:** Engine is running (bit 1)
- **Cranking:** Engine is cranking (bit 2)
- **Start-Up Enrichment:** Start-up enrichment active (bit 4)
- **Warm-Up Enrichment:** Warm-up enrichment active (bit 8)
- **TPS Acceleration:** TPS acceleration enrichment active (bit 16)
- **Decel Enlean:** Deceleration enleanment active (bit 32)
- **MAP Acceleration:** MAP acceleration enrichment active (bit 64)

**Important Considerations:**
- **O2 Sensor Data:** Only use narrow band O2 sensor data when engine bit = 1 (running, no enrichments)
- **Filter Data:** Filter out unsuitable data (acceleration, warm-up, etc.) when analyzing
- **Steady State:** Use steady-state data for VE/AFR table tuning
- **Transient Data:** Use transient data for acceleration enrichment tuning

**Best Practices:**
- **Log Everything:** Log all available parameters
- **Long Logs:** Take longer logs to see patterns
- **Multiple Conditions:** Log idle, cruise, WOT, acceleration, deceleration
- **Compare Logs:** Compare before/after tuning changes
- **Document:** Save logs with notes about what was being tested

**Bottom Line:**
Datalogging is essential for effective tuning. Record data during testing, then analyze to identify issues and verify tuning changes. Use engine status bits to filter data appropriately.""",
        "keywords": ["datalogging", "data logging", "tuning logs", "EFI logging", "tuning analysis"],
        "topic": "EFI Tuning - Datalogging"
    },
    {
        "question": "What are common EFI tuning mistakes and how to avoid them?",
        "answer": """Common EFI tuning mistakes can lead to poor performance, engine damage, or tuning frustration.

**Tuning Order Mistakes:**
- **Tuning Acceleration Before Base Tables:** Must tune VE, AFR, and spark tables first
- **Trying to Drive with Bad Idle:** Fix idle before attempting to drive
- **Changing Multiple Things at Once:** Change one parameter at a time

**Safety Mistakes:**
- **Ignoring Fuel Leaks:** Starting engine with fuel leaks is extremely dangerous
- **Wrong Fuel Pressure:** Not verifying fuel pressure before starting
- **Power Supply Issues:** Using power source that doesn't work during cranking
- **No Fire Extinguishers:** Not having safety equipment on hand

**Tuning Mistakes:**
- **Too Aggressive Changes:** Making large changes instead of small, incremental adjustments
- **No Backup:** Not being able to return to previous working state
- **Ignoring Sensors:** Not verifying sensors read correctly before tuning
- **Wrong Timing Base:** Not setting base timing correctly before tuning advance

**Data Analysis Mistakes:**
- **Using Wrong Data:** Using O2 sensor data during acceleration/warm-up (should only use during steady-state)
- **Not Logging:** Not using datalogging to verify changes
- **Ignoring Patterns:** Not looking for patterns in logged data
- **No Documentation:** Not documenting what was changed and why

**Communication Mistakes:**
- **Vague Problem Reports:** Saying "it doesn't work" without details
- **Missing Information:** Not providing datalogs, configuration files, versions
- **No Context:** Not explaining what was being tested when problem occurred

**How to Avoid:**
- **Follow Tuning Order:** Tune base tables first, then supporting features
- **Safety First:** Always check for leaks, verify fuel pressure, ensure proper power
- **Small Changes:** Make small, incremental changes
- **Always Backup:** Keep backups of working configurations
- **Use Datalogging:** Log everything and analyze the data
- **Document Everything:** Document changes, test conditions, and results
- **Verify Sensors:** Check all sensors before starting to tune
- **Test Systematically:** Test one thing at a time under controlled conditions

**Best Practices:**
- One change at a time
- Always have backup
- Fix idle before driving
- Tune in proper order (VE → AFR → Spark → Acceleration)
- Use datalogging extensively
- Document everything
- Verify sensors before tuning
- Test under actual conditions

**Bottom Line:**
Avoid common mistakes by following proper tuning order, making small incremental changes, using datalogging, verifying sensors, and always maintaining backups. Safety first - check for leaks and verify systems before starting.""",
        "keywords": ["tuning mistakes", "EFI errors", "tuning problems", "common mistakes", "tuning pitfalls"],
        "topic": "EFI Tuning - Common Mistakes"
    },
    {
        "question": "How does barometric pressure correction work in EFI tuning?",
        "answer": """Barometric pressure correction compensates for changes in atmospheric pressure (altitude).

**How It Works:**
- **Start-Up Recording:** ECU records ambient barometric pressure when powered on
- **Pressure Measurement:** Uses MAP sensor reading before engine starts (before vacuum is created)
- **Correction Multiplier:** Applies correction multiplier to VE table based on pressure
- **Altitude Compensation:** Higher altitude (lower pressure) = more fuel added

**Why It's Needed:**
- **At Higher Altitude:** At given MAP, engine flows more air with less exhaust back pressure
- **More Air = More Fuel:** Engine needs more fuel at higher altitudes
- **Consistency:** Maintains consistent air/fuel ratios regardless of altitude

**Correction Values:**
- **Source:** Correction values typically come from OEM ECU calibrations (e.g., 1990 Corvette ECU)
- **Pressure-Based:** Correction increases as pressure decreases (higher altitude)
- **Automatic:** Applied automatically once barometric pressure is recorded

**Important Considerations:**
- **Start-Up Timing:** Barometric pressure must be recorded before engine starts
- **Running Reset:** If ECU resets while running, it may grab engine vacuum instead of barometric pressure
- **Reset Detection:** Can detect resets by monitoring seconds counter (should count 0-255 continuously)
- **Unusual Values:** If barometric pressure shows unusual values (like 76 kPa), ECU may be resetting while running

**Verification:**
- **Check Seconds Counter:** Should count 0-255 continuously without resets
- **Barometric Display:** Should show reasonable atmospheric pressure (~100 kPa at sea level)
- **Reset Detection:** Audible beep and reset counter if reset detected
- **Datalog Review:** Check datalog seconds count for unexpected rollovers

**Bottom Line:**
Barometric pressure correction automatically compensates for altitude by recording ambient pressure at start-up and applying correction multipliers to the VE table. This maintains consistent air/fuel ratios regardless of altitude.""",
        "keywords": ["barometric pressure", "altitude correction", "baro correction", "atmospheric pressure", "altitude compensation"],
        "topic": "EFI Tuning - Barometric Correction"
    },
    {
        "question": "What is the difference between open loop and closed loop operation?",
        "answer": """Open loop and closed loop refer to whether the ECU uses oxygen sensor feedback to adjust fuel delivery.

**Closed Loop Operation:**
- **O2 Sensor Feedback:** ECU uses oxygen sensor to monitor actual air/fuel ratio
- **Automatic Adjustment:** ECU automatically adjusts fuel delivery to maintain target AFR
- **Best For:** Cruise conditions, steady-state operation
- **Activation:** Set O2 sensor step to non-zero value

**Open Loop Operation:**
- **No O2 Feedback:** ECU does not use oxygen sensor for fuel adjustment
- **Fixed Fuel Delivery:** Fuel delivery based solely on VE table and other fixed parameters
- **Best For:** WOT (wide open throttle), boost conditions, acceleration
- **Activation:** Set O2 sensor step to 0 (zero)

**When to Use Each:**
- **Closed Loop:** Use for cruise, idle, light load conditions where O2 sensor can accurately monitor AFR
- **Open Loop:** Use for WOT, boost, acceleration where O2 sensor may not be accurate or fast enough

**Important Considerations:**
- **O2 Sensor Data:** In open loop, O2 sensor voltage is still logged but not used for adjustment
- **Target AFR:** In open loop, must rely on VE table accuracy to achieve target AFR
- **Wideband O2:** Wideband O2 sensors provide more accurate feedback than narrow band
- **Narrow Band O2:** Only accurate near stoichiometric (14.7:1), not suitable for WOT/boost

**Tuning Implications:**
- **Closed Loop Tuning:** Can use O2 sensor feedback to automatically correct VE table
- **Open Loop Tuning:** Must manually tune VE table to achieve target AFR
- **Verification:** Use wideband O2 sensor to verify AFR in both modes

**Best Practice:**
- Use closed loop for cruise and light load
- Use open loop for WOT and boost
- Monitor wideband O2 sensor in both modes for verification
- Tune VE table accurately for open loop operation

**Bottom Line:**
Closed loop uses O2 sensor feedback for automatic fuel adjustment (best for cruise), while open loop uses fixed fuel delivery from VE table (best for WOT/boost). Choose based on operating conditions.""",
        "keywords": ["open loop", "closed loop", "O2 sensor", "lambda feedback", "fuel control"],
        "topic": "EFI Tuning - Open/Closed Loop"
    }
]

ARTICLE_URL = "https://www.useasydocs.com/details/us3tune.htm"
ARTICLE_SOURCE = "EFI Tuning Principles and Best Practices"


def main():
    """Add EFI tuning principles to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in EFI_TUNING_KNOWLEDGE:
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
                    "category": "EFI Tuning",
                    "data_type": "tuning_principles"
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
    LOGGER.info(f"Total entries: {len(EFI_TUNING_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nEFI Tuning Principles and Best Practices have been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - Fundamental tuning parameters (VE, AFR, Spark)")
    LOGGER.info(f"  - Safety procedures and best practices")
    LOGGER.info(f"  - VE table tuning methods")
    LOGGER.info(f"  - AFR table tuning strategies")
    LOGGER.info(f"  - Ignition timing tuning")
    LOGGER.info(f"  - Cold start and warm-up enrichment")
    LOGGER.info(f"  - Acceleration enrichment")
    LOGGER.info(f"  - Idle tuning procedures")
    LOGGER.info(f"  - Datalogging and analysis")
    LOGGER.info(f"  - Common tuning mistakes")
    LOGGER.info(f"  - Barometric pressure correction")
    LOGGER.info(f"  - Open loop vs closed loop operation")


if __name__ == "__main__":
    main()

