#!/usr/bin/env python3
"""
Add Spud's Nitro Notes from Fuel Injection Enterprises to the AI Chat Advisor knowledge base.
Comprehensive guide on running nitromethane in drag racing applications.
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

# Key sections from Spud's Nitro Notes
NITRO_KNOWLEDGE = [
    {
        "question": "What is nitromethane and why should I run it in my drag car?",
        "answer": """Nitromethane (nitro) is a powerful fuel additive that can significantly increase horsepower in drag racing applications.

**Why Run Nitro:**
- Pick up a few tenths and 5-10 MPH just from pouring a different mix in the tank
- Extra power and performance without major engine modifications (at light loads)
- Sounds great (extra pop and cackle)
- Smells distinctive
- Very inexpensive way to gain major horsepower when done correctly
- Can be done safely without damaging parts if proper procedures are followed

**Performance Gains:**
- Light loads (10-25%): Moderate power gains with minimal risk
- Medium loads (25-50%): Significant power gains, requires some hardware upgrades
- Heavy loads (50%+): Major power gains but requires extensive engine preparation

**Important Note:**
Nitro is NOT for everyone. It requires proper fuel system components, engine preparation, and careful tuning. When done incorrectly, it can quickly destroy engine parts. This guide focuses on the AFR (Air/Fuel Ratio) method which works well up to about 80% nitro.""",
        "keywords": ["nitromethane", "nitro", "fuel additive", "horsepower", "drag racing", "performance"],
        "topic": "Nitromethane - Introduction"
    },
    {
        "question": "How risky is running nitromethane and what are the dangers?",
        "answer": """Running nitromethane carries significant risks that must be understood and managed:

**Engine Component Risks:**
- **Detonation is the killer** - A lean condition can melt pistons, but more commonly promotes detonation which can break parts, spin bearings, and blow head gaskets
- **Fuel system requirements** - You will burn much more fuel volume than normal at elevated percentages. If your existing fuel system is marginal (worn pump, small nozzles), you won't want to run any nitro
- **Bottom end requirements** - Light loads don't require special bottom end, but heavier loads (25%+) require:
  * Steel main caps (not stock cast caps!)
  * Main girdle consideration
  * Aluminum rods for heavy loads (aluminum absorbs shock loads, steel rods transfer shock to crank)
  * Never use cast iron crank with any nitro

**Real-World Failures:**
- Stock 4-bolt main caps broke in two at 50% nitro
- Bearings can spin from shock loads
- Head gaskets can blow
- Pistons can melt from lean conditions

**Safety Risks:**
- **Engine can explode during cranking** - An engine with even a small amount of nitro in one cylinder can be extremely dangerous when cranking
- **Always remove spark plugs** after running nitro before working on engine
- **Spin motor with fuel off and plugs out** to dry it out before working on it
- **Treat engine like a bomb** after running nitro - remove plugs before towing back or working on engine

**The Key:** Stay on the safe side and only run what you can safely run. Don't push percentages higher without upgrading hardware. Plan ahead and buy the right parts rather than replacing torched parts.""",
        "keywords": ["nitro risks", "detonation", "engine damage", "safety", "nitromethane dangers", "bearing failure"],
        "topic": "Nitromethane - Risks and Safety"
    },
    {
        "question": "Is nitromethane legal in drag racing?",
        "answer": """The legality of nitromethane varies by track and racing organization:

**Track Policies:**
- Many tracks do not allow it at regular events due to increased insurance requirements
- At big events, oldies, and nostalgia events, it's usually okay
- **Always ask the track operator** - when in doubt, ask permission
- Some tracks have a "don't ask and we won't have to tell you no" policy, but it's better to be upfront

**NHRA Rules:**
- Nitro is illegal for anything but the pro nitro classes
- Junior Fuel rules state "Methanol only"
- It is okay in Nostalgia Eliminator classes

**Detection:**
- At 10% or more, the smell will be very obvious
- Scented fuel additives can help cover it up at low percentages, but won't help at 20% or more
- If you have to hide it, you probably shouldn't be doing it

**Consistency Considerations:**
- Running nitro successfully in nostalgia brackets requires experience (quite a few laps)
- Requires a constant fuel mix
- Until you get a handle on it, you may find it very hard to be consistent
- Once you figure it out, you will be very consistent!

**Best Practice:** Always ask permission or at least let the track manager know what you're doing.""",
        "keywords": ["nitro legality", "NHRA rules", "track rules", "nitromethane legal", "racing regulations"],
        "topic": "Nitromethane - Legality"
    },
    {
        "question": "What safety precautions should I take when running nitromethane?",
        "answer": """Critical safety precautions when running nitromethane:

**Before Working on Engine:**
- **ALWAYS remove spark plugs** after running nitro - treat the engine like a bomb
- Spin the motor in the pits with fuel off (or disconnected) and plugs out to dry it out
- For hemi-style motors, back it down to get stray fuel out of cylinders
- You can even squirt some methanol or gas through spark plug hole to dilute anything in there and spin that out

**During Engine Work:**
- Remove plugs from motor at top end before towing back
- If engine rotates on tow back, you could have big problems
- Crew should check plugs are out before running valves or putting breaker bar on motor
- Without pressure, nitro won't hurt anyone

**Real Dangers:**
- Entire front corner of engine block can be blown out at touch of starter button
- Entire cylinder heads can be ripped off and shot across pits
- Heavy, sharp chunks of metal can go anywhere
- This can happen to those who aren't careful

**Starting System (30%+ nitro):**
- Consider using a system to start and run motor on pure methanol or gas
- Switch motor over to nitro mix for the run
- Easiest method: another set of nozzles gravity fed by small vessel quick-connected to motor
- Idle adjustment via needle valve or nozzle orifice changes
- Main fuel system with nitro isn't turned on until motor is running
- Once cackle begins, vessel is detached and ready to run

**Crew Safety:**
- Educate your crew about nitro dangers
- Establish safety procedures and stick to them
- Never skip safety steps, even when in a hurry""",
        "keywords": ["nitro safety", "spark plugs", "engine explosion", "safety precautions", "nitromethane safety"],
        "topic": "Nitromethane - Safety Procedures"
    },
    {
        "question": "What are the characteristics of nitromethane and how does it affect engine performance?",
        "answer": """Nitromethane has unique characteristics that affect engine performance:

**Fuel Characteristics:**
- Nitro burns much more fuel volume than methanol alone
- Requires significantly more fuel delivery capacity
- Burns at different air/fuel ratios than methanol
- Produces more power per unit of fuel

**Performance Effects:**
- **Power Increase:** 50% nitro can provide about 180 HP at the wheels over straight methanol
- **RPM Changes:** Top end RPM may be 800-1000 RPM higher
- **Shift Points:** Car may like to be shifted 1000 RPM lower than on methanol alone
- **Torque:** Produces massive torque increases
- **Converter Stall:** Converter stall speed increases significantly (5800 RPM to 6800 RPM at 50% nitro)

**Tuning Characteristics:**
- Nitro likes to be "lugged" - prefers lower RPM operation
- Taller gears work better (moved from 4.10 to 3.73 rear gears)
- Short shifting works well
- Taller tires can help

**Fuel System Demands:**
- Need more volume above 33% nitro
- Marginal methanol setup won't work
- Fuel pump must be adequate
- Nozzles must be sized correctly
- System pressure management becomes critical

**Heat Generation:**
- Transmission gets much hotter
- Oil temperatures increase
- Cooling system demands increase
- Need to manage heat buildup

**Traction and Chassis:**
- May need more nose ballast with added power
- Traction may become an issue
- Tire pressures may need adjustment
- May experience tire shake
- Braking distance increases with higher speeds""",
        "keywords": ["nitro characteristics", "nitromethane performance", "power increase", "fuel consumption", "RPM changes"],
        "topic": "Nitromethane - Characteristics"
    },
    {
        "question": "How much performance improvement can I expect from nitromethane?",
        "answer": """Performance improvements from nitromethane vary based on percentage used:

**ET and MPH Gains:**
- Can pick up a few tenths and 5-10 MPH from pouring a different mix in the tank
- Gains increase with percentage used
- At 50% nitro: approximately 180 HP at the wheels over straight methanol

**Factors Affecting Gains:**
- Percentage of nitro in mix
- Engine preparation and hardware
- Fuel system capacity
- Tuning accuracy
- Track conditions

**Real-World Example:**
- 50% nitro provided 180 HP gain at wheels
- Converter stall increased from 5800 to 6800 RPM
- Shift point changed by 1000 RPM (lower)
- Moved from 4.10 to 3.73 rear gears and shed almost a tenth
- Top end RPM increased by 800-1000 RPM

**Important Considerations:**
- More power means more stress on all components
- Transmission gets much hotter
- Oil demands increase
- Traction may become an issue
- Braking distance increases
- May need more nose ballast

**Consistency:**
- Until you get experience, nitro can be hard to be consistent with
- Requires constant fuel mix
- Once you figure it out, you will be very consistent
- Takes quite a few laps to get a handle on it

The key is starting with light loads and working up gradually while upgrading hardware as needed.""",
        "keywords": ["nitro performance", "ET improvement", "MPH gain", "horsepower increase", "nitromethane gains"],
        "topic": "Nitromethane - Performance Gains"
    },
    {
        "question": "How much nitromethane should I use and how do I mix it?",
        "answer": """Determining nitro percentage and mixing procedures:

**Starting Out:**
- Begin with light loads (10-25%)
- Work up gradually as you gain experience
- Only increase percentage when you have proper hardware

**Mixing Methods:**
There are two basic ways to run nitro:
1. **AFR Method** - Covered in this guide, works well up to about 80% nitro
2. **Volume Method** - Different approach, difficult to make sense of at first

**AFR Method:**
- Uses stoichiometric values for nitromethane and methanol
- Provides reliable guide for tuning
- The math works!
- Works well up to about 80% nitro
- After 80%, things get unpredictable and you may start melting things

**Mixing Procedure:**
- Mix must be consistent for consistency in performance
- Measure carefully - don't guess
- Use proper containers and mixing equipment
- Store mixed fuel properly

**Percentage Guidelines:**
- **10-25%:** Light loads, minimal hardware changes needed
- **25-50%:** Medium loads, requires some upgrades (steel main caps, better fuel system)
- **50%+:** Heavy loads, requires extensive preparation (aluminum rods, main girdle, etc.)

**Important:** The question "I thought I had to run richer on nitro!" is addressed in the guide - the AFR method uses stoichiometric values which may seem counterintuitive at first.""",
        "keywords": ["nitro percentage", "mixing nitro", "AFR method", "volume method", "nitromethane mixing"],
        "topic": "Nitromethane - Mixing and Percentages"
    },
    {
        "question": "What engine modifications are needed for different nitromethane percentages?",
        "answer": """Engine modifications required vary by nitro percentage:

**Light Loads (10-25%):**
- Right fuel system components (pump, nozzles)
- No special bottom end requirements
- Can run with existing setup if fuel system is adequate

**Medium Loads (25-50%):**
- **Steel main caps** (not stock cast caps!) - essential
- Consider main girdle
- Adequate fuel system (more volume needed above 33%)
- Better oil system
- Head studs recommended
- Wire o-rings in block and copper head gaskets at 50%

**Heavy Loads (50%+):**
- **Aluminum rods** - essential (aluminum absorbs shock loads)
- Steel rods transfer shock to crank and can cause bearing failures
- Main girdle
- Steel main caps (not cast)
- Never use cast iron crank
- Wire o-rings in block
- Copper head gaskets
- Receiver groove in head to accept o-ring (superior seal)
- Head torque: 70 ft/lbs (stock torque not enough)
- Have block honed with torque plate at increased torque value

**Oil System (50%+):**
- Run SAE 50 weight oil (thick oil)
- Oil filter that's easily inspected (Oberg or System One)
- Coarse filter screen for heavy weight oil
- Check filter frequently for flakes and signs of spun bearing
- More main bearing clearance (.004-.005" on mains)
- Titan oil pump adjusted to 80 PSI
- More oil through bearing means less heat
- King bearings recommended (softer, thicker material, fully grooved version available)

**Real-World Failures:**
- Stock 4-bolt main caps broke in two at 50% nitro
- Bearings spun and messed up rod bearings
- Head gaskets blew until proper sealing was implemented

**Important:** Plan ahead and buy the right parts rather than replacing torched parts!""",
        "keywords": ["nitro engine mods", "aluminum rods", "main caps", "head gaskets", "oil system", "engine preparation"],
        "topic": "Nitromethane - Engine Modifications"
    },
    {
        "question": "What is the high-speed bypass and how do I tune it for nitromethane?",
        "answer": """The high-speed bypass is a critical component for nitro tuning:

**What It Is:**
- A bypass system that opens at high RPM to regulate fuel pressure
- Prevents over-fueling at top end
- Can be spring and poppet style or electronic

**How It Works:**
- Cracks open slightly and gradually opens to regulate top pressure
- Does NOT pop open suddenly and dump huge amount of fuel
- Regulates the pressure achieved at high RPM

**Finding the "Knee":**
- The "knee" is where your fuel curve changes
- This is where high-speed should crack open
- If airflow/RPM graph flattens at 7250 RPM, that's where high-speed should open
- Can calculate on paper with proper math
- EGT probe data can help identify the knee - temperature graph should resemble fuel curve shape

**Tuning the High-Speed:**
- Start rich and work lean
- Quit removing shims when performance improvement stops
- Do NOT intentionally keep leaning until it pops out intake
- If it ever pops out injector tubes, GET OUT OF IT - it's too lean!
- Throw small shim in and reduce high-speed pill size

**Pill and Shim Relationship:**
- Bigger main pill = less system pressure = lighter spring needed in high-speed
- For every main pill step (.005) decrease (richer), add one small shim to high-speed to raise bypass pressure
- This is guess work without proper flow testing

**Flow Testing:**
- Spend couple hundred bucks getting system flowed
- High-speed will be right on the money
- Shims can be custom made for each different tune-up

**Weather Adjustments:**
- Need to change things for weather
- Recommendation: for every main pill step decrease, add one small shim to high-speed
- This is really guess work without flow data

**Component Differences:**
- Different check valves have different lengths
- Kinsler quick-disconnect is .125" longer inside than Hilborn
- Must check with regulator, not just use same number of shims
- Wrong setup can begin bypassing at wrong pressure and burn up motor

**Electronic Systems:**
- Electronic lean-out valves with RPM activated switch are more predictable
- Less trouble to setup than spring and poppet style

**Critical Warning:** The high-speed is the best way to torch your motor with nitro. Do the math or get expert help!""",
        "keywords": ["high-speed bypass", "nitro tuning", "fuel pressure", "bypass system", "nitromethane tuning"],
        "topic": "Nitromethane - High-Speed Bypass Tuning"
    },
    {
        "question": "What fuel system components do I need for nitromethane?",
        "answer": """Fuel system requirements for nitromethane:

**Basic Requirements:**
- Adequate fuel pump (not marginal or worn)
- Properly sized nozzles
- System must handle increased fuel volume
- More volume needed above 33% nitro

**Marginal Systems:**
- If your existing fuel system is marginal (worn pump, small nozzles), you won't want to run any nitro
- Marginal methanol setup just won't do for nitro
- Need more volume than methanol-only setup

**Component Checklist:**
- **Fuel Pump:** Must be adequate for increased volume demands
- **Nozzles:** Must be sized correctly for nitro percentage
- **High-Speed Bypass:** Critical for regulating top end pressure
- **Check Valves:** Must be compatible and checked for proper length
- **Fuel Lines:** Must handle increased flow
- **Filters:** Must be adequate for increased flow

**Starting System (30%+ nitro):**
- Consider separate starting system
- Another set of nozzles gravity fed by small vessel
- Quick-connect to motor
- Idle adjustment via needle valve or nozzle orifice changes
- Main fuel system with nitro isn't turned on until motor is running

**System Pressure:**
- Must be properly regulated
- High-speed bypass critical for top end
- Pressure changes with main pill size
- Must do the math or get system flowed

**Flow Testing:**
- Recommended to spend couple hundred bucks getting system flowed
- Ensures high-speed is right on the money
- Allows custom shims for each tune-up
- Prevents costly mistakes

**Component Compatibility:**
- Different brands have different specifications
- Check valve lengths vary (Kinsler .125" longer than Hilborn example)
- Must verify with regulator, not assume same settings work

**The Bottom Line:** You need more volume above 33% nitro, and a marginal methanol setup won't work. Upgrade your fuel system before running nitro!""",
        "keywords": ["nitro fuel system", "fuel pump", "nozzles", "fuel system components", "nitromethane fuel system"],
        "topic": "Nitromethane - Fuel System Requirements"
    },
    {
        "question": "What other modifications are needed when running higher percentages of nitromethane?",
        "answer": """Additional modifications needed for higher nitro percentages:

**Transmission:**
- Gets much hotter than before
- Build external cooler unit that plugs into car
- Circulates trans fluid through cooler in pits
- Works great, no extra weight
- Converter may need re-stalling (5800 RPM to 6800 RPM at 50%)
- If you go back to straight methanol, things are mismatched again

**Gearing:**
- Nitro likes to be lugged
- May need taller gears (moved from 4.10 to 3.73)
- Shed almost a tenth from gear change alone
- Taller tires can help

**Shift Points:**
- Shift point will likely change
- Car may like to be shifted 1000 RPM lower than on methanol
- Short shifting works well

**Traction:**
- May need more nose ballast with added power
- Traction may now be an issue
- Tire pressures might need tweaking
- May experience tire shake

**Braking:**
- If you pick up 10 MPH, takes more distance or more aggressive braking to stop
- Plan for increased stopping distance

**Oil System:**
- Higher demands on oil
- Feed it SAE 50 weight oil
- Get oil filter that's easily inspected (Oberg or System One)
- Use coarse filter screen if running heavy weight oil
- Check frequently for flakes and signs of spun bearing
- Keep spare set of rod and main bearings in trailer
- Run more main bearing clearance (.004-.005" on mains)
- Straight SAE 50 oil
- Titan oil pump adjusted to 80 PSI
- More oil through bearing means less heat
- King bearings recommended (softer, thicker material, fully grooved version)

**Oil Preheating:**
- SAE 50 oil is very thick
- If running bronze gear on mag, want to preheat oil
- Heat oil first and pour it in or use pan warmer
- Built 7 quart steel vessel with heater probe and heat blanket
- When gauge says 180°, hook up air hose and pre-lube motor with hot oil
- Helps chase air out of filter and gets warm oil into motor in about 60 seconds

**Weak Components:**
- If something is weak and ready to break (tranny, axles, crankshaft), throwing another 100 HP at it may find it
- Be ready for component failures
- Upgrade weak links before they break""",
        "keywords": ["nitro modifications", "transmission cooler", "gearing", "oil system", "traction", "nitromethane setup"],
        "topic": "Nitromethane - Additional Modifications"
    },
    {
        "question": "What is the AFR method for tuning nitromethane?",
        "answer": """The AFR (Air/Fuel Ratio) method is one of two ways to run nitro:

**What It Is:**
- Uses stoichiometric values for nitromethane and methanol
- Provides reliable guide for tuning
- The math works!
- Works well up to about 80% nitro

**Limitations:**
- After 80% nitro, things get out of control and become very unpredictable
- At that point, if you don't make the jump to volume method, you will start melting things
- Volume method is different beast entirely and difficult to make sense of at first

**How It Works:**
- Based on stoichiometric air/fuel ratios
- Assumes optimal air/fuel mixture remains constant (it does)
- Uses mathematical calculations to determine fuel requirements
- Provides reliable tuning guide

**Key Principle:**
- The question "I thought I had to run richer on nitro!" is addressed
- AFR method uses stoichiometric values which may seem counterintuitive
- The math works even though it may not seem right at first

**Tuning Process:**
- Calculate fuel requirements based on stoichiometric values
- Adjust fuel system accordingly
- Monitor performance and adjust as needed
- Works reliably up to 80% nitro

**When to Use:**
- Best for beginners starting with nitro
- Works well for percentages up to 80%
- Provides reliable, predictable tuning
- Easier to understand than volume method

**Transition Point:**
- At 80% nitro, must transition to volume method
- Volume method is completely different approach
- Requires different understanding and setup

The AFR method is the recommended starting point for those new to nitro tuning.""",
        "keywords": ["AFR method", "nitro tuning", "stoichiometric", "air fuel ratio", "nitromethane tuning method"],
        "topic": "Nitromethane - AFR Tuning Method"
    }
]

ARTICLE_URL = "https://www.fuelinjectionent.com/nitro_new.php"
ARTICLE_AUTHOR = "Spud Miller - Fuel Injection Enterprises"


def main():
    """Add Spud's Nitro Notes to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in NITRO_KNOWLEDGE:
        try:
            LOGGER.info(f"Adding: {entry['question'][:60]}...")
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{entry['question']}\n\n{entry['answer']}",
                metadata={
                    "question": entry["question"],
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": "Spud's Nitro Notes - Fuel Injection Enterprises",
                    "url": ARTICLE_URL,
                    "author": ARTICLE_AUTHOR,
                    "category": "Nitromethane Tuning"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                source="Spud's Nitro Notes - Fuel Injection Enterprises",
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
    LOGGER.info(f"Total entries: {len(NITRO_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nSpud's Nitro Notes have been added to the knowledge base!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"Author: {ARTICLE_AUTHOR}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - Introduction to nitromethane")
    LOGGER.info(f"  - Risks and safety considerations")
    LOGGER.info(f"  - Legality and track rules")
    LOGGER.info(f"  - Safety procedures")
    LOGGER.info(f"  - Nitro characteristics and performance")
    LOGGER.info(f"  - Performance gains")
    LOGGER.info(f"  - Mixing and percentages")
    LOGGER.info(f"  - Engine modifications by percentage")
    LOGGER.info(f"  - High-speed bypass tuning")
    LOGGER.info(f"  - Fuel system requirements")
    LOGGER.info(f"  - Additional modifications")
    LOGGER.info(f"  - AFR tuning method")


if __name__ == "__main__":
    main()

