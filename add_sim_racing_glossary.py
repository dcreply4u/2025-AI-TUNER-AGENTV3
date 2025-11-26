#!/usr/bin/env python3
"""
Add sim racing and motorsports terminology glossary to the AI Chat Advisor knowledge base.
Scrapes and adds comprehensive sim racing terminology definitions from Asetek.
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

# Sim racing terminology from Asetek glossary
SIM_RACING_TERMS = [
    {
        "term": "Aerodynamics",
        "definition": "Aerodynamics is the study of airflow around an object and is a crucial part of Formula One and racing in general. The F1 teams use a lot of money and energy to gain aerodynamic advantages like minimization of air resistance and maximum downforce.",
        "category": "Vehicle Design"
    },
    {
        "term": "Apex",
        "definition": "Apex is the center point of a curve on a racetrack. Hitting the apex is essential for the optimal acceleration out of the curve. Therefore, professional racers always try to hit the apex in hopes of clocking the fastest lap times.",
        "category": "Track Navigation"
    },
    {
        "term": "BAR",
        "definition": "BAR is a metric unit of pressure. In racing, BAR is used as a term when applying pressure to the brake. When you measure in BAR, you can adjust your braking technique to the corresponding amount of pressure.",
        "category": "Measurement Units"
    },
    {
        "term": "Belt-driven",
        "definition": "Belt-driven wheelbases are often seen as a small step up compared to gear-driven wheelbases. Belt-driven wheelbases utilize a belt–and–pulley system to amplify the strength of a small motor. However, using this system is at the cost of more accurate force feedback.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Blistering",
        "definition": "Blistering is the consequence of an overheated tire. Too much heat can cause the rubber to soften, and eventually, small pieces of rubber will detach from the tire. Several scenarios can cause blistering. For example, an inappropriate tire compound where the tires are too soft for the circuit conditions will most likely overheat the tires.",
        "category": "Tire Management"
    },
    {
        "term": "Dead Zone",
        "definition": "Dead zone is a term mostly used in sim racing. Dead zones are lower or upper limits that you can calibrate according to your racing preferences. Dead zones are useful when you want to reach 100% without pushing the throttle or brake pedals to max capacity. For example, if you have the habit of resting your foot on the brake pedal while racing, you can insert a dead zone in your brake, so it doesn't register your input before you press more than the amount you've calibrated it to.",
        "category": "Sim Racing Setup"
    },
    {
        "term": "Direct Drive",
        "definition": "Direct drive is a way of making wheelbases for simulator racing. Unlike belt-driven or gear-driven wheelbases, there are no external motors used to power the driveshaft, as it is the driveshaft itself that is motorized. Direct drive wheelbases consist of a servo motor that is directly attached to the wheel. This allows for more precise and detailed force feedback compared to other options on the market. It is often the more expensive solution regarding wheelbases for simulator racing.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Downforce",
        "definition": "Downforce is a racing term that you hear a lot in racing – and especially Formula 1. Downforce is the downward lift force that is created by aerodynamic factors like wings and suspension parts on a moving car. For example, racecars are designed in a way that pushes the car to the track. Therefore, downforce can give the car a better grip at higher speeds.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Drag",
        "definition": "Drag is the aerodynamic resistance a moving object experiences when moving forward.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "DRS (Drag Reduction System)",
        "definition": "DRS is short for Drag Reduction System and is an adjustment the driver can make on the rear wing to increase top speed and promote overtaking. DRS can only be used when a car is less than one second behind another car. Furthermore, DRS is restricted to pre-determined areas on the racetrack during the race.",
        "category": "Racing Systems"
    },
    {
        "term": "Force Feedback",
        "definition": "In sim racing, force feedback is a simulation of physical resistance, to provide the driver with a feeling of realism and immersion. Force feedback tries to simulate the same feeling a race driver would experience when racing in real life. The simulated feeling is often created by the wheelbase, and different wheelbase systems (belt-driven, direct drive and gear-driven) provide different variations of force feedback.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Gear-driven",
        "definition": "This is the most affordable solution to making wheelbases. This solution takes advantage of helical gears to connect the motor to the steering column. The helical gears used in these wheelbases may provide a less smooth experience and provide less detailed force feedback.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Hairpin",
        "definition": "A hairpin is used to describe a specific type of turn in motorsports. A hairpin turn is a bend in the racetrack where the inner angle is very acute. Hairpin turns are often 180 degrees.",
        "category": "Track Navigation"
    },
    {
        "term": "Hall Sensor",
        "definition": "Hall sensor-based pedals function with a magnet that measures the travel of the pedals more precisely than a potentiometer. Also, unlike a potentiometer, hall sensor-based pedals are less affected by dust and such getting into the components.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Heel-and-Toe",
        "definition": "Heel-and-toe is a driving technique that involves operating the brake and the throttle simultaneously with the right foot, while activating the clutch with the left foot. The heel-and-toe technique is used before entering a turn. If the technique is executed correctly, it allows the racer to gain engine speed and engage the lower gear to accelerate out of the turn without losing more speed than is necessary.",
        "category": "Driving Technique"
    },
    {
        "term": "Hydraulic",
        "definition": "Hydraulic-based pedals measure braking force through the hydraulic pressure created when compressing the pedal. This results in a more accurate simulation of a brake pedal in a real-world racecar.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Loadcell",
        "definition": "Loadcell-based pedals measure braking force using a loadcell. This differs from potentiometers, as loadcells measure the force put onto the pedals rather than the pedals' compressed distance.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Newton Meter (Nm)",
        "definition": "A unit of measurement for torque. In sim racing, it is used in conjunction with the maximum amount of feedback or force you can get from a wheelbase.",
        "category": "Measurement Units"
    },
    {
        "term": "Oversteer",
        "definition": "Oversteer is a tendency of a car's handling characteristics. When a car oversteers, its rear end tends to slide when either entering or exiting a corner. This handling characteristic may make the car difficult to predict and more difficult to drive.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Potentiometer",
        "definition": "Potentiometers, like hall-sensor pedals, measure the travel, to determine force. Unlike hall-sensors, potentiometers are based on moving mechanical parts to measure travel. These moving parts may wear and accumulate dust, decreasing accuracy, and may ultimately cause them to fail.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Pole Position",
        "definition": "Pole position is the starting front position of all the cars in the race. When a car is in pole position before the start of the race, it is always in front of the remaining cars.",
        "category": "Racing Procedures"
    },
    {
        "term": "Simulators (Games)",
        "definition": "A genre of racing games that focuses on simulation and authenticity. There can be discussions about whether a racing game is a true simulator or more of an arcade game. While F1 or Gran Turismo may be simulators to more casual gamers, dedicated sim racers would rather ascribe that term to games such as iRacing, Assetto Corsa Competizone or RFactor 2.",
        "category": "Sim Racing Software"
    },
    {
        "term": "Slipstreaming",
        "definition": "Slipstreaming is when a driver can benefit from the car in front to reduce drag. When slipstreaming is executed correctly, the following car can gain superior speed to overtake.",
        "category": "Driving Technique"
    },
    {
        "term": "Stint",
        "definition": "A stint is the duration between a car leaving the pit lane after service and it coming back to the pit lane for further service. For instance, in endurance races, a stint is the time between a racecar leaving the pit with a full tank of fuel, and it coming back in to be refilled.",
        "category": "Racing Procedures"
    },
    {
        "term": "Straight",
        "definition": "A straight is a part of a racetrack that is either completely straight or only curves slightly, so the racing cars do not have to slow down to make the turns. They are often followed by narrower corners to slow the cars back down, creating an ideal setting for an overtake.",
        "category": "Track Navigation"
    },
    {
        "term": "Telemetry",
        "definition": "Telemetry is data sent from the car to the mechanics and engineers, and vice versa. The mechanics and engineers can keep track of everything that happens in the car due to telemetry. Telemetry is a key factor in understanding the car's condition, and how to make it perform better.",
        "category": "Data Analysis"
    },
    {
        "term": "Trail Braking",
        "definition": "Trail braking is an advanced driving technique, in which you brake in a specific way when entering a corner. Trail braking is a combination of braking hard, and then slowly taking your foot off the brake as you turn and increase speed again. Perfect use of trail braking enables the racer to brake a few moments later and control the car, to hit curves and corners with more momentum.",
        "category": "Driving Technique"
    },
    {
        "term": "Travel (Pedal)",
        "definition": "Travel (or throw) in pedals is the amount of movement allowed by the pedal set before the pedal hits a bump stop to avoid it going further. Some pedal sets allow the pedal to be depressed further than others, i.e., allows for more travel. The travel of a throttle or clutch pedal is usually long, while a brake pedal can benefit from a very short travel.",
        "category": "Sim Racing Hardware"
    },
    {
        "term": "Understeer",
        "definition": "Understeer, like oversteer, is a characteristic of the way a car handles. The opposite of oversteer, understeer means that the car slides on the front tires and not the rear tires. This means the car is attempting to go straight even when the driver is turning the steering wheel. This behavior is usually more predictable compared to oversteer.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Wheelbase",
        "definition": "A wheelbase is the hardware placed behind the steering wheel in a sim racing setup. The wheelbase is essentially the centerpiece of the setup because it combines all the parts in the rig. Wheelbases are primarily constructed in three different ways: gear-driven, belt-driven, and direct drive.",
        "category": "Sim Racing Hardware"
    }
]

# Flag definitions
FLAG_TERMS = [
    {
        "term": "Black Flag",
        "definition": "A black flag may have several meanings, depending on which sanctioning body is responsible for the racing series. For example, in FIA sanctioned series, a black flag means that the driver in question has been disqualified. However, in NASCAR, the black flag means you must go to the pits and serve a penalty.",
        "category": "Track Flags"
    },
    {
        "term": "Blue Flag",
        "definition": "A signal to let faster drivers by as they are a lap or more ahead of you.",
        "category": "Track Flags"
    },
    {
        "term": "Checkered Flag",
        "definition": "The race is finished.",
        "category": "Track Flags"
    },
    {
        "term": "Green Flag",
        "definition": "This flag signals the start of the race.",
        "category": "Track Flags"
    },
    {
        "term": "Mechanical Flag (Meatball Flag)",
        "definition": "Also known as the 'meatball-flag'. The flag is black with an orange circle in the middle. It indicates you have been involved in an incident and race control deems your car unsafe in its current state, so you must pit for repairs.",
        "category": "Track Flags"
    },
    {
        "term": "Red Flag",
        "definition": "This signals the race has been stopped. This can be for several reasons, such as weather and track conditions. However, it can also be because of an incident involving several cars, or other serious concerns.",
        "category": "Track Flags"
    },
    {
        "term": "White Flag",
        "definition": "Signals the beginning of the final lap of the race.",
        "category": "Track Flags"
    },
    {
        "term": "Yellow Flag",
        "definition": "There has been an incident ahead, slow down and proceed with caution.",
        "category": "Track Flags"
    }
]

ARTICLE_URL = "https://www.asetek.com/simsports/guides/glossary-sim-racing-and-motorsports-terms/"


def main():
    """Add sim racing terminology to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    all_terms = SIM_RACING_TERMS + FLAG_TERMS
    
    # Group terms by category for better organization
    categories = {}
    for term in all_terms:
        cat = term["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(term)
    
    # Add individual terms
    for term in all_terms:
        try:
            LOGGER.info(f"Adding: {term['term']}...")
            
            question = f"What is {term['term']} in sim racing and motorsports?"
            answer = f"{term['term']}: {term['definition']}"
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{question}\n\n{answer}",
                metadata={
                    "term": term["term"],
                    "category": term["category"],
                    "source": "Asetek Sim Racing Glossary",
                    "url": ARTICLE_URL,
                    "topic": "Sim Racing and Motorsports Terminology",
                    "keywords": f"sim racing, {term['term'].lower()}, {term['category'].lower()}, motorsports, terminology"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=question,
                answer=answer,
                source="Asetek Sim Racing Glossary",
                url=ARTICLE_URL,
                keywords=[term["term"].lower(), term["category"].lower(), "sim racing", "motorsports", "terminology"],
                topic=f"Sim Racing Terminology - {term['category']}",
                confidence=0.9,
                verified=True
            )
            
            added_count += 1
            LOGGER.info(f"  Successfully added")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add term: {e}")
    
    # Add category summaries
    for category, terms in categories.items():
        try:
            LOGGER.info(f"Adding category summary: {category}...")
            
            term_list = "\n".join([f"- **{t['term']}**: {t['definition']}" for t in terms])
            
            question = f"What are the {category} terms in sim racing and motorsports?"
            answer = f"**{category} Terminology:**\n\n{term_list}"
            
            vector_store.add_knowledge(
                text=f"{question}\n\n{answer}",
                metadata={
                    "category": category,
                    "source": "Asetek Sim Racing Glossary",
                    "url": ARTICLE_URL,
                    "topic": f"Sim Racing Terminology - {category}",
                    "keywords": f"sim racing, {category.lower()}, terminology, glossary"
                }
            )
            
            added_count += 1
            LOGGER.info(f"  Category summary added")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add category summary: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total terms: {len(all_terms)}")
    LOGGER.info(f"Categories: {len(categories)}")
    LOGGER.info(f"Successfully added: {added_count} entries")
    LOGGER.info(f"\nSim racing and motorsports terminology glossary has been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nCategories covered:")
    for cat in sorted(categories.keys()):
        LOGGER.info(f"  - {cat} ({len(categories[cat])} terms)")


if __name__ == "__main__":
    main()

