"""
Add Dyno Technical Information and Formulas to Knowledge Base
Extracts technical information and formulas from dyno testing documentation,
disregarding vendor-specific information.
"""

import logging
from services.vector_knowledge_store import VectorKnowledgeStore
from services.knowledge_base_manager import KnowledgeBaseManager
from services.knowledge_base_file_manager import KnowledgeBaseFileManager
from typing import Dict, Any, List

LOGGER = logging.getLogger(__name__)

ARTICLE_URL = "https://www.rbracing-rsr.com/downloads/dynojet.pdf"
ARTICLE_TITLE = "Dyno Technical Information - Formulas and Physics"
ARTICLE_TOPIC = "Dyno Testing - Technical"

# Technical content extracted from the PDF (vendor-specific info removed)
DYNO_TECHNICAL_CONTENT = [
    {
        "title": "How Horsepower is Determined and Calculated",
        "content": """Horsepower cannot be measured directly - it must be calculated. You can measure torque, revolutions per minute, and acceleration, but you cannot measure horsepower. It is always derived by measuring something else.

**Definition:**
Horsepower is the ability to accomplish a specific amount of work in a given amount of time, such as moving a race car down a quarter mile track in 10 seconds. Torque alone accomplishes no work - it is only a force. When a force (torque) is applied to an object and displacement of the object (movement) occurs, work is performed. Power is the rate of performing work, expressed as the time derivative of work.

**Fundamental Equation:**
Horsepower = (Torque × RPM) / 5252

**Where 5252 comes from:**
- One horsepower is defined as 33,000 pound-feet of work per minute
- Or: 550 pounds lifted one foot in one second
- The constant 5252 is derived from: 33,000 / (2 × π) = 5252
- At 5252 RPM, torque and horsepower are equal
- Below 5252 RPM: torque value is greater than horsepower value
- Above 5252 RPM: horsepower value is greater than torque value

**Key Point:** The physics behind this did not come from any dyno manufacturer - it came from James Watt, who invented the steam engine and needed a way to market his engines by comparing them to the work of horses.""",
        "keywords": ["horsepower", "torque", "RPM", "5252", "power calculation", "work", "force", "physics", "James Watt"],
        "topic": "Dyno Testing - Physics"
    },
    {
        "title": "Chassis Dyno Types and Power Calculation",
        "content": """There are generally two types of chassis dynamometers:

**1. Inertia-Only Dynos (Accelerometers):**
- Can only measure a rate of acceleration of a known mass
- Sometimes called "inertia-only dynos" or "accelerometers"
- Compute power based on acceleration of a fixed mass (the roller/drum)

**2. Load-Bearing Dynos:**
- Can measure acceleration of a known mass
- Plus have some type of load device (usually an eddy current Power Absorption Unit or fluid brake)
- Can perform loaded tests and steady-state tuning

**Fundamental Physics:**
The fundamental physics in all dynamometer types must correlate to the basic horsepower equation: HP = (Torque × RPM) / 5252. This equation must be used in some form or another to compute the correct horsepower.

**Power Equation for Chassis Dynos:**
InertiaPower + DynoLosses + AbsorberPower = WheelPower

**Inertia Power Calculation:**
InertiaPower = (InertialMass × Acceleration(in G's) × RollSpeed) / 375

Where:
- Roll speed displays as miles per hour
- The constant 375 converts units: 1 hp = 375 lbf × mph
- Inertia times acceleration is the force (torque) applied to the roll
- This equation is derived from the basic horsepower equation

**Key Point:** The fundamental physics applies regardless of dynamometer manufacturer.""",
        "keywords": ["inertia dyno", "load-bearing dyno", "eddy current", "PAU", "power absorption", "inertia power", "acceleration", "dyno losses"],
        "topic": "Dyno Testing - Types and Calculations"
    },
    {
        "title": "Dyno Losses and Friction",
        "content": """Dyno losses are the power consumed by the dynamometer itself during operation.

**Types of Dyno Losses:**
1. **Frictional Losses:** Occur when rotating components move in their bearings
2. **Windage Losses:** Occur as components spin through the air
3. **Other Mechanical Losses:** Any power consumed by the dyno's own operation

**Why They Matter:**
These losses consume some of the vehicle power applied to the rolls during the test. To properly compute power applied to the rolls, we must add this lost power to the measured power. Nothing is friction-free, and certainly not dynamometer rolls.

**Important:** When comparing dyno results, understanding how different dynos account for (or don't account for) these losses is critical. Some dynos subtract losses, some add them, and some ignore them entirely, which can lead to significant differences in reported power numbers.""",
        "keywords": ["dyno losses", "friction", "windage", "mechanical losses", "bearing friction", "power consumption"],
        "topic": "Dyno Testing - Losses"
    },
    {
        "title": "Inertia Mass and Acceleration Measurement",
        "content": """In an inertia-only dyno, power is computed by measuring the force moving the rolls.

**Acceleration Measurement:**
- An acceleration value is derived by comparing the velocity of the surface of the rolls from one revolution to another
- Some dynos do this comparison many times during one revolution to increase accuracy
- Others may only do this once per revolution (less accurate)

**Equivalent Inertia Mass:**
- The software must be provided with a known value of equivalent inertia mass (the roll)
- This value is derived through a very thorough calibration process
- For emission testing dynos, this process was certified
- You must generally trust that these numbers are valid, as there's no simple way to prove otherwise

**Calculation:**
The inertia power calculation is based on two measurements:
1. Roll speed in mph
2. Acceleration in mph per second, or G's

**Formula:**
InertiaPower = (InertialMass × Acceleration × RollSpeed) / 375

**Key Point:** The accuracy of the acceleration measurement and the calibration of the inertia mass directly affect the accuracy of power calculations.""",
        "keywords": ["inertia mass", "acceleration", "calibration", "equivalent mass", "roll speed", "velocity", "measurement accuracy"],
        "topic": "Dyno Testing - Inertia Measurement"
    },
    {
        "title": "Tire and Wheel Effects on Dyno Results",
        "content": """Changes to tire and wheel combinations can significantly affect dyno power measurements, especially on inertia dynos.

**Factors That Affect Results:**
1. **Tire Diameter:** Affects gearing and speed calculations
   - Smaller diameter = higher effective gear ratio = different acceleration rate
   - Speed in mph changes for any given engine RPM

2. **Wheel/Tire Weight (Inertia):** Affects acceleration rate
   - Heavier wheel/tire = more inertia = slower acceleration
   - Lighter wheel/tire = less inertia = faster acceleration

3. **Combined Effects:**
   - Smaller diameter tire may accelerate faster (better gearing)
   - But heavier tire may slow acceleration (more inertia)
   - These can offset each other, making results confusing

**Example from Testing:**
- Test with 25.6" worn tire vs. 25.2" new tire
- New tire was smaller (better gearing) but heavier (more inertia)
- Acceleration rates appeared similar, but power curves were different
- The difference came from the speed (mph) component in the calculation, not just acceleration

**Important:** When comparing dyno results, ensure the same tire/wheel combination is used. Even small differences in diameter or weight can cause significant variations in reported power, especially at higher speeds where wheel inertia has greater effect.

**Step Testing:**
Performing step tests (loaded tests) removes the effects of wheel inertia, allowing for more accurate comparisons between different tire/wheel combinations.""",
        "keywords": ["tire diameter", "wheel weight", "inertia", "gearing", "acceleration", "step test", "loaded test", "tire effects"],
        "topic": "Dyno Testing - Tire Effects"
    },
    {
        "title": "Power Equation Derivation - The 5252 Constant",
        "content": """The constant 5252 in the horsepower equation comes from unit conversions and fundamental definitions.

**Derivation:**

1. **Definition of Power:**
   Power = (Force × Distance) / Time

2. **Distance Per Revolution:**
   DistancePerRevolution = 2 × π × Radius

3. **Distance Per Minute:**
   DistancePerMinute = Radius × 2 × π × RPM

4. **Torque Definition:**
   Torque = Force × Radius
   Therefore: Force = Torque / Radius

5. **Combining Equations:**
   Power = (Torque / Radius) × (RPM × Radius × 2 × π)
   Power = Torque × RPM × 2 × π

6. **Converting to Horsepower:**
   Since 1 HP = 33,000 lb-ft per minute:
   HP = (Torque × RPM × 2 × π) / 33,000
   
   Since 2 × π = 6.2832:
   HP = (Torque × RPM × 6.2832) / 33,000
   
   Since 33,000 / 6.2832 = 5,252:
   HP = (Torque × RPM) / 5,252

**Key Points:**
- At 5252 RPM, torque and horsepower are numerically equal
- Below 5252 RPM: torque number is greater than horsepower number
- Above 5252 RPM: horsepower number is greater than torque number
- This is a fundamental relationship based on the definition of horsepower, not a dyno manufacturer's choice""",
        "keywords": ["5252", "power equation", "derivation", "torque", "RPM", "horsepower", "constant", "unit conversion"],
        "topic": "Dyno Testing - Physics"
    },
    {
        "title": "Why Dyno Numbers Don't Match Between Different Dynos",
        "content": """There are fundamental reasons why power numbers from different dynos will never match exactly, even when testing the same vehicle.

**Primary Reasons:**

1. **Different Calculation Methods:**
   - Some dynos account for losses, some don't
   - Some add losses, some subtract them
   - Different methods of measuring acceleration
   - Different calibration procedures

2. **Different Inertia Masses:**
   - Each dyno has different roll mass/inertia
   - Calibration of equivalent inertia mass varies
   - This directly affects power calculations

3. **Different Loss Accounting:**
   - How losses are measured and applied varies
   - Some dynos ignore losses entirely
   - This can cause significant differences

4. **Measurement Frequency:**
   - Some dynos measure acceleration many times per revolution
   - Others measure once per revolution
   - More measurements = better accuracy

5. **Tire/Wheel Effects:**
   - Different tire diameters affect results
   - Different wheel weights affect inertia
   - These effects are more pronounced on inertia dynos

**Important Concepts:**
- A dyno is a tool for comparison, not absolute measurement
- Repeatability is more important than absolute accuracy
- Focus on changes (before/after modifications) rather than absolute numbers
- Learn to use your dyno as a tuning tool, not a bragging rights generator

**Bottom Line:** If you're using a different type of dyno than another shop, your numbers will not match. This is expected and normal due to fundamental differences in how power is calculated and how losses are accounted for.""",
        "keywords": ["dyno comparison", "power numbers", "calculation methods", "losses", "inertia", "repeatability", "accuracy"],
        "topic": "Dyno Testing - Comparison"
    },
    {
        "title": "Using a Dyno as a Tuning Tool",
        "content": """A dynamometer is a tool for tuning and comparison, not just for measuring absolute power numbers.

**Best Practices:**

1. **Focus on Repeatability:**
   - A good dyno should produce repeatable results
   - If it repeats well, it's a good tool
   - Absolute numbers matter less than consistency

2. **Learn Your Dyno:**
   - Understand how it calculates power
   - Learn which testing methods work best for your applications
   - Know how to interpret the data

3. **Proper Calibration:**
   - Keep your dyno calibrated
   - Follow manufacturer's calibration procedures
   - Regular maintenance ensures accuracy

4. **Testing Methods:**
   - Learn which methods work best for different applications
   - Inertia tests vs. loaded tests
   - Step testing for steady-state tuning
   - Full passes for overall performance

5. **Data Interpretation:**
   - Focus on changes, not absolute numbers
   - Compare before/after modifications
   - Look for trends and patterns
   - Use data to guide tuning decisions

**Key Point:** The value of a dyno session comes from using it to make your vehicle faster, not from the absolute power number it reports. A dyno that consistently shows improvements when you make good modifications is more valuable than one that gives high numbers but poor repeatability.""",
        "keywords": ["dyno tuning", "repeatability", "calibration", "testing methods", "data interpretation", "tuning tool"],
        "topic": "Dyno Testing - Best Practices"
    },
    {
        "title": "Inertia Power Formula Details",
        "content": """The inertia power calculation uses specific measurements and constants.

**Formula:**
InertiaPower = (InertialMass × Acceleration × RollSpeed) / 375

**Components:**

1. **InertialMass:** The equivalent mass of the dyno roll
   - Determined through calibration
   - Must be accurately known for correct calculations

2. **Acceleration:** Measured in G's or mph per second
   - Derived from velocity changes between revolutions
   - More frequent measurements = better accuracy
   - Some dynos measure many times per revolution
   - Others measure once per revolution

3. **RollSpeed:** Measured in miles per hour
   - Surface speed of the dyno roll
   - Affected by tire diameter
   - Different tire diameters = different speeds for same RPM

4. **Constant 375:**
   - Conversion factor: 1 hp = 375 lbf × mph
   - Derived from fundamental horsepower definition
   - Converts force × speed to horsepower

**Important Notes:**
- The InertialMass × Acceleration portion equals the force (torque) applied
- This is fundamentally related to the basic horsepower equation
- The formula accounts for the acceleration of a known mass
- Speed component (mph) is critical - tire diameter changes affect this

**Example Effect:**
If tire diameter changes:
- Smaller tire = lower speed (mph) for same RPM
- But may have different acceleration rate
- Both affect the final power calculation
- This is why tire/wheel changes affect results""",
        "keywords": ["inertia power", "formula", "inertial mass", "acceleration", "roll speed", "375 constant", "calculation"],
        "topic": "Dyno Testing - Formulas"
    }
]


def main():
    """Add dyno technical information to knowledge base."""
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_manager = KnowledgeBaseManager(vector_store)
    kb_file_manager = KnowledgeBaseFileManager()

    added_count = 0
    for entry_data in DYNO_TECHNICAL_CONTENT:
        title = entry_data["title"]
        content = entry_data["content"]
        keywords = entry_data["keywords"]
        topic = entry_data["topic"]
        
        # Create question from title
        question = f"What is {title.lower()}?" if not title.lower().startswith("what") else title
        
        LOGGER.info(f"Adding: {title}")
        try:
            # Add to vector store directly
            vector_store.add_knowledge(
                text=f"Title: {title}\nContent: {content}",
                metadata={
                    "question": question,
                    "answer": content,
                    "source": ARTICLE_URL,
                    "title": title,
                    "topic": topic,
                    "keywords": keywords + [title.lower()] + ARTICLE_TOPIC.lower().split()
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=question,
                answer=content,
                source=ARTICLE_URL,
                title=title,
                topic=topic,
                keywords=keywords + [title.lower()] + ARTICLE_TOPIC.lower().split(),
                verified=True
            )
            
            LOGGER.info(f"  [OK] Added: {title}")
            added_count += 1
        except Exception as e:
            LOGGER.error(f"  [FAIL] Failed to add '{title}': {e}")

    LOGGER.info("\n" + "=" * 70)
    LOGGER.info("SUMMARY")
    LOGGER.info("=" * 70)
    LOGGER.info(f"Total entries: {len(DYNO_TECHNICAL_CONTENT)}")
    LOGGER.info(f"Successfully added: {added_count}")
    if added_count == len(DYNO_TECHNICAL_CONTENT):
        LOGGER.info(f"\n[SUCCESS] Dyno Technical Information and Formulas have been added to the AI Chat Advisor!")
        LOGGER.info(f"Source: {ARTICLE_URL}")
    else:
        LOGGER.warning(f"\n[WARNING] Some entries failed to add.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

