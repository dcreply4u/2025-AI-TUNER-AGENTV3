# Nitrous Tuning Papers Ingestion Guide

## Overview

This guide explains how to add nitrous tuning academic papers to the AI Chat Advisor's knowledge base.

## Automatic Download (Attempted)

The script `ingest_nitrous_papers.py` attempts to automatically download papers from the provided URLs. However, many academic papers are:

- **Behind paywalls** (SAE papers require purchase)
- **Require login** (ResearchGate often requires account)
- **URLs may have changed** (404 errors are common)
- **Hosted on institutional servers** (may block direct access)

## Manual Download Process

If automatic download fails, you can manually download and add papers:

### Step 1: Download PDFs

1. Visit the paper URLs (or search for them on Google Scholar, ResearchGate, etc.)
2. Download the PDFs to your computer
3. Place them in: `downloads/nitrous_papers/`

### Step 2: Rename Files (Optional)

The script expects files named like:
- `01_Performance_and_Emission_Characteristics...pdf`
- `02_Effect_of_Nitrous_Oxide_Injection...pdf`
- etc.

But you can use any name - the script will try to ingest any PDFs in the directory.

### Step 3: Run Ingestion

```bash
python ingest_nitrous_papers.py
```

The script will:
- Check for existing PDFs in `downloads/nitrous_papers/`
- Ingest any PDFs it finds
- Add them to the knowledge base with proper metadata

## Paper List

### 1. Performance and Emission Characteristics of a Spark Ignition Engine Using Nitrous Oxide Injection
- **Authors:** S. Kumar et al.
- **Journal:** International Journal of Mechanical Engineering and Technology (IJMET)
- **URL:** https://www.researchgate.net/publication/335842746_Performance_and_Emission_Characteristics_of_a_Spark_Ignition_Engine_Using_Nitrous_Oxide_Injection
- **Status:** Requires ResearchGate login

### 2. Effect of Nitrous Oxide Injection on the Performance of Gasoline Engines
- **Authors:** A. S. Abdalla et al.
- **Journal:** ARPN Journal of Engineering and Applied Sciences
- **URL:** http://www.arpnjournals.org/jeas/research_papers/rp_2017/jeas_0317_5934.pdf
- **Status:** URL may have changed (404 error)

### 3. Numerical Simulation of Nitrous Oxide Injection in Internal Combustion Engines
- **Authors:** M. S. Islam et al.
- **Journal:** International Journal of Automotive and Mechanical Engineering
- **URL:** https://ijame.ump.edu.my/images/Volume_16_1_2019/10_Islam.pdf
- **Status:** URL may have changed (404 error)

### 4. Optimization of Nitrous Oxide Injection Systems for Racing Applications
- **Authors:** SAE Technical Paper
- **Journal:** SAE Technical Paper 2002-01-1668
- **URL:** https://www.sae.org/publications/technical-papers/content/2002-01-1668/
- **Status:** Requires purchase or institutional access

### 5. Experimental Study on the Effect of Nitrous Oxide on Engine Performance
- **Authors:** M. V. Reddy et al.
- **Journal:** International Journal of Engineering Research & Technology (IJERT)
- **URL:** https://www.ijert.org/research/experimental-study-on-the-effect-of-nitrous-oxide-on-engine-performance-IJERTV3IS110642.pdf
- **Status:** URL may have changed (404 error)

## Alternative Sources

If the original URLs don't work, try:

1. **Google Scholar:** https://scholar.google.com/
   - Search for paper titles
   - Many papers have "PDF" links

2. **ResearchGate:** https://www.researchgate.net/
   - Create free account
   - Search for papers
   - Request full-text or download if available

3. **Institutional Repositories:**
   - Many universities host papers on their repositories
   - Search for author names + paper title

4. **Sci-Hub** (if legal in your jurisdiction):
   - Can access many paywalled papers
   - Use DOI or URL

## Verification

After ingestion, test the knowledge base:

```python
from services.vector_knowledge_store import VectorKnowledgeStore

store = VectorKnowledgeStore()
results = store.search("nitrous oxide injection tuning", n_results=5)

for result in results:
    print(f"Title: {result['metadata'].get('title', 'Unknown')}")
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Preview: {result['text'][:200]}...")
    print()
```

## Topics Covered

These papers cover:

- **Combustion Efficiency:** How N₂O increases oxygen availability
- **Tuning Parameters:** Air-fuel ratio, ignition timing, jet sizing
- **Thermal Stress:** Impact on engine durability
- **CFD Modeling:** Predictive simulation of injection effects
- **Emission Effects:** NOx and CO₂ emissions analysis

## Next Steps

1. Download available PDFs manually
2. Place them in `downloads/nitrous_papers/`
3. Run `python ingest_nitrous_papers.py`
4. Test the AI Chat Advisor with nitrous-related questions
5. Add more papers as you find them

