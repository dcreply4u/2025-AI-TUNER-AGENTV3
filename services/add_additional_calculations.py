"""
Add Additional Calculation Formulas - Extended Knowledge Base
Additional formulas for BSFC, volumetric efficiency, tire calculations, and more.
"""

from __future__ import annotations

import logging
from services.vector_knowledge_store import VectorKnowledgeStore

LOGGER = logging.getLogger(__name__)


def add_additional_calculations(vector_store: VectorKnowledgeStore) -> int:
    """Add additional calculation formulas."""
    count = 0
    
    knowledge_entries = [
        # BSFC and Efficiency
        {
            "text": """Brake Specific Fuel Consumption (BSFC) and Efficiency Calculations

BSFC DEFINITION:
BSFC = Fuel_Consumption (lb/hr) / Brake_Horsepower

Where:
- Fuel_Consumption = Fuel flow rate in pounds per hour
- Brake_Horsepower = Power output at crankshaft

TYPICAL BSFC VALUES:
- Naturally Aspirated Gasoline: 0.45-0.55 lb/hp-hr
- Turbocharged Gasoline: 0.50-0.65 lb/hp-hr
- Supercharged Gasoline: 0.55-0.70 lb/hp-hr
- Diesel: 0.35-0.45 lb/hp-hr
- Lower BSFC = More efficient engine

THERMAL EFFICIENCY:
Thermal_Efficiency = (2545 / (BSFC × Fuel_Heating_Value)) × 100%

Where:
- 2545 = Conversion factor (BTU/hp-hr)
- Fuel_Heating_Value = BTU/lb
  - Gasoline: ~18,500 BTU/lb
  - E85: ~12,500 BTU/lb
  - Methanol: ~9,500 BTU/lb

VOLUMETRIC EFFICIENCY (VE):
VE = (Actual_Airflow / Theoretical_Airflow) × 100%

Theoretical_Airflow = (Displacement × RPM × Air_Density) / (2 × 1728)

Where:
- Displacement = Engine displacement (cubic inches)
- RPM = Engine speed
- Air_Density = Air density (lb/ft³)
- 1728 = Conversion (cubic inches to cubic feet)
- Factor of 2 accounts for 4-stroke cycle

TYPICAL VE VALUES:
- Naturally Aspirated: 75-95%
- Turbocharged: 100-150% (boosted)
- Supercharged: 100-180% (boosted)
- Race engines: 100-110% (naturally aspirated)

AIRFLOW FROM VE:
Actual_Airflow = Theoretical_Airflow × (VE / 100)

FUEL REQUIREMENT FROM AIRFLOW:
Fuel_Flow = (Airflow / AFR) × Fuel_Density_Correction

Where AFR is the target air-fuel ratio.""",
            "metadata": {
                "topic": "BSFC and Efficiency Calculations",
                "category": "calculation",
                "source": "Engine Performance",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "BSFC, brake specific fuel consumption, thermal efficiency, volumetric efficiency, VE, airflow"
            }
        },
        
        # Tire Calculations
        {
            "text": """Tire Size and Diameter Calculations

TIRE SIZE NOTATION:
Example: 275/60R15
- 275 = Section width in millimeters
- 60 = Aspect ratio (sidewall height as % of width)
- R = Radial construction
- 15 = Rim diameter in inches

TIRE DIAMETER CALCULATION:
Tire_Diameter (inches) = (2 × Sidewall_Height) + Rim_Diameter

Sidewall_Height (inches) = (Section_Width × Aspect_Ratio) / (25.4 × 100)

Where:
- Section_Width = Tire width in mm
- Aspect_Ratio = Percentage (e.g., 60 = 60%)
- 25.4 = mm to inches conversion
- Rim_Diameter = Rim diameter in inches

SIMPLIFIED:
Tire_Diameter = Rim_Diameter + (2 × (Width × Aspect_Ratio / 2540))

TIRE CIRCUMFERENCE:
Circumference (inches) = Tire_Diameter × π
Circumference (feet) = (Tire_Diameter × π) / 12
Circumference (meters) = (Tire_Diameter × 0.0254 × π)

REVOLUTIONS PER MILE:
Revolutions_per_Mile = 5280 / Circumference (feet)
Revolutions_per_Mile = 63360 / Circumference (inches)

SPEED FROM TIRE SIZE AND RPM:
Speed (mph) = (RPM × Tire_Diameter × π) / (Gear_Ratio × Final_Drive × 1056)

RPM FROM SPEED:
RPM = (Speed × Gear_Ratio × Final_Drive × 1056) / (Tire_Diameter × π)

TIRE GROWTH AT SPEED:
Tire_Diameter_At_Speed = Static_Diameter × (1 + Growth_Factor × Speed²)

Where:
- Growth_Factor ≈ 0.00001-0.00002 per (mph)²
- Typical growth: 0.1-0.3 inches at high speed

EFFECTIVE GEAR RATIO:
Effective_Ratio = Gear_Ratio × (Original_Tire_Diameter / New_Tire_Diameter)

CALCULATION EXAMPLE:
Tire: 275/60R15
Sidewall = (275 × 60) / 2540 = 6.496 inches
Diameter = (2 × 6.496) + 15 = 27.992 inches
Circumference = 27.992 × π = 87.96 inches = 7.33 feet
Revolutions per mile = 5280 / 7.33 = 720.3 rev/mile""",
            "metadata": {
                "topic": "Tire Size and Diameter Calculations",
                "category": "calculation",
                "source": "Automotive Engineering",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "tire diameter, tire size, aspect ratio, circumference, revolutions per mile, effective gear ratio"
            }
        },
        
        # G-Force and Acceleration
        {
            "text": """G-Force and Acceleration Calculations

G-FORCE DEFINITION:
G-Force = Acceleration / Standard_Gravity

Where:
- Acceleration = Rate of change of velocity (ft/s² or m/s²)
- Standard_Gravity = 32.174 ft/s² (9.80665 m/s²)

LONGITUDINAL G-FORCE (Acceleration/Braking):
Longitudinal_G = Acceleration (ft/s²) / 32.174

From speed data:
Longitudinal_G = (ΔVelocity / ΔTime) / 32.174

Where:
- ΔVelocity = Change in velocity (ft/s)
- ΔTime = Time interval (seconds)

LATERAL G-FORCE (Cornering):
Lateral_G = (Velocity²) / (Radius × 32.174)

Where:
- Velocity = Speed (ft/s)
- Radius = Turn radius (feet)

From lateral acceleration:
Lateral_G = Lateral_Acceleration (ft/s²) / 32.174

COMBINED G-FORCE:
Combined_G = sqrt(Longitudinal_G² + Lateral_G²)

VERTICAL G-FORCE (Bumps/Jumps):
Vertical_G = Vertical_Acceleration / 32.174

ACCELERATION FROM G-FORCE:
Acceleration (ft/s²) = G-Force × 32.174
Acceleration (mph/s) = G-Force × 21.94

TYPICAL VALUES:
- Street car acceleration: 0.3-0.5 G
- Sports car acceleration: 0.6-0.8 G
- Supercar acceleration: 0.8-1.0 G
- Drag car acceleration: 1.0-1.5 G
- F1 car cornering: 4-6 G
- Street car cornering: 0.8-1.2 G

FORCE FROM G-FORCE:
Force (lbf) = Mass (lb) × G-Force

POWER FROM G-FORCE:
Power = (Mass × G-Force × Velocity) / 550

Where:
- Mass = Vehicle weight (lb)
- G-Force = Longitudinal G
- Velocity = Speed (ft/s)
- 550 = Conversion (ft-lb/s to HP)

CALCULATION EXAMPLE:
Vehicle: 3500 lb, accelerating at 0.8 G, speed 60 mph (88 ft/s)
Force = 3500 × 0.8 = 2,800 lbf
Power = (3500 × 0.8 × 88) / 550 = 448 HP""",
            "metadata": {
                "topic": "G-Force and Acceleration Calculations",
                "category": "calculation",
                "source": "Physics",
                "tuning_related": False,
                "telemetry_relevant": True,
                "keywords": "G-force, acceleration, lateral G, longitudinal G, cornering, braking, physics"
            }
        },
        
        # Engine Displacement
        {
            "text": """Engine Displacement and Compression Ratio Calculations

DISPLACEMENT CALCULATION:
Displacement = (π / 4) × Bore² × Stroke × Number_of_Cylinders

Where:
- Bore = Cylinder diameter (inches or mm)
- Stroke = Piston travel distance (inches or mm)
- Number_of_Cylinders = Engine cylinder count

CONVERSION:
- Cubic inches to liters: CI × 0.016387 = Liters
- Liters to cubic inches: Liters × 61.024 = CI

COMPRESSION RATIO:
CR = (Swept_Volume + Clearance_Volume) / Clearance_Volume

Where:
- Swept_Volume = Displacement per cylinder
- Clearance_Volume = Volume at TDC (top dead center)

Swept_Volume = (π / 4) × Bore² × Stroke

Clearance_Volume = (π / 4) × Bore² × (Deck_Height + Head_Volume + Piston_Dish)

DYNAMIC COMPRESSION RATIO:
DCR accounts for valve timing and considers when intake valve closes.

DCR = (Swept_Volume_After_IVC + Clearance_Volume) / Clearance_Volume

Where IVC = Intake Valve Closing point.

TYPICAL VALUES:
- Street engine: 8:1 to 10:1 CR
- Performance: 10:1 to 12:1 CR
- Race (pump gas): 11:1 to 12.5:1 CR
- Race (race fuel): 13:1 to 15:1+ CR

COMPRESSION PRESSURE:
Compression_Pressure = Atmospheric_Pressure × CR^γ

Where:
- γ = Specific heat ratio (1.3-1.4 for air-fuel mixture)
- Typical: 150-200 PSI for 10:1 CR

CALCULATION EXAMPLE:
Engine: 4.030" bore, 3.750" stroke, 8 cylinders
Displacement = (π / 4) × 4.030² × 3.750 × 8
Displacement = 0.7854 × 16.24 × 3.750 × 8 = 382.7 cubic inches
Displacement = 382.7 × 0.016387 = 6.27 liters""",
            "metadata": {
                "topic": "Engine Displacement and Compression Calculations",
                "category": "calculation",
                "source": "Engine Design",
                "tuning_related": True,
                "telemetry_relevant": False,
                "keywords": "displacement, compression ratio, bore, stroke, swept volume, clearance volume, dynamic compression"
            }
        },
        
        # Timing and Shift Points
        {
            "text": """Shift Point and Timing Calculations

OPTIMAL SHIFT POINT:
Shift at peak horsepower RPM, land at peak torque RPM after shift.

Shift_RPM = Peak_HP_RPM
Land_RPM = Shift_RPM / Next_Gear_Ratio × Current_Gear_Ratio

Where gear ratios are relative (e.g., 2nd/3rd ratio).

POWER LOSS FROM EARLY SHIFT:
If shifting before peak HP, power drops immediately.

POWER LOSS FROM LATE SHIFT:
If shifting after peak HP, engine operates in lower power range.

TYPICAL STRATEGY:
- Street: Shift at peak HP or slightly after
- Drag racing: Shift at peak HP, sometimes slightly before to account for shift time
- Road racing: Shift at peak HP for maximum acceleration

TIME TO SHIFT:
Shift_Time = Time to disengage clutch + Time to engage next gear
Typical: 0.1-0.3 seconds for manual, 0.05-0.15 for automatic

RPM DROP DURING SHIFT:
RPM_Drop = Shift_RPM × (1 - (Next_Gear_Ratio / Current_Gear_Ratio))

IDEAL GEAR RATIOS:
For even power delivery, gear ratios should be evenly spaced:
Ideal_Ratio = (First_Ratio / Last_Ratio)^(1 / (Number_of_Gears - 1))

60-FOOT TIME OPTIMIZATION:
Launch_RPM = RPM where torque × gear ratio is maximum
Typically: Peak torque RPM or slightly above

TRACTION LIMITED LAUNCH:
If wheel slip > optimal, reduce launch RPM or throttle.

CALCULATION EXAMPLE:
Peak HP at 6500 RPM, peak torque at 4500 RPM
2nd gear ratio: 2.10, 3rd gear ratio: 1.50
Shift at 6500 RPM
Land RPM = 6500 / 1.50 × 2.10 = 9,100 RPM (over-rev!)
Better: Shift earlier or use different gear ratios.""",
            "metadata": {
                "topic": "Shift Point and Timing Calculations",
                "category": "calculation",
                "source": "Performance Tuning",
                "tuning_related": True,
                "telemetry_relevant": True,
                "keywords": "shift point, shift RPM, gear ratio, peak horsepower, peak torque, launch RPM, 60 foot"
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
            LOGGER.info(f"Added additional calculation: {entry['metadata']['topic']}")
        except Exception as e:
            LOGGER.error(f"Failed to add calculation '{entry['metadata']['topic']}': {e}")
            continue
    
    LOGGER.info(f"Additional calculations complete: {count} entries added")
    return count


def main():
    """Main function."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    vector_store = VectorKnowledgeStore()
    count = add_additional_calculations(vector_store)
    print(f"Added {count} additional calculation entries")
    return count


if __name__ == "__main__":
    main()

