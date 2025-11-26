#!/usr/bin/env python3
"""
Download and add water/methanol injection setup guide to the AI Chat Advisor knowledge base.
Source: Water/Methanol Injection Manual (generalized, vendor-agnostic)
"""

import logging
import sys
import requests
from pathlib import Path
import tempfile
import re

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

PAPER_URL = "https://documents.aemelectronics.com/2979cfadc3060bead75f0e6957d2f01c999b7f00.pdf"
PAPER_TITLE = "Water/Methanol Injection System Setup and Tuning Guide"
PAPER_TOPIC = "Water/Methanol Injection"


def download_pdf(url: str, output_path: Path) -> bool:
    """Download PDF from URL."""
    try:
        LOGGER.info(f"Downloading PDF from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        LOGGER.info(f"Downloaded PDF to: {output_path}")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to download PDF: {e}")
        return False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        LOGGER.info("Extracting text using PyPDF2...")
        text_content = []
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
                except Exception as e:
                    LOGGER.warning(f"Failed to extract text from page {page_num + 1}: {e}")
        return "\n\n".join(text_content)
    except ImportError:
        LOGGER.error("PyPDF2 not available. Install with: pip install PyPDF2")
        return ""


def create_knowledge_entries(text: str) -> list:
    """Create structured knowledge entries from extracted text."""
    entries = []
    
    # Remove vendor-specific references and make generic
    text = re.sub(r'\bAEM\b', 'water/methanol injection system', text, flags=re.IGNORECASE)
    text = re.sub(r'\bP/N\s+\d+-\d+\b', '', text)  # Remove part numbers
    text = re.sub(r'Part\s+#\s*\d+-\d+', '', text, flags=re.IGNORECASE)
    
    # Extract key sections and create entries
    
    # 1. Safety and Methanol Concentration
    safety_match = re.search(r'IMPORTANT SAFETY NOTICE.*?50\s*%.*?concentration.*?(?=\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
    if safety_match:
        safety_text = safety_match.group(0)
        entries.append({
            "question": "What is the recommended maximum methanol concentration for water/methanol injection systems?",
            "answer": f"""For safety reasons, it is strongly recommended to never exceed 50% methanol concentration when using water/methanol injection systems.

**Safety Considerations:**
- Methanol is toxic and highly flammable
- 100% methanol ignites easily and burns with an almost undetectable flame
- Methanol can be absorbed through the skin
- Even small amounts can cause blindness or death
- Using high concentrations at high pressures in under-hood environments with nylon lines and fittings is very unsafe

**Performance vs. Safety:**
- The performance advantages of using greater than 50% methanol concentrations are small, if they exist at all
- Safety issues far outweigh any perceived benefit of running high concentrations
- All system components (pump, lines, fittings, filter, flow sensor, tank, nozzles) are chemically compatible with methanol, but safety should be the priority

**Recommendation:**
Use a maximum of 50% methanol concentration for the best balance of performance and safety.""",
            "keywords": ["methanol concentration", "water methanol injection", "safety", "50% methanol", "methanol safety"],
            "topic": "Water/Methanol Injection - Safety"
        })
    
    # 2. System Components
    components_text = """
Water/methanol injection systems typically consist of:
- High-pressure injection pump (typically 200 PSI)
- Progressive pump controller with boost-safe feature
- High amperage pump driver with protection circuits
- System status LED indicators
- Test button for manual pump triggering
- Pump speed control dials
- High-pressure nylon hose (typically 1/4")
- Injection nozzles with check valves
- Wiring harness
- Optional: Solenoid valve, flow sensor, filter, tank level sensor
"""
    entries.append({
        "question": "What components are included in a water/methanol injection system?",
        "answer": components_text,
        "keywords": ["water methanol injection", "components", "system parts", "injection system"],
        "topic": "Water/Methanol Injection - Components"
    })
    
    # 3. Installation Process
    install_steps = """
**Installation Checklist:**

1. **Install Pump:**
   - Select suitable location near and below the lowest fluid level of tank
   - Fasten securely with appropriate hardware
   - Cut and install nylon hose from tank to pump

2. **Install Controller:**
   - Disconnect ground side of battery during electronic installation
   - Mount controller inside driver's compartment (NOT in engine bay - controller is NOT waterproof)
   - Find location in driver's field of view and install external LED
   - Follow wire diagram and connect wires from harness
   - Connect input signal wire

3. **Flush Tank:**
   - Connect hose to pump (DO NOT CONNECT NOZZLE)
   - Fill tank with water (distilled water recommended)
   - Turn on key power to power on controller
   - Use TEST button on controller to flush tank into separate container
   - Drain tank

4. **Connect Nozzle:**
   - Select appropriate nozzle and connect to nylon hose
   - Fill tank with water
   - Use TEST button to test complete system

5. **System Check:**
   - While pushing TEST button, ensure no errors are reported
   - System should produce gradually increasing flow out of nozzle
   - May require pressing TEST button multiple times to purge system
   - Drain tank and fill with desired water/methanol mixture
   - DO NOT use hydrocarbon fuel - only water and methanol are supported

6. **Install Nozzle:**
   - Nozzle must be mounted above the tank (prevents gravity/siphoning leaks)
   - Nozzle must be mounted before throttle plate
   - Nozzle should be mounted after MAF sensor if present
   - Nozzle must be mounted after intercooler if present
   - Failure to mount correctly may result in engine damage
"""
    entries.append({
        "question": "How do you install a water/methanol injection system?",
        "answer": install_steps,
        "keywords": ["water methanol injection", "installation", "setup", "install procedure"],
        "topic": "Water/Methanol Injection - Installation"
    })
    
    # 4. Nozzle Selection and Placement
    nozzle_text = """
**Nozzle Selection:**
- Nozzles are available in different flow rates (pintle sizes)
- Selection depends on engine size, boost level, and desired injection rate
- Multiple nozzles can be used for larger engines or higher flow requirements

**Nozzle Placement Requirements:**
- Must be mounted above the tank (prevents gravity/siphoning)
- Must be mounted before throttle plate
- Should be mounted after MAF sensor (if present)
- Must be mounted after intercooler (if present)
- Failure to mount correctly may result in fluid leaking into intake tract, causing engine damage

**Modern Nozzles:**
- New style nozzles have internal check valves
- External check valve is no longer needed
- Prevents backflow when system is not active
"""
    entries.append({
        "question": "How do you select and place water/methanol injection nozzles?",
        "answer": nozzle_text,
        "keywords": ["nozzle selection", "nozzle placement", "injection nozzle", "water methanol"],
        "topic": "Water/Methanol Injection - Nozzle Setup"
    })
    
    # 5. Engine Tuning with Water/Methanol
    tuning_match = re.search(r'ENGINE TUNING.*?(?=COLD WEATHER|MAINTENANCE|OPTIONAL|\Z)', text, re.DOTALL | re.IGNORECASE)
    if tuning_match:
        tuning_text = tuning_match.group(0)
        # Clean up and generalize
        tuning_text = re.sub(r'\bAEM\b', 'water/methanol injection system', tuning_text, flags=re.IGNORECASE)
        tuning_text = re.sub(r'P/N\s+\d+-\d+', '', tuning_text)
        
        entries.append({
            "question": "How do you tune an engine with water/methanol injection?",
            "answer": """Water/methanol injection is generally not considered a bolt-on power adder for forced induction gasoline applications. Engine tuning is usually required to maximize potential power gain. Water/methanol injection allows for a more aggressive tune while still using pump gas as base fuel.

**Recommended Mixture:**
- Using a 50/50 mix of water/methanol is recommended for best combination of air charge cooling and detonation control

**Tuning Process:**
1. **Establish Base AFR:**
   - With conservative boost and timing, establish a base AFR that is one point higher than your final target AFR
   - Example: If final target AFR with injection is 11.0:1, set base AFR to 12.0:1

2. **Set Injection Flow Rate:**
   - Start injecting water/methanol
   - Adjust injection flow rate to achieve final target AFR
   - Example: If base AFR is 12.0:1 and during injection AFR drops to 10.5:1, reduce flow rate until target 11.0:1 is reached
   - Generally recommended to change injection flow rate (not primary fueling) to reach target AFR
   - Flow rate adjustments can be made by:
     - Changing nozzle selection
     - Adjusting "Start PSI" and "Full PSI" settings on controller

3. **Increase Boost and Timing:**
   - Once injection flow rate is set to deliver desired final AFR
   - Increase boost and ignition timing to take advantage of additional air charge cooling and detonation control

**Performance Expectations:**
- When injecting correct amount, 50/50 mix provides effective octane of over 110 when using base fuel of 91-93 octane pump gas
- Properly tuned system will usually support typical "race gas" engine tune""",
            "keywords": ["water methanol tuning", "injection tuning", "AFR tuning", "boost tuning", "engine tuning"],
            "topic": "Water/Methanol Injection - Tuning"
        })
    
    # 6. Cold Weather Operation
    cold_weather_text = """
Water/methanol mix lowers the freezing point of the fluid. Below are freezing points for different percentages of water/methanol mixtures:

**Freezing Point Chart:**
- 20°F: Requires 13% methanol concentration by volume
- 0°F: Requires 24% methanol concentration by volume
- -15°F: Requires 35% methanol concentration by volume
- -40°F: Requires 46% methanol concentration by volume

**Cold Weather Considerations:**
- Higher methanol concentrations are needed in colder climates to prevent freezing
- However, never exceed 50% methanol for safety reasons
- If operating below -40°F, consider additional anti-freeze measures or system protection
"""
    entries.append({
        "question": "How does cold weather affect water/methanol injection systems?",
        "answer": cold_weather_text,
        "keywords": ["cold weather", "freezing point", "methanol concentration", "winter operation"],
        "topic": "Water/Methanol Injection - Cold Weather"
    })
    
    # 7. Maintenance
    maintenance_text = """
**Regular Maintenance:**
- Injector nozzle should be cleaned periodically
- Disassemble nozzle and clean with suitable cleaner until all debris is removed
- If excessive contamination is found, check rest of system for source

**System Inspection:**
- Check for leaks in hoses and fittings
- Verify pump operation and flow
- Check controller operation and error indicators
- Inspect filter (if equipped) and replace if necessary

**Fluid Quality:**
- Use distilled water (not tap water) to prevent mineral buildup
- Use quality methanol
- Keep system clean to prevent nozzle clogging
"""
    entries.append({
        "question": "How do you maintain a water/methanol injection system?",
        "answer": maintenance_text,
        "keywords": ["maintenance", "cleaning", "nozzle cleaning", "system maintenance"],
        "topic": "Water/Methanol Injection - Maintenance"
    })
    
    # 8. Optional Components
    optional_text = """
**Optional System Upgrades:**

1. **Solenoid Valve:**
   - Eliminates any chance of water/methanol flow into inlet when system is not engaged
   - Features high flow capability and low current draw
   - Installed after pump and before nozzle (close to nozzle for best results)
   - Activates whenever system is pumping

2. **Injection Filter:**
   - Inline filter with micronic mesh screen (typically 40 microns)
   - Filters particles to protect pump, lines, and nozzles
   - Increases overall system longevity
   - Highly recommended when using flow gauge

3. **Additional Nozzles:**
   - Multiple nozzles can be used for larger engines or higher flow requirements
   - Includes complete nozzle, multiple pintle sizes, and necessary hardware

4. **Larger Tank:**
   - Upgrade to larger capacity tank for extended operation
   - May include level sensor for monitoring fluid level

5. **Flow Sensor/Gauge:**
   - Monitor actual injection flow rate
   - Helps with tuning and system verification
"""
    entries.append({
        "question": "What optional components are available for water/methanol injection systems?",
        "answer": optional_text,
        "keywords": ["optional components", "solenoid", "filter", "flow sensor", "upgrades"],
        "topic": "Water/Methanol Injection - Components"
    })
    
    # 9. Controller Settings
    controller_text = """
**Progressive Controller Features:**
- Progressive pump controller with "Boost Safe" feature
- Two dial pump speed control (Start PSI and Full PSI)
- System status LED indicators (pump duty cycle and system errors)
- Test button for manual pump triggering
- Error protection with over-current, over-voltage, and over-temperature protection
- Pump open and short detection

**Controller Settings:**
- **Start PSI:** Boost pressure at which injection begins
- **Full PSI:** Boost pressure at which injection reaches maximum flow
- **Non-Progressive Operation:** Set "Full PSI" lower than "Start PSI" for on/off operation

**Controller Location:**
- Must be mounted inside vehicle (NOT in engine bay)
- Controller is NOT waterproof
- Common locations: dash or glove box
"""
    entries.append({
        "question": "How do you configure a water/methanol injection controller?",
        "answer": controller_text,
        "keywords": ["controller", "settings", "progressive controller", "boost safe", "PSI settings"],
        "topic": "Water/Methanol Injection - Controller"
    })
    
    # 10. Safety Warnings
    safety_warnings = """
**Critical Safety Warnings:**

1. **Methanol Toxicity:**
   - Methanol is a potent neurotoxin
   - Can be absorbed through skin
   - Even small amounts can cause blindness or death
   - Handle with extreme care

2. **Flammability:**
   - Methanol is highly flammable
   - 100% methanol ignites easily
   - Burns with almost undetectable flame
   - Use maximum 50% concentration for safety

3. **Installation Safety:**
   - Disconnect battery ground during electronic installation
   - Follow all installation instructions carefully
   - Improper installation can result in major engine/vehicle damage

4. **Legal Restrictions:**
   - Race-only product for competition vehicles
   - May not be used on public roads
   - Check local laws and regulations

5. **Nozzle Placement:**
   - Must be mounted above tank to prevent gravity/siphoning leaks
   - Incorrect placement can cause engine damage
"""
    entries.append({
        "question": "What are the safety warnings for water/methanol injection systems?",
        "answer": safety_warnings,
        "keywords": ["safety", "methanol safety", "toxicity", "flammability", "warnings"],
        "topic": "Water/Methanol Injection - Safety"
    })
    
    return entries


def main():
    """Download paper and add to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    # Create temp directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "water_methanol_manual.pdf"
        
        # Download PDF
        if not download_pdf(PAPER_URL, pdf_path):
            LOGGER.error("Failed to download PDF")
            return
        
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            LOGGER.error("Downloaded file is empty or doesn't exist")
            return
        
        LOGGER.info(f"PDF size: {pdf_path.stat().st_size} bytes")
        
        # Extract text
        full_text = extract_text_from_pdf(pdf_path)
        if not full_text or len(full_text) < 500:
            LOGGER.error("Failed to extract sufficient text from PDF")
            return
        
        LOGGER.info(f"Extracted {len(full_text)} characters from PDF")
        
        # Create knowledge entries
        entries = create_knowledge_entries(full_text)
        LOGGER.info(f"Created {len(entries)} knowledge entries")
        
        # Initialize knowledge base
        LOGGER.info("Initializing knowledge base...")
        vector_store = VectorKnowledgeStore()
        kb_file_manager = KnowledgeBaseFileManager()
        
        added_count = 0
        
        # Add each entry
        for entry in entries:
            try:
                LOGGER.info(f"Adding: {entry['question'][:60]}...")
                
                # Add to vector store
                vector_store.add_knowledge(
                    text=f"{entry['question']}\n\n{entry['answer']}",
                    metadata={
                        "question": entry["question"],
                        "topic": entry["topic"],
                        "keywords": ", ".join(entry["keywords"]),
                        "source": PAPER_URL,
                        "title": entry["question"],
                        "category": "Water/Methanol Injection",
                        "data_type": "installation_guide"
                    }
                )
                
                # Add to KB file manager
                kb_file_manager.add_entry(
                    question=entry["question"],
                    answer=entry["answer"],
                    source=PAPER_URL,
                    title=entry["question"],
                    topic=entry["topic"],
                    keywords=entry["keywords"],
                    verified=True
                )
                
                added_count += 1
                LOGGER.info(f"  Successfully added")
                
            except Exception as e:
                LOGGER.error(f"  Failed to add entry: {e}")
        
        LOGGER.info(f"\n{'='*70}")
        LOGGER.info(f"SUMMARY")
        LOGGER.info(f"{'='*70}")
        LOGGER.info(f"Total entries: {len(entries)}")
        LOGGER.info(f"Successfully added: {added_count}")
        LOGGER.info(f"\nWater/Methanol Injection setup guide has been added!")
        LOGGER.info(f"Source: {PAPER_URL}")


if __name__ == "__main__":
    main()

