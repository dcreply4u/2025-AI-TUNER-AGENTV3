#!/usr/bin/env python3
"""
Add comprehensive methanol tuning information to the AI Chat Advisor knowledge base.
Includes provided tuning guide and scraped content from referenced websites.
"""

import logging
import sys
import requests
from pathlib import Path
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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

# Methanol tuning information from user
METHANOL_TUNING_ENTRIES = [
    {
        "question": "How do you tune an engine for methanol racing fuel?",
        "answer": """To tune for methanol racing gas, follow these key steps:

**1. Air-Fuel Ratio (AFR) Adjustment:**
- Target a much richer mixture than gasoline: AFR between 9.0:1 and 9.3:1
- Lambda of 0.61 to 0.635 for safety and longevity
- Being intentionally rich is a safety measure - it's safer to go richer than leaner
- Methanol has a stoichiometric air-fuel ratio of about 6.42:1 (nearly half that of gasoline)

**2. Ignition Timing:**
- Advance ignition timing significantly
- Methanol burns slower and cooler than gasoline, requiring more aggressive timing to maximize power
- Document all changes carefully

**3. Compression Ratio:**
- Increase compression ratio to maximize gains
- Methanol's high octane rating and cooling properties allow for higher compression without knocking
- May see little to no advantage without increasing compression
- Consult engine builder before making changes

**4. Fuel System Requirements:**
- Ensure fuel system is compatible with methanol (methanol is corrosive to many materials)
- Use larger fuel injectors (need about twice the fuel flow)
- Consider staged injection systems
- Upgrade fuel pump and lines for higher flow rates

**5. Water-Methanol Injection (if applicable):**
- Adjust injection start time to avoid negative impact on flame front
- Set end time at maximum boost pressure
- Match nozzle size to power level (overly large nozzle can cause power loss)

**6. Monitoring and Documentation:**
- Use wideband oxygen sensor to monitor AFR closely
- Document all changes and results
- Maintain clean fuel system (methanol is hygroscopic and attracts water)""",
        "keywords": ["methanol tuning", "methanol racing fuel", "AFR tuning", "methanol AFR", "methanol fuel system"],
        "topic": "Methanol Tuning - Overview"
    },
    {
        "question": "What is the target air-fuel ratio for methanol racing fuel?",
        "answer": """Methanol requires a much richer air-fuel ratio than gasoline.

**Target AFR:**
- **AFR Range:** 9.0:1 to 9.3:1
- **Lambda Range:** 0.61 to 0.635
- **Purpose:** Safety and engine longevity

**Why So Rich:**
- Methanol's stoichiometric AFR is about 6.42:1 (nearly half that of gasoline's 14.7:1)
- Being intentionally rich is a safety measure
- It's safer to go richer than leaner with methanol
- Prevents engine damage from lean conditions

**Enrichment Requirements:**
- **Normally Aspirated:** May need around 15% excess fuel
- **Supercharged/Forced Induction:** Could need 65-85% excess fuel depending on cylinder head
- Enrichment needs vary based on engine configuration and boost levels

**Important:**
- Always use a wideband oxygen sensor to monitor AFR closely
- Tune to manufacturer's recommended values
- Document all changes and results""",
        "keywords": ["methanol AFR", "air fuel ratio", "methanol mixture", "9.0:1", "9.3:1", "lambda 0.61"],
        "topic": "Methanol Tuning - AFR"
    },
    {
        "question": "How much fuel flow is needed for methanol compared to gasoline?",
        "answer": """Methanol requires approximately twice the fuel flow compared to gasoline.

**Fuel Flow Requirements:**
- **Stoichiometric AFR:** Methanol is 6.42:1 vs. gasoline's 14.7:1
- **Fuel Flow:** Need about twice the fuel flow for methanol
- **Injector Size:** Often requires larger fuel injectors or staged injection systems

**Fuel System Upgrades:**
- **Injectors:** Upgrade to larger injectors to handle increased flow
- **Staged Injection:** Consider staged injection system with smaller set for low-speed/low-load conditions
- **Fuel Pump:** Ensure fuel pump can handle higher flow rates
- **Fuel Lines:** Upgrade fuel lines to handle increased flow

**Enrichment by Engine Type:**
- **Normally Aspirated:** Around 15% excess fuel
- **Supercharged/Forced Induction:** 65-85% excess fuel depending on cylinder head and boost level

**Important Considerations:**
- Fuel system must be compatible with methanol (methanol is corrosive)
- Ensure adequate fuel system capacity before tuning
- Monitor fuel pressure and flow rates during tuning""",
        "keywords": ["methanol fuel flow", "fuel injectors", "fuel system", "methanol fuel requirement", "staged injection"],
        "topic": "Methanol Tuning - Fuel System"
    },
    {
        "question": "How do you adjust ignition timing for methanol?",
        "answer": """Methanol requires more aggressive ignition timing than gasoline.

**Timing Adjustment:**
- **Advance Ignition Timing:** Methanol's slower burn requires more aggressive timing to maximize power
- **Burn Characteristics:** Methanol burns cooler and slower than gasoline
- **Purpose:** Maximize power output by allowing complete combustion

**Important Considerations:**
- Document all timing changes carefully
- Monitor engine behavior after each adjustment
- Methanol's high octane rating allows for more aggressive timing without knocking
- Work with engine builder to determine optimal timing for your specific setup

**Tuning Process:**
- Start with conservative timing
- Gradually advance timing while monitoring for detonation
- Use data logging to track timing changes and results
- Methanol's cooling properties help prevent detonation even with advanced timing""",
        "keywords": ["methanol timing", "ignition timing", "spark advance", "methanol burn", "timing adjustment"],
        "topic": "Methanol Tuning - Ignition Timing"
    },
    {
        "question": "What compression ratio should be used with methanol?",
        "answer": """Methanol allows for higher compression ratios than gasoline.

**Compression Ratio:**
- **Increase Compression:** Methanol's high octane rating and cooling properties allow for higher compression without knocking
- **Performance Gain:** May see little to no advantage without increasing compression
- **Consultation:** Wise to consult engine builder before making changes

**Why Higher Compression Works:**
- Methanol has very high octane rating (typically 100+)
- Methanol's cooling properties help prevent detonation
- Higher compression maximizes the benefits of methanol's properties

**Important:**
- Compression changes require engine modifications
- Consult with engine builder for your specific application
- Higher compression increases power potential but requires proper tuning
- Ensure fuel system can support increased fuel requirements at higher compression""",
        "keywords": ["methanol compression", "compression ratio", "high compression", "methanol octane"],
        "topic": "Methanol Tuning - Compression"
    },
    {
        "question": "What fuel system components are compatible with methanol?",
        "answer": """Methanol is corrosive and requires compatible fuel system components.

**Compatibility Requirements:**
- **Methanol Corrosion:** Methanol is corrosive to many materials, especially unanodized aluminum
- **Compatible Materials:** Use fuel system rated for methanol
- **Components to Check:**
  - Fuel lines (must be methanol-compatible)
  - Fuel tanks (must be methanol-compatible)
  - Seals and gaskets (must be methanol-compatible)
  - Fuel injectors (must handle methanol)
  - Fuel pump (must be methanol-compatible)

**System Upgrades:**
- Upgrade fuel injectors for higher flow rates
- Ensure fuel pump can handle increased flow
- Upgrade fuel lines to handle flow and be methanol-compatible
- Use methanol-compatible seals throughout system

**Maintenance:**
- Methanol is hygroscopic (attracts water), which can lead to corrosion
- Proper storage and maintenance are critical
- Keep fuel system clean and free of debris
- Monitor for corrosion and replace components as needed""",
        "keywords": ["methanol compatibility", "fuel system", "methanol corrosion", "fuel lines", "methanol safe"],
        "topic": "Methanol Tuning - Fuel System Compatibility"
    },
    {
        "question": "How do you tune water-methanol injection timing?",
        "answer": """Water-methanol injection timing must be carefully adjusted for optimal performance.

**Injection Timing:**
- **Start Time:** Set injection start time to a point where it won't negatively impact the flame front
- **End Time:** Set end time at maximum boost pressure
- **Purpose:** Ensure injection occurs at optimal point in combustion cycle

**Nozzle Selection:**
- **Match Nozzle Size:** Select nozzle size that corresponds to your power level
- **Oversized Nozzle:** Using overly large nozzle can cause power loss
- **Downsizing:** May need to downsize nozzle if you see performance drop
- **Testing:** Test different nozzle sizes to find optimal flow rate

**Tuning Process:**
- Start with conservative injection timing
- Monitor engine performance and AFR during injection
- Adjust timing to maximize power without negative effects
- Test different nozzle sizes to optimize flow rate
- Document all changes and results""",
        "keywords": ["water methanol injection", "injection timing", "nozzle size", "WMI timing", "injection start"],
        "topic": "Methanol Tuning - Water/Methanol Injection"
    },
    {
        "question": "What are the best practices for methanol tuning?",
        "answer": """Follow these best practices when tuning for methanol:

**1. Use Wideband Oxygen Sensor:**
- Monitor air-fuel ratio closely using wideband O2 sensor
- Tune to manufacturer's recommended values
- Essential for safe and accurate tuning

**2. Document Everything:**
- Keep detailed log of all changes and results
- Helps fine-tune engine and avoid costly mistakes
- Track AFR, timing, compression, and fuel system changes

**3. Maintain Clean Fuel System:**
- Methanol is hygroscopic and attracts water
- Water can lead to corrosion
- Proper storage and maintenance are critical
- Keep fuel system clean and free of debris

**4. Safety First:**
- Target rich AFR (9.0:1 to 9.3:1) for safety
- It's safer to go richer than leaner
- Monitor engine closely during tuning
- Use compatible fuel system components

**5. Gradual Changes:**
- Make one change at a time
- Test and document results before next change
- Work with experienced tuner or engine builder
- Consult manufacturer recommendations""",
        "keywords": ["methanol tuning", "best practices", "tuning tips", "methanol safety", "tuning procedure"],
        "topic": "Methanol Tuning - Best Practices"
    }
]

# URLs to scrape
URLS_TO_SCRAPE = [
    "https://www.vpracing.com.au/blogs/the-ultimate-guide-to-racing-fuel-1/the-ultimate-guide-to-methanol-racing-fuel",
    "https://ctracing.net/site/tip-sheets/running-alcohol-tip-sheet-2/",
    "https://dragnews.com.au/masters-of-methanol-drag-racing-fuel-system-tricks/",
    "https://racecarbook.com/news/amount-of-enrichment-for-methanol-racing-engines/",
    "https://www.enginelabs.com/engine-tech/by-the-numbers-tuning-with-air-fuel-ratio-and-lambda/",
    "https://bosphorusinnovations.com/how-can-i-choose-the-correct-nozzle-size-on-water-methanol-injection/",
    "https://www.motortrend.com/how-to/0810chp-jet-performance-engine-tuning-and-transmission-setup"
]


def scrape_website(url: str) -> dict:
    """Scrape content from a website."""
    try:
        LOGGER.info(f"Scraping: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content
        main_content = None
        for selector in ['article', 'main', '.content', '.post-content', '.entry-content', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Extract text
            text = main_content.get_text(separator='\n', strip=True)
            # Clean up text
            text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive newlines
            text = text.strip()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else urlparse(url).path
            
            return {
                "url": url,
                "title": title_text,
                "content": text,
                "success": True
            }
        else:
            return {"url": url, "title": url, "content": "", "success": False, "error": "No content found"}
            
    except Exception as e:
        LOGGER.error(f"Failed to scrape {url}: {e}")
        return {"url": url, "title": url, "content": "", "success": False, "error": str(e)}


def split_content_into_chunks(content: str, max_chunk_size: int = 2000) -> list:
    """Split content into manageable chunks."""
    if len(content) <= max_chunk_size:
        return [content]
    
    chunks = []
    paragraphs = content.split('\n\n')
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        if current_size + para_size > max_chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def main():
    """Add methanol tuning information and scrape websites."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    # Add provided methanol tuning entries
    LOGGER.info("Adding provided methanol tuning information...")
    for entry in METHANOL_TUNING_ENTRIES:
        try:
            LOGGER.info(f"Adding: {entry['question'][:60]}...")
            
            vector_store.add_knowledge(
                text=f"{entry['question']}\n\n{entry['answer']}",
                metadata={
                    "question": entry["question"],
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": "Methanol Tuning Guide",
                    "title": entry["question"],
                    "category": "Methanol Tuning",
                    "data_type": "tuning_guide"
                }
            )
            
            kb_file_manager.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                source="Methanol Tuning Guide",
                title=entry["question"],
                topic=entry["topic"],
                keywords=entry["keywords"],
                verified=True
            )
            
            added_count += 1
            LOGGER.info(f"  Successfully added")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add entry: {e}")
    
    # Scrape websites and add content
    LOGGER.info("\nScraping websites for additional information...")
    for url in URLS_TO_SCRAPE:
        try:
            scraped = scrape_website(url)
            if scraped["success"] and scraped["content"]:
                LOGGER.info(f"  Scraped {len(scraped['content'])} characters from {scraped['title'][:50]}...")
                
                # Split into chunks if too large
                chunks = split_content_into_chunks(scraped["content"], max_chunk_size=2000)
                
                for i, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 200:  # Skip very short chunks
                        continue
                    
                    question = f"Information from {scraped['title']}"
                    if len(chunks) > 1:
                        question += f" (Part {i+1}/{len(chunks)})"
                    
                    try:
                        vector_store.add_knowledge(
                            text=chunk,
                            metadata={
                                "question": question,
                                "topic": "Methanol Tuning - Reference",
                                "keywords": "methanol, tuning, racing fuel, reference",
                                "source": scraped["url"],
                                "title": scraped["title"],
                                "category": "Methanol Tuning",
                                "data_type": "scraped_content"
                            }
                        )
                        
                        kb_file_manager.add_entry(
                            question=question,
                            answer=chunk,
                            source=scraped["url"],
                            title=scraped["title"],
                            topic="Methanol Tuning - Reference",
                            keywords=["methanol", "tuning", "racing fuel", "reference"],
                            verified=False  # Scraped content, not manually verified
                        )
                        
                        added_count += 1
                        
                    except Exception as e:
                        LOGGER.warning(f"  Failed to add chunk {i+1}: {e}")
            else:
                LOGGER.warning(f"  Failed to scrape {url}: {scraped.get('error', 'Unknown error')}")
                
        except Exception as e:
            LOGGER.error(f"  Error processing {url}: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Provided entries: {len(METHANOL_TUNING_ENTRIES)}")
    LOGGER.info(f"Websites scraped: {len(URLS_TO_SCRAPE)}")
    LOGGER.info(f"Total entries added: {added_count}")
    LOGGER.info(f"\nMethanol tuning information has been added to the AI Chat Advisor!")


if __name__ == "__main__":
    main()

