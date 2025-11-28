# Comprehensive QA Test Suite

## Overview

This directory contains a comprehensive QA test suite for the AI Tuner Agent application. The test suite covers all major features and functionality, ensuring quality and reliability.

## Running Tests

### Run All Tests

```bash
python tests/run_all_tests.py
```

This will:
- Run all test modules
- Generate detailed reports (text, JSON, PDF)
- Create an issues list for review
- Provide comprehensive coverage statistics

### Run Individual Test Modules

```bash
# Using pytest directly
pytest tests/test_file_operations.py -v
pytest tests/test_graphing.py -v
pytest tests/test_ai_advisor.py -v
# etc.
```

## Test Coverage

### Core Functionality
- **File Operations** (`test_file_operations.py`): File upload, export, CSV/JSON handling
- **Graphing & Visualization** (`test_graphing.py`): Data plotting, chart generation
- **Data Reading** (`test_data_reading.py`): CAN, GPS, OBD, sensor interfaces
- **AI Advisor** (`test_ai_advisor.py`): AI advisor knowledge, responses, context
- **Telemetry Processing** (`test_telemetry_processing.py`): Data processing, calculations

### Advanced Features
- **Virtual Dyno** (`test_virtual_dyno.py`): Virtual dyno calculations, power estimation
- **Video Recording** (`test_video_recording.py`): Video recording, streaming, overlays
- **GPS & Lap Timing** (`test_gps_lap_timing.py`): GPS functionality, lap detection, performance tracking
- **Voice Control** (`test_voice_control.py`): Voice recognition, TTS, voice commands
- **AI Racing Coach** (`test_ai_racing_coach.py`): AI coaching advice, lap analysis
- **Auto-Tuning Engine** (`test_auto_tuning.py`): Automatic ECU parameter optimization
- **Enhanced Graphing** (`test_enhanced_graphing.py`): X-Y plots, FFT, histograms, math channels

### Integration & Quality
- **Integration** (`test_integration.py`): Module integration, data flow
- **Configuration** (`test_configuration.py`): Configuration management
- **UI Components** (`test_ui_components.py`): UI component functionality
- **Error Handling** (`test_error_handling.py`): Error handling mechanisms
- **Performance** (`test_performance.py`): Performance benchmarks
- **CAN Bus** (`test_can_bus.py`): CAN interface, decoder, simulator
- **Comprehensive QA** (`test_comprehensive_qa.py`): End-to-end scenarios

## Test Reports

After running tests, the following reports are generated:

1. **Text Report** (`test_report.txt`): Human-readable summary
2. **JSON Report** (`test_report.json`): Machine-readable results
3. **PDF Report** (`test_report.pdf`): Professional PDF document (requires `reportlab` or `fpdf`)
4. **Issues List** (`test_issues_list.txt`): Prioritized list of issues found

### Installing PDF Dependencies

To generate PDF reports, install one of the following:

```bash
# Option 1 (Recommended)
pip install reportlab

# Option 2
pip install fpdf
```

## Test Structure

### Fixtures

Common test fixtures are defined in `conftest.py`:
- `sample_data`: Sample telemetry data
- `sample_can_message`: Sample CAN message
- `mock_gps_fix`: Mock GPS fix data

### Test Organization

Tests are organized by feature area, with each module testing:
- Import/availability checks
- Basic functionality
- Edge cases
- Error handling
- Integration points

## Continuous Integration

This test suite is designed to be run:
- Before commits (pre-commit hook)
- In CI/CD pipelines
- As part of release validation
- For regression testing

## Adding New Tests

When adding new features:

1. Create a new test file: `tests/test_<feature_name>.py`
2. Add it to the test modules list in `run_all_tests.py`
3. Follow the existing test structure and patterns
4. Include import checks, basic functionality, and error cases

## Troubleshooting

### Tests Fail to Import

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that the project root is in Python path
- Verify module structure matches imports

### PDF Generation Fails

- Install `reportlab` or `fpdf`: `pip install reportlab`
- Check file permissions for report directory
- Review error messages in console output

### Tests Timeout

- Some tests may require hardware (CAN, GPS)
- Use mocking for hardware-dependent tests
- Check network connectivity for web-based tests

## Best Practices

1. **Mock External Dependencies**: Use `unittest.mock` for hardware interfaces
2. **Skip When Appropriate**: Use `pytest.skip()` for optional features
3. **Clear Test Names**: Use descriptive test method names
4. **Isolated Tests**: Each test should be independent
5. **Comprehensive Coverage**: Test happy paths, edge cases, and errors

## Status

This test suite is actively maintained and expanded as new features are added. All tests should pass before merging code changes.
