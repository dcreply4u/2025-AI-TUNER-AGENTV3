#!/usr/bin/env python3
"""
Download and add methanol tuning paper to the AI Chat Advisor knowledge base.
Source: Cal Poly Digital Commons
"""

import logging
import sys
import requests
from pathlib import Path
import tempfile
import os

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

PAPER_URL = "https://digitalcommons.calpoly.edu/cgi/viewcontent.cgi?httpsredir=1&article=1345&context=eeng_fac"
PAPER_TITLE = "Methanol Fuel Tuning and Engine Performance"
PAPER_TOPIC = "Methanol Fuel Tuning"


def download_pdf(url: str, output_path: Path) -> bool:
    """Download PDF from URL."""
    try:
        LOGGER.info(f"Downloading PDF from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
            # Check first bytes for PDF magic number
            first_bytes = response.content[:4]
            if first_bytes != b'%PDF':
                LOGGER.warning("Response doesn't appear to be a PDF, but continuing...")
        
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
                            text_content.append(f"--- Page {page_num + 1} ---\n{text}")
                    except Exception as e:
                        LOGGER.warning(f"Failed to extract text from page {page_num + 1}: {e}")
            return "\n\n".join(text_content)
        except ImportError:
            LOGGER.warning("PyPDF2 not available, trying pdfplumber...")
            try:
                import pdfplumber
                LOGGER.info("Extracting text using pdfplumber...")
                text_content = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            text = page.extract_text()
                            if text:
                                text_content.append(f"--- Page {page_num + 1} ---\n{text}")
                        except Exception as e:
                            LOGGER.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                return "\n\n".join(text_content)
            except ImportError:
                LOGGER.error("Neither PyPDF2 nor pdfplumber available. Install one: pip install PyPDF2 or pip install pdfplumber")
                return ""
    except Exception as e:
        LOGGER.error(f"Failed to extract text from PDF: {e}")
        return ""


def split_into_sections(text: str) -> list:
    """Split text into logical sections based on headings."""
    sections = []
    lines = text.split('\n')
    current_section_title = "Introduction"
    current_section_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Detect section headings (all caps, numbered, or specific patterns)
        if (line_stripped and 
            (line_stripped.isupper() and len(line_stripped) > 5 and len(line_stripped) < 100) or
            (line_stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) and len(line_stripped) < 100) or
            (any(keyword in line_stripped.lower() for keyword in ['abstract', 'introduction', 'methodology', 'results', 'conclusion', 'references', 'appendix']) and len(line_stripped) < 100)):
            
            # Save previous section
            if current_section_content:
                sections.append({
                    "title": current_section_title,
                    "content": "\n".join(current_section_content).strip()
                })
            
            # Start new section
            current_section_title = line_stripped
            current_section_content = []
        else:
            current_section_content.append(line)
    
    # Add last section
    if current_section_content:
        sections.append({
            "title": current_section_title,
            "content": "\n".join(current_section_content).strip()
        })
    
    # Filter out very short sections (likely headers/footers)
    sections = [s for s in sections if len(s["content"]) > 100]
    
    return sections


def main():
    """Download paper and add to knowledge base."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    # Create temp directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "methanol_paper.pdf"
        
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
            LOGGER.info(f"Extracted text length: {len(full_text)}")
            return
        
        LOGGER.info(f"Extracted {len(full_text)} characters from PDF")
        
        # Split into sections
        sections = split_into_sections(full_text)
        if not sections:
            # If section splitting failed, use full text as one section
            LOGGER.warning("Section splitting failed, using full text as single entry")
            sections = [{"title": PAPER_TITLE, "content": full_text}]
        
        LOGGER.info(f"Split into {len(sections)} sections")
        
        # Initialize knowledge base
        LOGGER.info("Initializing knowledge base...")
        vector_store = VectorKnowledgeStore()
        kb_file_manager = KnowledgeBaseFileManager()
        
        added_count = 0
        
        # Add each section
        for i, section in enumerate(sections):
            section_title = section["title"]
            section_content = section["content"]
            
            # Skip very short sections or references
            if len(section_content) < 200 or "reference" in section_title.lower():
                continue
            
            question = f"What is {section_title}?" if not section_title.lower().startswith("what is") else section_title
            
            LOGGER.info(f"Adding section {i+1}/{len(sections)}: {section_title[:60]}...")
            try:
                # Add to vector store
                vector_store.add_knowledge(
                    text=f"Title: {section_title}\nContent: {section_content}",
                    metadata={
                        "question": question,
                        "answer": section_content,
                        "source": PAPER_URL,
                        "title": section_title,
                        "topic": PAPER_TOPIC,
                        "keywords": ", ".join(section_title.lower().split() + ["methanol", "fuel", "tuning", "engine performance"]),
                        "document_type": "research_paper"
                    }
                )
                
                # Add to KB file manager
                kb_file_manager.add_entry(
                    question=question,
                    answer=section_content,
                    source=PAPER_URL,
                    title=section_title,
                    topic=PAPER_TOPIC,
                    keywords=section_title.lower().split() + ["methanol", "fuel", "tuning", "engine performance"],
                    verified=True
                )
                
                added_count += 1
                LOGGER.info(f"  Successfully added")
                
            except Exception as e:
                LOGGER.error(f"  Failed to add section '{section_title[:60]}...': {e}")
        
        # Add full paper as comprehensive reference
        LOGGER.info("Adding full paper as comprehensive reference...")
        try:
            full_question = f"Summarize the methanol fuel tuning paper: {PAPER_TITLE}"
            vector_store.add_knowledge(
                text=full_text,
                metadata={
                    "question": full_question,
                    "answer": full_text,
                    "source": PAPER_URL,
                    "title": PAPER_TITLE + " (Full Paper)",
                    "topic": PAPER_TOPIC,
                    "keywords": "methanol, fuel, tuning, engine performance, full paper, complete",
                    "document_type": "research_paper"
                }
            )
            kb_file_manager.add_entry(
                question=full_question,
                answer=full_text,
                source=PAPER_URL,
                title=PAPER_TITLE + " (Full Paper)",
                topic=PAPER_TOPIC,
                keywords=["methanol", "fuel", "tuning", "engine performance", "full paper", "complete"],
                verified=True
            )
            added_count += 1
            LOGGER.info("  Full paper added")
        except Exception as e:
            LOGGER.error(f"  Failed to add full paper: {e}")
        
        LOGGER.info(f"\n{'='*70}")
        LOGGER.info(f"SUMMARY")
        LOGGER.info(f"{'='*70}")
        LOGGER.info(f"Total sections: {len(sections)}")
        LOGGER.info(f"Successfully added: {added_count} entries")
        LOGGER.info(f"\nMethanol fuel tuning paper has been added to the AI Chat Advisor!")
        LOGGER.info(f"Source: {PAPER_URL}")
        LOGGER.info(f"PDF size: {pdf_path.stat().st_size} bytes")
        LOGGER.info(f"Text extracted: {len(full_text)} characters")


if __name__ == "__main__":
    main()

