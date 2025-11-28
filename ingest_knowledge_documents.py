#!/usr/bin/env python3
"""
Knowledge Document Ingestion System

Downloads and ingests useful documents from the internet into the knowledge base.
Focuses on: dyno manuals, EFI tuning guides, Holley EFI, nitrous, turbo tuning.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("KNOWLEDGE DOCUMENT INGESTION SYSTEM")
print("="*80)
print()

try:
    from services.web_search_service import WebSearchService
    from services.vector_knowledge_store import VectorKnowledgeStore
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    
    # Try to import KnowledgeBaseManager if it exists
    try:
        from services.knowledge_base_manager import KnowledgeBaseManager
        kb_manager_available = True
    except ImportError:
        kb_manager_available = False
        print("⚠ KnowledgeBaseManager not available, will use VectorKnowledgeStore directly")
    
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    print("  This script requires web_search_service, vector_knowledge_store, and knowledge_base_file_manager")
    sys.exit(1)

# Document sources to search for
document_sources = [
    # Dyno manuals and guides
    {"query": "dyno manual PDF tuning", "category": "Dyno", "max_results": 5},
    {"query": "dynamometer calculation formulas", "category": "Dyno", "max_results": 5},
    {"query": "SAE dyno correction factor formula", "category": "Dyno", "max_results": 3},
    {"query": "virtual dyno calculation horsepower", "category": "Dyno", "max_results": 5},
    {"query": "chassis dyno vs engine dyno", "category": "Dyno", "max_results": 3},
    
    # EFI tuning
    {"query": "EFI tuning guide PDF", "category": "EFI Tuning", "max_results": 5},
    {"query": "electronic fuel injection tuning manual", "category": "EFI Tuning", "max_results": 5},
    {"query": "EFI fuel map tuning guide", "category": "EFI Tuning", "max_results": 3},
    {"query": "EFI sensor calibration guide", "category": "EFI Tuning", "max_results": 3},
    
    # Holley EFI
    {"query": "Holley EFI tuning manual PDF", "category": "Holley EFI", "max_results": 5},
    {"query": "Holley EFI software guide", "category": "Holley EFI", "max_results": 3},
    {"query": "Holley EFI calibration guide", "category": "Holley EFI", "max_results": 3},
    {"query": "Holley EFI Learn feature", "category": "Holley EFI", "max_results": 3},
    
    # Nitrous tuning
    {"query": "nitrous oxide tuning guide PDF", "category": "Nitrous", "max_results": 5},
    {"query": "nitrous system installation tuning", "category": "Nitrous", "max_results": 3},
    {"query": "progressive nitrous control tuning", "category": "Nitrous", "max_results": 3},
    
    # Turbo tuning
    {"query": "turbocharger tuning guide PDF", "category": "Turbo", "max_results": 5},
    {"query": "turbo boost control tuning", "category": "Turbo", "max_results": 3},
    {"query": "turbo sizing calculation guide", "category": "Turbo", "max_results": 3},
    {"query": "turbo compressor map reading", "category": "Turbo", "max_results": 3},
]

def ingest_documents():
    """Ingest documents from web search into knowledge base."""
    print("Initializing services...")
    
    # Initialize services
    vector_store = VectorKnowledgeStore()
    if kb_manager_available:
        kb_manager = KnowledgeBaseManager(vector_store=vector_store)
    kb_file_manager = KnowledgeBaseFileManager(auto_save=True)
    web_search = WebSearchService(enable_search=True, prefer_google=True)
    
    if not web_search.is_available():
        print("⚠ Web search not available - cannot ingest documents")
        return
    
    print("✓ Services initialized")
    print(f"  - Vector Store: {type(vector_store).__name__}")
    print(f"  - Web Search: Available")
    print()
    
    total_chunks = 0
    
    for i, source in enumerate(document_sources, 1):
        print(f"[{i}/{len(document_sources)}] Searching: {source['query']}")
        print(f"  Category: {source['category']}")
        
        try:
            # Search for documents
            search_results = web_search.search(source['query'], max_results=source['max_results'])
            
            if search_results and search_results.results:
                print(f"  ✓ Found {len(search_results.results)} results")
                
                chunks_added = 0
                for result in search_results.results:
                    try:
                        # Create knowledge entry
                        knowledge_text = f"{result.title}\n\n{result.snippet}\n\nSource: {result.url}"
                        
                        # Add to vector store
                        doc_id = vector_store.add_knowledge(
                            text=knowledge_text,
                            metadata={
                                "source": "web_search",
                                "url": result.url,
                                "category": source['category'],
                                "query": source['query'],
                                "auto_populated": True,
                                "document_type": "guide"
                            }
                        )
                        
                        # Add to KB file manager
                        kb_file_manager.add_entry(
                            question=f"Information about {source['category']}",
                            answer=knowledge_text,
                            source="web_search",
                            url=result.url,
                            title=result.title,
                            confidence=0.7,
                            topic=source['category'],
                            keywords=source['query'].split(),
                            verified=False
                        )
                        
                        chunks_added += 1
                        total_chunks += 1
                        print(f"    ➕ Added: {result.title[:60]}...")
                        
                    except Exception as e:
                        print(f"    ✗ Failed to add: {e}")
                
                print(f"  ✓ Added {chunks_added} chunks from this search")
            else:
                print(f"  ⚠ No results found")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Search failed: {e}")
        
        print()
    
    print("="*80)
    print(f"INGESTION COMPLETE")
    print(f"Total chunks added: {total_chunks}")
    print("="*80)

if __name__ == "__main__":
    ingest_documents()

