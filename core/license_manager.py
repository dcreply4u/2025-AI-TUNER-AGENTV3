"""
License Manager - Simple License Key System with YubiKey Support

Manages license validation, demo mode detection, and feature gating.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)

# YubiKey integration (optional)
try:
    from core.yubikey_auth import YubiKeyAuth
    YUBIKEY_AVAILABLE = True
except ImportError:
    YUBIKEY_AVAILABLE = False
    YubiKeyAuth = None  # type: ignore


class LicenseType(Enum):
    """License types."""
    DEMO = "demo"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseManager:
    """
    License Manager - Simple license key system with YubiKey support.
    
    Features:
    - License key validation
    - Device binding
    - YubiKey hardware support
    - Feature gating
    - Demo mode detection
    """
    
    def __init__(self, license_file: Optional[Path] = None) -> None:
        """
        Initialize license manager.
        
        Args:
            license_file: Optional path to license file (default: config/license.json)
        """
        self.license_file = license_file or Path("config/license.json")
        self.device_id = self._get_device_id()
        self.license_data: Optional[Dict] = None
        self.yubikey_auth: Optional[YubiKeyAuth] = None
        self.yubikey_enabled = False
        
        # Load existing license
        self.load_license()
        
        # Initialize YubiKey if available
        self._init_yubikey()
    
    def _get_device_id(self) -> str:
        """Get unique device identifier (MAC address)."""
        try:
            import uuid
            mac = uuid.getnode()
            # Format as MAC address
            mac_str = ':'.join(['{:02x}'.format((mac >> i) & 0xff) 
                               for i in range(0, 8*6, 8)][::-1])
            return mac_str
        except Exception:
            # Fallback: use machine name + platform
            import platform
            return f"{platform.node()}-{platform.machine()}"
    
    def _init_yubikey(self) -> None:
        """Initialize YubiKey authentication if available."""
        if YUBIKEY_AVAILABLE and YubiKeyAuth:
            try:
                self.yubikey_auth = YubiKeyAuth(require_yubikey=False)
                # Check if YubiKey is present
                if self.yubikey_auth.detect_yubikey():
                    self.yubikey_enabled = True
                    LOGGER.info("YubiKey detected and available")
            except Exception as e:
                LOGGER.debug(f"YubiKey initialization failed: {e}")
                self.yubikey_enabled = False
    
    def load_license(self) -> None:
        """Load license from file."""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    self.license_data = json.load(f)
                LOGGER.info("License loaded from file")
            except Exception as e:
                LOGGER.error(f"Failed to load license: {e}")
                self.license_data = None
        else:
            # Check environment variable
            env_key = os.environ.get("AI_TUNER_LICENSE_KEY")
            if env_key:
                # Try to activate from environment
                if self.validate_license_key(env_key):
                    self.activate_license(env_key, save_to_file=False)
    
    def save_license(self) -> bool:
        """Save license to file."""
        if not self.license_data:
            return False
        
        try:
            self.license_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.license_file, 'w') as f:
                json.dump(self.license_data, f, indent=2)
            LOGGER.info("License saved to file")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to save license: {e}")
            return False
    
    def validate_license_key(self, license_key: str) -> bool:
        """
        Validate license key format and checksum.
        
        Format: AI-TUNER-XXXX-XXXX-XXXX-XXXX
        """
        if not license_key:
            return False
        
        # Remove whitespace and convert to uppercase
        license_key = license_key.strip().upper()
        
        # Check format
        parts = license_key.split('-')
        if len(parts) != 5:
            return False
        
        if parts[0] != 'AI' or parts[1] != 'TUNER':
            return False
        
        # Validate segments (4 characters each, alphanumeric)
        for part in parts[2:]:
            if len(part) != 4:
                return False
            if not all(c in 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' for c in part):
                return False
        
        # Validate checksum (last character of last segment)
        key_data = ''.join(parts[2:4])  # First two data segments
        expected_checksum = self._calculate_checksum(key_data)
        actual_checksum = parts[4][-1]  # Last char of checksum segment
        
        return expected_checksum == actual_checksum
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate checksum for license validation."""
        hash_obj = hashlib.md5(data.encode())
        return hash_obj.hexdigest()[-1].upper()
    
    def _decode_license_type(self, license_key: str) -> LicenseType:
        """Decode license type from key."""
        parts = license_key.split('-')
        if len(parts) < 3:
            return LicenseType.DEMO
        
        # First character of third segment indicates type
        type_code = parts[2][0] if len(parts[2]) > 0 else 'D'
        
        type_map = {
            'B': LicenseType.BASIC,
            'P': LicenseType.PRO,
            'E': LicenseType.ENTERPRISE,
            'D': LicenseType.DEMO,
        }
        return type_map.get(type_code, LicenseType.DEMO)
    
    def _decode_expiration(self, license_key: str) -> Optional[datetime]:
        """Decode expiration date from license key (if present)."""
        # For now, licenses don't expire (can be enhanced later)
        # Expiration would be encoded in the key
        return None
    
    def activate_license(
        self,
        license_key: str,
        save_to_file: bool = True,
        use_yubikey: bool = False,
    ) -> tuple[bool, str]:
        """
        Activate license key.
        
        Args:
            license_key: License key to activate
            save_to_file: Save to license file
            use_yubikey: Use YubiKey for activation (if available)
            
        Returns:
            (success, message)
        """
        # Validate format
        if not self.validate_license_key(license_key):
            return False, "Invalid license key format"
        
        # YubiKey activation
        if use_yubikey and self.yubikey_enabled and self.yubikey_auth:
            try:
                if not self.yubikey_auth.verify_license_yubikey():
                    return False, "YubiKey license verification failed"
                # Store license on YubiKey
                LOGGER.info("License activated via YubiKey")
            except Exception as e:
                LOGGER.error(f"YubiKey activation failed: {e}")
                return False, f"YubiKey activation failed: {e}"
        
        # Decode license information
        license_type = self._decode_license_type(license_key)
        expiration = self._decode_expiration(license_key)
        
        # Save license
        self.license_data = {
            'key': license_key,
            'type': license_type.value,
            'device_id': self.device_id,
            'activated': True,
            'activated_date': datetime.now().isoformat(),
            'expires': expiration.isoformat() if expiration else None,
            'yubikey_used': use_yubikey,
        }
        
        if save_to_file:
            if not self.save_license():
                return False, "Failed to save license"
        
        LOGGER.info(f"License activated: {license_type.value}")
        return True, f"License activated: {license_type.value}"
    
    def is_licensed(self) -> bool:
        """Check if valid license is active."""
        # Check YubiKey first (if enabled)
        if self.yubikey_enabled and self.yubikey_auth:
            try:
                if self.yubikey_auth.verify_license_yubikey():
                    return True
            except Exception:
                pass
        
        # Check file-based license
        if not self.license_data:
            return False
        
        # Check if activated
        if not self.license_data.get('activated', False):
            return False
        
        # Check device binding
        stored_device_id = self.license_data.get('device_id')
        if stored_device_id and stored_device_id != self.device_id:
            LOGGER.warning("License device ID mismatch")
            return False
        
        # Check expiration
        expires_str = self.license_data.get('expires')
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str)
                if expires < datetime.now():
                    LOGGER.warning("License has expired")
                    return False
            except Exception:
                pass
        
        return True
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return not self.is_licensed()
    
    def get_license_type(self) -> LicenseType:
        """Get current license type."""
        if self.is_demo_mode():
            return LicenseType.DEMO
        
        if self.license_data:
            license_type_str = self.license_data.get('type', 'demo')
            try:
                return LicenseType(license_type_str)
            except ValueError:
                return LicenseType.DEMO
        
        return LicenseType.DEMO
    
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if feature is enabled for current license.
        
        Features:
        - ecu_tuning_write: Write ECU parameters
        - advanced_ai: ML-based AI features
        - cloud_sync: Cloud synchronization
        - video_recording: Video recording
        - auto_tuning: Auto-tuning engine
        - racing_controls: Racing controls (anti-lag, launch)
        - unlimited_logging: Unlimited data logging
        - export_unlimited: Unlimited exports
        - advanced_tuning: Advanced tuning engine
        """
        license_type = self.get_license_type()
        
        # Feature matrix
        features = {
            'ecu_tuning_write': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'advanced_ai': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'cloud_sync': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'video_recording': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'auto_tuning': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'racing_controls': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'unlimited_logging': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'export_unlimited': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'advanced_tuning': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'session_management': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'lap_detection': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'telemetry_overlay': [LicenseType.PRO, LicenseType.ENTERPRISE],
        }
        
        allowed_types = features.get(feature, [])
        return license_type in allowed_types
    
    def get_license_info(self) -> Dict:
        """Get license information."""
        if self.is_demo_mode():
            return {
                'licensed': False,
                'type': 'demo',
                'device_id': self.device_id,
                'yubikey_available': self.yubikey_enabled,
            }
        
        return {
            'licensed': True,
            'type': self.get_license_type().value,
            'device_id': self.device_id,
            'key': self.license_data.get('key', '')[:20] + '...' if self.license_data else '',
            'activated_date': self.license_data.get('activated_date') if self.license_data else None,
            'expires': self.license_data.get('expires') if self.license_data else None,
            'yubikey_used': self.license_data.get('yubikey_used', False) if self.license_data else False,
            'yubikey_available': self.yubikey_enabled,
        }
    
    def deactivate_license(self) -> bool:
        """Deactivate current license."""
        self.license_data = None
        if self.license_file.exists():
            try:
                self.license_file.unlink()
                LOGGER.info("License deactivated")
                return True
            except Exception as e:
                LOGGER.error(f"Failed to remove license file: {e}")
                return False
        return True
    
    @staticmethod
    def generate_license_key(license_type: LicenseType, device_id: Optional[str] = None) -> str:
        """
        Generate a license key (for testing/admin use).
        
        Args:
            license_type: Type of license to generate
            device_id: Optional device ID for binding
            
        Returns:
            Generated license key
        """
        # Type code
        type_code = {
            LicenseType.BASIC: 'B',
            LicenseType.PRO: 'P',
            LicenseType.ENTERPRISE: 'E',
            LicenseType.DEMO: 'D',
        }.get(license_type, 'D')
        
        # Generate random segments
        segments = []
        for i in range(3):
            if i == 0:
                # First segment: type code + 3 random chars
                segment = type_code + ''.join(
                    secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') 
                    for _ in range(3)
                )
            else:
                # Other segments: 4 random chars
                segment = ''.join(
                    secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') 
                    for _ in range(4)
                )
            segments.append(segment)
        
        # Calculate checksum
        key_data = ''.join(segments[:2])  # First two segments
        checksum = hashlib.md5(key_data.encode()).hexdigest()[-1].upper()
        checksum_segment = ''.join(
            secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') 
            for _ in range(3)
        ) + checksum
        
        segments.append(checksum_segment)
        
        return f"AI-TUNER-{'-'.join(segments)}"


# Global license manager instance
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


__all__ = [
    "LicenseManager",
    "LicenseType",
    "get_license_manager",
]










