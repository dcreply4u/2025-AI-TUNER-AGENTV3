#!/usr/bin/env python3
"""
Add EFI Tuning Theory and Principles to the AI Chat Advisor knowledge base.
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

# EFI Tuning Theory and Principles
EFI_TUNING_THEORY = [
    {
        "question": "What is stoichiometric air/fuel ratio and why does it matter?",
        "answer": """Stoichiometric mixture is a chemically correct mixture of fuel and air that would result in complete consumption of all fuel and all oxygen if combusted and given enough time to burn completely.

**Stoichiometric Ratio:**
- **Gasoline:** Typically quoted as 14.7:1 (air:fuel ratio)
- **Variation:** Can vary by a few tenths depending on fuel composition and additives
- **Oxygenates:** Ethanol or MTBE additives can affect stoichiometric ratio
- **Complete Combustion:** All fuel and oxygen consumed in ideal conditions

**Why It Matters:**
- **Efficiency:** Stoichiometric ratio provides optimal fuel efficiency
- **Emissions:** Complete combustion reduces harmful emissions
- **Baseline:** Used as reference point for tuning decisions
- **O2 Sensors:** Narrow band O2 sensors detect stoichiometric mixture

**Tuning Applications:**
- **Cruise Conditions:** Often tuned near stoichiometric for efficiency
- **WOT/Boost:** Tuned richer than stoichiometric for power and safety
- **Idle:** May be slightly rich or lean of stoichiometric for stability
- **Emissions:** Stoichiometric is target for emissions compliance

**Important Notes:**
- **Not Always Best:** Stoichiometric is not always the best ratio for all conditions
- **Power vs. Efficiency:** Power applications often run richer, efficiency applications run leaner
- **Safety Margins:** Boost and high-load conditions require richer mixtures
- **Fuel Variations:** Different fuels have different stoichiometric ratios

**Bottom Line:**
Stoichiometric ratio (14.7:1 for gasoline) is the chemically correct air/fuel ratio. It's used as a baseline, but optimal tuning may deviate from stoichiometric based on operating conditions and goals.""",
        "keywords": ["stoichiometric", "air fuel ratio", "14.7:1", "chemically correct", "AFR", "stoichiometric mixture"],
        "topic": "EFI Tuning - Theory"
    },
    {
        "question": "How does spark advance affect engine performance?",
        "answer": """Spark advance (ignition timing) controls when the spark plug fires relative to piston position, significantly affecting engine performance.

**What Spark Advance Does:**
- **Timing Control:** Determines when spark occurs in relation to piston position
- **Power Output:** Affects how efficiently fuel is burned
- **Torque Production:** Influences torque and horsepower output
- **Detonation Prevention:** Can prevent or cause detonation/knock

**How It Works:**
- **Early Spark (More Advance):** Spark fires earlier, giving more time for combustion
- **Late Spark (Less Advance/Retard):** Spark fires later, less time for combustion
- **Optimal Timing:** Balance between maximum power and detonation prevention

**Performance Effects:**
- **Too Much Advance:** Can cause detonation/knock, potential engine damage
- **Too Little Advance:** Reduced power, incomplete combustion, higher exhaust temps
- **Optimal Advance:** Maximum power without detonation

**Tuning Considerations:**
- **Load Dependent:** Timing needs vary with engine load (MAP/vacuum)
- **RPM Dependent:** Timing needs vary with engine speed
- **Fuel Quality:** Higher octane allows more advance
- **Compression Ratio:** Higher compression may require less advance
- **Boost:** Forced induction typically requires less advance

**Typical Timing Patterns:**
- **Low Load, Low RPM:** More advance (better efficiency)
- **High Load, High RPM:** Less advance (prevent detonation)
- **Boost Conditions:** Even less advance (prevent detonation under pressure)
- **Idle:** Moderate advance for stability

**Retard:**
- **Definition:** Reducing ignition advance timing
- **Purpose:** Often used to avoid detonation
- **Method:** Can be separate setting or achieved by reducing spark advance table values

**Bottom Line:**
Spark advance significantly affects engine performance. More advance can increase power but risks detonation. Less advance is safer but reduces power. Optimal timing balances maximum power with detonation prevention.""",
        "keywords": ["spark advance", "ignition timing", "timing advance", "spark timing", "ignition advance"],
        "topic": "EFI Tuning - Spark Advance Theory"
    },
    {
        "question": "What is the relationship between torque and horsepower?",
        "answer": """Torque and horsepower are related but different measures of engine performance.

**Torque:**
- **Definition:** Rotational force produced by the engine
- **Measurement:** Typically in foot-pounds (ft-lb) or Newton-meters (Nm)
- **What It Does:** Determines how hard the engine can "push"
- **Feel:** Torque is what you "feel" when accelerating

**Horsepower:**
- **Definition:** Rate at which work is done (power)
- **Calculation:** Horsepower = (Torque × RPM) / 5252
- **Measurement:** Typically in horsepower (HP) or kilowatts (kW)
- **What It Does:** Determines how fast work can be done
- **Feel:** Horsepower determines top speed and high-RPM performance

**The Relationship:**
- **Formula:** HP = (Torque × RPM) / 5252
- **At 5252 RPM:** Torque and horsepower are equal (by definition)
- **Below 5252 RPM:** Torque is higher than horsepower
- **Above 5252 RPM:** Horsepower is higher than torque

**Tuning Implications:**
- **Torque Focus:** Tune for maximum torque at lower RPMs (better acceleration, towing)
- **Horsepower Focus:** Tune for maximum power at higher RPMs (top speed, racing)
- **Balance:** Most applications benefit from balanced torque and horsepower curves

**What Affects Each:**
- **Torque:** Affected by volumetric efficiency, compression, fuel delivery at low-mid RPM
- **Horsepower:** Affected by ability to maintain torque at high RPM
- **Both:** Affected by air/fuel ratio, ignition timing, volumetric efficiency

**Tuning Strategy:**
- **Low RPM Tuning:** Focus on volumetric efficiency and fuel delivery for torque
- **High RPM Tuning:** Focus on maintaining efficiency and preventing power loss
- **Balance:** Optimize across RPM range for balanced performance

**Bottom Line:**
Torque is rotational force (what you feel), horsepower is rate of work (power output). They're related by the formula HP = (Torque × RPM) / 5252. Tuning can focus on maximizing torque, horsepower, or balancing both.""",
        "keywords": ["torque", "horsepower", "HP", "ft-lb", "power", "engine performance"],
        "topic": "EFI Tuning - Performance Theory"
    },
    {
        "question": "What is the tuning process for EFI systems?",
        "answer": """The EFI tuning process involves systematic adjustment of parameters to optimize engine performance.

**General Tuning Process:**
1. **Initial Setup:** Configure basic engine parameters, verify sensors, ensure safety
2. **Get Engine Running:** Tune cold start and cranking to get engine started
3. **Idle Tuning:** Get engine idling smoothly and consistently
4. **Base Fuel Tuning:** Tune VE table for steady-state conditions
5. **AFR Tuning:** Set target air/fuel ratios for different conditions
6. **Timing Tuning:** Tune spark advance table
7. **Acceleration Tuning:** Tune acceleration enrichment
8. **Fine-Tuning:** Optimize all parameters based on testing

**Tuning Order:**
- **Critical:** Must tune in proper order - fuel before timing, base before acceleration
- **One at a Time:** Change one parameter at a time
- **Verify Each Step:** Ensure each step works before moving to next
- **Document Changes:** Keep track of what was changed and why

**Tuning Methods:**
- **Steady-State Tuning:** Tune at constant RPM and load conditions
- **Transient Tuning:** Tune during acceleration, deceleration, transitions
- **Data Logging:** Use datalogging to analyze engine behavior
- **Dyno Testing:** Use dynamometer for controlled testing conditions
- **Road Testing:** Test under actual driving conditions

**Operating Envelope:**
- **Idle:** Low RPM, high vacuum (low MAP)
- **Cruise:** Mid RPM, mid vacuum
- **WOT:** High RPM, low vacuum (high MAP) or boost
- **Boost:** High load, may be at various RPMs
- **Transitions:** Between different operating conditions

**Specific Conditions:**
- **Cold Start:** Engine cold, requires enrichment
- **Warm-Up:** Engine warming, enrichment decreasing
- **Hot Start:** Engine hot, minimal enrichment needed
- **Acceleration:** Rapid throttle opening, requires enrichment
- **Deceleration:** Rapid throttle closing, may need enleanment

**Tuning Symptoms and Remedies:**
- **Too Rich:** Black smoke, poor fuel economy, fouled plugs - reduce fuel
- **Too Lean:** Hesitation, backfire, high EGTs - increase fuel
- **Too Much Timing:** Detonation/knock - reduce timing
- **Too Little Timing:** Reduced power, high EGTs - increase timing
- **Poor Idle:** Adjust idle fuel, timing, or idle control

**Bottom Line:**
The tuning process involves systematic adjustment of fuel, air/fuel ratio, and timing in proper order. Tune one parameter at a time, verify each step, and use data logging to guide decisions.""",
        "keywords": ["tuning process", "EFI tuning steps", "tuning methodology", "tuning order", "tuning procedure"],
        "topic": "EFI Tuning - Process"
    },
    {
        "question": "What are the general settings and engine parameters needed for EFI tuning?",
        "answer": """General settings and engine parameters provide the foundation for EFI tuning.

**Engine Parameters:**
- **Displacement:** Engine size (cubic inches or liters)
- **Number of Cylinders:** 4, 6, 8, etc.
- **Compression Ratio:** Ratio of cylinder volume at BDC to TDC
- **Fuel Type:** Gasoline, E85, methanol, etc.
- **Injector Size:** Flow rate of fuel injectors
- **Fuel Pressure:** Operating fuel pressure

**Sensor Calibrations:**
- **MAP Sensor:** Calibrate for vacuum and boost range
- **TPS Sensor:** Calibrate for 0-100% throttle position
- **Coolant Temperature:** Calibrate temperature sensor
- **Intake Air Temperature:** Calibrate IAT sensor
- **O2 Sensor:** Calibrate narrow band or wideband sensor

**Basic Settings:**
- **Required Fuel:** Base fuel calculation parameter
- **Idle Speed:** Target idle RPM
- **Rev Limit:** Maximum engine RPM
- **Fuel Cut:** RPM or other condition for fuel cut
- **Ignition Settings:** Base timing, trigger settings, etc.

**Operating Parameters:**
- **VE Table Size:** Typically 12×12 (MAP vs. RPM)
- **AFR Table Size:** Typically 12×12 (MAP vs. RPM)
- **Spark Table Size:** Typically 12×12 (MAP vs. RPM)
- **RPM Bins:** RPM breakpoints for tables
- **MAP Bins:** Load breakpoints for tables

**Important Considerations:**
- **Accuracy:** All parameters must be accurate for proper tuning
- **Verification:** Verify all sensors read correctly before tuning
- **Documentation:** Document all settings for reference
- **Backup:** Keep backups of working configurations

**Bottom Line:**
General settings and engine parameters provide the foundation for tuning. All parameters must be accurate, sensors must be calibrated, and settings must be documented for effective tuning.""",
        "keywords": ["engine parameters", "EFI settings", "sensor calibration", "tuning setup", "engine configuration"],
        "topic": "EFI Tuning - Setup"
    },
    {
        "question": "What is volumetric efficiency and how does it affect tuning?",
        "answer": """Volumetric efficiency (VE) is a measure of how efficiently an engine fills its cylinders with air.

**Definition:**
- **Ratio:** Mass of air that enters cylinder in a cycle compared to cylinder displacement
- **Percentage:** Expressed as percentage (100% = cylinder completely filled)
- **Typical Range:** Naturally aspirated engines typically 70-90% VE
- **Forced Induction:** Can exceed 100% with supercharger or turbo

**What Affects VE:**
- **Intake System:** Ease of air movement through intake system
- **Valve Timing:** Valve opening and closing times (cam timing)
- **Valve Size:** Size of intake and exhaust valves
- **Port Design:** Cylinder head port design and flow
- **Exhaust System:** Exhaust backpressure affects VE
- **RPM:** VE varies with engine speed
- **Load:** VE varies with engine load

**How It Affects Tuning:**
- **VE Table:** EFI systems use VE table to determine fuel delivery
- **Fuel Calculation:** Higher VE = more air = more fuel needed
- **Load Indication:** VE indicates engine load and air flow
- **Tuning Target:** Tune VE table to match actual engine VE characteristics

**VE Table Tuning:**
- **Purpose:** VE table tells ECU how much air engine is flowing
- **Values:** Higher values = more air flow = more fuel
- **Tuning:** Adjust VE values to achieve target air/fuel ratios
- **Smooth Transitions:** VE values should transition smoothly

**Important Considerations:**
- **Not Constant:** VE varies with RPM and load
- **Engine Specific:** Each engine has unique VE characteristics
- **Modifications:** Engine modifications change VE
- **Tuning Required:** VE table must be tuned for each engine

**Bottom Line:**
Volumetric efficiency measures how efficiently engine fills cylinders. It varies with RPM, load, and engine design. The VE table in EFI systems uses this to determine fuel delivery, and must be tuned to match actual engine characteristics.""",
        "keywords": ["volumetric efficiency", "VE", "air flow", "cylinder filling", "VE table"],
        "topic": "EFI Tuning - Volumetric Efficiency"
    },
    {
        "question": "What is MAP (Manifold Absolute Pressure) and how is it used in tuning?",
        "answer": """MAP (Manifold Absolute Pressure) is a measure of absolute pressure in the intake manifold, used to determine engine load and fueling requirements.

**What MAP Measures:**
- **Absolute Pressure:** Pressure relative to perfect vacuum (0 kPa)
- **Intake Manifold:** Pressure in the intake manifold
- **Engine Load:** Indicates how hard engine is working
- **Vacuum/Boost:** Measures both vacuum and boost conditions

**MAP Scale:**
- **0 kPa:** Perfect vacuum (maximum vacuum)
- **~100 kPa:** Typical atmospheric pressure (sea level)
- **>100 kPa:** Boost (forced induction)
- **Example:** 50 kPa ≈ 15 inHg vacuum, 250 kPa ≈ 21 PSI boost

**How It's Used:**
- **Load Indication:** MAP indicates engine load (lower MAP = higher load in naturally aspirated)
- **Fuel Calculation:** Used with VE table to determine fuel delivery
- **Table Axis:** One axis of VE, AFR, and spark tables
- **Acceleration Detection:** Rate of MAP change (MAPdot) indicates acceleration

**MAP in Tuning:**
- **VE Table:** MAP is one axis of VE table (other is RPM)
- **AFR Table:** MAP is one axis of AFR table
- **Spark Table:** MAP is one axis of spark advance table
- **Load Ranges:** Different MAP ranges represent different operating conditions

**Typical MAP Values:**
- **Idle:** 25-35 kPa (high vacuum, low load)
- **Cruise:** 40-60 kPa (moderate vacuum, light load)
- **WOT (NA):** 80-100 kPa (low vacuum, high load)
- **Boost:** 100-250+ kPa (positive pressure, very high load)

**Important Considerations:**
- **Barometric Pressure:** MAP sensor reads absolute pressure, affected by altitude
- **Calibration:** MAP sensor must be calibrated correctly
- **Range:** Ensure MAP sensor range covers vacuum and boost (if applicable)
- **Response:** MAP responds quickly to throttle changes

**MAPdot:**
- **Definition:** Rate of change of MAP sensor output
- **Use:** Indicates rapid pressure changes (acceleration/deceleration)
- **Acceleration Enrichment:** Can trigger acceleration enrichment

**Bottom Line:**
MAP measures absolute pressure in intake manifold, indicating engine load. It's used as one axis of tuning tables (VE, AFR, Spark) and helps determine fuel delivery and timing requirements.""",
        "keywords": ["MAP", "manifold absolute pressure", "engine load", "vacuum", "boost", "kPa"],
        "topic": "EFI Tuning - MAP"
    },
    {
        "question": "What is detonation (knock) and how do you prevent it?",
        "answer": """Detonation (also called knock, ping, or pink) is a dangerous condition where combustion starts in multiple locations in the cylinder.

**What Detonation Is:**
- **Normal Combustion:** Burning starts at spark plug and spreads smoothly
- **Detonation:** Combustion starts in second location (hot spot) before normal flame front arrives
- **Flame Fronts Collide:** Two flame fronts raise cylinder pressure to destructive levels
- **Sound:** Audible "ping" or "knock" sound
- **Damage:** Can cause piston, ring, or head gasket damage

**Causes of Detonation:**
- **Too Much Timing:** Excessive ignition advance
- **Too Lean:** Lean air/fuel mixture
- **High Compression:** High compression ratio
- **High Boost:** Excessive boost pressure
- **Hot Spots:** Hot spots in combustion chamber
- **Low Octane Fuel:** Fuel with insufficient octane rating
- **High EGTs:** High exhaust gas temperatures

**How to Prevent Detonation:**
- **Reduce Timing:** Retard ignition timing (reduce advance)
- **Enrichen Mixture:** Add more fuel (richer air/fuel ratio)
- **Reduce Boost:** Lower boost pressure (if forced induction)
- **Higher Octane:** Use higher octane fuel
- **Cooling:** Improve engine cooling
- **EGT Monitoring:** Monitor exhaust gas temperatures

**Tuning to Prevent Detonation:**
- **Conservative Timing:** Start with conservative timing, gradually increase
- **Rich WOT/Boost:** Run richer air/fuel ratios at WOT and boost
- **Timing Retard:** Reduce timing in high-load, high-RPM areas
- **Safety Margins:** Leave safety margins, don't push to absolute limit
- **Monitor:** Use knock sensors or listen for detonation

**Detonation Detection:**
- **Audible:** "Ping" or "knock" sound from engine
- **Knock Sensors:** Electronic sensors detect detonation
- **Power Loss:** Engine may lose power when detonating
- **Damage Signs:** Piston damage, ring damage, head gasket failure

**Important:**
- **Immediate Action:** If detonation detected, immediately reduce timing or enrichen mixture
- **Don't Ignore:** Detonation can cause severe engine damage quickly
- **Safety First:** Better to lose a little power than damage engine

**Bottom Line:**
Detonation is dangerous condition where combustion starts in multiple locations, causing destructive pressure. Prevent by reducing timing, enrichening mixture, reducing boost, using higher octane fuel, and maintaining safety margins.""",
        "keywords": ["detonation", "knock", "ping", "pink", "pre-ignition", "engine damage"],
        "topic": "EFI Tuning - Detonation"
    },
    {
        "question": "What is the difference between narrow band and wideband O2 sensors?",
        "answer": """Narrow band and wideband O2 sensors measure exhaust gas oxygen, but with different capabilities.

**Narrow Band O2 Sensor (NB-O2):**
- **Range:** Only detects stoichiometric mixture (14.7:1 for gasoline) very closely
- **Output:** Switches between high and low voltage at stoichiometric
- **Limitation:** Cannot accurately measure other air/fuel ratios
- **Use:** Good for closed-loop operation at stoichiometric
- **Cost:** Less expensive

**Wideband O2 Sensor (WB-O2):**
- **Range:** Can measure air/fuel ratios from 10:1 to 20:1 (all ratios of interest)
- **Output:** Provides continuous, accurate AFR reading
- **Capability:** Accurate across entire tuning range
- **Use:** Essential for tuning WOT, boost, and all operating conditions
- **Controller:** Requires sophisticated controller board to operate
- **Cost:** More expensive

**Key Differences:**
- **Accuracy:** Wideband is accurate across full range, narrow band only at stoichiometric
- **Tuning:** Wideband essential for tuning, narrow band limited to stoichiometric
- **Closed Loop:** Narrow band works for closed loop at stoichiometric
- **WOT/Boost:** Wideband needed for tuning WOT and boost conditions
- **Cost:** Narrow band less expensive, wideband more expensive

**Tuning Applications:**
- **Narrow Band:** Use for closed-loop operation during cruise (near stoichiometric)
- **Wideband:** Use for all tuning, especially WOT, boost, and off-stoichiometric conditions
- **Best Practice:** Use wideband for all tuning, narrow band only for basic closed-loop

**Important Considerations:**
- **Wideband Required:** Wideband O2 sensor is essential for proper EFI tuning
- **Controller Needed:** Wideband sensors require controller board
- **Calibration:** Both types need proper calibration
- **Placement:** Sensor placement affects accuracy

**Bottom Line:**
Narrow band sensors only detect stoichiometric mixture, while wideband sensors measure full AFR range (10:1 to 20:1). Wideband is essential for proper EFI tuning, especially for WOT and boost conditions.""",
        "keywords": ["narrow band O2", "wideband O2", "O2 sensor", "lambda sensor", "AFR sensor", "EGO sensor"],
        "topic": "EFI Tuning - O2 Sensors"
    },
    {
        "question": "What is IAT (Intake Air Temperature) and why is it important?",
        "answer": """IAT (Intake Air Temperature) is the temperature of air entering the cylinder, critical for accurate fuel calculation.

**What IAT Measures:**
- **Temperature:** Temperature of air entering intake system
- **Location:** Typically measured in intake manifold or air filter housing
- **Variation:** Changes with ambient temperature, engine heat, intercooler effectiveness

**Why It's Important:**
- **Mass Calculation:** Temperature affects air density (mass per volume)
- **Fuel Calculation:** EFI systems use IAT with MAP to calculate air mass
- **Ideal Gas Law:** Relationship between pressure, temperature, and volume
- **Accurate Fueling:** Correct IAT reading ensures accurate fuel delivery

**How It's Used:**
- **Air Mass Calculation:** IAT + MAP + VE = air mass calculation
- **Fuel Delivery:** Air mass determines required fuel delivery
- **Temperature Compensation:** Compensates for temperature changes
- **Density Correction:** Colder air = denser = more fuel needed

**Temperature Effects:**
- **Cold Air:** Denser, contains more oxygen, needs more fuel
- **Hot Air:** Less dense, contains less oxygen, needs less fuel
- **Intercooler:** Reduces IAT in forced induction applications
- **Heat Soak:** Engine heat can raise IAT when idling

**Tuning Considerations:**
- **Sensor Placement:** Location affects accuracy (manifold vs. filter housing)
- **Calibration:** Sensor must be calibrated correctly
- **Heat Soak:** Account for heat soak effects
- **Intercooler:** Monitor IAT to verify intercooler effectiveness

**Important:**
- **Accuracy:** IAT must be accurate for proper fuel calculation
- **Placement:** Sensor placement affects readings
- **Calibration:** Verify sensor calibration
- **Monitoring:** Monitor IAT during tuning to identify issues

**Bottom Line:**
IAT measures temperature of air entering engine. It's critical for accurate fuel calculation because temperature affects air density. EFI systems use IAT with MAP and VE to calculate air mass and determine fuel delivery.""",
        "keywords": ["IAT", "intake air temperature", "air temperature", "temperature sensor", "air density"],
        "topic": "EFI Tuning - IAT"
    },
    {
        "question": "What are the symptoms of tuning problems and their remedies?",
        "answer": """Recognizing tuning symptoms and knowing remedies is essential for effective EFI tuning.

**Too Rich (Too Much Fuel):**
- **Symptoms:** Black smoke from exhaust, poor fuel economy, fouled spark plugs, rough idle, sluggish performance
- **Remedy:** Reduce fuel delivery (lower VE table values, reduce pulse width)
- **Check:** Fuel pressure, injector size, VE table values

**Too Lean (Too Little Fuel):**
- **Symptoms:** Hesitation, backfire, high exhaust gas temperatures, engine damage risk, detonation
- **Remedy:** Increase fuel delivery (raise VE table values, increase pulse width)
- **Check:** Fuel pressure, injector flow, fuel system capacity, VE table values

**Too Much Timing Advance:**
- **Symptoms:** Detonation/knock, pinging sound, potential engine damage
- **Remedy:** Reduce ignition timing (retard timing, lower spark advance table values)
- **Check:** Spark advance table, base timing, timing calibration

**Too Little Timing Advance:**
- **Symptoms:** Reduced power, high exhaust gas temperatures, incomplete combustion
- **Remedy:** Increase ignition timing (advance timing, raise spark advance table values)
- **Check:** Spark advance table, base timing, timing calibration

**Poor Idle:**
- **Symptoms:** Rough idle, surging, stalling, inconsistent idle speed
- **Remedy:** Adjust idle fuel (VE table at idle), adjust idle timing, adjust idle control
- **Check:** Idle VE values, idle timing, idle air control, fuel pressure

**Hesitation on Acceleration:**
- **Symptoms:** Engine stumbles or hesitates when throttle opens
- **Remedy:** Increase acceleration enrichment, check VE table transitions
- **Check:** Acceleration enrichment settings, VE table smoothness

**Detonation/Knock:**
- **Symptoms:** Pinging/knocking sound, potential engine damage
- **Remedy:** Reduce timing, enrichen mixture, reduce boost, use higher octane fuel
- **Check:** Spark advance, air/fuel ratio, boost pressure, fuel quality

**High Exhaust Gas Temperatures:**
- **Symptoms:** Very high EGT readings, risk of engine damage
- **Remedy:** Enrichen mixture, reduce timing, check for lean conditions
- **Check:** Air/fuel ratio, ignition timing, cooling system

**Poor Fuel Economy:**
- **Symptoms:** Excessive fuel consumption
- **Remedy:** Lean out cruise conditions, optimize timing for efficiency
- **Check:** Cruise VE values, cruise timing, air/fuel ratios

**Bottom Line:**
Recognize tuning symptoms (rich/lean, timing issues, idle problems, etc.) and apply appropriate remedies. Use data logging and wideband O2 sensor to identify and fix problems systematically.""",
        "keywords": ["tuning symptoms", "tuning problems", "tuning remedies", "rich", "lean", "detonation", "tuning issues"],
        "topic": "EFI Tuning - Troubleshooting"
    },
    {
        "question": "What is TPSdot and MAPdot and how are they used?",
        "answer": """TPSdot and MAPdot measure the rate of change of throttle position and manifold pressure, used for acceleration enrichment.

**TPSdot:**
- **Definition:** Rate of change of TPS (Throttle Position Sensor) output
- **Measures:** How quickly throttle is being opened
- **Units:** Typically volts per second or percentage per second
- **Use:** Triggers acceleration enrichment when throttle opens quickly

**MAPdot:**
- **Definition:** Rate of change of MAP (Manifold Absolute Pressure) sensor output
- **Measures:** How quickly manifold pressure is changing
- **Units:** Typically kPa per second
- **Use:** Triggers acceleration enrichment when manifold pressure increases rapidly

**How They're Used:**
- **Acceleration Detection:** Detect rapid throttle opening or pressure increase
- **Acceleration Enrichment:** Trigger additional fuel during acceleration
- **Prevent Hesitation:** Provide extra fuel to prevent lean condition during acceleration
- **Smooth Response:** Ensure smooth engine response to throttle changes

**Acceleration Enrichment:**
- **Purpose:** Prevents lean condition when throttle opens quickly
- **Trigger:** TPSdot or MAPdot exceeds threshold
- **Duration:** Provides extra fuel for short duration
- **Amount:** Enrichment amount based on rate of change

**Tuning Considerations:**
- **Thresholds:** Set thresholds for when enrichment activates
- **Amount:** Adjust enrichment amount based on engine response
- **Duration:** Set how long enrichment lasts
- **Both Sensors:** Can use TPSdot, MAPdot, or both

**Important:**
- **Prevents Hesitation:** Proper acceleration enrichment prevents hesitation
- **Too Much:** Can cause bogging or rich condition
- **Too Little:** Can cause hesitation or lean condition
- **Testing:** Test under actual driving conditions

**Bottom Line:**
TPSdot and MAPdot measure rate of change of throttle position and manifold pressure. They're used to detect acceleration and trigger enrichment to prevent lean conditions and ensure smooth engine response.""",
        "keywords": ["TPSdot", "MAPdot", "acceleration enrichment", "throttle rate", "pressure rate", "acceleration detection"],
        "topic": "EFI Tuning - Acceleration"
    },
    {
        "question": "What is WOT (Wide Open Throttle) and how is it tuned?",
        "answer": """WOT (Wide Open Throttle) is when throttle is fully open, representing maximum engine load and power output.

**What WOT Is:**
- **Definition:** Throttle fully open (100% throttle position)
- **Condition:** Maximum engine load (for naturally aspirated engines)
- **Power Output:** Maximum power production
- **Tuning Critical:** Most critical tuning condition for power applications

**WOT Characteristics:**
- **High Load:** Maximum engine load
- **High RPM:** Typically occurs at high RPM
- **Maximum Air Flow:** Maximum air flow through engine
- **Maximum Fuel:** Requires maximum fuel delivery
- **Maximum Power:** Where maximum power is produced

**WOT Tuning:**
- **Fuel Delivery:** Must deliver sufficient fuel for maximum power
- **Air/Fuel Ratio:** Typically tuned richer (11.5-12.5:1) for power and safety
- **Ignition Timing:** Tuned for maximum power without detonation
- **Safety Margins:** Must leave safety margins to prevent damage

**Tuning Strategy:**
- **Rich Mixture:** Run richer than stoichiometric (11.5-12.5:1 typical)
- **Conservative Timing:** Use conservative timing to prevent detonation
- **Fuel System:** Ensure fuel system can deliver sufficient fuel
- **Monitoring:** Monitor AFR, EGT, and knock during WOT

**Important Considerations:**
- **Safety First:** WOT is high-stress condition, safety margins critical
- **Fuel System:** Must have adequate fuel system capacity
- **Detonation Risk:** High risk of detonation, must monitor carefully
- **EGT Monitoring:** Monitor exhaust gas temperatures
- **Wideband O2:** Essential for accurate AFR monitoring at WOT

**Boost Applications:**
- **WOT + Boost:** Even higher load, requires even richer mixture
- **More Fuel:** Boost applications need even more fuel capacity
- **Less Timing:** Typically need less timing advance under boost
- **Safety Critical:** Boost + WOT is most critical condition

**Bottom Line:**
WOT is maximum throttle opening, representing maximum load and power. Tune with richer air/fuel ratios (11.5-12.5:1), conservative timing, adequate fuel system, and careful monitoring for detonation and EGTs.""",
        "keywords": ["WOT", "wide open throttle", "full throttle", "maximum power", "WOT tuning"],
        "topic": "EFI Tuning - WOT"
    }
]

ARTICLE_URL = "https://www.megamanual.com/begintuning.htm"
ARTICLE_SOURCE = "EFI Tuning Theory and Principles"


def main():
    """Add EFI tuning theory to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in EFI_TUNING_THEORY:
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
                    "category": "EFI Tuning Theory",
                    "data_type": "tuning_theory"
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
    LOGGER.info(f"Total entries: {len(EFI_TUNING_THEORY)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nEFI Tuning Theory and Principles have been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - Stoichiometric air/fuel ratio")
    LOGGER.info(f"  - Spark advance theory")
    LOGGER.info(f"  - Torque and horsepower relationship")
    LOGGER.info(f"  - Tuning process and methodology")
    LOGGER.info(f"  - General settings and engine parameters")
    LOGGER.info(f"  - Volumetric efficiency")
    LOGGER.info(f"  - MAP (Manifold Absolute Pressure)")
    LOGGER.info(f"  - Detonation and prevention")
    LOGGER.info(f"  - Narrow band vs wideband O2 sensors")
    LOGGER.info(f"  - IAT (Intake Air Temperature)")
    LOGGER.info(f"  - Tuning symptoms and remedies")
    LOGGER.info(f"  - TPSdot and MAPdot")
    LOGGER.info(f"  - WOT (Wide Open Throttle) tuning")


if __name__ == "__main__":
    main()

