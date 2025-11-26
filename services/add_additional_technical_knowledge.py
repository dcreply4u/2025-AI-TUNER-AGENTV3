"""
Add Additional Technical Knowledge - Spark Plugs, Oil, Transmission, etc.
"""

from __future__ import annotations

import logging
from services.vector_knowledge_store import VectorKnowledgeStore

LOGGER = logging.getLogger(__name__)


def add_additional_technical_knowledge(vector_store: VectorKnowledgeStore) -> int:
    """Add additional technical knowledge."""
    count = 0
    
    knowledge_entries = [
        # Spark Plug Selection
        {
            "text": """Spark Plug Selection and Tuning

HEAT RANGE:
Spark plug heat range determines how quickly plug dissipates heat.

- Hot plug: Long insulator, retains heat (for cold/low-load engines)
- Cold plug: Short insulator, dissipates heat quickly (for hot/high-load engines)

SELECTION CRITERIA:
1. Engine load: High load = colder plug
2. Compression: High compression = colder plug
3. Boost: Forced induction = colder plug
4. Fuel: Higher octane = can use colder plug
5. RPM: High RPM = colder plug

TYPICAL SELECTIONS:
- Street engine: Heat range 5-7 (NGK scale)
- Performance: Heat range 6-8
- Turbo/Supercharged: Heat range 7-9
- Race: Heat range 8-10

GAP SETTING:
Spark plug gap affects spark intensity and ignition.

TYPICAL GAPS:
- Stock ignition: 0.030-0.040" (0.75-1.0mm)
- Performance ignition: 0.035-0.045" (0.9-1.1mm)
- High energy ignition: 0.040-0.055" (1.0-1.4mm)
- Forced induction: May need smaller gap (0.025-0.035")

GAP EFFECTS:
- Larger gap: Stronger spark, but harder to fire under pressure
- Smaller gap: Easier to fire, but weaker spark
- Too large: Misfire under load
- Too small: Weak spark, poor combustion

READING SPARK PLUGS:
- Light tan/chocolate: Optimal AFR and timing
- White/ashy: Too lean, too much timing, or too hot plug
- Dark/sooty: Too rich, too little timing, or too cold plug
- Wet/oily: Oil consumption issue
- Melted electrode: Too much timing, too lean, or wrong heat range

ELECTRODE MATERIAL:
- Copper: Good performance, shorter life
- Platinum: Longer life, good performance
- Iridium: Longest life, best performance
- Silver: Good performance, moderate life

REACH:
Plug reach must match head design.
- Too short: Won't reach combustion chamber
- Too long: Can hit piston or cause pre-ignition

THREAD SIZE:
Must match head threads (typically 14mm or 18mm).

TUNING WITH PLUGS:
- Change heat range if plug shows too hot/cold
- Adjust gap for ignition system capability
- Monitor plug condition regularly
- Replace based on condition, not just mileage""",
            "metadata": {
                "topic": "Spark Plug Selection and Tuning",
                "category": "tuning",
                "source": "Ignition Systems",
                "tuning_related": True,
                "telemetry_relevant": False,
                "keywords": "spark plug, heat range, gap, electrode, reading plugs, ignition, plug selection"
            }
        },
        
        # Oil Selection
        {
            "text": """Engine Oil Selection - Viscosity and Additives

OIL VISCOSITY:
Viscosity rating (e.g., 5W-30) indicates oil thickness.

- First number (5W): Cold viscosity (W = winter)
- Second number (30): Hot viscosity at 212°F

TYPICAL SELECTIONS:
- Street: 5W-30, 10W-30, 10W-40
- Performance: 10W-40, 15W-50
- Race: 20W-50, 15W-50
- Turbo: 5W-40, 10W-40 (better flow when cold)

VISCOSITY EFFECTS:
- Thinner (lower number): Better cold flow, less protection at high temp
- Thicker (higher number): Better high-temp protection, worse cold flow
- Too thin: Insufficient protection, low oil pressure
- Too thick: Poor flow, high oil pressure, more drag

OIL TYPES:
1. Conventional: Basic protection, shorter change intervals
2. Synthetic: Better protection, longer intervals, better flow
3. Synthetic blend: Mix of conventional and synthetic
4. Racing oil: High zinc content, frequent changes

ADDITIVES:
- Zinc (ZDDP): Anti-wear protection (important for flat tappet cams)
- Detergents: Keep engine clean
- Dispersants: Keep contaminants suspended
- Anti-foam: Prevent foaming
- Friction modifiers: Reduce friction

OIL PRESSURE:
Normal: 10 PSI per 1000 RPM minimum
- Idle: 20-40 PSI typical
- Running: 40-80 PSI typical
- High RPM: 60-100 PSI typical

OIL TEMPERATURE:
Optimal: 200-240°F (93-115°C)
- Too cold: Poor flow, more wear
- Too hot: Breaks down oil, loses protection
- Monitor: Oil temp gauge recommended

OIL CHANGE INTERVALS:
- Street: 3000-5000 miles (conventional), 5000-7500 (synthetic)
- Performance: 2000-3000 miles
- Race: Every event or 500-1000 miles
- Track day: Change before and after

OIL FILTER:
- Quality: Use good filter (not cheapest)
- Size: Match to engine requirements
- Change: Every oil change

BREAK-IN OIL:
- Conventional: Better for break-in (less slippery)
- High zinc: Protects during break-in
- Change: After first 20 minutes, then 100-500 miles

RACING OIL:
- High zinc: 1200-2000 PPM typical
- Frequent changes: Every event
- Viscosity: Thicker for high-RPM protection
- Additives: Optimized for racing conditions""",
            "metadata": {
                "topic": "Engine Oil Selection and Management",
                "category": "maintenance",
                "source": "Lubrication",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "engine oil, viscosity, oil pressure, oil temperature, synthetic, conventional, racing oil, ZDDP"
            }
        },
        
        # Transmission and Gearing
        {
            "text": """Transmission and Final Drive Optimization

GEAR RATIO CALCULATION:
Gear_Ratio = Input_Speed / Output_Speed

FINAL DRIVE RATIO:
Final_Drive = Ring_Gear_Teeth / Pinion_Gear_Teeth

OVERALL RATIO:
Overall_Ratio = Gear_Ratio × Final_Drive_Ratio

SPEED FROM GEAR RATIO:
Speed (mph) = (RPM × Tire_Diameter × π) / (Gear_Ratio × Final_Drive × 1056)

RPM FROM SPEED:
RPM = (Speed × Gear_Ratio × Final_Drive × 1056) / (Tire_Diameter × π)

GEAR RATIO SELECTION:

For Drag Racing:
- First gear: Very low (4.0:1 to 6.0:1) for launch
- Gears: Evenly spaced for consistent RPM drop
- Final drive: Match to track length and power band

For Road Racing:
- Gears: Optimize for track layout
- Ratios: Cover RPM range efficiently
- Final drive: Match to track speeds

RPM DROP BETWEEN GEARS:
RPM_Drop = Shift_RPM × (1 - (Next_Gear_Ratio / Current_Gear_Ratio))

Optimal: Land at peak torque RPM after shift

GEAR SPACING:
Even spacing: Each gear ratio is similar percentage change
Formula: Ratio_N = Ratio_1 × (Ratio_Last / Ratio_1)^((N-1)/(Gears-1))

TYPICAL GEAR RATIOS:
- 4-speed: 2.50, 1.50, 1.00, 0.70
- 5-speed: 2.97, 1.94, 1.34, 1.00, 0.78
- 6-speed: 3.00, 2.00, 1.50, 1.20, 1.00, 0.80

FINAL DRIVE SELECTION:
- Lower (numerically higher): Better acceleration, lower top speed
- Higher (numerically lower): Better top speed, worse acceleration
- Typical: 3.50-4.10 for street, 4.10-4.56 for performance, 4.56+ for drag

EFFECTIVE GEAR RATIO WITH TIRE CHANGE:
Effective_Ratio = Original_Ratio × (Original_Tire_Diameter / New_Tire_Diameter)

TORQUE MULTIPLICATION:
Torque_at_Wheels = Engine_Torque × Gear_Ratio × Final_Drive_Ratio

POWER LOSS:
Transmission efficiency: 85-95% typical
- Manual: 90-95% efficient
- Automatic: 85-90% efficient
- CVT: 80-85% efficient

GEAR SELECTION STRATEGY:
- Launch: Lowest gear for maximum torque multiplication
- Acceleration: Use gears to stay in power band
- Top speed: Highest gear for maximum speed
- Economy: Higher gears for lower RPM

CALCULATION EXAMPLE:
Engine: 500 lb-ft torque, 3.50:1 first gear, 3.73:1 final drive
Torque at wheels = 500 × 3.50 × 3.73 = 6,527 lb-ft
This is why low gears provide massive acceleration!""",
            "metadata": {
                "topic": "Transmission and Final Drive Optimization",
                "category": "tuning",
                "source": "Drivetrain",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "transmission, gear ratio, final drive, gear selection, torque multiplication, RPM drop, gear spacing"
            }
        },
        
        # Mechanical Fuel Injection
        {
            "text": """Mechanical Fuel Injection Tuning - High Performance

MECHANICAL FUEL INJECTION BASICS:
Mechanical systems use engine-driven pump and mechanical metering.

COMPONENTS:
1. Fuel pump: Engine-driven, high pressure
2. Metering unit: Controls fuel delivery
3. Nozzles: Inject fuel into intake
4. Fuel lines: High-pressure lines
5. Regulator: Controls system pressure

FUEL PRESSURE:
- Typical: 30-60 PSI
- Higher pressure: More fuel delivery
- Adjust: Based on power requirements

NOZZLE SELECTION:
Nozzle size determines fuel flow rate.

SIZING:
- Too small: Lean condition, power loss
- Too large: Rich condition, poor economy
- Selection: Based on engine size, power level, RPM

TYPICAL NOZZLE SIZES:
- Small engine (2.0L): 0.030-0.040"
- Medium engine (3.0-4.0L): 0.040-0.050"
- Large engine (5.0L+): 0.050-0.060"
- Race: 0.060-0.080"+

AIR-FUEL RATIO ADJUSTMENT:
- Metering unit: Adjusts fuel delivery
- Nozzle size: Affects flow rate
- Pressure: Affects flow rate
- Balance: All cylinders should be similar

TUNING PROCESS:
1. Start with baseline nozzle size
2. Test at various RPM/load points
3. Adjust metering unit for AFR
4. Fine-tune nozzle size if needed
5. Balance all cylinders
6. Verify at all operating conditions

IDLE ADJUSTMENT:
- Idle fuel: Separate adjustment
- Idle air: Throttle stop adjustment
- Balance: Smooth idle, correct AFR

WOT TUNING:
- Full throttle: Maximum fuel delivery
- AFR target: 12.5-13.2:1 for power
- Monitor: Wideband O2 sensor
- Adjust: Metering unit or nozzle size

PARTIAL THROTTLE:
- Metering unit: Controls part-throttle fuel
- Adjustment: Fine-tune for smooth operation
- AFR target: 14.0-15.0:1 for efficiency

BALANCING CYLINDERS:
- Individual nozzles: May need adjustment
- Goal: Same AFR in all cylinders
- Method: EGT or O2 sensor per cylinder
- Adjustment: Individual nozzle flow

TEMPERATURE COMPENSATION:
- Cold start: May need enrichment
- Hot engine: May need adjustment
- Ambient: May affect tuning

ADVANTAGES:
- Simple: Fewer components
- Reliable: Mechanical, no electronics
- Responsive: Direct mechanical link
- Race proven: Used in many race applications

DISADVANTAGES:
- Less precise: Harder to fine-tune
- No compensation: No automatic adjustments
- Manual tuning: Requires experience
- Limited features: No advanced strategies""",
            "metadata": {
                "topic": "Mechanical Fuel Injection Tuning",
                "category": "tuning",
                "source": "Fuel Systems",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "mechanical fuel injection, MFI, nozzle sizing, metering unit, fuel pressure, cylinder balancing"
            }
        },
        
        # Suspension Tuning
        {
            "text": """Suspension Tuning - Performance Optimization

SUSPENSION BASICS:
Suspension affects handling, traction, and ride quality.

COMPONENTS:
1. Springs: Support vehicle weight
2. Shocks/Dampers: Control spring oscillation
3. Sway bars: Control body roll
4. Alignment: Tire angles
5. Bushings: Allow movement, affect compliance

SPRING RATE:
Spring rate = Force required to compress spring 1 inch

TYPICAL VALUES:
- Street: 200-400 lb/in front, 150-300 lb/in rear
- Performance: 400-800 lb/in front, 300-600 lb/in rear
- Race: 800-1500+ lb/in front, 600-1200+ lb/in rear

SPRING SELECTION:
- Softer: Better ride, more body roll
- Stiffer: Better handling, harsher ride
- Front vs Rear: Balance affects handling characteristics

SHOCK DAMPING:
Controls how quickly suspension compresses/extends.

SETTINGS:
- Compression: How fast spring compresses
- Rebound: How fast spring extends
- Adjustable: Many performance shocks are adjustable

TYPICAL SETTINGS:
- Street: Soft compression, medium rebound
- Performance: Medium compression, medium rebound
- Race: Firm compression, firm rebound

SWAY BARS (Anti-roll bars):
Reduce body roll during cornering.

SIZING:
- Larger diameter: More roll resistance
- Front bar: Affects understeer/oversteer
- Rear bar: Affects understeer/oversteer

TYPICAL VALUES:
- Street: 0.75-1.0" front, 0.625-0.875" rear
- Performance: 1.0-1.25" front, 0.875-1.125" rear
- Race: 1.25-1.5"+ front, 1.0-1.375"+ rear

ALIGNMENT:
Tire angles affect handling and tire wear.

CAMBER:
- Negative camber: Top of tire leans in (better cornering)
- Positive camber: Top of tire leans out (rare)
- Typical: -0.5° to -2.0° for performance

CASTER:
- Positive caster: Steering axis tilted back (better stability)
- Typical: 3° to 7° for performance

TOE:
- Toe-in: Front of tires point inward
- Toe-out: Front of tires point outward
- Typical: 0° to 0.25° toe-in for street, slight toe-out for race

WEIGHT TRANSFER:
During acceleration/braking/cornering, weight shifts.

FORMULA:
Weight_Transfer = (Weight × Height × Acceleration) / Track_Width

Where:
- Weight = Vehicle weight
- Height = Center of gravity height
- Acceleration = G-force
- Track_Width = Distance between wheels

SUSPENSION TUNING FOR DRAG RACING:
- Front: Soft to allow weight transfer
- Rear: Stiff to prevent squat
- Goal: Maximum weight on rear wheels for traction

SUSPENSION TUNING FOR ROAD RACING:
- Balanced: Front and rear work together
- Stiffer: Less body roll, better handling
- Goal: Maximum grip in corners

COMMON ADJUSTMENTS:
1. Lower vehicle: Lower center of gravity
2. Stiffer springs: Less body roll
3. More damping: Better control
4. Larger sway bars: Less roll
5. More negative camber: Better cornering grip""",
            "metadata": {
                "topic": "Suspension Tuning",
                "category": "tuning",
                "source": "Chassis",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "suspension, spring rate, shock damping, sway bar, alignment, camber, caster, toe, weight transfer"
            }
        },
        
        # Weather and Environmental Effects
        {
            "text": """Weather and Environmental Effects on Performance

AIR DENSITY:
Air density affects engine power output.

CALCULATION:
Air_Density = (P × 144) / (R × T_absolute)

Where:
- P = Barometric pressure (PSIA)
- R = Gas constant (1716.5 ft-lb/slug-°R)
- T_absolute = Temperature in Rankine (°F + 459.67)

EFFECT ON POWER:
Power_Change = (Actual_Density / Standard_Density) × 100%

Standard density: 0.002377 slugs/ft³ at sea level, 59°F

TEMPERATURE EFFECTS:
- Hot air: Less dense, less power
- Cold air: More dense, more power
- Rule of thumb: ~1% power per 10°F temperature change

HUMIDITY EFFECTS:
- High humidity: Less oxygen, slightly less power
- Low humidity: More oxygen, slightly more power
- Effect: Smaller than temperature, but measurable

BAROMETRIC PRESSURE:
- High pressure: More dense air, more power
- Low pressure: Less dense air, less power
- Effect: Significant (altitude effect)

ALTITUDE EFFECTS:
- Higher altitude: Less pressure, less power
- Sea level: Maximum power
- Effect: ~3% power loss per 1000 ft elevation

DENSITY ALTITUDE:
Combines all factors into single metric.

CALCULATION:
DA = 145442.156 × (1 - ((P / 29.921) × ((T + 459.67) / 518.67))^0.234969)

EFFECT ON PERFORMANCE:
- Low DA: Better performance
- High DA: Worse performance
- Rule of thumb: ~1% power loss per 1000 ft DA

WEATHER ADAPTATION:
Tuning adjustments for conditions:

1. HOT WEATHER:
- Reduce timing: -1° per 20°F above 100°F
- May need richer AFR: Slightly richer for cooling
- Monitor IAT: Keep intake cool
- Reduce boost: If IAT too high

2. COLD WEATHER:
- Can run more timing: +1-2° possible
- May need leaner AFR: Slightly leaner
- Monitor warm-up: Ensure proper temperature
- Can run more boost: If IAT low

3. HIGH ALTITUDE:
- Reduce boost targets: Less air available
- Adjust fuel: May need less fuel
- Adjust timing: May need less timing
- Monitor: All parameters closely

4. HIGH HUMIDITY:
- Slight power reduction: ~1-2%
- May need slight timing reduction
- Monitor: For any issues

TRACK CONDITIONS:
- Hot track: Better tire grip (to a point)
- Cold track: Less tire grip
- Wet track: Significantly less grip
- Track prep: VHT improves grip dramatically

TUNING STRATEGY:
1. Baseline: Establish performance in standard conditions
2. Monitor: Track weather conditions
3. Adjust: Make tuning changes for conditions
4. Test: Verify adjustments work
5. Document: Keep records of conditions and changes""",
            "metadata": {
                "topic": "Weather and Environmental Effects",
                "category": "tuning",
                "source": "Performance Tuning",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "weather, air density, temperature, humidity, barometric pressure, altitude, density altitude, environmental effects"
            }
        },
        
        # Engine Protection Systems
        {
            "text": """Engine Protection Systems - Safety and Reliability

REV LIMITER:
Prevents engine from exceeding safe RPM.

TYPES:
1. Hard cut: Instant fuel/spark cut
2. Soft cut: Gradual reduction
3. Per-gear: Different limits per gear

SETTINGS:
- Stock engine: Factory redline
- Performance: +500-1000 RPM above stock
- Built engine: Based on components (rods, valves, etc.)
- Safety margin: 200-500 RPM below component limit

OVERBOOST PROTECTION:
Prevents boost from exceeding safe levels.

METHODS:
1. Fuel cut: Cuts fuel if boost too high
2. Wastegate dump: Opens wastegate fully
3. Throttle reduction: Reduces throttle opening
4. Timing retard: Reduces timing (less effective)

SETTINGS:
- Street: 1-2 PSI above target
- Performance: 2-3 PSI above target
- Safety: Set based on engine capability

LEAN PROTECTION:
Prevents engine from running too lean.

METHODS:
1. Fuel cut: Cuts fuel if AFR too lean
2. Timing retard: Reduces timing
3. Boost reduction: Reduces boost
4. Throttle reduction: Reduces load

SETTINGS:
- AFR threshold: 14.5:1 at WOT (typical)
- Lambda threshold: 1.0 (stoichiometric)
- Response: Immediate cut or gradual reduction

EGT PROTECTION:
Prevents exhaust gas temperature from exceeding limits.

SETTINGS:
- Maximum EGT: 1600°F (871°C) typical
- Warning: 1500°F (816°C) typical
- Response: Fuel cut, timing retard, or boost reduction

COOLANT TEMPERATURE PROTECTION:
Prevents engine from overheating.

SETTINGS:
- Maximum temp: 240°F (115°C) typical
- Warning: 220°F (104°C) typical
- Response: Reduce power, warning light, or shutdown

OIL PRESSURE PROTECTION:
Prevents engine damage from low oil pressure.

SETTINGS:
- Minimum pressure: 10 PSI per 1000 RPM
- Warning: 15 PSI per 1000 RPM typical
- Response: Reduce RPM, warning light, or shutdown

KNOCK PROTECTION:
Automatically retards timing when knock detected.

SETTINGS:
- Sensitivity: Adjust based on engine
- Retard amount: -2° to -5° per knock event
- Recovery: Gradually advance timing back
- Maximum retard: Total limit (e.g., -10°)

FUEL PRESSURE PROTECTION:
Monitors fuel system pressure.

SETTINGS:
- Minimum pressure: Based on system (40 PSI typical)
- Maximum pressure: Based on system (80 PSI typical)
- Response: Warning or fuel cut

IAT PROTECTION:
Prevents damage from hot intake air.

SETTINGS:
- Maximum IAT: 200°F (93°C) typical
- Warning: 180°F (82°C) typical
- Response: Reduce timing/boost, or warning

BEST PRACTICES:
1. Set all protections before tuning
2. Test protections to ensure they work
3. Don't disable protections (safety critical)
4. Monitor all parameters during runs
5. Adjust protections based on engine capability
6. Document protection settings

TYPICAL PROTECTION HIERARCHY:
1. Rev limit: Always active
2. Overboost: Critical for forced induction
3. Lean protection: Critical for engine safety
4. EGT protection: Important for turbo engines
5. Temperature protection: Important for all engines
6. Oil pressure: Critical for engine life""",
            "metadata": {
                "topic": "Engine Protection Systems",
                "category": "safety",
                "source": "Engine Management",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "engine protection, rev limiter, overboost protection, lean protection, EGT protection, safety systems"
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
            LOGGER.info(f"Added technical knowledge: {entry['metadata']['topic']}")
        except Exception as e:
            LOGGER.error(f"Failed to add knowledge '{entry['metadata']['topic']}': {e}")
            continue
    
    LOGGER.info(f"Additional technical knowledge complete: {count} entries added")
    return count


def main():
    """Main function."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    vector_store = VectorKnowledgeStore()
    count = add_additional_technical_knowledge(vector_store)
    print(f"Added {count} additional technical knowledge entries")
    return count


if __name__ == "__main__":
    main()

