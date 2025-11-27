"""
Comprehensive Knowledge Loader
Loads ALL knowledge from all sources into the vector store.
This ensures the advisor has complete racing/tuning knowledge.
"""

from __future__ import annotations

import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)


def load_all_knowledge(vector_store) -> int:
    """
    Load ALL knowledge from all sources into vector store.
    
    This includes:
    - Racing/tuning knowledge
    - Technical knowledge
    - Calculation knowledge
    - Enhanced advisor knowledge
    - Basic advisor knowledge
    
    Args:
        vector_store: VectorKnowledgeStore instance
        
    Returns:
        Total number of entries loaded
    """
    total_loaded = 0
    
    # 1. Load racing/tuning knowledge
    try:
        from services.add_racing_tuning_knowledge import add_racing_tuning_knowledge
        count = add_racing_tuning_knowledge(vector_store)
        total_loaded += count
        LOGGER.info(f"Loaded {count} racing/tuning knowledge entries")
    except Exception as e:
        LOGGER.warning(f"Failed to load racing knowledge: {e}")
    
    # 2. Load additional technical knowledge
    try:
        from services.add_additional_technical_knowledge import add_additional_technical_knowledge
        count = add_additional_technical_knowledge(vector_store)
        total_loaded += count
        LOGGER.info(f"Loaded {count} additional technical knowledge entries")
    except Exception as e:
        LOGGER.warning(f"Failed to load additional technical knowledge: {e}")
    
    # 3. Load calculation knowledge
    try:
        from services.add_calculation_knowledge import add_calculation_knowledge_to_store
        count = add_calculation_knowledge_to_store(vector_store)
        total_loaded += count
        LOGGER.info(f"Loaded {count} calculation knowledge entries")
    except Exception as e:
        LOGGER.warning(f"Failed to load calculation knowledge: {e}")
    
    # 4. Migrate enhanced advisor knowledge
    try:
        from services.migrate_knowledge_to_rag import migrate_from_enhanced_advisor
        count = migrate_from_enhanced_advisor(vector_store)
        total_loaded += count
        LOGGER.info(f"Migrated {count} entries from enhanced advisor")
    except Exception as e:
        LOGGER.warning(f"Failed to migrate enhanced advisor knowledge: {e}")
    
    # 5. Add critical missing knowledge entries directly
    critical_knowledge = [
        {
            "text": """VE Table (Volumetric Efficiency Table) - Complete Guide

WHAT IS A VE TABLE?
A VE (Volumetric Efficiency) table is a 2D map that defines how efficiently the engine fills its cylinders with air at different load and RPM points. It's the foundation of fuel tuning.

HOW IT WORKS:
- X-axis: Engine RPM (typically 500-8000 RPM)
- Y-axis: Engine Load (MAP, MAF, or TPS - depending on load source)
- Values: Volumetric Efficiency percentage (typically 50-120%)

PURPOSE:
The VE table tells the ECU how much air is entering the engine at each load/RPM point. The ECU uses this to calculate:
- Required fuel injector pulse width
- Target air-fuel ratio
- Expected airflow for boost control

TUNING PROCESS:
1. Start with a baseline VE table (from similar engines or calculated)
2. Log actual AFR vs target AFR during runs
3. Adjust VE values up if running lean (need more fuel)
4. Adjust VE values down if running rich (need less fuel)
5. Use autotune feature to automatically adjust based on logged data
6. Smooth the table using interpolation tools

BEST PRACTICES:
- Always backup before tuning
- Make small incremental changes
- Smooth transitions between cells (use interpolation)
- Test on dyno or controlled environment
- Monitor knock sensors during tuning
- Consider temperature and altitude compensation

COMMON VALUES:
- Naturally aspirated: 70-95% VE
- Turbocharged: 90-120% VE (boost increases effective VE)
- Supercharged: 85-110% VE
""",
            "metadata": {
                "topic": "VE Table",
                "category": "tuning",
                "keywords": "ve table, volumetric efficiency, fuel map, tuning"
            }
        },
        {
            "text": """Ignition Timing Tuning - Complete Guide

WHAT IS IGNITION TIMING?
Ignition timing controls when the spark plug fires relative to piston position. Measured in degrees Before Top Dead Center (BTDC).

HOW IT WORKS:
- Advanced timing: Spark fires earlier (more BTDC) = more power but risk of knock
- Retarded timing: Spark fires later (less BTDC) = less power but safer

TUNING PROCESS:
1. Start with conservative timing (factory or slightly retarded)
2. Gradually advance timing in small increments (1-2 degrees)
3. Monitor for knock using knock sensors
4. Stop advancing when knock is detected
5. Retard timing 2-3 degrees from knock threshold for safety margin
6. Test at different load and RPM points
7. Build timing map (Load vs RPM)

FACTORS AFFECTING TIMING:
- Compression ratio: Higher compression = less advance needed
- Fuel octane: Higher octane = more advance possible
- Boost pressure: More boost = less advance needed
- Air temperature: Hotter air = less advance needed
- Engine load: Higher load = less advance needed

OPTIMAL TIMING:
- Naturally aspirated: 25-35 degrees BTDC at WOT
- Turbocharged: 15-25 degrees BTDC at WOT (depends on boost)
- Supercharged: 20-30 degrees BTDC at WOT

SAFETY:
- Always use knock sensors
- Start conservative
- Test incrementally
- Monitor EGT (Exhaust Gas Temperature)
- Too much advance = engine damage
""",
            "metadata": {
                "topic": "Ignition Timing",
                "category": "tuning",
                "keywords": "ignition timing, spark timing, advance, retard, knock"
            }
        },
        {
            "text": """Boost Control - Complete Guide

WHAT IS BOOST CONTROL?
Boost control manages turbocharger or supercharger output pressure to optimize power while maintaining safety.

TYPES:
1. Open Loop: Fixed wastegate duty cycle based on RPM/load
2. Closed Loop: PID controller maintains target boost pressure
3. Hybrid: Open loop base with closed loop correction

COMPONENTS:
- Wastegate: Controls exhaust flow to turbo (mechanical or electronic)
- Solenoid: Electronic wastegate control valve
- Boost sensor: Measures actual boost pressure
- ECU: Calculates wastegate duty cycle

TUNING PROCESS:
1. Set target boost pressure (consider engine limits)
2. Configure wastegate duty cycle table (RPM vs Load)
3. Set up closed loop PID if available:
   - P (Proportional): Response speed
   - I (Integral): Eliminates steady-state error
   - D (Derivative): Reduces overshoot
4. Test and adjust duty cycle to hit target boost
5. Add compensation for:
   - Air temperature
   - Altitude
   - Gear (higher gear = more boost possible)

SAFETY:
- Set maximum boost limit (hardware protection)
- Monitor boost spikes
- Use boost cut protection
- Consider engine internals strength
- Monitor AFR (more boost = need more fuel)

COMMON SETTINGS:
- Street: 8-15 PSI
- Track: 15-25 PSI
- Race: 25-40+ PSI (depends on engine build)
""",
            "metadata": {
                "topic": "Boost Control",
                "category": "tuning",
                "keywords": "boost control, turbo, wastegate, psi, bar, pressure"
            }
        },
        {
            "text": """E85 and Flex Fuel Tuning - Complete Guide

WHAT IS E85?
E85 is a fuel blend containing 85% ethanol and 15% gasoline. It has higher octane (105+) and requires more fuel volume due to lower energy content.

ADVANTAGES:
- Higher octane = more timing advance possible
- More power potential
- Lower cost (in some regions)
- Cleaner burning

DISADVANTAGES:
- Requires 30-40% more fuel volume
- Lower energy content = worse fuel economy
- Requires fuel system upgrades (pumps, injectors, lines)
- Cold start issues in cold weather

TUNING FOR E85:
1. Upgrade fuel system:
   - Larger fuel pump (2-3x capacity)
   - Larger injectors (30-40% more flow)
   - Larger fuel lines if needed
2. Adjust fuel maps:
   - Increase fuel delivery by 30-40%
   - Adjust VE table or fuel multiplier
3. Adjust ignition timing:
   - Can advance timing 3-5 degrees more than gasoline
   - Higher octane allows more aggressive timing
4. Cold start tuning:
   - May need additional fuel for cold starts
   - Consider fuel temperature compensation

FLEX FUEL SYSTEMS:
- Automatically detects ethanol content (0-85%)
- Switches between gasoline and E85 maps
- Adjusts fuel and timing based on ethanol percentage
- Requires ethanol content sensor

BEST PRACTICES:
- Always test fuel system capacity first
- Start with conservative timing
- Monitor fuel pressure
- Test cold start behavior
- Consider dual fuel pump setup for high power
""",
            "metadata": {
                "topic": "E85 Tuning",
                "category": "tuning",
                "keywords": "e85, ethanol, flex fuel, fuel tuning, octane"
            }
        },
        {
            "text": """Fuel Map Tuning - Complete Guide

WHAT IS A FUEL MAP?
A fuel map (or fuel table) defines how much fuel to inject at each engine load and RPM point to achieve the target air-fuel ratio (AFR).

TYPES:
1. VE Table Based: Uses volumetric efficiency to calculate fuel
2. Direct Fuel Map: Directly specifies injector pulse width
3. AFR Target Table: Specifies target AFR, ECU calculates fuel

TUNING PROCESS:
1. Set target AFR:
   - Idle: 14.7:1 (stoichiometric)
   - Part throttle: 14.5-15.0:1
   - Wide open throttle (WOT): 12.5-13.2:1 (rich for safety)
   - Boost: 11.5-12.5:1 (very rich for safety)
2. Log actual AFR vs target AFR
3. Adjust fuel delivery:
   - If actual AFR > target (lean): Add fuel
   - If actual AFR < target (rich): Remove fuel
4. Use autotune feature to automatically adjust
5. Smooth the fuel map using interpolation

FACTORS AFFECTING FUEL NEEDS:
- Engine load (more load = more fuel)
- RPM (higher RPM = more fuel)
- Boost pressure (more boost = more fuel)
- Air temperature (hotter air = less dense = less fuel)
- Altitude (higher altitude = less air = less fuel)
- Fuel type (E85 needs 30-40% more fuel)

SAFETY:
- Always run rich at WOT (better safe than sorry)
- Monitor AFR constantly
- Use wideband O2 sensors
- Set lean protection limits
- Too lean = engine damage

COMMON AFR TARGETS:
- Idle: 14.7:1
- Cruise: 14.5-15.0:1
- WOT NA: 12.8-13.2:1
- WOT Boost: 11.5-12.5:1
""",
            "metadata": {
                "topic": "Fuel Map Tuning",
                "category": "tuning",
                "keywords": "fuel map, fuel tuning, afr, air fuel ratio, injector"
            }
        },
    ]
    
    # Add critical knowledge entries
    for entry in critical_knowledge:
        try:
            vector_store.add_knowledge(
                text=entry["text"],
                metadata=entry["metadata"]
            )
            total_loaded += 1
        except Exception as e:
            LOGGER.warning(f"Failed to add critical knowledge entry: {e}")
    
    LOGGER.info(f"Total knowledge loaded: {total_loaded} entries")
    return total_loaded

