"""
Enhanced Security Features
Enterprise-grade security for connected vehicles.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event."""
    event_id: str
    event_type: str
    severity: SecurityLevel
    timestamp: float
    description: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    action_taken: Optional[str] = None


class SecurityEnhancements:
    """
    Enhanced security features.
    
    Features:
    - End-to-end encryption
    - Secure key management
    - Intrusion detection
    - Security auditing
    - Access control
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize security enhancements.
        
        Args:
            master_key: Master encryption key (generated if None)
        """
        if not CRYPTO_AVAILABLE:
            LOGGER.warning("Cryptography library not available - security features limited")
        
        self.master_key = master_key or self._generate_master_key()
        self.cipher = None
        
        if CRYPTO_AVAILABLE:
            try:
                self.cipher = Fernet(self.master_key)
            except Exception as e:
                LOGGER.error("Failed to initialize cipher: %s", e)
        
        self.security_events: List[SecurityEvent] = []
        self.failed_attempts: Dict[str, int] = {}
        self.blocked_ips: List[str] = []
        
        # Security policies
        self.max_failed_attempts = 5
        self.block_duration = 3600  # 1 hour
    
    def _generate_master_key(self) -> bytes:
        """Generate master encryption key."""
        if CRYPTO_AVAILABLE:
            return Fernet.generate_key()
        else:
            # Fallback: use HMAC-based key
            return secrets.token_bytes(32)
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
        
        Returns:
            Encrypted data (base64 encoded)
        """
        if not CRYPTO_AVAILABLE or not self.cipher:
            # Fallback: simple encoding (not secure, but better than plaintext)
            return base64.b64encode(data.encode()).decode() if 'base64' in globals() else data
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            LOGGER.error("Encryption failed: %s", e)
            return data
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
        
        Returns:
            Decrypted data
        """
        if not CRYPTO_AVAILABLE or not self.cipher:
            # Fallback: simple decoding
            try:
                return base64.b64decode(encrypted_data).decode() if 'base64' in globals() else encrypted_data
            except Exception:
                return encrypted_data
        
        try:
            decoded = base64.b64decode(encrypted_data)
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            LOGGER.error("Decryption failed: %s", e)
            raise
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        Hash password using secure method.
        
        Args:
            password: Password to hash
            salt: Salt (generated if None)
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 for password hashing
        if CRYPTO_AVAILABLE:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            key = kdf.derive(password.encode())
            hashed = base64.b64encode(key).decode()
        else:
            # Fallback: SHA256 with salt
            hashed = hashlib.sha256(password.encode() + salt).hexdigest()
        
        return hashed, salt
    
    def verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """
        Verify password.
        
        Args:
            password: Password to verify
            hashed_password: Stored hash
            salt: Stored salt
        
        Returns:
            True if password matches
        """
        computed_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, hashed_password)
    
    def check_intrusion(
        self,
        source_ip: str,
        user_id: Optional[str] = None,
        action: str = "access",
    ) -> bool:
        """
        Check for intrusion attempts.
        
        Args:
            source_ip: Source IP address
            user_id: User ID (optional)
            action: Action being attempted
        
        Returns:
            True if access should be allowed
        """
        # Check if IP is blocked
        if source_ip in self.blocked_ips:
            self._log_security_event(
                "blocked_access",
                SecurityLevel.HIGH,
                f"Blocked IP attempted access: {source_ip}",
                source_ip=source_ip,
            )
            return False
        
        # Check failed attempts
        key = f"{source_ip}:{user_id or 'anonymous'}"
        failed_count = self.failed_attempts.get(key, 0)
        
        if failed_count >= self.max_failed_attempts:
            # Block IP
            self.blocked_ips.append(source_ip)
            self._log_security_event(
                "ip_blocked",
                SecurityLevel.CRITICAL,
                f"IP blocked due to {failed_count} failed attempts: {source_ip}",
                source_ip=source_ip,
                user_id=user_id,
                action_taken="ip_blocked",
            )
            return False
        
        return True
    
    def record_failed_attempt(
        self,
        source_ip: str,
        user_id: Optional[str] = None,
        reason: str = "authentication_failed",
    ) -> None:
        """Record failed access attempt."""
        key = f"{source_ip}:{user_id or 'anonymous'}"
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1
        
        self._log_security_event(
            "failed_attempt",
            SecurityLevel.MEDIUM,
            f"Failed attempt: {reason}",
            source_ip=source_ip,
            user_id=user_id,
        )
    
    def reset_failed_attempts(self, source_ip: str, user_id: Optional[str] = None) -> None:
        """Reset failed attempts counter."""
        key = f"{source_ip}:{user_id or 'anonymous'}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def _log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        action_taken: Optional[str] = None,
    ) -> None:
        """Log security event."""
        event = SecurityEvent(
            event_id=secrets.token_hex(16),
            event_type=event_type,
            severity=severity,
            timestamp=time.time(),
            description=description,
            source_ip=source_ip,
            user_id=user_id,
            action_taken=action_taken,
        )
        
        self.security_events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self.security_events) > 1000:
            self.security_events.pop(0)
        
        # Log to logger
        log_level = {
            SecurityLevel.LOW: logging.INFO,
            SecurityLevel.MEDIUM: logging.WARNING,
            SecurityLevel.HIGH: logging.ERROR,
            SecurityLevel.CRITICAL: logging.CRITICAL,
        }.get(severity, logging.INFO)
        
        LOGGER.log(log_level, "Security event: %s - %s", event_type, description)
    
    def get_security_events(
        self,
        severity: Optional[SecurityLevel] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """Get security events."""
        events = self.security_events.copy()
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events[-limit:]
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(length)
    
    def verify_hmac(
        self,
        message: str,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            message: Original message
            signature: HMAC signature
            secret: Secret key
        
        Returns:
            True if signature is valid
        """
        expected_signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)



