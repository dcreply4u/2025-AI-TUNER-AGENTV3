"""
Input Validation and Sanitization
Provides secure input validation for user inputs.
"""

from __future__ import annotations

import re
import html
from typing import Any, Optional, List, Dict
import logging

LOGGER = logging.getLogger(__name__)


class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers (onclick, onload, etc.)
        r'data:text/html',  # Data URLs with HTML
        r'vbscript:',  # VBScript protocol
    ]
    
    # SQL injection patterns (basic)
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(\\)|(--)|(\*)|(\/\*)|(\*\/)|(\+)|(\|)|(\&)|(\%)|(\$)|(\#)|(\@)|(\!))",
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$(){}]',  # Command separators
        r'\b(cat|ls|rm|mv|cp|chmod|chown|sudo|su)\b',  # Dangerous commands
    ]
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000, allow_html: bool = False) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (default: False, will escape)
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Trim whitespace
        text = text.strip()
        
        # Check length
        if len(text) > max_length:
            LOGGER.warning(f"Input text truncated from {len(text)} to {max_length} characters")
            text = text[:max_length]
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # HTML escape if not allowing HTML
        if not allow_html:
            text = html.escape(text)
        
        # Remove dangerous patterns
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text
    
    @staticmethod
    def validate_chat_input(text: str) -> tuple[bool, Optional[str]]:
        """
        Validate chat input for security.
        
        Args:
            text: Chat input text
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Input cannot be empty"
        
        # Check length
        if len(text) > 5000:
            return False, "Input too long (max 5000 characters)"
        
        # Check for SQL injection patterns
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                LOGGER.warning(f"Potential SQL injection detected in chat input")
                return False, "Invalid input detected"
        
        # Check for command injection patterns (only if executing commands)
        # Note: Chat input shouldn't execute commands, but validate anyway
        for pattern in InputValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                LOGGER.warning(f"Potential command injection detected in chat input")
                # Don't reject, but log - chat input shouldn't execute commands
        
        # Check for script tags
        if re.search(r'<script', text, re.IGNORECASE):
            return False, "Script tags not allowed"
        
        return True, None
    
    @staticmethod
    def validate_numeric_input(value: Any, min_value: Optional[float] = None, 
                              max_value: Optional[float] = None) -> tuple[bool, Optional[str], Optional[float]]:
        """
        Validate numeric input.
        
        Args:
            value: Input value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, error_message, converted_value)
        """
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, "Invalid number", None
        
        # Check for NaN or Infinity
        if not (num_value == num_value):  # NaN check
            return False, "Invalid number (NaN)", None
        
        if abs(num_value) == float('inf'):
            return False, "Invalid number (Infinity)", None
        
        # Check bounds
        if min_value is not None and num_value < min_value:
            return False, f"Value below minimum: {num_value} < {min_value}", None
        
        if max_value is not None and num_value > max_value:
            return False, f"Value above maximum: {num_value} > {max_value}", None
        
        return True, None, num_value
    
    @staticmethod
    def validate_parameter_name(name: str) -> tuple[bool, Optional[str]]:
        """
        Validate ECU parameter name.
        
        Args:
            name: Parameter name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Parameter name cannot be empty"
        
        # Check length
        if len(name) > 100:
            return False, "Parameter name too long (max 100 characters)"
        
        # Check for dangerous characters
        if re.search(r'[<>"\';\\]', name):
            return False, "Parameter name contains invalid characters"
        
        # Check for path traversal
        if '..' in name or '/' in name or '\\' in name:
            return False, "Parameter name contains path traversal characters"
        
        return True, None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other issues.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename


