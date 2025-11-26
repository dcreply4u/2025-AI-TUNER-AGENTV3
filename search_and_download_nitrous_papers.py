#!/usr/bin/env python3
"""
Enhanced script to search for and download nitrous tuning papers from multiple sources.
Uses web scraping to extract content when PDFs aren't directly available.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    LOGGER.error("requests/beautifulsoup4 not available. Install with: pip install requests beautifulsoup4")

try:
    from services.knowledge_base_manager import KnowledgeBaseManager
    from services.vector_knowledge_store import VectorKnowledgeStore
    KB_AVAILABLE = True
except ImportError as e:
    KB_AVAILABLE = False
    LOGGER.error(f"Knowledge base modules not available: {e}")

# Alternative search queries for each paper
PAPER_SEARCH_QUERIES = [
    {
        "title": "Performance and Emission Characteristics of a Spark Ignition Engine Using Nitrous Oxide Injection",
        "authors": "S. Kumar",
        "search_terms": [
            "nitrous oxide injection spark ignition engine performance emission",
            "N2O injection gasoline engine performance",
            "nitrous oxide SI engine tuning"
        ],
        "alternative_sources": [
            "https://scholar.google.com/scholar?q=nitrous+oxide+injection+spark+ignition+engine",
            "https://www.researchgate.net/search?q=nitrous%20oxide%20injection%20engine"
        ]
    },
    {
        "title": "Effect of Nitrous Oxide Injection on the Performance of Gasoline Engines",
        "authors": "A. S. Abdalla",
        "search_terms": [
            "nitrous oxide gasoline engine performance ARPN",
            "N2O injection gasoline engine optimization",
            "nitrous oxide injection ratio timing"
        ],
        "alternative_sources": [
            "https://scholar.google.com/scholar?q=nitrous+oxide+gasoline+engine+ARPN",
            "http://www.arpnjournals.org/jeas/"
        ]
    },
    {
        "title": "Numerical Simulation of Nitrous Oxide Injection in Internal Combustion Engines",
        "authors": "M. S. Islam",
        "search_terms": [
            "nitrous oxide CFD simulation internal combustion engine",
            "N2O injection numerical simulation",
            "nitrous oxide injection modeling"
        ],
        "alternative_sources": [
            "https://scholar.google.com/scholar?q=nitrous+oxide+CFD+simulation+engine",
            "https://ijame.ump.edu.my/"
        ]
    },
    {
        "title": "Experimental Study on the Effect of Nitrous Oxide on Engine Performance",
        "authors": "M. V. Reddy",
        "search_terms": [
            "nitrous oxide experimental study engine performance IJERT",
            "N2O injection torque power fuel air ratio",
            "nitrous oxide engine tuning experimental"
        ],
        "alternative_sources": [
            "https://scholar.google.com/scholar?q=nitrous+oxide+experimental+engine+performance",
            "https://www.ijert.org/"
        ]
    }
]


def extract_text_from_html(url: str) -> Optional[str]:
    """
    Extract text content from an HTML page.
    
    Args:
        url: URL to scrape
        
    Returns:
        Extracted text or None
    """
    if not REQUESTS_AVAILABLE:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if len(text) > 500:  # Only return if substantial content
            return text
        
        return None
    except Exception as e:
        LOGGER.debug(f"Failed to extract text from {url}: {e}")
        return None


def find_pdf_links(url: str) -> List[str]:
    """
    Find PDF links on a webpage.
    
    Args:
        url: URL to search
        
    Returns:
        List of PDF URLs
    """
    if not REQUESTS_AVAILABLE:
        return []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_links = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf') or 'pdf' in href.lower():
                # Make absolute URL
                full_url = urljoin(url, href)
                pdf_links.append(full_url)
        
        return pdf_links
    except Exception as e:
        LOGGER.debug(f"Failed to find PDF links on {url}: {e}")
        return []


def download_pdf(url: str, output_path: Path) -> bool:
    """Download a PDF file."""
    if not REQUESTS_AVAILABLE:
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = output_path.stat().st_size
        if file_size > 1000:  # At least 1KB
            LOGGER.info(f"Downloaded {file_size:,} bytes")
            return True
        else:
            output_path.unlink()  # Delete if too small
            return False
    except Exception as e:
        LOGGER.debug(f"Download failed: {e}")
        return False


def save_text_content(text: str, output_path: Path, metadata: Dict) -> bool:
    """Save extracted text content as a text file for ingestion."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a formatted text document
        content = f"""Title: {metadata.get('title', 'Unknown')}
Authors: {metadata.get('authors', 'Unknown')}
Source: {metadata.get('url', 'Unknown')}
Extracted: {time.strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
CONTENT
{'='*70}

{text}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        LOGGER.info(f"Saved text content to {output_path}")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to save text: {e}")
        return False


def main():
    """Main function."""
    if not KB_AVAILABLE or not REQUESTS_AVAILABLE:
        LOGGER.error("Required modules not available")
        return
    
    downloads_dir = project_root / "downloads" / "nitrous_papers"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_manager = KnowledgeBaseManager(vector_store=vector_store)
    
    ingested_count = 0
    
    for i, paper in enumerate(PAPER_SEARCH_QUERIES, 1):
        title = paper["title"]
        authors = paper.get("authors", "")
        search_terms = paper.get("search_terms", [])
        alt_sources = paper.get("alternative_sources", [])
        
        LOGGER.info(f"\n[{i}/{len(PAPER_SEARCH_QUERIES)}] Processing: {title}")
        
        # Try to find and download PDFs from alternative sources
        pdf_found = False
        for source_url in alt_sources:
            LOGGER.info(f"  Checking: {source_url}")
            
            # Look for PDF links on the page
            pdf_links = find_pdf_links(source_url)
            for pdf_url in pdf_links[:3]:  # Try first 3 PDFs found
                safe_title = title.replace('/', '_').replace('\\', '_')[:100]
                pdf_path = downloads_dir / f"{i:02d}_{safe_title}.pdf"
                
                if pdf_path.exists():
                    LOGGER.info(f"  PDF already exists: {pdf_path}")
                    pdf_found = True
                    break
                
                LOGGER.info(f"  Attempting to download: {pdf_url}")
                if download_pdf(pdf_url, pdf_path):
                    pdf_found = True
                    break
            
            if pdf_found:
                break
            
            # If no PDF links, try extracting text content
            LOGGER.info(f"  No PDF found, extracting text content...")
            text = extract_text_from_html(source_url)
            if text and len(text) > 1000:
                txt_path = downloads_dir / f"{i:02d}_{safe_title}.txt"
                if save_text_content(text, txt_path, {
                    "title": title,
                    "authors": authors,
                    "url": source_url
                }):
                    # Ingest the text file
                    try:
                        result = kb_manager.add_document(str(txt_path), metadata={
                            "title": title,
                            "authors": authors,
                            "url": source_url,
                            "source": "nitrous_tuning_papers",
                            "topic": "Nitrous Tuning",
                            "category": "Academic Paper",
                            "extracted_from": "web_scraping"
                        })
                        if result.get("success"):
                            ingested_count += 1
                            LOGGER.info(f"  ✓ Ingested text content ({result.get('chunks_added', 0)} chunks)")
                    except Exception as e:
                        LOGGER.error(f"  ✗ Failed to ingest: {e}")
                break
        
        if not pdf_found:
            LOGGER.warning(f"  Could not find PDF or extract content for: {title}")
    
    # Try to ingest any PDFs that were downloaded
    LOGGER.info("\n" + "="*70)
    LOGGER.info("Ingesting downloaded PDFs...")
    LOGGER.info("="*70)
    
    for pdf_file in downloads_dir.glob("*.pdf"):
        try:
            LOGGER.info(f"Processing: {pdf_file.name}")
            result = kb_manager.add_document(str(pdf_file), metadata={
                "source": "nitrous_tuning_papers",
                "topic": "Nitrous Tuning",
                "category": "Academic Paper"
            })
            if result.get("success"):
                ingested_count += 1
                LOGGER.info(f"  ✓ Ingested {result.get('chunks_added', 0)} chunks")
            else:
                LOGGER.warning(f"  ✗ Failed: {result.get('errors', [])}")
        except Exception as e:
            LOGGER.error(f"  ✗ Error: {e}")
    
    LOGGER.info(f"\n✓ Total ingested: {ingested_count} papers/documents")


if __name__ == "__main__":
    main()

