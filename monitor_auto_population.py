#!/usr/bin/env python3
"""
Monitor Auto-Population Process

Tests and monitors the auto-population system to ensure it's working correctly.
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auto_population_monitor.log', encoding='utf-8')
    ]
)

LOGGER = logging.getLogger(__name__)

print("="*80)
print("AUTO-POPULATION MONITOR")
print("="*80)
print()

def check_component(name, component, required=True):
    """Check if a component is available."""
    status = "✓" if component else "✗"
    print(f"{status} {name}: {'Available' if component else 'NOT AVAILABLE'}")
    if required and not component:
        print(f"  ⚠ WARNING: {name} is required!")
    return component is not None

# Step 1: Check all dependencies
print("[1] Checking dependencies...")
try:
    from services.web_search_service import WebSearchService
    from services.knowledge_base_manager import KnowledgeBaseManager
    from services.vector_knowledge_store import VectorKnowledgeStore
    from services.auto_knowledge_populator import AutoKnowledgePopulator
    from services.ai_advisor_learning_system import AILearningSystem
    from services.website_ingestion_service import WebsiteIngestionService
    from services.website_list_manager import WebsiteListManager
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    print("  ✓ All imports successful")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Initialize components
print("\n[2] Initializing components...")

# Vector store
print("  Initializing vector store...", end=" ", flush=True)
try:
    vector_store = VectorKnowledgeStore()
    print("✓")
    vector_store_ok = True
except Exception as e:
    print(f"✗ {e}")
    vector_store_ok = False
    import traceback
    traceback.print_exc()

# Knowledge base manager
print("  Initializing knowledge base manager...", end=" ", flush=True)
try:
    kb_manager = KnowledgeBaseManager(vector_store=vector_store) if vector_store_ok else None
    print("✓")
    kb_manager_ok = kb_manager is not None
except Exception as e:
    print(f"✗ {e}")
    kb_manager_ok = False
    import traceback
    traceback.print_exc()

# Web search service
print("  Initializing web search service...", end=" ", flush=True)
try:
    web_search = WebSearchService(enable_search=True, prefer_google=True)
    web_search_available = web_search.is_available()
    print(f"{'✓' if web_search_available else '⚠'} ({'Available' if web_search_available else 'Not Available'})")
except Exception as e:
    print(f"✗ {e}")
    web_search = None
    web_search_available = False

# Learning system
print("  Initializing learning system...", end=" ", flush=True)
try:
    learning_system = AILearningSystem(vector_store=vector_store, enable_auto_learning=True) if vector_store_ok else None
    print("✓")
    learning_system_ok = learning_system is not None
except Exception as e:
    print(f"✗ {e}")
    learning_system_ok = False
    learning_system = None

# KB file manager
print("  Initializing KB file manager...", end=" ", flush=True)
try:
    kb_file_manager = KnowledgeBaseFileManager(auto_save=True)
    print("✓")
    kb_file_manager_ok = True
except Exception as e:
    print(f"⚠ {e}")
    kb_file_manager_ok = False
    kb_file_manager = None

# Website list manager (not needed but check)
print("  Checking website list manager...", end=" ", flush=True)
try:
    website_list_manager = WebsiteListManager()
    website_count = len(website_list_manager.websites)
    print(f"✓ ({website_count} websites)")
except Exception as e:
    print(f"⚠ {e}")
    website_list_manager = None

# Website ingestion service (not needed but check)
website_ingestion_service = None
if website_list_manager and kb_manager_ok:
    try:
        from services.website_ingestion_service import WebsiteIngestionService
        website_ingestion_service = WebsiteIngestionService(
            website_list_manager=website_list_manager,
            knowledge_base_manager=kb_manager
        )
    except Exception as e:
        LOGGER.debug(f"Website ingestion service not available: {e}")

# Step 3: Initialize auto-populator
print("\n[3] Initializing auto-populator...")
try:
    auto_populator = AutoKnowledgePopulator(
        learning_system=learning_system if learning_system_ok else None,
        website_ingestion_service=website_ingestion_service,
        knowledge_base_manager=kb_manager if kb_manager_ok else None,
        web_search_service=web_search if web_search_available else None,
        kb_file_manager=kb_file_manager if kb_file_manager_ok else None,
        auto_populate_enabled=True,
        confidence_threshold=0.5,
        min_gap_frequency=1
    )
    print("  ✓ Auto-populator initialized")
except Exception as e:
    print(f"  ✗ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test web search
print("\n[4] Testing web search...")
test_query = "What is ECU tuning?"
print(f"  Query: {test_query}")
if web_search_available:
    try:
        start = time.time()
        search_results = web_search.search(test_query, max_results=3)
        elapsed = time.time() - start
        
        if search_results and search_results.results:
            print(f"  ✓ Search successful ({elapsed:.2f}s)")
            print(f"  - Results: {len(search_results.results)}")
            for i, result in enumerate(search_results.results[:3], 1):
                print(f"    {i}. {result.title[:60]}...")
                print(f"       URL: {result.url[:60]}...")
        else:
            print(f"  ✗ Search returned no results")
    except Exception as e:
        print(f"  ✗ Search failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⚠ Web search not available - skipping test")

# Step 5: Test knowledge addition
print("\n[5] Testing knowledge addition to vector store...")
if kb_manager_ok and vector_store_ok:
    test_text = "ECU tuning is the process of modifying the engine control unit parameters to optimize performance."
    test_metadata = {
        "source": "test",
        "topic": "ECU Tuning",
        "auto_populated": True
    }
    
    try:
        print(f"  Adding test knowledge...", end=" ", flush=True)
        doc_id = vector_store.add_knowledge(
            text=test_text,
            metadata=test_metadata
        )
        print("✓")
        print(f"  - Document ID: {doc_id}")
        
        # Verify it was added
        print("  Verifying addition...", end=" ", flush=True)
        search_results = vector_store.search("ECU tuning", n_results=1)
        if search_results and len(search_results) > 0:
            print("✓")
            print(f"  - Found: {search_results[0].get('text', '')[:60]}...")
        else:
            print("⚠ (Not found in search, but may still be added)")
    except Exception as e:
        print(f"✗ {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⚠ Knowledge base manager or vector store not available")

# Step 6: Test auto-population
print("\n[6] Testing auto-population...")
test_question = "What is a fuel map?"
test_confidence = 0.3  # Low confidence to trigger auto-population
test_answer = "A fuel map is a table that defines fuel delivery based on engine load and RPM."

print(f"  Question: {test_question}")
print(f"  Confidence: {test_confidence} (low - should trigger auto-population)")
print(f"  Starting auto-population...")

try:
    start = time.time()
    result = auto_populator.check_and_populate(
        question=test_question,
        confidence=test_confidence,
        answer=test_answer
    )
    elapsed = time.time() - start
    
    print(f"\n  Result ({elapsed:.2f}s):")
    print(f"  - Success: {result.get('success', False)}")
    print(f"  - Chunks added: {result.get('chunks_added', 0)}")
    print(f"  - Sources tried: {result.get('sources_tried', [])}")
    
    if result.get('errors'):
        print(f"  - Errors ({len(result['errors'])}):")
        for error in result['errors'][:3]:  # Show first 3 errors
            print(f"    • {error}")
    
    if result.get('success'):
        print("\n  ✓ Auto-population SUCCESSFUL!")
        
        # Verify knowledge was added
        if vector_store_ok:
            print("  Verifying knowledge was added...", end=" ", flush=True)
            search_results = vector_store.search("fuel map", n_results=3)
            if search_results:
                print(f"✓ (Found {len(search_results)} results)")
            else:
                print("⚠ (No results found)")
    else:
        print("\n  ✗ Auto-population FAILED")
        print("  Checking why...")
        
        # Diagnose
        if not web_search_available:
            print("    • Web search is not available")
        if not kb_manager_ok:
            print("    • Knowledge base manager is not working")
        if not vector_store_ok:
            print("    • Vector store is not working")
        if result.get('chunks_added', 0) == 0:
            print("    • No chunks were added (check errors above)")
            
except Exception as e:
    print(f"  ✗ Auto-population test failed: {e}")
    import traceback
    traceback.print_exc()

# Step 7: Check vector store count
print("\n[7] Checking vector store status...")
if vector_store_ok:
    try:
        if hasattr(vector_store, 'collection') and vector_store.collection:
            count = vector_store.collection.count()
            print(f"  Total knowledge entries: {count}")
        else:
            print("  Vector store type: TF-IDF (in-memory)")
            print("  Note: TF-IDF doesn't persist, entries are in-memory only")
    except Exception as e:
        print(f"  ⚠ Could not get count: {e}")

# Summary
print("\n" + "="*80)
print("MONITORING SUMMARY")
print("="*80)
print(f"Web Search: {'✓ Available' if web_search_available else '✗ Not Available'}")
print(f"Vector Store: {'✓ Working' if vector_store_ok else '✗ Not Working'}")
print(f"KB Manager: {'✓ Working' if kb_manager_ok else '✗ Not Working'}")
print(f"Learning System: {'✓ Working' if learning_system_ok else '✗ Not Working'}")
print(f"KB File Manager: {'✓ Working' if kb_file_manager_ok else '⚠ Not Working'}")
print(f"Auto-Populator: {'✓ Initialized' if auto_populator else '✗ Failed'}")
print("\nCheck 'auto_population_monitor.log' for detailed logs.")
print("="*80)

