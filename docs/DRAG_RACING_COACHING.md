# Drag Racing Time Analysis & Coaching

## Overview

The AI Tuner Agent now includes comprehensive drag racing time analysis and coaching for:
- **60ft time** (launch performance)
- **1/8th mile time**
- **1/4 mile time**
- **1/2 mile time** (for high-speed runs)

## Features

### Time Tracking
- Automatic detection and recording of all drag racing segments
- Best time tracking for each segment
- Run history and statistics
- Comparison between runs

### AI Coaching
- Real-time analysis of each segment
- Actionable advice to improve times
- Priority-based coaching (high/medium/low)
- Improvement potential calculations
- Voice coaching integration

### Analysis
- Segment-by-segment breakdown
- Consistency analysis
- Improvement trends
- Performance statistics

## How It Works

### Automatic Detection
The system automatically detects when you start a drag run and tracks:
1. **60ft time** - Measures launch performance
2. **1/8th mile time** - Measures short-track performance
3. **1/4 mile time** - Standard drag racing metric
4. **1/2 mile time** - For high-speed runs

### Coaching Advice

The system provides specific coaching for each segment:

#### 60ft Time (Launch)
- Tire pressure recommendations
- Launch RPM optimization
- Throttle control advice
- Transbrake/launch control suggestions
- Suspension setup tips

#### 1/8th Mile
- Shift point optimization
- Traction control settings
- Gear selection advice
- Acceleration technique

#### 1/4 Mile
- Top-end performance tips
- Aerodynamics recommendations
- Power band optimization
- Boost/nitrous timing

#### 1/2 Mile
- High-speed aerodynamics
- Gearing optimization
- Cooling considerations
- Power delivery timing

## Usage

### In the UI
1. Start a drag racing session
2. Complete a run
3. View coaching advice in the Drag Coaching Widget
4. Review actionable steps for improvement

### Programmatic
```python
from services import DragRacingAnalyzer, DragRun

# Create analyzer
analyzer = DragRacingAnalyzer(voice_feedback=voice_feedback)

# Record a run
run = DragRun(
    run_id="run_001",
    timestamp=time.time(),
    times={
        "60ft": 1.85,
        "1/8 mile": 7.92,
        "1/4 mile": 12.45,
    },
    speeds={
        "1/4 mile": 112.5,
    },
)

# Record and analyze
analyzer.record_run(run)
advice = analyzer.analyze_run(run)

# Get statistics
stats = analyzer.get_statistics()
```

## Coaching Examples

### Example 1: Slow 60ft Time
**Current**: 2.1s  
**Best**: 1.8s  
**Advice**: "Your 60ft time is slow. Focus on launch technique."

**Actionable Steps**:
- Check tire pressure (lower for better grip)
- Improve launch RPM (find optimal RPM for your setup)
- Work on throttle control (smooth application, avoid wheelspin)
- Consider transbrake or launch control if available
- Check suspension setup for weight transfer

### Example 2: Inconsistent Times
**Issue**: Times vary by 0.5s between runs  
**Advice**: "Your times vary significantly. Focus on consistency."

**Actionable Steps**:
- Practice consistent launch technique
- Record what's different between runs
- Focus on repeatability over speed initially

## Integration

The drag racing analyzer integrates with:
- **Performance Tracker** - Tracks all drag segments
- **AI Racing Coach** - Provides overall coaching
- **Voice Feedback** - Spoken coaching advice
- **UI Components** - Visual display of advice
- **Data Logger** - Records all runs for analysis

## Best Practices

1. **Consistency First**: Focus on consistent times before pushing for faster
2. **One Change at a Time**: Make one adjustment per run to see what works
3. **Record Everything**: Note conditions, setup, and changes
4. **Review Trends**: Look at improvement trends over time
5. **Follow Advice**: The AI provides specific, actionable steps

## Future Enhancements

- Machine learning-based optimal launch RPM prediction
- Weather condition adjustments
- Vehicle-specific tuning recommendations
- Integration with ECU tuning for automatic adjustments
- Social comparison with other racers

---

**This is a UNIQUE feature** - no other racing telemetry system provides AI-powered drag racing coaching with actionable advice!

