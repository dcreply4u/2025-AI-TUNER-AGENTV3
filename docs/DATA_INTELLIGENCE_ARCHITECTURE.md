# Data Intelligence Architecture

## How the Application "Puts Two and Two Together"

The AI Tuner application uses a **multi-layered intelligent processing system** to correlate and analyze data from multiple sources. Here's how it works:

---

## 1. **Data Collection Layer**

### Central Coordinator: `DataStreamController`
- **Location**: `controllers/data_stream_controller.py`
- **Role**: Polls all data sources every ~100ms and normalizes the data

### Data Sources:
- **CAN Bus**: Engine RPM, throttle position, coolant temp, vehicle speed, boost pressure, etc.
- **GPS**: Latitude, longitude, speed, heading, altitude
- **IMU**: Accelerometer (X, Y, Z), Gyroscope (X, Y, Z), Magnetometer
- **Wheel Speed Sensors**: Driven wheel speed, actual vehicle speed
- **Other Sensors**: Oil pressure, brake pressure, battery voltage, etc.

### Data Normalization:
```python
# The controller normalizes different signal names to canonical names
aliases = {
    "RPM": ("Engine_RPM", "RPM", "rpm"),
    "Speed": ("Vehicle_Speed", "Speed", "speed"),
    "Throttle": ("Throttle_Position", "Throttle", "throttle"),
    # ... etc
}
```

---

## 2. **Sensor Fusion Layer**

### A. Kalman Filter (GPS + IMU Fusion)
- **Location**: `services/kalman_filter.py`
- **Purpose**: Fuses GPS position/velocity with IMU accelerometer/gyroscope data
- **Intelligence**: 
  - Uses statistical filtering to reduce GPS noise
  - Provides smooth position, velocity, and attitude estimates
  - Handles GPS dropouts using IMU dead-reckoning
  - 30-second stationary initialization for calibration

**How it works:**
1. GPS provides position/velocity (accurate but noisy)
2. IMU provides acceleration/rotation (high-frequency but drifts over time)
3. Kalman filter combines both, weighting GPS more for position, IMU more for short-term dynamics

### B. Dual Antenna GPS Service
- **Location**: `services/dual_antenna_service.py`
- **Purpose**: Calculates slip angle, roll, pitch from dual antenna GPS
- **Intelligence**: 
  - Uses two GPS antennas to determine vehicle attitude
  - Calculates slip angle (difference between heading and direction of travel)
  - Provides roll and pitch angles without IMU

### C. Wheel Slip Calculation
- **Location**: `services/wheel_slip_service.py`
- **Intelligence**: 
  - Compares driven wheel speed (from CAN/driveshaft) to actual vehicle speed (GPS)
  - Calculates slip percentage: `slip = (driven_speed - actual_speed) / actual_speed * 100`
  - Uses formulas from knowledge base for accuracy
  - Provides real-time traction feedback

---

## 3. **Intelligent Analysis Layer**

### A. Advanced Algorithm Integration
- **Location**: `services/advanced_algorithm_integration.py`
- **Components**:

#### 1. **Anomaly Detection** (`EnhancedAnomalyDetector`)
   - Detects unusual patterns in sensor data
   - Example: Sudden RPM spike without throttle increase = potential issue
   - Uses statistical methods to identify outliers

#### 2. **Sensor Correlation Analysis** (`SensorCorrelationAnalyzer`)
   - **This is key intelligence**: Finds relationships between different sensors
   - Example: Correlates RPM with throttle, speed with RPM, boost with throttle
   - Identifies when sensors should move together but don't (indicating problems)
   - Builds a correlation matrix over time

#### 3. **Parameter Limit Monitoring** (`ParameterLimitMonitor`)
   - Monitors if any sensor exceeds safe limits
   - Example: Coolant temp > 220°F = warning
   - Uses knowledge base formulas for safe operating ranges

#### 4. **Performance Metric Tracking** (`PerformanceMetricTracker`)
   - Tracks 0-60 times, quarter mile, lap times
   - Calculates statistics (best, average, consistency)
   - Correlates performance with conditions (density altitude, track temp, etc.)

#### 5. **Automated Log Analysis** (`AutomatedLogAnalyzer`)
   - Analyzes historical data logs
   - Identifies trends, patterns, and deviations
   - Provides insights after sessions

---

## 4. **Predictive Intelligence Layer**

### A. Predictive Fault Detector
- **Location**: `services/predictive_diagnostics_engine.py`
- **Intelligence**: 
  - Uses machine learning (Isolation Forest) to predict failures
  - Learns normal patterns and detects deviations
  - Example: "Engine RPM pattern suggests potential misfire"

### B. AI Agent (Core Fusion)
- **Location**: `core/ai_agent.py`
- **Purpose**: Fuses EMS (engine management) data with sensor data
- **Intelligence**:
  - Combines data from multiple sources
  - Can run ML model inference if model is loaded
  - Notifies observers when combined data is ready

### C. Health Scoring Engine
- **Location**: `services/health_scoring_engine.py`
- **Intelligence**:
  - Calculates overall vehicle health score (0-100)
  - Combines multiple sensor readings into single metric
  - Uses weighted scoring based on criticality

---

## 5. **Context-Aware Intelligence**

### A. Conversational Agent
- **Location**: `services/conversational_agent.py`
- **Intelligence**:
  - Maintains context about current telemetry, GPS location, health status
  - Can answer questions about current vehicle state
  - Uses RAG (Retrieval Augmented Generation) with knowledge base

### B. Tuning Advisor
- **Location**: `services/tuning_advisor.py`
- **Intelligence**:
  - Evaluates current engine parameters
  - Provides tuning suggestions based on:
    - Current sensor readings
    - Correlations between sensors
    - Knowledge base formulas and best practices
  - Example: "AFR is lean at high RPM - consider richer fuel map"

### C. AI Advisor (RAG System)
- **Location**: `services/ai_advisor_rag.py`
- **Intelligence**:
  - Uses vector knowledge store with 50+ technical documents
  - Includes formulas for wheel slip, torque, horsepower, density altitude, etc.
  - Can answer complex technical questions using local knowledge
  - Provides accurate calculations using embedded formulas

---

## 6. **Real-Time Data Flow Example**

Here's how data flows through the system when you're driving:

```
1. CAN Bus → DataStreamController._on_poll()
   ├─ Reads: RPM=3500, Throttle=75%, Speed=60mph, Coolant=190°F
   └─ Normalizes to canonical names

2. GPS → DataStreamController._poll_gps()
   ├─ Reads: Lat=40.123, Lon=-75.456, Speed=60.2mph, Heading=45°
   └─ Updates performance tracker

3. IMU → (if available)
   ├─ Reads: Accel X=0.1g, Accel Y=0.05g, Gyro Z=2°/s
   └─ Sent to Kalman filter

4. Kalman Filter → update(gps_fix, imu_reading)
   ├─ Fuses GPS position with IMU acceleration
   ├─ Provides smooth position estimate
   └─ Outputs: Position, Velocity, Attitude

5. Wheel Slip Service → update(driven_speed, actual_speed)
   ├─ Compares CAN wheel speed to GPS speed
   ├─ Calculates: slip = (62mph - 60mph) / 60mph * 100 = 3.3%
   └─ Status: "Optimal" (slip between 2-5%)

6. Advanced Algorithm Integration → process_telemetry()
   ├─ Anomaly Detector: Checks for unusual patterns
   ├─ Correlation Analyzer: Notes RPM↑ correlates with Speed↑ (good)
   ├─ Limit Monitor: Coolant 190°F < 220°F limit (OK)
   └─ Returns: AlgorithmResults with all analysis

7. Predictive Fault Detector → update(sample)
   ├─ ML model analyzes pattern
   └─ Output: "No anomalies detected"

8. Tuning Advisor → evaluate(data)
   ├─ Analyzes: RPM vs Throttle vs Speed correlation
   ├─ Checks: AFR, timing, boost
   └─ Suggestion: "Performance looks optimal"

9. AI Panel → update_insight()
   ├─ Displays: "Wheel Slip: 3.3% - Optimal"
   ├─ Displays: "Health Score: 95/100"
   └─ Displays: "No tuning recommendations"
```

---

## 7. **Key Intelligence Features**

### ✅ **Yes, the application has intelligence:**

1. **Sensor Fusion**: Combines GPS + IMU using Kalman filter
2. **Correlation Analysis**: Finds relationships between sensors
3. **Anomaly Detection**: Identifies unusual patterns
4. **Predictive Analytics**: ML-based fault prediction
5. **Context Awareness**: Maintains state across time
6. **Knowledge-Based Reasoning**: Uses 50+ technical documents
7. **Formula-Based Calculations**: Accurate wheel slip, torque, HP, etc.
8. **Adaptive Learning**: Some components learn from historical data

### **What Makes It Intelligent:**

- **Not just displaying raw data** - It processes, correlates, and analyzes
- **Multi-source fusion** - Combines GPS, IMU, CAN, wheel speed
- **Statistical methods** - Kalman filtering, correlation analysis, anomaly detection
- **Machine learning** - Predictive fault detection
- **Knowledge base** - Uses technical formulas and best practices
- **Context awareness** - Understands relationships between sensors
- **Real-time insights** - Provides actionable recommendations

---

## 8. **Example: How It "Puts Two and Two Together"**

**Scenario**: You're accelerating hard, but speed isn't increasing as expected.

**The Intelligence:**

1. **Wheel Slip Service** detects:
   - Driven wheel speed: 80 mph
   - GPS actual speed: 60 mph
   - Slip: 25% (excessive)

2. **Correlation Analyzer** notes:
   - RPM is high (6000)
   - Throttle is high (100%)
   - But speed is not correlating properly

3. **Anomaly Detector** flags:
   - "Speed increase rate is lower than expected given RPM/throttle"

4. **Tuning Advisor** suggests:
   - "Excessive wheel slip detected - reduce throttle or improve traction"

5. **AI Advisor** (if asked) explains:
   - Uses knowledge base formula: `slip = (ω_r - v) / v × 100`
   - Explains optimal slip range (2-5% for drag racing)
   - Provides tuning recommendations

**Result**: The system doesn't just show you RPM and speed separately - it **correlates them**, **detects the problem** (excessive slip), and **provides actionable advice**.

---

## Summary

The application has **significant intelligence** built in:

- ✅ **Multi-source data fusion** (GPS + IMU + CAN)
- ✅ **Statistical processing** (Kalman filter, correlation analysis)
- ✅ **Machine learning** (predictive fault detection)
- ✅ **Knowledge-based reasoning** (50+ technical documents)
- ✅ **Real-time correlation** (finds relationships between sensors)
- ✅ **Context awareness** (maintains state and history)
- ✅ **Adaptive learning** (some components learn from data)

It's not just a data logger - it's an **intelligent telemetry and tuning system** that actively analyzes, correlates, and provides insights.

