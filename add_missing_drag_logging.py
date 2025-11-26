#!/usr/bin/env python3
"""
Add any missing drag racing data logging concepts to ensure complete coverage.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from services.vector_knowledge_store import VectorKnowledgeStore
    from services.knowledge_base_file_manager import KnowledgeBaseFileManager
    KB_AVAILABLE = True
except ImportError as e:
    KB_AVAILABLE = False
    LOGGER.error(f"Knowledge base modules not available: {e}")

# Missing or enhanced concepts
MISSING_KNOWLEDGE = [
    {
        "question": "What is torque converter line cooler pressure and why is it important?",
        "answer": """Torque converter line cooler pressure (also called torque converter line pressure) is a critical parameter for automatic transmission data logging:

**What It Is:**
- Pressure in the line that feeds the torque converter
- Measured between the transmission pump and torque converter
- Indicates how the torque converter is functioning

**Why It's Critical:**
- **Converter Function Analysis** - Shows how the torque converter is operating
- **Converter Lockup** - Reveals when and how the converter locks up
- **Converter Efficiency** - Indicates converter slippage and efficiency
- **Transmission Health** - Can reveal transmission pump issues
- **Performance Optimization** - Helps optimize converter selection and tuning

**What to Look For:**
- **Normal Operation** - Pressure should be consistent and within expected range
- **Converter Lockup** - Pressure changes when converter locks up
- **Slippage Indicators** - Abnormal pressure can indicate excessive converter slip
- **Pump Issues** - Low pressure can indicate transmission pump problems

**Data Logging Applications:**
- Log converter line pressure throughout the run
- Compare pressure curves between runs
- Correlate with engine RPM and driveshaft speed
- Use to optimize converter tuning
- Identify when converter needs attention

**Optimization:**
- Use data to select optimal converter stall speed
- Fine-tune converter lockup timing
- Identify converter that's too tight or too loose
- Optimize for track conditions

Torque converter line cooler pressure is essential for understanding automatic transmission performance and optimizing converter function.""",
        "keywords": ["torque converter", "line cooler pressure", "line pressure", "automatic transmission", "converter lockup", "converter efficiency"],
        "topic": "Drag Racing Data Logging - Torque Converter Pressure"
    },
    {
        "question": "How do you use data visualization in drag racing data analysis?",
        "answer": """Data visualization uses software to plot data as graphs and charts to make trends and patterns more apparent than looking at raw numbers alone:

**Benefits of Visualization:**
- **Pattern Recognition** - Graphs reveal patterns that numbers alone can't show
- **Trend Identification** - Easier to spot trends over multiple runs
- **Quick Analysis** - Visual representation is faster to interpret
- **Comparison** - Overlaying multiple runs shows differences clearly
- **Communication** - Visuals help explain findings to drivers and team members

**Common Visualization Types:**
- **Speed vs Distance** - Speed trace showing acceleration and braking
- **RPM vs Time** - Engine speed throughout the run
- **AFR vs RPM** - Air/fuel ratio at different engine speeds
- **Pressure vs Time** - Fuel pressure, oil pressure, boost pressure
- **Temperature vs Time** - Coolant, oil, air temperatures
- **G-Force vs Time** - Longitudinal and lateral forces
- **Overlay Comparisons** - Multiple runs overlaid to see differences

**Visualization Techniques:**
- **Color Coding** - Use different colors for different runs or conditions
- **Zoom and Pan** - Focus on specific sections of the run
- **Markers** - Add markers for shift points, events, or key moments
- **Annotations** - Add notes and labels to explain what's happening
- **Multi-Channel Views** - Display multiple parameters simultaneously

**Speed Trace Visualization:**
- Plot speed vs distance to see acceleration characteristics
- Identify "sawtooth" patterns (desirable) vs curves (inefficient)
- Spot areas where time is being lost
- Compare runs to identify improvements or regressions

**AFR Visualization:**
- Plot AFR vs RPM to see fuel delivery throughout power band
- Identify optimal shift points based on AFR
- Spot lean or rich conditions
- Compare AFR between cylinders

**Pressure and Temperature Visualization:**
- Plot pressures to see system performance
- Identify pressure drops or spikes
- Monitor temperature trends
- Correlate with performance changes

**Overlay Analysis:**
- Overlay multiple runs to compare performance
- Identify what changed between runs
- See effects of tuning changes
- Track consistency over time

**Software Tools:**
- AEMdata, Racepak, Holley EFI, etc. provide visualization tools
- Export data to Excel or specialized analysis software
- Create custom dashboards for specific analysis needs

**Best Practices:**
- Always visualize key parameters, not just look at numbers
- Use consistent scales for easy comparison
- Create standard views for common analysis tasks
- Save visualization templates for repeatable analysis
- Use visualization to communicate findings effectively

Data visualization transforms raw numbers into actionable insights, making it much easier to identify problems, optimize performance, and improve consistency.""",
        "keywords": ["data visualization", "graphs", "charts", "speed trace", "overlay", "analysis software", "trends", "patterns"],
        "topic": "Drag Racing Data Logging - Data Visualization"
    },
    {
        "question": "How do you overcome information overload when analyzing drag racing data logs?",
        "answer": """Overcoming information overload is critical when dealing with the vast amount of data collected in drag racing:

**The Problem:**
- Modern data loggers can record dozens or hundreds of channels
- Each run generates thousands of data points
- Trying to analyze everything at once leads to confusion
- Important information gets lost in the noise

**Solution: Focus on Critical Metrics:**
- **Identify Key Parameters** - Determine which metrics matter most for your specific goals
- **Prioritize by Impact** - Focus on parameters that have the biggest impact on performance
- **Ignore Non-Essential Data** - Don't waste time on parameters that don't affect performance
- **Build Analysis Hierarchy** - Create a system that prioritizes most important data first

**Structured Analysis Approach:**
1. **Start with Basics** - Always check critical safety parameters first (oil pressure, fuel pressure, temperatures)
2. **Performance Metrics** - Then analyze performance metrics (ET, speed, RPM)
3. **Specific Goals** - Focus on data relevant to your current tuning goal
4. **One Thing at a Time** - Don't try to optimize everything simultaneously

**Creating Focus Areas:**
- **Launch Analysis** - Focus only on launch-related data (RPM, throttle, G-forces, 60-foot time)
- **Mid-Track Analysis** - Focus on mid-track performance (shift points, AFR, driveshaft speed)
- **Top End Analysis** - Focus on finish line performance (trap speed, final RPM, braking)
- **Problem-Specific** - When troubleshooting, focus only on data related to the problem

**Data Filtering Techniques:**
- **Time-Based Filtering** - Focus on specific time ranges (e.g., first 2 seconds for launch analysis)
- **Event-Based Filtering** - Filter by events (shifts, launch, braking)
- **Condition-Based Filtering** - Filter by conditions (RPM ranges, speed ranges)
- **Channel Selection** - Only display channels relevant to current analysis

**Building Analysis Templates:**
- Create standard analysis views for common tasks
- Save templates for launch analysis, shift analysis, etc.
- Use consistent analysis procedures
- Build a library of successful analysis patterns

**Progressive Analysis:**
- **Level 1: Safety Check** - Quick review of critical safety parameters
- **Level 2: Performance Summary** - Review overall performance metrics
- **Level 3: Detailed Analysis** - Deep dive into specific areas
- **Level 4: Advanced Analysis** - Complex multi-parameter correlation

**Using Software Features:**
- **Dashboards** - Create custom dashboards showing only critical metrics
- **Alarms and Warnings** - Set up automatic alerts for critical parameters
- **Summary Reports** - Use software to generate summary reports
- **Comparison Tools** - Use built-in comparison features instead of manual analysis

**Best Practices:**
- **Start Simple** - Begin with basic parameters, add complexity as needed
- **Document What Works** - Keep notes on which analysis approaches work best
- **Standardize Procedures** - Use consistent analysis procedures
- **Time Management** - Set time limits for analysis to avoid getting lost in data
- **Ask Specific Questions** - Instead of "what's wrong?", ask "is the AFR correct at shift points?"

**Avoiding Overload:**
- Don't log more channels than you can effectively analyze
- Focus on quality over quantity of data
- Use data to answer specific questions, not to explore everything
- Trust your analysis process and don't second-guess with more data

**When to Go Deeper:**
- Only dive deep into detailed analysis when basic analysis doesn't reveal the issue
- Use detailed analysis to confirm hypotheses, not to search blindly
- Know when you have enough information to make a decision

By focusing on critical metrics and using structured analysis approaches, you can overcome information overload and make effective use of data logging to improve performance.""",
        "keywords": ["information overload", "data analysis", "focus", "critical metrics", "prioritize", "filtering", "analysis templates"],
        "topic": "Drag Racing Data Logging - Overcoming Information Overload"
    },
    {
        "question": "What is the complete workflow for drag racing data logging from setup to analysis?",
        "answer": """Complete workflow for drag racing data logging:

**Phase 1: Setup and Configuration**
1. Install and configure data logger
2. Set up core parameters (RPM, temperatures, pressures, speeds)
3. Add transmission-specific sensors (converter pressure or clutch speed)
4. Install chassis sensors (shock pots, G-meters)
5. Configure driver input sensors (steering, brake, throttle)
6. Set up failsafes in ECU
7. Calibrate all sensors
8. Test data logging system

**Phase 2: Baseline Data Collection**
1. Make baseline runs with consistent setup
2. Log multiple runs to establish normal operating ranges
3. Document track conditions and weather
4. Record baseline performance (ET, speed, incremental times)
5. Create baseline data library

**Phase 3: Run Execution**
1. Document pre-run conditions (weather, track, setup)
2. Make the run
3. Immediately review critical safety parameters
4. Download and save data log
5. Document run results (timeslip, notes, observations)

**Phase 4: Quick Safety Check**
1. Review oil pressure throughout run
2. Check fuel pressure
3. Verify temperatures stayed in safe range
4. Check for any failsafe activations
5. Review AFR for dangerous lean conditions

**Phase 5: Performance Analysis**
1. Review overall performance (ET, speed, incremental times)
2. Compare to baseline or previous runs
3. Identify areas of improvement or concern
4. Focus on specific goals (launch, mid-track, top end)

**Phase 6: Detailed Analysis (As Needed)**
1. Analyze specific areas based on goals:
   - Launch: RPM, throttle, G-forces, shock travel, 60-foot time
   - Shifts: Shift points, AFR at shifts, shift duration, recovery
   - Top End: Trap speed, final RPM, braking technique
2. Use data visualization to identify patterns
3. Correlate multiple parameters
4. Compare to previous runs

**Phase 7: Optimization Decisions**
1. Identify specific changes needed
2. Make one change at a time
3. Predict expected results
4. Document planned changes

**Phase 8: Implementation and Validation**
1. Make the change
2. Log new runs
3. Compare data to previous runs
4. Quantify the improvement (or lack thereof)
5. Document results

**Phase 9: Continuous Improvement**
1. Build knowledge base of what works
2. Refine analysis procedures
3. Improve consistency
4. Track long-term trends

**Key Principles:**
- Always start with safety checks
- Focus on critical metrics, not everything
- Make one change at a time
- Document everything
- Use data to answer specific questions
- Build on what works

This workflow ensures systematic, effective use of data logging to continuously improve performance.""",
        "keywords": ["workflow", "data logging", "setup", "baseline", "analysis", "optimization", "workflow", "procedure"],
        "topic": "Drag Racing Data Logging - Complete Workflow"
    }
]


def main():
    """Add missing drag racing data logging knowledge."""
    if not KB_AVAILABLE:
        LOGGER.error("Knowledge base modules not available")
        return
    
    LOGGER.info("Initializing knowledge base...")
    vector_store = VectorKnowledgeStore()
    kb_file_manager = KnowledgeBaseFileManager()
    
    added_count = 0
    
    for entry in MISSING_KNOWLEDGE:
        try:
            LOGGER.info(f"Adding: {entry['question'][:60]}...")
            
            # Add to vector store
            doc_id = vector_store.add_knowledge(
                text=f"{entry['question']}\n\n{entry['answer']}",
                metadata={
                    "question": entry["question"],
                    "topic": entry["topic"],
                    "keywords": ", ".join(entry["keywords"]),
                    "source": "comprehensive_drag_logging_knowledge",
                    "category": "Drag Racing Data Logging"
                }
            )
            
            # Add to KB file manager
            kb_file_manager.add_entry(
                question=entry["question"],
                answer=entry["answer"],
                source="comprehensive_drag_logging_knowledge",
                keywords=entry["keywords"],
                topic=entry["topic"],
                confidence=0.95,
                verified=True
            )
            
            added_count += 1
            LOGGER.info(f"  Successfully added")
            
        except Exception as e:
            LOGGER.error(f"  Failed to add entry: {e}")
    
    LOGGER.info(f"\n{'='*70}")
    LOGGER.info(f"SUMMARY")
    LOGGER.info(f"{'='*70}")
    LOGGER.info(f"Total entries: {len(MISSING_KNOWLEDGE)}")
    LOGGER.info(f"Successfully added: {added_count}")
    LOGGER.info(f"\nMissing drag racing data logging concepts have been added!")
    LOGGER.info(f"Coverage now includes:")
    LOGGER.info(f"  - Torque converter line cooler pressure (detailed)")
    LOGGER.info(f"  - Data visualization techniques and best practices")
    LOGGER.info(f"  - Overcoming information overload strategies")
    LOGGER.info(f"  - Complete workflow from setup to analysis")


if __name__ == "__main__":
    main()

