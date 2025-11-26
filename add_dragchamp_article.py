#!/usr/bin/env python3
"""
Add DragChamp article about drag racing data analysis to the knowledge base.
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
    from services.knowledge_base_manager import KnowledgeBaseManager
    KB_AVAILABLE = True
except ImportError as e:
    KB_AVAILABLE = False
    LOGGER.error(f"Knowledge base modules not available: {e}")

# Article content (from web scraping)
ARTICLE_CONTENT = """Drag Racing Data Analysis and Acquisition: Logging Concepts and Techniques

Written by Ainsley Jacobs, courtesy of AEM Performance Electronics.

Only a few short years ago, drag racing seemed significantly simpler. Weather stations and chassis specialists could get you going in the right direction rather quickly based on only a few inputs, and decisions about how much power to add (or pull) were made through visceral tools like touch and feel – bare hands on tires or shoes on the track.

Although there are still seasoned bracket racers who rely heavily on the old school tricks of the trade, more racers are embracing electronic innovation and reaping the rewards for doing so. Logbooks are being supplemented by detailed data logs to gain a competitive advantage, go rounds and land a coveted spot in the winner's circle.

Learning to use a data logger, though, is only a part of the overarching challenge. It means nothing if you don't know what to do with the data once you've got it. For aspiring data analysts and even experienced acquisitionists, the sheer amount of data that can be collected can overwhelming. What exactly should be collected at the basic level? What are more advanced methods of data acquisition and analysis that professionals use, and how can you apply those to your own program to run quicker and prevent problems along the way?

THE BASICS

To start, it's recommended to set up standard channels such as air/fuel ratio and boost or vacuum along with other necessities such as fuel pressure, engine oil pressure, engine oil temperature, water/coolant temperature, timing, and more. These channels give good insights into the engine's overall health and operating state. By themselves, they can warn you of an issue, but with some experience when you see two or more of these that are simultaneously not where they should be during a pass, they can lead you to the likely culprit much more quickly.

Eric Holliday, the talented tuner at JPC Racing who is responsible for many of the quickest and fastest NMRA Street Outlaw, Renegade, and Coyote Modified cars, has extensive experience working with smaller-displacement turbocharged combinations – be it Modular motors, Coyote engines, or pushrod powerplants – but knows the basics apply to all engine types regardless of size or origin.

"Get situated, and when you've got a car that will start and run, the next step is to move into specific sensors to give you the data you need about whatever you're trying to control, be it shock sensors or transmission things," added Holliday, "If you're new to a logging system or aftermarket ECU, you'll want to record things like the throttle position and MAP sensor."

Once you've got a couple laps under your belt and have a solid A-to-B tune up in the engine computer, it's fairly straightforward to overlay data from runs on top of one another and see what areas can be improved upon. If the car is down on boost because of weather conditions, or making too much because of good air, you'll have your files to compare and can get an "off the trailer" type tune up ready to get down the track in almost any situation.

"Temperatures and pressures are absolutely key," reiterated Justin Jordan, proprietor of late model domestic drag racing-specialty shop Jordan Performance and Racing. "If you know your engine is staying cool and healthy, that's half the battle. If you measure air coming in, its temperature, and fuel going in, you've got most of what the engine needs to run already covered."

Monitoring coolant pressure allows you to see when the pressures begin to creep up, and make an educated decision on how much longer you can safely push it – or if an engine refresh is needed. Basically, if the coolant pressure logs look like your boost pressure logs, that's not a good sign!

Craig Watson, owner of a notorious 8-second '73 Chevy Nova and nitrous oxide guru, has an expert handle on what to log and how to interpret the acquired data as well.

"After a typical run, the first thing we look at when we pull up the data is the crankcase vacuum to make sure the tune-up was happy and we don't possibly have any hurt cylinders," explained Watson, who also checks the oil pressure during the run to make sure it was normal and needs to know if anything went awry to maximize his chances of making a repair before the next round. He documents the nitrous pressure, fuel pressure, shift RPM, and RPM at the finish line in his log book, along with the timeslip information and any additional relevant notes. "I've already, of course, documented the weather and the setup of the car before the run in the log book."

Fuel pressure feedback is incredibly useful, regardless of power adder. In Watson's world, nitrous is the name of the game and the data he receives from his fuel pressure sensors for both the carburetor and nitrous systems keep him informed if the fuel pump is getting worn and losing flow during a run while the AEM X-series wideband oxygen sensors give him important tune-up data early- and mid-run that he can't always see on the plugs themselves.

Former AEM Electronics Tech Specialist Henry Schelley (now with Honda Racing) has a few helpful tips for aspiring data acquisition and analysis experts and suggests:

1. Once you have your baseline tune and data logging on channels such as fuel pressure, oil pressure, engine launch RPM, throttle position, air/fuel ratio going down the track, and EGTs on all cylinders, you can start making changes for your next run(s).
2. Then, download that data and confirm the changes you made are showing up in the data before comparing your time slip to see where you did better or worse.
3. As some point, you can only get the engine running safely and reliably enough and you'll need to focus on chassis setup to improve your time. If improving your time is the goal, breaking up the track into small sections and focusing on each would be the simple approach. Trying to do everything at once could send you chasing your tail and result in inconsistent runs.
4. If you made a change to your tune up or to your car's setup and it didn't do what you wanted (or thought it should) – always ask why!

INDIVIDUAL CYLINDER MONITORING AND BOOST CHANNELS

Most moderate or serious drag cars also have exhaust gas temperature (EGT) sensors dedicated to each cylinder, often paired with their own wideband oxygen sensors as well. After each run, plugs are pulled and compared to what the data is reporting. "The more information you have, the better the decisions you can make," asserted Holliday, who built a successful career on making winning decisions. Once you collect the data, you can start putting two and two together to figure out what changes effect what.

Wes Choate, owner of the Missouri-based tuning and EFI conversion specialist shop Sho-Me Speed, regularly manages some of the baddest LS-powered no prep cars in the Southeast and is no stranger to the power of power management and how to use certain sensors to his advantage. He also does a lot of tuning for the off-road industry, including Ultra4s for King of the Hammers.

Choate often utilizes the AEM AQ-1 data logger along with eight wideband O2 sensors and the AEM Infinity ECU to help get cars in his care up to speed. "The 8-channel wideband is priceless to see cylinder-to-cylinder distribution and see what one is doing versus another," he outlined of how he helps identify issues.

ADVANCED TECHNIQUES AND SAFETY FEATURES

Data acquisition and analysis is also incredibly useful in developing products for racing. When JC Beattie of ATI Performance Products is working on a new item, he uses data to refine and perfect it.

Manufacturing in-house using as many American-made materials as possible, ATI Performance is equipped with a hub dyno, engine dyno, torque converter dyno, two transmission dynos, and more. Three racecars that run anywhere from 6.70- to 9.70-second elapsed times are also considered "real world dynos," and Beattie has everything wired with AEM equipment. "I rely on the AEM's feedback for every transmission we build when we're dyno testing, and we watch the data through the dash as well while also recording it. Collecting and analyzing the data significantly helps us optimize our products."

Beattie is also a racer himself, and – of course – his cars are all sporting AEM sensors, dashes, and engine management systems. "With blower cars, having a plethora of wideband sensors really makes a big difference since air distribution is a mess and the widebands make cleaning it up a piece of cake after viewing the data logs or looking at the incoming data stream in real time," he continued.

VISUALIZING THE DATA

In addition to having a configurable engine management system/computer, it's also extremely helpful to have a way to quickly and easily access the data that's being collected because all the data acquisition in the world means nothing if you don't have the proper tools to help analyze it effectively.

AEM's CD-7 digital logging dash, for example, accepts channels from CAN bus connections and is also compatible with third-party componentry. "For people who are new and still learning their routine, AEM's dash is key because it's configurable to prevent problems and set reminders, so you know where your numbers need to be and can easily see where the car is at," noted Holliday.

Watson uses his CD-7 digital logging dash to show custom layouts on each screen. For him, screen one shows driver Jeremy Lyons only the facts and figures he needs to see when he's strapped in and making a run. Screen two, however, is for warm-ups and has additional information on temperatures, O2 sensor read outs, and driveshaft RPM data. Screen three is smartly set to display sponsor logos and draws attention while the car is in the pits and the staging lanes, while screen four has as many channels as he could fit and is used primarily for diagnostics.

The CD-7 dash makes the post-race data analysis process a convenient and easily repeatable task for Watson, who relies heavily on his dash to display pertinent details and appreciates the device's digital prowess and flexibility. "Another great feature of the CD-series dashes is the ability to import data from the MSD Power Grid ignition controller," Watson continued. "We no longer have to look at two separate data logs to see all the data – it's all right there in AEMdata [data analysis software] where we can easily see the big picture."

If you aren't comfortable with tuning or doing data analysis yourself, or are worried about not always having your tuner with them at the track, AEM's Infinity is also able to be tuned remotely. "We just log in and tune someone's software with TeamViewer software or something," said Choate, who can quickly see what's going on in real-time and help his customers anywhere in the world all from the convenience of his shop.

In AEM's Infinity engine management system, too, you have the ability to look at your tune file and your data log all in the same screen instead of having to switch back and forth. This significantly reduces wasted time, which can make or break a race when there are only moments to spare between rounds.

"With InfinityTuner I can upload everything into one screen and it's a huge time saver at the track," shared Holliday. "Whatever you want to do, if you can think of it, you can do it with the Infinity."

THE TAKEAWAY

Taking the time to sort through a set up and implement thoughtful data acquisition channels can yield big dividends later on down the road. By being consistent in your data endeavors, maintaining a repository that's organized intelligently by track, date, time, pass, etc., and keeping a physical log book can save time, save parts, save money, and translate to success.

Organization and interpretation are equally important, and it can be easy to get wrapped up in too much data, but starting slow and taking the time to fully analyze, interpret, and understand the acquired information will ultimately help you make momentous moves in the long run.

Continuous learning is the name of the game in data analysis, and always seeking to understand the what, why and how will help improve performance of the car and the skill of its tuner alike.

And, when in doubt, always consult an expert, work with your tuner, or contact your data acquisition manufacturer for assistance."""

ARTICLE_URL = "https://dragchamp.com/2022/marketing-partners/drag-racing-data-analysis-and-acquisition-logging-concepts-and-techniques/"


def main():
    """Add DragChamp article to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_manager = KnowledgeBaseManager(vector_store=vector_store)
    kb_file_manager = KnowledgeBaseFileManager()
    
    # Split article into logical sections for better searchability
    sections = [
        {
            "title": "Drag Racing Data Analysis Basics",
            "content": """Standard data logging channels for drag racing include:
- Air/fuel ratio
- Boost or vacuum
- Fuel pressure
- Engine oil pressure
- Engine oil temperature
- Water/coolant temperature
- Ignition timing
- Throttle position
- MAP sensor

These channels provide insights into engine health and operating state. When multiple channels show anomalies simultaneously, they can quickly lead you to identify the problem.

Key advice from professional tuners:
- Start with basic channels, then add specific sensors for what you're trying to control
- Overlay data from multiple runs to see areas for improvement
- Compare data when weather conditions change to adjust tune-up
- Temperatures and pressures are absolutely key for engine health
- Monitor coolant pressure - if it looks like boost pressure logs, that's a bad sign"""
        },
        {
            "title": "Nitrous Oxide Data Logging",
            "content": """For nitrous oxide systems, key data points to log include:
- Crankcase vacuum (first check after a run to ensure tune-up was happy)
- Oil pressure during the run
- Nitrous pressure
- Fuel pressure (both carburetor and nitrous systems)
- Shift RPM
- RPM at finish line
- Wideband oxygen sensor data (early and mid-run)
- Weather conditions and car setup (documented before run)

Fuel pressure feedback is incredibly useful for nitrous systems. Data from fuel pressure sensors can indicate if the fuel pump is getting worn and losing flow during a run. Wideband oxygen sensors provide important tune-up data that may not be visible on spark plugs."""
        },
        {
            "title": "Individual Cylinder Monitoring",
            "content": """Most serious drag cars have:
- Exhaust gas temperature (EGT) sensors for each cylinder
- Individual wideband oxygen sensors per cylinder
- After each run, compare spark plugs to what the data reports

The more information you have, the better decisions you can make. With 8-channel wideband systems, you can see cylinder-to-cylinder distribution and identify which cylinders are behaving differently.

For blower cars, multiple wideband sensors are especially valuable since air distribution can be uneven. The widebands make it easy to clean up the tune after viewing data logs or real-time data streams."""
        },
        {
            "title": "Data Analysis Workflow",
            "content": """Professional workflow for data analysis:

1. Establish baseline tune with data logging on key channels:
   - Fuel pressure
   - Oil pressure
   - Engine launch RPM
   - Throttle position
   - Air/fuel ratio going down the track
   - EGTs on all cylinders

2. Make changes for next run(s)

3. Download data and confirm changes are showing in the data

4. Compare time slip to see where you did better or worse

5. Break track into small sections and focus on each section individually
   - Trying to do everything at once can lead to chasing your tail
   - Results in inconsistent runs

6. Always ask "why" if a change didn't do what you expected

Key principle: At some point, you can only get the engine running safely and reliably enough, then you need to focus on chassis setup to improve times."""
        },
        {
            "title": "Data Visualization and Dash Systems",
            "content": """Modern data logging dashes provide:
- Configurable displays for different scenarios
- Custom layouts for different screens (race, warm-up, diagnostics, sponsor display)
- CAN bus connectivity
- Third-party component compatibility
- Ability to import data from other controllers (e.g., MSD Power Grid)
- All data in one place for easy analysis

Screen organization example:
- Screen 1: Driver view - only essential facts and figures during run
- Screen 2: Warm-up view - temperatures, O2 sensors, driveshaft RPM
- Screen 3: Sponsor logos for pits and staging lanes
- Screen 4: Diagnostics - as many channels as possible

Remote tuning capability allows tuners to log in and tune software remotely using tools like TeamViewer, enabling real-time assistance from anywhere in the world."""
        },
        {
            "title": "Safety Features and Engine Protection",
            "content": """Data acquisition systems can provide critical safety features:

- Safety features in engine management systems can automatically pull timing or kill the motor if oil pressure is lost
- Wideband O2 sensors with built-in warnings can protect the engine if it goes too lean
- These features act like insurance policies - might cost you a race but can save thousands of dollars in engine damage
- For learning tuners, safety settings provide protection in case of mistakes

Real-world example: A racer lost oil pressure at a race, but the AEM Infinity computer's safety feature ripped out all timing and killed the motor before it could hurt itself. It was a false alarm from a faulty sensor, but the computer acted correctly in the unexpected situation."""
        },
        {
            "title": "Data Organization and Best Practices",
            "content": """Best practices for data management:

- Be consistent in data collection
- Maintain organized repository by:
  * Track
  * Date
  * Time
  * Pass number
- Keep physical log book alongside digital data
- Start slow and fully analyze, interpret, and understand information
- Don't get wrapped up in too much data at once
- Organization and interpretation are equally important

Benefits:
- Save time
- Save parts
- Save money
- Translate to success

Continuous learning is key - always seek to understand the what, why, and how. This improves both car performance and tuner skill."""
        }
    ]
    
    added_count = 0
    
    # Add each section to knowledge base
    for i, section in enumerate(sections, 1):
        try:
            LOGGER.info(f"Adding section {i}/{len(sections)}: {section['title']}")
            
            # Combine title and content
            full_text = f"{section['title']}\n\n{section['content']}"
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=full_text,
                metadata={
                    "title": section["title"],
                    "source": "DragChamp Article",
                    "url": ARTICLE_URL,
                    "topic": "Drag Racing Data Analysis",
                    "category": "Data Logging",
                    "keywords": "data logging, drag racing, telemetry, data acquisition, tuning, sensors"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=f"What is {section['title'].lower()}?",
                answer=section["content"],
                source="DragChamp Article",
                url=ARTICLE_URL,
                keywords=["drag racing", "data logging", "telemetry", section["title"].lower()],
                topic="Drag Racing Data Analysis",
                confidence=0.9,
                verified=True
            )
            
            added_count += 1
            LOGGER.info(f"  Successfully added section")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add section: {e}")
    
    # Also add the full article as a single entry
    try:
        LOGGER.info("Adding full article as complete reference...")
        vector_store.add_knowledge(
            text=ARTICLE_CONTENT,
            metadata={
                "title": "Drag Racing Data Analysis and Acquisition: Logging Concepts and Techniques",
                "source": "DragChamp Article",
                "url": ARTICLE_URL,
                "topic": "Drag Racing Data Analysis",
                "category": "Complete Article",
                "author": "Ainsley Jacobs",
                "keywords": "drag racing, data logging, telemetry, data acquisition, tuning, sensors, AEM, nitrous, EGT, wideband"
            }
        )
        added_count += 1
        LOGGER.info("  Full article added")
    except Exception as e:
        LOGGER.error(f"  Failed to add full article: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total sections: {len(sections)}")
    LOGGER.info(f"Successfully added: {added_count} entries")
    LOGGER.info(f"\nDrag racing data analysis article has been added to the AI Chat Advisor!")
    LOGGER.info(f"Source: {ARTICLE_URL}")


if __name__ == "__main__":
    main()

