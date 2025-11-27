"""
Comprehensive Test of AI Advisor Knowledge
Tests the advisor against a comprehensive set of racing/tuning questions.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

LOGGER = logging.getLogger(__name__)

# Test questions covering all major racing/tuning topics
TEST_QUESTIONS = [
    # Engine Tuning Basics
    "What is a VE table?",
    "How do I tune ignition timing?",
    "What causes engine knock?",
    "How do I prevent detonation?",
    "What is the optimal air-fuel ratio for turbocharged engines?",
    
    # Boost Control
    "How does boost control work?",
    "What is the difference between open loop and closed loop boost?",
    "How do I set up wastegate control?",
    
    # Fuel Tuning
    "How do I tune fuel maps?",
    "What is E85 tuning?",
    "How do I tune for flex fuel?",
    "What is methanol injection?",
    
    # Nitrous
    "How do I tune for nitrous oxide?",
    "What is nitrous bottle pressure?",
    "How do I prevent nitrous backfire?",
    
    # Racing Techniques
    "What is launch control?",
    "How do I set up traction control?",
    "What is anti-lag?",
    "How do I optimize my racing line?",
    
    # Calculations
    "How do I calculate wheel slip?",
    "What is the formula for horsepower?",
    "How do I calculate torque?",
    "What is density altitude?",
    
    # Diagnostics
    "My engine is running lean, what should I check?",
    "How do I diagnose knock?",
    "What causes high EGT?",
    "How do I troubleshoot boost issues?",
    
    # Advanced Topics
    "What is camshaft timing?",
    "How do I tune exhaust systems?",
    "What is cylinder head porting?",
    "How do I optimize intake systems?",
]


def test_advisor_knowledge():
    """Test advisor with comprehensive questions."""
    print("=" * 80)
    print("COMPREHENSIVE AI ADVISOR KNOWLEDGE TEST")
    print("=" * 80)
    print()
    
    # Initialize vector store
    try:
        from services.vector_knowledge_store import VectorKnowledgeStore
        vector_store = VectorKnowledgeStore()
        print(f"[OK] Vector store initialized (count: {vector_store.count()})")
    except Exception as e:
        print(f"[FAIL] Failed to initialize vector store: {e}")
        return False
    
    # Ensure knowledge is loaded
    try:
        from services.ensure_racing_knowledge_loaded import ensure_racing_knowledge_loaded
        added = ensure_racing_knowledge_loaded(vector_store)
        print(f"[OK] Knowledge loading complete (added {added} entries)")
        print(f"  Total entries in store: {vector_store.count()}")
    except Exception as e:
        print(f"[FAIL] Failed to load knowledge: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("Testing knowledge retrieval...")
    print("-" * 80)
    
    # Test each question
    results = {
        "passed": 0,
        "failed": 0,
        "partial": 0,
        "details": []
    }
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Question: {question}")
        
        try:
            # Search vector store
            matches = vector_store.search(question, n_results=3, min_similarity=0.2)
            
            if not matches:
                print(f"  [FAIL] NO MATCHES FOUND")
                results["failed"] += 1
                results["details"].append({
                    "question": question,
                    "status": "failed",
                    "matches": 0,
                    "top_score": 0.0
                })
                continue
            
            top_match = matches[0]
            top_score = top_match.get("score", 0.0)
            top_text = top_match.get("text", "")[:150]
            
            print(f"  [OK] Found {len(matches)} matches")
            print(f"    Top score: {top_score:.3f}")
            print(f"    Top result: {top_text}...")
            
            # Evaluate quality
            if top_score >= 0.5:
                print(f"  [PASS] HIGH CONFIDENCE")
                results["passed"] += 1
                status = "passed"
            elif top_score >= 0.3:
                print(f"  [PARTIAL] MODERATE CONFIDENCE")
                results["partial"] += 1
                status = "partial"
            else:
                print(f"  [FAIL] LOW CONFIDENCE")
                results["failed"] += 1
                status = "failed"
            
            results["details"].append({
                "question": question,
                "status": status,
                "matches": len(matches),
                "top_score": top_score,
                "top_text": top_text
            })
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            results["failed"] += 1
            results["details"].append({
                "question": question,
                "status": "error",
                "error": str(e)
            })
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total questions: {len(TEST_QUESTIONS)}")
    print(f"[PASS] Passed (high confidence): {results['passed']}")
    print(f"[PARTIAL] Partial (moderate confidence): {results['partial']}")
    print(f"[FAIL] Failed (low/no confidence): {results['failed']}")
    print()
    
    # Calculate success rate
    success_rate = (results['passed'] + results['partial'] * 0.5) / len(TEST_QUESTIONS) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    print()
    
    # Show failed questions
    if results['failed'] > 0:
        print("FAILED QUESTIONS:")
        print("-" * 80)
        for detail in results['details']:
            if detail['status'] == 'failed':
                print(f"  - {detail['question']}")
                print(f"    (Score: {detail.get('top_score', 0):.3f}, Matches: {detail.get('matches', 0)})")
        print()
    
    # Test with actual advisor
    print("=" * 80)
    print("TESTING WITH ACTUAL ADVISOR")
    print("=" * 80)
    print()
    
    try:
        from services.ai_advisor_rag import RAGAIAdvisor
        
        advisor = RAGAIAdvisor(
            use_local_llm=False,  # Don't require LLM for this test
            enable_web_search=False,
            vector_store=vector_store
        )
        
        # Test a few questions with the advisor
        test_questions = [
            "What causes engine knock?",
            "How do I tune ignition timing?",
            "What is a VE table?",
        ]
        
        for question in test_questions:
            print(f"Question: {question}")
            try:
                response = advisor.answer(question)
                print(f"Answer: {response.answer[:200]}...")
                print(f"Confidence: {response.confidence:.2f}")
                print(f"Sources: {len(response.sources)}")
                print()
            except Exception as e:
                print(f"Error: {e}")
                print()
        
    except Exception as e:
        print(f"Could not test with advisor: {e}")
        import traceback
        traceback.print_exc()
    
    # Return success if >80% pass rate
    return success_rate >= 80.0


if __name__ == "__main__":
    success = test_advisor_knowledge()
    sys.exit(0 if success else 1)

