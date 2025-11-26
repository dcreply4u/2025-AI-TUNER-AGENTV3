"""
Add Comprehensive Racing, Tuning, and Engine Technical Knowledge
Searches and adds missing knowledge about racing techniques, engine tuning, and technical information.
"""

from __future__ import annotations

import logging
from services.vector_knowledge_store import VectorKnowledgeStore

LOGGER = logging.getLogger(__name__)


def add_racing_tuning_knowledge(vector_store: VectorKnowledgeStore) -> int:
    """
    Add comprehensive racing, tuning, and engine technical knowledge.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        
    Returns:
        Number of knowledge entries added
    """
    count = 0
    
    knowledge_entries = [
        # Engine Knock and Detonation
        {
            "text": """Engine Knock and Detonation - Causes, Prevention, and Diagnosis

KNOCK vs DETONATION vs PRE-IGNITION:
- Knock/Detonation: Fuel ignites after spark, but second flame front collides with first
- Pre-Ignition: Fuel ignites BEFORE spark plug fires (more dangerous)
- Both cause engine damage if severe

CAUSES OF KNOCK:
1. Too much ignition advance (most common)
2. Too lean air-fuel ratio (AFR > 13.5:1 at WOT)
3. Too much boost pressure
4. Hot intake air temperature (IAT > 150°F)
5. Low octane fuel
6. Carbon deposits (hot spots in cylinder)
7. High compression ratio
8. Lean fuel injectors
9. Exhaust backpressure
10. Engine overheating

SYMPTOMS:
- Metallic pinging/knocking sound (especially under load)
- Power loss
- High exhaust gas temperature (EGT)
- Rough idle (if severe)
- Engine damage (piston damage, ring land failure, head gasket failure)

PREVENTION STRATEGIES:
1. Conservative Timing: Start 5-10° retarded, advance gradually
2. Proper AFR: 12.5-13.2:1 at WOT (not leaner)
3. Boost Management: Don't exceed safe levels for engine
4. Intake Cooling: Intercooler, methanol injection, E85
5. Fuel Quality: Use appropriate octane (91+ for performance)
6. Engine Health: Clean injectors, good compression, no carbon buildup
7. Monitoring: Always use knock sensor, log knock counts

KNOCK SENSOR OPERATION:
- Detects vibration frequency of knock (typically 5-15 kHz)
- ECU can automatically retard timing when knock detected
- Typical response: -2° to -5° timing per knock event
- Some systems use knock intensity (mild vs severe)

TIMING RETARD FOR KNOCK:
- Immediate: Retard 2-3° in affected cell
- If knock persists: Retard another 2-3°
- Check other causes: AFR, boost, IAT, fuel quality
- Safe timing = 2-3° retarded from knock threshold

DIAGNOSIS PROCEDURE:
1. Log knock sensor data during pull
2. Identify RPM/load points with knock
3. Check AFR at those points (may be too lean)
4. Check boost at those points (may be too high)
5. Check IAT (may be too hot)
6. Reduce timing in those specific cells
7. Re-test and verify knock is gone

SEVERITY LEVELS:
- Mild: Occasional knock, minimal power loss
- Moderate: Frequent knock, noticeable power loss
- Severe: Constant knock, significant power loss, engine damage risk
- Critical: Immediate engine damage possible

TYPICAL TIMING REDUCTIONS:
- For boost: -1° to -2° per PSI of boost
- For high IAT: -1° per 20°F above 100°F
- For lean AFR: -2° to -5° depending on severity
- For low octane: -3° to -8° depending on fuel quality""",
            "metadata": {
                "topic": "Engine Knock and Detonation",
                "category": "tuning",
                "source": "Engine Performance",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "knock, detonation, pre-ignition, ping, knock sensor, timing retard, engine damage, prevention"
            }
        },
        
        # Camshaft Timing
        {
            "text": """Camshaft Timing and Overlap - Performance Tuning

CAM TIMING BASICS:
- Intake Valve Opening (IVO): When intake valve starts to open
- Intake Valve Closing (IVC): When intake valve fully closes
- Exhaust Valve Opening (EVO): When exhaust valve starts to open
- Exhaust Valve Closing (EVC): When exhaust valve fully closes
- Overlap: Period when both intake and exhaust valves are open

VALVE OVERLAP:
Overlap = IVO to EVC (both valves open simultaneously)

Effects:
- More overlap: Better high-RPM power, worse low-RPM torque
- Less overlap: Better low-RPM torque, worse high-RPM power
- Zero overlap: Best low-RPM, worst high-RPM
- Large overlap: Best high-RPM, worst idle/low-RPM

TYPICAL OVERLAP VALUES:
- Street: 0-20° overlap
- Performance: 20-50° overlap
- Race: 50-80° overlap
- Extreme race: 80-120° overlap

LSA (Lobe Separation Angle):
LSA = (Intake_Centerline + Exhaust_Centerline) / 2

Effects:
- Narrow LSA (104-108°): More overlap, better high-RPM
- Wide LSA (112-118°): Less overlap, better low-RPM torque
- Typical: 108-112° for street performance

DURATION:
Duration = Total degrees of cam rotation valve is open

Effects:
- Short duration (200-220°): Better low-RPM, worse high-RPM
- Long duration (240-280°): Better high-RPM, worse low-RPM
- Typical street: 220-240°
- Typical race: 250-280°+

LIFT:
Lift = Maximum valve opening distance

Effects:
- More lift: Better airflow, more power
- Limited by: Piston clearance, valve spring capability
- Typical: 0.400-0.600" for street, 0.600-0.800" for race

ADVANCE/RETARD:
- Advancing cam: IVO/EVO earlier, better low-RPM torque
- Retarding cam: IVO/EVO later, better high-RPM power
- Typical adjustment: ±4° from centerline

DYNAMIC COMPRESSION RATIO:
Affected by IVC (Intake Valve Closing):
- Early IVC: Higher dynamic compression, better low-RPM
- Late IVC: Lower dynamic compression, better high-RPM

TUNING STRATEGY:
- Low-RPM focus: Narrow LSA, short duration, advance cam
- High-RPM focus: Wide LSA, long duration, retard cam
- Balanced: Medium LSA (110°), medium duration (230-250°)

CALCULATION:
Effective Compression = Static_CR × (Swept_Volume_After_IVC / Total_Swept_Volume)

Where IVC determines how much cylinder is filled before compression starts.""",
            "metadata": {
                "topic": "Camshaft Timing and Overlap",
                "category": "tuning",
                "source": "Engine Performance",
                "tuning_related": True,
                "telemetry_relevant": False,
                "keywords": "camshaft, cam timing, valve overlap, LSA, duration, lift, advance, retard, IVO, IVC, EVO, EVC"
            }
        },
        
        # Exhaust Tuning
        {
            "text": """Exhaust System Tuning - Headers, Scavenging, and Performance

HEADER PRIMARY LENGTH:
Optimal length creates pressure wave tuning for scavenging.

FORMULA (Simplified):
Primary_Length (inches) ≈ (850 × Exhaust_Duration) / (RPM × 4)

Where:
- Exhaust_Duration = Cam exhaust duration in degrees
- RPM = Target RPM for peak power
- Result in inches

TYPICAL VALUES:
- Low-RPM (2000-4000): 30-36 inches
- Mid-RPM (4000-6000): 24-30 inches
- High-RPM (6000-8000): 18-24 inches
- Extreme (8000+): 14-18 inches

PRIMARY DIAMETER:
Diameter affects exhaust velocity and flow.

FORMULA:
Primary_Diameter (inches) ≈ sqrt((Displacement_per_Cylinder × RPM) / 88,200)

Where:
- Displacement_per_Cylinder = Engine displacement / number of cylinders
- RPM = Target RPM
- Result in inches

TYPICAL VALUES:
- Small engine (2.0L): 1.375-1.5"
- Medium engine (3.0-4.0L): 1.5-1.625"
- Large engine (5.0L+): 1.625-1.875"
- Race engine: 1.75-2.0"+

COLLECTOR SIZE:
Collector diameter affects backpressure and flow.

FORMULA:
Collector_Diameter ≈ Primary_Diameter × 1.5 to 2.0

TYPICAL VALUES:
- 4-into-1: 2.5-3.5" diameter
- 4-into-2-into-1: 2.0-3.0" per branch
- Merge collector: Optimized for specific RPM range

COLLECTOR LENGTH:
Affects tuning frequency and scavenging.

TYPICAL VALUES:
- Short (8-12"): High-RPM focus
- Medium (12-18"): Balanced
- Long (18-24"): Low-RPM focus

SCAVENGING EFFECT:
Negative pressure wave from exhaust pulse helps pull fresh charge into cylinder.

Optimal when:
- Exhaust pulse creates negative pressure at exhaust valve
- Negative pressure occurs during overlap period
- Helps evacuate exhaust and draw in fresh charge

BACKPRESSURE EFFECTS:
- Too much: Restricts flow, reduces power
- Too little: Can hurt low-RPM torque (loses scavenging)
- Optimal: Minimal backpressure with good scavenging

EXHAUST SYSTEM COMPONENTS:
1. Headers: Primary tuning (length/diameter)
2. Collectors: Secondary tuning and flow
3. X-pipe/H-pipe: Balance cylinders, affects sound
4. Mufflers: Sound control, minimal flow restriction
5. Tailpipes: Final tuning, minimal effect

TUNING STRATEGY:
- Street: Longer primaries (30-36"), moderate diameter
- Track: Shorter primaries (24-28"), larger diameter
- Drag: Very short primaries (18-24"), large diameter
- Balanced: 26-30" primaries, 1.625" diameter

CALCULATION EXAMPLE:
Engine: 5.0L V8, 250° exhaust duration, target 6500 RPM
Primary_Length = (850 × 250) / (6500 × 4) = 8.17" (too short!)
Better: Target 5000 RPM = (850 × 250) / (5000 × 4) = 10.6"
Or use longer duration cam for higher RPM target.""",
            "metadata": {
                "topic": "Exhaust System Tuning",
                "category": "tuning",
                "source": "Engine Performance",
                "tuning_related": True,
                "telemetry_relevant": False,
                "keywords": "exhaust, headers, primary length, collector, scavenging, backpressure, exhaust tuning, primary diameter"
            }
        },
        
        # Intake Manifold Tuning
        {
            "text": """Intake Manifold Tuning - Runner Length and Plenum Volume

RUNNER LENGTH TUNING:
Optimal length creates pressure wave tuning for intake charge ramming.

FORMULA (Helmholtz Resonance):
Optimal_Runner_Length ≈ (Speed_of_Sound × 90) / (RPM × 4)

Where:
- Speed_of_Sound ≈ 1,125 ft/s at 70°F
- RPM = Target RPM for peak torque
- Result in inches

SIMPLIFIED:
Runner_Length (inches) ≈ 84,000 / RPM

TYPICAL VALUES:
- Low-RPM (2000-3000): 12-16 inches
- Mid-RPM (3000-5000): 8-12 inches
- High-RPM (5000-7000): 6-8 inches
- Very high (7000+): 4-6 inches

PLENUM VOLUME:
Affects throttle response and power delivery.

TYPICAL VALUES:
- Small plenum (50-100% of displacement): Better throttle response, worse top-end
- Medium plenum (100-150% of displacement): Balanced
- Large plenum (150-300% of displacement): Better top-end, worse throttle response

RUNNER DIAMETER:
Affects airflow velocity and volume.

TYPICAL VALUES:
- Small engine: 1.5-2.0" diameter
- Medium engine: 2.0-2.5" diameter
- Large engine: 2.5-3.5" diameter
- Race: 3.0-4.0" diameter

INTAKE MANIFOLD TYPES:
1. Single-plane: All runners feed from one plenum (high-RPM power)
2. Dual-plane: Two separate plenums (better low-RPM torque)
3. Tunnel ram: Very long runners, large plenum (extreme high-RPM)
4. EFI manifolds: Optimized for fuel injection (better distribution)

TUNING EFFECTS:
- Longer runners: Better low-RPM torque (pressure wave tuning)
- Shorter runners: Better high-RPM power (less restriction)
- Larger plenum: Better high-RPM, worse low-RPM response
- Smaller plenum: Better low-RPM response, worse high-RPM

CALCULATION EXAMPLE:
Target: 5500 RPM peak torque
Runner_Length = 84,000 / 5500 = 15.3 inches
This creates resonance at 5500 RPM for maximum charge ramming effect.""",
            "metadata": {
                "topic": "Intake Manifold Tuning",
                "category": "tuning",
                "source": "Engine Performance",
                "tuning_related": True,
                "telemetry_relevant": False,
                "keywords": "intake manifold, runner length, plenum volume, Helmholtz resonance, charge ramming, single-plane, dual-plane"
            }
        },
        
        # Cooling System
        {
            "text": """Cooling System Management - Engine Temperature Control

OPTIMAL OPERATING TEMPERATURES:
- Coolant Temperature: 180-200°F (82-93°C) for performance
- Oil Temperature: 200-240°F (93-115°C) for performance
- Intake Air Temperature: <120°F (49°C) for best power
- Exhaust Gas Temperature: <1600°F (871°C) at WOT

THERMOSTAT SELECTION:
- Stock: 195°F (90°C) - maintains emissions compliance
- Performance: 180°F (82°C) - better power, slightly less efficient
- Race: 160-170°F (71-77°C) - maximum power, poor warm-up

RADIATOR SIZING:
Radiator_Size = (HP × Heat_Rejection) / (Temperature_Difference × Airflow)

Where:
- Heat_Rejection ≈ 33% of HP (typical)
- Temperature_Difference = Coolant_Temp - Ambient_Temp
- Airflow = Fan CFM or vehicle speed

TYPICAL SIZING:
- Street: 1 sq ft per 50-75 HP
- Performance: 1 sq ft per 40-50 HP
- Race: 1 sq ft per 30-40 HP

FAN CONTROL:
- Electric fans: On/off or variable speed
- On temperature: 195-205°F (90-96°C)
- Off temperature: 185-195°F (85-90°C)
- Hysteresis: 10-15°F to prevent cycling

WATER PUMP:
- Flow rate: 20-40 GPM typical
- Higher flow: Better cooling, more parasitic loss
- Impeller design: Affects flow at various RPM

COOLANT MIXTURE:
- 50/50 water/antifreeze: Standard protection
- 70/30 water/antifreeze: Better cooling, less protection
- Water + Water Wetter: Best cooling, no freeze protection
- Pure water: Best cooling, no protection (race only)

OVERHEATING CAUSES:
1. Insufficient radiator size
2. Blocked radiator (debris, bugs)
3. Faulty thermostat (stuck closed)
4. Low coolant level
5. Faulty water pump
6. Head gasket leak (combustion into coolant)
7. Insufficient airflow (fan not working)
8. Too much timing advance (creates more heat)

COOLING SYSTEM PRESSURE:
- Operating pressure: 12-16 PSI (typical)
- Higher pressure: Higher boiling point
- Pressure cap rating: Matches system pressure
- Leak detection: Pressure test system

OIL COOLING:
- Oil-to-air cooler: Most common
- Oil-to-water cooler: More efficient, complex
- Sizing: 1 sq ft per 50-75 HP typical
- Thermostatic bypass: Prevents over-cooling

INTERCOOLER (Forced Induction):
- Air-to-air: Most common, efficient
- Air-to-water: More compact, requires pump
- Sizing: Match to boost level and airflow
- Efficiency: 60-80% typical (reduces IAT significantly)

TEMPERATURE MONITORING:
- Coolant temp sensor: Critical for engine protection
- Oil temp sensor: Important for oil life
- IAT sensor: Critical for power (affects timing/boost)
- EGT sensor: Critical for safety (detects lean conditions)

TUNING FOR TEMPERATURE:
- Hot engine: Reduce timing, may need richer AFR
- Cold engine: More timing possible, but warm-up important
- IAT compensation: -1° timing per 20°F above 100°F
- Coolant temp compensation: Adjust if engine runs hot/cold""",
            "metadata": {
                "topic": "Cooling System Management",
                "category": "tuning",
                "source": "Engine Performance",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "cooling system, radiator, thermostat, water pump, overheating, oil cooling, intercooler, temperature"
            }
        },
        
        # Launch Control
        {
            "text": """Launch Control - Drag Racing Launch Techniques

LAUNCH CONTROL SYSTEMS:
Electronic systems that manage RPM and traction during launch for optimal 60-foot times.

TYPES:
1. RPM Limiter: Holds RPM at set point (typically 3000-5000 RPM)
2. Traction Control: Reduces power when wheel slip detected
3. Two-Step: Different RPM limits for launch vs burnout
4. Progressive: Gradually increases RPM/power during launch

OPTIMAL LAUNCH RPM:
Depends on:
- Power curve (peak torque RPM ideal)
- Tire grip (more grip = higher RPM possible)
- Track conditions (prepped vs street)
- Vehicle weight and power

TYPICAL VALUES:
- Street tires: 2000-3000 RPM
- Drag radials: 3000-4000 RPM
- Slicks: 4000-6000 RPM
- Pro Stock: 6000-8000 RPM

LAUNCH TECHNIQUE:
1. Stage: Position vehicle at starting line
2. Pre-load: Build boost (if turbo) or prepare system
3. Launch: Release transbrake/brake at optimal RPM
4. Traction: Monitor wheel slip, adjust if needed
5. Shift: Shift at optimal RPM for next gear

WHEEL SLIP TARGET:
- Optimal: 5-12% slip for maximum acceleration
- Too little: Not using full traction
- Too much: Wasting power, losing time

TRANBRAKE:
- Holds transmission in gear while brakes applied
- Allows RPM to build against converter
- Release launches vehicle
- Typical: 2nd gear for automatic, 1st for manual

CLUTCH TECHNIQUE (Manual):
- Slip clutch: Gradual engagement for traction
- Dump clutch: Quick release for maximum acceleration
- Balance: Enough slip for traction, quick enough for time

BOOST BUILDING (Turbo):
- Two-step: Different RPM limit for boost building
- Anti-lag: Keeps turbo spooled between runs
- Launch RPM: High enough to build boost quickly

60-FOOT TIME TARGETS:
- Excellent: <1.4 seconds
- Good: 1.4-1.6 seconds
- Average: 1.6-1.8 seconds
- Poor: >1.8 seconds

FACTORS AFFECTING LAUNCH:
1. Tire pressure (lower = more grip, but watch for sidewall)
2. Track prep (VHT, track bite)
3. Suspension setup (weight transfer)
4. Power delivery (smooth vs aggressive)
5. Weather conditions (temperature, humidity)

TUNING LAUNCH CONTROL:
1. Start conservative (low RPM, high traction control)
2. Gradually increase RPM
3. Monitor 60-foot times
4. Adjust based on wheel slip data
5. Fine-tune for track conditions

SAFETY:
- Always test in safe area first
- Monitor engine parameters (knock, AFR, EGT)
- Have safety systems active (rev limit, overboost protection)
- Check for wheel hop (can damage drivetrain)""",
            "metadata": {
                "topic": "Launch Control and Techniques",
                "category": "racing",
                "source": "Drag Racing",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "launch control, two-step, transbrake, 60 foot time, wheel slip, traction control, drag racing launch"
            }
        },
        
        # Traction Control
        {
            "text": """Traction Control Systems - Wheel Slip Management

TRACTION CONTROL METHODS:
1. Ignition Cut: Cuts spark to reduce power
2. Fuel Cut: Cuts fuel to reduce power
3. Throttle Reduction: Reduces throttle opening
4. Boost Reduction: Reduces boost (turbo applications)
5. Brake Application: Applies brake to spinning wheel (advanced)

WHEEL SLIP DETECTION:
- GPS speed vs wheel speed comparison
- Individual wheel speed sensors
- Accelerometer data (longitudinal acceleration)
- Driveshaft RPM vs vehicle speed

OPTIMAL SLIP TARGETS:
- Street tires: 3-8% slip
- Drag radials: 5-12% slip
- Slick tires: 8-15% slip
- Pro Stock: 10-18% slip

TRACTION CONTROL ALGORITHM:
1. Measure wheel slip percentage
2. Compare to target range
3. If slip > target: Reduce power
4. If slip < target: Increase power
5. Adjust continuously for optimal slip

POWER REDUCTION METHODS:
- Ignition Cut: Fast response, can cause misfire
- Fuel Cut: Slower response, smoother
- Throttle: Smooth, but slower response
- Boost: Very effective for turbo, slower response

SENSITIVITY SETTINGS:
- Aggressive: Quick response, may be too sensitive
- Moderate: Balanced response
- Conservative: Slower response, may allow too much slip

APPLICATION:
- Drag Racing: Maintain optimal slip during launch and shifts
- Road Racing: Prevent wheel spin in corners
- Street: Safety feature, prevent loss of control

INTEGRATION WITH ECU:
- Real-time slip calculation
- Power adjustment based on slip
- Per-gear settings (different slip targets)
- RPM-based settings (different at various RPM)

TUNING PROCESS:
1. Set target slip percentage
2. Set sensitivity (how quickly system responds)
3. Test and log slip data
4. Adjust based on 60-foot times and trap speeds
5. Fine-tune for track conditions

ADVANCED FEATURES:
- Predictive: Anticipates slip based on throttle/load
- Learning: Adapts to track conditions
- Per-wheel: Individual control for AWD
- Launch-specific: Different settings for launch vs running

SAFETY CONSIDERATIONS:
- Don't disable completely (safety feature)
- Test in safe area
- Monitor for false triggers
- Have manual override available""",
            "metadata": {
                "topic": "Traction Control Systems",
                "category": "racing",
                "source": "Vehicle Dynamics",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "traction control, wheel slip, launch control, power reduction, slip detection, drag racing"
            }
        },
        
        # Engine Break-In
        {
            "text": """Engine Break-In Procedures - New Engine Setup

BREAK-IN PURPOSE:
- Seat piston rings to cylinder walls
- Wear-in bearings and other moving parts
- Establish proper clearances
- Clean up manufacturing debris

BREAK-IN METHODS:

1. TRADITIONAL (Conservative):
- First 20 minutes: Vary RPM 2000-4000, no full throttle
- First 50 miles: Vary RPM, light throttle, no extended cruise
- First 500 miles: Gradually increase load, avoid extended high RPM
- First 1000 miles: Normal driving, avoid extended high RPM
- After 1000 miles: Full power use

2. MODERN (Performance):
- First 20-30 minutes: Heat cycle (warm up, cool down) 3-5 times
- Immediate use: Vary RPM, use full throttle in short bursts
- Load the engine: Helps seat rings faster
- Avoid: Extended idle, extended cruise at one RPM

3. DYNO BREAK-IN:
- Run on dyno with varying load
- Heat cycle multiple times
- Check for issues before road use
- More controlled environment

OIL FOR BREAK-IN:
- Conventional oil: Better for break-in (less slippery)
- Break-in oil: Special formulation for break-in
- Change after first 20 minutes: Remove debris
- Change after first 100-500 miles: Remove wear particles

FUEL MIXTURE:
- Slightly rich: Helps cooling during break-in
- Monitor AFR: Should be safe (not too lean)
- Avoid: Extended lean conditions

TIMING:
- Conservative: Slightly retarded for safety
- Avoid: Aggressive timing that could cause knock
- Monitor: Knock sensor during break-in

COOLING:
- Monitor temperature: Don't overheat
- Ensure: Proper coolant flow
- Check: For leaks

WHAT TO MONITOR:
1. Oil pressure: Should be normal
2. Coolant temperature: Should stabilize
3. Compression: Check after break-in
4. Oil consumption: May be high initially
5. Leaks: Check for any fluid leaks
6. Unusual sounds: Investigate immediately

SIGNS OF PROBLEMS:
- Low oil pressure
- Overheating
- Excessive oil consumption
- Unusual noises
- Smoke from exhaust
- Fluid leaks

POST BREAK-IN:
- Change oil and filter
- Check compression (all cylinders)
- Check timing (may need adjustment)
- Check valve lash (if applicable)
- Tune for optimal performance
- Log baseline data

TYPICAL BREAK-IN TIME:
- Street engine: 500-1000 miles
- Performance engine: 200-500 miles
- Race engine: 50-200 miles or dyno break-in
- Depends on: Engine type, components, use""",
            "metadata": {
                "topic": "Engine Break-In Procedures",
                "category": "maintenance",
                "source": "Engine Building",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "engine break-in, break in procedure, new engine, ring seating, break-in oil, heat cycle"
            }
        },
        
        # Cylinder Head Porting
        {
            "text": """Cylinder Head Porting - Airflow Optimization

PORTING PURPOSE:
Modify intake and exhaust ports to improve airflow, increasing power and efficiency.

PORTING BASICS:
- Intake ports: Bring air/fuel into cylinder
- Exhaust ports: Remove exhaust gases
- Goal: Maximum flow with minimal turbulence

FLOW BENCH TESTING:
Measures airflow through ports at various valve lifts.

METRICS:
- Flow at 0.100" lift: Low-lift flow (important for low-RPM)
- Flow at 0.200" lift: Mid-lift flow
- Flow at 0.300" lift: High-lift flow
- Flow at 0.400"+ lift: Maximum lift flow

TYPICAL FLOW IMPROVEMENTS:
- Stock head: Baseline
- Ported head: +15-30% flow improvement
- Race ported: +30-50% flow improvement
- Extreme: +50-100% flow improvement (race only)

PORTING TECHNIQUES:
1. Enlarge ports: Increase cross-sectional area
2. Smooth surfaces: Reduce turbulence
3. Shape optimization: Improve flow direction
4. Short-side radius: Critical area for flow
5. Valve guide: Reduce size or shape for flow

INTAKE PORTING:
- Focus: Maximum flow, good velocity
- Enlarge: Gradually, maintain velocity
- Smooth: Remove casting marks, smooth transitions
- Shape: Optimize for flow direction

EXHAUST PORTING:
- Focus: Maximum flow, minimal backpressure
- Enlarge: More aggressive than intake
- Smooth: Critical for flow
- Shape: Optimize for scavenging

VALVE JOB:
- Multi-angle: Improves flow
- Back-cut: Reduces flow restriction
- Valve size: Larger = more flow (if head allows)

COMBUSTION CHAMBER:
- Shape: Affects compression and flame propagation
- Volume: Affects compression ratio
- Smooth: Reduces hot spots (knock prevention)

PORT MATCHING:
- Intake manifold to head: Match port sizes
- Exhaust header to head: Match port sizes
- Gasket matching: Match to gasket size

TYPICAL POWER GAINS:
- Street porting: +10-20 HP
- Performance porting: +20-40 HP
- Race porting: +40-80+ HP
- Depends on: Engine size, original flow, other mods

COST vs BENEFIT:
- DIY porting: Low cost, high risk
- Professional: Higher cost, guaranteed results
- CNC porting: Most consistent, highest cost

PORTING LIMITATIONS:
- Too large: Loses velocity, hurts low-RPM
- Too aggressive: Can weaken head
- Wrong shape: Can hurt flow
- Valve size: Limited by head design""",
            "metadata": {
                "topic": "Cylinder Head Porting",
                "category": "tuning",
                "source": "Engine Building",
                "tuning_related": True,
                "telemetry_relevant": False,
                "keywords": "cylinder head porting, porting, flow bench, intake port, exhaust port, valve job, airflow"
            }
        },
        
        # Data Logging Best Practices
        {
            "text": """Data Logging Best Practices - Effective Tuning Data Collection

LOG RATE SELECTION:
- High rate (100 Hz): Best for transient events (launch, shifts)
- Medium rate (20-50 Hz): Good for general tuning
- Low rate (1-10 Hz): Sufficient for steady-state

WHAT TO LOG:
Essential Parameters:
1. RPM: Engine speed
2. Throttle Position: Load indicator
3. MAP/MAF: Airflow measurement
4. AFR/Lambda: Air-fuel ratio
5. Ignition Timing: Spark advance
6. Boost Pressure: Forced induction
7. IAT: Intake air temperature
8. Coolant Temp: Engine temperature
9. EGT: Exhaust gas temperature (if available)
10. Knock Count: Detonation detection
11. Vehicle Speed: Performance metric
12. Wheel Slip: Traction metric

Additional Useful:
- Fuel Pressure
- Oil Pressure
- Oil Temperature
- Gear Position
- Brake Pressure
- Steering Angle
- Lateral G-Force
- GPS Data (speed, position)

LOG DURATION:
- Short pulls: 10-30 seconds (dyno, drag strip)
- Long pulls: 1-5 minutes (road course, street)
- Extended: 10-30 minutes (endurance, testing)

LOG TRIGGERS:
- Manual: Start/stop logging manually
- Speed-based: Start above X mph
- RPM-based: Start above X RPM
- Throttle-based: Start above X% throttle
- Time-based: Log for X seconds after trigger

DATA ANALYSIS:
1. Identify key events: Launch, shifts, WOT sections
2. Compare before/after: Tune changes
3. Look for anomalies: Knock, lean conditions, overheating
4. Track trends: Performance over time
5. Correlate parameters: Find relationships

COMMON MISTAKES:
- Not logging enough parameters
- Logging at wrong rate (too low for events)
- Not logging long enough
- Not comparing before/after
- Ignoring knock sensor data
- Not logging environmental conditions

BEST PRACTICES:
1. Always log before making changes
2. Log after every change
3. Use consistent conditions (same track, same weather)
4. Log multiple runs for average
5. Keep logs organized (date, conditions, changes)
6. Review logs immediately after run
7. Compare logs over time

LOG FILE MANAGEMENT:
- Name files descriptively: Date_Vehicle_Conditions.csv
- Store in organized folders
- Keep backup of important logs
- Document what changed between logs

ANALYSIS TOOLS:
- Spreadsheet: Excel, Google Sheets
- Specialized software: RaceRender, TrackAddict
- Custom analysis: Python scripts
- Real-time: During run if possible

CORRELATION ANALYSIS:
- AFR vs Power: Find optimal AFR
- Timing vs Knock: Find safe timing
- Boost vs Power: Find optimal boost
- Temperature vs Performance: Find optimal temps""",
            "metadata": {
                "topic": "Data Logging Best Practices",
                "category": "tuning",
                "source": "Performance Tuning",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "data logging, log rate, parameters, analysis, best practices, tuning data, telemetry"
            }
        },
        
        # Engine Diagnostics
        {
            "text": """Engine Diagnostics - Troubleshooting Common Issues

COMPRESSION TEST:
Measures cylinder sealing capability.

PROCEDURE:
1. Remove spark plugs
2. Install compression gauge
3. Crank engine 4-6 times
4. Record pressure for each cylinder

NORMAL VALUES:
- Healthy: 150-200 PSI (varies by engine)
- Variation: <10% between cylinders
- Low: <120 PSI indicates problem
- High: >220 PSI may indicate carbon buildup

INTERPRETATION:
- Low all cylinders: Worn rings, timing issue
- Low one cylinder: Valve, ring, or head gasket issue
- Wet test: Add oil, if pressure increases = rings
- Dry test: No oil, baseline compression

LEAKDOWN TEST:
Measures where compression is leaking.

PROCEDURE:
1. Bring cylinder to TDC
2. Apply compressed air to cylinder
3. Measure pressure loss
4. Listen for leak location

INTERPRETATION:
- Intake valve: Hiss from intake
- Exhaust valve: Hiss from exhaust
- Rings: Hiss from oil fill or PCV
- Head gasket: Bubbles in coolant, pressure in other cylinder

FUEL PRESSURE TEST:
Measures fuel system pressure.

NORMAL VALUES:
- Port injection: 40-60 PSI
- Direct injection: 2000-3000 PSI
- Carbureted: 4-7 PSI

ISSUES:
- Low pressure: Weak pump, clogged filter, leak
- High pressure: Faulty regulator
- Fluctuating: Pump issue, regulator issue

VACUUM TEST:
Measures intake manifold vacuum.

NORMAL VALUES:
- Idle: 15-22 inHg (varies by cam)
- Steady: Should be stable
- WOT: Drops to near zero

INTERPRETATION:
- Low vacuum: Leak, cam timing, compression issue
- Fluctuating: Valve issue, compression issue
- High vacuum: Good engine health

OIL PRESSURE:
Normal: 10 PSI per 1000 RPM (minimum)
- Idle: 20-40 PSI typical
- Running: 40-80 PSI typical

ISSUES:
- Low pressure: Pump, bearing clearance, oil level
- High pressure: Relief valve, wrong oil weight
- Fluctuating: Pump issue, bearing issue

COOLING SYSTEM TEST:
Pressure test: 12-16 PSI typical

ISSUES:
- Leaks: Visible or pressure drop
- Head gasket: Combustion gases in coolant
- Thermostat: Stuck open/closed

IGNITION SYSTEM TEST:
Spark test: Should jump 0.5" gap minimum

ISSUES:
- Weak spark: Coil, wires, plugs
- No spark: Coil, module, wiring
- Misfire: Plug, wire, coil, injector

SENSOR DIAGNOSTICS:
- O2 sensor: Should oscillate (0.1-0.9V)
- MAF sensor: Should read airflow
- MAP sensor: Should read pressure
- IAT sensor: Should read temperature
- TPS: Should read 0-100% smoothly

COMMON PROBLEMS:
1. Rich condition: Faulty O2, MAF, injector
2. Lean condition: Vacuum leak, fuel pressure, injector
3. Misfire: Ignition, injector, compression
4. Knock: Timing, AFR, boost, fuel quality
5. Overheating: Cooling system, timing, AFR
6. Low power: Timing, AFR, boost, compression
7. Rough idle: Vacuum leak, injector, timing
8. High fuel consumption: Rich condition, leak, sensor""",
            "metadata": {
                "topic": "Engine Diagnostics and Troubleshooting",
                "category": "troubleshooting",
                "source": "Automotive Diagnostics",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "diagnostics, compression test, leakdown, fuel pressure, vacuum test, troubleshooting, engine problems"
            }
        },
        
        # Sensor Calibration
        {
            "text": """Sensor Calibration - Accurate Measurement Setup

WIDEBAND O2 SENSOR CALIBRATION:
Critical for accurate AFR measurement.

CALIBRATION PROCEDURE:
1. Free air calibration: Expose sensor to air, calibrate to 20.9% O2
2. Span calibration: Use known gas mixture
3. Heater calibration: Ensure proper operating temperature

ACCURACY:
- Wideband: ±0.1 AFR typical
- Narrowband: ±1.0 AFR (less accurate)
- Calibration frequency: Every 6-12 months or if readings suspect

MAF SENSOR CALIBRATION:
Measures mass airflow into engine.

CALIBRATION:
- Use known airflow source
- Compare to calculated airflow
- Adjust calibration table
- Verify at multiple flow rates

MAP SENSOR CALIBRATION:
Measures manifold absolute pressure.

CALIBRATION:
- Atmospheric pressure: Calibrate at known pressure
- Zero point: With engine off, should read barometric
- Full scale: Check at known pressure (boost gauge)

TPS CALIBRATION:
Throttle position sensor.

CALIBRATION:
- Closed throttle: Should read 0% (adjust if needed)
- Wide open: Should read 100% (adjust if needed)
- Linear: Should be smooth 0-100%

IAT SENSOR CALIBRATION:
Intake air temperature.

CALIBRATION:
- Compare to known temperature source
- Check at multiple temperatures
- Verify linearity

COOLANT TEMP SENSOR:
Engine coolant temperature.

CALIBRATION:
- Compare to known temperature
- Check at operating temperature
- Verify accuracy

FUEL PRESSURE SENSOR:
Fuel system pressure.

CALIBRATION:
- Compare to mechanical gauge
- Check at various pressures
- Verify linearity

BOOST PRESSURE SENSOR:
Turbo/supercharger boost.

CALIBRATION:
- Compare to mechanical gauge
- Check atmospheric reading
- Verify at various boost levels

KNOCK SENSOR CALIBRATION:
Detects engine knock.

CALIBRATION:
- Test with known knock source
- Adjust sensitivity
- Verify detection threshold

GPS SPEED CALIBRATION:
Vehicle speed from GPS.

CALIBRATION:
- Compare to wheel speed sensors
- Verify at various speeds
- Account for tire growth at speed

CALIBRATION FREQUENCY:
- Critical sensors: Every 6-12 months
- After modifications: Re-calibrate affected sensors
- If readings suspect: Calibrate immediately
- Before major tuning: Verify all sensors

CALIBRATION TOOLS:
- Known reference sources
- Calibration gases (for O2)
- Mechanical gauges (for pressure)
- Thermometers (for temperature)
- Speed reference (for speed sensors)

ACCURACY REQUIREMENTS:
- AFR: ±0.1 for tuning
- Pressure: ±1% for critical measurements
- Temperature: ±2°F for critical measurements
- Speed: ±0.1 mph for performance measurements""",
            "metadata": {
                "topic": "Sensor Calibration Procedures",
                "category": "configuration",
                "source": "Data Acquisition",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "sensor calibration, O2 sensor, MAF, MAP, TPS, IAT, fuel pressure, boost pressure, accuracy"
            }
        },
        
        # Advanced Racing Techniques
        {
            "text": """Advanced Racing Techniques - Performance Optimization

DRAG RACING TECHNIQUES:

1. BURNOUT:
- Purpose: Heat tires for maximum grip
- Technique: Spin tires in water box, roll out, do burnout
- Duration: 3-5 seconds typical
- RPM: 4000-6000 RPM typical
- Monitor: Tire smoke, temperature

2. STAGING:
- Shallow stage: Front tires just break beam (better reaction time)
- Deep stage: Further into beam (worse reaction time, better ET)
- Technique: Roll in slowly, stop when both bulbs lit

3. LAUNCH:
- RPM: Optimal for traction (varies by setup)
- Technique: Smooth release, monitor wheel slip
- Traction: 5-12% slip optimal
- Shift: At peak horsepower RPM

4. SHIFTING:
- Speed: Fast but smooth
- RPM: Peak horsepower point
- Technique: Don't lift, quick shift
- Monitor: RPM drop, should land at peak torque

ROAD RACING TECHNIQUES:

1. BRAKING:
- Threshold braking: Maximum braking without lockup
- Trail braking: Brake into corner, release gradually
- Brake points: Consistent markers
- Brake balance: Front/rear distribution

2. CORNERING:
- Apex: Hit inside of corner at optimal point
- Line: Outside-inside-outside for maximum speed
- Speed: Fastest speed through corner
- Traction: Monitor lateral G, wheel slip

3. ACCELERATION:
- Exit speed: Critical for lap time
- Traction: Smooth throttle application
- Shift points: Optimal for track layout
- Power delivery: Smooth, not abrupt

4. OVERTAKING:
- Brake later: Out-brake opponent
- Better exit: Faster corner exit speed
- Drafting: Use slipstream for passing
- Timing: Pass at optimal location

DATA ANALYSIS FOR RACING:

1. SECTOR TIMES:
- Break track into sectors
- Compare sector times
- Identify where time is lost/gained
- Focus improvement on slow sectors

2. LAP COMPARISON:
- Compare best lap to current lap
- Identify differences
- Adjust technique based on data
- Track improvements over time

3. TELEMETRY ANALYSIS:
- Speed traces: Compare corner speeds
- Brake points: Compare braking distances
- Throttle application: Compare exit speeds
- G-forces: Compare cornering loads

OPTIMIZATION PROCESS:
1. Baseline: Establish current performance
2. Identify: Find areas for improvement
3. Test: Try different techniques
4. Measure: Compare results
5. Refine: Fine-tune based on data
6. Repeat: Continuous improvement

COMMON MISTAKES:
- Over-driving: Trying too hard, making mistakes
- Inconsistent: Not repeating same technique
- Ignoring data: Not using telemetry
- Too aggressive: Not smooth, losing time
- Not practicing: Need seat time to improve""",
            "metadata": {
                "topic": "Advanced Racing Techniques",
                "category": "racing",
                "source": "Racing Performance",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "drag racing, road racing, burnout, staging, launch, shifting, braking, cornering, sector times, lap analysis"
            }
        }
    ]
    
    for entry in knowledge_entries:
        try:
            doc_id = vector_store.add_knowledge(
                text=entry["text"],
                metadata=entry["metadata"]
            )
            count += 1
            LOGGER.info(f"Added racing/tuning knowledge: {entry['metadata']['topic']}")
        except Exception as e:
            LOGGER.error(f"Failed to add knowledge '{entry['metadata']['topic']}': {e}")
            continue
    
    LOGGER.info(f"Racing/tuning knowledge addition complete: {count} entries added")
    return count


def main():
    """Main function."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    vector_store = VectorKnowledgeStore()
    count = add_racing_tuning_knowledge(vector_store)
    print(f"Added {count} racing/tuning/engine knowledge entries")
    return count


if __name__ == "__main__":
    main()

