#!/usr/bin/env python3
"""
Add racetrack terminology glossary to the AI Chat Advisor knowledge base.
Scrapes and adds comprehensive track terminology definitions.
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

# Racetrack terminology from the glossary
RACETRACK_TERMS = [
    {
        "term": "9 and 3",
        "definition": "This refers to your hands on the wheel and the hands of a clock. In this case, the 9 and 3 o'clock position. This allows drivers to securely hold the wheel, due to its ergonomic shape, all while allowing them to freely rotate the steering wheel from one direction to the other. By placing your hands here, you can safely navigate a track without having to remove your hands from this position.",
        "category": "Driving Technique"
    },
    {
        "term": "Aerodynamic",
        "definition": "The shape of a car and its body that allow drag to be reduced as air passes over and around it.",
        "category": "Vehicle Design"
    },
    {
        "term": "Active Aerodynamics",
        "definition": "Active aerodynamics are added to vehicles, giving them the ability to make adjustments based on real-time situations, like high speeds, in order to keep air moving past (over, through, around) the car, allowing it to stay planted to the ground.",
        "category": "Vehicle Design"
    },
    {
        "term": "All Wheel Drive (AWD)",
        "definition": "This refers to the axle of the car which 'drives' or propels the vehicle forwards or backward. Vehicles can be front wheel drive (FWD), rear wheel drive (RWD), all wheel drive (AWD), or four wheel drive (4WD).",
        "category": "Vehicle Design"
    },
    {
        "term": "Apex",
        "definition": "In motorsports, this term refers to the 'midpoint' or neutral section of a turn. When 'attacking' a corner, the driver's goal is to 'clip' the apex, by successfully directing the car to and through the midpoint or apex of the turn.",
        "category": "Track Navigation"
    },
    {
        "term": "Armco",
        "definition": "Armco refers to a specific type of barrier used on roads and race tracks alike. These off-road barriers are used to aid in the protection of exterior/foreign objects or hazardous sections of road/track that might be susceptible to low impact.",
        "category": "Track Safety"
    },
    {
        "term": "Balance",
        "definition": "Every vehicle on the road has its own balance. This is based on cars' weight and center of gravity, and forces applied to the car such as braking, turning, etc. Maintaining a balance during cornering is necessary, in order to keep your grip on the pavement.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Bend",
        "definition": "A slight adjustment in the direction of the track.",
        "category": "Track Navigation"
    },
    {
        "term": "Black Flag",
        "definition": "A black flag is usually seen in conjunction with a racer's number, notifying that the driver must return to the pits. This means that car has been excluded from the race.",
        "category": "Track Flags"
    },
    {
        "term": "Blend Line",
        "definition": "The blend line divides the pit lane exit from the cars on the track. This lane is utilized by cars who are re-entering the track, from the pit area. It is imperative that all cars on track maintain their distance from the blend line, to avoid collision with slower moving vehicles. It's equally important for cars who are re-entering the track, to stay within bounds of the blend line to avoid a collision with faster moving vehicles.",
        "category": "Track Navigation"
    },
    {
        "term": "Blind Spot",
        "definition": "Every vehicle has its blind spots. In many cases, these are located on both sides of the vehicle. It's important to make sure mirrors are in the correct position so you can minimize the space on either side of the car which is 'blind' from the driver.",
        "category": "Driving Technique"
    },
    {
        "term": "Blind Turn",
        "definition": "Many tracks with features such as elevation changes, often have sections of the track that are not visible (blind) as you approach them. This just means, that you must be prepared and knowledgeable of what's on the other side of that turn, so as to avoid contact with a structure, another driver, or going off track.",
        "category": "Track Navigation"
    },
    {
        "term": "Brake Markers",
        "definition": "Brake Markers are numbered signs located at various turns on a race track. These typically start with a number such as '4' and go down to '1' as you approach your turn-in point. These signs are meant to indicate you're approaching a braking zone, and the suggested distance to begin and end your braking.",
        "category": "Track Navigation"
    },
    {
        "term": "Brake Zone",
        "definition": "This is a section of the track, leading to your turn-in point, where braking is meant to take place. Often times, this zone can be identified by brake markers, however, this must be managed and understood by the driver and their vehicle.",
        "category": "Track Navigation"
    },
    {
        "term": "Burnout",
        "definition": "This is a scenario where a driver forces the front or rear axle of the vehicle spin its wheels for a duration of time, causing the tire to burn and therefore smoke. This is a result of stomping on the gas pedal in a powerful vehicle, from a stop or at a very low speed. This is not an ideal scenario for the track and should not be practiced outside of a drag racing – to generate heat into the tires.",
        "category": "Driving Technique"
    },
    {
        "term": "Carousel",
        "definition": "The Carousel is a circular shaped turn, featured at many racetracks. Carousels are often constant radius turns that require a driver to nearly complete an entire circle. This type of turn can be either on or off camber (incline/decline).",
        "category": "Track Navigation"
    },
    {
        "term": "Chassis",
        "definition": "This is typically known as the base frame of a vehicle. In some cases, several vehicles in a manufacturer's lineup might be built around one chassis, whereas a race car has a purpose-built chassis.",
        "category": "Vehicle Design"
    },
    {
        "term": "Checkered Flag",
        "definition": "This flag is waved to notify drivers the race has started, and when it has ended.",
        "category": "Track Flags"
    },
    {
        "term": "Chicane",
        "definition": "The chicane is usually one of the slowest turns on the track. This is a series of turns that alternate in direction, typically in an S-shaped pattern. These turns are designed to slow down vehicles before a straightaway.",
        "category": "Track Navigation"
    },
    {
        "term": "Corner Entry",
        "definition": "The point at which a driver begins to turn into a corner. This is the initial phase of navigating a turn, where the driver positions the car and begins to apply steering input.",
        "category": "Track Navigation"
    },
    {
        "term": "Corner Exit",
        "definition": "The point at which a driver completes a turn and begins to accelerate out of the corner. Proper corner exit is crucial for maintaining speed down the following straightaway.",
        "category": "Track Navigation"
    },
    {
        "term": "Oversteer",
        "definition": "Oversteer occurs when the rear tires lose grip before the front tires during cornering. This causes the rear of the car to slide out, requiring the driver to counter-steer to maintain control.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Understeer",
        "definition": "While entering a turn/corner, the momentum leading the car forward must be met by grip from the front tires, and later propelled around the turn while accelerating. If the speed and momentum in which a turn is entered, exceeds the grip of the tires, this will lead to understeer. This means the car will 'push' itself away from the apex of the turn.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Racing Line",
        "definition": "The optimal path through a corner that allows for the highest speed. The racing line typically involves entering wide, hitting the apex, and exiting wide to maximize cornering speed.",
        "category": "Track Navigation"
    },
    {
        "term": "Track Out",
        "definition": "While driving the racing line, you will guide your car from the outside to the inside of a turn, followed by the outside. The process in which the car is guided to the outside is called 'tracking out'.",
        "category": "Track Navigation"
    },
    {
        "term": "Turn In",
        "definition": "Simply put this refers to entry position of a corner or turn. While driving a vehicle on track, your goal is to put your vehicle in the right position to execute a proper turn in as you point toward the apex of the turn.",
        "category": "Track Navigation"
    },
    {
        "term": "Tachometer",
        "definition": "This instrument can be found in nearly every vehicle, and is typically beside the speedometer. The Tachometer measures revolutions per minute or RPM.",
        "category": "Vehicle Instruments"
    },
    {
        "term": "Target Fixation",
        "definition": "This is when a person focuses on one object and begins to navigate towards that object. This is a situation you want to avoid while driving on the track because it can cause you to leave the boundaries of the track or worse.",
        "category": "Driving Technique"
    },
    {
        "term": "Torque",
        "definition": "In its simplest definition, torque refers to the rotational force generated by a motor and its connection with the driving axle of a vehicle. Torque works in conjunction with horsepower.",
        "category": "Vehicle Performance"
    },
    {
        "term": "Smooth Inputs",
        "definition": "Smooth inputs refers to the method in which a driver interacts with a vehicle's controls. In this case, we're referring to 'smoothly' making steering, braking and accelerating inputs, as opposed to quick/stabbing actions.",
        "category": "Driving Technique"
    },
    {
        "term": "Roll on the Throttle",
        "definition": "This is a term often used in conjunction with 'smooth inputs' as it refers to your interaction with the throttle/gas pedal. In this case, the interaction is considered to be a 'rolling' motion, rather than a stabbing action. This helps build speed and avoid loss of traction. Think of adjusting the volume on your stereo and how you interact with a volume knob.",
        "category": "Driving Technique"
    },
    {
        "term": "String Theory",
        "definition": "The string theory is meant to describe the position the steering wheel in relation to accelerating or braking while driving on the track. The theory suggests that, when the wheel is turned, your foot is 'lifted' from the brake pedal or the accelerator then as the wheel returns back to its straight position, your foot can begin to depress either pedal. Thus insinuating your foot and the wheel is tied to a string.",
        "category": "Driving Technique"
    },
    {
        "term": "Standing on the Brake",
        "definition": "When discussing braking scenarios, this phrase refers to applying pressure to the brake. If you were to 'stand' on the brake, you are applying maximum pressure for a duration of time.",
        "category": "Driving Technique"
    },
    {
        "term": "Stomp on the Gas/Brake",
        "definition": "Stopping on the gas is a term used to describe the action of abruptly and forcefully pushing your foot into either the gas or brake pedal.",
        "category": "Driving Technique"
    },
    {
        "term": "Slip Angle",
        "definition": "This is the angle between a rolling wheel's actual direction of travel and the direction towards which it is pointing.",
        "category": "Vehicle Dynamics"
    },
    {
        "term": "Yellow Flag",
        "definition": "This flag will be displayed at a corner worker stations to alert drivers usually of a spin or car off track. When a yellow flag is shown, there's no passing between the corner worker station and the incident.",
        "category": "Track Flags"
    },
    {
        "term": "Waving Yellow Flag",
        "definition": "When a yellow flag is waiving the incident ahead is on the racing surface. Extra caution is advised.",
        "category": "Track Flags"
    },
    {
        "term": "Standing Yellow Flag",
        "definition": "When a yellow flag is displayed but not being waved, the incident ahead is usually off the racing surface. Drivers should always be aware of vehicles merging back onto the racing surface.",
        "category": "Track Flags"
    },
    {
        "term": "White Flag",
        "definition": "This flag is waived when there's a slow moving vehicle on the track, such as an emergency vehicle or other.",
        "category": "Track Flags"
    },
    {
        "term": "Warm Up Laps",
        "definition": "Warm up laps are executed to ensure that a vehicle which intends on driving on a race track, is operating at optimal temperature. This refers to the engine, brakes, tires, and more.",
        "category": "Track Procedures"
    },
    {
        "term": "Run-Off Area",
        "definition": "A run-off area refers to sections where a car might be prone to leave the track. Run-offs help protect drivers from external surroundings which might cause danger/harm. There are several types of runoffs, such as Grass, gravel, sand or even an added section of tarmac.",
        "category": "Track Safety"
    },
    {
        "term": "Sections",
        "definition": "A race track typically can be broken down into sections. In motorsports, driver's times are most often measured by their time through sections, and ultimately completing a lap around the track.",
        "category": "Track Navigation"
    },
    {
        "term": "Straightaway",
        "definition": "This is a section of the track that does not have any turns.",
        "category": "Track Navigation"
    },
    {
        "term": "Sweeper",
        "definition": "This is a generalized term used to describe the sweeping motion of a long and fast turn/corner on a track.",
        "category": "Track Navigation"
    },
    {
        "term": "Semi-automatic Transmission",
        "definition": "This refers to the type of transmission in a car, which can be shifted manually or automatically and in a combination of both.",
        "category": "Vehicle Design"
    },
    {
        "term": "Snell Rating SA",
        "definition": "Snell memorial foundation is a not-for-profit organization that sets standards for protective headgear used for over the road use and racing. The standards set by Snell are the industry's toughest.",
        "category": "Safety Equipment"
    },
    {
        "term": "Roll Bar/Cage",
        "definition": "This a tubular reinforcement structure that is built into a vehicle. It provides added rigidity and stability to a vehicle, as well as safety for those who are involved in motorsports.",
        "category": "Safety Equipment"
    },
    {
        "term": "Right Seat",
        "definition": "This is the passenger seat of a vehicle typically occupied by an instructor, while on track.",
        "category": "Track Procedures"
    },
    {
        "term": "Redline",
        "definition": "The redline is the maximum RPM that your engine can safely operate at. You can find this on your vehicle's dashboard, by looking at your tachometer. There you will see the red line which ends at a number which your vehicle's engine is limited to.",
        "category": "Vehicle Performance"
    },
    {
        "term": "Waivers",
        "definition": "This is a formal document presented to each individual who looks to enter a race track facility. The document has legal copy expressing risk and ownership of that risk by those who enter the facility.",
        "category": "Track Procedures"
    },
    {
        "term": "Wheel Chock",
        "definition": "This device is used to help keep cars in position while they're in the pits or paddock. To keep this from happening, they are wedged beneath a rear or front tire of the car.",
        "category": "Track Procedures"
    }
]

ARTICLE_URL = "https://www.thextremexperience.com/racetrack-glossary/"


def main():
    """Add racetrack terminology to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    # Group terms by category for better organization
    categories = {}
    for term in RACETRACK_TERMS:
        cat = term["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(term)
    
    # Add individual terms
    for term in RACETRACK_TERMS:
        try:
            LOGGER.info(f"Adding: {term['term']}...")
            
            question = f"What is {term['term']} in racetrack terminology?"
            answer = f"{term['term']}: {term['definition']}"
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{question}\n\n{answer}",
                metadata={
                    "term": term["term"],
                    "category": term["category"],
                    "source": "Xtreme Xperience Racetrack Glossary",
                    "url": ARTICLE_URL,
                    "topic": "Racetrack Terminology",
                    "keywords": f"racetrack, {term['term'].lower()}, {term['category'].lower()}, track terminology"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=question,
                answer=answer,
                source="Xtreme Xperience Racetrack Glossary",
                url=ARTICLE_URL,
                keywords=[term["term"].lower(), term["category"].lower(), "racetrack", "terminology"],
                topic=f"Racetrack Terminology - {term['category']}",
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
            
            question = f"What are the {category} terms in racetrack terminology?"
            answer = f"**{category} Terminology:**\n\n{term_list}"
            
            vector_store.add_knowledge(
                text=f"{question}\n\n{answer}",
                metadata={
                    "category": category,
                    "source": "Xtreme Xperience Racetrack Glossary",
                    "url": ARTICLE_URL,
                    "topic": f"Racetrack Terminology - {category}",
                    "keywords": f"racetrack, {category.lower()}, terminology, glossary"
                }
            )
            
            added_count += 1
            LOGGER.info(f"  Category summary added")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add category summary: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total terms: {len(RACETRACK_TERMS)}")
    LOGGER.info(f"Categories: {len(categories)}")
    LOGGER.info(f"Successfully added: {added_count} entries")
    LOGGER.info(f"\nRacetrack terminology glossary has been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nCategories covered:")
    for cat in sorted(categories.keys()):
        LOGGER.info(f"  - {cat} ({len(categories[cat])} terms)")


if __name__ == "__main__":
    main()

