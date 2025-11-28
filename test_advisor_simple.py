#!/usr/bin/env python3
"""
Simple Advisor Test - Minimal initialization

Tests advisor with minimal setup to avoid timeouts.
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
print("SIMPLE ADVISOR TEST")
print("="*80)
print()

# Step 1: Import
print("[1] Importing...", end=" ", flush=True)
try:
    from services.ai_advisor_rag import RAGAIAdvisor
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

# Step 2: Initialize (this might take time)
print("[2] Initializing advisor (this may take 30-60 seconds)...", flush=True)
print("    Loading vector store and knowledge base...", flush=True)

start_init = time.time()
try:
    advisor = RAGAIAdvisor(
        use_local_llm=False,  # Skip LLM for speed
        enable_web_search=False,  # Skip web search for speed
    )
    init_time = time.time() - start_init
    print(f"    ✓ Initialized in {init_time:.1f}s")
    print(f"    - Vector Store: {advisor.vector_store is not None}")
except Exception as e:
    print(f"    ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test questions
print("\n[3] Testing questions...")
questions = [
    "What is ECU tuning?",
    "What is a fuel map?",
    "What is boost pressure?",
]

results = []
for i, question in enumerate(questions, 1):
    print(f"  [{i}/{len(questions)}] {question}...", end=" ", flush=True)
    try:
        start = time.time()
        response = advisor.ask(question)
        elapsed = time.time() - start
        
        answer = response.answer if hasattr(response, 'answer') else str(response)
        confidence = response.confidence if hasattr(response, 'confidence') else 0.0
        
        status = "✓" if confidence > 0.5 else "⚠" if confidence > 0.3 else "✗"
        print(f"{status} (conf: {confidence:.2f}, {elapsed:.1f}s)")
        
        results.append({
            "question": question,
            "confidence": confidence,
            "answer_length": len(answer),
        })
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append({"question": question, "error": str(e)})

# Summary
print("\n[4] Summary:")
if results:
    successful = [r for r in results if "error" not in r]
    if successful:
        avg_conf = sum(r["confidence"] for r in successful) / len(successful)
        print(f"  Questions: {len(successful)}/{len(questions)} successful")
        print(f"  Avg Confidence: {avg_conf:.2f}")
        
        if avg_conf > 0.6:
            print("  ✓ Advisor has good knowledge!")
        elif avg_conf > 0.4:
            print("  ⚠ Advisor has moderate knowledge")
        else:
            print("  ✗ Advisor has limited knowledge")
    else:
        print("  ✗ No successful responses")
else:
    print("  ✗ No results")

print("\n" + "="*80)
print("Test Complete")
print("="*80)

