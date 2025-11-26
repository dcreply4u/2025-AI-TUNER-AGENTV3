#!/usr/bin/env python3
"""
Add ASM Tuning E85 fuel tuning guide to the AI Chat Advisor knowledge base.
Comprehensive guide on tuning cars for E85 fuel and boost performance.
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

# E85 Tuning Knowledge from ASM Tuning article
E85_TUNING_KNOWLEDGE = [
    {
        "question": "What is E85 fuel and why does it matter for performance?",
        "answer": """E85 is a high-performance ethanol blend that contains 85% ethanol and 15% gasoline.

**Key Characteristics:**
- **Octane Rating:** 100-105 (much higher than premium pump gas)
- **High Knock Resistance:** Allows more boost, higher compression, and more aggressive timing curves
- **Heat Absorption:** Ethanol absorbs more heat during vaporization, keeping intake temps low
- **Reduced Detonation Risk:** Lower intake temperatures reduce risk of detonation
- **Cost-Effective:** Race-fuel-like benefits at pump gas prices
- **Cleaner Burning:** Higher oxygen content leads to reduced carbon buildup and better emissions
- **Renewable:** Eco-friendly production process

**Performance Benefits:**
- More power potential without breaking the budget
- Better stability under pressure
- Reduced carbon buildup
- Better emissions

**Important Consideration:**
E85 has less energy per liter than gasoline, so you need more fuel per combustion cycle. This requires adjusting air/fuel ratios and upgrading supporting components.

**Bottom Line:**
E85's high octane unleashes tuning headroom that's simply out of reach with regular gasoline.""",
        "keywords": ["E85", "ethanol", "fuel", "octane rating", "performance fuel", "ethanol blend"],
        "topic": "E85 Tuning - Basics"
    },
    {
        "question": "What are the benefits of tuning your car for E85 fuel?",
        "answer": """Tuning for E85 delivers significant performance gains and reliability benefits:

**Power Gains:**
- **Naturally Aspirated Engines:** 5-15% horsepower gains with well-executed E85 tuning
- **Turbo/Supercharged Engines:** 15-25% (or more) horsepower gains
- Results are data-backed from dyno testing

**Performance Advantages:**
- **Higher Boost:** Can safely run higher boost levels
- **Higher Compression:** Increased compression ratios possible
- **More Ignition Advance:** More aggressive timing curves without knock risk
- **Lower Exhaust Gas Temps:** Helps reliability and longevity at elevated power levels
- **Crisper Response:** Immediate noticeable difference on the road
- **Smoother Delivery:** Better throttle response

**Reliability Benefits:**
- **Reduced Carbon Buildup:** E85 burns cleaner, leading to less maintenance
- **Smoother Idle:** Better combustion characteristics
- **Longer-Term Reliability:** Especially beneficial for high-mileage or track-driven builds
- **Lower EGTs:** Reduced thermal stress on engine components

**Bottom Line:**
E85 tuning is one of the fastest ways to unlock reliable power, crisp response, and bolder capability.""",
        "keywords": ["E85 benefits", "E85 power gains", "E85 tuning advantages", "ethanol performance", "E85 horsepower"],
        "topic": "E85 Tuning - Benefits"
    },
    {
        "question": "Can any car run on E85 and what are the prerequisites?",
        "answer": """Not every car is ready for E85 out of the box. Converting to E85 requires specific prerequisites:

**Fuel System Requirements:**
- **Larger Fuel Injectors:** E85 requires 30-40% more fuel flow than gasoline
- **Higher Capacity Fuel Pump:** Must deliver sufficient volume at adequate pressure
- **E85-Compatible Fuel Lines:** Standard rubber lines may degrade with ethanol
- **E85-Compatible Seals:** O-rings and gaskets must be ethanol-resistant
- **Fuel Filter:** May need more frequent changes

**ECU/Engine Management:**
- **Programmable ECU:** Must be able to adjust fuel maps, timing, and other parameters
- **Wideband O2 Sensor:** Essential for accurate air/fuel ratio monitoring
- **Data Logging Capability:** Important for tuning and monitoring

**Engine Components:**
- **Compression Ratio:** Higher compression works well with E85's high octane
- **Boost Levels:** Can safely run higher boost with proper tuning
- **Ignition System:** Must be in good condition to handle increased power

**Important Considerations:**
- Check manufacturer recommendations (some vehicles explicitly state "No E85" on fuel filler)
- Warranty implications (may void warranty)
- Emissions compliance (check local laws)
- Fuel availability in your area

**Bottom Line:**
Proper preparation and supporting modifications are essential for reliable E85 operation.""",
        "keywords": ["E85 conversion", "E85 prerequisites", "E85 fuel system", "E85 compatible", "E85 requirements"],
        "topic": "E85 Tuning - Prerequisites"
    },
    {
        "question": "How do you tune a car for E85 fuel?",
        "answer": """Tuning for E85 requires systematic adjustments to fuel delivery, timing, and supporting systems:

**Step 1: Fuel System Upgrades**
- Upgrade to larger fuel injectors (30-40% more flow capacity)
- Install higher capacity fuel pump
- Replace fuel lines with E85-compatible materials
- Upgrade fuel filter

**Step 2: ECU Calibration**
- **Fuel Maps:** Increase fuel delivery by 30-40% across all load/RPM ranges
- **Air/Fuel Ratios:** Target AFR typically 9.5-10.5:1 (richer than gasoline's 12-13:1)
- **Ignition Timing:** Add 3-8 degrees of advance (E85's high octane allows more timing)
- **Boost Levels:** Can increase boost 2-5 PSI safely with proper fuel delivery

**Step 3: Cold Start Tuning**
- E85 requires more enrichment for cold starts
- Adjust cold start fuel tables
- May need longer cranking time
- Consider flex fuel sensor for automatic blending

**Step 4: Data Logging and Validation**
- Monitor air/fuel ratios across all conditions
- Check for knock/detonation
- Verify fuel pressure stability
- Test under various load conditions
- Validate cold start and warm-up behavior

**Step 5: Fine-Tuning**
- Adjust based on data logs
- Optimize for drivability
- Balance power and reliability
- Test under real-world conditions

**Key Tuning Parameters:**
- Fuel injector pulse width (increase 30-40%)
- Ignition timing advance (add 3-8 degrees)
- Boost pressure (can increase 2-5 PSI)
- Air/fuel ratio targets (richer than gasoline)

**Bottom Line:**
Proper E85 tuning requires systematic fuel system upgrades, ECU calibration, and thorough validation through data logging.""",
        "keywords": ["E85 tuning process", "how to tune E85", "E85 calibration", "E85 fuel maps", "E85 ignition timing"],
        "topic": "E85 Tuning - Process"
    },
    {
        "question": "What fuel system upgrades are needed for E85?",
        "answer": """E85 requires significant fuel system upgrades due to its lower energy density:

**Fuel Injectors:**
- **Size Increase:** Need 30-40% larger injectors than gasoline
- **Flow Rate:** Must deliver sufficient fuel at all RPM/load conditions
- **Duty Cycle:** Should stay below 85% at maximum power
- **Quality:** High-quality injectors essential for reliability

**Fuel Pump:**
- **Higher Flow Rate:** Must deliver 30-40% more volume
- **Pressure Stability:** Maintain consistent pressure under all conditions
- **Dual Pump Setup:** May be needed for high-power applications
- **E85 Compatibility:** Pump must be compatible with ethanol

**Fuel Lines:**
- **E85-Compatible Materials:** Standard rubber lines degrade with ethanol
- **PTFE or Stainless Steel:** Recommended for E85 applications
- **Proper Routing:** Avoid heat sources that could cause vapor lock

**Fuel Filter:**
- **More Frequent Changes:** E85 can clean deposits, requiring more frequent filter changes
- **High-Quality Filter:** Essential for protecting injectors
- **Proper Sizing:** Must handle increased flow rates

**Fuel Pressure Regulator:**
- **Adjustable:** Allows fine-tuning of fuel pressure
- **Stable Operation:** Must maintain consistent pressure
- **E85 Compatibility:** Materials must resist ethanol

**Additional Considerations:**
- **Fuel Rail:** May need larger diameter for high-flow applications
- **Return Line:** Proper return system for pressure regulation
- **Fuel Pressure Sensor:** Monitor pressure for tuning and diagnostics

**Bottom Line:**
Proper fuel system upgrades are critical for reliable E85 operation and maximum performance.""",
        "keywords": ["E85 fuel system", "E85 injectors", "E85 fuel pump", "E85 fuel lines", "E85 upgrades"],
        "topic": "E85 Tuning - Fuel System"
    },
    {
        "question": "What air/fuel ratios should you target with E85?",
        "answer": """E85 requires different air/fuel ratio targets than gasoline:

**Target AFR for E85:**
- **Idle/Cruise:** 9.5-10.5:1 (richer than gasoline)
- **WOT (Wide Open Throttle):** 9.0-10.0:1
- **Boost Conditions:** 8.5-9.5:1 for safety
- **Lambda Equivalent:** Approximately 0.65-0.75 (gasoline is ~0.85-0.95)

**Why Richer Than Gasoline?**
- E85 has less energy per unit volume
- Requires more fuel to achieve same power output
- Richer mixture helps with cooling and detonation prevention
- Ethanol's oxygen content allows for richer mixtures

**Monitoring:**
- **Wideband O2 Sensor:** Essential for accurate AFR monitoring
- **Data Logging:** Monitor AFR across all conditions
- **Safety Margins:** Keep slightly rich to prevent lean conditions

**Important Notes:**
- These are general guidelines; specific targets depend on engine setup
- Boost applications may need richer mixtures
- High compression engines may tolerate slightly leaner mixtures
- Always monitor for knock/detonation

**Bottom Line:**
E85 requires richer air/fuel ratios (9.0-10.5:1) compared to gasoline (12-13:1) due to its lower energy density.""",
        "keywords": ["E85 AFR", "E85 air fuel ratio", "E85 lambda", "E85 fuel mixture", "E85 stoichiometric"],
        "topic": "E85 Tuning - Air/Fuel Ratios"
    },
    {
        "question": "How much ignition timing advance can you run with E85?",
        "answer": """E85's high octane rating allows for significantly more ignition timing advance:

**Timing Advance with E85:**
- **Typical Increase:** 3-8 degrees more advance than gasoline
- **Base Timing:** Start with 3-5 degrees additional advance
- **Maximum Advance:** Can often run 5-10 degrees more than pump gas safely
- **Boost Applications:** May see even more timing benefit

**Why More Timing Works:**
- **High Octane:** 100-105 octane rating resists knock/detonation
- **Cooler Intake Temps:** Ethanol's cooling effect reduces knock risk
- **Better Combustion:** More complete burn allows for earlier ignition

**Tuning Process:**
1. Start conservative (add 3-5 degrees)
2. Monitor for knock/detonation
3. Gradually increase timing
4. Use data logging to find optimal timing
5. Leave safety margin (don't push to absolute limit)

**Considerations:**
- **Compression Ratio:** Higher compression benefits more from timing
- **Boost Levels:** More boost may require more timing
- **Engine Load:** Timing needs vary with load/RPM
- **Safety Margins:** Always leave margin for safety

**Monitoring:**
- **Knock Sensors:** Monitor for detonation
- **Data Logging:** Track timing across all conditions
- **EGT Monitoring:** Watch exhaust gas temperatures

**Bottom Line:**
E85 typically allows 3-8 degrees more ignition timing advance than gasoline, with some applications seeing even more benefit.""",
        "keywords": ["E85 ignition timing", "E85 timing advance", "E85 spark advance", "E85 octane", "E85 knock resistance"],
        "topic": "E85 Tuning - Ignition Timing"
    },
    {
        "question": "How much boost can you safely run with E85?",
        "answer": """E85's high octane and cooling properties allow for significantly higher boost levels:

**Boost Increase with E85:**
- **Typical Increase:** 2-5 PSI more boost than gasoline safely
- **Conservative Approach:** Start with 2-3 PSI increase
- **Aggressive Tuning:** Some applications see 5-10 PSI increases
- **Maximum Boost:** Depends on engine components and fuel system capacity

**Why More Boost Works:**
- **High Octane:** 100-105 octane resists knock at higher pressures
- **Cooling Effect:** Ethanol's vaporization cools intake charge
- **Lower EGTs:** Reduced exhaust gas temperatures
- **Better Detonation Resistance:** Can handle higher cylinder pressures

**Safety Considerations:**
- **Fuel System Capacity:** Must deliver sufficient fuel for increased boost
- **Engine Components:** Pistons, rods, head gaskets must handle increased pressure
- **Turbo/Supercharger:** Must be sized appropriately
- **Intercooler:** Still important for managing intake temps

**Tuning Process:**
1. Ensure fuel system can support increased boost
2. Start with 2-3 PSI increase
3. Monitor for knock/detonation
4. Gradually increase boost
5. Monitor fuel pressure and AFR
6. Leave safety margin

**Monitoring:**
- **Boost Pressure:** Monitor actual vs. target boost
- **Knock Sensors:** Watch for detonation
- **Fuel Pressure:** Ensure adequate fuel delivery
- **AFR:** Monitor air/fuel ratios under boost
- **EGT:** Watch exhaust gas temperatures

**Bottom Line:**
E85 typically allows 2-5 PSI more boost than gasoline safely, with proper fuel system support and careful tuning.""",
        "keywords": ["E85 boost", "E85 turbo", "E85 supercharger", "E85 boost pressure", "E85 forced induction"],
        "topic": "E85 Tuning - Boost"
    },
    {
        "question": "What are common E85 tuning mistakes to avoid?",
        "answer": """Common E85 tuning mistakes that can lead to engine damage or poor performance:

**Fuel System Mistakes:**
- **Insufficient Fuel Flow:** Not upgrading injectors/pump enough (need 30-40% more capacity)
- **Incompatible Materials:** Using standard rubber fuel lines that degrade with ethanol
- **Inadequate Fuel Pressure:** Not maintaining proper fuel pressure under all conditions
- **Poor Fuel Filter Maintenance:** Not changing filters frequently enough

**Tuning Mistakes:**
- **Too Lean:** Not adding enough fuel (E85 needs 30-40% more)
- **Insufficient Timing Advance:** Not taking advantage of E85's high octane
- **Aggressive Changes:** Making too large changes at once without validation
- **Ignoring Cold Start:** Not properly tuning cold start enrichment

**Monitoring Mistakes:**
- **No Wideband O2 Sensor:** Trying to tune without accurate AFR monitoring
- **Insufficient Data Logging:** Not logging enough parameters
- **Ignoring Knock:** Not monitoring for detonation
- **No Safety Margins:** Pushing to absolute limits

**Maintenance Mistakes:**
- **Infrequent Filter Changes:** E85 cleans deposits, requiring more frequent filter changes
- **Ignoring Leaks:** Not checking for fuel system leaks regularly
- **Corrosion Issues:** Not inspecting for ethanol-related corrosion
- **Tune Drift:** Not monitoring for changes over time

**Best Practices:**
- Upgrade fuel system properly (30-40% more capacity)
- Use E85-compatible materials throughout
- Tune systematically with data logging
- Monitor all critical parameters
- Leave safety margins
- Regular maintenance and inspection

**Bottom Line:**
Avoid common mistakes by properly upgrading fuel systems, tuning systematically with data logging, and maintaining safety margins.""",
        "keywords": ["E85 mistakes", "E85 tuning errors", "E85 problems", "E85 troubleshooting", "E85 best practices"],
        "topic": "E85 Tuning - Common Mistakes"
    },
    {
        "question": "What maintenance is required for E85 fuel systems?",
        "answer": """E85 fuel systems require specific maintenance to ensure reliability:

**Regular Maintenance:**
- **Fuel Filter Changes:** More frequent than gasoline (every 5,000-10,000 miles or after initial switch)
- **System Inspection:** Check for leaks, corrosion, and wear every few months
- **Fuel Pressure Monitoring:** Verify pressure stability regularly
- **Injector Cleaning:** May need more frequent cleaning due to deposits

**Initial Switch Maintenance:**
- **Change Fuel Filter:** Immediately after switching to E85
- **Inspect Fuel Lines:** Check for degradation or leaks
- **Check Seals:** Inspect O-rings and gaskets for ethanol compatibility
- **System Flush:** Consider flushing system if switching from gasoline

**Ongoing Inspection:**
- **Leak Detection:** Check for fuel leaks regularly
- **Corrosion Check:** Inspect for ethanol-related corrosion
- **Material Degradation:** Watch for signs of incompatible materials breaking down
- **Tune Validation:** Monitor for tune drift over time

**High-Performance Use:**
- **More Frequent Inspection:** If running hard or track use
- **After Storage:** Inspect system if car has been stored
- **Filter Changes:** More frequent for track/racing applications
- **System Pressure:** Verify fuel pressure after extended use

**Warning Signs:**
- **Fuel Pressure Drop:** Indicates pump or filter issues
- **Leaning Out:** AFR going leaner over time
- **Starting Issues:** May indicate fuel system problems
- **Performance Degradation:** Could signal fuel delivery issues

**Best Practices:**
- Change filters after initial switch
- Inspect for leaks, corrosion, and tune drift every few months
- More frequent maintenance for hard use or storage
- Monitor fuel pressure and AFR regularly

**Bottom Line:**
E85 systems require more frequent filter changes and regular inspection for leaks, corrosion, and tune drift, especially with hard use or storage.""",
        "keywords": ["E85 maintenance", "E85 fuel filter", "E85 inspection", "E85 care", "E85 system maintenance"],
        "topic": "E85 Tuning - Maintenance"
    },
    {
        "question": "What power gains should I expect from E85 tuning?",
        "answer": """E85 tuning delivers significant power gains when properly executed:

**Naturally Aspirated Engines:**
- **Typical Gains:** 5-15% horsepower increase
- **Factors:** Compression ratio, cam timing, supporting modifications
- **Best Results:** Higher compression engines see better gains

**Turbo/Supercharged Engines:**
- **Typical Gains:** 15-25% horsepower increase (or more)
- **Factors:** Boost levels, fuel system capacity, supporting modifications
- **Best Results:** Well-tuned forced induction applications

**Real-World Results:**
- Gains are data-backed from dyno testing
- Results vary based on engine setup and tuning quality
- Supporting modifications amplify gains
- Proper fuel system upgrades are essential

**Factors Affecting Gains:**
- **Compression Ratio:** Higher compression benefits more
- **Boost Levels:** More boost = more potential gains
- **Fuel System:** Proper upgrades essential for maximum gains
- **Tuning Quality:** Professional tuning maximizes results
- **Supporting Mods:** Intake, exhaust, etc. amplify gains

**Expectations:**
- Conservative estimates: 5-15% NA, 15-25% boosted
- Aggressive tuning: Can see even more with proper setup
- Results are measurable and repeatable
- Gains are sustainable with proper maintenance

**Bottom Line:**
Expect 5-15% gains for naturally aspirated engines and 15-25% (or more) for turbo/supercharged applications with proper E85 tuning and supporting modifications.""",
        "keywords": ["E85 power gains", "E85 horsepower", "E85 performance", "E85 dyno results", "E85 power increase"],
        "topic": "E85 Tuning - Power Gains"
    }
]

ARTICLE_URL = "https://asmtuning.co/how-to-tune-your-car-for-e85-fuel/"
ARTICLE_SOURCE = "ASM Tuning - E85 Fuel Tuning Guide"


def main():
    """Add E85 tuning guide to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in E85_TUNING_KNOWLEDGE:
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
                    "category": "E85 Tuning",
                    "data_type": "comprehensive_guide"
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
    LOGGER.info(f"Total entries: {len(E85_TUNING_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nASM Tuning E85 fuel tuning guide has been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - E85 fuel basics and characteristics")
    LOGGER.info(f"  - Benefits of E85 tuning")
    LOGGER.info(f"  - Prerequisites and compatibility")
    LOGGER.info(f"  - Tuning process and procedures")
    LOGGER.info(f"  - Fuel system upgrades")
    LOGGER.info(f"  - Air/fuel ratio targets")
    LOGGER.info(f"  - Ignition timing advance")
    LOGGER.info(f"  - Boost pressure increases")
    LOGGER.info(f"  - Common mistakes to avoid")
    LOGGER.info(f"  - Maintenance requirements")
    LOGGER.info(f"  - Expected power gains")


if __name__ == "__main__":
    main()

