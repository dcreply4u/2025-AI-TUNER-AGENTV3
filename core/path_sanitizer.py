"""
Path Sanitization Utility
Provides secure path operations to prevent path traversal attacks.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, List

LOGGER = __import__('logging').getLogger(__name__)


class PathSanitizer:
    """Utility class for sanitizing and validating file paths."""
    
    # Dangerous path patterns
    DANGEROUS_PATTERNS = [
        r'\.\.',  # Parent directory
        r'\.\./',  # Parent directory with slash
        r'\.\.\\',  # Parent directory with backslash (Windows)
        r'//',  # Multiple slashes (potential issue)
        r'\\',  # Backslashes (potential issue on Unix)
    ]
    
    # Allowed characters in paths (adjust as needed)
    ALLOWED_CHARS = r'[a-zA-Z0-9_\-\./\\: ]'
    
    @staticmethod
    def sanitize_path(
        user_input: str,
        base_dir: Optional[Path] = None,
        allow_absolute: bool = False
    ) -> Optional[Path]:
        """
        Sanitize a user-provided path to prevent path traversal attacks.
        
        Args:
            user_input: User-provided path string
            base_dir: Base directory to resolve relative paths against
            allow_absolute: Whether to allow absolute paths
            
        Returns:
            Sanitized Path object, or None if invalid
            
        Raises:
            ValueError: If path contains dangerous patterns
        """
        if not user_input or not isinstance(user_input, str):
            return None
        
        # Remove null bytes
        user_input = user_input.replace('\x00', '')
        
        # Check for dangerous patterns
        for pattern in PathSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, user_input):
                LOGGER.warning(f"Path traversal attempt detected: {user_input}")
                raise ValueError(f"Invalid path: contains dangerous pattern '{pattern}'")
        
        # Normalize path
        try:
            path = Path(user_input)
        except Exception as e:
            LOGGER.warning(f"Invalid path format: {user_input} - {e}")
            return None
        
        # Resolve relative to base directory
        if base_dir:
            if path.is_absolute() and not allow_absolute:
                LOGGER.warning(f"Absolute path not allowed: {user_input}")
                return None
            
            # Resolve relative to base
            if not path.is_absolute():
                resolved = (base_dir / path).resolve()
            else:
                resolved = path.resolve()
            
            # Verify resolved path is within base directory
            try:
                resolved.relative_to(base_dir.resolve())
            except ValueError:
                LOGGER.warning(f"Path traversal attempt: {user_input} resolves outside base directory")
                return None
            
            return resolved
        else:
            # No base directory, just normalize
            if path.is_absolute() and not allow_absolute:
                return None
            return path.resolve() if path.is_absolute() else path
    
    @staticmethod
    def validate_filename(filename: str, max_length: int = 255) -> bool:
        """
        Validate a filename (not a full path).
        
        Args:
            filename: Filename to validate
            max_length: Maximum filename length
            
        Returns:
            True if valid, False otherwise
        """
        if not filename or len(filename) > max_length:
            return False
        
        # Check for path separators
        if '/' in filename or '\\' in filename:
            return False
        
        # Check for null bytes
        if '\x00' in filename:
            return False
        
        # Check for dangerous characters (Windows)
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + \
                        [f'COM{i}' for i in range(1, 10)] + \
                        [f'LPT{i}' for i in range(1, 10)]
        if filename.upper() in reserved_names:
            return False
        
        return True
    
    @staticmethod
    def safe_join(base: Path, *parts: str) -> Optional[Path]:
        """
        Safely join path parts, preventing path traversal.
        
        Args:
            base: Base directory
            *parts: Path parts to join
            
        Returns:
            Joined Path, or None if invalid
        """
        try:
            result = base
            for part in parts:
                # Validate each part
                if not PathSanitizer.validate_filename(part):
                    LOGGER.warning(f"Invalid path part: {part}")
                    return None
                
                # Join and resolve
                result = (result / part).resolve()
                
                # Verify still within base
                try:
                    result.relative_to(base.resolve())
                except ValueError:
                    LOGGER.warning(f"Path traversal detected in part: {part}")
                    return None
            
            return result
        except Exception as e:
            LOGGER.warning(f"Error joining paths: {e}")
            return None
    
    @staticmethod
    def get_safe_output_path(
        user_input: str,
        output_dir: Path,
        default_name: str = "output",
        extension: Optional[str] = None
    ) -> Path:
        """
        Get a safe output path from user input.
        
        Args:
            user_input: User-provided filename or path
            output_dir: Base output directory
            default_name: Default filename if input is invalid
            extension: File extension to add if not present
            
        Returns:
            Safe output Path
        """
        # Extract filename from input
        if '/' in user_input or '\\' in user_input:
            # User provided a path, extract filename
            filename = Path(user_input).name
        else:
            filename = user_input
        
        # Validate filename
        if not PathSanitizer.validate_filename(filename):
            LOGGER.warning(f"Invalid filename, using default: {user_input}")
            filename = default_name
        
        # Add extension if needed
        if extension and not filename.endswith(extension):
            filename = f"{filename}.{extension}"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Return safe path
        return output_dir / filename


# Convenience functions
def sanitize_path(user_input: str, base_dir: Optional[Path] = None, allow_absolute: bool = False) -> Optional[Path]:
    """Convenience function for path sanitization."""
    return PathSanitizer.sanitize_path(user_input, base_dir, allow_absolute)


def validate_filename(filename: str, max_length: int = 255) -> bool:
    """Convenience function for filename validation."""
    return PathSanitizer.validate_filename(filename, max_length)


def safe_join(base: Path, *parts: str) -> Optional[Path]:
    """Convenience function for safe path joining."""
    return PathSanitizer.safe_join(base, *parts)


__all__ = [
    "PathSanitizer",
    "sanitize_path",
    "validate_filename",
    "safe_join",
]

