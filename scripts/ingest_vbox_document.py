#!/usr/bin/env python3
"""
Ingest VBOX 3i User Guide PDF into Vector Knowledge Store
Extracts text from PDF and chunks it for semantic search.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vector_knowledge_store import VectorKnowledgeStore

LOGGER = logging.getLogger(__name__)

# Try to import PDF libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    LOGGER.warning("PyPDF2 not available - install with: pip install PyPDF2")


def extract_pdf_text(pdf_path: str) -> list[str]:
    """
    Extract text from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of page texts
    """
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 not available")
    
    pages = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    pages.append(text)
                    LOGGER.debug(f"Extracted page {page_num + 1}: {len(text)} characters")
    except Exception as e:
        LOGGER.error(f"Failed to extract PDF text: {e}")
        raise
    
    return pages


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Chunk text into smaller pieces for better semantic search.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, max(start, end - 200), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def determine_topic(text: str) -> str:
    """
    Determine topic/category from text content.
    
    Args:
        text: Text to analyze
        
    Returns:
        Topic string
    """
    text_lower = text.lower()
    
    # GPS/GNSS topics
    if any(keyword in text_lower for keyword in ['gps', 'gnss', 'satellite', 'antenna', 'rtk', 'dgps']):
        if 'dual antenna' in text_lower or 'dual antenna' in text_lower:
            return "GPS - Dual Antenna"
        elif 'rtk' in text_lower:
            return "GPS - RTK/DGPS"
        else:
            return "GPS - General"
    
    # IMU topics
    if any(keyword in text_lower for keyword in ['imu', 'kalman', 'filter', 'accelerometer', 'gyroscope']):
        if 'kalman' in text_lower or 'filter' in text_lower:
            return "IMU - Kalman Filter"
        elif 'calibration' in text_lower:
            return "IMU - Calibration"
        else:
            return "IMU - General"
    
    # ADAS topics
    if any(keyword in text_lower for keyword in ['adas', 'target', 'static point', 'lane departure']):
        return "ADAS"
    
    # CAN topics
    if any(keyword in text_lower for keyword in ['can', 'can bus', 'vehicle can', 'vci']):
        return "CAN Bus"
    
    # Logging topics
    if any(keyword in text_lower for keyword in ['logging', 'log rate', 'sample rate', 'channels']):
        return "Logging"
    
    # Setup/Configuration topics
    if any(keyword in text_lower for keyword in ['setup', 'configuration', 'menu', 'settings']):
        return "Setup/Configuration"
    
    # Hardware topics
    if any(keyword in text_lower for keyword in ['connector', 'pinout', 'led', 'button', 'power']):
        return "Hardware"
    
    return "General"


def ingest_vbox_document(pdf_path: str, vector_store: VectorKnowledgeStore) -> int:
    """
    Ingest VBOX 3i document into vector knowledge store.
    
    Args:
        pdf_path: Path to VBOX 3i PDF document
        vector_store: Vector knowledge store instance
        
    Returns:
        Number of chunks ingested
    """
    LOGGER.info(f"Ingesting VBOX 3i document: {pdf_path}")
    
    # Extract text from PDF
    pages = extract_pdf_text(pdf_path)
    LOGGER.info(f"Extracted {len(pages)} pages from PDF")
    
    # Chunk and ingest
    total_chunks = 0
    
    for page_num, page_text in enumerate(pages):
        # Chunk the page
        chunks = chunk_text(page_text)
        
        for chunk_num, chunk in enumerate(chunks):
            # Determine topic
            topic = determine_topic(chunk)
            
            # Create metadata
            metadata = {
                "source": "VBOX 3i Dual Antenna (v5) User Guide v2.8",
                "page": page_num + 1,
                "chunk": chunk_num + 1,
                "topic": topic,
                "document_type": "user_guide",
            }
            
            # Add to vector store
            try:
                vector_store.add_knowledge(
                    text=chunk,
                    metadata=metadata,
                )
                total_chunks += 1
                
                if total_chunks % 10 == 0:
                    LOGGER.info(f"Ingested {total_chunks} chunks...")
            except Exception as e:
                LOGGER.error(f"Failed to ingest chunk {chunk_num} from page {page_num + 1}: {e}")
    
    LOGGER.info(f"Successfully ingested {total_chunks} chunks from VBOX 3i document")
    return total_chunks


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest VBOX 3i User Guide PDF into knowledge base")
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to VBOX 3i User Guide PDF file"
    )
    parser.add_argument(
        "--store-dir",
        type=str,
        default=None,
        help="Directory for vector store persistence (default: ~/.aituner/vector_db)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        LOGGER.error(f"PDF file not found: {pdf_path}")
        return 1
    
    # Initialize vector store
    try:
        vector_store = VectorKnowledgeStore(
            persist_directory=args.store_dir,
            collection_name="vbox3i_knowledge",
        )
        LOGGER.info("Vector knowledge store initialized")
    except Exception as e:
        LOGGER.error(f"Failed to initialize vector store: {e}")
        return 1
    
    # Ingest document
    try:
        count = ingest_vbox_document(str(pdf_path), vector_store)
        LOGGER.info(f"✅ Successfully ingested {count} chunks into knowledge base")
        LOGGER.info(f"Total documents in store: {vector_store.count()}")
        return 0
    except Exception as e:
        LOGGER.error(f"Failed to ingest document: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
