#!/usr/bin/env python3
"""Test RAG advisor with specific queries"""

from services.ai_advisor_rag import RAGAIAdvisor

advisor = RAGAIAdvisor()

test_queries = [
    "what is fuel pressure",
    "what is spark",
    "how do I tune boost",
    "what causes knock"
]

print("Testing RAG Advisor Answers")
print("=" * 60)

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 60)
    response = advisor.answer(query)
    
    if hasattr(response, 'answer'):
        answer = response.answer
        confidence = getattr(response, 'confidence', 'N/A')
        sources = getattr(response, 'sources', [])
        
        print(f"Answer: {answer[:300]}...")
        print(f"Confidence: {confidence}")
        if sources:
            print(f"Sources: {len(sources)} found")
            for i, source in enumerate(sources[:2], 1):
                print(f"  {i}. {source.get('topic', 'Unknown')[:50]}")
    else:
        print(f"Response: {str(response)[:300]}...")
    
    print()

