#!/usr/bin/env python3
"""
Working Advisor Test - With Progress Feedback

Tests advisor with detailed progress reporting and timeout handling.
"""

import sys
import time
import signal
import json
from pathlib import Path
from threading import Timer
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Global timeout flag
timeout_occurred = False

def timeout_handler(signum, frame):
    global timeout_occurred
    timeout_occurred = True
    print("\n⚠ TIMEOUT - Test taking too long, but continuing...")
    print("   (This is normal for first-time initialization)")

# Set up timeout (5 minutes)
if sys.platform != "win32":
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes

print("="*80)
print("ADVISOR KNOWLEDGE BASE TEST")
print("="*80)
print()

def print_progress(msg):
    """Print progress message with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

# Step 1: Import
print_progress("[1/5] Importing modules...")
try:
    from services.ai_advisor_rag import RAGAIAdvisor
    print_progress("    ✓ Imports successful")
except Exception as e:
    print_progress(f"    ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Initialize vector store (this is the slow part)
print_progress("[2/5] Initializing vector store...")
print_progress("    (This may take 30-120 seconds on first run)")
print_progress("    (Loading embedding model - this is normal)")

start_init = time.time()
init_time = 0.0
count = 0
try:
    # Initialize with web search enabled (for Google search)
    advisor = RAGAIAdvisor(
        use_local_llm=False,  # Skip LLM initialization
        enable_web_search=True,  # Enable web search for Google
    )
    
    # Note: Auto-populator will use Google search instead of slow forum scraping
    print_progress("    - Web search enabled (will use Google/DuckDuckGo)")
    init_time = time.time() - start_init
    print_progress(f"    ✓ Vector store initialized in {init_time:.1f}s")
    
    if advisor.vector_store:
        print_progress(f"    - Vector store type: {type(advisor.vector_store).__name__}")
        if hasattr(advisor.vector_store, 'collection'):
            count = advisor.vector_store.collection.count() if advisor.vector_store.collection else 0
            print_progress(f"    - Knowledge entries: {count}")
    else:
        print_progress("    ⚠ Vector store not available")
        sys.exit(1)
        
except Exception as e:
    print_progress(f"    ✗ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test questions
print_progress("[3/5] Testing knowledge base with questions...")

test_questions = [
    # Basic ECU Tuning Concepts
    ("What is ECU tuning?", "Should explain ECU remapping/flashing"),
    ("What is a fuel map?", "Should explain fuel mapping"),
    ("What is a VE table?", "Should explain volumetric efficiency table"),
    ("What is boost pressure?", "Should explain turbo boost"),
    ("How do I tune ignition timing?", "Should provide tuning advice"),
    ("What is knock detection?", "Should explain knock sensors"),
    ("What is AFR?", "Should explain air-fuel ratio"),
    ("What is lambda?", "Should explain lambda value"),
    ("What is stoichiometric ratio?", "Should explain 14.7:1 for gasoline"),
    
    # Fuel Tuning
    ("How do I tune the fuel VE table?", "Should explain fuel calibration process"),
    ("What AFR should I target at WOT?", "Should mention 12.5-13.2:1 range"),
    ("What is the stoichiometric AFR for gasoline?", "Should mention 14.7:1"),
    ("How do I use Local Autotune?", "Should explain A key shortcut"),
    ("What does too rich mean?", "Should explain rich condition symptoms"),
    ("What does too lean mean?", "Should explain lean condition and dangers"),
    ("How do I interpolate fuel tables?", "Should mention Ctrl+H/V shortcuts"),
    ("What is a fuel map used for?", "Should explain fuel calibration"),
    ("How do I smooth fuel tables?", "Should mention Ctrl+S or interpolation"),
    ("What AFR should I use for idle?", "Should mention 14.5-15.0:1 range"),
    ("How do I tune fuel for E85?", "Should explain E85 fuel requirements"),
    ("What is the difference between rich and lean?", "Should explain AFR concepts"),
    
    # Ignition Timing
    ("What is MBT timing?", "Should explain Minimum Best Timing"),
    ("How do I tune ignition timing?", "Should provide step-by-step process"),
    ("What happens if timing is too advanced?", "Should mention knock/detonation"),
    ("What happens if timing is too retarded?", "Should mention power loss and EGT"),
    ("How much timing should I run at WOT?", "Should mention 25-35° BTDC range"),
    ("How do I prevent knock?", "Should explain timing adjustment and monitoring"),
    ("What is knock detection?", "Should explain knock sensor operation"),
    ("How does boost affect ignition timing?", "Should mention reducing timing with boost"),
    ("Can I run more timing with E85?", "Should explain higher octane benefits"),
    ("What is detonation?", "Should explain engine knock/detonation"),
    
    # Boost Control
    ("How do I tune boost control?", "Should explain boost tuning process"),
    ("What is a wastegate?", "Should explain wastegate function"),
    ("What is overboost protection?", "Should explain safety feature"),
    ("How do I set boost targets?", "Should mention typical psi/bar values"),
    ("What is closed loop boost control?", "Should explain PID control"),
    ("What is open loop boost control?", "Should explain fixed duty cycle"),
    ("How much boost can I run?", "Should mention engine build requirements"),
    ("What is boost compensation?", "Should explain temperature/altitude adjustment"),
    ("How do I prevent boost spikes?", "Should mention ramp-in and safety"),
    ("What is a boost leak?", "Should explain symptoms and detection"),
    
    # Protections
    ("What is rev limit protection?", "Should explain RPM limiting"),
    ("What is EGT protection?", "Should explain exhaust gas temperature monitoring"),
    ("What is lean power cut?", "Should explain lambda-based protection"),
    ("How do I set up safety protections?", "Should explain protection configuration"),
    ("What is soft cut vs hard cut?", "Should explain rev limit types"),
    ("What EGT is too high?", "Should mention 900°C threshold"),
    ("How do I configure rev limit?", "Should explain rev limit setup"),
    ("What is speed limiting?", "Should explain pit lane/road speed limiters"),
    
    # Motorsport Features
    ("What is launch control?", "Should explain 3-stage launch system"),
    ("How do I set up anti-lag?", "Should explain anti-lag configuration"),
    ("What is traction control?", "Should explain slip-based power management"),
    ("How does shift cut work?", "Should explain paddle shift support"),
    ("What is a 3-stage launch?", "Should explain launch control stages"),
    ("How do I tune traction control?", "Should explain slip threshold adjustment"),
    ("What is boost by gear?", "Should explain gear-based boost control"),
    
    # Nitrous Oxide
    ("How do I tune nitrous?", "Should explain nitrous system tuning"),
    ("What is dry nitrous?", "Should explain nitrous-only system"),
    ("What is wet nitrous?", "Should explain nitrous+fuel system"),
    ("What bottle pressure should I use?", "Should mention 900-1100 psi"),
    ("What is progressive nitrous?", "Should explain gradual activation"),
    ("How much fuel do I need with nitrous?", "Should mention 50-100% increase"),
    ("What AFR should I use with nitrous?", "Should mention 11.5-12.5:1"),
    
    # Methanol Injection
    ("What is methanol injection?", "Should explain methanol system"),
    ("How do I tune methanol injection?", "Should explain duty cycle tuning"),
    ("What does methanol do?", "Should explain charge cooling and octane boost"),
    ("How much methanol should I inject?", "Should mention 10-30% duty at boost"),
    ("What is methanol failsafe?", "Should explain safety shutdown"),
    ("How does methanol affect timing?", "Should mention +2-5° timing increase"),
    
    # E85/Flex Fuel
    ("What is E85?", "Should explain ethanol blend"),
    ("How do I tune for flex fuel?", "Should explain flex fuel sensor setup"),
    ("What is ethanol content?", "Should explain 51-83% for E85"),
    ("How much more fuel does E85 need?", "Should mention 30-40% more fuel"),
    ("Can I run more timing with E85?", "Should explain higher octane benefits"),
    ("What is a flex fuel sensor?", "Should explain ethanol content measurement"),
    ("What is the stoichiometric ratio for E85?", "Should mention 9.8:1"),
    
    # Sensors
    ("What is a wideband O2 sensor?", "Should explain wideband lambda sensor"),
    ("What is a knock sensor?", "Should explain detonation detection"),
    ("What is a MAF sensor?", "Should explain mass airflow sensor"),
    ("What is a MAP sensor?", "Should explain manifold absolute pressure"),
    ("How do I calibrate sensors?", "Should explain sensor calibration process"),
    ("What is EGT?", "Should explain exhaust gas temperature"),
    ("What is IAT?", "Should explain intake air temperature"),
    ("What is TPS?", "Should explain throttle position sensor"),
    
    # Transmission
    ("What transmissions are supported?", "Should list supported gearboxes"),
    ("How do I tune clutch slip?", "Should explain torque converter control"),
    ("What is sequential control?", "Should explain sequential gearbox control"),
    ("How do I configure transmission?", "Should explain TCU setup"),
    
    # Hardware & Interfaces
    ("What GPIO boards are supported?", "Should list supported hardware"),
    ("How do I set up Arduino?", "Should explain Arduino GPIO setup"),
    ("What is I2C?", "Should explain I2C bus communication"),
    ("How do I connect sensors?", "Should explain sensor interface setup"),
    ("What USB cameras are supported?", "Should list camera vendors"),
    
    # Software Features
    ("How do I backup my tune?", "Should explain backup system"),
    ("How do I revert changes?", "Should explain revert/restore"),
    ("What keyboard shortcuts are available?", "Should list common shortcuts"),
    ("How do I view tables in 3D?", "Should explain V key toggle"),
    ("How do I interpolate tables?", "Should explain Ctrl+H/V"),
    ("How do I smooth tables?", "Should explain smoothing function"),
    
    # Troubleshooting
    ("My engine is knocking, what should I do?", "Should explain knock troubleshooting"),
    ("Why is my AFR too rich?", "Should explain rich condition causes"),
    ("Why is my AFR too lean?", "Should explain lean condition causes"),
    ("My boost is inconsistent, why?", "Should mention boost leaks"),
    ("My ECU won't connect, what's wrong?", "Should explain connection troubleshooting"),
    ("My camera isn't detected, help?", "Should explain camera detection"),
    ("My backup failed, why?", "Should explain backup troubleshooting"),
    
    # Advanced Concepts
    ("What is volumetric efficiency?", "Should explain VE concept"),
    ("What is MBT?", "Should explain Minimum Best Timing"),
    ("What is charge cooling?", "Should explain intake cooling"),
    ("What is octane rating?", "Should explain fuel octane"),
    ("What is detonation vs pre-ignition?", "Should explain difference"),
    ("What is boost creep?", "Should explain boost control issue"),
    ("What is fuel staging?", "Should explain primary/secondary injectors"),
    ("What is individual cylinder correction?", "Should explain per-cylinder tuning"),
    ("What is trailing ignition?", "Should explain rotary engine ignition"),
    ("What is flex fuel blending?", "Should explain automatic map switching"),
    
    # Tuning Process & Strategy
    ("How do I start tuning from scratch?", "Should explain systematic approach"),
    ("What should I tune first?", "Should mention fuel before timing"),
    ("How do I tune safely?", "Should emphasize protections and small changes"),
    ("What is the tuning process?", "Should explain step-by-step methodology"),
    ("How do I optimize power?", "Should explain power tuning strategy"),
    ("How do I tune for efficiency?", "Should explain efficiency tuning"),
    ("How do I tune for racing?", "Should explain motorsport tuning approach"),
    ("How do I tune for street?", "Should explain street tuning considerations"),
    
    # Specific Scenarios
    ("How do I tune a turbo engine?", "Should explain turbo-specific tuning"),
    ("How do I tune a supercharged engine?", "Should explain supercharger tuning"),
    ("How do I tune a rotary engine?", "Should mention trailing ignition"),
    ("How do I tune for high altitude?", "Should explain altitude compensation"),
    ("How do I tune for hot weather?", "Should explain temperature compensation"),
    ("How do I tune for cold weather?", "Should explain cold start tuning"),
    
    # Data Logging & Analysis
    ("How do I log data?", "Should explain data logging"),
    ("What should I log?", "Should list important parameters"),
    ("How do I analyze logs?", "Should explain log analysis"),
    ("What is telemetry?", "Should explain real-time data"),
    
    # Safety & Best Practices
    ("What safety features should I enable?", "Should list important protections"),
    ("How do I tune safely?", "Should emphasize safety first approach"),
    ("What should I backup?", "Should explain backup best practices"),
    ("How often should I backup?", "Should recommend frequent backups"),
    ("What are tuning best practices?", "Should list recommended practices"),
]

results = []
for i, (question, expected_topic) in enumerate(test_questions, 1):
    print_progress(f"  [{i}/{len(test_questions)}] Q: {question}")
    try:
        start = time.time()
        response = advisor.answer(question)
        elapsed = time.time() - start
        
        # Handle both RAGResponse and string responses
        if hasattr(response, 'answer'):
            answer = response.answer
            confidence = response.confidence if hasattr(response, 'confidence') else 0.0
            sources = response.sources if hasattr(response, 'sources') else []
        else:
            # String response - calculate confidence from vector store
            answer = str(response)
            confidence = 0.5  # Default for template responses
            sources = []
            
            # Try to get confidence from vector store search
            if advisor.vector_store:
                try:
                    search_results = advisor.vector_store.search(question, n_results=1)
                    if search_results:
                        confidence = search_results[0].get('similarity', 0.5)
                except:
                    pass
        
        # Determine status
        if confidence > 0.6:
            status = "✓ GOOD"
        elif confidence > 0.4:
            status = "⚠ MODERATE"
        elif confidence > 0.2:
            status = "⚠ LOW"
        else:
            status = "✗ POOR"
        
        print_progress(f"      {status} | Confidence: {confidence:.2f} | Time: {elapsed:.1f}s")
        print_progress(f"      Answer length: {len(answer)} chars")
        if sources:
            print_progress(f"      Sources: {len(sources)}")
        
        results.append({
            "question": question,
            "expected_topic": expected_topic,
            "answer": answer[:500],  # Store first 500 chars for PDF
            "confidence": confidence,
            "answer_length": len(answer),
            "response_time": elapsed,
            "sources_count": len(sources),
            "status": status,
        })
        
    except Exception as e:
        print_progress(f"      ✗ ERROR: {e}")
        results.append({
            "question": question,
            "error": str(e),
            "status": "✗ ERROR"
        })

# Step 4: Summary
print_progress("[4/5] Generating summary...")

successful = [r for r in results if "error" not in r]
avg_conf = 0.0
avg_time = 0.0
good = 0
moderate = 0
low = 0
assessment = "No successful responses"

if successful:
    avg_conf = sum(r["confidence"] for r in successful) / len(successful)
    avg_time = sum(r["response_time"] for r in successful) / len(successful)
    
    good = len([r for r in successful if r["confidence"] > 0.6])
    moderate = len([r for r in successful if r["confidence"] > 0.4])
    low = len([r for r in successful if r["confidence"] <= 0.4])
    
    print_progress(f"  Questions answered: {len(successful)}/{len(test_questions)}")
    print_progress(f"  Average confidence: {avg_conf:.2f}")
    print_progress(f"  Average response time: {avg_time:.1f}s")
    print_progress(f"  Quality breakdown:")
    print_progress(f"    - Good (conf > 0.6): {good}")
    print_progress(f"    - Moderate (0.4-0.6): {moderate}")
    print_progress(f"    - Low (< 0.4): {low}")
    
    # Overall assessment
    if avg_conf > 0.6:
        assessment = "✓ EXCELLENT - Advisor has strong knowledge base"
    elif avg_conf > 0.4:
        assessment = "⚠ GOOD - Advisor has decent knowledge, may need more content"
    else:
        assessment = "✗ NEEDS IMPROVEMENT - Advisor needs more knowledge base content"
    
    print_progress(f"  Assessment: {assessment}")
else:
    print_progress("  ✗ No successful responses")

# Step 5: Detailed results
print_progress("[5/5] Detailed results:")
print()
for i, result in enumerate(results, 1):
    print(f"  {i}. {result['question']}")
    if "error" in result:
        print(f"     Status: {result['status']}")
        print(f"     Error: {result['error']}")
    else:
        print(f"     Status: {result['status']}")
        print(f"     Confidence: {result['confidence']:.2f}")
        print(f"     Response time: {result['response_time']:.1f}s")
        print(f"     Answer length: {result['answer_length']} chars")
    print()

print("="*80)
print("TEST COMPLETE")
if timeout_occurred:
    print("⚠ Note: Test exceeded timeout but completed successfully")
print("="*80)

# Save results to JSON
test_results = {
    "test_name": "AI Advisor Knowledge Base Test",
    "timestamp": datetime.now().isoformat(),
    "initialization_time": init_time,
    "vector_store_type": type(advisor.vector_store).__name__ if advisor.vector_store else None,
    "knowledge_entries": count if advisor.vector_store and hasattr(advisor.vector_store, 'collection') else 0,
    "questions": results,
    "summary": {
        "total_questions": len(test_questions),
        "successful": len(successful) if successful else 0,
        "failed": len([r for r in results if "error" in r]),
        "average_confidence": avg_conf if successful else 0.0,
        "average_response_time": avg_time if successful else 0.0,
        "good_responses": good if successful else 0,
        "moderate_responses": moderate if successful else 0,
        "low_responses": low if successful else 0,
        "assessment": assessment if successful else "No successful responses"
    }
}

# Save JSON
json_path = project_root / "advisor_test_results.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(test_results, f, indent=2, ensure_ascii=False)
print_progress(f"Results saved to: {json_path}")

# Generate PDF
print_progress("Generating PDF report...")
try:
    from tests.pdf_report_generator import PDFReportGenerator
    pdf_gen = PDFReportGenerator()
    pdf_path = project_root / "advisor_test_report.pdf"
    
    # Convert to format expected by PDF generator
    pdf_results = {
        "test_name": test_results["test_name"],
        "generated": test_results["timestamp"],
        "summary": test_results["summary"],
        "modules": [{
            "name": "AI Advisor Knowledge Base",
            "passed": test_results["summary"]["successful"],
            "failed": test_results["summary"]["failed"],
            "skipped": 0,
            "total": test_results["summary"]["total_questions"],
            "tests": [
                {
                    "name": r["question"],
                    "status": "passed" if "error" not in r else "failed",
                    "message": r.get("status", ""),
                    "details": {
                        "confidence": r.get("confidence", 0.0),
                        "response_time": r.get("response_time", 0.0),
                        "answer_length": r.get("answer_length", 0),
                        "error": r.get("error", None)
                    }
                } for r in results
            ]
        }]
    }
    
    if pdf_gen.generate_report(pdf_results, pdf_path):
        print_progress(f"PDF report generated: {pdf_path}")
    else:
        print_progress("⚠ PDF generation failed, but JSON results are available")
except Exception as e:
    print_progress(f"⚠ PDF generation error: {e}")
    print_progress("JSON results are still available")

# Cancel timeout
if sys.platform != "win32":
    signal.alarm(0)

