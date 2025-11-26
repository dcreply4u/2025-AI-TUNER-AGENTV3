#!/usr/bin/env python3
"""
Download and ingest nitrous tuning academic papers into the AI Chat Advisor knowledge base.

This script downloads PDF papers from the provided URLs and adds them to the vector knowledge store.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Try to import required libraries
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    LOGGER.error("requests library not available. Install with: pip install requests")

try:
    from services.knowledge_base_manager import KnowledgeBaseManager
    from services.vector_knowledge_store import VectorKnowledgeStore
    KB_AVAILABLE = True
except ImportError as e:
    KB_AVAILABLE = False
    LOGGER.error(f"Knowledge base modules not available: {e}")

# Paper information
NITROUS_PAPERS = [
    {
        "title": "Performance and Emission Characteristics of a Spark Ignition Engine Using Nitrous Oxide Injection",
        "authors": "S. Kumar et al.",
        "journal": "International Journal of Mechanical Engineering and Technology (IJMET)",
        "url": "https://www.researchgate.net/publication/335842746_Performance_and_Emission_Characteristics_of_a_Spark_Ignition_Engine_Using_Nitrous_Oxide_Injection",
        "focus": "Experimental analysis of N₂O injection effects on power, torque, and emissions",
        "downloadable": True,
        "note": "ResearchGate - may require login or direct PDF link"
    },
    {
        "title": "Effect of Nitrous Oxide Injection on the Performance of Gasoline Engines",
        "authors": "A. S. Abdalla et al.",
        "journal": "ARPN Journal of Engineering and Applied Sciences",
        "url": "http://www.arpnjournals.org/jeas/research_papers/rp_2017/jeas_0317_5934.pdf",
        "focus": "Investigates optimal injection ratios and timing for improved combustion efficiency",
        "downloadable": True,
        "direct_pdf": True
    },
    {
        "title": "Numerical Simulation of Nitrous Oxide Injection in Internal Combustion Engines",
        "authors": "M. S. Islam et al.",
        "journal": "International Journal of Automotive and Mechanical Engineering",
        "url": "https://ijame.ump.edu.my/images/Volume_16_1_2019/10_Islam.pdf",
        "focus": "CFD modeling of N₂O injection and its thermodynamic impact",
        "downloadable": True,
        "direct_pdf": True
    },
    {
        "title": "Optimization of Nitrous Oxide Injection Systems for Racing Applications",
        "authors": "SAE Technical Paper",
        "journal": "SAE Technical Paper 2002-01-1668",
        "url": "https://www.sae.org/publications/technical-papers/content/2002-01-1668/",
        "focus": "System design, jet sizing, and fuel compensation strategies",
        "downloadable": False,
        "note": "SAE Paper - requires purchase or institutional access"
    },
    {
        "title": "Experimental Study on the Effect of Nitrous Oxide on Engine Performance",
        "authors": "M. V. Reddy et al.",
        "journal": "International Journal of Engineering Research & Technology (IJERT)",
        "url": "https://www.ijert.org/research/experimental-study-on-the-effect-of-nitrous-oxide-on-engine-performance-IJERTV3IS110642.pdf",
        "focus": "Experimental setup and data on torque, power, and fuel-air ratio tuning",
        "downloadable": True,
        "direct_pdf": True
    }
]


def search_for_pdf(title: str, authors: str = "") -> Optional[str]:
    """
    Search for PDF using web search as fallback.
    
    Args:
        title: Paper title
        authors: Paper authors
        
    Returns:
        URL if found, None otherwise
    """
    try:
        from services.web_search_service import WebSearchService
        search_service = WebSearchService()
        
        if not search_service.is_available():
            LOGGER.debug("Web search service not available")
            return None
        
        # Try multiple search queries
        queries = [
            f'"{title}" filetype:pdf',
            f"{title} {authors} pdf",
            f"{title} download pdf",
            f"{title} site:researchgate.net OR site:academia.edu OR site:arxiv.org"
        ]
        
        for query in queries:
            try:
                LOGGER.debug(f"  Searching: {query}")
                results = search_service.search(query, max_results=5)
                
                for result in results:
                    url = result.url.lower()
                    snippet = result.snippet.lower() if result.snippet else ""
                    
                    # Check if it's a PDF link
                    if (url.endswith('.pdf') or 
                        'pdf' in url or 
                        'pdf' in snippet or
                        'download' in snippet):
                        LOGGER.info(f"  Found alternative PDF source: {result.url}")
                        return result.url
            except Exception as e:
                LOGGER.debug(f"  Search query failed: {e}")
                continue
        
        return None
    except Exception as e:
        LOGGER.debug(f"Web search failed: {e}")
        return None


def download_pdf(url: str, output_path: Path, headers: Optional[Dict[str, str]] = None) -> bool:
    """
    Download a PDF file from a URL.
    
    Args:
        url: URL to download from
        output_path: Path to save the PDF
        headers: Optional HTTP headers
        
    Returns:
        True if successful, False otherwise
    """
    if not REQUESTS_AVAILABLE:
        LOGGER.error("requests library not available")
        return False
    
    try:
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        if headers:
            default_headers.update(headers)
        
        LOGGER.info(f"Downloading from: {url}")
        response = requests.get(url, headers=default_headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if content is PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'pdf' not in content_type and not url.endswith('.pdf'):
            LOGGER.warning(f"URL may not be a PDF (Content-Type: {content_type})")
        
        # Save file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = output_path.stat().st_size
        LOGGER.info(f"Downloaded {file_size:,} bytes to {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        LOGGER.error(f"Unexpected error downloading {url}: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def main():
    """Main function to download and ingest papers."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available. Cannot proceed.")
        return
    
    if not REQUESTS_AVAILABLE:
        LOGGER.error("requests library not available. Install with: pip install requests")
        return
    
    # Create downloads directory
    downloads_dir = project_root / "downloads" / "nitrous_papers"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize knowledge base
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_manager = KnowledgeBaseManager(vector_store=vector_store)
    
    downloaded_count = 0
    ingested_count = 0
    failed_downloads = []
    failed_ingestions = []
    
    # Process each paper
    for i, paper in enumerate(NITROUS_PAPERS, 1):
        title = paper["title"]
        url = paper["url"]
        authors = paper.get("authors", "Unknown")
        journal = paper.get("journal", "Unknown")
        focus = paper.get("focus", "")
        
        LOGGER.info(f"\n[{i}/{len(NITROUS_PAPERS)}] Processing: {title}")
        LOGGER.info(f"  Authors: {authors}")
        LOGGER.info(f"  Journal: {journal}")
        
        # Skip if not downloadable
        if not paper.get("downloadable", False):
            LOGGER.warning(f"  Skipping - {paper.get('note', 'Not directly downloadable')}")
            continue
        
        # Generate filename
        safe_title = sanitize_filename(title)
        filename = f"{i:02d}_{safe_title}.pdf"
        file_path = downloads_dir / filename
        
        # Download PDF
        if file_path.exists():
            LOGGER.info(f"  File already exists: {file_path}")
        else:
            success = False
            
            # Try direct download first
            LOGGER.info(f"  Attempting direct download...")
            success = download_pdf(url, file_path)
            
            # If direct download failed, try web search for alternative sources
            if not success:
                LOGGER.info(f"  Direct download failed, searching for alternative PDF sources...")
                alt_url = search_for_pdf(title, authors)
                if alt_url and alt_url != url:  # Only try if different URL
                    LOGGER.info(f"  Attempting download from alternative source...")
                    success = download_pdf(alt_url, file_path)
            
            # If still failed, try searching with just title
            if not success:
                LOGGER.info(f"  Trying broader search with title only...")
                alt_url = search_for_pdf(title, "")
                if alt_url and alt_url != url:
                    LOGGER.info(f"  Attempting download from alternative source...")
                    success = download_pdf(alt_url, file_path)
            
            if not success:
                LOGGER.warning(f"  Could not download PDF automatically.")
                LOGGER.warning(f"  Manual download instructions:")
                LOGGER.warning(f"    1. Search for: '{title}'")
                LOGGER.warning(f"    2. Download PDF and save to: {file_path}")
                LOGGER.warning(f"    3. Re-run this script to ingest it")
                failed_downloads.append((title, url))
                continue
            
            downloaded_count += 1
        
        # Ingest into knowledge base
        try:
            LOGGER.info(f"  Ingesting into knowledge base...")
            metadata = {
                "title": title,
                "authors": authors,
                "journal": journal,
                "focus": focus,
                "url": url,
                "source": "nitrous_tuning_papers",
                "topic": "Nitrous Tuning",
                "category": "Academic Paper"
            }
            
            result = kb_manager.add_document(str(file_path), metadata=metadata)
            
            if result.get("success"):
                chunks = result.get("chunks_added", 0)
                LOGGER.info(f"  ✓ Successfully ingested {chunks} chunks")
                ingested_count += 1
            else:
                errors = result.get("errors", [])
                LOGGER.error(f"  ✗ Ingestion failed: {errors}")
                failed_ingestions.append((title, errors))
                
        except Exception as e:
            LOGGER.error(f"  ✗ Failed to ingest {title}: {e}")
            failed_ingestions.append((title, str(e)))
    
    # Summary
    LOGGER.info("\n" + "="*70)
    LOGGER.info("SUMMARY")
    LOGGER.info("="*70)
    LOGGER.info(f"Total papers: {len(NITROUS_PAPERS)}")
    LOGGER.info(f"Downloaded: {downloaded_count}")
    LOGGER.info(f"Ingested: {ingested_count}")
    
    if failed_downloads:
        LOGGER.warning(f"\nFailed downloads ({len(failed_downloads)}):")
        for title, url in failed_downloads:
            LOGGER.warning(f"  - {title}")
            LOGGER.warning(f"    URL: {url}")
    
    if failed_ingestions:
        LOGGER.warning(f"\nFailed ingestions ({len(failed_ingestions)}):")
        for title, error in failed_ingestions:
            LOGGER.warning(f"  - {title}")
            LOGGER.warning(f"    Error: {error}")
    
    if ingested_count > 0:
        LOGGER.info(f"\n✓ Successfully added {ingested_count} papers to knowledge base!")
        LOGGER.info("The AI Chat Advisor can now answer questions about nitrous tuning.")
    else:
        LOGGER.warning("\nNo papers were successfully ingested.")


if __name__ == "__main__":
    main()

