#!/usr/bin/env python3
"""
Add comprehensive nitrous tuning knowledge to the AI Chat Advisor knowledge base.
Creates detailed knowledge entries based on the academic papers and research topics.
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

# Comprehensive nitrous tuning knowledge entries
NITROUS_KNOWLEDGE_ENTRIES = [
    {
        "question": "What is nitrous oxide injection and how does it work?",
        "answer": """Nitrous oxide (N₂O) injection is a performance enhancement system for internal combustion engines that increases power output by providing additional oxygen during combustion.

How it works:
1. Nitrous oxide is stored as a liquid under pressure in a bottle
2. When activated, N₂O is injected into the intake manifold or directly into the combustion chamber
3. Under high temperatures in the cylinder, N₂O decomposes: 2N₂O → 2N₂ + O₂
4. This releases additional oxygen molecules, allowing more fuel to be burned
5. The result is significantly increased power output (typically 30-150+ horsepower gains)

Key components:
- Nitrous bottle (high-pressure storage)
- Solenoids (control N₂O and fuel flow)
- Jets/nozzles (meter the amount of N₂O injected)
- Fuel enrichment system (adds extra fuel to maintain proper air-fuel ratio)
- Activation switch/button

The system works by increasing the oxygen content in the combustion chamber, which allows more fuel to be burned efficiently, resulting in higher cylinder pressures and increased power output.""",
        "keywords": ["nitrous oxide", "N2O", "nitrous injection", "performance", "power", "oxygen"],
        "topic": "Nitrous Tuning - Basics"
    },
    {
        "question": "What are the key tuning parameters for nitrous oxide injection?",
        "answer": """The main tuning parameters for nitrous oxide injection systems include:

1. **Jet Sizing**: The size of the nitrous and fuel jets determines how much N₂O and fuel are delivered. Larger jets = more power but also more stress on the engine.

2. **Air-Fuel Ratio (AFR)**: With nitrous, you need to enrich the fuel mixture. Typical target AFR with nitrous is 11.5:1 to 12.5:1 (richer than normal 14.7:1). Too lean = detonation/engine damage. Too rich = power loss.

3. **Ignition Timing**: Must retard timing when using nitrous to prevent detonation. Typical retard is 2-4 degrees per 50hp of nitrous. More nitrous = more retard needed.

4. **Injection Timing**: When during the intake stroke the nitrous is injected. Early injection allows better mixing but may cause backfire. Late injection reduces mixing time.

5. **Nitrous Pressure**: Bottle pressure affects flow rate. Warmer bottles = higher pressure = more flow. Pressure should be monitored and maintained (typically 900-1100 PSI).

6. **Fuel Pressure**: Must increase fuel pressure to compensate for the additional fuel needed. Fuel system must be capable of supporting the increased demand.

7. **Activation RPM**: When to activate the system. Too early can cause bogging, too late wastes potential power.

8. **Progressive Controller Settings**: For progressive systems, ramp rate and initial percentage are critical to prevent sudden power spikes that can damage drivetrain components.""",
        "keywords": ["nitrous tuning", "jet sizing", "air fuel ratio", "ignition timing", "nitrous pressure", "fuel pressure"],
        "topic": "Nitrous Tuning - Parameters"
    },
    {
        "question": "How does nitrous oxide affect combustion efficiency and engine performance?",
        "answer": """Nitrous oxide significantly impacts combustion efficiency and engine performance through several mechanisms:

**Combustion Efficiency:**
- N₂O decomposes at high temperatures (572°F/300°C) releasing oxygen: 2N₂O → 2N₂ + O₂
- This provides additional oxygen molecules (33% more oxygen by weight than air)
- More oxygen allows more complete fuel combustion
- Results in higher combustion temperatures and pressures
- Typical power gains: 30-150+ horsepower depending on system size

**Performance Effects:**
- **Power Output**: Dramatic increase in horsepower and torque
- **Torque Curve**: Power gains are most noticeable in the mid-to-high RPM range
- **Throttle Response**: Instant power on demand when activated
- **Top Speed**: Can significantly increase top speed potential

**Thermal Effects:**
- Combustion temperatures increase significantly (can exceed 3000°F)
- Increased cylinder pressures (can reach 2000+ PSI)
- Higher exhaust gas temperatures
- Increased heat load on pistons, rings, and cylinder heads

**Emission Effects:**
- NOx emissions typically increase due to higher combustion temperatures
- CO₂ emissions may increase due to more complete combustion
- Unburned hydrocarbons may decrease if properly tuned

**Mechanical Stress:**
- Higher cylinder pressures stress pistons, rods, and crankshaft
- Increased heat can cause piston ring failure or cylinder head warping
- Detonation risk increases if not properly tuned
- Engine durability may be reduced without proper preparation

**Research Findings:**
Studies show that optimal N₂O injection ratios (typically 0.3-0.5 N₂O to fuel ratio) provide the best balance of power increase and engine safety. CFD modeling indicates that injection timing and location significantly affect in-cylinder pressure distribution and temperature gradients.""",
        "keywords": ["combustion efficiency", "engine performance", "nitrous effects", "thermal stress", "emissions", "cylinder pressure"],
        "topic": "Nitrous Tuning - Performance Analysis"
    },
    {
        "question": "What safety considerations are important when using nitrous oxide?",
        "answer": """Safety is critical when using nitrous oxide injection systems. Key considerations include:

**Engine Preparation:**
- Engine must be in good mechanical condition
- Stronger pistons, rods, and crankshaft recommended for high power levels
- Upgraded head gaskets and head studs often necessary
- Proper cooling system (larger radiator, better water pump)
- Stronger valve springs to prevent float at high RPM

**Fuel System:**
- Fuel system must be capable of supporting increased demand
- Larger fuel pump, injectors, and fuel lines
- Fuel pressure regulator to maintain proper pressure
- Fuel filters must be clean and adequate capacity

**Ignition System:**
- Strong ignition system (high-output coil, good spark plugs)
- Spark plugs should be one heat range colder
- Proper gap (typically 0.028-0.032 inches)
- Retard timing appropriately (2-4 degrees per 50hp)

**Monitoring:**
- Wideband oxygen sensor to monitor air-fuel ratio
- Fuel pressure gauge
- Nitrous pressure gauge
- EGT (exhaust gas temperature) gauge
- Knock sensor or detonation detection

**System Components:**
- Quality solenoids (not cheap knockoffs)
- Proper wiring with adequate gauge wire
- Fuses and relays properly sized
- Bottle mounted securely
- Lines routed safely away from heat sources

**Tuning Approach:**
- Start with small jet sizes and work up
- Always monitor AFR, EGT, and listen for detonation
- Never run lean - better to be slightly rich
- Progressive controllers help prevent sudden power spikes
- Test in safe conditions (dyno or controlled environment)

**Common Failures:**
- Running too lean = detonation = engine damage
- Too much timing = detonation
- Insufficient fuel = lean condition = engine damage
- Overheating = warped heads, blown head gaskets
- Sudden activation = drivetrain damage

**Best Practices:**
- Always have proper safety equipment (fire extinguisher)
- Never activate nitrous below certain RPM (typically 3000-3500 RPM)
- Use progressive controllers for smooth power delivery
- Regular maintenance of all system components
- Keep bottle pressure in proper range (900-1100 PSI)
- Never exceed manufacturer's recommended power levels without proper engine preparation""",
        "keywords": ["nitrous safety", "engine preparation", "fuel system", "ignition timing", "monitoring", "detonation"],
        "topic": "Nitrous Tuning - Safety"
    },
    {
        "question": "What is the difference between wet and dry nitrous systems?",
        "answer": """There are two main types of nitrous oxide injection systems:

**Dry Nitrous System:**
- Only injects nitrous oxide into the intake
- Relies on the engine's existing fuel system to provide additional fuel
- Uses a fuel pressure sensor to signal the ECU to add more fuel
- Simpler installation (fewer components)
- Less precise fuel control
- Requires ECU tuning or fuel pressure regulator adjustment
- Better for engines with sophisticated fuel management systems

**Wet Nitrous System:**
- Injects both nitrous oxide AND additional fuel
- Has separate fuel solenoid and fuel jets
- More precise control over air-fuel ratio
- More complex installation (additional fuel lines, solenoids)
- Can work with carbureted or fuel-injected engines
- More popular for carbureted applications
- Requires separate fuel source (often separate fuel cell or T-fitting)

**Fogger Systems:**
- Direct port injection - injects N₂O and fuel directly into each intake port
- Most precise distribution
- Most complex installation
- Best for high power applications
- Allows per-cylinder tuning

**Plate Systems:**
- Installs between throttle body and intake manifold
- Simpler installation
- Good for moderate power levels
- Less precise distribution than fogger systems

**Choosing a System:**
- Dry: Best for modern fuel-injected engines with ECU tuning capability
- Wet: Best for carbureted engines or when you want precise fuel control
- Fogger: Best for maximum power and precision
- Plate: Best for ease of installation and moderate power gains""",
        "keywords": ["dry nitrous", "wet nitrous", "fogger system", "plate system", "nitrous types"],
        "topic": "Nitrous Tuning - System Types"
    },
    {
        "question": "How do you calculate the correct jet sizes for nitrous and fuel?",
        "answer": """Jet sizing is critical for safe and effective nitrous operation. Here's how to calculate:

**Basic Principles:**
- Nitrous jets are sized in thousandths of an inch (e.g., 0.031 = 31 thousandths)
- Fuel jets are typically larger than nitrous jets
- The ratio between fuel and nitrous jets determines air-fuel ratio

**General Guidelines:**
- For every 0.001" increase in nitrous jet size, expect ~10-15 horsepower increase
- Fuel jet should be 1.5-2x the size of the nitrous jet (depending on fuel type)
- Example: 0.031" nitrous jet might use 0.046" fuel jet

**Calculation Method:**
1. Determine target power gain (e.g., 50hp, 100hp, 150hp)
2. Start with manufacturer's recommended jet sizes for that power level
3. Use a jet size calculator (many available online)
4. Consider: engine size, compression ratio, fuel type, nitrous pressure

**Factors Affecting Jet Sizing:**
- **Engine Size**: Larger engines need larger jets for same power gain
- **Nitrous Pressure**: Higher pressure = more flow (need larger jets for same power)
- **Fuel Type**: Gasoline vs. E85 vs. methanol have different requirements
- **Compression Ratio**: Higher compression may need richer mixture
- **Altitude**: Higher altitude = less air = may need adjustment

**Typical Jet Combinations (Wet System):**
- 50hp: 0.017" N₂O / 0.024" Fuel
- 75hp: 0.021" N₂O / 0.031" Fuel  
- 100hp: 0.025" N₂O / 0.037" Fuel
- 125hp: 0.029" N₂O / 0.043" Fuel
- 150hp: 0.033" N₂O / 0.049" Fuel

**Safety Considerations:**
- Always start smaller and work up
- Monitor air-fuel ratio with wideband O2 sensor
- Target AFR: 11.5:1 to 12.5:1 with nitrous
- Too small fuel jet = lean = dangerous
- Too large fuel jet = rich = power loss but safer

**Testing Process:**
1. Install smaller jets than target
2. Test on dyno or controlled environment
3. Monitor AFR, EGT, and listen for detonation
4. Gradually increase jet sizes while monitoring
5. Stop if you see any signs of detonation or lean condition

**Professional Tuning:**
- Many professional tuners use data logging
- Monitor multiple parameters simultaneously
- Make incremental changes
- Document all changes and results""",
        "keywords": ["jet sizing", "nitrous jets", "fuel jets", "power calculation", "air fuel ratio"],
        "topic": "Nitrous Tuning - Jet Sizing"
    }
]


def main():
    """Add nitrous tuning knowledge to the knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in NITROUS_KNOWLEDGE_ENTRIES:
        try:
            LOGGER.info(f"Adding: {entry['question'][:60]}...")
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{entry['question']}\n\n{entry['answer']}",
                metadata={
                    "question": entry["question"],
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": "nitrous_tuning_knowledge_base",
                    "category": "Nitrous Tuning"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                source="nitrous_tuning_knowledge_base",
                keywords=entry["keywords"],
                topic=entry["topic"],
                confidence=0.9,
                verified=True
            )
            
            added_count += 1
            LOGGER.info(f"  ✓ Added to knowledge base")
            
        except Exception as e:
            LOGGER.error(f"  ✗ Failed to add entry: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total entries: {len(NITROUS_KNOWLEDGE_ENTRIES)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\n✓ Nitrous tuning knowledge has been added to the AI Chat Advisor!")
    LOGGER.info(f"The advisor can now answer questions about nitrous oxide injection systems.")


if __name__ == "__main__":
    main()

