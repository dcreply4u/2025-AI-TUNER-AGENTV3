#!/usr/bin/env python3
"""
Test script for Knowledge Base Manager
Tests document ingestion, web scraping, and forum search.
"""

from services.knowledge_base_manager import KnowledgeBaseManager
from services.vector_knowledge_store import VectorKnowledgeStore

def test_knowledge_base():
    """Test knowledge base manager."""
    print("Testing Knowledge Base Manager")
    print("=" * 60)
    
    # Initialize
    vector_store = VectorKnowledgeStore()
    manager = KnowledgeBaseManager(vector_store)
    
    # Get initial stats
    print("\n1. Initial Knowledge Base Stats:")
    stats = manager.get_stats()
    print(f"   Total entries: {stats.get('total_entries', 0)}")
    
    # Test adding a website
    print("\n2. Testing website scraping...")
    result = manager.add_website(
        "https://en.wikipedia.org/wiki/Engine_control_unit",
        metadata={"topic": "ECU", "source_type": "wikipedia"}
    )
    print(f"   Success: {result.get('success')}")
    print(f"   Chunks added: {result.get('chunks_added', 0)}")
    if result.get('errors'):
        print(f"   Errors: {result.get('errors')}")
    
    # Test forum search (example - may need real forum URL)
    print("\n3. Testing forum search...")
    print("   (Skipping - requires specific forum URL)")
    
    # Get updated stats
    print("\n4. Updated Knowledge Base Stats:")
    stats = manager.get_stats()
    print(f"   Total entries: {stats.get('total_entries', 0)}")
    
    print("\n" + "=" * 60)
    print("✅ Knowledge Base Manager test complete!")

if __name__ == "__main__":
    test_knowledge_base()

