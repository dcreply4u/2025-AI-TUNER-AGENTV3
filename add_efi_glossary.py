#!/usr/bin/env python3
"""
Add EFI Tuning Glossary Terms to the AI Chat Advisor knowledge base.
Extracted from general tuning glossary - excludes product-specific information.
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

# EFI Tuning Glossary Terms
EFI_GLOSSARY_TERMS = [
    {
        "term": "AFR",
        "definition": "Air/Fuel Ratio - The ratio of air to fuel in the combustion mixture. For gasoline, stoichiometric is approximately 14.7:1 (air:fuel). AFR is critical for engine performance, efficiency, and preventing damage.",
        "keywords": ["AFR", "air fuel ratio", "air/fuel ratio", "stoichiometric", "mixture ratio"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Barometric Pressure",
        "definition": "The atmospheric pressure at a given location. Measured in kPa (kilopascals) or inHg (inches of mercury). At sea level, typical barometric pressure is approximately 101.3 kPa (29.92 inHg). Barometric pressure decreases with altitude. EFI systems use barometric pressure for altitude compensation in fuel calculations.",
        "keywords": ["barometric pressure", "atmospheric pressure", "baro", "altitude", "kPa"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Boost",
        "definition": "Positive pressure in the intake manifold created by forced induction (turbocharger or supercharger). Boost is measured above atmospheric pressure. For example, 10 PSI boost means the intake manifold pressure is 10 PSI above atmospheric pressure. Boost increases air density, requiring more fuel delivery.",
        "keywords": ["boost", "forced induction", "turbocharger", "supercharger", "positive pressure"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Closed Loop",
        "definition": "An operating mode where the ECU uses oxygen sensor feedback to automatically adjust fuel delivery to maintain target air/fuel ratio. Closed loop operation is typically used during cruise conditions near stoichiometric AFR. The ECU continuously monitors O2 sensor and adjusts fuel to maintain target AFR.",
        "keywords": ["closed loop", "O2 feedback", "lambda feedback", "feedback control"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Detonation",
        "definition": "Also called knock, ping, or pink. A dangerous condition where combustion starts in multiple locations in the cylinder simultaneously. Normal combustion starts at the spark plug and spreads smoothly. Detonation occurs when a second flame front starts from a hot spot before the main flame front arrives. The two flame fronts collide, creating destructive pressure levels that can damage pistons, rings, or head gaskets. Detonation is audible as a 'pinging' or 'knocking' sound.",
        "keywords": ["detonation", "knock", "ping", "pink", "pre-ignition", "engine damage"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "EGO",
        "definition": "Exhaust Gas Oxygen - The amount of oxygen remaining in the exhaust gases. EGO sensors measure this oxygen content, which indicates the air/fuel ratio of the intake mixture. Narrow band sensors detect only stoichiometric mixture, while wideband sensors can measure AFR from 10:1 to 20:1.",
        "keywords": ["EGO", "exhaust gas oxygen", "O2 sensor", "lambda sensor", "oxygen sensor"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "EGT",
        "definition": "Exhaust Gas Temperature - The temperature of exhaust gases leaving the engine. EGT is sometimes used for tuning, but it's difficult to generalize about normal values as they vary significantly by engine and application. High EGTs can indicate lean conditions or excessive timing advance. EGT monitoring is useful for detecting problems, but AFR monitoring is generally more reliable for tuning.",
        "keywords": ["EGT", "exhaust gas temperature", "exhaust temperature", "EGT sensor"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "IAT",
        "definition": "Intake Air Temperature - The temperature of air entering the intake system. IAT is critical for accurate fuel calculation because temperature affects air density. Colder air is denser and contains more oxygen, requiring more fuel. Hotter air is less dense and requires less fuel. EFI systems use IAT with MAP and volumetric efficiency to calculate air mass and determine fuel delivery using the Ideal Gas Law.",
        "keywords": ["IAT", "intake air temperature", "air temperature", "temperature sensor", "air density"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "MAP",
        "definition": "Manifold Absolute Pressure - A measure of absolute pressure in the intake manifold (relative to perfect vacuum). MAP indicates engine load and is used to determine fueling requirements. MAP scale: 0 kPa = perfect vacuum, ~100 kPa = atmospheric pressure, >100 kPa = boost. MAP is one axis of VE, AFR, and spark advance tables. MAPdot is the rate of change of MAP, used for acceleration enrichment.",
        "keywords": ["MAP", "manifold absolute pressure", "engine load", "vacuum", "boost", "kPa"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "MAPdot",
        "definition": "The rate of change of MAP (Manifold Absolute Pressure) sensor output. MAPdot indicates how quickly manifold pressure is changing, typically measured in kPa per second. MAPdot is used to detect rapid pressure increases (acceleration) and trigger acceleration enrichment to prevent lean conditions when throttle opens quickly.",
        "keywords": ["MAPdot", "MAP rate", "pressure rate", "acceleration detection", "acceleration enrichment"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Narrow Band O2 Sensor",
        "definition": "An exhaust gas oxygen sensor that can only detect stoichiometric air/fuel mixture (14.7:1 for gasoline) very closely. Narrow band sensors switch between high and low voltage at stoichiometric, but cannot accurately measure other air/fuel ratios. They are suitable for closed-loop operation at stoichiometric but not for tuning WOT or boost conditions.",
        "keywords": ["narrow band O2", "NB-O2", "narrow band sensor", "stoichiometric sensor"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Open Loop",
        "definition": "An operating mode where the ECU does not use oxygen sensor feedback for fuel adjustment. Fuel delivery is based solely on fixed parameters (VE table, etc.). Open loop is typically used for WOT (wide open throttle) and boost conditions where O2 sensor may not be accurate or fast enough. In open loop, O2 sensor voltage may still be logged but is not used for fuel adjustment.",
        "keywords": ["open loop", "no feedback", "fixed fuel", "WOT", "boost"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Retard",
        "definition": "The process of reducing ignition advance timing. Retarding timing reduces the amount of advance, firing the spark plug later. Retard is often used to avoid detonation. It can be a separate setting or achieved by reducing values in the spark advance table at specific RPM and load conditions.",
        "keywords": ["retard", "timing retard", "reduce advance", "less timing", "detonation prevention"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "RPM",
        "definition": "Revolutions Per Minute - A measure of the rotational speed of the engine. RPM indicates how fast the engine is spinning. RPM is one axis of VE, AFR, and spark advance tables. Engine performance varies significantly with RPM, requiring different fuel and timing values at different engine speeds.",
        "keywords": ["RPM", "revolutions per minute", "engine speed", "RPM range"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Stoichiometric",
        "definition": "A chemically correct mixture of fuel and air that would result in complete consumption of all fuel and all oxygen if combusted and given enough time to burn completely. For gasoline, stoichiometric is often quoted as 14.7:1 (air:fuel), but can vary by a few tenths depending on fuel composition and additives (especially oxygenates like ethanol or MTBE). Stoichiometric provides optimal fuel efficiency and emissions, but may not be best for all operating conditions.",
        "keywords": ["stoichiometric", "14.7:1", "chemically correct", "ideal mixture", "stoichiometric ratio"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Switch Point",
        "definition": "The voltage at which a narrow band O2 sensor switches from low voltage to high voltage, indicating a stoichiometric mixture. Narrow band sensors have a characteristic voltage switch point that occurs at stoichiometric AFR. This switch point is used for closed-loop operation to maintain stoichiometric mixture.",
        "keywords": ["switch point", "O2 switch", "stoichiometric switch", "narrow band switch"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "TPS",
        "definition": "Throttle Position Sensor - A voltage divider that provides information about throttle opening position. TPS indicates how far the throttle is open, from 0% (closed) to 100% (wide open throttle). TPS is used to compute rate of throttle opening (TPSdot) for acceleration enrichment. TPS also indicates driver demand and engine load.",
        "keywords": ["TPS", "throttle position sensor", "throttle position", "throttle angle"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "TPSdot",
        "definition": "The rate of change of TPS (Throttle Position Sensor) output. TPSdot indicates how quickly the throttle is being opened, typically measured in volts per second or percentage per second. TPSdot is used to detect rapid throttle opening (acceleration) and trigger acceleration enrichment to prevent lean conditions when throttle opens quickly.",
        "keywords": ["TPSdot", "TPS rate", "throttle rate", "acceleration detection", "acceleration enrichment"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Vacuum",
        "definition": "Pressure below atmospheric pressure in the intake manifold. Vacuum is the same physical phenomenon as manifold absolute pressure (MAP), but measured differently. While MAP starts at 0 for perfect vacuum and increases to ~101.3 kPa at atmospheric pressure, vacuum starts at 0 at atmospheric pressure and measures pressure below that, typically in inHg (inches of mercury), running from 0 at atmospheric to 29.92 inHg for perfect vacuum. Higher vacuum indicates lower engine load (throttle more closed).",
        "keywords": ["vacuum", "manifold vacuum", "intake vacuum", "inHg", "vacuum pressure"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "VE",
        "definition": "Volumetric Efficiency - The ratio of the mass of air that enters the cylinder in a cycle compared to the displacement of that cylinder. VE is expressed as a percentage, where 100% means the cylinder is completely filled. Naturally aspirated engines typically operate at 70-90% VE. Forced induction engines can exceed 100% VE. VE is affected by intake system design, valve timing, valve size, port design, exhaust system, RPM, and load. The VE table in EFI systems uses this to determine fuel delivery.",
        "keywords": ["VE", "volumetric efficiency", "air flow", "cylinder filling", "VE table"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Wideband O2 Sensor",
        "definition": "An exhaust gas oxygen sensor that can measure air/fuel ratios from 10:1 to 20:1, covering all ratios of interest for tuning. Wideband sensors require a sophisticated controller board to operate. They provide continuous, accurate AFR readings across the entire tuning range, making them essential for tuning WOT, boost, and all operating conditions. Wideband sensors are much more capable than narrow band sensors for tuning purposes.",
        "keywords": ["wideband O2", "WB-O2", "wideband sensor", "AFR sensor", "lambda sensor"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "WOT",
        "definition": "Wide Open Throttle - When the throttle is fully open (100% throttle position). WOT represents maximum engine load for naturally aspirated engines and maximum power production. WOT is a critical tuning condition for power applications, requiring richer air/fuel ratios (typically 11.5-12.5:1), conservative timing to prevent detonation, and adequate fuel system capacity.",
        "keywords": ["WOT", "wide open throttle", "full throttle", "maximum power", "maximum load"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "WUE",
        "definition": "Warm Up Enrichment - Additional fuel enrichment applied when the engine coolant temperature is low. WUE compensates for poor fuel vaporization and increased friction when the engine is cold. WUE typically decreases as engine temperature increases, reaching 100% (no enrichment) at operating temperature. WUE ensures smooth engine operation during warm-up.",
        "keywords": ["WUE", "warm up enrichment", "cold start enrichment", "warm-up", "cold engine"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "kPa",
        "definition": "KiloPascals - A metric unit of pressure measurement. In EFI applications, kPa is typically used to measure intake manifold vacuum, boost, or barometric pressure. The kPa scale starts at zero for total vacuum, increases to 101.3 kPa for typical atmospheric pressure at sea level, and goes higher for boost. Examples: 50 kPa ≈ 15 inHg vacuum, 100 kPa = atmospheric pressure, 250 kPa ≈ 21 PSI boost.",
        "keywords": ["kPa", "kilopascals", "pressure unit", "metric pressure"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "TBI",
        "definition": "Throttle Body Injection - A form of fuel injection where fuel is injected above the throttle plate(s). TBI was typically used on older engines as a simpler system, but is also found on some very high output racing engines because the longer vaporization time can be beneficial. TBI systems typically operate at lower fuel pressure (12-15 PSI) compared to port injection (42-45 PSI).",
        "keywords": ["TBI", "throttle body injection", "throttle body", "injection type"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Port Injection",
        "definition": "A form of fuel injection where fuel is injected directly into the intake port, near the intake valve. Port injection provides better fuel atomization and distribution compared to throttle body injection. Port injection systems typically operate at higher fuel pressure (42-45 PSI) and provide more precise fuel delivery. Most modern EFI systems use port injection.",
        "keywords": ["port injection", "fuel injection", "injection type", "port fuel injection"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "VR Sensor",
        "definition": "Variable Reluctor Sensor - An induction type sensor that is 'passive' (does not require a power source) and has a small magnet built in. VR sensors generate a voltage signal when a metal object (like a trigger wheel tooth) passes by. VR sensors are commonly used for crankshaft and camshaft position sensing. The signal from a VR sensor is inverted by VR conditioning circuits.",
        "keywords": ["VR sensor", "variable reluctor", "induction sensor", "crank sensor", "cam sensor"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Wasted Spark",
        "definition": "A method of firing spark plugs where one 'double-ended' coil simultaneously fires two spark plugs on different cylinders. One cylinder is the intended target (near TDC on compression stroke), while the other is offset by 360° in the firing order (near TDC on exhaust stroke). The second spark is 'wasted' because it doesn't ignite a mixture, but the hot ionized exhaust gases require little energy, so nearly all energy goes to the target cylinder. Wasted spark systems require a missing tooth crank wheel but don't need a cam sync signal.",
        "keywords": ["wasted spark", "ignition system", "coil on plug", "spark system"],
        "topic": "EFI Tuning - Terminology"
    },
    {
        "term": "Datalogging",
        "definition": "The process of recording real-time engine variables over time. Datalogging creates a running record of engine parameters (RPM, MAP, TPS, temperatures, AFR, etc.) that can be analyzed after the fact. Datalogs are typically stored in comma-separated value (CSV) format. Datalogging is essential for effective EFI tuning, allowing tuners to review engine behavior, identify issues, and verify tuning changes.",
        "keywords": ["datalogging", "data logging", "tuning logs", "engine logs", "datalog"],
        "topic": "EFI Tuning - Terminology"
    }
]

ARTICLE_URL = "https://www.megamanual.com/ms2/glossary.htm"
ARTICLE_SOURCE = "EFI Tuning Glossary"


def main():
    """Add EFI glossary terms to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in EFI_GLOSSARY_TERMS:
        try:
            term = entry["term"]
            LOGGER.info(f"Adding: {term}...")
            
            # Create question format
            question = f"What is {term}?"
            answer = f"{term} ({entry['term']}): {entry['definition']}"
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{question}\n\n{answer}",
                metadata={
                    "question": question,
                    "term": term,
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": ARTICLE_SOURCE,
                    "url": ARTICLE_URL,
                    "category": "EFI Glossary",
                    "data_type": "glossary_term"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=question,
                answer=answer,
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
            LOGGER.error(f"  Failed to add entry '{term}': {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total terms: {len(EFI_GLOSSARY_TERMS)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nEFI Tuning Glossary Terms have been added!")
    LOGGER.info(f"Source: {ARTICLE_URL}")
    LOGGER.info(f"\nTerms added:")
    for entry in EFI_GLOSSARY_TERMS:
        LOGGER.info(f"  - {entry['term']}")


if __name__ == "__main__":
    main()

