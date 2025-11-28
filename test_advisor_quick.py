#!/usr/bin/env python3
"""
Quick Advisor Test - Shows real-time output

Tests a few questions to verify auto-population is working.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("QUICK ADVISOR TEST - AUTO-POPULATION CHECK")
print("="*80)
print()
print("Initializing advisor...", flush=True)

try:
    from services.ai_advisor_rag import RAGAIAdvisor
    
    # Initialize with web search enabled
    advisor = RAGAIAdvisor(
        use_local_llm=False,
        enable_web_search=True,
    )
    
    print("✓ Advisor initialized")
    print(f"  - Vector Store: {advisor.vector_store is not None}")
    print(f"  - Web Search: {advisor.web_search is not None and advisor.web_search.is_available() if advisor.web_search else False}")
    print(f"  - Auto-Populator: {advisor.auto_populator is not None}")
    print()
    
    # Test questions
    test_questions = [
        "What is ECU tuning?",
        "What is a fuel map?",
        "What is boost pressure?",
    ]
    
    print(f"Testing {len(test_questions)} questions...")
    print()
    
    for i, question in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] Question: {question}")
        print("  Processing...", flush=True)
        
        try:
            start = time.time()
            response = advisor.answer(question)
            elapsed = time.time() - start
            
            # Handle response
            if hasattr(response, 'answer'):
                answer = response.answer
                confidence = response.confidence
            else:
                answer = str(response)
                confidence = 0.5
            
            print(f"  ✓ Response received ({elapsed:.1f}s)")
            print(f"  - Confidence: {confidence:.2f}")
            print(f"  - Answer length: {len(answer)} chars")
            print(f"  - Preview: {answer[:100]}...")
            
            # Check if auto-population happened
            if advisor.auto_populator:
                print(f"  - Auto-populator: Enabled")
                print(f"    Successful: {advisor.auto_populator.successful_populations}")
                print(f"    Failed: {advisor.auto_populator.failed_populations}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    if advisor.auto_populator:
        print(f"\nAuto-Population Stats:")
        print(f"  Successful: {advisor.auto_populator.successful_populations}")
        print(f"  Failed: {advisor.auto_populator.failed_populations}")
        print(f"  Total attempts: {len(advisor.auto_populator.auto_population_history)}")
        
        if advisor.auto_populator.auto_population_history:
            print(f"\nRecent attempts:")
            for attempt in advisor.auto_populator.auto_population_history[-3:]:
                result = attempt.get('result', {})
                status = "✓" if result.get('success') else "✗"
                print(f"  {status} {attempt['question'][:50]}...")
                if not result.get('success') and result.get('errors'):
                    print(f"    Error: {result['errors'][0]}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
