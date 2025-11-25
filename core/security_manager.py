"""
ISO/IEC 27001 Security Management
Information security controls and management.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import json
import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    LOGGER = logging.getLogger(__name__)
    LOGGER.warning("cryptography library not available - encryption features disabled")

LOGGER = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access control levels."""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class SecurityEventType(Enum):
    """Security event types."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_VIOLATION = "security_violation"
    ENCRYPTION_ERROR = "encryption_error"
    DECRYPTION_ERROR = "decryption_error"


@dataclass
class SecurityEvent:
    """Security audit event."""
    event_id: str
    timestamp: float
    event_type: SecurityEventType
    user_id: Optional[str]
    resource: str
    action: str
    result: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessControlEntry:
    """Access control list entry."""
    resource: str
    access_level: AccessLevel
    permissions: Set[str] = field(default_factory=set)
    allowed_users: Set[str] = field(default_factory=set)
    denied_users: Set[str] = field(default_factory=set)


class SecurityManager:
    """Manages information security according to ISO/IEC 27001."""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library required for security features")
        
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            # Generate or load encryption key
            self.encryption_key = self._load_or_generate_key()
        
        self.cipher = Fernet(self.encryption_key)
        
        # Access control
        self.access_control: Dict[str, AccessControlEntry] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Audit logging
        self.audit_log: List[SecurityEvent] = []
        self.max_audit_entries = 10000
        
        # Security policies
        self.password_policy = {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digits": True,
            "require_special": True,
            "max_age_days": 90,
        }
        
        self.session_policy = {
            "timeout_minutes": 30,
            "max_sessions_per_user": 5,
            "require_https": True,
        }
        
        # Initialize default access controls
        self._initialize_access_controls()
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate encryption key."""
        import os
        from pathlib import Path
        
        key_file = Path("config/encryption.key")
        
        if key_file.exists():
            try:
                with open(key_file, "rb") as f:
                    return f.read()
            except Exception as e:
                LOGGER.warning("Failed to load encryption key: %s", e)
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, "wb") as f:
            f.write(key)
        
        # Set restrictive permissions (Unix only)
        try:
            os.chmod(key_file, 0o600)
        except Exception:
            pass
        
        LOGGER.info("Generated new encryption key")
        return key
    
    def _initialize_access_controls(self) -> None:
        """Initialize default access controls."""
        # ECU programming - admin only
        self.add_access_control("ecu.programming", AccessLevel.ADMIN, {
            "read", "write", "execute"
        })
        
        # Configuration - user or admin
        self.add_access_control("configuration", AccessLevel.USER, {
            "read", "write"
        })
        
        # Telemetry data - user or admin
        self.add_access_control("telemetry", AccessLevel.USER, {
            "read"
        })
        
        # System settings - admin only
        self.add_access_control("system", AccessLevel.ADMIN, {
            "read", "write", "execute"
        })
    
    def add_access_control(
        self,
        resource: str,
        min_level: AccessLevel,
        permissions: Set[str],
    ) -> None:
        """Add access control entry."""
        self.access_control[resource] = AccessControlEntry(
            resource=resource,
            access_level=min_level,
            permissions=permissions,
        )
    
    def check_access(
        self,
        user_id: str,
        user_level: AccessLevel,
        resource: str,
        permission: str,
    ) -> bool:
        """Check if user has access to resource."""
        entry = self.access_control.get(resource)
        if not entry:
            # Default deny
            self._log_security_event(
                SecurityEventType.ACCESS_DENIED,
                user_id=user_id,
                resource=resource,
                action=permission,
                result="DENIED - No access control entry",
            )
            return False
        
        # Check access level
        level_order = {
            AccessLevel.GUEST: 0,
            AccessLevel.USER: 1,
            AccessLevel.ADMIN: 2,
            AccessLevel.SYSTEM: 3,
        }
        
        if level_order[user_level] < level_order[entry.access_level]:
            self._log_security_event(
                SecurityEventType.ACCESS_DENIED,
                user_id=user_id,
                resource=resource,
                action=permission,
                result=f"DENIED - Insufficient access level (required: {entry.access_level.value})",
            )
            return False
        
        # Check permission
        if permission not in entry.permissions:
            self._log_security_event(
                SecurityEventType.ACCESS_DENIED,
                user_id=user_id,
                resource=resource,
                action=permission,
                result="DENIED - Permission not granted",
            )
            return False
        
        # Check user-specific deny list
        if user_id in entry.denied_users:
            self._log_security_event(
                SecurityEventType.ACCESS_DENIED,
                user_id=user_id,
                resource=resource,
                action=permission,
                result="DENIED - User in deny list",
            )
            return False
        
        # Check user-specific allow list (if exists)
        if entry.allowed_users and user_id not in entry.allowed_users:
            self._log_security_event(
                SecurityEventType.ACCESS_DENIED,
                user_id=user_id,
                resource=resource,
                action=permission,
                result="DENIED - User not in allow list",
            )
            return False
        
        # Access granted
        self._log_security_event(
            SecurityEventType.ACCESS_GRANTED,
            user_id=user_id,
            resource=resource,
            action=permission,
            result="GRANTED",
        )
        return True
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data."""
        try:
            return self.cipher.encrypt(data)
        except Exception as e:
            self._log_security_event(
                SecurityEventType.ENCRYPTION_ERROR,
                resource="encryption",
                action="encrypt",
                result=f"ERROR: {str(e)}",
            )
            raise
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data."""
        try:
            return self.cipher.decrypt(encrypted_data)
        except Exception as e:
            self._log_security_event(
                SecurityEventType.DECRYPTION_ERROR,
                resource="decryption",
                action="decrypt",
                result=f"ERROR: {str(e)}",
            )
            raise
    
    def encrypt_string(self, text: str) -> str:
        """Encrypt string and return base64-encoded result."""
        encrypted = self.encrypt_data(text.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt base64-encoded string."""
        encrypted_data = base64.b64decode(encrypted_text.encode('utf-8'))
        decrypted = self.decrypt_data(encrypted_data)
        return decrypted.decode('utf-8')
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Hash password using PBKDF2."""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    def verify_password(self, password: str, hashed: bytes, salt: bytes) -> bool:
        """Verify password against hash."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        try:
            kdf.verify(password.encode('utf-8'), hashed)
            return True
        except Exception:
            return False
    
    def validate_password(self, password: str) -> tuple[bool, List[str]]:
        """Validate password against policy."""
        errors = []
        
        if len(password) < self.password_policy["min_length"]:
            errors.append(f"Password must be at least {self.password_policy['min_length']} characters")
        
        if self.password_policy["require_uppercase"] and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        
        if self.password_policy["require_lowercase"] and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        
        if self.password_policy["require_digits"] and not any(c.isdigit() for c in password):
            errors.append("Password must contain digits")
        
        if self.password_policy["require_special"]:
            special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special for c in password):
                errors.append("Password must contain special characters")
        
        return len(errors) == 0, errors
    
    def create_session(
        self,
        user_id: str,
        user_level: AccessLevel,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Create user session."""
        session_id = secrets.token_urlsafe(32)
        
        self.user_sessions[session_id] = {
            "user_id": user_id,
            "user_level": user_level,
            "created_at": time.time(),
            "last_activity": time.time(),
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        
        self._log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            resource="session",
            action="create",
            result="SUCCESS",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and update last activity."""
        session = self.user_sessions.get(session_id)
        if not session:
            return None
        
        # Check timeout
        timeout_seconds = self.session_policy["timeout_minutes"] * 60
        if time.time() - session["last_activity"] > timeout_seconds:
            del self.user_sessions[session_id]
            return None
        
        session["last_activity"] = time.time()
        return session
    
    def _log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        resource: str = "",
        action: str = "",
        result: str = "",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log security event for audit."""
        event = SecurityEvent(
            event_id=f"SEC-{int(time.time() * 1000000)}",
            timestamp=time.time(),
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        
        self.audit_log.append(event)
        
        # Keep only recent entries
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries:]
        
        # Log to logger
        log_level = logging.INFO
        if event_type in (SecurityEventType.SECURITY_VIOLATION, SecurityEventType.ACCESS_DENIED):
            log_level = logging.WARNING
        elif event_type == SecurityEventType.LOGIN_FAILURE:
            log_level = logging.WARNING
        
        LOGGER.log(
            log_level,
            "Security event: %s - %s - %s - %s",
            event_type.value, resource, action, result
        )
    
    def get_audit_log(
        self,
        event_type: Optional[SecurityEventType] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """Get audit log entries."""
        filtered = self.audit_log
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        
        return filtered[-limit:]
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security status report."""
        return {
            "encryption_enabled": CRYPTO_AVAILABLE,
            "active_sessions": len(self.user_sessions),
            "access_controls": len(self.access_control),
            "audit_entries": len(self.audit_log),
            "recent_violations": len([
                e for e in self.audit_log[-100:]
                if e.event_type == SecurityEventType.SECURITY_VIOLATION
            ]),
        }


# Global instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


__all__ = [
    "SecurityManager",
    "AccessLevel",
    "SecurityEventType",
    "SecurityEvent",
    "get_security_manager",
]
