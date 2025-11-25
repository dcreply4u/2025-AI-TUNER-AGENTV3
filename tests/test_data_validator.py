"""
Tests for DataValidator.
"""

import pytest

from core.data_validator import DataValidator, ValidationLevel


class TestDataValidator:
    """Test suite for DataValidator."""

    def test_valid_data(self, data_validator, sample_telemetry_data):
        """Test validation of valid data."""
        results = data_validator.validate(sample_telemetry_data)

        # All should pass or have warnings only
        for result in results:
            assert result.valid or result.level == ValidationLevel.WARNING
            assert result.level != ValidationLevel.ERROR
            assert result.level != ValidationLevel.CRITICAL

    def test_invalid_data(self, data_validator, sample_invalid_telemetry_data):
        """Test validation of invalid data."""
        results = data_validator.validate(sample_invalid_telemetry_data)

        # Should have errors or critical issues
        has_errors = any(
            r.level == ValidationLevel.ERROR or r.level == ValidationLevel.CRITICAL for r in results
        )
        assert has_errors

    def test_outlier_detection(self, data_validator):
        """Test outlier detection."""
        # Feed normal values
        for i in range(20):
            data_validator.validate({"Engine_RPM": 3000.0 + (i * 10)})

        # Feed outlier
        results = data_validator.validate({"Engine_RPM": 10000.0})

        # Should detect outlier
        outlier_detected = any("outlier" in r.message.lower() for r in results)
        assert outlier_detected

    def test_rate_of_change(self, data_validator):
        """Test rate of change validation."""
        import time

        # Normal change
        data_validator.validate({"Engine_RPM": 3000.0})
        time.sleep(0.1)
        data_validator.validate({"Engine_RPM": 3100.0})

        # Rapid change (should trigger warning)
        time.sleep(0.1)
        results = data_validator.validate({"Engine_RPM": 8000.0})

        rapid_change = any("rapidly" in r.message.lower() for r in results)
        assert rapid_change

    def test_metric_definition(self, data_validator):
        """Test adding custom metric definition."""
        from core.data_validator import MetricDefinition

        custom_metric = MetricDefinition(
            name="CustomMetric",
            min_value=0,
            max_value=100,
            expected_range=(10, 90),
        )

        data_validator.add_metric_definition(custom_metric)

        results = data_validator.validate({"CustomMetric": 50.0})
        assert len(results) > 0
        assert any(r.metric_name == "CustomMetric" for r in results)

    def test_validation_summary(self, data_validator, sample_telemetry_data):
        """Test validation summary generation."""
        results = data_validator.validate(sample_telemetry_data)
        summary = data_validator.get_validation_summary(results)

        assert "total" in summary
        assert "passed" in summary
        assert "warnings" in summary
        assert "errors" in summary
        assert "quality_score" in summary
        assert summary["total"] > 0

