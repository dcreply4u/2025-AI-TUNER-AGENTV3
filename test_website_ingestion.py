#!/usr/bin/env python3
"""
Test Website Ingestion and Search
Tests that websites are ingested and searchable.
"""

from services.website_list_manager import WebsiteListManager
from services.website_ingestion_service import WebsiteIngestionService
from services.ai_advisor_rag import RAGAIAdvisor
from services.vector_knowledge_store import VectorKnowledgeStore

def test_website_list():
    """Test website list manager."""
    print("=" * 70)
    print("Testing Website List Manager")
    print("=" * 70)
    
    manager = WebsiteListManager()
    
    # Show current websites
    print("\n1. Current Websites:")
    websites = manager.get_websites()
    for i, site in enumerate(websites, 1):
        print(f"   {i}. {site.name}")
        print(f"      URL: {site.url}")
        print(f"      Category: {site.category}")
        print(f"      Enabled: {site.enabled}")
        print(f"      Chunks: {site.chunks_added}")
        print()
    
    # Show stats
    print("2. Website List Statistics:")
    stats = manager.get_stats()
    print(f"   Total websites: {stats['total_websites']}")
    print(f"   Enabled: {stats['enabled_websites']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Total chunks: {stats['total_chunks_added']}")
    print(f"   Ingested: {stats['websites_ingested']}")
    
    return manager


def test_ingestion():
    """Test website ingestion."""
    print("\n" + "=" * 70)
    print("Testing Website Ingestion")
    print("=" * 70)
    
    service = WebsiteIngestionService()
    
    # Get initial knowledge base count
    vector_store = VectorKnowledgeStore()
    initial_count = vector_store.count()
    print(f"\nInitial knowledge base entries: {initial_count}")
    
    # Ingest one website as test
    print("\nIngesting first enabled website...")
    websites = service.website_list_manager.get_websites(enabled_only=True)
    if websites:
        test_url = websites[0].url
        print(f"Testing with: {websites[0].name}")
        result = service.ingest_website(test_url)
        
        if result.get("success"):
            chunks = result.get("chunks_added", 0)
            print(f"✓ Success! Added {chunks} chunks")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    
    # Check updated count
    updated_count = vector_store.count()
    print(f"\nUpdated knowledge base entries: {updated_count}")
    print(f"New entries: {updated_count - initial_count}")
    
    return service


def test_search():
    """Test that ingested content is searchable."""
    print("\n" + "=" * 70)
    print("Testing Search Functionality")
    print("=" * 70)
    
    advisor = RAGAIAdvisor()
    
    # Test queries that should find content from forums
    test_queries = [
        "tuning",
        "fuel pressure",
        "boost control",
        "ECU tuning",
        "ignition timing"
    ]
    
    print("\nTesting search queries:")
    print("-" * 70)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        response = advisor.answer(query)
        
        print(f"   Answer: {response.answer[:150]}...")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Sources: {len(response.sources)}")
        
        if response.sources:
            print("   Source topics:")
            for source in response.sources[:3]:
                topic = source.get("metadata", {}).get("topic", "Unknown")
                name = source.get("metadata", {}).get("name", "Unknown")
                print(f"     - {name or topic}")
    
    print("\n" + "=" * 70)
    print("Search Test Complete")
    print("=" * 70)


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Website Ingestion and Search Test Suite")
    print("=" * 70)
    
    try:
        # Test 1: Website list
        manager = test_website_list()
        
        # Test 2: Ingestion (optional - comment out if you don't want to ingest now)
        print("\n" + "=" * 70)
        print("NOTE: Website ingestion will scrape websites and may take time.")
        print("Uncomment the ingestion test below to actually ingest websites.")
        print("=" * 70)
        
        # Uncomment to actually ingest:
        # service = test_ingestion()
        
        # Test 3: Search
        test_search()
        
        print("\n✅ All tests complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

