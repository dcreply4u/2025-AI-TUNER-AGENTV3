"""
Unit tests for input validation.
"""

import pytest
from core.input_validator import InputValidator


class TestInputValidator:
    """Test input validation functions."""
    
    def test_sanitize_text_basic(self):
        """Test basic text sanitization."""
        text = "Hello World"
        result = InputValidator.sanitize_text(text)
        assert result == "Hello World"
    
    def test_sanitize_text_html_escape(self):
        """Test HTML escaping."""
        text = "<script>alert('xss')</script>"
        result = InputValidator.sanitize_text(text, allow_html=False)
        assert "<script>" not in result
        assert "&lt;" in result or "&gt;" in result
    
    def test_sanitize_text_length_limit(self):
        """Test length limiting."""
        text = "a" * 20000
        result = InputValidator.sanitize_text(text, max_length=1000)
        assert len(result) <= 1000
    
    def test_validate_chat_input_valid(self):
        """Test valid chat input."""
        text = "What is AFR?"
        is_valid, error = InputValidator.validate_chat_input(text)
        assert is_valid is True
        assert error is None
    
    def test_validate_chat_input_empty(self):
        """Test empty chat input."""
        is_valid, error = InputValidator.validate_chat_input("")
        assert is_valid is False
        assert error is not None
    
    def test_validate_chat_input_too_long(self):
        """Test chat input that's too long."""
        text = "a" * 6000
        is_valid, error = InputValidator.validate_chat_input(text)
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_validate_chat_input_script_tag(self):
        """Test chat input with script tag."""
        text = "<script>alert('xss')</script>"
        is_valid, error = InputValidator.validate_chat_input(text)
        assert is_valid is False
    
    def test_validate_numeric_input_valid(self):
        """Test valid numeric input."""
        is_valid, error, value = InputValidator.validate_numeric_input("123.45")
        assert is_valid is True
        assert error is None
        assert value == 123.45
    
    def test_validate_numeric_input_invalid(self):
        """Test invalid numeric input."""
        is_valid, error, value = InputValidator.validate_numeric_input("abc")
        assert is_valid is False
        assert error is not None
        assert value is None
    
    def test_validate_numeric_input_bounds(self):
        """Test numeric input with bounds."""
        is_valid, error, value = InputValidator.validate_numeric_input("50", min_value=0, max_value=100)
        assert is_valid is True
        assert value == 50.0
        
        is_valid, error, value = InputValidator.validate_numeric_input("150", min_value=0, max_value=100)
        assert is_valid is False
    
    def test_validate_parameter_name_valid(self):
        """Test valid parameter name."""
        is_valid, error = InputValidator.validate_parameter_name("fuel_map_rpm_1000")
        assert is_valid is True
        assert error is None
    
    def test_validate_parameter_name_invalid_chars(self):
        """Test parameter name with invalid characters."""
        is_valid, error = InputValidator.validate_parameter_name("fuel/map")
        assert is_valid is False
    
    def test_validate_parameter_name_path_traversal(self):
        """Test parameter name with path traversal."""
        is_valid, error = InputValidator.validate_parameter_name("../../../etc/passwd")
        assert is_valid is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        filename = "../../../etc/passwd"
        result = InputValidator.sanitize_filename(filename)
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result

