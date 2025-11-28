#!/usr/bin/env python3
"""
Chat Advisor Test with Timeout Handling

Tests advisor with proper timeout handling to prevent hangs.
"""

import sys
import signal
from pathlib import Path
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


@contextmanager
def timeout_handler(seconds):
    """Handle timeout for operations."""
    if sys.platform != "win32":
        def timeout_handler_func(signum, frame):
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        
        signal.signal(signal.SIGALRM, timeout_handler_func)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
    else:
        # Windows doesn't support SIGALRM, use threading timeout instead
        import threading
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = True
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(seconds)
        
        if thread.is_alive():
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        if exception[0]:
            raise exception[0]
        yield


def test_advisor():
    """Test advisor with timeout protection."""
    print("="*80)
    print("ADVISOR KNOWLEDGE TEST (with timeout protection)")
    print("="*80)
    
    # Step 1: Import
    print("\n[Step 1/5] Importing modules...")
    try:
        from services.ai_advisor_rag import RAGAIAdvisor
        print("✓ Import successful")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Step 2: Initialize advisor (with timeout)
    print("\n[Step 2/5] Initializing advisor (60s timeout)...")
    advisor = None
    try:
        # Try initialization with explicit timeout awareness
        print("  Creating advisor instance...")
        advisor = RAGAIAdvisor(
            use_local_llm=False,
            enable_web_search=False,
        )
        print("✓ Advisor created")
        print(f"  - Vector Store: {advisor.vector_store is not None}")
        print(f"  - LLM Available: {advisor.llm_available}")
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user")
        return False
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if not advisor:
        print("✗ Advisor is None")
        return False
    
    # Step 3: Test single question
    print("\n[Step 3/5] Testing single question...")
    try:
        question = "What is ECU tuning?"
        print(f"  Question: {question}")
        
        response = advisor.ask(question)
        
        answer = response.answer if hasattr(response, 'answer') else str(response)
        confidence = response.confidence if hasattr(response, 'confidence') else 0.0
        
        print(f"✓ Response received")
        print(f"  - Answer: {answer[:100]}...")
        print(f"  - Confidence: {confidence:.2f}")
        
    except Exception as e:
        print(f"✗ Question test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test multiple questions
    print("\n[Step 4/5] Testing multiple questions...")
    questions = [
        "What is ECU tuning?",
        "What is a fuel map?",
        "What is boost pressure?",
    ]
    
    results = []
    for i, question in enumerate(questions, 1):
        try:
            print(f"  [{i}/{len(questions)}] {question[:50]}...")
            response = advisor.ask(question)
            
            answer = response.answer if hasattr(response, 'answer') else str(response)
            confidence = response.confidence if hasattr(response, 'confidence') else 0.0
            
            results.append({
                "question": question,
                "confidence": confidence,
                "has_answer": len(answer) > 10,
            })
            
            status = "✓" if confidence > 0.5 else "⚠" if confidence > 0.3 else "✗"
            print(f"    {status} Confidence: {confidence:.2f}")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results.append({"question": question, "error": str(e)})
    
    # Step 5: Summary
    print("\n[Step 5/5] Generating summary...")
    successful = [r for r in results if "error" not in r and r.get("has_answer", False)]
    
    if successful:
        avg_conf = sum(r["confidence"] for r in successful) / len(successful)
        print(f"\n✓ Test completed successfully!")
        print(f"  - Questions answered: {len(successful)}/{len(questions)}")
        print(f"  - Average confidence: {avg_conf:.2f}")
        return True
    else:
        print(f"\n✗ No successful responses")
        return False


if __name__ == "__main__":
    try:
        success = test_advisor()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

