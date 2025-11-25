"""
Tests for ErrorHandler.
"""

import pytest

from core.error_handler import ErrorHandler, ErrorSeverity


class TestErrorHandler:
    """Test suite for ErrorHandler."""

    def test_handle_error(self, error_handler):
        """Test basic error handling."""
        error = ValueError("Test error")
        context = error_handler.handle_error(error, "test_component", ErrorSeverity.MEDIUM)

        assert context.error_type == "ValueError"
        assert context.component == "test_component"
        assert context.severity == ErrorSeverity.MEDIUM
        assert len(error_handler.error_history) > 0

    def test_error_recovery(self, error_handler):
        """Test error recovery."""
        # Register recovery strategy
        recovered = False

        def recovery_strategy(error, context):
            nonlocal recovered
            recovered = True
            return True

        error_handler.register_recovery_strategy(ConnectionError, recovery_strategy)

        error = ConnectionError("Connection failed")
        context = error_handler.handle_error(error, "test_component", attempt_recovery=True)

        assert context.recovery_attempted
        assert recovered

    def test_error_callback(self, error_handler):
        """Test error callbacks."""
        callback_called = False
        callback_context = None

        def callback(context):
            nonlocal callback_called, callback_context
            callback_called = True
            callback_context = context

        error_handler.register_error_callback(callback)

        error = ValueError("Test error")
        error_handler.handle_error(error, "test_component")

        assert callback_called
        assert callback_context is not None

    def test_error_statistics(self, error_handler):
        """Test error statistics."""
        error_handler.handle_error(ValueError("Error 1"), "component1", ErrorSeverity.LOW)
        error_handler.handle_error(ValueError("Error 2"), "component1", ErrorSeverity.MEDIUM)
        error_handler.handle_error(ValueError("Error 3"), "component2", ErrorSeverity.HIGH)

        stats = error_handler.get_error_stats()

        assert stats["total_errors"] == 3
        assert "component1" in stats["by_component"]
        assert stats["by_component"]["component1"] == 2

    def test_get_recent_errors(self, error_handler):
        """Test getting recent errors."""
        for i in range(5):
            error_handler.handle_error(ValueError(f"Error {i}"), "test_component")

        recent = error_handler.get_recent_errors(limit=3)
        assert len(recent) == 3

        filtered = error_handler.get_recent_errors(component="test_component", limit=10)
        assert len(filtered) == 5

