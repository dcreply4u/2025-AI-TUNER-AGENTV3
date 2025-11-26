"""
Add Hot Rod Dyno Testing Guide to Knowledge Base
Scrapes and ingests the comprehensive dyno testing guide from Hot Rod magazine.
"""

import logging
from services.vector_knowledge_store import VectorKnowledgeStore
from services.knowledge_base_manager import KnowledgeBaseManager
from services.knowledge_base_file_manager import KnowledgeBaseFileManager
from typing import Dict, Any, List

LOGGER = logging.getLogger(__name__)

ARTICLE_URL = "https://www.hotrod.com/how-to/hppp-1012-dyno-testing-guide"
ARTICLE_TITLE = "Dyno Testing Guide - Let The Good Times Roll!"
ARTICLE_TOPIC = "Dyno Testing"

# Content extracted from the article
DYNO_GUIDE_CONTENT = [
    {
        "title": "Chassis Dyno Types",
        "content": """There are two types of chassis dynos you are most likely to encounter: inertia and load-bearing (or brake).

**Inertia Dynamometer:**
- Power measurements are derived using the fixed mass of the roller or drum
- During a pull, the dyno's computer measures rpm and the acceleration rate of that fixed mass (no other load applied) to calculate torque and horsepower
- Some inertia dynos tend to produce higher power numbers than load-bearing dynos based on how they perform their calculations

**Load-Bearing Dynamometer:**
- Employs a brake (most use an eddy current brake) to apply an adjustable load on the engine
- The computer notes the applied braking torque and measures the engine's ability to maintain or raise the rpm against it via inputs from a speed sensor and strain gauge to calculate torque and horsepower
- Provides steady-state load in order to tune or diagnose the engine at a certain rpm
- Provides a test that accurately depicts the on-the-road or on-the-track experience of the car
- These characteristics are not shared by inertia dynos""",
        "keywords": ["chassis dyno", "inertia dyno", "load-bearing dyno", "eddy current brake", "dyno types", "torque", "horsepower"],
        "topic": "Dyno Testing - Types"
    },
    {
        "title": "Choosing a Dyno Shop",
        "content": """Finding a qualified shop is paramount to getting an efficient dyno session.

**Considerations:**
1. Determine your particular requirements, how involved in the process you want to get, and honestly evaluate your skill level
2. Do you want to drop your car off and have all the work done, or purchase just dyno and operator time so you can do your own tuning?
3. Visit a prospective shop before you decide - discuss your goals with the staff
4. Ask about their qualifications with regard to your vehicle if you want the shop to handle any tuning
5. Look around the shop - a properly sized fan should be available to cool the engine, and access to the dyno roller should not interfere with any body panels or air dams

**Equipment Requirements:**
- Data-acquisition systems to work with the dyno software
- Wide-band, five-wire, oxygen-sensor-equipped, fast-acting air/fuel ratio meter that can provide a graph or printout for each pull
- An OE oxygen-sensor-based meter isn't fast enough and will not be accurate at a mixture strength other than 14.7:1

**Pricing:**
- Many shops provide a charge for the first hour, and then a reduced rate for each hour after that
- Discuss appointment and cancellation policy, fees, and your involvement in the session""",
        "keywords": ["dyno shop", "dyno operator", "wideband O2 sensor", "air/fuel ratio", "data acquisition", "dyno pricing"],
        "topic": "Dyno Testing - Shop Selection"
    },
    {
        "title": "Prepping Your Vehicle for Dyno Testing",
        "content": """A lack of preparation wastes more dyno time than any other factor. If your vehicle has mechanical issues or leaks, dyno time will be a waste of money until they are fixed.

**Safety Concerns:**
- Major safety concern: condition of the universal joints in the driveshaft, and the drive wheels and tires
- Failure of these components at 100 mph on the rollers can have devastating results

**Pre-Dyno Maintenance:**
- Perform a tuneup and install fresh:
  - Air filter
  - Fuel filter
  - Spark plugs
  - Distributor cap and rotor
  - Oil and oil filter
  - PCV valve
- Check ignition wires, coil, EGR system (if equipped), and carburetor linkage for proper operation

**Carbon Removal:**
- Consider how much carbon has built up on the pistons, in the combustion chambers, and behind the intake valves
- Add a high-quality chemical treatment such as Chevron Techron to the fuel to clean them out
- Removing the carbon deposits will ensure that your created air/fuel ratio is actually delivered to the chambers
- Run that tankful of gas all the way through the system and replace it with fresh fuel prior to the dyno session

**Fuel Selection:**
- Don't show up with 87 octane in the tank if you know 93 octane will provide better results
- Conversely, don't tune on 93 octane or race fuel if you plan to run 87 on the street

**What to Bring:**
- Pack anything and everything that you may require: high-octane fuel, nitrous, jets, tools and timing equipment (if you will tune), and/or parts""",
        "keywords": ["dyno prep", "pre-dyno maintenance", "carbon removal", "fuel selection", "safety", "driveshaft", "tires"],
        "topic": "Dyno Testing - Preparation"
    },
    {
        "title": "At The Dyno Shop - Procedures",
        "content": """On your appointed dyno day, get to the shop at least one hour earlier than your appointment to allow the engine and transmission to cool down. Park in the shade facing the wind, and open the hood to speed the cool-down process.

**Planning:**
- Bring a list of what you want to get done during the session and go over it with the operator
- Items may include: eliminate detonation, find maximum power, improve light throttle tip-in, find optimal shift points
- If the dyno operator knows what you want, he can change the test procedure to accommodate you

**Driving Procedure:**
- If you're driving (some shops allow the owner to drive, but others don't), review the driving procedure with the dyno operator before making the first pull
- He can observe more than you do during a pull, and he may see or hear something that could potentially damage your engine or drivetrain
- Decide on a hand signal so that he can tell you to abort the run if necessary

**Cooling:**
- A properly sized fan should be available to cool the engine
- Open hood and fan in front of grille can significantly impact results (see observations from article)

**Gear Selection:**
- The gear for the most accurate results is a 1:1 ratio
- Depending on the dyno and its software, the most valid information is gleaned with a longer sample rate
- A test pull that lasts less than six or seven seconds usually provides false data
- Don't use overdrive on the dyno (can cause fluid overflow from transmission pressure relief valve)""",
        "keywords": ["dyno procedure", "cooling", "gear selection", "1:1 ratio", "dyno pull", "sample rate"],
        "topic": "Dyno Testing - Procedures"
    },
    {
        "title": "Tire Pressure and Dyno Results",
        "content": """Tire pressure significantly impacts dyno results:

- Low tire pressure increases rolling resistance, which in turn reduces the recorded power
- The tire pressure, even with slicks, should be high enough to support the car on the rollers without wanting to walk or move
- Drag slicks will require substantially more pressure on the dyno than on the track
- Example from article: Dropping tire pressure from 35 to 25 psi reduced power (compare run 3 to run 10)""",
        "keywords": ["tire pressure", "rolling resistance", "dyno results", "drag slicks"],
        "topic": "Dyno Testing - Tire Pressure"
    },
    {
        "title": "Engine Temperature and Dyno Results",
        "content": """Every engine is affected by heat - some more and others less.

**Optimal Temperature:**
- Most engines will produce the most power with the engine coolant around 170 to 180 degrees Fahrenheit
- As much cold-intake air as possible is beneficial (which is why Ram Air cars were so fast)

**Tuning Considerations:**
- If you are in a horsepower contest, then the temperature is very critical
- But if you are tuning, then you need to keep the engine and intake manifold at a thermal value that represents real-life driving
- Open hood and fan in front of grille can significantly improve results compared to closed hood (see article observations)""",
        "keywords": ["engine temperature", "coolant temperature", "intake air temperature", "thermal management", "dyno results"],
        "topic": "Dyno Testing - Temperature"
    },
    {
        "title": "Driving Style Impact on Dyno Numbers",
        "content": """Yes, especially on an inertia dyno. Power is measured by the rate of acceleration of the dyno drum, which is a fixed mass.

**How It Works:**
- The equation for horsepower is work/time
- The quicker the work is performed, the more power there is
- Think of the dyno as a stoplight drag race - the quicker you hit the throttle when the light turns green, the more power you are transferring to the ground

**Best Practice:**
- You need to be as aggressive as you can when the dyno operator signals to begin the run
- Consistent driving technique is important for repeatable results""",
        "keywords": ["driving style", "inertia dyno", "throttle application", "dyno technique", "repeatability"],
        "topic": "Dyno Testing - Driving Technique"
    },
    {
        "title": "Tire and Flywheel Horsepower Correlation",
        "content": """When using a chassis dyno, the general consensus among most manufacturers and operators is there is no definitive answer, though many say that a 15- to 20-percent loss is a good number if you need one.

**Example:**
- A vehicle producing 400 hp at the flywheel will see around 320-340 hp at the tire

**Important Notes:**
- To accurately determine drivetrain loss, first engine-dyno the powerplant, and then test again in the chassis
- The percentage of loss is only valid for your particular car and combination
- Don't get mired in power numbers when chassis dyno tuning - instead, call it bananas if you like
- If at first the engine has 320 bananas and you recurve the distributor and now it has 340 bananas at the tire, that's all that counts
- As long as every change makes the number go up, the car will go faster down the track""",
        "keywords": ["flywheel horsepower", "tire horsepower", "drivetrain loss", "chassis dyno", "power numbers"],
        "topic": "Dyno Testing - Power Correlation"
    },
    {
        "title": "Comparing Results from Different Dynos",
        "content": """The biggest mistake is to compare to a finite level the results from two different dyno shops, let alone equipment brands.

**Key Points:**
- If your vehicle makes 400 hp on a Super Flow chassis dyno, don't look for that exact same number on a Dyno-Jet
- One may be higher than the other, or the same
- A dyno session is meant to look for quantitative changes - it's not a contest from shop to shop
- If you change dyno shops, then simply establish a new baseline for that day and do not be concerned with the number you had from the other facility""",
        "keywords": ["dyno comparison", "different dynos", "Super Flow", "Dyno-Jet", "baseline", "quantitative changes"],
        "topic": "Dyno Testing - Comparison"
    },
    {
        "title": "Correction Factors",
        "content": """This is where a dyno shop can lead you astray. There are many different correction factors that can be applied to the results.

**Raw Numbers:**
- The uncorrected power readings are usually called raw numbers
- This is what the engine produced at that moment given the weather and atmospheric conditions

**SAE Correction:**
- SAE is the traditional test authority and has different standards based upon the ambient air temperature, humidity, and barometric pressure
- It would be listed as SAE with a number and letter code
- If the test day has worse weather conditions than the SAE standard, the corrected values will be higher
- If the day is better than the SAE protocol, the raw data will be higher

**Best Practice:**
- When tuning, it is best to limit the variables and use the SAE correction factor
- The atmospheric conditions will usually change during the course of your time on the dyno rollers""",
        "keywords": ["correction factors", "SAE correction", "raw numbers", "atmospheric conditions", "barometric pressure", "humidity"],
        "topic": "Dyno Testing - Correction Factors"
    },
    {
        "title": "Advanced Dyno Testing Techniques",
        "content": """To get data on what the engine is doing in each gear and rpm range after tuning is done, make a full pass on the dyno as you would at the strip.

**Full Pass Analysis:**
- Discount the horsepower and torque numbers as they will be skewed by the gear ratio and the different steps in engine speed
- The rest of the data will show you what the engine is doing under full load as the rpm changes
- This can be helpful in determining a few things

**Diagnostics:**
- Though many think a dyno's sole purpose is to measure power output, you can also use it for diagnostics
- Since the vehicle can be instrumented while under load and remaining stationary, you can correct a variety of driveability and/or driveline issues
- Examples: part-throttle surge, ignition miss in a certain rpm range

**Shift Point Optimization:**
- To determine the best shift points, check out the dyno graph
- Generally, you want to shift at peak horsepower and the rpm should drop to near peak torque

**Gear Ratio Testing:**
- To simulate the effects of a rear gear change, you can test different sets of wheels and tires
- Use very similar weight and compound but taller or shorter than your current combo
- This will show if more or less gear will unleash power""",
        "keywords": ["advanced dyno", "diagnostics", "shift points", "gear ratio", "full pass", "driveability"],
        "topic": "Dyno Testing - Advanced Techniques"
    },
    {
        "title": "Detonation and Dyno Testing",
        "content": """Once knock is evoked, a rest period is required to allow the piston crown and combustion chamber to reject the additional heat.

**Important:**
- If back-to-back runs after detonation are made, the engine power will drop substantially
- Always allow proper cool-down after detonation before making another pull
- Monitor for detonation carefully during dyno pulls to prevent engine damage""",
        "keywords": ["detonation", "knock", "cool-down", "engine damage", "dyno safety"],
        "topic": "Dyno Testing - Detonation"
    },
    {
        "title": "Tying Down the Vehicle",
        "content": """The method or tightness of the car to the dyno rollers for all practical purposes will not impact the data enough to worry about it.

**Safety is Key:**
- Don't allow the car to walk off the rollers at 100 mph
- The straps should be attached to a safe and strong mooring on the car
- Have little to no freeplay when secured properly
- Safety should be the primary concern, not data accuracy""",
        "keywords": ["tying down", "straps", "safety", "dyno rollers", "mooring"],
        "topic": "Dyno Testing - Safety"
    },
    {
        "title": "Dyno Testing Best Practices Summary",
        "content": """Purchasing chassis dyno time can be one of the best decisions you make, as 98 percent or more of your vehicle's power potential can be realized on the rollers.

**Key Takeaways:**
- Further minor tuning at the strip may be required to take into account wind resistance and the increased airflow (both through the radiator and at the carb at high speed)
- If your vehicle is ready to hit the streets or the strip and you have yet to take advantage of this technology, now is the time to consider it
- Use 1:1 gear ratio for most accurate results
- Keep pulls to 6-7 seconds minimum for valid data
- Maintain consistent driving technique
- Use proper cooling (open hood, fan in front)
- Monitor engine temperature (170-180°F optimal)
- Use appropriate tire pressure
- Allow proper cool-down after detonation
- Focus on quantitative changes, not absolute numbers""",
        "keywords": ["best practices", "dyno testing", "power potential", "tuning", "summary"],
        "topic": "Dyno Testing - Best Practices"
    }
]


def main():
    """Add dyno testing guide to knowledge base."""
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_manager = KnowledgeBaseManager(vector_store)
    kb_file_manager = KnowledgeBaseFileManager()

    added_count = 0
    for entry_data in DYNO_GUIDE_CONTENT:
        title = entry_data["title"]
        content = entry_data["content"]
        keywords = entry_data["keywords"]
        topic = entry_data["topic"]
        
        # Create question from title
        question = f"What is {title.lower()} in dyno testing?" if not title.lower().startswith("what") else title
        
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
    LOGGER.info(f"Total entries: {len(DYNO_GUIDE_CONTENT)}")
    LOGGER.info(f"Successfully added: {added_count}")
    if added_count == len(DYNO_GUIDE_CONTENT):
        LOGGER.info(f"\n[SUCCESS] Hot Rod Dyno Testing Guide has been added to the AI Chat Advisor!")
        LOGGER.info(f"Source: {ARTICLE_URL}")
    else:
        LOGGER.warning(f"\n[WARNING] Some entries failed to add.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

