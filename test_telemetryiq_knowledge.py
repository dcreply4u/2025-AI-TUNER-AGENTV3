#!/usr/bin/env python3
"""
Test TelemetryIQ Knowledge
Tests if the advisor can answer questions about its own software.
"""

from services.ai_advisor_rag import RAGAIAdvisor

def test_telemetryiq_knowledge():
    """Test advisor with TelemetryIQ questions."""
    print("=" * 70)
    print("Testing TelemetryIQ Knowledge")
    print("=" * 70)
    
    advisor = RAGAIAdvisor()
    
    # Test questions about the software itself
    test_questions = [
        "what is telemetryiq",
        "what features does telemetryiq have",
        "what ECUs does telemetryiq support",
        "how do I use the AI advisor",
        "what is the AI chat advisor",
        "does telemetryiq support video recording",
        "can telemetryiq do live streaming"
    ]
    
    print("\nTesting Questions About TelemetryIQ:\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"{'='*70}")
        print(f"Question {i}: {question}")
        print(f"{'-'*70}")
        
        response = advisor.answer(question)
        
        print(f"Answer: {response.answer[:500]}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Sources: {len(response.sources)}")
        print(f"Used Web Search: {response.used_web_search}")
        
        if response.sources:
            print("\nSource Details:")
            for j, source in enumerate(response.sources[:2], 1):
                metadata = source.get("metadata", {})
                topic = metadata.get("topic", "Unknown")
                category = metadata.get("category", "Unknown")
                print(f"  {j}. {topic} ({category})")
        
        # Check if answer is relevant
        answer_lower = response.answer.lower()
        if "telemetryiq" in answer_lower or "aituner" in answer_lower or response.confidence > 0.5:
            print("  ✓ Answer appears relevant")
        else:
            print("  ⚠️  Answer may not be relevant")
        
        print()
    
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    test_telemetryiq_knowledge()

