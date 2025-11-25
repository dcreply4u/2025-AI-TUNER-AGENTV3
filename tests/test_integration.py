"""
Integration tests for AI Tuner Agent.

Tests the integration between multiple components.
"""

import pytest
import time

from core.config_manager import ConfigManager
from core.data_validator import DataValidator
from core.error_handler import ErrorHandler
from services.data_logger import DataLogger
from services.performance_tracker import PerformanceTracker


class TestIntegration:
    """Integration test suite."""

    def test_data_flow(self, temp_dir, sample_telemetry_data):
        """Test complete data flow: validation -> logging."""
        # Setup
        validator = DataValidator()
        logger = DataLogger(log_dir=str(temp_dir / "logs"))

        # Validate
        results = validator.validate(sample_telemetry_data)
        assert len(results) > 0

        # Log
        logger.log(sample_telemetry_data)

        # Verify log file exists
        assert logger.file_path.exists()

    def test_error_handling_integration(self, error_handler, data_validator, sample_invalid_telemetry_data):
        """Test error handling with data validation."""
        # Validate invalid data
        results = data_validator.validate(sample_invalid_telemetry_data)

        # Check for errors
        errors = [r for r in results if r.level.value in ["error", "critical"]]
        assert len(errors) > 0

        # Handle errors
        for error_result in errors:
            error = ValueError(error_result.message)
            error_handler.handle_error(error, "data_validator", ErrorSeverity.MEDIUM)

        assert len(error_handler.error_history) > 0

    def test_performance_tracking(self, performance_tracker):
        """Test performance tracking integration."""
        # Simulate speed updates
        for speed in [0, 10, 20, 30, 40, 50, 60]:
            performance_tracker.update_speed(speed, timestamp=time.time())
            time.sleep(0.1)

        snapshot = performance_tracker.snapshot()
        assert snapshot is not None
        assert "0-60 mph" in snapshot.metrics
        assert snapshot.metrics["0-60 mph"] is not None

    def test_config_and_logging(self, config_manager, temp_dir):
        """Test configuration with logging."""
        # Create profile
        profile = config_manager.create_profile("Test Vehicle", obd_port="/dev/ttyUSB0")

        # Create logger with profile settings
        logger = DataLogger(log_dir=str(temp_dir / "logs"))

        # Log some data
        test_data = {"Engine_RPM": 3000.0, "Vehicle_Speed": 60.0}
        logger.log(test_data)

        assert logger.file_path.exists()

    def test_multiple_components(self, temp_dir):
        """Test multiple components working together."""
        # Initialize components
        config_manager = ConfigManager(config_file=str(temp_dir / "config.json"))
        validator = DataValidator()
        logger = DataLogger(log_dir=str(temp_dir / "logs"))
        error_handler = ErrorHandler()

        # Create profile
        config_manager.create_profile("Test Vehicle")

        # Process data
        data = {"Engine_RPM": 3000.0, "Coolant_Temp": 90.0}

        # Validate
        results = validator.validate(data)

        # Log if valid
        if all(r.valid for r in results):
            logger.log(data)
        else:
            # Handle validation errors
            for result in results:
                if not result.valid:
                    error = ValueError(result.message)
                    error_handler.handle_error(error, "validator", ErrorSeverity.MEDIUM)

        # Verify everything worked
        assert logger.file_path.exists()
        assert len(config_manager.list_profiles()) > 0

