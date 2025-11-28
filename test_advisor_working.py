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
    ("What is a dynamometer?", "Should explain what is a dynamometer?"),
    ("How do I use a dynamometer?", "Should explain usage"),
    ("How does a chassis dyno work?", "Should explain how does a chassis dyno work?"),
    ("How does an engine dyno work?", "Should explain how does an engine dyno work?"),
    ("What is SAE correction factor?", "Should explain what is sae correction factor?"),
    ("How do I use SAE correction factor?", "Should explain usage"),
    ("What is STD correction factor?", "Should explain what is std correction factor?"),
    ("How do I use STD correction factor?", "Should explain usage"),
    ("What is uncorrected horsepower?", "Should explain what is uncorrected horsepower?"),
    ("How do I use uncorrected horsepower?", "Should explain usage"),
    ("What is corrected horsepower?", "Should explain what is corrected horsepower?"),
    ("How do I use corrected horsepower?", "Should explain usage"),
    ("How do I calculate horsepower from torque?", "Should explain how do i calculate horsepower from torque?"),
    ("What is the formula for calculate horsepower from torque?", "Should provide formula"),
    ("How do I calculate torque from horsepower?", "Should explain how do i calculate torque from horsepower?"),
    ("What is the formula for calculate torque from horsepower?", "Should provide formula"),
    ("What is the 5252 rule?", "Should explain what is the 5252 rule?"),
    ("How do I use the 5252 rule?", "Should explain usage"),
    ("How do I calculate rear wheel horsepower?", "Should explain how do i calculate rear wheel horsepower?"),
    ("What is the formula for calculate rear wheel horsepower?", "Should provide formula"),
    ("How do I calculate flywheel horsepower from rear wheel horsepower?", "Should explain how do i calculate flywheel horsepower from rear wheel horsepower?"),
    ("What is the formula for calculate flywheel horsepower from rear wheel horsepower?", "Should provide formula"),
    ("What is drivetrain loss?", "Should explain what is drivetrain loss?"),
    ("How do I use drivetrain loss?", "Should explain usage"),
    ("How much drivetrain loss should I expect?", "Should explain how much drivetrain loss should i expect?"),
    ("How do I perform a dyno pull?", "Should explain how do i perform a dyno pull?"),
    ("What is a steady state dyno test?", "Should explain what is a steady state dyno test?"),
    ("How do I use a steady state dyno test?", "Should explain usage"),
    ("What is a sweep test on a dyno?", "Should explain what is a sweep test on a dyno?"),
    ("How do I use a sweep test on a dyno?", "Should explain usage"),
    ("How long should a dyno pull be?", "Should explain how long should a dyno pull be?"),
    ("What RPM range should I test on a dyno?", "Should explain what rpm range should i test on a dyno?"),
    ("How do I read a dyno graph?", "Should explain how do i read a dyno graph?"),
    ("What is a power curve?", "Should explain what is a power curve?"),
    ("How do I use a power curve?", "Should explain usage"),
    ("What is a torque curve?", "Should explain what is a torque curve?"),
    ("How do I use a torque curve?", "Should explain usage"),
    ("What is peak horsepower?", "Should explain what is peak horsepower?"),
    ("How do I use peak horsepower?", "Should explain usage"),
    ("What is peak torque?", "Should explain what is peak torque?"),
    ("How do I use peak torque?", "Should explain usage"),
    ("What is area under the curve?", "Should explain what is area under the curve?"),
    ("How do I use area under the curve?", "Should explain usage"),
    ("What is EFI tuning?", "Should explain what is efi tuning?"),
    ("Why is EFI tuning?", "Should explain importance"),
    ("How does EFI work?", "Should explain how does efi work?"),
    ("What is an EFI system?", "Should explain what is an efi system?"),
    ("Why is an EFI system?", "Should explain importance"),
    ("What is a fuel injector?", "Should explain what is a fuel injector?"),
    ("Why is a fuel injector?", "Should explain importance"),
    ("How do fuel injectors work?", "Should explain how do fuel injectors work?"),
    ("What is injector pulse width?", "Should explain what is injector pulse width?"),
    ("Why is injector pulse width?", "Should explain importance"),
    ("What is injector duty cycle?", "Should explain what is injector duty cycle?"),
    ("Why is injector duty cycle?", "Should explain importance"),
    ("How do I calculate injector size?", "Should explain how do i calculate injector size?"),
    ("What happens if I don't calculate injector size?", "Should explain consequences"),
    ("What size injectors do I need?", "Should explain what size injectors do i need?"),
    ("How do I calculate fuel flow rate?", "Should explain how do i calculate fuel flow rate?"),
    ("What happens if I don't calculate fuel flow rate?", "Should explain consequences"),
    ("What is a fuel map in EFI?", "Should explain what is a fuel map in efi?"),
    ("Why is a fuel map in EFI?", "Should explain importance"),
    ("What is an ignition map in EFI?", "Should explain what is an ignition map in efi?"),
    ("Why is an ignition map in EFI?", "Should explain importance"),
    ("What is VE table in EFI?", "Should explain what is ve table in efi?"),
    ("Why is VE table in EFI?", "Should explain importance"),
    ("How do I tune the VE table?", "Should explain how do i tune the ve table?"),
    ("What happens if I don't tune the VE table?", "Should explain consequences"),
    ("What is injector dead time?", "Should explain what is injector dead time?"),
    ("Why is injector dead time?", "Should explain importance"),
    ("How do I measure injector dead time?", "Should explain how do i measure injector dead time?"),
    ("What happens if I don't measure injector dead time?", "Should explain consequences"),
    ("What is injector latency?", "Should explain what is injector latency?"),
    ("Why is injector latency?", "Should explain importance"),
    ("What is fuel pressure?", "Should explain what is fuel pressure?"),
    ("Why is fuel pressure?", "Should explain importance"),
    ("How does fuel pressure affect tuning?", "Should explain how does fuel pressure affect tuning?"),
    ("What fuel pressure should I run?", "Should explain what fuel pressure should i run?"),
    ("How do I adjust fuel pressure?", "Should explain how do i adjust fuel pressure?"),
    ("What happens if I don't adjust fuel pressure?", "Should explain consequences"),
    ("What is a MAP sensor?", "Should explain what is a map sensor?"),
    ("Why is a MAP sensor?", "Should explain importance"),
    ("What is a MAF sensor?", "Should explain what is a maf sensor?"),
    ("Why is a MAF sensor?", "Should explain importance"),
    ("What is the difference between MAP and MAF?", "Should explain what is the difference between map and maf?"),
    ("Why is the difference between MAP and MAF?", "Should explain importance"),
    ("How do I calibrate a MAP sensor?", "Should explain how do i calibrate a map sensor?"),
    ("What happens if I don't calibrate a MAP sensor?", "Should explain consequences"),
    ("How do I calibrate a MAF sensor?", "Should explain how do i calibrate a maf sensor?"),
    ("What happens if I don't calibrate a MAF sensor?", "Should explain consequences"),
    ("What is a TPS sensor?", "Should explain what is a tps sensor?"),
    ("Why is a TPS sensor?", "Should explain importance"),
    ("How do I calibrate TPS?", "Should explain how do i calibrate tps?"),
    ("What happens if I don't calibrate TPS?", "Should explain consequences"),
    ("What is an IAT sensor?", "Should explain what is an iat sensor?"),
    ("Why is an IAT sensor?", "Should explain importance"),
    ("What is an ECT sensor?", "Should explain what is an ect sensor?"),
    ("Why is an ECT sensor?", "Should explain importance"),
    ("How do temperature sensors affect tuning?", "Should explain how do temperature sensors affect tuning?"),
    ("How do I tune EFI for idle?", "Should explain how do i tune efi for idle?"),
    ("What happens if I don't tune EFI for idle?", "Should explain consequences"),
    ("How do I tune EFI for cruise?", "Should explain how do i tune efi for cruise?"),
    ("What happens if I don't tune EFI for cruise?", "Should explain consequences"),
    ("How do I tune EFI for WOT?", "Should explain how do i tune efi for wot?"),
    ("What happens if I don't tune EFI for WOT?", "Should explain consequences"),
    ("What is closed loop tuning?", "Should explain what is closed loop tuning?"),
    ("Why is closed loop tuning?", "Should explain importance"),
    ("What is open loop tuning?", "Should explain what is open loop tuning?"),
    ("Why is open loop tuning?", "Should explain importance"),
    ("What is adaptive learning?", "Should explain what is adaptive learning?"),
    ("Why is adaptive learning?", "Should explain importance"),
    ("How do I disable adaptive learning?", "Should explain how do i disable adaptive learning?"),
    ("What happens if I don't disable adaptive learning?", "Should explain consequences"),
    ("What is fuel trim?", "Should explain what is fuel trim?"),
    ("Why is fuel trim?", "Should explain importance"),
    ("What is long term fuel trim?", "Should explain what is long term fuel trim?"),
    ("Why is long term fuel trim?", "Should explain importance"),
    ("What is short term fuel trim?", "Should explain what is short term fuel trim?"),
    ("Why is short term fuel trim?", "Should explain importance"),
    ("Why is my EFI running rich?", "Should explain why is my efi running rich?"),
    ("Why is my EFI running lean?", "Should explain why is my efi running lean?"),
    ("How do I fix rich condition in EFI?", "Should explain how do i fix rich condition in efi?"),
    ("What happens if I don't fix rich condition in EFI?", "Should explain consequences"),
    ("How do I fix lean condition in EFI?", "Should explain how do i fix lean condition in efi?"),
    ("What happens if I don't fix lean condition in EFI?", "Should explain consequences"),
    ("What causes injector misfire?", "Should explain what causes injector misfire?"),
    ("How do I test fuel injectors?", "Should explain how do i test fuel injectors?"),
    ("What happens if I don't test fuel injectors?", "Should explain consequences"),
    ("What is injector balance?", "Should explain what is injector balance?"),
    ("Why is injector balance?", "Should explain importance"),
    ("How do I clean fuel injectors?", "Should explain how do i clean fuel injectors?"),
    ("What happens if I don't clean fuel injectors?", "Should explain consequences"),
    ("What is Holley EFI?", "Should explain what is holley efi?"),
    ("How do I connect to Holley EFI?", "Should explain how do i connect to holley efi?"),
    ("What software do I use for Holley EFI?", "Should explain what software do i use for holley efi?"),
    ("What is Holley EFI software?", "Should explain what is holley efi software?"),
    ("How do I load a tune in Holley EFI?", "Should explain how do i load a tune in holley efi?"),
    ("How do I save a tune in Holley EFI?", "Should explain how do i save a tune in holley efi?"),
    ("What is a Holley EFI calibration file?", "Should explain what is a holley efi calibration file?"),
    ("What is the Base Fuel Table in Holley?", "Should explain what is the base fuel table in holley?"),
    ("How do I tune the Base Fuel Table?", "Should explain how do i tune the base fuel table?"),
    ("What is the Target AFR Table in Holley?", "Should explain what is the target afr table in holley?"),
    ("How do I set Target AFR in Holley?", "Should explain how do i set target afr in holley?"),
    ("What is the Ignition Timing Table in Holley?", "Should explain what is the ignition timing table in holley?"),
    ("How do I tune ignition timing in Holley?", "Should explain how do i tune ignition timing in holley?"),
    ("What is the VE Table in Holley?", "Should explain what is the ve table in holley?"),
    ("How do I tune VE in Holley EFI?", "Should explain how do i tune ve in holley efi?"),
    ("What is the Acceleration Enrichment in Holley?", "Should explain what is the acceleration enrichment in holley?"),
    ("How do I tune Acceleration Enrichment?", "Should explain how do i tune acceleration enrichment?"),
    ("What is Holley EFI Learn?", "Should explain what is holley efi learn?"),
    ("How do I enable Holley Learn?", "Should explain how do i enable holley learn?"),
    ("How do I disable Holley Learn?", "Should explain how do i disable holley learn?"),
    ("What is Holley EFI Closed Loop?", "Should explain what is holley efi closed loop?"),
    ("How do I enable Closed Loop in Holley?", "Should explain how do i enable closed loop in holley?"),
    ("What is Holley EFI Boost Control?", "Should explain what is holley efi boost control?"),
    ("How do I set up boost control in Holley?", "Should explain how do i set up boost control in holley?"),
    ("What is Holley EFI Nitrous Control?", "Should explain what is holley efi nitrous control?"),
    ("How do I set up nitrous in Holley EFI?", "Should explain how do i set up nitrous in holley efi?"),
    ("How do I calibrate MAP sensor in Holley?", "Should explain how do i calibrate map sensor in holley?"),
    ("How do I calibrate TPS in Holley?", "Should explain how do i calibrate tps in holley?"),
    ("How do I set up wideband O2 in Holley?", "Should explain how do i set up wideband o2 in holley?"),
    ("What wideband sensors work with Holley?", "Should explain what wideband sensors work with holley?"),
    ("How do I configure IAT sensor in Holley?", "Should explain how do i configure iat sensor in holley?"),
    ("How do I configure ECT sensor in Holley?", "Should explain how do i configure ect sensor in holley?"),
    ("What is Holley EFI 2-Step?", "Should explain what is holley efi 2-step?"),
    ("How do I set up 2-Step in Holley?", "Should explain how do i set up 2-step in holley?"),
    ("What is Holley EFI Traction Control?", "Should explain what is holley efi traction control?"),
    ("How do I set up Traction Control in Holley?", "Should explain how do i set up traction control in holley?"),
    ("What is Holley EFI Boost by Gear?", "Should explain what is holley efi boost by gear?"),
    ("How do I set up Boost by Gear in Holley?", "Should explain how do i set up boost by gear in holley?"),
    ("What is Holley EFI Flex Fuel?", "Should explain what is holley efi flex fuel?"),
    ("How do I set up Flex Fuel in Holley?", "Should explain how do i set up flex fuel in holley?"),
    ("Why won't my Holley EFI connect?", "Should explain why won't my holley efi connect?"),
    ("How do I update Holley EFI firmware?", "Should explain how do i update holley efi firmware?"),
    ("What causes Holley EFI to run rich?", "Should explain what causes holley efi to run rich?"),
    ("What causes Holley EFI to run lean?", "Should explain what causes holley efi to run lean?"),
    ("How do I reset Holley EFI?", "Should explain how do i reset holley efi?"),
    ("How do I backup Holley EFI tune?", "Should explain how do i backup holley efi tune?"),
    ("What is nitrous oxide?", "Should explain what is nitrous oxide?"),
    ("How does nitrous oxide work?", "Should explain how does nitrous oxide work?"),
    ("What does nitrous do to an engine?", "Should explain what does nitrous do to an engine?"),
    ("How much power does nitrous add?", "Should explain how much power does nitrous add?"),
    ("What is a dry nitrous system?", "Should explain what is a dry nitrous system?"),
    ("What is a wet nitrous system?", "Should explain what is a wet nitrous system?"),
    ("What is the difference between dry and wet nitrous?", "Should explain what is the difference between dry and wet nitrous?"),
    ("What is direct port nitrous?", "Should explain what is direct port nitrous?"),
    ("What is a plate nitrous system?", "Should explain what is a plate nitrous system?"),
    ("What is a nitrous solenoid?", "Should explain what is a nitrous solenoid?"),
    ("What is a nitrous bottle?", "Should explain what is a nitrous bottle?"),
    ("What is nitrous bottle pressure?", "Should explain what is nitrous bottle pressure?"),
    ("What pressure should nitrous bottle be at?", "Should explain what pressure should nitrous bottle be at?"),
    ("How do I check nitrous bottle pressure?", "Should explain how do i check nitrous bottle pressure?"),
    ("What is a nitrous nozzle?", "Should explain what is a nitrous nozzle?"),
    ("How do I size a nitrous nozzle?", "Should explain how do i size a nitrous nozzle?"),
    ("What is the formula for size a nitrous nozzle?", "Should provide formula"),
    ("What is a nitrous purge?", "Should explain what is a nitrous purge?"),
    ("How do I set up nitrous purge?", "Should explain how do i set up nitrous purge?"),
    ("How do I tune for nitrous?", "Should explain how do i tune for nitrous?"),
    ("How much fuel do I need with nitrous?", "Should explain how much fuel do i need with nitrous?"),
    ("What AFR should I run with nitrous?", "Should explain what afr should i run with nitrous?"),
    ("How do I add fuel for nitrous?", "Should explain how do i add fuel for nitrous?"),
    ("What timing should I run with nitrous?", "Should explain what timing should i run with nitrous?"),
    ("How much should I retard timing with nitrous?", "Should explain how much should i retard timing with nitrous?"),
    ("What is progressive nitrous?", "Should explain what is progressive nitrous?"),
    ("How do I set up progressive nitrous?", "Should explain how do i set up progressive nitrous?"),
    ("What is a nitrous window switch?", "Should explain what is a nitrous window switch?"),
    ("How do I set up a nitrous window switch?", "Should explain how do i set up a nitrous window switch?"),
    ("What safety features do I need for nitrous?", "Should explain what safety features do i need for nitrous?"),
    ("What is nitrous failsafe?", "Should explain what is nitrous failsafe?"),
    ("How do I set up nitrous failsafe?", "Should explain how do i set up nitrous failsafe?"),
    ("What happens if nitrous bottle pressure drops?", "Should explain what happens if nitrous bottle pressure drops?"),
    ("How do I prevent nitrous backfire?", "Should explain how do i prevent nitrous backfire?"),
    ("What causes nitrous backfire?", "Should explain what causes nitrous backfire?"),
    ("How do I test nitrous system safely?", "Should explain how do i test nitrous system safely?"),
    ("What size nitrous shot should I start with?", "Should explain what size nitrous shot should i start with?"),
    ("What size nitrous shot should I start with?", "Should provide formula"),
    ("How do I calculate nitrous shot size?", "Should explain how do i calculate nitrous shot size?"),
    ("What is the formula for calculate nitrous shot size?", "Should provide formula"),
    ("What is a 50hp nitrous shot?", "Should explain what is a 50hp nitrous shot?"),
    ("What is a 100hp nitrous shot?", "Should explain what is a 100hp nitrous shot?"),
    ("What is a 150hp nitrous shot?", "Should explain what is a 150hp nitrous shot?"),
    ("How do I increase nitrous shot size?", "Should explain how do i increase nitrous shot size?"),
    ("What is the formula for increase nitrous shot size?", "Should provide formula"),
    ("What is the maximum safe nitrous shot?", "Should explain what is the maximum safe nitrous shot?"),
    ("Why isn't my nitrous working?", "Should explain why isn't my nitrous working?"),
    ("What causes nitrous to not activate?", "Should explain what causes nitrous to not activate?"),
    ("Why is my nitrous bottle pressure low?", "Should explain why is my nitrous bottle pressure low?"),
    ("How do I refill nitrous bottle?", "Should explain how do i refill nitrous bottle?"),
    ("What causes nitrous solenoid failure?", "Should explain what causes nitrous solenoid failure?"),
    ("How do I test nitrous solenoid?", "Should explain how do i test nitrous solenoid?"),
    ("What is a turbocharger?", "Should explain what is a turbocharger?"),
    ("How does a turbocharger work?", "Should explain how does a turbocharger work?"),
    ("What is turbo lag?", "Should explain what is turbo lag?"),
    ("How do I reduce turbo lag?", "Should explain how do i reduce turbo lag?"),
    ("What happens if I don't reduce turbo lag?", "Should explain consequences"),
    ("What is boost threshold?", "Should explain what is boost threshold?"),
    ("What is boost pressure?", "Should explain what is boost pressure?"),
    ("What is PSI in boost?", "Should explain what is psi in boost?"),
    ("What is bar in boost?", "Should explain what is bar in boost?"),
    ("How do I convert PSI to bar?", "Should explain how do i convert psi to bar?"),
    ("What happens if I don't convert PSI to bar?", "Should explain consequences"),
    ("What is a turbo compressor?", "Should explain what is a turbo compressor?"),
    ("What is a turbo turbine?", "Should explain what is a turbo turbine?"),
    ("What is a wastegate?", "Should explain what is a wastegate?"),
    ("How does a wastegate work?", "Should explain how does a wastegate work?"),
    ("What is an internal wastegate?", "Should explain what is an internal wastegate?"),
    ("What is an external wastegate?", "Should explain what is an external wastegate?"),
    ("What is a blow-off valve?", "Should explain what is a blow-off valve?"),
    ("What is a bypass valve?", "Should explain what is a bypass valve?"),
    ("What is the difference between BOV and bypass valve?", "Should explain what is the difference between bov and bypass valve?"),
    ("What is an intercooler?", "Should explain what is an intercooler?"),
    ("How does an intercooler work?", "Should explain how does an intercooler work?"),
    ("What is charge air temperature?", "Should explain what is charge air temperature?"),
    ("How do I size a turbo?", "Should explain how do i size a turbo?"),
    ("What happens if I don't size a turbo?", "Should explain consequences"),
    ("What is turbo A/R ratio?", "Should explain what is turbo a/r ratio?"),
    ("What A/R should I use?", "Should explain what a/r should i use?"),
    ("What is compressor map?", "Should explain what is compressor map?"),
    ("How do I read a compressor map?", "Should explain how do i read a compressor map?"),
    ("What happens if I don't read a compressor map?", "Should explain consequences"),
    ("What is turbo trim?", "Should explain what is turbo trim?"),
    ("What trim should I use?", "Should explain what trim should i use?"),
    ("What is single turbo vs twin turbo?", "Should explain what is single turbo vs twin turbo?"),
    ("What is sequential turbo?", "Should explain what is sequential turbo?"),
    ("What is twin scroll turbo?", "Should explain what is twin scroll turbo?"),
    ("How do I tune for turbo?", "Should explain how do i tune for turbo?"),
    ("What happens if I don't tune for turbo?", "Should explain consequences"),
    ("What boost should I run?", "Should explain what boost should i run?"),
    ("How do I increase boost?", "Should explain how do i increase boost?"),
    ("What happens if I don't increase boost?", "Should explain consequences"),
    ("How do I decrease boost?", "Should explain how do i decrease boost?"),
    ("What happens if I don't decrease boost?", "Should explain consequences"),
    ("What is boost creep?", "Should explain what is boost creep?"),
    ("How do I fix boost creep?", "Should explain how do i fix boost creep?"),
    ("What happens if I don't fix boost creep?", "Should explain consequences"),
    ("What is boost spike?", "Should explain what is boost spike?"),
    ("How do I prevent boost spike?", "Should explain how do i prevent boost spike?"),
    ("What happens if I don't prevent boost spike?", "Should explain consequences"),
    ("What is boost taper?", "Should explain what is boost taper?"),
    ("How do I tune boost taper?", "Should explain how do i tune boost taper?"),
    ("What happens if I don't tune boost taper?", "Should explain consequences"),
    ("How do I tune fuel for turbo?", "Should explain how do i tune fuel for turbo?"),
    ("What happens if I don't tune fuel for turbo?", "Should explain consequences"),
    ("What AFR should I run with turbo?", "Should explain what afr should i run with turbo?"),
    ("How do I tune timing for turbo?", "Should explain how do i tune timing for turbo?"),
    ("What happens if I don't tune timing for turbo?", "Should explain consequences"),
    ("How much should I retard timing with boost?", "Should explain how much should i retard timing with boost?"),
    ("What is boost compensation?", "Should explain what is boost compensation?"),
    ("How do I set up boost compensation?", "Should explain how do i set up boost compensation?"),
    ("What happens if I don't set up boost compensation?", "Should explain consequences"),
    ("What is boost enrichment?", "Should explain what is boost enrichment?"),
    ("How do I set up boost enrichment?", "Should explain how do i set up boost enrichment?"),
    ("What happens if I don't set up boost enrichment?", "Should explain consequences"),
    ("How do I cool intake air with turbo?", "Should explain how do i cool intake air with turbo?"),
    ("What happens if I don't cool intake air with turbo?", "Should explain consequences"),
    ("What is intercooler efficiency?", "Should explain what is intercooler efficiency?"),
    ("How do I improve intercooler efficiency?", "Should explain how do i improve intercooler efficiency?"),
    ("What happens if I don't improve intercooler efficiency?", "Should explain consequences"),
    ("What is water injection?", "Should explain what is water injection?"),
    ("How do I set up water injection?", "Should explain how do i set up water injection?"),
    ("What happens if I don't set up water injection?", "Should explain consequences"),
    ("What is methanol injection?", "Should explain what is methanol injection?"),
    ("How do I set up methanol injection?", "Should explain how do i set up methanol injection?"),
    ("What happens if I don't set up methanol injection?", "Should explain consequences"),
    ("Why is my turbo not making boost?", "Should explain why is my turbo not making boost?"),
    ("What causes low boost?", "Should explain what causes low boost?"),
    ("What causes high boost?", "Should explain what causes high boost?"),
    ("Why is my turbo surging?", "Should explain why is my turbo surging?"),
    ("How do I fix turbo surge?", "Should explain how do i fix turbo surge?"),
    ("What happens if I don't fix turbo surge?", "Should explain consequences"),
    ("What causes turbo failure?", "Should explain what causes turbo failure?"),
    ("How do I prevent turbo failure?", "Should explain how do i prevent turbo failure?"),
    ("What happens if I don't prevent turbo failure?", "Should explain consequences"),
    ("What is turbo oiling?", "Should explain what is turbo oiling?"),
    ("How do I set up turbo oiling?", "Should explain how do i set up turbo oiling?"),
    ("What happens if I don't set up turbo oiling?", "Should explain consequences"),
    ("Calculate horsepower if torque is 400 ft-lb at 6000 RPM", "Should calculate HP = (400 × 6000) / 5252 = 457 HP"),
    ("Calculate torque if horsepower is 500 HP at 5500 RPM", "Should calculate T = (500 × 5252) / 5500 = 477 ft-lb"),
    ("What is horsepower at 300 ft-lb and 7000 RPM?", "Should calculate HP = (300 × 7000) / 5252 = 400 HP"),
    ("What is torque at 600 HP and 5000 RPM?", "Should calculate T = (600 × 5252) / 5000 = 630 ft-lb"),
    ("Calculate HP from 450 ft-lb at 6500 RPM", "Should calculate HP"),
    ("Calculate torque from 550 HP at 6000 RPM", "Should calculate torque"),
    ("What is the 5252 constant in HP calculation?", "Should explain 5252 constant"),
    ("Why do HP and torque cross at 5252 RPM?", "Should explain mathematical reason"),
    ("Convert 500 HP to kilowatts", "Should calculate 500 × 0.746 = 373 kW"),
    ("Convert 400 kW to horsepower", "Should calculate 400 × 1.34 = 536 HP"),
    ("Calculate CFM for 350 CID engine at 6000 RPM with 90% VE", "Should calculate CFM = (350 × 6000 × 0.9) / 3456 = 546 CFM"),
    ("Calculate VE if engine flows 500 CFM at 5500 RPM, 350 CID", "Should calculate VE = (500 × 3456) / (350 × 5500) = 0.90"),
    ("What is airflow for 400 CID at 7000 RPM, 95% VE?", "Should calculate CFM"),
    ("Calculate VE from 600 CFM, 400 CID, 6500 RPM", "Should calculate VE"),
    ("What is the airflow formula?", "Should provide CFM = (CID × RPM × VE) / 3456"),
    ("How do I calculate air density?", "Should provide density formula"),
    ("Calculate air density at 80°F, 29.92 inHg, 50% humidity", "Should calculate density"),
    ("What is air density at sea level, 60°F?", "Should mention 1.225 kg/m³"),
    ("Calculate injector size for 600 HP engine, 0.6 BSFC, 80% duty, 8 injectors", "Should calculate size = (600 × 0.6) / (0.8 × 8) = 56.25 lb/hr"),
    ("What injector size for 500 HP, 0.65 BSFC, 85% duty, 6 injectors?", "Should calculate size needed"),
    ("Calculate fuel flow at 50% duty cycle, 60 lb/hr injector", "Should calculate flow = 60 × 0.5 = 30 lb/hr"),
    ("What is new flow if fuel pressure changes from 43.5 to 58 PSI?", "Should calculate new = old × sqrt(58/43.5) = old × 1.15"),
    ("Calculate fuel flow for 8 injectors at 70% duty, 50 lb/hr each", "Should calculate total flow"),
    ("What is BSFC for an engine making 500 HP using 30 lb/hr fuel?", "Should calculate BSFC = 30 / 500 = 0.06"),
    ("Calculate required fuel for 600 HP at 0.65 BSFC", "Should calculate 600 × 0.65 = 390 lb/hr"),
    ("Convert 15 PSI boost to bar", "Should calculate 15 / 14.5 = 1.03 bar"),
    ("Convert 1.5 bar boost to PSI", "Should calculate 1.5 × 14.5 = 21.75 PSI"),
    ("What is 20 PSI in bar?", "Should calculate 20 / 14.5 = 1.38 bar"),
    ("What is 2.0 bar in PSI?", "Should calculate 2.0 × 14.5 = 29 PSI"),
    ("Calculate absolute pressure at 10 PSI boost, 14.7 PSI atmospheric", "Should calculate 10 + 14.7 = 24.7 PSIA"),
    ("What is effective compression ratio at 15 PSI boost, 10:1 static CR?", "Should calculate effective CR"),
    ("Calculate power to weight if car weighs 3000 lbs and makes 450 HP", "Should calculate 450 / 1.5 = 0.15 HP/lb"),
    ("What weight for 0.2 HP/lb ratio at 600 HP?", "Should calculate weight = 600 / 0.2 = 3000 lbs"),
    ("Calculate 0-60 time for 400 HP, 3200 lb car", "Should estimate time"),
    ("Calculate quarter mile time for 500 HP, 3500 lb car", "Should estimate ET"),
    ("What is trap speed for 600 HP, 3000 lb car?", "Should estimate trap speed"),
    ("Calculate SAE correction factor at 85°F, 29.92 inHg, 60% humidity", "Should calculate correction"),
    ("What is corrected HP if uncorrected is 400 HP and correction factor is 0.95?", "Should calculate 400 × 0.95 = 380 HP"),
    ("Calculate temperature correction for dyno results", "Should provide temp correction formula"),
    ("What is altitude correction factor at 5000 ft?", "Should calculate altitude correction"),
    ("Calculate nitrous flow rate at 1000 PSI bottle pressure", "Should calculate flow"),
    ("What is fuel flow needed for 100hp nitrous shot?", "Should calculate fuel requirement"),
    ("Calculate nitrous shot size from flow rate", "Should provide shot size calculation"),
    ("Calculate turbo airflow requirement for 600 HP", "Should calculate airflow needed"),
    ("What is compressor efficiency at given pressure ratio?", "Should explain efficiency calculation"),
    ("Calculate intercooler efficiency if inlet is 200°F and outlet is 120°F, ambient 80°F", "Should calculate (200-120)/(200-80) = 67%"),
    ("What is charge temperature after intercooler?", "Should calculate outlet temperature"),
    ("I made 450 HP on a dyno at 75°F, what would it be at 95°F?", "Should provide solution for i made 450 hp on a dyno at 75°f, what would it be at 95°f?"),
    ("My dyno shows 400 RWHP, what is my estimated crank HP?", "Should provide solution for my dyno shows 400 rwhp, what is my estimated crank hp?"),
    ("I need to correct dyno results from 2000 ft altitude to sea level", "Should provide solution for i need to correct dyno results from 2000 ft altitude to sea level"),
    ("My dyno pull shows power dropping after 6000 RPM, why?", "Should provide solution for my dyno pull shows power dropping after 6000 rpm, why?"),
    ("How do I interpret my dyno graph showing torque curve?", "Should provide solution for how do i interpret my dyno graph showing torque curve?"),
    ("My dyno results show inconsistent numbers between pulls, why?", "Should provide solution for my dyno results show inconsistent numbers between pulls, why?"),
    ("What causes power to drop off at high RPM on dyno?", "Should provide solution for what causes power to drop off at high rpm on dyno?"),
    ("How do I calibrate my virtual dyno to match real dyno?", "Should provide solution for how do i calibrate my virtual dyno to match real dyno?"),
    ("My virtual dyno shows different numbers than chassis dyno, why?", "Should provide solution for my virtual dyno shows different numbers than chassis dyno, why?"),
    ("How accurate is virtual dyno compared to real dyno?", "Should provide solution for how accurate is virtual dyno compared to real dyno?"),
    ("My EFI is running rich at idle but lean at WOT, what's wrong?", "Should provide solution for my efi is running rich at idle but lean at wot, what's wrong?"),
    ("I installed larger injectors, how do I recalibrate my EFI?", "Should provide solution for i installed larger injectors, how do i recalibrate my efi?"),
    ("My EFI shows negative fuel trim, what does that mean?", "Should provide solution for my efi shows negative fuel trim, what does that mean?"),
    ("I'm getting injector misfire codes, how do I diagnose?", "Should provide solution for i'm getting injector misfire codes, how do i diagnose?"),
    ("My EFI won't start after tune changes, what happened?", "Should provide solution for my efi won't start after tune changes, what happened?"),
    ("My EFI is hunting at idle, how do I fix it?", "Should provide solution for my efi is hunting at idle, how do i fix it?"),
    ("I'm getting lean codes but AFR looks rich, why?", "Should provide solution for i'm getting lean codes but afr looks rich, why?"),
    ("My EFI fuel pressure is dropping under load, why?", "Should provide solution for my efi fuel pressure is dropping under load, why?"),
    ("How do I diagnose a bad MAF sensor?", "Should provide solution for how do i diagnose a bad maf sensor?"),
    ("My EFI is running fine but fuel economy is poor, why?", "Should provide solution for my efi is running fine but fuel economy is poor, why?"),
    ("How do I transfer a tune from one Holley EFI to another?", "Should provide solution for how do i transfer a tune from one holley efi to another?"),
    ("My Holley EFI Learn is making unwanted changes, how do I stop it?", "Should provide solution for my holley efi learn is making unwanted changes, how do i stop it?"),
    ("I need to set up boost control in Holley EFI, how?", "Should provide solution for i need to set up boost control in holley efi, how?"),
    ("How do I configure wideband O2 sensor in Holley EFI?", "Should provide solution for how do i configure wideband o2 sensor in holley efi?"),
    ("My Holley EFI won't connect to the software, help?", "Should provide solution for my holley efi won't connect to the software, help?"),
    ("My Holley EFI tune won't load, what's wrong?", "Should provide solution for my holley efi tune won't load, what's wrong?"),
    ("How do I backup my Holley EFI calibration?", "Should provide solution for how do i backup my holley efi calibration?"),
    ("My Holley EFI is running too rich, how do I fix it?", "Should provide solution for my holley efi is running too rich, how do i fix it?"),
    ("How do I set up flex fuel in Holley EFI?", "Should provide solution for how do i set up flex fuel in holley efi?"),
    ("My Holley EFI 2-step won't activate, why?", "Should provide solution for my holley efi 2-step won't activate, why?"),
    ("I want to add a 100hp nitrous shot, what do I need?", "Should provide solution for i want to add a 100hp nitrous shot, what do i need?"),
    ("My nitrous bottle pressure keeps dropping, why?", "Should provide solution for my nitrous bottle pressure keeps dropping, why?"),
    ("I'm getting backfire when nitrous activates, what's wrong?", "Should provide solution for i'm getting backfire when nitrous activates, what's wrong?"),
    ("How do I set up progressive nitrous for better traction?", "Should provide solution for how do i set up progressive nitrous for better traction?"),
    ("What safety features do I need for a 150hp nitrous shot?", "Should provide solution for what safety features do i need for a 150hp nitrous shot?"),
    ("My nitrous won't activate, how do I troubleshoot?", "Should provide solution for my nitrous won't activate, how do i troubleshoot?"),
    ("I'm getting lean condition when nitrous hits, why?", "Should provide solution for i'm getting lean condition when nitrous hits, why?"),
    ("How do I test my nitrous system safely?", "Should provide solution for how do i test my nitrous system safely?"),
    ("My nitrous solenoid is clicking but no flow, why?", "Should provide solution for my nitrous solenoid is clicking but no flow, why?"),
    ("What causes nitrous bottle to lose pressure quickly?", "Should provide solution for what causes nitrous bottle to lose pressure quickly?"),
    ("I'm upgrading to a larger turbo, how do I retune?", "Should provide solution for i'm upgrading to a larger turbo, how do i retune?"),
    ("My turbo is surging at high RPM, how do I fix it?", "Should provide solution for my turbo is surging at high rpm, how do i fix it?"),
    ("I'm getting boost creep, what causes this?", "Should provide solution for i'm getting boost creep, what causes this?"),
    ("How do I set up boost by gear in my ECU?", "Should provide solution for how do i set up boost by gear in my ecu?"),
    ("My intercooler isn't cooling enough, what can I do?", "Should provide solution for my intercooler isn't cooling enough, what can i do?"),
    ("My turbo won't make target boost, why?", "Should provide solution for my turbo won't make target boost, why?"),
    ("I'm getting boost spikes, how do I prevent them?", "Should provide solution for i'm getting boost spikes, how do i prevent them?"),
    ("My turbo is making too much boost, how do I reduce it?", "Should provide solution for my turbo is making too much boost, how do i reduce it?"),
    ("What causes turbo lag and how do I reduce it?", "Should provide solution for what causes turbo lag and how do i reduce it?"),
    ("My turbo is making noise, is it failing?", "Should provide solution for my turbo is making noise, is it failing?"),
    ("What if my dyno shows lower numbers than expected?", "Should explain troubleshooting for what if my dyno shows lower numbers than expected?"),
    ("What if my EFI won't start?", "Should explain troubleshooting for what if my efi won't start?"),
    ("What if my Holley EFI won't connect?", "Should explain troubleshooting for what if my holley efi won't connect?"),
    ("What if my nitrous won't activate?", "Should explain troubleshooting for what if my nitrous won't activate?"),
    ("What if my turbo won't make boost?", "Should explain troubleshooting for what if my turbo won't make boost?"),
    ("What if my engine is knocking?", "Should explain troubleshooting for what if my engine is knocking?"),
    ("What if my AFR is too rich?", "Should explain troubleshooting for what if my afr is too rich?"),
    ("What if my AFR is too lean?", "Should explain troubleshooting for what if my afr is too lean?"),
    ("What if my boost is inconsistent?", "Should explain troubleshooting for what if my boost is inconsistent?"),
    ("What if my fuel pressure is low?", "Should explain troubleshooting for what if my fuel pressure is low?"),
    ("What is the difference between chassis dyno and engine dyno?", "Should explain differences in what is the difference between chassis dyno and engine dyno?"),
    ("What is the difference between MAP and MAF sensors?", "Should explain differences in what is the difference between map and maf sensors?"),
    ("What is the difference between dry and wet nitrous?", "Should explain differences in what is the difference between dry and wet nitrous?"),
    ("What is the difference between internal and external wastegate?", "Should explain differences in what is the difference between internal and external wastegate?"),
    ("What is the difference between BOV and bypass valve?", "Should explain differences in what is the difference between bov and bypass valve?"),
    ("What is the difference between SAE and STD correction?", "Should explain differences in what is the difference between sae and std correction?"),
    ("What is the difference between open loop and closed loop?", "Should explain differences in what is the difference between open loop and closed loop?"),
    ("What is the difference between single and twin turbo?", "Should explain differences in what is the difference between single and twin turbo?"),
    ("What is the difference between progressive and non-progressive nitrous?", "Should explain differences in what is the difference between progressive and non-progressive nitrous?"),
    ("What is the difference between Holley Learn and manual tuning?", "Should explain differences in what is the difference between holley learn and manual tuning?"),
    ("When should I use a chassis dyno vs engine dyno?", "Should explain when to use when should i use a chassis dyno vs engine dyno?"),
    ("When should I use MAP vs MAF sensor?", "Should explain when to use when should i use map vs maf sensor?"),
    ("When should I use dry vs wet nitrous?", "Should explain when to use when should i use dry vs wet nitrous?"),
    ("When should I use internal vs external wastegate?", "Should explain when to use when should i use internal vs external wastegate?"),
    ("When should I use single vs twin turbo?", "Should explain when to use when should i use single vs twin turbo?"),
    ("When should I use progressive nitrous?", "Should explain when to use when should i use progressive nitrous?"),
    ("When should I enable Holley Learn?", "Should explain when to use when should i enable holley learn?"),
    ("When should I use closed loop tuning?", "Should explain when to use when should i use closed loop tuning?"),
    ("When should I upgrade injectors?", "Should explain when to use when should i upgrade injectors?"),
    ("When should I upgrade turbo?", "Should explain when to use when should i upgrade turbo?"),
    ("What is the best AFR for power?", "Should recommend best practices for what is the best afr for power?"),
    ("What is the best AFR for efficiency?", "Should recommend best practices for what is the best afr for efficiency?"),
    ("What is the best timing for power?", "Should recommend best practices for what is the best timing for power?"),
    ("What is the best boost level for my engine?", "Should recommend best practices for what is the best boost level for my engine?"),
    ("What is the best nitrous shot size to start with?", "Should recommend best practices for what is the best nitrous shot size to start with?"),
    ("What is the best turbo size for my power goals?", "Should recommend best practices for what is the best turbo size for my power goals?"),
    ("What is the best intercooler setup?", "Should recommend best practices for what is the best intercooler setup?"),
    ("What is the best fuel pressure?", "Should recommend best practices for what is the best fuel pressure?"),
    ("What is the best injector size for my setup?", "Should recommend best practices for what is the best injector size for my setup?"),
    ("What is the best dyno correction to use?", "Should recommend best practices for what is the best dyno correction to use?"),
    ("My engine won't start, what should I do?", "Should provide troubleshooting for my engine won't start, what should i do?"),
    ("Why is my engine won't start?", "Should provide troubleshooting for why is my engine won't start?"),
    ("How do I fix engine won't start?", "Should provide troubleshooting for how do i fix engine won't start?"),
    ("My engine runs rich, what should I do?", "Should provide troubleshooting for my engine runs rich, what should i do?"),
    ("Why is my engine runs rich?", "Should provide troubleshooting for why is my engine runs rich?"),
    ("How do I fix engine runs rich?", "Should provide troubleshooting for how do i fix engine runs rich?"),
    ("My engine runs lean, what should I do?", "Should provide troubleshooting for my engine runs lean, what should i do?"),
    ("Why is my engine runs lean?", "Should provide troubleshooting for why is my engine runs lean?"),
    ("How do I fix engine runs lean?", "Should provide troubleshooting for how do i fix engine runs lean?"),
    ("My engine knocking, what should I do?", "Should provide troubleshooting for my engine knocking, what should i do?"),
    ("Why is my engine knocking?", "Should provide troubleshooting for why is my engine knocking?"),
    ("How do I fix engine knocking?", "Should provide troubleshooting for how do i fix engine knocking?"),
    ("My engine missing, what should I do?", "Should provide troubleshooting for my engine missing, what should i do?"),
    ("Why is my engine missing?", "Should provide troubleshooting for why is my engine missing?"),
    ("How do I fix engine missing?", "Should provide troubleshooting for how do i fix engine missing?"),
    ("My engine won't idle, what should I do?", "Should provide troubleshooting for my engine won't idle, what should i do?"),
    ("Why is my engine won't idle?", "Should provide troubleshooting for why is my engine won't idle?"),
    ("How do I fix engine won't idle?", "Should provide troubleshooting for how do i fix engine won't idle?"),
    ("My engine stalls, what should I do?", "Should provide troubleshooting for my engine stalls, what should i do?"),
    ("Why is my engine stalls?", "Should provide troubleshooting for why is my engine stalls?"),
    ("How do I fix engine stalls?", "Should provide troubleshooting for how do i fix engine stalls?"),
    ("My engine hesitates, what should I do?", "Should provide troubleshooting for my engine hesitates, what should i do?"),
    ("Why is my engine hesitates?", "Should provide troubleshooting for why is my engine hesitates?"),
    ("How do I fix engine hesitates?", "Should provide troubleshooting for how do i fix engine hesitates?"),
    ("My engine backfires, what should I do?", "Should provide troubleshooting for my engine backfires, what should i do?"),
    ("Why is my engine backfires?", "Should provide troubleshooting for why is my engine backfires?"),
    ("How do I fix engine backfires?", "Should provide troubleshooting for how do i fix engine backfires?"),
    ("My engine overheats, what should I do?", "Should provide troubleshooting for my engine overheats, what should i do?"),
    ("Why is my engine overheats?", "Should provide troubleshooting for why is my engine overheats?"),
    ("How do I fix engine overheats?", "Should provide troubleshooting for how do i fix engine overheats?"),
    ("My engine won't make boost, what should I do?", "Should provide troubleshooting for my engine won't make boost, what should i do?"),
    ("Why is my engine won't make boost?", "Should provide troubleshooting for why is my engine won't make boost?"),
    ("How do I fix engine won't make boost?", "Should provide troubleshooting for how do i fix engine won't make boost?"),
    ("My engine boost spikes, what should I do?", "Should provide troubleshooting for my engine boost spikes, what should i do?"),
    ("Why is my engine boost spikes?", "Should provide troubleshooting for why is my engine boost spikes?"),
    ("How do I fix engine boost spikes?", "Should provide troubleshooting for how do i fix engine boost spikes?"),
    ("My engine boost creeps, what should I do?", "Should provide troubleshooting for my engine boost creeps, what should i do?"),
    ("Why is my engine boost creeps?", "Should provide troubleshooting for why is my engine boost creeps?"),
    ("How do I fix engine boost creeps?", "Should provide troubleshooting for how do i fix engine boost creeps?"),
    ("My engine turbo surging, what should I do?", "Should provide troubleshooting for my engine turbo surging, what should i do?"),
    ("Why is my engine turbo surging?", "Should provide troubleshooting for why is my engine turbo surging?"),
    ("How do I fix engine turbo surging?", "Should provide troubleshooting for how do i fix engine turbo surging?"),
    ("My engine nitrous won't work, what should I do?", "Should provide troubleshooting for my engine nitrous won't work, what should i do?"),
    ("Why is my engine nitrous won't work?", "Should provide troubleshooting for why is my engine nitrous won't work?"),
    ("How do I fix engine nitrous won't work?", "Should provide troubleshooting for how do i fix engine nitrous won't work?"),
    ("My engine nitrous backfire, what should I do?", "Should provide troubleshooting for my engine nitrous backfire, what should i do?"),
    ("Why is my engine nitrous backfire?", "Should provide troubleshooting for why is my engine nitrous backfire?"),
    ("How do I fix engine nitrous backfire?", "Should provide troubleshooting for how do i fix engine nitrous backfire?"),
    ("My engine low bottle pressure, what should I do?", "Should provide troubleshooting for my engine low bottle pressure, what should i do?"),
    ("Why is my engine low bottle pressure?", "Should provide troubleshooting for why is my engine low bottle pressure?"),
    ("How do I fix engine low bottle pressure?", "Should provide troubleshooting for how do i fix engine low bottle pressure?"),
    ("My engine won't connect, what should I do?", "Should provide troubleshooting for my engine won't connect, what should i do?"),
    ("Why is my engine won't connect?", "Should provide troubleshooting for why is my engine won't connect?"),
    ("How do I fix engine won't connect?", "Should provide troubleshooting for how do i fix engine won't connect?"),
    ("My engine tune won't load, what should I do?", "Should provide troubleshooting for my engine tune won't load, what should i do?"),
    ("Why is my engine tune won't load?", "Should provide troubleshooting for why is my engine tune won't load?"),
    ("How do I fix engine tune won't load?", "Should provide troubleshooting for how do i fix engine tune won't load?"),
    ("My engine calibration error, what should I do?", "Should provide troubleshooting for my engine calibration error, what should i do?"),
    ("Why is my engine calibration error?", "Should provide troubleshooting for why is my engine calibration error?"),
    ("How do I fix engine calibration error?", "Should provide troubleshooting for how do i fix engine calibration error?"),
    ("My engine sensor error, what should I do?", "Should provide troubleshooting for my engine sensor error, what should i do?"),
    ("Why is my engine sensor error?", "Should provide troubleshooting for why is my engine sensor error?"),
    ("How do I fix engine sensor error?", "Should provide troubleshooting for how do i fix engine sensor error?"),
    ("My engine injector problem, what should I do?", "Should provide troubleshooting for my engine injector problem, what should i do?"),
    ("Why is my engine injector problem?", "Should provide troubleshooting for why is my engine injector problem?"),
    ("How do I fix engine injector problem?", "Should provide troubleshooting for how do i fix engine injector problem?"),
    ("My engine fuel pressure low, what should I do?", "Should provide troubleshooting for my engine fuel pressure low, what should i do?"),
    ("Why is my engine fuel pressure low?", "Should provide troubleshooting for why is my engine fuel pressure low?"),
    ("How do I fix engine fuel pressure low?", "Should provide troubleshooting for how do i fix engine fuel pressure low?"),
    ("My engine dyno numbers low, what should I do?", "Should provide troubleshooting for my engine dyno numbers low, what should i do?"),
    ("Why is my engine dyno numbers low?", "Should provide troubleshooting for why is my engine dyno numbers low?"),
    ("How do I fix engine dyno numbers low?", "Should provide troubleshooting for how do i fix engine dyno numbers low?"),
    ("My engine inconsistent dyno results, what should I do?", "Should provide troubleshooting for my engine inconsistent dyno results, what should i do?"),
    ("Why is my engine inconsistent dyno results?", "Should provide troubleshooting for why is my engine inconsistent dyno results?"),
    ("How do I fix engine inconsistent dyno results?", "Should provide troubleshooting for how do i fix engine inconsistent dyno results?"),
    ("My engine virtual dyno inaccurate, what should I do?", "Should provide troubleshooting for my engine virtual dyno inaccurate, what should i do?"),
    ("Why is my engine virtual dyno inaccurate?", "Should provide troubleshooting for why is my engine virtual dyno inaccurate?"),
    ("How do I fix engine virtual dyno inaccurate?", "Should provide troubleshooting for how do i fix engine virtual dyno inaccurate?"),
    ("My EFI won't start, what should I do?", "Should provide troubleshooting for my efi won't start, what should i do?"),
    ("Why is my EFI won't start?", "Should provide troubleshooting for why is my efi won't start?"),
    ("How do I fix EFI won't start?", "Should provide troubleshooting for how do i fix efi won't start?"),
    ("My EFI runs rich, what should I do?", "Should provide troubleshooting for my efi runs rich, what should i do?"),
    ("Why is my EFI runs rich?", "Should provide troubleshooting for why is my efi runs rich?"),
    ("How do I fix EFI runs rich?", "Should provide troubleshooting for how do i fix efi runs rich?"),
    ("My EFI runs lean, what should I do?", "Should provide troubleshooting for my efi runs lean, what should i do?"),
    ("Why is my EFI runs lean?", "Should provide troubleshooting for why is my efi runs lean?"),
    ("How do I fix EFI runs lean?", "Should provide troubleshooting for how do i fix efi runs lean?"),
    ("My EFI knocking, what should I do?", "Should provide troubleshooting for my efi knocking, what should i do?"),
    ("Why is my EFI knocking?", "Should provide troubleshooting for why is my efi knocking?"),
    ("How do I fix EFI knocking?", "Should provide troubleshooting for how do i fix efi knocking?"),
    ("My EFI missing, what should I do?", "Should provide troubleshooting for my efi missing, what should i do?"),
    ("Why is my EFI missing?", "Should provide troubleshooting for why is my efi missing?"),
    ("How do I fix EFI missing?", "Should provide troubleshooting for how do i fix efi missing?"),
    ("My EFI won't idle, what should I do?", "Should provide troubleshooting for my efi won't idle, what should i do?"),
    ("Why is my EFI won't idle?", "Should provide troubleshooting for why is my efi won't idle?"),
    ("How do I fix EFI won't idle?", "Should provide troubleshooting for how do i fix efi won't idle?"),
    ("My EFI stalls, what should I do?", "Should provide troubleshooting for my efi stalls, what should i do?"),
    ("Why is my EFI stalls?", "Should provide troubleshooting for why is my efi stalls?"),
    ("How do I fix EFI stalls?", "Should provide troubleshooting for how do i fix efi stalls?"),
    ("My EFI hesitates, what should I do?", "Should provide troubleshooting for my efi hesitates, what should i do?"),
    ("Why is my EFI hesitates?", "Should provide troubleshooting for why is my efi hesitates?"),
    ("How do I fix EFI hesitates?", "Should provide troubleshooting for how do i fix efi hesitates?"),
    ("My EFI backfires, what should I do?", "Should provide troubleshooting for my efi backfires, what should i do?"),
    ("Why is my EFI backfires?", "Should provide troubleshooting for why is my efi backfires?"),
    ("How do I fix EFI backfires?", "Should provide troubleshooting for how do i fix efi backfires?"),
    ("My EFI overheats, what should I do?", "Should provide troubleshooting for my efi overheats, what should i do?"),
    ("Why is my EFI overheats?", "Should provide troubleshooting for why is my efi overheats?"),
    ("How do I fix EFI overheats?", "Should provide troubleshooting for how do i fix efi overheats?"),
    ("My EFI won't make boost, what should I do?", "Should provide troubleshooting for my efi won't make boost, what should i do?"),
    ("Why is my EFI won't make boost?", "Should provide troubleshooting for why is my efi won't make boost?"),
    ("How do I fix EFI won't make boost?", "Should provide troubleshooting for how do i fix efi won't make boost?"),
    ("My EFI boost spikes, what should I do?", "Should provide troubleshooting for my efi boost spikes, what should i do?"),
    ("Why is my EFI boost spikes?", "Should provide troubleshooting for why is my efi boost spikes?"),
    ("How do I fix EFI boost spikes?", "Should provide troubleshooting for how do i fix efi boost spikes?"),
    ("My EFI boost creeps, what should I do?", "Should provide troubleshooting for my efi boost creeps, what should i do?"),
    ("Why is my EFI boost creeps?", "Should provide troubleshooting for why is my efi boost creeps?"),
    ("How do I fix EFI boost creeps?", "Should provide troubleshooting for how do i fix efi boost creeps?"),
    ("My EFI turbo surging, what should I do?", "Should provide troubleshooting for my efi turbo surging, what should i do?"),
    ("Why is my EFI turbo surging?", "Should provide troubleshooting for why is my efi turbo surging?"),
    ("How do I fix EFI turbo surging?", "Should provide troubleshooting for how do i fix efi turbo surging?"),
    ("My EFI nitrous won't work, what should I do?", "Should provide troubleshooting for my efi nitrous won't work, what should i do?"),
    ("Why is my EFI nitrous won't work?", "Should provide troubleshooting for why is my efi nitrous won't work?"),
    ("How do I fix EFI nitrous won't work?", "Should provide troubleshooting for how do i fix efi nitrous won't work?"),
    ("My EFI nitrous backfire, what should I do?", "Should provide troubleshooting for my efi nitrous backfire, what should i do?"),
    ("Why is my EFI nitrous backfire?", "Should provide troubleshooting for why is my efi nitrous backfire?"),
    ("How do I fix EFI nitrous backfire?", "Should provide troubleshooting for how do i fix efi nitrous backfire?"),
    ("My EFI low bottle pressure, what should I do?", "Should provide troubleshooting for my efi low bottle pressure, what should i do?"),
    ("Why is my EFI low bottle pressure?", "Should provide troubleshooting for why is my efi low bottle pressure?"),
    ("How do I fix EFI low bottle pressure?", "Should provide troubleshooting for how do i fix efi low bottle pressure?"),
    ("My EFI won't connect, what should I do?", "Should provide troubleshooting for my efi won't connect, what should i do?"),
    ("Why is my EFI won't connect?", "Should provide troubleshooting for why is my efi won't connect?"),
    ("How do I fix EFI won't connect?", "Should provide troubleshooting for how do i fix efi won't connect?"),
    ("My EFI tune won't load, what should I do?", "Should provide troubleshooting for my efi tune won't load, what should i do?"),
    ("Why is my EFI tune won't load?", "Should provide troubleshooting for why is my efi tune won't load?"),
    ("How do I fix EFI tune won't load?", "Should provide troubleshooting for how do i fix efi tune won't load?"),
    ("My EFI calibration error, what should I do?", "Should provide troubleshooting for my efi calibration error, what should i do?"),
    ("Why is my EFI calibration error?", "Should provide troubleshooting for why is my efi calibration error?"),
    ("How do I fix EFI calibration error?", "Should provide troubleshooting for how do i fix efi calibration error?"),
    ("My EFI sensor error, what should I do?", "Should provide troubleshooting for my efi sensor error, what should i do?"),
    ("Why is my EFI sensor error?", "Should provide troubleshooting for why is my efi sensor error?"),
    ("How do I fix EFI sensor error?", "Should provide troubleshooting for how do i fix efi sensor error?"),
    ("My EFI injector problem, what should I do?", "Should provide troubleshooting for my efi injector problem, what should i do?"),
    ("Why is my EFI injector problem?", "Should provide troubleshooting for why is my efi injector problem?"),
    ("How do I fix EFI injector problem?", "Should provide troubleshooting for how do i fix efi injector problem?"),
    ("My EFI fuel pressure low, what should I do?", "Should provide troubleshooting for my efi fuel pressure low, what should i do?"),
    ("Why is my EFI fuel pressure low?", "Should provide troubleshooting for why is my efi fuel pressure low?"),
    ("How do I fix EFI fuel pressure low?", "Should provide troubleshooting for how do i fix efi fuel pressure low?"),
    ("My EFI dyno numbers low, what should I do?", "Should provide troubleshooting for my efi dyno numbers low, what should i do?"),
    ("Why is my EFI dyno numbers low?", "Should provide troubleshooting for why is my efi dyno numbers low?"),
    ("How do I fix EFI dyno numbers low?", "Should provide troubleshooting for how do i fix efi dyno numbers low?"),
    ("Calculate horsepower from 300 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 300 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 300 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 300 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 300 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 300 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 300 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 300 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 300 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 300 ft-lb at 7000 rpm"),
    ("Calculate horsepower from 350 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 350 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 350 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 350 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 350 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 350 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 350 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 350 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 350 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 350 ft-lb at 7000 rpm"),
    ("Calculate horsepower from 400 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 400 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 400 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 400 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 400 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 400 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 400 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 400 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 400 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 400 ft-lb at 7000 rpm"),
    ("Calculate horsepower from 450 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 450 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 450 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 450 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 450 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 450 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 450 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 450 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 450 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 450 ft-lb at 7000 rpm"),
    ("Calculate horsepower from 500 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 500 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 500 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 500 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 500 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 500 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 500 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 500 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 500 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 500 ft-lb at 7000 rpm"),
    ("Calculate horsepower from 550 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 550 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 550 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 550 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 550 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 550 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 550 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 550 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 550 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 550 ft-lb at 7000 rpm"),
    ("Calculate horsepower from 600 ft-lb at 5000 RPM", "Should calculate calculate horsepower from 600 ft-lb at 5000 rpm"),
    ("Calculate horsepower from 600 ft-lb at 5500 RPM", "Should calculate calculate horsepower from 600 ft-lb at 5500 rpm"),
    ("Calculate horsepower from 600 ft-lb at 6000 RPM", "Should calculate calculate horsepower from 600 ft-lb at 6000 rpm"),
    ("Calculate horsepower from 600 ft-lb at 6500 RPM", "Should calculate calculate horsepower from 600 ft-lb at 6500 rpm"),
    ("Calculate horsepower from 600 ft-lb at 7000 RPM", "Should calculate calculate horsepower from 600 ft-lb at 7000 rpm"),
    ("Calculate torque from 400 HP at 5000 RPM", "Should calculate calculate torque from 400 hp at 5000 rpm"),
    ("Calculate torque from 400 HP at 5500 RPM", "Should calculate calculate torque from 400 hp at 5500 rpm"),
    ("Calculate torque from 400 HP at 6000 RPM", "Should calculate calculate torque from 400 hp at 6000 rpm"),
    ("Calculate torque from 400 HP at 6500 RPM", "Should calculate calculate torque from 400 hp at 6500 rpm"),
    ("Calculate torque from 400 HP at 7000 RPM", "Should calculate calculate torque from 400 hp at 7000 rpm"),
    ("Calculate torque from 450 HP at 5000 RPM", "Should calculate calculate torque from 450 hp at 5000 rpm"),
    ("Calculate torque from 450 HP at 5500 RPM", "Should calculate calculate torque from 450 hp at 5500 rpm"),
    ("Calculate torque from 450 HP at 6000 RPM", "Should calculate calculate torque from 450 hp at 6000 rpm"),
    ("Calculate torque from 450 HP at 6500 RPM", "Should calculate calculate torque from 450 hp at 6500 rpm"),
    ("Calculate torque from 450 HP at 7000 RPM", "Should calculate calculate torque from 450 hp at 7000 rpm"),
    ("Calculate torque from 500 HP at 5000 RPM", "Should calculate calculate torque from 500 hp at 5000 rpm"),
    ("Calculate torque from 500 HP at 5500 RPM", "Should calculate calculate torque from 500 hp at 5500 rpm"),
    ("Calculate torque from 500 HP at 6000 RPM", "Should calculate calculate torque from 500 hp at 6000 rpm"),
    ("Calculate torque from 500 HP at 6500 RPM", "Should calculate calculate torque from 500 hp at 6500 rpm"),
    ("Calculate torque from 500 HP at 7000 RPM", "Should calculate calculate torque from 500 hp at 7000 rpm"),
    ("Calculate torque from 550 HP at 5000 RPM", "Should calculate calculate torque from 550 hp at 5000 rpm"),
    ("Calculate torque from 550 HP at 5500 RPM", "Should calculate calculate torque from 550 hp at 5500 rpm"),
    ("Calculate torque from 550 HP at 6000 RPM", "Should calculate calculate torque from 550 hp at 6000 rpm"),
    ("Calculate torque from 550 HP at 6500 RPM", "Should calculate calculate torque from 550 hp at 6500 rpm"),
    ("Calculate torque from 550 HP at 7000 RPM", "Should calculate calculate torque from 550 hp at 7000 rpm"),
    ("Calculate torque from 600 HP at 5000 RPM", "Should calculate calculate torque from 600 hp at 5000 rpm"),
    ("Calculate torque from 600 HP at 5500 RPM", "Should calculate calculate torque from 600 hp at 5500 rpm"),
    ("Calculate torque from 600 HP at 6000 RPM", "Should calculate calculate torque from 600 hp at 6000 rpm"),
    ("Calculate torque from 600 HP at 6500 RPM", "Should calculate calculate torque from 600 hp at 6500 rpm"),
    ("Calculate torque from 600 HP at 7000 RPM", "Should calculate calculate torque from 600 hp at 7000 rpm"),
    ("Calculate torque from 650 HP at 5000 RPM", "Should calculate calculate torque from 650 hp at 5000 rpm"),
    ("Calculate torque from 650 HP at 5500 RPM", "Should calculate calculate torque from 650 hp at 5500 rpm"),
    ("Calculate torque from 650 HP at 6000 RPM", "Should calculate calculate torque from 650 hp at 6000 rpm"),
    ("Calculate torque from 650 HP at 6500 RPM", "Should calculate calculate torque from 650 hp at 6500 rpm"),
    ("Calculate torque from 650 HP at 7000 RPM", "Should calculate calculate torque from 650 hp at 7000 rpm"),
    ("Calculate torque from 700 HP at 5000 RPM", "Should calculate calculate torque from 700 hp at 5000 rpm"),
    ("Calculate torque from 700 HP at 5500 RPM", "Should calculate calculate torque from 700 hp at 5500 rpm"),
    ("Calculate torque from 700 HP at 6000 RPM", "Should calculate calculate torque from 700 hp at 6000 rpm"),
    ("Calculate torque from 700 HP at 6500 RPM", "Should calculate calculate torque from 700 hp at 6500 rpm"),
    ("Calculate torque from 700 HP at 7000 RPM", "Should calculate calculate torque from 700 hp at 7000 rpm"),
    ("Convert 5 PSI boost to bar", "Should calculate convert 5 psi boost to bar"),
    ("Convert 10 PSI boost to bar", "Should calculate convert 10 psi boost to bar"),
    ("Convert 15 PSI boost to bar", "Should calculate convert 15 psi boost to bar"),
    ("Convert 20 PSI boost to bar", "Should calculate convert 20 psi boost to bar"),
    ("Convert 25 PSI boost to bar", "Should calculate convert 25 psi boost to bar"),
    ("Convert 30 PSI boost to bar", "Should calculate convert 30 psi boost to bar"),
    ("Convert 0.5 bar boost to PSI", "Should calculate convert 0.5 bar boost to psi"),
    ("Convert 1.0 bar boost to PSI", "Should calculate convert 1.0 bar boost to psi"),
    ("Convert 1.5 bar boost to PSI", "Should calculate convert 1.5 bar boost to psi"),
    ("Convert 2.0 bar boost to PSI", "Should calculate convert 2.0 bar boost to psi"),
    ("Convert 2.5 bar boost to PSI", "Should calculate convert 2.5 bar boost to psi"),
    ("Calculate injector size for 400 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 400 hp, 0.5 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 400 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 400 hp, 0.6 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 400 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 400 hp, 0.65 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 400 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 400 hp, 0.7 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 500 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 500 hp, 0.5 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 500 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 500 hp, 0.6 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 500 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 500 hp, 0.65 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 500 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 500 hp, 0.7 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 600 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 600 hp, 0.5 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 600 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 600 hp, 0.6 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 600 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 600 hp, 0.65 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 600 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 600 hp, 0.7 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 700 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 700 hp, 0.5 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 700 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 700 hp, 0.6 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 700 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 700 hp, 0.65 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 700 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 700 hp, 0.7 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 800 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 800 hp, 0.5 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 800 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 800 hp, 0.6 bsfc, 8 injectors, 80% duty"),
    ("Calculate injector size for 800 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate calculate injector size for 800 hp, 0.65 bsfc, 8 injectors, 80% duty"),
    ("Calculate horsepower from 300 ft-lb at 5000 RPM", "Should calculate HP = (300 × 5000) / 5252"),    ("Calculate horsepower from 300 ft-lb at 5500 RPM", "Should calculate HP = (300 × 5500) / 5252"),    ("Calculate horsepower from 300 ft-lb at 6000 RPM", "Should calculate HP = (300 × 6000) / 5252"),    ("Calculate horsepower from 300 ft-lb at 6500 RPM", "Should calculate HP = (300 × 6500) / 5252"),    ("Calculate horsepower from 300 ft-lb at 7000 RPM", "Should calculate HP = (300 × 7000) / 5252"),    ("Calculate horsepower from 300 ft-lb at 7500 RPM", "Should calculate HP = (300 × 7500) / 5252"),    ("Calculate horsepower from 350 ft-lb at 5000 RPM", "Should calculate HP = (350 × 5000) / 5252"),    ("Calculate horsepower from 350 ft-lb at 5500 RPM", "Should calculate HP = (350 × 5500) / 5252"),    ("Calculate horsepower from 350 ft-lb at 6000 RPM", "Should calculate HP = (350 × 6000) / 5252"),    ("Calculate horsepower from 350 ft-lb at 6500 RPM", "Should calculate HP = (350 × 6500) / 5252"),    ("Calculate horsepower from 350 ft-lb at 7000 RPM", "Should calculate HP = (350 × 7000) / 5252"),    ("Calculate horsepower from 350 ft-lb at 7500 RPM", "Should calculate HP = (350 × 7500) / 5252"),    ("Calculate horsepower from 400 ft-lb at 5000 RPM", "Should calculate HP = (400 × 5000) / 5252"),    ("Calculate horsepower from 400 ft-lb at 5500 RPM", "Should calculate HP = (400 × 5500) / 5252"),    ("Calculate horsepower from 400 ft-lb at 6000 RPM", "Should calculate HP = (400 × 6000) / 5252"),    ("Calculate horsepower from 400 ft-lb at 6500 RPM", "Should calculate HP = (400 × 6500) / 5252"),    ("Calculate horsepower from 400 ft-lb at 7000 RPM", "Should calculate HP = (400 × 7000) / 5252"),    ("Calculate horsepower from 400 ft-lb at 7500 RPM", "Should calculate HP = (400 × 7500) / 5252"),    ("Calculate horsepower from 450 ft-lb at 5000 RPM", "Should calculate HP = (450 × 5000) / 5252"),    ("Calculate horsepower from 450 ft-lb at 5500 RPM", "Should calculate HP = (450 × 5500) / 5252"),    ("Calculate horsepower from 450 ft-lb at 6000 RPM", "Should calculate HP = (450 × 6000) / 5252"),    ("Calculate horsepower from 450 ft-lb at 6500 RPM", "Should calculate HP = (450 × 6500) / 5252"),    ("Calculate horsepower from 450 ft-lb at 7000 RPM", "Should calculate HP = (450 × 7000) / 5252"),    ("Calculate horsepower from 450 ft-lb at 7500 RPM", "Should calculate HP = (450 × 7500) / 5252"),    ("Calculate horsepower from 500 ft-lb at 5000 RPM", "Should calculate HP = (500 × 5000) / 5252"),    ("Calculate horsepower from 500 ft-lb at 5500 RPM", "Should calculate HP = (500 × 5500) / 5252"),    ("Calculate horsepower from 500 ft-lb at 6000 RPM", "Should calculate HP = (500 × 6000) / 5252"),    ("Calculate horsepower from 500 ft-lb at 6500 RPM", "Should calculate HP = (500 × 6500) / 5252"),    ("Calculate horsepower from 500 ft-lb at 7000 RPM", "Should calculate HP = (500 × 7000) / 5252"),    ("Calculate horsepower from 500 ft-lb at 7500 RPM", "Should calculate HP = (500 × 7500) / 5252"),    ("Calculate horsepower from 550 ft-lb at 5000 RPM", "Should calculate HP = (550 × 5000) / 5252"),    ("Calculate horsepower from 550 ft-lb at 5500 RPM", "Should calculate HP = (550 × 5500) / 5252"),    ("Calculate horsepower from 550 ft-lb at 6000 RPM", "Should calculate HP = (550 × 6000) / 5252"),    ("Calculate horsepower from 550 ft-lb at 6500 RPM", "Should calculate HP = (550 × 6500) / 5252"),    ("Calculate horsepower from 550 ft-lb at 7000 RPM", "Should calculate HP = (550 × 7000) / 5252"),    ("Calculate horsepower from 550 ft-lb at 7500 RPM", "Should calculate HP = (550 × 7500) / 5252"),    ("Calculate horsepower from 600 ft-lb at 5000 RPM", "Should calculate HP = (600 × 5000) / 5252"),    ("Calculate horsepower from 600 ft-lb at 5500 RPM", "Should calculate HP = (600 × 5500) / 5252"),    ("Calculate horsepower from 600 ft-lb at 6000 RPM", "Should calculate HP = (600 × 6000) / 5252"),    ("Calculate horsepower from 600 ft-lb at 6500 RPM", "Should calculate HP = (600 × 6500) / 5252"),    ("Calculate horsepower from 600 ft-lb at 7000 RPM", "Should calculate HP = (600 × 7000) / 5252"),    ("Calculate horsepower from 600 ft-lb at 7500 RPM", "Should calculate HP = (600 × 7500) / 5252"),    ("Calculate horsepower from 650 ft-lb at 5000 RPM", "Should calculate HP = (650 × 5000) / 5252"),    ("Calculate horsepower from 650 ft-lb at 5500 RPM", "Should calculate HP = (650 × 5500) / 5252"),    ("Calculate horsepower from 650 ft-lb at 6000 RPM", "Should calculate HP = (650 × 6000) / 5252"),    ("Calculate horsepower from 650 ft-lb at 6500 RPM", "Should calculate HP = (650 × 6500) / 5252"),    ("Calculate horsepower from 650 ft-lb at 7000 RPM", "Should calculate HP = (650 × 7000) / 5252"),    ("Calculate horsepower from 650 ft-lb at 7500 RPM", "Should calculate HP = (650 × 7500) / 5252"),    ("Calculate horsepower from 700 ft-lb at 5000 RPM", "Should calculate HP = (700 × 5000) / 5252"),    ("Calculate horsepower from 700 ft-lb at 5500 RPM", "Should calculate HP = (700 × 5500) / 5252"),    ("Calculate horsepower from 700 ft-lb at 6000 RPM", "Should calculate HP = (700 × 6000) / 5252"),    ("Calculate horsepower from 700 ft-lb at 6500 RPM", "Should calculate HP = (700 × 6500) / 5252"),    ("Calculate horsepower from 700 ft-lb at 7000 RPM", "Should calculate HP = (700 × 7000) / 5252"),    ("Calculate horsepower from 700 ft-lb at 7500 RPM", "Should calculate HP = (700 × 7500) / 5252"),    ("Calculate torque from 400 HP at 5000 RPM", "Should calculate T = (400 × 5252) / 5000"),    ("Calculate torque from 400 HP at 5500 RPM", "Should calculate T = (400 × 5252) / 5500"),    ("Calculate torque from 400 HP at 6000 RPM", "Should calculate T = (400 × 5252) / 6000"),    ("Calculate torque from 400 HP at 6500 RPM", "Should calculate T = (400 × 5252) / 6500"),    ("Calculate torque from 400 HP at 7000 RPM", "Should calculate T = (400 × 5252) / 7000"),    ("Calculate torque from 450 HP at 5000 RPM", "Should calculate T = (450 × 5252) / 5000"),    ("Calculate torque from 450 HP at 5500 RPM", "Should calculate T = (450 × 5252) / 5500"),    ("Calculate torque from 450 HP at 6000 RPM", "Should calculate T = (450 × 5252) / 6000"),    ("Calculate torque from 450 HP at 6500 RPM", "Should calculate T = (450 × 5252) / 6500"),    ("Calculate torque from 450 HP at 7000 RPM", "Should calculate T = (450 × 5252) / 7000"),    ("Calculate torque from 500 HP at 5000 RPM", "Should calculate T = (500 × 5252) / 5000"),    ("Calculate torque from 500 HP at 5500 RPM", "Should calculate T = (500 × 5252) / 5500"),    ("Calculate torque from 500 HP at 6000 RPM", "Should calculate T = (500 × 5252) / 6000"),    ("Calculate torque from 500 HP at 6500 RPM", "Should calculate T = (500 × 5252) / 6500"),    ("Calculate torque from 500 HP at 7000 RPM", "Should calculate T = (500 × 5252) / 7000"),    ("Calculate torque from 550 HP at 5000 RPM", "Should calculate T = (550 × 5252) / 5000"),    ("Calculate torque from 550 HP at 5500 RPM", "Should calculate T = (550 × 5252) / 5500"),    ("Calculate torque from 550 HP at 6000 RPM", "Should calculate T = (550 × 5252) / 6000"),    ("Calculate torque from 550 HP at 6500 RPM", "Should calculate T = (550 × 5252) / 6500"),    ("Calculate torque from 550 HP at 7000 RPM", "Should calculate T = (550 × 5252) / 7000"),    ("Calculate torque from 600 HP at 5000 RPM", "Should calculate T = (600 × 5252) / 5000"),    ("Calculate torque from 600 HP at 5500 RPM", "Should calculate T = (600 × 5252) / 5500"),    ("Calculate torque from 600 HP at 6000 RPM", "Should calculate T = (600 × 5252) / 6000"),    ("Calculate torque from 600 HP at 6500 RPM", "Should calculate T = (600 × 5252) / 6500"),    ("Calculate torque from 600 HP at 7000 RPM", "Should calculate T = (600 × 5252) / 7000"),    ("Calculate torque from 650 HP at 5000 RPM", "Should calculate T = (650 × 5252) / 5000"),    ("Calculate torque from 650 HP at 5500 RPM", "Should calculate T = (650 × 5252) / 5500"),    ("Calculate torque from 650 HP at 6000 RPM", "Should calculate T = (650 × 5252) / 6000"),    ("Calculate torque from 650 HP at 6500 RPM", "Should calculate T = (650 × 5252) / 6500"),    ("Calculate torque from 650 HP at 7000 RPM", "Should calculate T = (650 × 5252) / 7000"),    ("Calculate torque from 700 HP at 5000 RPM", "Should calculate T = (700 × 5252) / 5000"),    ("Calculate torque from 700 HP at 5500 RPM", "Should calculate T = (700 × 5252) / 5500"),    ("Calculate torque from 700 HP at 6000 RPM", "Should calculate T = (700 × 5252) / 6000"),    ("Calculate torque from 700 HP at 6500 RPM", "Should calculate T = (700 × 5252) / 6500"),    ("Calculate torque from 700 HP at 7000 RPM", "Should calculate T = (700 × 5252) / 7000"),    ("Calculate torque from 750 HP at 5000 RPM", "Should calculate T = (750 × 5252) / 5000"),    ("Calculate torque from 750 HP at 5500 RPM", "Should calculate T = (750 × 5252) / 5500"),    ("Calculate torque from 750 HP at 6000 RPM", "Should calculate T = (750 × 5252) / 6000"),    ("Calculate torque from 750 HP at 6500 RPM", "Should calculate T = (750 × 5252) / 6500"),    ("Calculate torque from 750 HP at 7000 RPM", "Should calculate T = (750 × 5252) / 7000"),    ("Calculate torque from 800 HP at 5000 RPM", "Should calculate T = (800 × 5252) / 5000"),    ("Calculate torque from 800 HP at 5500 RPM", "Should calculate T = (800 × 5252) / 5500"),    ("Calculate torque from 800 HP at 6000 RPM", "Should calculate T = (800 × 5252) / 6000"),    ("Calculate torque from 800 HP at 6500 RPM", "Should calculate T = (800 × 5252) / 6500"),    ("Calculate torque from 800 HP at 7000 RPM", "Should calculate T = (800 × 5252) / 7000"),    ("Convert 5 PSI boost to bar", "Should calculate 5 / 14.5 = 0.34 bar"),    ("Convert 7 PSI boost to bar", "Should calculate 7 / 14.5 = 0.48 bar"),    ("Convert 10 PSI boost to bar", "Should calculate 10 / 14.5 = 0.69 bar"),    ("Convert 12 PSI boost to bar", "Should calculate 12 / 14.5 = 0.83 bar"),    ("Convert 15 PSI boost to bar", "Should calculate 15 / 14.5 = 1.03 bar"),    ("Convert 18 PSI boost to bar", "Should calculate 18 / 14.5 = 1.24 bar"),    ("Convert 20 PSI boost to bar", "Should calculate 20 / 14.5 = 1.38 bar"),    ("Convert 22 PSI boost to bar", "Should calculate 22 / 14.5 = 1.52 bar"),    ("Convert 25 PSI boost to bar", "Should calculate 25 / 14.5 = 1.72 bar"),    ("Convert 28 PSI boost to bar", "Should calculate 28 / 14.5 = 1.93 bar"),    ("Convert 30 PSI boost to bar", "Should calculate 30 / 14.5 = 2.07 bar"),    ("Convert 35 PSI boost to bar", "Should calculate 35 / 14.5 = 2.41 bar"),    ("Convert 0.3 bar boost to PSI", "Should calculate 0.3 × 14.5 = 4.3 PSI"),    ("Convert 0.5 bar boost to PSI", "Should calculate 0.5 × 14.5 = 7.2 PSI"),    ("Convert 0.7 bar boost to PSI", "Should calculate 0.7 × 14.5 = 10.1 PSI"),    ("Convert 1.0 bar boost to PSI", "Should calculate 1.0 × 14.5 = 14.5 PSI"),    ("Convert 1.2 bar boost to PSI", "Should calculate 1.2 × 14.5 = 17.4 PSI"),    ("Convert 1.5 bar boost to PSI", "Should calculate 1.5 × 14.5 = 21.8 PSI"),    ("Convert 1.8 bar boost to PSI", "Should calculate 1.8 × 14.5 = 26.1 PSI"),    ("Convert 2.0 bar boost to PSI", "Should calculate 2.0 × 14.5 = 29.0 PSI"),    ("Convert 2.2 bar boost to PSI", "Should calculate 2.2 × 14.5 = 31.9 PSI"),    ("Convert 2.5 bar boost to PSI", "Should calculate 2.5 × 14.5 = 36.2 PSI"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 66.7 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 62.5 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 58.8 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 44.4 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 41.7 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 39.2 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 33.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 31.2 lb/hr"),    ("Calculate injector size for 400 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 29.4 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 73.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 68.8 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 64.7 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 48.9 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 45.8 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 43.1 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 36.7 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 34.4 lb/hr"),    ("Calculate injector size for 400 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 32.4 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 80.0 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 70.6 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 53.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 50.0 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 47.1 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 40.0 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 37.5 lb/hr"),    ("Calculate injector size for 400 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 35.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 86.7 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 81.2 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 76.5 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 57.8 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 54.2 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 51.0 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 43.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 40.6 lb/hr"),    ("Calculate injector size for 400 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 38.2 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 93.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 87.5 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 82.4 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 62.2 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 58.3 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 54.9 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 46.7 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 43.8 lb/hr"),    ("Calculate injector size for 400 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 41.2 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 70.3 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 66.2 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 50.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 46.9 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 44.1 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 37.5 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 35.2 lb/hr"),    ("Calculate injector size for 450 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 33.1 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 82.5 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 77.3 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 72.8 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 55.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 51.6 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 48.5 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 41.3 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 38.7 lb/hr"),    ("Calculate injector size for 450 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 36.4 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 90.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 84.4 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 79.4 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 60.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 56.2 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 52.9 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 45.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 42.2 lb/hr"),    ("Calculate injector size for 450 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 39.7 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 97.5 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 91.4 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 86.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 65.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 60.9 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 57.4 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 48.8 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 45.7 lb/hr"),    ("Calculate injector size for 450 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 43.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 105.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 98.4 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 92.6 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 70.0 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 65.6 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 61.8 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 52.5 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 49.2 lb/hr"),    ("Calculate injector size for 450 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 46.3 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 83.3 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 78.1 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 73.5 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 55.6 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 52.1 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 49.0 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 41.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 39.1 lb/hr"),    ("Calculate injector size for 500 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 36.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 91.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 85.9 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 80.9 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 61.1 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 57.3 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 53.9 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 45.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 43.0 lb/hr"),    ("Calculate injector size for 500 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 40.4 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 100.0 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 93.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 88.2 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 66.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 62.5 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 58.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 50.0 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 46.9 lb/hr"),    ("Calculate injector size for 500 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 44.1 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 108.3 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 101.6 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 95.6 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 72.2 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 67.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 63.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 54.2 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 50.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 47.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 116.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 109.4 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 102.9 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 77.8 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 72.9 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 68.6 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 58.3 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 54.7 lb/hr"),    ("Calculate injector size for 500 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 51.5 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 91.7 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 85.9 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 80.9 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 61.1 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 57.3 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 53.9 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 45.8 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 43.0 lb/hr"),    ("Calculate injector size for 550 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 40.4 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 100.8 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 94.5 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 89.0 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 67.2 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 63.0 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 59.3 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 50.4 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 47.3 lb/hr"),    ("Calculate injector size for 550 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 44.5 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 110.0 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 103.1 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 97.1 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 73.3 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 68.7 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 64.7 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 55.0 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 51.6 lb/hr"),    ("Calculate injector size for 550 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 48.5 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 119.2 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 111.7 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 105.1 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 79.4 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 74.5 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 70.1 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 59.6 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 55.9 lb/hr"),    ("Calculate injector size for 550 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 52.6 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 128.3 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 120.3 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 113.2 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 85.6 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 80.2 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 75.5 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 64.2 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 60.2 lb/hr"),    ("Calculate injector size for 550 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 56.6 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 100.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 93.8 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 88.2 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 66.7 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 62.5 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 58.8 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 50.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 46.9 lb/hr"),    ("Calculate injector size for 600 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 44.1 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 110.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 103.1 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 97.1 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 73.3 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 68.7 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 64.7 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 55.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 51.6 lb/hr"),    ("Calculate injector size for 600 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 48.5 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 120.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 112.5 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 105.9 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 80.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 70.6 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 60.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 56.2 lb/hr"),    ("Calculate injector size for 600 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 52.9 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 130.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 121.9 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 114.7 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 86.7 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 81.2 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 76.5 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 65.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 60.9 lb/hr"),    ("Calculate injector size for 600 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 57.4 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 140.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 131.2 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 123.5 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 93.3 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 87.5 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 82.4 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 70.0 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 65.6 lb/hr"),    ("Calculate injector size for 600 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 61.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 108.3 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 101.6 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 95.6 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 72.2 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 67.7 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 63.7 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 54.2 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 50.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 47.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 119.2 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 111.7 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 105.1 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 79.4 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 74.5 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 70.1 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 59.6 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 55.9 lb/hr"),    ("Calculate injector size for 650 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 52.6 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 130.0 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 121.9 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 114.7 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 86.7 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 81.2 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 76.5 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 65.0 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 60.9 lb/hr"),    ("Calculate injector size for 650 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 57.4 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 140.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 132.0 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 124.3 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 93.9 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 88.0 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 82.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 70.4 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 66.0 lb/hr"),    ("Calculate injector size for 650 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 62.1 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 151.7 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 142.2 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 133.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 101.1 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 94.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 89.2 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 75.8 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 71.1 lb/hr"),    ("Calculate injector size for 650 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 66.9 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 116.7 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 109.4 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 102.9 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 77.8 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 72.9 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 68.6 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 58.3 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 54.7 lb/hr"),    ("Calculate injector size for 700 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 51.5 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 128.3 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 120.3 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 113.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 85.6 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 80.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 75.5 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 64.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 60.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 56.6 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 140.0 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 131.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 123.5 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 93.3 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 87.5 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 82.4 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 70.0 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 65.6 lb/hr"),    ("Calculate injector size for 700 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 61.8 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 151.7 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 142.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 133.8 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 101.1 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 94.8 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 89.2 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 75.8 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 71.1 lb/hr"),    ("Calculate injector size for 700 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 66.9 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 163.3 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 153.1 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 144.1 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 108.9 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 102.1 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 96.1 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 81.7 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 76.6 lb/hr"),    ("Calculate injector size for 700 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 72.1 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 125.0 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 117.2 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 110.3 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 83.3 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 78.1 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 73.5 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 62.5 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 58.6 lb/hr"),    ("Calculate injector size for 750 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 55.1 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 137.5 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 128.9 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 121.3 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 91.7 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 85.9 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 80.9 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 68.8 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 64.5 lb/hr"),    ("Calculate injector size for 750 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 60.7 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 150.0 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 140.6 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 132.4 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 100.0 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 93.7 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 88.2 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 70.3 lb/hr"),    ("Calculate injector size for 750 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 66.2 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 162.5 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 152.3 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 143.4 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 108.3 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 101.6 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 95.6 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 81.2 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 76.2 lb/hr"),    ("Calculate injector size for 750 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 71.7 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 175.0 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 164.1 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 154.4 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 116.7 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 109.4 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 102.9 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 87.5 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 82.0 lb/hr"),    ("Calculate injector size for 750 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 77.2 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 133.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 125.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 117.6 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 88.9 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 83.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 78.4 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 66.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 62.5 lb/hr"),    ("Calculate injector size for 800 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 58.8 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 146.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 137.5 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 129.4 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 97.8 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 91.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 86.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 73.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 68.8 lb/hr"),    ("Calculate injector size for 800 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 64.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 160.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 150.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 141.2 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 106.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 100.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 94.1 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 80.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 70.6 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 173.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 162.5 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 152.9 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 115.6 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 108.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 102.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 86.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 81.2 lb/hr"),    ("Calculate injector size for 800 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 76.5 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 186.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 175.0 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 164.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 124.4 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 116.7 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 109.8 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 93.3 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 87.5 lb/hr"),    ("Calculate injector size for 800 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 82.4 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 141.7 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 132.8 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 125.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 94.4 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 88.5 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 83.3 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 70.8 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 66.4 lb/hr"),    ("Calculate injector size for 850 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 62.5 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 155.8 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 146.1 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 137.5 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 103.9 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 97.4 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 91.7 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 77.9 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 73.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 68.8 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 170.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 159.4 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 150.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 113.3 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 106.2 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 100.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 85.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 79.7 lb/hr"),    ("Calculate injector size for 850 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 184.2 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 172.7 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 162.5 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 122.8 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 115.1 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 108.3 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 92.1 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 86.3 lb/hr"),    ("Calculate injector size for 850 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 81.2 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 198.3 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 185.9 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 175.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 132.2 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 124.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 116.7 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 99.2 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 93.0 lb/hr"),    ("Calculate injector size for 850 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 87.5 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 150.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 140.6 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 132.4 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 100.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 93.7 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 88.2 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 75.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 70.3 lb/hr"),    ("Calculate injector size for 900 HP, 0.5 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 66.2 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 165.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 154.7 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 145.6 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 110.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 103.1 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 97.1 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 82.5 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 77.3 lb/hr"),    ("Calculate injector size for 900 HP, 0.55 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 72.8 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 180.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 168.8 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 158.8 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 120.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 112.5 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 105.9 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 90.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 84.4 lb/hr"),    ("Calculate injector size for 900 HP, 0.6 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 79.4 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 195.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 182.8 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 172.1 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 130.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 121.9 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 114.7 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 97.5 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 91.4 lb/hr"),    ("Calculate injector size for 900 HP, 0.65 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 86.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 4 injectors, 75% duty", "Should calculate size ≈ 210.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 4 injectors, 80% duty", "Should calculate size ≈ 196.9 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 4 injectors, 85% duty", "Should calculate size ≈ 185.3 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 6 injectors, 75% duty", "Should calculate size ≈ 140.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 6 injectors, 80% duty", "Should calculate size ≈ 131.2 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 6 injectors, 85% duty", "Should calculate size ≈ 123.5 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 8 injectors, 75% duty", "Should calculate size ≈ 105.0 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 8 injectors, 80% duty", "Should calculate size ≈ 98.4 lb/hr"),    ("Calculate injector size for 900 HP, 0.7 BSFC, 8 injectors, 85% duty", "Should calculate size ≈ 92.6 lb/hr"),    ("Calculate CFM for 300 CID engine at 5000 RPM with 80% VE", "Should calculate CFM ≈ 347"),    ("Calculate CFM for 300 CID engine at 5000 RPM with 85% VE", "Should calculate CFM ≈ 369"),    ("Calculate CFM for 300 CID engine at 5000 RPM with 90% VE", "Should calculate CFM ≈ 391"),    ("Calculate CFM for 300 CID engine at 5000 RPM with 95% VE", "Should calculate CFM ≈ 412"),    ("Calculate CFM for 300 CID engine at 5000 RPM with 100% VE", "Should calculate CFM ≈ 434"),    ("Calculate CFM for 300 CID engine at 5500 RPM with 80% VE", "Should calculate CFM ≈ 382"),    ("Calculate CFM for 300 CID engine at 5500 RPM with 85% VE", "Should calculate CFM ≈ 406"),    ("Calculate CFM for 300 CID engine at 5500 RPM with 90% VE", "Should calculate CFM ≈ 430"),    ("Calculate CFM for 300 CID engine at 5500 RPM with 95% VE", "Should calculate CFM ≈ 454"),    ("Calculate CFM for 300 CID engine at 5500 RPM with 100% VE", "Should calculate CFM ≈ 477"),    ("Calculate CFM for 300 CID engine at 6000 RPM with 80% VE", "Should calculate CFM ≈ 417"),    ("Calculate CFM for 300 CID engine at 6000 RPM with 85% VE", "Should calculate CFM ≈ 443"),    ("Calculate CFM for 300 CID engine at 6000 RPM with 90% VE", "Should calculate CFM ≈ 469"),    ("Calculate CFM for 300 CID engine at 6000 RPM with 95% VE", "Should calculate CFM ≈ 495"),    ("Calculate CFM for 300 CID engine at 6000 RPM with 100% VE", "Should calculate CFM ≈ 521"),    ("Calculate CFM for 300 CID engine at 6500 RPM with 80% VE", "Should calculate CFM ≈ 451"),    ("Calculate CFM for 300 CID engine at 6500 RPM with 85% VE", "Should calculate CFM ≈ 480"),    ("Calculate CFM for 300 CID engine at 6500 RPM with 90% VE", "Should calculate CFM ≈ 508"),    ("Calculate CFM for 300 CID engine at 6500 RPM with 95% VE", "Should calculate CFM ≈ 536"),    ("Calculate CFM for 300 CID engine at 6500 RPM with 100% VE", "Should calculate CFM ≈ 564"),    ("Calculate CFM for 300 CID engine at 7000 RPM with 80% VE", "Should calculate CFM ≈ 486"),    ("Calculate CFM for 300 CID engine at 7000 RPM with 85% VE", "Should calculate CFM ≈ 516"),    ("Calculate CFM for 300 CID engine at 7000 RPM with 90% VE", "Should calculate CFM ≈ 547"),    ("Calculate CFM for 300 CID engine at 7000 RPM with 95% VE", "Should calculate CFM ≈ 577"),    ("Calculate CFM for 300 CID engine at 7000 RPM with 100% VE", "Should calculate CFM ≈ 608"),    ("Calculate CFM for 350 CID engine at 5000 RPM with 80% VE", "Should calculate CFM ≈ 405"),    ("Calculate CFM for 350 CID engine at 5000 RPM with 85% VE", "Should calculate CFM ≈ 430"),    ("Calculate CFM for 350 CID engine at 5000 RPM with 90% VE", "Should calculate CFM ≈ 456"),    ("Calculate CFM for 350 CID engine at 5000 RPM with 95% VE", "Should calculate CFM ≈ 481"),    ("Calculate CFM for 350 CID engine at 5000 RPM with 100% VE", "Should calculate CFM ≈ 506"),    ("Calculate CFM for 350 CID engine at 5500 RPM with 80% VE", "Should calculate CFM ≈ 446"),    ("Calculate CFM for 350 CID engine at 5500 RPM with 85% VE", "Should calculate CFM ≈ 473"),    ("Calculate CFM for 350 CID engine at 5500 RPM with 90% VE", "Should calculate CFM ≈ 501"),    ("Calculate CFM for 350 CID engine at 5500 RPM with 95% VE", "Should calculate CFM ≈ 529"),    ("Calculate CFM for 350 CID engine at 5500 RPM with 100% VE", "Should calculate CFM ≈ 557"),    ("Calculate CFM for 350 CID engine at 6000 RPM with 80% VE", "Should calculate CFM ≈ 486"),    ("Calculate CFM for 350 CID engine at 6000 RPM with 85% VE", "Should calculate CFM ≈ 516"),    ("Calculate CFM for 350 CID engine at 6000 RPM with 90% VE", "Should calculate CFM ≈ 547"),    ("Calculate CFM for 350 CID engine at 6000 RPM with 95% VE", "Should calculate CFM ≈ 577"),    ("Calculate CFM for 350 CID engine at 6000 RPM with 100% VE", "Should calculate CFM ≈ 608"),    ("Calculate CFM for 350 CID engine at 6500 RPM with 80% VE", "Should calculate CFM ≈ 527"),    ("Calculate CFM for 350 CID engine at 6500 RPM with 85% VE", "Should calculate CFM ≈ 560"),    ("Calculate CFM for 350 CID engine at 6500 RPM with 90% VE", "Should calculate CFM ≈ 592"),    ("Calculate CFM for 350 CID engine at 6500 RPM with 95% VE", "Should calculate CFM ≈ 625"),    ("Calculate CFM for 350 CID engine at 6500 RPM with 100% VE", "Should calculate CFM ≈ 658"),    ("Calculate CFM for 350 CID engine at 7000 RPM with 80% VE", "Should calculate CFM ≈ 567"),    ("Calculate CFM for 350 CID engine at 7000 RPM with 85% VE", "Should calculate CFM ≈ 603"),    ("Calculate CFM for 350 CID engine at 7000 RPM with 90% VE", "Should calculate CFM ≈ 638"),    ("Calculate CFM for 350 CID engine at 7000 RPM with 95% VE", "Should calculate CFM ≈ 673"),    ("Calculate CFM for 350 CID engine at 7000 RPM with 100% VE", "Should calculate CFM ≈ 709"),    ("Calculate CFM for 400 CID engine at 5000 RPM with 80% VE", "Should calculate CFM ≈ 463"),    ("Calculate CFM for 400 CID engine at 5000 RPM with 85% VE", "Should calculate CFM ≈ 492"),    ("Calculate CFM for 400 CID engine at 5000 RPM with 90% VE", "Should calculate CFM ≈ 521"),    ("Calculate CFM for 400 CID engine at 5000 RPM with 95% VE", "Should calculate CFM ≈ 550"),    ("Calculate CFM for 400 CID engine at 5000 RPM with 100% VE", "Should calculate CFM ≈ 579"),    ("Calculate CFM for 400 CID engine at 5500 RPM with 80% VE", "Should calculate CFM ≈ 509"),    ("Calculate CFM for 400 CID engine at 5500 RPM with 85% VE", "Should calculate CFM ≈ 541"),    ("Calculate CFM for 400 CID engine at 5500 RPM with 90% VE", "Should calculate CFM ≈ 573"),    ("Calculate CFM for 400 CID engine at 5500 RPM with 95% VE", "Should calculate CFM ≈ 605"),    ("Calculate CFM for 400 CID engine at 5500 RPM with 100% VE", "Should calculate CFM ≈ 637"),    ("Calculate CFM for 400 CID engine at 6000 RPM with 80% VE", "Should calculate CFM ≈ 556"),    ("Calculate CFM for 400 CID engine at 6000 RPM with 85% VE", "Should calculate CFM ≈ 590"),    ("Calculate CFM for 400 CID engine at 6000 RPM with 90% VE", "Should calculate CFM ≈ 625"),    ("Calculate CFM for 400 CID engine at 6000 RPM with 95% VE", "Should calculate CFM ≈ 660"),    ("Calculate CFM for 400 CID engine at 6000 RPM with 100% VE", "Should calculate CFM ≈ 694"),    ("Calculate CFM for 400 CID engine at 6500 RPM with 80% VE", "Should calculate CFM ≈ 602"),    ("Calculate CFM for 400 CID engine at 6500 RPM with 85% VE", "Should calculate CFM ≈ 639"),    ("Calculate CFM for 400 CID engine at 6500 RPM with 90% VE", "Should calculate CFM ≈ 677"),    ("Calculate CFM for 400 CID engine at 6500 RPM with 95% VE", "Should calculate CFM ≈ 715"),    ("Calculate CFM for 400 CID engine at 6500 RPM with 100% VE", "Should calculate CFM ≈ 752"),    ("Calculate CFM for 400 CID engine at 7000 RPM with 80% VE", "Should calculate CFM ≈ 648"),    ("Calculate CFM for 400 CID engine at 7000 RPM with 85% VE", "Should calculate CFM ≈ 689"),    ("Calculate CFM for 400 CID engine at 7000 RPM with 90% VE", "Should calculate CFM ≈ 729"),    ("Calculate CFM for 400 CID engine at 7000 RPM with 95% VE", "Should calculate CFM ≈ 770"),    ("Calculate CFM for 400 CID engine at 7000 RPM with 100% VE", "Should calculate CFM ≈ 810"),    ("Calculate CFM for 450 CID engine at 5000 RPM with 80% VE", "Should calculate CFM ≈ 521"),    ("Calculate CFM for 450 CID engine at 5000 RPM with 85% VE", "Should calculate CFM ≈ 553"),    ("Calculate CFM for 450 CID engine at 5000 RPM with 90% VE", "Should calculate CFM ≈ 586"),    ("Calculate CFM for 450 CID engine at 5000 RPM with 95% VE", "Should calculate CFM ≈ 618"),    ("Calculate CFM for 450 CID engine at 5000 RPM with 100% VE", "Should calculate CFM ≈ 651"),    ("Calculate CFM for 450 CID engine at 5500 RPM with 80% VE", "Should calculate CFM ≈ 573"),    ("Calculate CFM for 450 CID engine at 5500 RPM with 85% VE", "Should calculate CFM ≈ 609"),    ("Calculate CFM for 450 CID engine at 5500 RPM with 90% VE", "Should calculate CFM ≈ 645"),    ("Calculate CFM for 450 CID engine at 5500 RPM with 95% VE", "Should calculate CFM ≈ 680"),    ("Calculate CFM for 450 CID engine at 5500 RPM with 100% VE", "Should calculate CFM ≈ 716"),    ("Calculate CFM for 450 CID engine at 6000 RPM with 80% VE", "Should calculate CFM ≈ 625"),    ("Calculate CFM for 450 CID engine at 6000 RPM with 85% VE", "Should calculate CFM ≈ 664"),    ("Calculate CFM for 450 CID engine at 6000 RPM with 90% VE", "Should calculate CFM ≈ 703"),    ("Calculate CFM for 450 CID engine at 6000 RPM with 95% VE", "Should calculate CFM ≈ 742"),    ("Calculate CFM for 450 CID engine at 6000 RPM with 100% VE", "Should calculate CFM ≈ 781"),    ("Calculate CFM for 450 CID engine at 6500 RPM with 80% VE", "Should calculate CFM ≈ 677"),    ("Calculate CFM for 450 CID engine at 6500 RPM with 85% VE", "Should calculate CFM ≈ 719"),    ("Calculate CFM for 450 CID engine at 6500 RPM with 90% VE", "Should calculate CFM ≈ 762"),    ("Calculate CFM for 450 CID engine at 6500 RPM with 95% VE", "Should calculate CFM ≈ 804"),    ("Calculate CFM for 450 CID engine at 6500 RPM with 100% VE", "Should calculate CFM ≈ 846"),    ("Calculate CFM for 450 CID engine at 7000 RPM with 80% VE", "Should calculate CFM ≈ 729"),    ("Calculate CFM for 450 CID engine at 7000 RPM with 85% VE", "Should calculate CFM ≈ 775"),    ("Calculate CFM for 450 CID engine at 7000 RPM with 90% VE", "Should calculate CFM ≈ 820"),    ("Calculate CFM for 450 CID engine at 7000 RPM with 95% VE", "Should calculate CFM ≈ 866"),    ("Calculate CFM for 450 CID engine at 7000 RPM with 100% VE", "Should calculate CFM ≈ 911"),    ("Calculate CFM for 500 CID engine at 5000 RPM with 80% VE", "Should calculate CFM ≈ 579"),    ("Calculate CFM for 500 CID engine at 5000 RPM with 85% VE", "Should calculate CFM ≈ 615"),    ("Calculate CFM for 500 CID engine at 5000 RPM with 90% VE", "Should calculate CFM ≈ 651"),    ("Calculate CFM for 500 CID engine at 5000 RPM with 95% VE", "Should calculate CFM ≈ 687"),    ("Calculate CFM for 500 CID engine at 5000 RPM with 100% VE", "Should calculate CFM ≈ 723"),    ("Calculate CFM for 500 CID engine at 5500 RPM with 80% VE", "Should calculate CFM ≈ 637"),    ("Calculate CFM for 500 CID engine at 5500 RPM with 85% VE", "Should calculate CFM ≈ 676"),    ("Calculate CFM for 500 CID engine at 5500 RPM with 90% VE", "Should calculate CFM ≈ 716"),    ("Calculate CFM for 500 CID engine at 5500 RPM with 95% VE", "Should calculate CFM ≈ 756"),    ("Calculate CFM for 500 CID engine at 5500 RPM with 100% VE", "Should calculate CFM ≈ 796"),    ("Calculate CFM for 500 CID engine at 6000 RPM with 80% VE", "Should calculate CFM ≈ 694"),    ("Calculate CFM for 500 CID engine at 6000 RPM with 85% VE", "Should calculate CFM ≈ 738"),    ("Calculate CFM for 500 CID engine at 6000 RPM with 90% VE", "Should calculate CFM ≈ 781"),    ("Calculate CFM for 500 CID engine at 6000 RPM with 95% VE", "Should calculate CFM ≈ 825"),    ("Calculate CFM for 500 CID engine at 6000 RPM with 100% VE", "Should calculate CFM ≈ 868"),    ("Calculate CFM for 500 CID engine at 6500 RPM with 80% VE", "Should calculate CFM ≈ 752"),    ("Calculate CFM for 500 CID engine at 6500 RPM with 85% VE", "Should calculate CFM ≈ 799"),    ("Calculate CFM for 500 CID engine at 6500 RPM with 90% VE", "Should calculate CFM ≈ 846"),    ("Calculate CFM for 500 CID engine at 6500 RPM with 95% VE", "Should calculate CFM ≈ 893"),    ("Calculate CFM for 500 CID engine at 6500 RPM with 100% VE", "Should calculate CFM ≈ 940"),    ("Calculate CFM for 500 CID engine at 7000 RPM with 80% VE", "Should calculate CFM ≈ 810"),    ("Calculate CFM for 500 CID engine at 7000 RPM with 85% VE", "Should calculate CFM ≈ 861"),    ("Calculate CFM for 500 CID engine at 7000 RPM with 90% VE", "Should calculate CFM ≈ 911"),    ("Calculate CFM for 500 CID engine at 7000 RPM with 95% VE", "Should calculate CFM ≈ 962"),    ("Calculate CFM for 500 CID engine at 7000 RPM with 100% VE", "Should calculate CFM ≈ 1013"),    ("Calculate VE if engine flows 400 CFM at 5000 RPM, 300 CID", "Should calculate VE ≈ 0.92"),    ("Calculate VE if engine flows 400 CFM at 5500 RPM, 300 CID", "Should calculate VE ≈ 0.84"),    ("Calculate VE if engine flows 400 CFM at 6000 RPM, 300 CID", "Should calculate VE ≈ 0.77"),    ("Calculate VE if engine flows 400 CFM at 6500 RPM, 300 CID", "Should calculate VE ≈ 0.71"),    ("Calculate VE if engine flows 400 CFM at 7000 RPM, 300 CID", "Should calculate VE ≈ 0.66"),    ("Calculate VE if engine flows 400 CFM at 5000 RPM, 350 CID", "Should calculate VE ≈ 0.79"),    ("Calculate VE if engine flows 400 CFM at 5500 RPM, 350 CID", "Should calculate VE ≈ 0.72"),    ("Calculate VE if engine flows 400 CFM at 6000 RPM, 350 CID", "Should calculate VE ≈ 0.66"),    ("Calculate VE if engine flows 400 CFM at 6500 RPM, 350 CID", "Should calculate VE ≈ 0.61"),    ("Calculate VE if engine flows 400 CFM at 7000 RPM, 350 CID", "Should calculate VE ≈ 0.56"),    ("Calculate VE if engine flows 400 CFM at 5000 RPM, 400 CID", "Should calculate VE ≈ 0.69"),    ("Calculate VE if engine flows 400 CFM at 5500 RPM, 400 CID", "Should calculate VE ≈ 0.63"),    ("Calculate VE if engine flows 400 CFM at 6000 RPM, 400 CID", "Should calculate VE ≈ 0.58"),    ("Calculate VE if engine flows 400 CFM at 6500 RPM, 400 CID", "Should calculate VE ≈ 0.53"),    ("Calculate VE if engine flows 400 CFM at 5000 RPM, 450 CID", "Should calculate VE ≈ 0.61"),    ("Calculate VE if engine flows 400 CFM at 5500 RPM, 450 CID", "Should calculate VE ≈ 0.56"),    ("Calculate VE if engine flows 400 CFM at 6000 RPM, 450 CID", "Should calculate VE ≈ 0.51"),    ("Calculate VE if engine flows 400 CFM at 5000 RPM, 500 CID", "Should calculate VE ≈ 0.55"),    ("Calculate VE if engine flows 400 CFM at 5500 RPM, 500 CID", "Should calculate VE ≈ 0.5"),    ("Calculate VE if engine flows 450 CFM at 5000 RPM, 300 CID", "Should calculate VE ≈ 1.04"),    ("Calculate VE if engine flows 450 CFM at 5500 RPM, 300 CID", "Should calculate VE ≈ 0.94"),    ("Calculate VE if engine flows 450 CFM at 6000 RPM, 300 CID", "Should calculate VE ≈ 0.86"),    ("Calculate VE if engine flows 450 CFM at 6500 RPM, 300 CID", "Should calculate VE ≈ 0.8"),    ("Calculate VE if engine flows 450 CFM at 7000 RPM, 300 CID", "Should calculate VE ≈ 0.74"),    ("Calculate VE if engine flows 450 CFM at 5000 RPM, 350 CID", "Should calculate VE ≈ 0.89"),    ("Calculate VE if engine flows 450 CFM at 5500 RPM, 350 CID", "Should calculate VE ≈ 0.81"),    ("Calculate VE if engine flows 450 CFM at 6000 RPM, 350 CID", "Should calculate VE ≈ 0.74"),    ("Calculate VE if engine flows 450 CFM at 6500 RPM, 350 CID", "Should calculate VE ≈ 0.68"),    ("Calculate VE if engine flows 450 CFM at 7000 RPM, 350 CID", "Should calculate VE ≈ 0.63"),    ("Calculate VE if engine flows 450 CFM at 5000 RPM, 400 CID", "Should calculate VE ≈ 0.78"),    ("Calculate VE if engine flows 450 CFM at 5500 RPM, 400 CID", "Should calculate VE ≈ 0.71"),    ("Calculate VE if engine flows 450 CFM at 6000 RPM, 400 CID", "Should calculate VE ≈ 0.65"),    ("Calculate VE if engine flows 450 CFM at 6500 RPM, 400 CID", "Should calculate VE ≈ 0.6"),    ("Calculate VE if engine flows 450 CFM at 7000 RPM, 400 CID", "Should calculate VE ≈ 0.56"),    ("Calculate VE if engine flows 450 CFM at 5000 RPM, 450 CID", "Should calculate VE ≈ 0.69"),    ("Calculate VE if engine flows 450 CFM at 5500 RPM, 450 CID", "Should calculate VE ≈ 0.63"),    ("Calculate VE if engine flows 450 CFM at 6000 RPM, 450 CID", "Should calculate VE ≈ 0.58"),    ("Calculate VE if engine flows 450 CFM at 6500 RPM, 450 CID", "Should calculate VE ≈ 0.53"),    ("Calculate VE if engine flows 450 CFM at 5000 RPM, 500 CID", "Should calculate VE ≈ 0.62"),    ("Calculate VE if engine flows 450 CFM at 5500 RPM, 500 CID", "Should calculate VE ≈ 0.57"),    ("Calculate VE if engine flows 450 CFM at 6000 RPM, 500 CID", "Should calculate VE ≈ 0.52"),    ("Calculate VE if engine flows 500 CFM at 5000 RPM, 300 CID", "Should calculate VE ≈ 1.15"),    ("Calculate VE if engine flows 500 CFM at 5500 RPM, 300 CID", "Should calculate VE ≈ 1.05"),    ("Calculate VE if engine flows 500 CFM at 6000 RPM, 300 CID", "Should calculate VE ≈ 0.96"),    ("Calculate VE if engine flows 500 CFM at 6500 RPM, 300 CID", "Should calculate VE ≈ 0.89"),    ("Calculate VE if engine flows 500 CFM at 7000 RPM, 300 CID", "Should calculate VE ≈ 0.82"),    ("Calculate VE if engine flows 500 CFM at 5000 RPM, 350 CID", "Should calculate VE ≈ 0.99"),    ("Calculate VE if engine flows 500 CFM at 5500 RPM, 350 CID", "Should calculate VE ≈ 0.9"),    ("Calculate VE if engine flows 500 CFM at 6000 RPM, 350 CID", "Should calculate VE ≈ 0.82"),    ("Calculate VE if engine flows 500 CFM at 6500 RPM, 350 CID", "Should calculate VE ≈ 0.76"),    ("Calculate VE if engine flows 500 CFM at 7000 RPM, 350 CID", "Should calculate VE ≈ 0.71"),    ("Calculate VE if engine flows 500 CFM at 5000 RPM, 400 CID", "Should calculate VE ≈ 0.86"),    ("Calculate VE if engine flows 500 CFM at 5500 RPM, 400 CID", "Should calculate VE ≈ 0.79"),    ("Calculate VE if engine flows 500 CFM at 6000 RPM, 400 CID", "Should calculate VE ≈ 0.72"),    ("Calculate VE if engine flows 500 CFM at 6500 RPM, 400 CID", "Should calculate VE ≈ 0.66"),    ("Calculate VE if engine flows 500 CFM at 7000 RPM, 400 CID", "Should calculate VE ≈ 0.62"),    ("Calculate VE if engine flows 500 CFM at 5000 RPM, 450 CID", "Should calculate VE ≈ 0.77"),    ("Calculate VE if engine flows 500 CFM at 5500 RPM, 450 CID", "Should calculate VE ≈ 0.7"),    ("Calculate VE if engine flows 500 CFM at 6000 RPM, 450 CID", "Should calculate VE ≈ 0.64"),
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

