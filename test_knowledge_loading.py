"""Quick test of knowledge loading and search."""

from services.vector_knowledge_store import VectorKnowledgeStore
from services.comprehensive_knowledge_loader import load_all_knowledge

# Clear and reload
vs = VectorKnowledgeStore()
vs.clear()
print(f"Starting with {vs.count()} entries")

# Load all knowledge
count = load_all_knowledge(vs)
print(f"Loaded {count} entries, total: {vs.count()}")

# Test search
test_questions = [
    "What is a VE table?",
    "How do I tune ignition timing?",
    "What causes engine knock?",
    "How does boost control work?",
    "What is E85 tuning?",
]

print("\nTesting searches:")
for q in test_questions:
    results = vs.search(q, n_results=1, min_similarity=0.1)
    if results:
        print(f"  {q}")
        print(f"    -> Found: similarity={results[0]['similarity']:.3f}")
        print(f"    -> Text: {results[0]['text'][:100]}...")
    else:
        print(f"  {q} -> NO RESULTS")

