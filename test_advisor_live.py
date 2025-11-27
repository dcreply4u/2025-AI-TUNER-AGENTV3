"""Test the actual advisor with real questions."""

from services.vector_knowledge_store import VectorKnowledgeStore
from services.comprehensive_knowledge_loader import load_all_knowledge
from services.ai_advisor_rag import RAGAIAdvisor

# Load knowledge
print("Loading knowledge...")
vs = VectorKnowledgeStore()
vs.clear()
load_all_knowledge(vs)
print(f"Loaded {vs.count()} knowledge entries\n")

# Create advisor
print("Initializing advisor...")
advisor = RAGAIAdvisor(
    use_local_llm=False,  # Test without LLM first
    enable_web_search=False,
    vector_store=vs
)
print("Advisor ready!\n")

# Test questions
test_questions = [
    "What is a VE table?",
    "How do I tune ignition timing?",
    "What causes engine knock?",
    "How does boost control work?",
    "What is E85 tuning?",
    "How do I tune fuel maps?",
    "What is the optimal air-fuel ratio for turbocharged engines?",
]

print("=" * 80)
print("TESTING ADVISOR")
print("=" * 80)
print()

for i, question in enumerate(test_questions, 1):
    print(f"[{i}/{len(test_questions)}] Question: {question}")
    print("-" * 80)
    
    try:
        response = advisor.answer(question)
        print(f"Answer: {response.answer[:500]}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Sources: {len(response.sources)}")
        if response.sources:
            print(f"Top source: {response.sources[0].get('text', response.sources[0].get('title', ''))[:100]}")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

