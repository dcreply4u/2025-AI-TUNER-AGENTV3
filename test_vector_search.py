#!/usr/bin/env python3
"""Debug vector store search"""

from services.vector_knowledge_store import VectorKnowledgeStore

vs = VectorKnowledgeStore()
print(f"Vector store has {vs.count()} entries\n")

test_queries = ["fuel pressure", "spark", "boost", "knock"]

for query in test_queries:
    print(f"Query: '{query}'")
    print("-" * 60)
    # Test with very low threshold to see all results
    results = vs.search(query, n_results=5, min_similarity=0.0)
    print(f"Found {len(results)} results (with min_similarity=0.0)")
    for i, r in enumerate(results, 1):
        topic = r.get("topic", "N/A")
        similarity = r.get("similarity", 0)
        text_preview = r.get("text", "")[:80].replace("\n", " ")
        print(f"  {i}. {topic} (similarity: {similarity:.3f})")
        print(f"     Preview: {text_preview}...")
    print()

