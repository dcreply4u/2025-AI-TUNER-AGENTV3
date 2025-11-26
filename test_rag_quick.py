"""
Quick RAG Advisor Test - Fast validation without heavy dependencies
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def quick_test():
    """Quick test of RAG advisor components."""
    print("Quick RAG Advisor Validation")
    print("=" * 50)
    
    # Test 1: Can we import?
    print("\n1. Testing imports...")
    try:
        from services.ai_advisor_rag import RAGAIAdvisor
        print("   ✅ RAG advisor imports OK")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    try:
        from services.vector_knowledge_store import VectorKnowledgeStore
        print("   ✅ Vector store imports OK")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Can we create vector store?
    print("\n2. Testing vector store creation...")
    try:
        vector_store = VectorKnowledgeStore()
        print(f"   ✅ Vector store created (has {vector_store.count()} entries)")
    except Exception as e:
        print(f"   ❌ Vector store creation failed: {e}")
        return False
    
    # Test 3: Can we search?
    print("\n3. Testing search functionality...")
    try:
        # Add a test entry
        vector_store.add_knowledge(
            text="Spark is the electrical discharge that ignites the air-fuel mixture in an engine. It is created by the spark plug.",
            metadata={"topic": "Spark", "category": "technical"}
        )
        
        # Search for it
        results = vector_store.search("what is spark", n_results=3)
        print(f"   ✅ Search works (found {len(results)} results)")
        
        if results:
            print(f"   Top result similarity: {results[0].get('similarity', 0):.2f}")
            print(f"   Top result topic: {results[0].get('metadata', {}).get('topic', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Can we create advisor?
    print("\n4. Testing advisor creation...")
    try:
        advisor = RAGAIAdvisor(
            use_local_llm=False,  # Skip LLM for quick test
            enable_web_search=False,
            vector_store=vector_store
        )
        print("   ✅ Advisor created")
    except Exception as e:
        print(f"   ❌ Advisor creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Can we get an answer?
    print("\n5. Testing answer generation...")
    try:
        response = advisor.answer("what is spark")
        if hasattr(response, 'answer'):
            answer = response.answer
            print(f"   ✅ Got answer ({len(answer)} chars)")
            print(f"   Answer preview: {answer[:150]}...")
            print(f"   Confidence: {response.confidence:.2f}")
            
            # Check if it's relevant
            if "spark" in answer.lower() or "ignition" in answer.lower():
                print("   ✅ Answer is relevant to 'spark'")
                return True
            else:
                print("   ⚠️  Answer may not be relevant")
                return False
        else:
            print(f"   ❌ Unexpected response type: {type(response)}")
            return False
    except Exception as e:
        print(f"   ❌ Answer generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    print("\n" + "=" * 50)
    if success:
        print("✅ Quick test PASSED")
    else:
        print("❌ Quick test FAILED")
    sys.exit(0 if success else 1)


