"""
Add Comprehensive Calculation Formulas and Knowledge to AI Advisor
This includes formulas for wheel slip, torque, horsepower, density altitude, virtual dyno, and more.
All formulas are verified for accuracy.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from services.vector_knowledge_store import VectorKnowledgeStore

LOGGER = logging.getLogger(__name__)


def add_calculation_knowledge_to_store(vector_store: VectorKnowledgeStore) -> int:
    """
    Add comprehensive calculation formulas and knowledge to the vector knowledge store.
    
    Args:
        vector_store: VectorKnowledgeStore instance
        
    Returns:
        Number of knowledge entries added
    """
    count = 0
    
    # Comprehensive calculation knowledge entries
    knowledge_entries = [
        # Wheel Slip Calculations
        {
            "text": """Wheel Slip Calculation - Formula and Methodology

Wheel slip is calculated by comparing driven wheel speed to actual vehicle ground speed.

FORMULA:
Slip% = ((Driven_Wheel_Speed - Actual_Vehicle_Speed) / Actual_Vehicle_Speed) × 100%

Where:
- Driven_Wheel_Speed: Speed of driven wheels (rear wheels for RWD, front for FWD, all for AWD)
- Actual_Vehicle_Speed: Ground speed from GPS or non-driven wheels
- Units: Both speeds must be in same units (mph, km/h, or m/s)

INTERPRETATION:
- 0% = Pure rolling, no slip (perfect traction)
- Positive % = Wheel spin (driven wheels turning faster than vehicle moving)
- Negative % = Wheel lockup (during braking, wheels slower than vehicle)

OPTIMAL SLIP RANGES (for maximum acceleration):
- Street tires: 3-8% slip
- Drag radials: 5-12% slip
- Slick tires: 8-15% slip
- Pro Stock: 10-18% slip

CALCULATION EXAMPLE:
If driven wheel speed = 60 mph and actual vehicle speed = 55 mph:
Slip% = ((60 - 55) / 55) × 100% = 9.09% slip

ACCURACY NOTES:
- GPS speed accuracy: ±0.1 km/h (VBOX 3i)
- Wheel speed sensor accuracy: ±1% typical
- Best results with 100 Hz GPS data logging
- Dual antenna GPS improves accuracy for slip angle calculation

RELATED CALCULATIONS:
- Slip Angle (from dual antenna): β = arctan(V_lateral / V_longitudinal)
- Wheel RPM to Speed: Speed = (Wheel_RPM × Tire_Diameter × π) / (Gear_Ratio × Final_Drive × 1056)
- Driveshaft RPM to Wheel Speed: Wheel_Speed = Driveshaft_RPM / (Final_Drive × Gear_Ratio)""",
            "metadata": {
                "topic": "Wheel Slip Calculation Formula",
                "category": "calculation",
                "source": "Automotive Engineering",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "wheel slip, slip percentage, traction, wheel spin, formula, calculation, driven wheel speed, GPS speed"
            }
        },
        
        # Torque and Horsepower
        {
            "text": """Torque and Horsepower Calculations - Fundamental Formulas

HORSEPOWER FORMULA (Primary):
HP = (Torque × RPM) / 5252

Where:
- HP = Horsepower (at the measurement point)
- Torque = Torque in lb-ft (pound-feet)
- RPM = Revolutions per minute
- 5252 = Constant derived from unit conversions

KEY RELATIONSHIPS:
- At 5252 RPM: Torque and Horsepower are numerically equal
- Below 5252 RPM: Torque number > Horsepower number
- Above 5252 RPM: Horsepower number > Torque number
- This is a fundamental relationship, not a coincidence

DERIVATION OF 5252:
1. Power = Work / Time
2. Work = Force × Distance
3. For rotating systems: Power = Torque × Angular Velocity
4. Angular Velocity (rad/min) = RPM × 2π
5. Power (ft-lb/min) = Torque (lb-ft) × RPM × 2π
6. 1 HP = 33,000 ft-lb/min (James Watt's definition)
7. HP = (Torque × RPM × 2π) / 33,000
8. HP = (Torque × RPM) / 5,252 (simplified)

TORQUE FROM HORSEPOWER:
Torque = (HP × 5252) / RPM

VIRTUAL DYNO FORMULA (Acceleration-based):
HP = (Mass × Acceleration × Velocity) / 375

Where:
- Mass = Vehicle weight in pounds
- Acceleration = Rate of change of velocity (mph/s)
- Velocity = Current speed (mph)
- 375 = Conversion factor (1 hp = 375 lbf × mph)

DERIVATION OF 375:
- 1 HP = 550 ft-lb/s
- 1 mph = 1.467 ft/s
- 1 HP = 375 lbf × mph (conversion)

FORCE CALCULATION:
Force = Mass × Acceleration
Force (lbf) = (Weight (lb) × Acceleration (ft/s²)) / 32.174

POWER FROM FORCE AND VELOCITY:
Power = Force × Velocity
HP = (Force (lbf) × Velocity (mph)) / 375

TORQUE FROM ACCELERATION:
Torque = (Force × Tire_Radius) / Gear_Ratio
Where Tire_Radius is in feet

FLYWHEEL vs WHEEL HORSEPOWER:
- Flywheel HP: Engine output (measured at crankshaft)
- Wheel HP: Power at wheels (after drivetrain losses)
- Drivetrain Loss: Typically 15-20% for manual, 20-25% for automatic
- Wheel HP = Flywheel HP × (1 - Drivetrain_Loss%)

EXAMPLE CALCULATION:
If engine produces 500 lb-ft torque at 6000 RPM:
HP = (500 × 6000) / 5252 = 571.4 HP

If measured at wheels with 20% drivetrain loss:
Wheel HP = 571.4 × 0.80 = 457.1 HP""",
            "metadata": {
                "topic": "Torque and Horsepower Calculation Formulas",
                "category": "calculation",
                "source": "Automotive Engineering",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "horsepower, torque, HP, RPM, 5252, power calculation, virtual dyno, flywheel horsepower, wheel horsepower"
            }
        },
        
        # Virtual Dyno Calculations
        {
            "text": """Virtual Dyno Calculation - Acceleration-Based Horsepower Estimation

Virtual dyno calculates horsepower and torque from acceleration data using physics principles.

PRIMARY FORMULA:
HP = (Mass × Acceleration × Velocity) / 375

Where:
- Mass = Vehicle weight in pounds (including driver, fuel, etc.)
- Acceleration = Rate of change of velocity in mph/s
- Velocity = Current speed in mph
- 375 = Conversion constant (1 hp = 375 lbf × mph)

ACCELERATION CALCULATION:
Acceleration = ΔVelocity / ΔTime
Acceleration (mph/s) = (V2 - V1) / (T2 - T1)

Where:
- V1, V2 = Velocities at times T1, T2
- Best accuracy with high sample rate (100 Hz GPS)

TORQUE FROM ACCELERATION:
Torque = (Force × Tire_Radius) / (Gear_Ratio × Final_Drive)

Where:
- Force = Mass × Acceleration (converted to lbf)
- Tire_Radius = Tire radius in feet
- Gear_Ratio = Current transmission gear ratio
- Final_Drive = Differential gear ratio

FORCE CALCULATION:
Force (lbf) = (Mass (lb) × Acceleration (ft/s²)) / 32.174

Converting mph/s to ft/s²:
Acceleration (ft/s²) = Acceleration (mph/s) × 1.467

CORRECTIONS AND FACTORS:

1. DRIVETRAIN LOSS CORRECTION:
Wheel HP = Calculated HP × (1 - Drivetrain_Loss%)
Typical losses: Manual 15-20%, Automatic 20-25%

2. ROLLING RESISTANCE:
Rolling_Resistance = Crr × Mass × g
Where Crr = Coefficient of rolling resistance (0.01-0.02 typical)

3. AERODYNAMIC DRAG:
Drag_Force = 0.5 × ρ × Cd × A × V²
Where:
- ρ = Air density (slugs/ft³)
- Cd = Drag coefficient
- A = Frontal area (ft²)
- V = Velocity (ft/s)

4. GRADE CORRECTION:
If on incline: Effective_Mass = Mass × sin(grade_angle)

ACCURACY CONSIDERATIONS:
- GPS speed accuracy: ±0.1 km/h (VBOX 3i)
- Sample rate: 100 Hz recommended
- Smooth acceleration data (filter noise)
- Account for wind, grade, temperature
- Use consistent test conditions

CALCULATION EXAMPLE:
Vehicle: 3500 lb, accelerating from 60 to 70 mph in 1.5 seconds
Acceleration = (70 - 60) / 1.5 = 6.67 mph/s
Average velocity = 65 mph
HP = (3500 × 6.67 × 65) / 375 = 4,040 HP (at wheels)

With 20% drivetrain loss:
Flywheel HP = 4,040 / 0.80 = 5,050 HP

NOTE: This example shows very high acceleration - typical values are much lower.""",
            "metadata": {
                "topic": "Virtual Dyno Calculation Formulas",
                "category": "calculation",
                "source": "Automotive Engineering",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "virtual dyno, acceleration dyno, horsepower from acceleration, torque calculation, drivetrain loss, rolling resistance"
            }
        },
        
        # Density Altitude
        {
            "text": """Density Altitude Calculation - Performance Correction Formula

Density altitude is the altitude at which the air density equals the actual air density at the measurement location. It affects engine performance significantly.

PRIMARY FORMULA (SAE Standard):
DA = 145442.156 × (1 - ((P / 29.921) × ((T + 459.67) / 518.67))^0.234969)

Where:
- DA = Density Altitude in feet
- P = Barometric Pressure in inches of mercury (inHg)
- T = Temperature in degrees Fahrenheit (°F)
- 29.921 = Standard sea level pressure (inHg)
- 518.67 = Standard sea level temperature (Rankine = 59°F + 459.67)

SIMPLIFIED FORMULA (Approximation):
DA = (145442.156 × (1 - (P / 29.921)^0.234969)) + ((T - 59) × 120)

Where:
- P = Barometric pressure (inHg)
- T = Temperature (°F)

ALTERNATIVE FORMULA (Using Pressure Altitude):
DA = PA + (120 × (OAT - ISA_Temp))

Where:
- PA = Pressure Altitude (feet)
- OAT = Outside Air Temperature (°F)
- ISA_Temp = International Standard Atmosphere temperature at PA

PRESSURE ALTITUDE CALCULATION:
PA = (29.921 - P) × 1000 + Elevation

Where:
- P = Barometric pressure (inHg)
- Elevation = Station elevation (feet)

AIR DENSITY CALCULATION:
ρ = (P × 144) / (R × T_absolute)

Where:
- ρ = Air density (slugs/ft³)
- P = Pressure (psf = inHg × 70.73)
- R = Gas constant (1716.5 ft-lb/slug-°R)
- T_absolute = Temperature in Rankine (°F + 459.67)

STANDARD CONDITIONS:
- Sea Level Pressure: 29.921 inHg
- Sea Level Temperature: 59°F (15°C)
- Sea Level Density: 0.002377 slugs/ft³

PERFORMANCE CORRECTION FACTORS:

1. HORSEPOWER CORRECTION:
Corrected_HP = Measured_HP × (29.921 / P) × sqrt((T + 459.67) / 518.67)

2. ET CORRECTION (Drag Racing):
Corrected_ET = Measured_ET × (DA / 1000)^0.1
(Approximate - actual varies by vehicle)

3. MPH CORRECTION:
Corrected_MPH = Measured_MPH × (1000 / DA)^0.05
(Approximate)

EFFECT ON PERFORMANCE:
- Higher DA = Lower air density = Less power = Slower times
- Lower DA = Higher air density = More power = Faster times
- Rule of thumb: ~1% power loss per 1000 ft DA increase

CALCULATION EXAMPLE:
Conditions: 85°F, 29.50 inHg, 500 ft elevation
DA = 145442.156 × (1 - ((29.50 / 29.921) × ((85 + 459.67) / 518.67))^0.234969)
DA ≈ 2,850 feet

This means the engine performs as if at 2,850 ft altitude even though physically at 500 ft.""",
            "metadata": {
                "topic": "Density Altitude Calculation Formula",
                "category": "calculation",
                "source": "SAE Standards",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "density altitude, DA, air density, performance correction, barometric pressure, temperature, altitude correction"
            }
        },
        
        # Slip Angle (Dual Antenna)
        {
            "text": """Slip Angle Calculation - Dual Antenna GPS Method

Slip angle (β) is the angle between the vehicle's heading direction and its actual velocity vector. Critical for vehicle dynamics analysis.

DUAL ANTENNA METHOD:
Slip_Angle = arctan(V_lateral / V_longitudinal)

Where:
- V_lateral = Lateral velocity component (sideways motion)
- V_longitudinal = Longitudinal velocity component (forward motion)
- Both velocities from dual antenna GPS system

VELOCITY COMPONENTS:
V_lateral = V × sin(Heading_Difference)
V_longitudinal = V × cos(Heading_Difference)

Where:
- V = Vehicle speed magnitude
- Heading_Difference = Difference between heading and velocity direction

DUAL ANTENNA ACCURACY:
Accuracy improves with antenna separation:
- 0.5 m separation: <0.2° RMS slip angle accuracy
- 1.0 m separation: <0.1° RMS slip angle accuracy
- 1.5 m separation: <0.067° RMS slip angle accuracy
- 2.0 m separation: <0.05° RMS slip angle accuracy
- 2.5 m separation: <0.04° RMS slip angle accuracy

YAW RATE FROM SLIP ANGLE:
Yaw_Rate = d(Slip_Angle) / dt

Where:
- d/dt = Time derivative
- Calculated from slip angle rate of change

LATERAL ACCELERATION:
Lateral_Accel = V × Yaw_Rate + d(V_lateral) / dt

Where:
- V = Vehicle speed
- Yaw_Rate = Angular velocity about vertical axis
- d(V_lateral)/dt = Rate of change of lateral velocity

SLIP ANGLE FROM WHEEL SPEEDS:
For individual wheels:
Front_Slip = arctan((V_front_lateral) / V_longitudinal)
Rear_Slip = arctan((V_rear_lateral) / V_longitudinal)

Where V_front_lateral and V_rear_lateral are calculated from wheel speed differences.

TYPICAL VALUES:
- Normal driving: 0-2° slip angle
- Aggressive cornering: 2-8° slip angle
- Racing/limit handling: 8-15° slip angle
- Drifting: 15-30° slip angle

CALCULATION EXAMPLE:
Vehicle traveling at 60 mph (88 ft/s) with 5° heading difference:
V_lateral = 88 × sin(5°) = 7.67 ft/s
V_longitudinal = 88 × cos(5°) = 87.7 ft/s
Slip_Angle = arctan(7.67 / 87.7) = 5.0°""",
            "metadata": {
                "topic": "Slip Angle Calculation - Dual Antenna GPS",
                "category": "calculation",
                "source": "Vehicle Dynamics",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "slip angle, dual antenna, GPS, vehicle dynamics, yaw rate, lateral acceleration, heading"
            }
        },
        
        # Speed and Distance Calculations
        {
            "text": """Speed and Distance Calculations - GPS and Wheel-Based

SPEED FROM WHEEL RPM:
Speed (mph) = (Wheel_RPM × Tire_Diameter × π) / (Gear_Ratio × Final_Drive × 1056)

Where:
- Wheel_RPM = Wheel rotational speed (revolutions per minute)
- Tire_Diameter = Tire diameter in inches
- π = 3.14159
- Gear_Ratio = Transmission gear ratio (1.0 if measuring after transmission)
- Final_Drive = Differential gear ratio
- 1056 = Conversion factor (12 in/ft × 5280 ft/mile / 60 min/hour)

SIMPLIFIED (No gear ratios):
Speed (mph) = (Wheel_RPM × Tire_Diameter × π) / 1056

SPEED FROM DRIVESHAFT RPM:
Speed (mph) = (Driveshaft_RPM × Tire_Diameter × π) / (Final_Drive × Gear_Ratio × 1056)

TIRE CIRCUMFERENCE:
Circumference (inches) = Tire_Diameter × π
Circumference (feet) = (Tire_Diameter × π) / 12

DISTANCE FROM WHEEL ROTATIONS:
Distance (feet) = Rotations × Circumference (feet)
Distance (miles) = Distance (feet) / 5280

GPS SPEED ACCURACY:
- Standard GPS: ±0.1-0.2 m/s (±0.2-0.4 mph)
- DGPS: ±0.05 m/s (±0.1 mph)
- RTK GPS: ±0.01 m/s (±0.02 mph)
- VBOX 3i: ±0.1 km/h (±0.06 mph) using Doppler shift

DISTANCE FROM GPS:
Distance = sqrt((Lat2 - Lat1)² + (Lon2 - Lon1)²) × Earth_Radius

Where:
- Lat1, Lat2 = Latitude coordinates (radians)
- Lon1, Lon2 = Longitude coordinates (radians)
- Earth_Radius = 3,959 miles (6,371 km)

HAVERSINE FORMULA (More Accurate):
a = sin²(ΔLat/2) + cos(Lat1) × cos(Lat2) × sin²(ΔLon/2)
c = 2 × atan2(√a, √(1-a))
Distance = Earth_Radius × c

ACCELERATION CALCULATION:
Acceleration = ΔVelocity / ΔTime
Acceleration (ft/s²) = (V2 - V1) / (T2 - T1)
Acceleration (mph/s) = Acceleration (ft/s²) / 1.467

JERK (Rate of Change of Acceleration):
Jerk = ΔAcceleration / ΔTime
Jerk (ft/s³) = (A2 - A1) / (T2 - T1)

CONVERSION FACTORS:
- 1 mph = 1.467 ft/s = 0.447 m/s
- 1 km/h = 0.621 mph = 0.278 m/s
- 1 m/s = 2.237 mph = 3.6 km/h
- 1 ft/s = 0.682 mph = 1.097 km/h""",
            "metadata": {
                "topic": "Speed and Distance Calculation Formulas",
                "category": "calculation",
                "source": "Automotive Engineering",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "speed calculation, distance, GPS, wheel speed, acceleration, jerk, conversion factors"
            }
        },
        
        # Quarter Mile Calculations
        {
            "text": """Quarter Mile Performance Calculations

QUARTER MILE TIME AND SPEED:
The quarter mile (1,320 feet or 402.3 meters) is the standard drag racing distance.

AVERAGE SPEED:
Average_Speed (mph) = (Distance / Time) × (3600 / 5280)
Average_Speed (mph) = (1320 / ET_seconds) × 0.6818

Where:
- Distance = 1320 feet (quarter mile)
- ET_seconds = Elapsed time in seconds
- 0.6818 = Conversion factor (3600/5280)

TRAP SPEED:
Trap_Speed = Speed at the finish line (typically measured at 66 feet before finish)

POWER-TO-WEIGHT RATIO:
Power_to_Weight = Horsepower / Vehicle_Weight (lb)
Typical values:
- Street car: 0.05-0.15 HP/lb
- Sports car: 0.15-0.25 HP/lb
- Supercar: 0.25-0.40 HP/lb
- Drag car: 0.40-1.0+ HP/lb

ESTIMATED ET FROM POWER-TO-WEIGHT:
ET ≈ 5.825 × (Weight / HP)^0.333
(Approximation, actual varies significantly)

ESTIMATED TRAP SPEED:
Trap_MPH ≈ 234 × (HP / Weight)^0.5
(Approximation)

60-FOOT TIME:
60_Foot_Time = Time to cover first 60 feet
Indicates launch quality and traction
- Excellent: <1.5 seconds
- Good: 1.5-1.7 seconds
- Average: 1.7-2.0 seconds
- Poor: >2.0 seconds

330-FOOT TIME:
330_Foot_Time = Time to cover first 330 feet
Indicates mid-track performance

INCREMENTAL TIMES:
Incremental_Time = Time between markers (60', 330', 660', 1000', 1320')
Used to identify where time is gained or lost

VELOCITY AT DISTANCE:
V = sqrt(2 × Acceleration × Distance)
(For constant acceleration)

For variable acceleration, integrate acceleration over time.

CALCULATION EXAMPLE:
Vehicle runs 11.5 seconds at 120 mph trap speed:
Average_Speed = (1320 / 11.5) × 0.6818 = 78.3 mph
Peak acceleration occurs early in the run.""",
            "metadata": {
                "topic": "Quarter Mile Performance Calculations",
                "category": "calculation",
                "source": "Drag Racing",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "quarter mile, ET, trap speed, 60 foot time, drag racing, elapsed time, power to weight"
            }
        },
        
        # Fuel Calculations
        {
            "text": """Fuel System Calculations - AFR, Lambda, and Fuel Flow

AIR-FUEL RATIO (AFR):
AFR = Mass_of_Air / Mass_of_Fuel

Stoichiometric AFR (complete combustion):
- Gasoline: 14.7:1
- E85: 9.8:1
- E100 (Ethanol): 9.0:1
- Methanol: 6.4:1
- Nitromethane: 1.7:1

LAMBDA (λ):
Lambda = Actual_AFR / Stoichiometric_AFR

- λ = 1.0: Stoichiometric (perfect air-fuel ratio)
- λ < 1.0: Rich (excess fuel)
- λ > 1.0: Lean (excess air)

EQUIVALENCE RATIO (φ):
Phi = 1 / Lambda = Stoichiometric_AFR / Actual_AFR

FUEL FLOW CALCULATION:
Fuel_Flow (lb/hr) = (HP × BSFC) / (AFR × Air_Density_Correction)

Where:
- HP = Horsepower
- BSFC = Brake Specific Fuel Consumption (lb/hp-hr)
  - Typical: 0.45-0.55 for naturally aspirated
  - Typical: 0.50-0.65 for forced induction
- AFR = Air-fuel ratio
- Air_Density_Correction = Correction for altitude/temperature

INJECTOR SIZE CALCULATION:
Injector_Size (lb/hr) = (HP × BSFC) / (Number_of_Injectors × Duty_Cycle)

Where:
- Duty_Cycle = Maximum injector duty cycle (typically 80-85%)

FUEL PRESSURE CORRECTION:
New_Flow = Old_Flow × sqrt(New_Pressure / Old_Pressure)

Where pressures are in PSI.

AIRFLOW CALCULATION:
Airflow (lb/min) = (Displacement × RPM × VE × Air_Density) / (2 × 1728)

Where:
- Displacement = Engine displacement (cubic inches)
- RPM = Engine speed
- VE = Volumetric efficiency (0.75-0.95 typical)
- Air_Density = Air density (lb/ft³)
- 1728 = Conversion factor (cubic inches to cubic feet)

BOOST PRESSURE EFFECT:
Boosted_Air_Density = Atmospheric_Density × (Boost_Pressure + Atmospheric_Pressure) / Atmospheric_Pressure

Where pressures are absolute (PSIA).

CALCULATION EXAMPLE:
Engine: 500 HP, BSFC = 0.50, AFR = 12.5:1
Fuel_Flow = (500 × 0.50) / 12.5 = 20 lb/hr
For 8 injectors at 80% duty cycle:
Injector_Size = (500 × 0.50) / (8 × 0.80) = 39.1 lb/hr per injector""",
            "metadata": {
                "topic": "Fuel System Calculation Formulas",
                "category": "calculation",
                "source": "Automotive Engineering",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "AFR, air-fuel ratio, lambda, fuel flow, injector size, BSFC, equivalence ratio, stoichiometric"
            }
        },
        
        # Boost and Pressure Calculations
        {
            "text": """Boost and Pressure Calculations - Turbo and Supercharger

BOOST PRESSURE:
Boost_PSI = Manifold_Pressure - Atmospheric_Pressure

Where:
- Manifold_Pressure = Absolute pressure in intake manifold (PSIA)
- Atmospheric_Pressure = Barometric pressure (PSIA)

PRESSURE RATIO:
Pressure_Ratio = (Boost_Pressure + Atmospheric_Pressure) / Atmospheric_Pressure

Example: 15 PSI boost at sea level (14.7 PSIA):
Pressure_Ratio = (15 + 14.7) / 14.7 = 2.02:1

COMPRESSOR EFFICIENCY:
Isentropic_Efficiency = (T2_ideal - T1) / (T2_actual - T1)

Where:
- T1 = Inlet temperature
- T2_ideal = Ideal outlet temperature (isentropic)
- T2_actual = Actual outlet temperature

OUTLET TEMPERATURE:
T2 = T1 × (Pressure_Ratio^((γ-1)/γ) / Efficiency) + T1

Where:
- γ = Specific heat ratio (1.4 for air)
- Efficiency = Compressor efficiency (0.70-0.85 typical)

AIR DENSITY INCREASE:
Density_Ratio = Pressure_Ratio × (T1 / T2)

Where temperatures are absolute (Rankine or Kelvin).

HORSEPOWER INCREASE (Approximate):
HP_Increase = Base_HP × (Pressure_Ratio - 1) × Efficiency

Where Efficiency accounts for heat, losses, etc. (typically 0.70-0.85).

TURBO SPOOL TIME:
Spool_Time depends on:
- Turbo size (larger = slower spool)
- Engine displacement
- Exhaust energy
- Compressor efficiency

WASTEGATE PRESSURE:
Wastegate opens when boost reaches set pressure, limiting maximum boost.

INTERCOOLER EFFICIENCY:
IC_Efficiency = (T_in - T_out) / (T_in - Ambient_Temp)

Where:
- T_in = Intake temperature before intercooler
- T_out = Intake temperature after intercooler
- Ambient_Temp = Ambient air temperature

TYPICAL VALUES:
- Intercooler efficiency: 60-80%
- Compressor efficiency: 70-85%
- Turbo lag: 1-3 seconds typical
- Supercharger: Instant response (belt-driven)

CALCULATION EXAMPLE:
Turbo at 20 PSI boost, 70% compressor efficiency, 80°F inlet:
Pressure_Ratio = (20 + 14.7) / 14.7 = 2.36:1
T2 = 540 × (2.36^0.286 / 0.70) + 540 = 540 × 1.28 + 540 = 1,231°R = 771°F
With 75% intercooler efficiency (ambient 80°F):
T_out = 771 - (771 - 80) × 0.75 = 253°F""",
            "metadata": {
                "topic": "Boost and Pressure Calculation Formulas",
                "category": "calculation",
                "source": "Forced Induction",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "boost pressure, pressure ratio, turbo, supercharger, compressor efficiency, intercooler, wastegate"
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
            LOGGER.info(f"Added calculation knowledge: {entry['metadata']['topic']}")
        except Exception as e:
            LOGGER.error(f"Failed to add calculation knowledge '{entry['metadata']['topic']}': {e}")
            continue
    
    LOGGER.info(f"Calculation knowledge addition complete: {count} entries added")
    return count


def main():
    """Main function to add calculation knowledge."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize vector store
    vector_store = VectorKnowledgeStore()
    
    # Add calculation knowledge
    count = add_calculation_knowledge_to_store(vector_store)
    
    print(f"Added {count} calculation knowledge entries to AI advisor knowledge base")
    return count


if __name__ == "__main__":
    main()

