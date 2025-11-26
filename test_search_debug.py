#!/usr/bin/env python3
"""Debug search functionality"""

from services.vector_knowledge_store import VectorKnowledgeStore

vs = VectorKnowledgeStore()
print(f"Knowledge base entries: {vs.count()}\n")

queries = ["telemetryiq", "what is telemetryiq", "telemetryiq overview"]

for query in queries:
    print(f"Query: '{query}'")
    print("-" * 60)
    results = vs.search(query, n_results=5, min_similarity=0.2)
    print(f"Found {len(results)} results")
    for i, r in enumerate(results, 1):
        topic = r.get("metadata", {}).get("topic", "N/A")
        similarity = r.get("similarity", 0)
        text_preview = r.get("text", "")[:100].replace("\n", " ")
        print(f"  {i}. {topic}")
        print(f"     Similarity: {similarity:.3f}")
        print(f"     Preview: {text_preview}...")
    print()

