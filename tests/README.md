# Comprehensive QA Test Suite

## Overview

This is a complete Quality Assurance test suite for the AI Tuner Agent application. It tests all major functionality including file operations, graphing, data reading, AI advisor, telemetry processing, and more.

## Quick Start

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Specific Test Module
```bash
pytest tests/test_file_operations.py -v
pytest tests/test_graphing.py -v
pytest tests/test_data_reading.py -v
pytest tests/test_ai_advisor.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=interfaces --cov=services --cov=controllers --cov-report=html
```

## Test Modules

1. **test_file_operations.py** - File upload, export, save, load
2. **test_graphing.py** - Graphing, visualization, data preparation
3. **test_data_reading.py** - CAN, GPS, OBD, sensor data reading
4. **test_ai_advisor.py** - AI advisor knowledge, recommendations
5. **test_telemetry_processing.py** - Data filtering, analysis, aggregation
6. **test_integration.py** - Component integration, data flow
7. **test_configuration.py** - Config loading, saving, validation
8. **test_ui_components.py** - UI component functionality
9. **test_error_handling.py** - Error handling, edge cases
10. **test_performance.py** - Performance, memory usage
11. **test_comprehensive_qa.py** - End-to-end workflows, edge cases

## Test Coverage

### File Operations
- ✅ CSV file upload/export
- ✅ JSON file upload/export
- ✅ Excel export (if pandas available)
- ✅ Configuration save/load
- ✅ Session data management

### Graphing
- ✅ Data preparation
- ✅ Multi-sensor data handling
- ✅ Time range selection
- ✅ Zoom operations
- ✅ X-Y plots
- ✅ FFT analysis
- ✅ Histograms
- ✅ Math channels
- ✅ Data export

### Data Reading
- ✅ CAN message reception/parsing
- ✅ GPS fix reading/validation
- ✅ Sensor data reading (analog, digital, I2C)
- ✅ OBD data reading
- ✅ Data normalization

### AI Advisor
- ✅ Knowledge retrieval
- ✅ Question parsing
- ✅ Answer generation
- ✅ Setup recommendations
- ✅ Telemetry-aware recommendations

### Telemetry Processing
- ✅ Outlier detection
- ✅ Data filtering (moving average, median)
- ✅ Correlation analysis
- ✅ Statistical analysis
- ✅ Trend analysis
- ✅ Data aggregation

### Integration
- ✅ CAN to telemetry flow
- ✅ GPS to telemetry flow
- ✅ Sensor to telemetry flow
- ✅ Data stream integration
- ✅ UI data integration

### Error Handling
- ✅ CAN connection failures
- ✅ GPS no fix scenarios
- ✅ Invalid data handling
- ✅ File operation errors
- ✅ Data validation

### Performance
- ✅ Large dataset processing
- ✅ Data filtering performance
- ✅ Memory usage (buffer limits)
- ✅ Concurrent operations

## Issues Reporting

After running tests, check:
- `test_report.txt` - Detailed test results
- `test_issues.json` - Issues found during testing

## Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock numpy
```

## Running on Raspberry Pi

SSH to Pi and run:
```bash
cd /home/aituner/AITUNER/2025-AI-TUNER-AGENTV3
python3 tests/run_all_tests.py
```

## Continuous Integration

This test suite can be integrated into CI/CD pipelines:
```yaml
# Example GitHub Actions
- name: Run Tests
  run: pytest tests/ -v --tb=short
```

## Notes

- Some tests require hardware (CAN, GPS) - these are marked and will skip if hardware unavailable
- UI tests are limited (Qt requires display) - focus on data/logic testing
- Performance tests have timing thresholds that may vary by hardware

