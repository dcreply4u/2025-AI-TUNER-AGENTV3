# Intelligent Tuning Advisor

## Overview

The Intelligent Advisor is an advanced AI system that analyzes every run/pass and provides actionable tuning advice based on:

- **Current run performance** vs. historical bests
- **Engine health** parameters
- **Trends** across multiple runs
- **Safety** considerations
- **Efficiency** optimizations

## How It Works

### Automatic Run Detection

The system automatically detects when a run/pass starts and ends:
- **Run Start**: Speed increases from <20 mph to >30 mph
- **Run End**: Speed decreases from >30 mph to <10 mph

During each run, it collects:
- Average RPM, boost, temperatures
- Lambda/AFR values
- Throttle position
- Performance metrics (0-60, lap times, trap speeds)

### Analysis After Each Run

After every run completes, the advisor:

1. **Compares to Historical Data**
   - Best run times
   - Recent averages
   - Performance trends

2. **Analyzes Engine Health**
   - Temperature issues
   - Oil pressure
   - Knock detection
   - Air/fuel ratios

3. **Detects Trends**
   - Performance degradation
   - Cooling system issues
   - Consistency problems

4. **Safety Checks**
   - Critical health warnings
   - Fuel/boost mismatches
   - Methanol tank levels

5. **Efficiency Analysis**
   - Boost utilization
   - Fuel optimization
   - Power delivery

### Advice Categories

- **🔴 CRITICAL**: Immediate action required (knock, low oil pressure)
- **🟠 HIGH**: Important improvements (performance degradation, safety issues)
- **🟡 MEDIUM**: Recommended optimizations (tuning adjustments)
- **🟢 LOW**: Nice-to-have improvements (fine-tuning)

### Example Advice

**After a slower run:**
```
🔴 Run Time Slower Than Best
Current run (12.45s) is 0.32s slower than best (12.13s)
Action: Review recent changes and compare to best run conditions
Expected: Potential 0.32s improvement
Based on: Best time: 12.13s
```

**After detecting knock:**
```
🔴 Engine Knock Detected
Knock count: 3
Action: Reduce timing advance, enrich fuel, or reduce boost immediately
Expected: Prevent engine damage
```

**Trend analysis:**
```
🟠 Performance Declining
Run times trending slower over recent runs
Action: Review recent tuning changes, check for mechanical issues
Based on: Times increased 0.45s over recent runs
```

## Features

### Historical Learning

The advisor learns from every run:
- Tracks consistency patterns
- Identifies optimal operating conditions
- Remembers what works and what doesn't

### Confidence Scoring

Each piece of advice includes a confidence score (0-100%) based on:
- Data quality
- Historical sample size
- Pattern strength

### Multi-Factor Analysis

Considers multiple factors simultaneously:
- Performance + Health + Trends + Safety
- No single-metric tunnel vision
- Holistic tuning recommendations

### Actionable Recommendations

Every piece of advice includes:
- **What** the issue is
- **Why** it matters
- **How** to fix it
- **Expected** improvement

## Integration

The advisor is fully integrated into:
- ✅ **Data Stream Controller** - Analyzes every run automatically
- ✅ **Advice Panel UI** - Displays advice cards with priority colors
- ✅ **AI Insight Panel** - Shows top 3 advice items
- ✅ **Voice Feedback** - Announces critical advice
- ✅ **Historical Database** - Stores all runs for long-term learning

## Usage

The advisor works automatically - no configuration needed! After each run:

1. Run completes (speed drops)
2. System analyzes the run
3. Advice appears in the Advice Panel
4. Top advice shown in AI Insights
5. Critical advice announced via voice

## Advanced Features

### Summary Advice

Get advice based on recent runs:
```python
summary = intelligent_advisor.get_summary_advice(num_runs=5)
# Returns top 10 prioritized advice items
```

### Historical Comparison

Compare current run to history:
```python
comparison = intelligent_advisor.get_historical_comparison(run_number=5)
# Shows improvement/degradation vs. previous runs
```

## Customization

You can extend the advisor with custom analysis rules:

```python
def custom_analysis(metrics, health_score):
    # Your custom logic
    return advice_list

intelligent_advisor.register_custom_analysis(custom_analysis)
```

---

The Intelligent Advisor makes every run a learning opportunity! 🚗💨

