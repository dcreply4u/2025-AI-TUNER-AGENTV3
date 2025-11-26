#!/usr/bin/env python3
"""
Add Holley/Weiand Supercharger Technical Information to the AI Chat Advisor knowledge base.
Comprehensive guide on supercharger types, operation, drive ratios, and specifications.
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

# Supercharger Technical Knowledge from Holley/Weiand
SUPERCHARGER_KNOWLEDGE = [
    {
        "question": "What are the different types of superchargers?",
        "answer": """There are three basic types of superchargers in the performance market:

**1. Roots Type Supercharger (Weiand)**
- **Design:** Simplest and least expensive
- **Compression:** External compression (air compression takes place in cylinders and manifold, not inside supercharger)
- **Operation:** Acts as an air pump, not compressing air inside the supercharger
- **History:** First appeared in automotive applications in the 1930s
- **Applications:** Used on GMC diesel engines for many years
- **Models:** 4-71, 6-71, 8-71, 10-71, 12-71, 14-71

**2. Centrifugal Supercharger**
- **Design:** Similar to turbocharger, but belt-driven instead of exhaust-driven
- **Operation:** Runs at extremely high speeds with internal stepup drive
- **Boost Characteristic:** Faster impeller spin = more boost
- **Limitation:** Typically doesn't produce much power at low engine speeds
- **Trade-off:** If geared for low RPM boost, would make too much boost at high RPM
- **Comparison:** Similar to turbocharger but without turbo lag

**3. Screw Type Supercharger**
- **Design:** Appears similar to Roots from outside, but internal rotors are different
- **Operation:** Rotors interleave and progressively compress air as it passes along rotors
- **Tolerance:** Requires extremely high degree of tolerance
- **Cost:** More expensive than Roots type due to precision requirements
- **Compression:** Internal compression (air compression takes place inside supercharger)

**Compression Types:**
- **Internal Compression:** Centrifugal and screw type (compression inside supercharger)
- **External Compression:** Roots type (compression in cylinders and manifold)

**Bottom Line:**
Roots superchargers are the simplest and least expensive, while centrifugal and screw types offer different characteristics with internal compression.""",
        "keywords": ["supercharger types", "Roots supercharger", "centrifugal supercharger", "screw supercharger", "blower types"],
        "topic": "Superchargers - Types"
    },
    {
        "question": "How does a supercharger work and what does it do?",
        "answer": """A supercharger forces more air and fuel into the engine cylinders, increasing power output.

**Basic Engine Operation:**
- Engine draws in air mixed with gasoline (fuel/air charge)
- Piston creates vacuum on intake stroke, drawing in charge
- Piston compresses charge on compression stroke (e.g., 9:1 compression ratio = 1/9th original volume)
- Spark plug ignites compressed charge
- Combustion forces piston down, producing power

**Volumetric Efficiency:**
- **Unblown Engine:** Atmospheric pressure tries to fill cylinder
- **100% Efficiency:** Would mean cylinder fills completely with air
- **Typical Efficiency:** Less than 100% due to restrictions (air cleaner, cylinder head, cam timing)
- **Improvement:** Better heads, cam timing, larger carburetor can improve efficiency

**What Superchargers Do:**
- **Force Air In:** Supercharger forces air into engine instead of relying on vacuum
- **Exceed 100% Efficiency:** Can pack more air/fuel into cylinders than atmospheric pressure allows
- **More Power:** More fuel and air in cylinder = more powerful combustion = more power and torque
- **Boost Creation:** Creates positive pressure (boost) in intake manifold

**Roots Supercharger Operation:**
- Does NOT compress air inside supercharger
- Acts as an air pump
- Compression (boost creation) takes place in cylinders and manifold
- This is why Roots are called "external compression" blowers

**Key Benefit:**
By forcing more air and fuel into cylinders, superchargers allow engines to produce significantly more power than naturally aspirated engines.""",
        "keywords": ["how supercharger works", "supercharger operation", "volumetric efficiency", "boost", "forced induction"],
        "topic": "Superchargers - Operation"
    },
    {
        "question": "What is a Roots supercharger and how does it differ from other types?",
        "answer": """Roots superchargers are the simplest and least expensive type of supercharger, used extensively by Weiand/Holley.

**Roots Supercharger Characteristics:**
- **Design:** Simplest of all supercharger types
- **Cost:** Least expensive option
- **Compression Type:** External compression (compression happens in cylinders/manifold, not inside blower)
- **Operation:** Acts as an air pump, not compressing air internally
- **History:** First appeared in automotive applications in the 1930s

**Development History:**
- Used on GMC diesel engines for many years (4-71, 6-71 models)
- Late 1950s: Phil Weiand developed manifolds and drive systems for adapting GMC diesel superchargers
- Evolved to Weiand-manufactured superchargers (including 8-71 models)
- Highly refined product offered by Holley under Weiand brand

**Differences from Other Types:**
- **vs. Centrifugal:** Roots provides boost at low RPM, centrifugal needs high RPM
- **vs. Screw Type:** Roots is simpler and less expensive, screw type has internal compression
- **vs. Turbo:** Roots is belt-driven, no lag, but uses engine power; turbo is exhaust-driven

**Weiand Models:**
- 142" (small block applications)
- 177" (small block and big block)
- 256" (big block)
- 6-71, 8-71, 10-71, 12-71, 14-71 (various sizes)

**Key Advantage:**
Roots superchargers provide immediate boost response at low RPM, making them ideal for drag racing and street performance applications where low-end torque is important.

**Bottom Line:**
Roots superchargers are simple, cost-effective, external compression blowers that provide immediate boost response, making them popular for performance applications.""",
        "keywords": ["Roots supercharger", "Weiand", "external compression", "blower", "supercharger basics"],
        "topic": "Superchargers - Roots Type"
    },
    {
        "question": "What is drive ratio and how does it affect supercharger boost?",
        "answer": """Drive ratio determines how fast the supercharger spins relative to engine speed, directly affecting boost output.

**Drive Ratio Explained:**
- **Definition:** Ratio of supercharger speed to engine speed
- **Overdriven:** Supercharger spins faster than engine (e.g., 1.30:1 = 30% faster)
- **Underdriven:** Supercharger spins slower than engine (e.g., 0.70:1 = 30% slower)
- **1:1 Ratio:** Supercharger spins at same speed as engine

**How It Affects Boost:**
- **Higher Drive Ratio = More Boost:** Faster supercharger spin = more air pumped = more boost
- **Lower Drive Ratio = Less Boost:** Slower supercharger spin = less air pumped = less boost
- **Engine Size Matters:** Larger engines need more air, so boost varies with engine displacement

**Weiand Drive Ratio Examples:**
- **6-71 Supercharger:**
  - 454 engine: 1.30:1 ratio = 19.7 PSI, 0.70:1 ratio = 3.8 PSI
  - 502 engine: 1.30:1 ratio = 16.4 PSI, 0.70:1 ratio = 3.0 PSI
  - 540 engine: 1.30:1 ratio = 14.2 PSI, 0.70:1 ratio = 2.3 PSI

- **8-71 Supercharger:**
  - 454 engine: 1.30:1 ratio = 21.7 PSI, 0.70:1 ratio = 4.9 PSI
  - 502 engine: 1.30:1 ratio = 18.2 PSI, 0.70:1 ratio = 3.0 PSI

- **10-71, 12-71, 14-71:** Similar pattern with varying boost levels

**Tuning Considerations:**
- **Power Goals:** Higher drive ratio for more power
- **Engine Limits:** Must match engine's ability to handle boost
- **Fuel System:** More boost requires more fuel capacity
- **Safety:** Don't exceed engine component limits

**Bottom Line:**
Drive ratio directly controls boost output - higher ratios produce more boost but require stronger engine components and more fuel delivery capacity.""",
        "keywords": ["drive ratio", "supercharger boost", "blower drive", "boost control", "supercharger gearing"],
        "topic": "Superchargers - Drive Ratio"
    },
    {
        "question": "What boost levels can different Weiand superchargers produce?",
        "answer": """Weiand superchargers produce varying boost levels based on model size, drive ratio, and engine displacement.

**6-71 Supercharger Boost (PSI):**
- **454 Engine:** 1.30:1 drive = 19.7 PSI, 1:1 drive = 13.3 PSI, 0.70:1 drive = 3.8 PSI
- **502 Engine:** 1.30:1 drive = 16.4 PSI, 1:1 drive = 10.6 PSI, 0.70:1 drive = 3.0 PSI
- **540 Engine:** 1.30:1 drive = 14.2 PSI, 1:1 drive = 8.8 PSI, 0.70:1 drive = 2.3 PSI
- **600 Engine:** 1.30:1 drive = 11.3 PSI, 1:1 drive = 6.5 PSI
- **650 Engine:** 1.30:1 drive = 9.3 PSI, 1:1 drive = 4.9 PSI

**8-71 Supercharger Boost (PSI):**
- **454 Engine:** 1.30:1 drive = 21.7 PSI, 1:1 drive = 13.3 PSI, 0.70:1 drive = 4.9 PSI
- **502 Engine:** 1.30:1 drive = 18.2 PSI, 1:1 drive = 10.6 PSI, 0.70:1 drive = 3.0 PSI
- **540 Engine:** 1.30:1 drive = 15.9 PSI, 1:1 drive = 8.8 PSI, 0.70:1 drive = 2.3 PSI
- **600 Engine:** 1.30:1 drive = 12.8 PSI, 1:1 drive = 6.5 PSI
- **650 Engine:** 1.30:1 drive = 10.7 PSI, 1:1 drive = 4.9 PSI

**10-71, 12-71, 14-71 Superchargers:**
- Produce similar boost patterns with variations based on size
- Larger models (14-71) produce more boost for same drive ratio
- Boost decreases as engine size increases (larger engines need more air)

**Key Factors:**
- **Supercharger Size:** Larger blowers (14-71) produce more boost than smaller (6-71)
- **Drive Ratio:** Higher drive ratio = more boost
- **Engine Size:** Larger engines produce less boost for same supercharger/drive ratio
- **Application:** Choose based on power goals and engine capabilities

**Bottom Line:**
Boost levels range from 3-22 PSI depending on supercharger model, drive ratio, and engine size. Larger superchargers and higher drive ratios produce more boost.""",
        "keywords": ["Weiand boost", "supercharger boost levels", "blower boost", "boost PSI", "supercharger pressure"],
        "topic": "Superchargers - Boost Levels"
    },
    {
        "question": "What are the physical dimensions of Weiand superchargers?",
        "answer": """Weiand superchargers come in various sizes with different dimensions for different applications.

**142\" Supercharger:**
- **Applications:** Chevrolet Small Block
- **Long Nose:** Height 7-5/8\", Width 8-15/16\", Length varies 8-1/4\" to 9-1/4\"
- **Short Nose:** Height 7-5/8\", Width 8-15/16\", Length 7\"
- **Pulley:** 6-rib pulley

**177\" Supercharger:**
- **Applications:** Chevrolet Small Block and Big Block
- **Small Block Long Nose:** Height 9-9/16\", Width 10-15/16\", Length 8-9/16\"
- **Small Block Short Nose:** Height 9-9/16\", Width 10-15/16\", Length 7-5/16\"
- **Big Block Long Nose:** Height 9-1/4\", Width 10-5/8\", Length 7-7/8\"
- **Big Block Short Nose:** Height 9-1/4\", Width 10-5/8\", Length 6-5/8\"
- **Pulley:** 6-rib (SB) or 10-rib (BB)

**256\" Supercharger:**
- **Application:** Chevrolet Big Block
- **Dimensions:** Height 10-1/2\", Width 10-1/2\", Length 9-1/4\"
- **Pulley:** 16-rib pulley
- **Note:** Dimensions listed are less carburetor adapter (add 1\" for adapter)

**6-71 Supercharger:**
- **Small Block:** Height 11-3/16\", Width 8-3/8\", Length 3-11/16\", Overall 15\"
- **Big Block Standard Deck:** Height 11-15/16\", Width 6-3/16\", Length 4-7/16\", Overall 15\"
- **Big Block Tall Deck:** Height 12-5/16\", Width 6-3/16\", Length 4-13/16\", Overall 15\"
- **Chrysler 392 Hemi:** Height 11-1/4\", Width 10-3/16\", Length 3-11/16\", Overall 15\"

**8-71 Supercharger:**
- **Small Block:** Height 11-9/16\", Width 8-3/8\", Length 3-11/16\", Overall 16\"
- **Big Block Standard Deck:** Height 12-1/8\", Width 7-3/16\", Length 4-7/16\", Overall 16\"
- **Big Block Tall Deck:** Height 12-1/2\", Width 7-3/16\", Length 4-13/16\", Overall 16\"
- **Chrysler 426 Hemi:** Height 12-5/16\", Width 12-1/4\", Length 4-1/2\", Overall 16\"

**10-71, 12-71, 14-71 Superchargers:**
- **10-71:** Overall length 17\" (add 0.600\" to dimension C & G for 10-rib)
- **12-71:** Overall length 18\"
- **14-71:** Overall length 19\"
- Dimensions vary by engine application (standard deck vs. tall deck)

**Important Notes:**
- Dimensions for 6-71 through 14-71 are less adapter (add 1\" for carburetor adapters, except adapter 7164 which is 2-3/4\")
- 10-rib dimensions add 0.600\" to dimension C & G
- Choose based on engine application and clearance requirements

**Bottom Line:**
Supercharger dimensions vary significantly by model and application. Proper measurement and clearance checking is essential before installation.""",
        "keywords": ["supercharger dimensions", "Weiand dimensions", "blower size", "supercharger measurements", "installation clearance"],
        "topic": "Superchargers - Dimensions"
    },
    {
        "question": "What is the difference between internal and external compression superchargers?",
        "answer": """Superchargers are classified by where air compression takes place - inside or outside the supercharger.

**External Compression (Roots Type):**
- **Compression Location:** Air compression takes place in cylinders and intake manifold
- **Supercharger Function:** Acts as an air pump, not compressing air internally
- **Operation:** Supercharger moves air, but compression happens downstream
- **Examples:** All Weiand/Roots superchargers (4-71, 6-71, 8-71, etc.)
- **Advantages:** Simpler design, less expensive, immediate boost response
- **Characteristics:** Boost builds as engine speed increases

**Internal Compression (Centrifugal and Screw Type):**
- **Compression Location:** Air compression takes place inside the supercharger
- **Supercharger Function:** Actively compresses air before it enters intake manifold
- **Operation:** Air is compressed as it passes through supercharger
- **Examples:** Centrifugal superchargers, screw-type superchargers
- **Advantages:** More efficient compression, can produce higher boost
- **Characteristics:** Compression ratio built into supercharger design

**Key Differences:**
- **Efficiency:** Internal compression is generally more efficient
- **Cost:** External compression (Roots) is simpler and less expensive
- **Boost Response:** External compression provides immediate low-RPM boost
- **Design Complexity:** Internal compression requires more precision and tighter tolerances

**Why It Matters:**
- **Tuning:** Understanding compression type helps with boost management
- **Selection:** Choose based on application needs (low-end torque vs. high-RPM power)
- **Efficiency:** Internal compression may be more efficient but Roots provides better low-RPM response

**Bottom Line:**
Roots superchargers use external compression (air compressed in cylinders/manifold), while centrifugal and screw types use internal compression (air compressed inside supercharger). Each has advantages for different applications.""",
        "keywords": ["internal compression", "external compression", "supercharger compression", "Roots vs centrifugal", "compression types"],
        "topic": "Superchargers - Compression Types"
    },
    {
        "question": "How do you select the right supercharger size and drive ratio?",
        "answer": """Selecting the right supercharger requires matching size and drive ratio to your engine and power goals.

**Supercharger Size Selection:**
- **142\" / 177\":** Small block applications, moderate power goals
- **256\":** Big block applications, higher power goals
- **6-71:** Entry-level, moderate boost applications
- **8-71:** Popular choice, good balance of size and power
- **10-71, 12-71, 14-71:** Larger applications, maximum power potential

**Drive Ratio Selection:**
- **High Drive Ratio (1.20:1 to 1.30:1):** Maximum boost, maximum power
  - Requires strong engine components
  - Needs robust fuel system
  - Higher stress on engine
- **Medium Drive Ratio (1:1):** Balanced performance
  - Good for street/strip applications
  - Moderate boost levels
  - More engine-friendly
- **Low Drive Ratio (0.70:1 to 0.90:1):** Lower boost, more reliability
  - Less stress on engine
  - Better for daily driving
  - Easier on engine components

**Engine Size Considerations:**
- **Larger Engines:** Need more air, so same supercharger/drive ratio produces less boost
- **Smaller Engines:** Same supercharger/drive ratio produces more boost
- **Example:** 6-71 at 1.30:1 on 454 = 19.7 PSI, but on 650 = 9.3 PSI

**Power Goal Matching:**
- **Moderate Power (5-10 PSI):** Smaller supercharger, lower drive ratio
- **High Power (10-15 PSI):** Medium supercharger, medium drive ratio
- **Maximum Power (15+ PSI):** Larger supercharger, high drive ratio

**Supporting Modifications:**
- **Fuel System:** Must support increased fuel demand
- **Engine Components:** Pistons, rods, head gaskets must handle boost
- **Ignition System:** Stronger ignition for denser charge
- **Cooling:** Intercooler may be needed for high boost

**Bottom Line:**
Select supercharger size and drive ratio based on engine size, power goals, and supporting modifications. Larger superchargers and higher drive ratios produce more boost but require stronger engine components.""",
        "keywords": ["supercharger selection", "blower sizing", "drive ratio selection", "supercharger matching", "boost selection"],
        "topic": "Superchargers - Selection"
    }
]

ARTICLE_URL = "https://documents.holley.com/techlibrary_supercharger_tech_info.pdf"
ARTICLE_SOURCE = "Holley/Weiand Supercharger Technical Information"


def main():
    """Add supercharger technical information to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in SUPERCHARGER_KNOWLEDGE:
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
                    "category": "Superchargers",
                    "data_type": "technical_manual"
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
    LOGGER.info(f"Total entries: {len(SUPERCHARGER_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nHolley/Weiand Supercharger Technical Information has been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTopics covered:")
    LOGGER.info(f"  - Supercharger types (Roots, Centrifugal, Screw)")
    LOGGER.info(f"  - How superchargers work")
    LOGGER.info(f"  - Roots supercharger characteristics")
    LOGGER.info(f"  - Drive ratio and boost relationship")
    LOGGER.info(f"  - Boost levels for different models")
    LOGGER.info(f"  - Physical dimensions and specifications")
    LOGGER.info(f"  - Internal vs external compression")
    LOGGER.info(f"  - Supercharger selection guide")


if __name__ == "__main__":
    main()


