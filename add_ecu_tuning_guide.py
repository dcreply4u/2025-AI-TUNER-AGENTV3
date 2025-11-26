#!/usr/bin/env python3
"""
Add comprehensive ECU tuning guide to the AI Chat Advisor knowledge base.
Extracted from fullpdfword.org ECU tuning guide.
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

# ECU Tuning Guide Knowledge
ECU_TUNING_KNOWLEDGE = [
    {
        "question": "What is an ECU and how does it work?",
        "answer": """The Engine Control Unit (ECU), sometimes referred to as the Engine Control Module (ECM), is a critical electronic component in modern vehicles. It acts as the vehicle's brain, managing various engine functions such as:

**Core Functions:**
- Air intake management
- Fuel injection timing and quantity
- Ignition timing
- Emissions control
- Boost pressure control (for turbocharged engines)
- Idle speed adjustment
- Throttle response

**How It Works:**
- Gathers data from various sensors throughout the vehicle (oxygen sensors, mass airflow sensors, throttle position sensors, etc.)
- Processes this sensor data in real-time
- Adjusts engine parameters to ensure optimal performance, fuel efficiency, and emissions compliance
- Contains pre-programmed maps and algorithms tuned by manufacturers during production

**Manufacturer Settings:**
- Factory settings are tuned to meet regulatory standards
- Designed to ensure broad compatibility and reliability
- Often leave performance potential untapped for safety and emissions compliance

**Tuning Potential:**
- ECU tuning involves modifying the firmware or calibration maps
- Changes how the ECU controls engine functions
- Allows unlocking hidden performance potential
- Can be customized for specific modifications or preferences""",
        "keywords": ["ECU", "engine control unit", "ECM", "engine control module", "how ECU works", "vehicle brain"],
        "topic": "ECU Tuning - Basics"
    },
    {
        "question": "Why should I tune my ECU?",
        "answer": """ECU tuning allows you to unlock performance potential that factory settings leave untapped. Common reasons for tuning include:

**Performance Benefits:**
- Increase horsepower and torque
- Improve throttle response
- Enhance acceleration and top speed
- Better drivability and responsiveness

**Efficiency Benefits:**
- Optimize fuel economy
- Improve fuel efficiency under specific driving conditions
- Better combustion efficiency

**Customization:**
- Adjust for aftermarket modifications (exhaust systems, intakes, turbo upgrades)
- Remove speed limiters or other restrictions
- Optimize for specific use cases (towing, racing, off-road)
- Tailor vehicle behavior to your preferences

**Adaptation:**
- Compensate for modifications like forced induction
- Adjust for different fuel types
- Optimize for specific driving conditions
- Create custom maps for different scenarios

**Important Considerations:**
- Benefits come with inherent risks (increased wear, decreased reliability, voided warranties)
- Must be done carefully and responsibly
- Requires understanding of vehicle systems and tuning principles
- Should consider legal and emissions compliance""",
        "keywords": ["why tune ECU", "ECU tuning benefits", "performance gains", "fuel economy", "customization"],
        "topic": "ECU Tuning - Benefits"
    },
    {
        "question": "What are the different types of ECU tuning methods?",
        "answer": """ECU tuning can be achieved through several methods, each with distinct advantages and considerations:

**1. Remapping (Software Tuning)**
- Most common and accessible method
- Involves directly editing the ECU's firmware or software map
- **Flash Tuning:** Using specialized hardware and software to reprogram ECU's memory directly, allows for detailed customization
- **Chiptuning:** Involves replacing or modifying the ECU's original chip or firmware
- **Advantages:** Precise control, customizable for specific modifications, usually reversible
- **Disadvantages:** Requires technical knowledge, risk of damaging ECU if done improperly

**2. Plug-and-Play Tuning Devices**
- Handheld devices or modules that plug into OBD-II port
- Modify engine parameters on the fly
- **Advantages:** Easy to install and operate, can be removed easily, suitable for DIY enthusiasts
- **Disadvantages:** Less customizable, may offer limited tuning options, potentially less safe if not designed properly

**3. ECU Swap**
- Replacing entire ECU with pre-tuned or aftermarket unit
- **Advantages:** Plug-and-play with optimized firmware, often compatible with other modifications
- **Disadvantages:** Can be costly, compatibility issues if not properly matched

**4. Chip Tuning and Hardware Modification**
- Physically replacing or reprogramming ECU's microchip or memory modules
- **Process:** Remove ECU/chip, use hardware programmer to read/modify firmware, reinstall
- **Advantages:** Encapsulates entire program, potentially more stable for certain ECUs
- **Disadvantages:** More invasive, time-consuming, requires specialized equipment, less flexible

**5. Piggyback Systems**
- Aftermarket devices that intercept or modify sensor signals
- Examples: Performance chips, piggyback ECU modules, boost controllers
- **Advantages:** Easy to install and remove, generally reversible
- **Disadvantages:** Less precise than software remapping, may not unlock full potential""",
        "keywords": ["ECU tuning methods", "remapping", "flash tuning", "chiptuning", "plug and play", "ECU swap"],
        "topic": "ECU Tuning - Methods"
    },
    {
        "question": "How do I prepare for ECU tuning?",
        "answer": """Proper preparation is crucial before ECU tuning to ensure safety, compliance, and desired outcomes:

**1. Understand Your Vehicle**
- Gather detailed information:
  * Make, model, year
  * Engine specifications
  * Existing modifications
  * ECU type and firmware version

**2. Define Your Goals**
- Identify what you want to achieve:
  * Increased power
  * Better fuel economy
  * Improved throttle response
  * Custom driving characteristics
  * Adaptation for modifications

**3. Backup Original ECU Data**
- **CRITICAL:** Always create a backup of your original ECU map before making any changes
- This allows you to revert to stock settings if needed
- Store backup in safe location
- Never proceed without a backup

**4. Use Quality Tools and Software**
- Invest in reputable tuning software and hardware suited for your vehicle
- Popular tools include:
  * EcuTek
  * HP Tuner
  * Cobb Tuning
  * Alientech Kess
- Avoid cheap or untested tools

**5. Consider Professional Assistance**
- While DIY tuning is possible, consulting with experienced tuners can prevent costly mistakes
- Professional tuners have proper tools and expertise
- Can optimize results and ensure safety
- Especially important for complex modifications

**6. Vehicle Condition**
- Ensure vehicle is in good mechanical condition
- Check cooling and fueling systems are adequate
- Verify all sensors are functioning properly
- Address any existing issues before tuning""",
        "keywords": ["ECU tuning preparation", "backup ECU", "tuning tools", "professional tuner", "vehicle preparation"],
        "topic": "ECU Tuning - Preparation"
    },
    {
        "question": "What is the step-by-step process for ECU tuning?",
        "answer": """Step-by-step guide to ECU tuning:

**Step 1: Connect to Your Vehicle**
- Use OBD-II interface or specialized hardware
- Connect tuning device or laptop to vehicle's diagnostic port
- Ensure stable connection before proceeding

**Step 2: Read and Save the Stock Map**
- Extract current ECU data to safe location
- This is your fallback and ensures you can restore original settings
- Verify backup was created successfully
- Store backup in multiple locations if possible

**Step 3: Analyze and Modify the Map**
- Using tuning software:
  * Identify key parameters (fuel maps, ignition timing, boost levels, throttle response)
  * Make incremental adjustments based on your goals
  * Use predefined profiles or custom maps designed for your modifications
  * Start with conservative changes

**Step 4: Write the Modified Map to the ECU**
- Upload the new tuning file to the ECU
- Ensure process completes successfully without interruption
- Do not disconnect or power off during write process
- Verify write was successful

**Step 5: Test and Monitor**
- Start the vehicle and perform test drives:
  * Observe how vehicle responds
  * Use diagnostic tools to monitor sensor data
  * Check for warning lights or errors
  * Monitor engine parameters (AFR, timing, boost, temperatures)

**Step 6: Fine-Tune as Needed**
- Based on real-world testing, adjust tune for optimal performance and safety
- Make small incremental changes
- Test after each adjustment
- Document changes for reference

**Important:** Always make small changes and test thoroughly before making additional modifications.""",
        "keywords": ["ECU tuning steps", "how to tune ECU", "tuning process", "ECU remapping steps", "tuning procedure"],
        "topic": "ECU Tuning - Process"
    },
    {
        "question": "What are the safety tips and best practices for ECU tuning?",
        "answer": """Critical safety tips and best practices for ECU tuning:

**Essential Safety Practices:**
- **Always back up original ECU data** before making any changes
- Make small incremental adjustments rather than drastic changes
- Use reputable tuning software and hardware
- Consider impact on emissions and legality in your region
- Ensure vehicle's cooling and fueling systems are up to the task
- Regularly monitor engine parameters during and after tuning
- Avoid tuning for maximum power at expense of reliability

**Calibration Best Practices:**
- Consider vehicle's stock configuration
- Account for upgrades or modifications
- Align tuning with intended use (daily driving, racing, off-road)
- Perform iterative testing and data logging to refine calibration
- Maintain safety margins to prevent engine damage

**Fuel and Monitoring:**
- Align tuning with fuel quality and octane ratings
- Higher octane fuels allow more aggressive ignition timing
- Using lower-octane fuel than tune requires can cause knocking and engine damage
- Continuously monitor parameters (AFR, ignition advance, exhaust gases)
- Use data logging to identify issues (detonation, fuel mixture imbalances, overheating)

**Safety Margins:**
- Avoid excessively aggressive ignition timing
- Don't exceed safe boost levels
- Ensure adequate fueling to prevent lean conditions
- Maintain margin of safety to prevent engine damage

**Professional Consultation:**
- Consult professional tuners if unsure about specific modifications
- Use reputable tuning shops or software
- Start with mild maps and progressively tune as needed
- Maintain documentation of original maps and modifications""",
        "keywords": ["ECU tuning safety", "tuning best practices", "safety tips", "tuning guidelines", "safe tuning"],
        "topic": "ECU Tuning - Safety"
    },
    {
        "question": "What are the legal and ethical considerations for ECU tuning?",
        "answer": """Important legal and ethical considerations for ECU tuning:

**Emissions Compliance:**
- ECU tuning can affect vehicle emissions and compliance with local laws
- Check local regulations regarding emissions testing and modifications
- Some tunes may render vehicles non-compliant with emissions standards
- May lead to legal issues or failed inspections
- Consider environmental impact and strive for responsible tuning

**Warranty Issues:**
- Many manufacturers consider ECU remapping a violation of warranty agreements
- ECU tuning can void your vehicle's warranty if detected during diagnostics or service
- Some manufacturers may offer warranty-friendly tuning options
- Check with your dealer before tuning
- Be aware that modifications may void warranties

**Legal Compliance:**
- Ensure tuning complies with local laws and regulations
- Some regions have restrictions on vehicle modifications
- Emissions testing may be required
- Street-legal requirements must be met
- Racing applications may have different regulations

**Responsible Tuning:**
- Consider environmental impact
- Strive for responsible tuning practices
- Balance performance with emissions compliance
- Use tuning to optimize efficiency when possible
- Avoid tuning that creates excessive pollution

**Documentation:**
- Keep records of original maps and modifications
- Document all tuning changes
- Maintain compliance documentation if required
- Be prepared to demonstrate compliance if needed""",
        "keywords": ["ECU tuning legal", "warranty void", "emissions compliance", "legal considerations", "tuning regulations"],
        "topic": "ECU Tuning - Legal"
    },
    {
        "question": "What are the risks and challenges of ECU tuning?",
        "answer": """ECU tuning carries inherent risks that require careful consideration:

**1. Engine Reliability and Longevity**
- Aggressive tuning can lead to increased stress on engine components
- Pistons, valves, and turbochargers may experience shortened lifespan
- Increased wear on engine parts
- Potential for premature component failure
- Must be properly managed to maintain reliability

**2. Warranty Voiding and Legal Compliance**
- Many manufacturers consider ECU remapping a violation of warranty agreements
- Modifications may render vehicles non-compliant with emissions standards
- May lead to legal issues or failed inspections
- Can void warranties if detected during service

**3. ECU Bricking and Software Failures**
- Incorrect tuning or interrupted flashing processes can render ECU inoperable
- ECU may become "bricked" and unusable
- Necessitates costly repairs or replacements
- Risk of permanent damage if process is interrupted

**4. Compatibility Issues**
- Not all ECUs are equally tunable
- Some are locked or protected by security features
- May complicate or prevent modification
- Compatibility issues if not properly matched
- Plug-and-play devices may not work with all vehicles

**5. Reliability of Tuning Services**
- Using unqualified or inexperienced tuners can result in poorly calibrated maps
- May lead to drivability issues
- Can cause engine damage
- Safety concerns from improper tuning
- Poor quality software can cause problems

**6. Fuel and Maintenance Requirements**
- Tuning may require higher octane fuel
- Increased maintenance needs
- More frequent monitoring required
- Potential for increased fuel consumption with aggressive tunes""",
        "keywords": ["ECU tuning risks", "tuning dangers", "engine damage", "ECU bricking", "tuning problems"],
        "topic": "ECU Tuning - Risks"
    },
    {
        "question": "What are common ECU tuning mistakes to avoid?",
        "answer": """Common ECU tuning mistakes that should be avoided:

**Critical Mistakes:**
- **Not backing up original data** - Always create backup before making changes
- **Making aggressive changes without testing** - Start with small incremental adjustments
- **Ignoring vehicle-specific requirements** - Each vehicle has unique characteristics
- **Overlooking cooling or fuel system capabilities** - Ensure systems can handle increased demands
- **Tuning without proper tools or expertise** - Use reputable software and hardware

**Process Mistakes:**
- Interrupting the flashing process
- Not verifying backup was created successfully
- Making multiple large changes at once
- Not testing after each modification
- Skipping monitoring and data logging

**Safety Mistakes:**
- Tuning for maximum power at expense of reliability
- Ignoring safety margins
- Using incorrect fuel octane rating
- Not monitoring engine parameters
- Ignoring warning signs or error codes

**Preparation Mistakes:**
- Not understanding vehicle's current state
- Not defining clear tuning goals
- Using cheap or untested tools
- Not consulting professionals when needed
- Rushing the tuning process

**Best Practices to Avoid Mistakes:**
- Research and education before tuning
- Use reputable tuning shops or software
- Start with mild maps and progress gradually
- Perform regular monitoring
- Maintain documentation
- Ensure proper fuel and maintenance
- Consult professionals when unsure""",
        "keywords": ["ECU tuning mistakes", "tuning errors", "common mistakes", "tuning pitfalls", "what to avoid"],
        "topic": "ECU Tuning - Mistakes"
    },
    {
        "question": "How much does ECU tuning cost?",
        "answer": """ECU tuning costs vary depending on several factors:

**Cost Range:**
- Typically ranges from $300 to $1500
- Custom tunes and high-performance modifications may cost more
- Professional tuning services generally cost more than DIY solutions

**Factors Affecting Cost:**
- Vehicle make and model
- Level of modification required
- Complexity of tuning needed
- Type of tuning method (remapping, plug-and-play, ECU swap)
- Reputation and experience of tuner
- Geographic location

**Cost Considerations:**
- Quality and reputation of tuner should be prioritized over price alone
- Cheap tuning may result in poor results or engine damage
- Professional tuning may cost more but provides better results and safety
- DIY solutions require investment in tools and software
- Ongoing tuning and adjustments may incur additional costs

**Value vs. Cost:**
- Consider value of professional expertise
- Factor in potential costs of mistakes (engine damage, ECU replacement)
- Quality tuning provides better long-term value
- Proper tuning can improve fuel economy and offset some costs
- Warranty considerations may affect long-term costs

**DIY vs. Professional:**
- DIY: Lower initial cost but requires tools, software, and expertise
- Professional: Higher cost but includes expertise, proper tools, and support
- Consider your experience level and risk tolerance
- Professional tuning recommended for complex modifications""",
        "keywords": ["ECU tuning cost", "tuning price", "how much does tuning cost", "tuning expenses", "tuning fees"],
        "topic": "ECU Tuning - Cost"
    },
    {
        "question": "Can ECU tuning improve fuel economy?",
        "answer": """ECU tuning can improve fuel economy when done correctly:

**How It Works:**
- Optimizes fuel delivery and combustion efficiency
- Adjusts parameters for better efficiency
- Can improve fuel economy especially in driving conditions where engine is underutilized
- Better combustion efficiency means less wasted fuel

**Performance vs. Economy:**
- Aggressive tuning aimed at maximum power may increase fuel consumption
- Economy-focused tuning prioritizes efficiency over power
- Proper tuning balances performance and efficiency
- Can create different maps for different scenarios (economy vs. performance)

**Optimization Strategies:**
- Lean out fuel mixture where safe
- Optimize ignition timing for efficiency
- Adjust throttle response for better efficiency
- Optimize for specific driving conditions
- Reduce unnecessary fuel consumption

**Real-World Results:**
- Results vary depending on vehicle, driving style, and tuning approach
- Economy-focused tunes can provide measurable improvements
- Performance-focused tunes may reduce economy
- Proper tuning can maintain or improve economy while gaining power

**Important Considerations:**
- Must be done carefully to avoid lean conditions
- Requires proper monitoring and testing
- Results depend on driving conditions and style
- Balance between economy and performance must be maintained
- Not all tunes will improve fuel economy""",
        "keywords": ["ECU tuning fuel economy", "fuel efficiency", "gas mileage", "economy tuning", "fuel savings"],
        "topic": "ECU Tuning - Fuel Economy"
    },
    {
        "question": "What are the key aspects of effective ECU tuning?",
        "answer": """Key aspects of effective ECU tuning:

**1. Calibration and Mapping**
- Specific adjustments made to engine maps (fuel, ignition timing, boost, etc.)
- Good calibration considers:
  * Vehicle's stock configuration
  * Upgrades or modifications
  * Intended use (daily driving, racing, off-road)
- Thorough tune involves iterative testing and data logging to refine calibration

**2. Fuel Quality and Octane Ratings**
- Tuning should be aligned with fuel quality
- Higher octane fuels resist knocking and allow more aggressive ignition timing
- Using lower-octane fuel than tune requires can cause knocking, engine damage, or reduced power
- Must match tune to available fuel

**3. Monitoring and Data Logging**
- Continuous monitoring of parameters is essential:
  * Air-fuel ratio (AFR)
  * Ignition advance
  * Exhaust gases
  * Temperatures
  * Boost pressure
- Data logging helps identify issues:
  * Detonation or knocking
  * Fuel mixture imbalances
  * Overheating
  * Abnormal sensor readings
- Advanced tuners utilize dynamometers and real-time diagnostics

**4. Safety Margins and Limits**
- Responsible tune maintains margin of safety to prevent engine damage
- Avoid excessively aggressive ignition timing
- Don't exceed safe boost levels
- Ensure adequate fueling to prevent lean conditions
- Balance performance with reliability

**5. Iterative Testing**
- Make small changes and test thoroughly
- Refine calibration based on real-world results
- Document all changes
- Monitor long-term effects
- Adjust as needed""",
        "keywords": ["effective ECU tuning", "calibration", "fuel quality", "data logging", "safety margins"],
        "topic": "ECU Tuning - Key Aspects"
    },
    {
        "question": "What are future trends in ECU tuning?",
        "answer": """Future trends in ECU tuning technology:

**1. Over-The-Air (OTA) Updates**
- Manufacturers increasingly offer OTA ECU updates
- Could be harnessed or modified for performance tuning
- Allows remote tuning and updates
- May change how tuning is performed

**2. Advanced Data Analytics**
- Machine learning and AI beginning to influence calibration techniques
- Automated tuning optimization
- Predictive tuning based on data analysis
- More sophisticated calibration algorithms

**3. Electric and Hybrid Vehicles**
- Tuning approaches shifting as traditional ICE engines are replaced
- Focus on software-based optimization
- Battery management system tuning
- Electric motor control optimization
- Different tuning paradigms for electric powertrains

**4. Integration with Vehicle Systems**
- More integrated tuning across vehicle systems
- Coordination between multiple control units
- Advanced sensor integration
- Real-time adaptive tuning

**5. Enhanced Diagnostics**
- More sophisticated diagnostic capabilities
- Predictive maintenance integration
- Real-time health monitoring
- Automated issue detection and correction

**6. User-Friendly Interfaces**
- More accessible tuning tools
- Simplified interfaces for DIY tuners
- Mobile app integration
- Cloud-based tuning services""",
        "keywords": ["ECU tuning trends", "future of tuning", "OTA updates", "AI tuning", "electric vehicle tuning"],
        "topic": "ECU Tuning - Future Trends"
    }
]

ARTICLE_URL = "https://fullpdfword.org/look-up/mL837B/604068/4965447-ecu-tuning-guide"
ARTICLE_SOURCE = "ECU Tuning Guide - Comprehensive Guide"


def main():
    """Add ECU tuning guide to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in ECU_TUNING_KNOWLEDGE:
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
                    "category": "ECU Tuning",
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
    LOGGER.info(f"Total entries: {len(ECU_TUNING_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nECU Tuning Guide has been added to the knowledge base!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - ECU basics and functionality")
    LOGGER.info(f"  - Tuning benefits and reasons")
    LOGGER.info(f"  - Different tuning methods")
    LOGGER.info(f"  - Preparation and process")
    LOGGER.info(f"  - Safety and best practices")
    LOGGER.info(f"  - Legal and ethical considerations")
    LOGGER.info(f"  - Risks and challenges")
    LOGGER.info(f"  - Common mistakes to avoid")
    LOGGER.info(f"  - Cost considerations")
    LOGGER.info(f"  - Fuel economy optimization")
    LOGGER.info(f"  - Key aspects of effective tuning")
    LOGGER.info(f"  - Future trends")


if __name__ == "__main__":
    main()

