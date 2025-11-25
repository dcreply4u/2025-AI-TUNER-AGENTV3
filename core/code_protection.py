"""
Code Protection System - Protect codebase from modification/theft on hardware

This implements multiple layers of protection:
1. Code obfuscation/compilation (PyInstaller/Nuitka)
2. License verification
3. Anti-tampering checks
4. Encrypted configuration
5. Secure boot verification
6. Runtime integrity checks
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import sys
import time
from pathlib import Path
from typing import Dict, Optional

try:
    import cryptography
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None  # type: ignore

# YubiKey integration (optional)
try:
    from core.yubikey_auth import YubiKeyAuth, YubiKeyProtectedApp
    YUBIKEY_AVAILABLE = True
except ImportError:
    YUBIKEY_AVAILABLE = False
    YubiKeyAuth = None  # type: ignore
    YubiKeyProtectedApp = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class CodeProtection:
    """
    Code protection system for hardware deployment.
    
    Protects against:
    - Code theft/copying
    - Unauthorized modification
    - Reverse engineering
    - Unauthorized access
    """

    def __init__(
        self,
        license_key: Optional[str] = None,
        require_yubikey: bool = False,
        yubikey_serial: Optional[str] = None,
    ) -> None:
        """
        Initialize code protection.

        Args:
            license_key: License key for device (optional, can be set via env)
            require_yubikey: Require YubiKey for operation
            yubikey_serial: Required YubiKey serial number
        """
        self.license_key = license_key or os.environ.get("AI_TUNER_LICENSE_KEY")
        self.device_id = self._get_device_id()
        self.is_protected = self._check_protection_mode()
        self.integrity_checksum = self._calculate_integrity_checksum()
        
        # YubiKey integration
        self.require_yubikey = require_yubikey
        self.yubikey_serial = yubikey_serial or os.environ.get("AI_TUNER_YUBIKEY_SERIAL")
        self.yubikey_auth: Optional[YubiKeyAuth] = None
        if require_yubikey and YUBIKEY_AVAILABLE and YubiKeyAuth:
            self.yubikey_auth = YubiKeyAuth(require_yubikey=True)

    def _get_device_id(self) -> str:
        """Get unique device ID (hardware-based)."""
        try:
            # Try to get MAC address (most reliable)
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0,2*6,2)][::-1])
            return mac
        except Exception:
            # Fallback: use machine name + platform
            return f"{platform.node()}-{platform.machine()}"

    def _check_protection_mode(self) -> bool:
        """
        Check if running in protected mode (compiled/obfuscated).
        
        Returns:
            True if code is protected (compiled), False if source code
        """
        # Check if running from PyInstaller bundle
        if getattr(sys, 'frozen', False):
            return True
        
        # Check if running from Nuitka
        if '__compiled__' in globals():
            return True
        
        # Check if .pyc files only (no .py source)
        main_file = Path(sys.argv[0] if sys.argv else __file__)
        if main_file.suffix == '.exe' or main_file.suffix == '':
            # Could be compiled
            return True
        
        return False

    def _calculate_integrity_checksum(self) -> str:
        """Calculate checksum of critical files for integrity checking."""
        try:
            # Get main application file
            main_file = Path(sys.argv[0] if sys.argv else __file__)
            if main_file.exists():
                with open(main_file, 'rb') as f:
                    content = f.read()
                    return hashlib.sha256(content).hexdigest()
        except Exception:
            pass
        return ""

    def verify_license(self) -> bool:
        """
        Verify device license (with YubiKey if enabled).
        
        Returns:
            True if license is valid, False otherwise
        """
        # If YubiKey required, use hardware verification
        if self.require_yubikey and self.yubikey_auth:
            return self.yubikey_auth.verify_license_yubikey(self.yubikey_serial)
        
        # Standard license verification
        if not self.license_key:
            LOGGER.warning("No license key provided")
            return False
        
        # Simple license verification (can be enhanced with server-side validation)
        # In production, this should validate against a license server
        try:
            # Check license format (example: AI-TUNER-XXXX-XXXX-XXXX)
            if len(self.license_key) < 20:
                return False
            
            # Verify license matches device (basic check)
            # In production, use cryptographic signature
            license_hash = hashlib.sha256(
                f"{self.license_key}-{self.device_id}".encode()
            ).hexdigest()
            
            # Store valid license hash (would be in secure storage in production)
            valid_hash = os.environ.get("AI_TUNER_LICENSE_HASH")
            if valid_hash:
                return license_hash == valid_hash
            
            # For development: accept any license key
            # In production: require valid license server validation
            return True
            
        except Exception as e:
            LOGGER.error("License verification failed: %s", e)
            return False

    def check_integrity(self) -> bool:
        """
        Check code integrity (anti-tampering).
        
        Returns:
            True if code is intact, False if tampered
        """
        try:
            current_checksum = self._calculate_integrity_checksum()
            if self.integrity_checksum and current_checksum != self.integrity_checksum:
                LOGGER.error("Code integrity check failed - possible tampering!")
                return False
            return True
        except Exception as e:
            LOGGER.error("Integrity check error: %s", e)
            return False

    def verify_secure_boot(self) -> bool:
        """
        Verify secure boot (check if system is in secure mode).
        Uses YubiKey if available for hardware verification.
        
        Returns:
            True if secure boot is active
        """
        # If YubiKey available, use hardware verification
        if self.yubikey_auth:
            return self.yubikey_auth.verify_secure_boot_yubikey()
        
        # Standard secure boot check
        # Check if running on expected hardware
        if platform.system() == "Linux":
            # Check if on reTerminal or expected device
            try:
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read().strip()
                    # Verify it's the expected hardware
                    if "reTerminal" in model or "Raspberry Pi" in model:
                        return True
            except Exception:
                pass
        
        # For development, allow any platform
        # In production, enforce specific hardware
        return True

    def encrypt_config(self, data: Dict, key: Optional[bytes] = None) -> bytes:
        """
        Encrypt configuration data.
        
        Args:
            data: Configuration data to encrypt
            key: Encryption key (defaults to device-based key)
            
        Returns:
            Encrypted data
        """
        if not CRYPTO_AVAILABLE:
            LOGGER.warning("Cryptography not available, config not encrypted")
            import json
            return json.dumps(data).encode()
        
        if key is None:
            # Generate device-based key
            key = self._generate_device_key()
        
        fernet = Fernet(key)
        import json
        encrypted = fernet.encrypt(json.dumps(data).encode())
        return encrypted

    def decrypt_config(self, encrypted_data: bytes, key: Optional[bytes] = None) -> Dict:
        """
        Decrypt configuration data.
        
        Args:
            encrypted_data: Encrypted configuration
            key: Decryption key (defaults to device-based key)
            
        Returns:
            Decrypted configuration data
        """
        if not CRYPTO_AVAILABLE:
            import json
            return json.loads(encrypted_data.decode())
        
        if key is None:
            key = self._generate_device_key()
        
        fernet = Fernet(key)
        import json
        decrypted = fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode())

    def _generate_device_key(self) -> bytes:
        """Generate device-specific encryption key."""
        if not CRYPTO_AVAILABLE:
            # Fallback: use device ID hash
            return hashlib.sha256(self.device_id.encode()).digest()[:32]
        
        # Use PBKDF2 to derive key from device ID
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ai_tuner_salt',  # In production, use random salt per device
            iterations=100000,
        )
        key = kdf.derive(self.device_id.encode())
        return key

    def protect_runtime(self) -> bool:
        """
        Enable runtime protection (anti-debugging, etc.).
        
        Returns:
            True if protection enabled
        """
        try:
            # Check for debugger attachment
            if sys.gettrace() is not None:
                LOGGER.warning("Debugger detected - disabling protection features")
                return False
            
            # Check for common reverse engineering tools
            suspicious_modules = ['pdb', 'pydevd', 'debugpy', 'pudb']
            for module in suspicious_modules:
                if module in sys.modules:
                    LOGGER.warning("Suspicious module detected: %s", module)
                    return False
            
            return True
        except Exception as e:
            LOGGER.error("Runtime protection error: %s", e)
            return False

    def enforce_protection(self) -> bool:
        """
        Enforce all protection measures.
        
        Returns:
            True if all checks pass, False otherwise
        """
        checks = [
            ("License", self.verify_license()),
            ("Integrity", self.check_integrity()),
            ("Secure Boot", self.verify_secure_boot()),
            ("Runtime", self.protect_runtime()),
        ]
        
        all_passed = all(check[1] for check in checks)
        
        if not all_passed:
            failed = [name for name, passed in checks if not passed]
            LOGGER.error("Protection checks failed: %s", ", ".join(failed))
            
            # In production, exit or disable features
            # For development, just warn
            if self.is_protected:
                LOGGER.critical("CRITICAL: Protection failure - application may exit")
                # sys.exit(1)  # Uncomment in production
        
        return all_passed


class SecureConfigManager:
    """Secure configuration manager with encryption."""

    def __init__(self, protection: CodeProtection) -> None:
        self.protection = protection
        self.config_path = Path("config/secure_config.enc")

    def save_config(self, config: Dict) -> bool:
        """Save encrypted configuration."""
        try:
            encrypted = self.protection.encrypt_config(config)
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'wb') as f:
                f.write(encrypted)
            return True
        except Exception as e:
            LOGGER.error("Failed to save secure config: %s", e)
            return False

    def load_config(self) -> Optional[Dict]:
        """Load and decrypt configuration."""
        try:
            if not self.config_path.exists():
                return None
            with open(self.config_path, 'rb') as f:
                encrypted = f.read()
            return self.protection.decrypt_config(encrypted)
        except Exception as e:
            LOGGER.error("Failed to load secure config: %s", e)
            return None


__all__ = ["CodeProtection", "SecureConfigManager"]

