"""
Test script to validate RAG AI Advisor functionality
Tests various queries to ensure correct responses
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_advisor():
    """Test RAG advisor with various queries."""
    print("=" * 70)
    print("RAG AI Advisor Validation Test")
    print("=" * 70)
    print()
    
    # Test 1: Check if RAG advisor can be imported
    print("Test 1: Importing RAG advisor...")
    try:
        from services.ai_advisor_rag import RAGAIAdvisor, RAGResponse
        from services.vector_knowledge_store import VectorKnowledgeStore
        print("✅ RAG advisor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import RAG advisor: {e}")
        print("   Dependencies may be missing. Install: pip install chromadb sentence-transformers ollama")
        return False
    
    # Test 2: Initialize vector store
    print("\nTest 2: Initializing vector knowledge store...")
    try:
        vector_store = VectorKnowledgeStore()
        count = vector_store.count()
        print(f"✅ Vector store initialized (contains {count} entries)")
        
        if count == 0:
            print("   ⚠️  Vector store is empty - migrating knowledge...")
            try:
                from services.migrate_knowledge_to_rag import migrate_from_enhanced_advisor
                migrated = migrate_from_enhanced_advisor(vector_store)
                print(f"   ✅ Migrated {migrated} knowledge entries")
                count = vector_store.count()
            except Exception as e:
                print(f"   ❌ Migration failed: {e}")
                return False
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return False
    
    # Test 3: Initialize RAG advisor
    print("\nTest 3: Initializing RAG advisor...")
    try:
        advisor = RAGAIAdvisor(
            use_local_llm=False,  # Don't require Ollama for basic testing
            enable_web_search=False,  # Disable web search for testing
            vector_store=vector_store
        )
        print("✅ RAG advisor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize RAG advisor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test queries
    print("\nTest 4: Testing queries...")
    print("-" * 70)
    
    test_queries = [
        ("what is spark", "Should return information about spark/ignition, not knock prevention"),
        ("what is fuel pressure", "Should return information about fuel pressure, not ECU tuning"),
        ("what is boost", "Should return information about boost/turbo"),
        ("how do I tune ignition timing", "Should return tuning advice for ignition timing"),
        ("what causes knock", "Should return information about knock/detonation"),
    ]
    
    results = []
    for question, expected in test_queries:
        print(f"\nQuery: '{question}'")
        print(f"Expected: {expected}")
        
        try:
            response = advisor.answer(question)
            
            if isinstance(response, RAGResponse):
                answer = response.answer
                confidence = response.confidence
                sources_count = len(response.sources)
                
                print(f"Answer: {answer[:200]}...")
                print(f"Confidence: {confidence:.2f}")
                print(f"Sources: {sources_count}")
                
                # Validate response
                answer_lower = answer.lower()
                question_lower = question.lower()
                
                # Check if answer is relevant
                if "what is spark" in question_lower:
                    is_relevant = (
                        "spark" in answer_lower or 
                        "ignition" in answer_lower
                    ) and "knock prevention" not in answer_lower[:100]
                    status = "✅" if is_relevant else "❌"
                    print(f"{status} Relevance check: {'PASS' if is_relevant else 'FAIL'}")
                    results.append(("spark", is_relevant))
                
                elif "what is fuel pressure" in question_lower:
                    is_relevant = (
                        "fuel pressure" in answer_lower or 
                        "pressure" in answer_lower
                    ) and "ecu tuning" not in answer_lower[:100]
                    status = "✅" if is_relevant else "❌"
                    print(f"{status} Relevance check: {'PASS' if is_relevant else 'FAIL'}")
                    results.append(("fuel pressure", is_relevant))
                
                elif "what is boost" in question_lower:
                    is_relevant = "boost" in answer_lower or "turbo" in answer_lower
                    status = "✅" if is_relevant else "❌"
                    print(f"{status} Relevance check: {'PASS' if is_relevant else 'FAIL'}")
                    results.append(("boost", is_relevant))
                
                else:
                    # Generic check - answer should not be empty
                    is_relevant = len(answer) > 50
                    status = "✅" if is_relevant else "❌"
                    print(f"{status} Relevance check: {'PASS' if is_relevant else 'FAIL'}")
                    results.append((question[:20], is_relevant))
                
            else:
                print(f"❌ Unexpected response type: {type(response)}")
                results.append((question[:20], False))
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((question[:20], False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for query, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {query}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! RAG advisor is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the results above.")
        return False


if __name__ == "__main__":
    success = test_rag_advisor()
    sys.exit(0 if success else 1)


