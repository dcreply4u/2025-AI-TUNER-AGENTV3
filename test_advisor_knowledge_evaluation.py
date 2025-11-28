#!/usr/bin/env python3
"""
Chat Advisor Knowledge Evaluation Test

Tests the chat advisor against the knowledge base to evaluate:
- What it knows
- What it doesn't know
- Response quality
- Confidence levels
- Web search usage
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class AdvisorKnowledgeEvaluator:
    """Evaluate advisor knowledge and responses."""
    
    def __init__(self):
        """Initialize evaluator."""
        self.results: List[Dict[str, Any]] = []
        self.advisor = None
        self._initialize_advisor()
    
    def _initialize_advisor(self):
        """Initialize the advisor."""
        try:
            from services.ai_advisor_rag import RAGAIAdvisor
            print("Initializing RAG AI Advisor...")
            self.advisor = RAGAIAdvisor(
                use_local_llm=False,  # Don't require LLM for testing
                enable_web_search=False,  # Disable web search for knowledge base testing
            )
            print("✓ Advisor initialized\n")
        except Exception as e:
            print(f"✗ Failed to initialize advisor: {e}")
            sys.exit(1)
    
    def test_question(self, question: str, category: str, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Test a question and evaluate the response.
        
        Args:
            question: Question to ask
            category: Category of question
            expected_keywords: Keywords that should appear in answer
        
        Returns:
            Test result dictionary
        """
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print(f"Category: {category}")
        print(f"{'='*80}")
        
        start_time = time.time()
        try:
            response = self.advisor.ask(question)
            elapsed = time.time() - start_time
            
            answer = response.answer if hasattr(response, 'answer') else str(response)
            confidence = response.confidence if hasattr(response, 'confidence') else 0.0
            sources = response.sources if hasattr(response, 'sources') else []
            used_web_search = response.used_web_search if hasattr(response, 'used_web_search') else False
            
            # Evaluate response
            answer_length = len(answer)
            has_content = answer_length > 10
            answer_lower = answer.lower()
            
            # Check for expected keywords
            keyword_matches = []
            if expected_keywords:
                for keyword in expected_keywords:
                    if keyword.lower() in answer_lower:
                        keyword_matches.append(keyword)
            
            # Determine quality
            if confidence >= 0.7 and has_content:
                quality = "EXCELLENT"
            elif confidence >= 0.5 and has_content:
                quality = "GOOD"
            elif confidence >= 0.3 and has_content:
                quality = "FAIR"
            elif has_content:
                quality = "POOR"
            else:
                quality = "EMPTY"
            
            result = {
                "question": question,
                "category": category,
                "answer": answer[:500],  # First 500 chars
                "full_answer": answer,
                "confidence": confidence,
                "quality": quality,
                "answer_length": answer_length,
                "has_content": has_content,
                "sources_count": len(sources),
                "used_web_search": used_web_search,
                "expected_keywords": expected_keywords or [],
                "keyword_matches": keyword_matches,
                "keyword_match_rate": len(keyword_matches) / len(expected_keywords) if expected_keywords else 0.0,
                "elapsed_time": elapsed,
            }
            
            # Print results
            print(f"Answer ({answer_length} chars, {elapsed:.2f}s):")
            print(f"  {answer[:300]}...")
            print(f"\nConfidence: {confidence:.2f} ({quality})")
            print(f"Sources: {len(sources)}")
            print(f"Web Search Used: {used_web_search}")
            if expected_keywords:
                print(f"Keyword Matches: {len(keyword_matches)}/{len(expected_keywords)}")
                if keyword_matches:
                    print(f"  Matched: {', '.join(keyword_matches)}")
                if len(keyword_matches) < len(expected_keywords):
                    missing = [k for k in expected_keywords if k.lower() not in answer_lower]
                    print(f"  Missing: {', '.join(missing)}")
            
            self.results.append(result)
            return result
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            result = {
                "question": question,
                "category": category,
                "error": str(e),
                "quality": "ERROR",
            }
            self.results.append(result)
            return result
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite."""
        print("="*80)
        print("CHAT ADVISOR KNOWLEDGE EVALUATION")
        print("="*80)
        print(f"Testing advisor against knowledge base...")
        print(f"Advisor Type: {type(self.advisor).__name__}")
        print(f"Vector Store: {self.advisor.vector_store is not None}")
        print(f"Web Search: {self.advisor.enable_web_search}")
        print("="*80)
        
        # Test questions organized by category
        test_questions = [
            # Basic Tuning Knowledge
            ("What is ECU tuning?", "Basic Tuning", ["ECU", "tuning", "engine"]),
            ("What is a fuel map?", "Basic Tuning", ["fuel", "map", "table"]),
            ("What is ignition timing?", "Basic Tuning", ["ignition", "timing", "degrees"]),
            ("What is boost pressure?", "Basic Tuning", ["boost", "pressure", "turbo"]),
            ("What is AFR?", "Basic Tuning", ["AFR", "air", "fuel", "ratio"]),
            
            # Advanced Tuning
            ("How do I tune ignition timing?", "Advanced Tuning", ["ignition", "timing", "advance", "retard"]),
            ("What is a wideband O2 sensor?", "Advanced Tuning", ["wideband", "oxygen", "sensor", "AFR"]),
            ("What is knock detection?", "Advanced Tuning", ["knock", "detonation", "sensor"]),
            ("How does boost control work?", "Advanced Tuning", ["boost", "control", "wastegate"]),
            ("What is fuel trim?", "Advanced Tuning", ["fuel", "trim", "correction"]),
            
            # Racing & Performance
            ("What is lap timing?", "Racing", ["lap", "timing", "time"]),
            ("What is telemetry?", "Racing", ["telemetry", "data", "sensors"]),
            ("What is drag racing?", "Racing", ["drag", "racing", "quarter", "mile"]),
            ("What is a racing line?", "Racing", ["racing", "line", "corner", "apex"]),
            ("What is launch control?", "Racing", ["launch", "control", "RPM", "clutch"]),
            
            # Nitrous & Forced Induction
            ("What is nitrous oxide?", "Nitrous", ["nitrous", "oxide", "N2O", "injection"]),
            ("How does a turbocharger work?", "Forced Induction", ["turbo", "compressor", "turbine"]),
            ("What is anti-lag?", "Forced Induction", ["anti-lag", "turbo", "exhaust"]),
            ("What is a wastegate?", "Forced Induction", ["wastegate", "boost", "pressure"]),
            
            # Safety & Diagnostics
            ("What is traction control?", "Safety", ["traction", "control", "wheel", "slip"]),
            ("What is knock?", "Safety", ["knock", "detonation", "pre-ignition"]),
            ("What is overboost protection?", "Safety", ["overboost", "protection", "safety"]),
            ("How do I diagnose engine problems?", "Diagnostics", ["diagnose", "engine", "problem", "troubleshoot"]),
            
            # Software & Features
            ("What is TelemetryIQ?", "Software", ["TelemetryIQ", "software", "application"]),
            ("What features does the AI Tuner Agent have?", "Software", ["features", "capabilities"]),
            ("How do I use the graphing features?", "Software", ["graphing", "plot", "data"]),
            
            # Technical Specifications (likely to need web search)
            ("What is the compression ratio of a 2024 Honda Civic Type R?", "Technical Specs", ["compression", "ratio"]),
            ("What is the latest Holley EFI firmware version?", "Technical Specs", ["firmware", "version"]),
            ("What is the stock boost pressure for a Subaru WRX?", "Technical Specs", ["boost", "pressure"]),
            
            # Troubleshooting
            ("My engine is running lean, what should I do?", "Troubleshooting", ["lean", "fuel", "AFR"]),
            ("How do I fix a boost leak?", "Troubleshooting", ["boost", "leak", "fix"]),
            ("What causes engine knock?", "Troubleshooting", ["knock", "cause", "detonation"]),
        ]
        
        # Run all tests
        for question, category, keywords in test_questions:
            self.test_question(question, category, keywords)
            time.sleep(0.5)  # Small delay between questions
        
        # Generate summary
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total = len(self.results)
        if total == 0:
            print("No tests completed.")
            return
        
        # Count by quality
        quality_counts = {}
        confidence_sum = 0.0
        has_content_count = 0
        web_search_count = 0
        total_keyword_matches = 0
        total_expected_keywords = 0
        
        for result in self.results:
            quality = result.get("quality", "UNKNOWN")
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            if "confidence" in result:
                confidence_sum += result["confidence"]
            
            if result.get("has_content", False):
                has_content_count += 1
            
            if result.get("used_web_search", False):
                web_search_count += 1
            
            if "keyword_match_rate" in result:
                total_keyword_matches += result.get("keyword_matches", [])
                if result.get("expected_keywords"):
                    total_expected_keywords += len(result["expected_keywords"])
        
        # Print statistics
        print(f"\nTotal Questions: {total}")
        print(f"\nQuality Distribution:")
        for quality in ["EXCELLENT", "GOOD", "FAIR", "POOR", "EMPTY", "ERROR"]:
            count = quality_counts.get(quality, 0)
            percentage = (count / total) * 100 if total > 0 else 0
            print(f"  {quality:10s}: {count:3d} ({percentage:5.1f}%)")
        
        avg_confidence = confidence_sum / total if total > 0 else 0.0
        print(f"\nAverage Confidence: {avg_confidence:.2f}")
        print(f"Responses with Content: {has_content_count}/{total} ({has_content_count/total*100:.1f}%)")
        print(f"Web Search Used: {web_search_count}/{total}")
        
        if total_expected_keywords > 0:
            keyword_match_rate = len(total_keyword_matches) / total_expected_keywords if total_expected_keywords > 0 else 0
            print(f"Keyword Match Rate: {keyword_match_rate*100:.1f}%")
        
        # Category breakdown
        print(f"\nCategory Breakdown:")
        category_stats = {}
        for result in self.results:
            category = result.get("category", "Unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "good": 0, "confidence_sum": 0.0}
            
            category_stats[category]["total"] += 1
            if result.get("quality") in ["EXCELLENT", "GOOD"]:
                category_stats[category]["good"] += 1
            if "confidence" in result:
                category_stats[category]["confidence_sum"] += result["confidence"]
        
        for category, stats in sorted(category_stats.items()):
            total_cat = stats["total"]
            good_cat = stats["good"]
            avg_conf_cat = stats["confidence_sum"] / total_cat if total_cat > 0 else 0.0
            print(f"  {category:20s}: {good_cat}/{total_cat} good ({avg_conf_cat:.2f} avg confidence)")
        
        # Best and worst responses
        print(f"\nBest Responses (High Confidence):")
        sorted_by_conf = sorted([r for r in self.results if "confidence" in r], 
                              key=lambda x: x["confidence"], reverse=True)
        for result in sorted_by_conf[:5]:
            print(f"  [{result['confidence']:.2f}] {result['question'][:60]}")
        
        print(f"\nWorst Responses (Low Confidence):")
        for result in sorted_by_conf[-5:]:
            print(f"  [{result['confidence']:.2f}] {result['question'][:60]}")
        
        # Knowledge gaps
        print(f"\nKnowledge Gaps (Low Confidence or Empty):")
        gaps = [r for r in self.results if r.get("confidence", 1.0) < 0.4 or not r.get("has_content", True)]
        for gap in gaps[:10]:
            print(f"  - {gap['question']}")
            print(f"    Confidence: {gap.get('confidence', 0):.2f}, Quality: {gap.get('quality', 'UNKNOWN')}")
        
        print("\n" + "="*80)
        print("Evaluation Complete")
        print("="*80)


def main():
    """Main entry point."""
    evaluator = AdvisorKnowledgeEvaluator()
    evaluator.run_comprehensive_test()


if __name__ == "__main__":
    main()

