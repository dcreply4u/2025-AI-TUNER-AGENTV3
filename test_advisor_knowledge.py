#!/usr/bin/env python3
"""
Test AI Advisor Knowledge
Tests if the advisor can answer questions that should be in forum websites.
"""

from services.ai_advisor_rag import RAGAIAdvisor
from services.vector_knowledge_store import VectorKnowledgeStore

def test_advisor_knowledge():
    """Test advisor with forum-related questions."""
    print("=" * 70)
    print("Testing AI Advisor Knowledge")
    print("=" * 70)
    
    # Check knowledge base size
    vs = VectorKnowledgeStore()
    kb_count = vs.count()
    print(f"\nKnowledge Base Entries: {kb_count}")
    
    if kb_count < 20:
        print("\n⚠️  WARNING: Knowledge base is small. Websites may not be ingested yet.")
        print("   Run: python3 manage_websites.py ingest")
    
    # Initialize advisor
    print("\nInitializing RAG Advisor...")
    advisor = RAGAIAdvisor()
    
    # Test questions that should be answerable from forums
    test_questions = [
        "how do I tune fuel pressure for a turbocharged engine",
        "what is the best way to adjust boost control",
        "how to tune ignition timing for performance",
        "what causes engine knock and how to prevent it",
        "how do I tune AFR for maximum power"
    ]
    
    print("\n" + "=" * 70)
    print("Testing Questions")
    print("=" * 70 + "\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"Question {i}: {question}")
        print("-" * 70)
        
        response = advisor.answer(question)
        
        print(f"Answer: {response.answer[:300]}...")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Sources: {len(response.sources)}")
        print(f"Used Web Search: {response.used_web_search}")
        
        if response.sources:
            print("Source info:")
            for j, source in enumerate(response.sources[:2], 1):
                metadata = source.get("metadata", {})
                name = metadata.get("name", "Unknown")
                url = metadata.get("url", "Unknown")
                category = metadata.get("category", "Unknown")
                print(f"  {j}. {name} ({category})")
                if url != "Unknown":
                    print(f"     URL: {url[:60]}...")
        
        print()
    
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    test_advisor_knowledge()

