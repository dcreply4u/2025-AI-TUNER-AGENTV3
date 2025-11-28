#!/usr/bin/env python3
"""
Component-Level Advisor Test

Tests advisor components individually to identify bottlenecks.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("COMPONENT-LEVEL ADVISOR TEST")
print("="*80)

# Test imports individually
print("\n[1] Testing imports...")
components = {
    "VectorKnowledgeStore": "services.vector_knowledge_store",
    "RAGAIAdvisor": "services.ai_advisor_rag",
}

for name, module_path in components.items():
    try:
        module = __import__(module_path, fromlist=[name])
        cls = getattr(module, name)
        print(f"  ✓ {name}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# Test vector store initialization
print("\n[2] Testing vector store initialization...")
try:
    from services.vector_knowledge_store import VectorKnowledgeStore
    print("  Creating vector store...", end=" ", flush=True)
    vs = VectorKnowledgeStore()
    print("✓")
    print(f"  - Type: {type(vs).__name__}")
except Exception as e:
    print(f"✗ {e}")
    import traceback
    traceback.print_exc()

# Test advisor creation (minimal)
print("\n[3] Testing advisor creation...")
try:
    from services.ai_advisor_rag import RAGAIAdvisor
    print("  Creating advisor (no LLM, no web search)...", end=" ", flush=True)
    advisor = RAGAIAdvisor(
        use_local_llm=False,
        enable_web_search=False,
    )
    print("✓")
    print(f"  - Vector Store: {advisor.vector_store is not None}")
    
    # Quick test
    print("\n[4] Testing single question...")
    print("  Question: 'What is ECU tuning?'", end=" ", flush=True)
    response = advisor.ask("What is ECU tuning?")
    answer = response.answer if hasattr(response, 'answer') else str(response)
    confidence = response.confidence if hasattr(response, 'confidence') else 0.0
    print("✓")
    print(f"  - Answer length: {len(answer)}")
    print(f"  - Confidence: {confidence:.2f}")
    print(f"  - Preview: {answer[:100]}...")
    
except Exception as e:
    print(f"✗ {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("Component test complete")
print("="*80)

