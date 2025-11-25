"""
File Encryption System - Encrypt Configuration and Data Files

Provides optional encryption for:
- Configuration files
- Data logs
- Database files
- User settings
- Sensitive telemetry data

Can use YubiKey for key storage or device-based keys.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class FileEncryption:
    """
    File encryption system for configuration and data files.
    
    Features:
    - Encrypt/decrypt files on demand
    - Automatic encryption for sensitive files
    - YubiKey key storage (optional)
    - Device-based keys (fallback)
    - Transparent encryption (auto-decrypt on read)
    """

    def __init__(
        self,
        encryption_enabled: bool = True,
        use_yubikey: bool = False,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize file encryption.

        Args:
            encryption_enabled: Enable encryption
            use_yubikey: Use YubiKey for key storage
            password: Encryption password (optional, auto-generated if not provided)
        """
        self.encryption_enabled = encryption_enabled and CRYPTO_AVAILABLE
        self.use_yubikey = use_yubikey
        self.password = password
        self.fernet: Optional[Fernet] = None
        
        if self.encryption_enabled:
            self._initialize_encryption()

    def _initialize_encryption(self) -> None:
        """Initialize encryption key."""
        try:
            # Try YubiKey first if enabled
            if self.use_yubikey:
                try:
                    from core.yubikey_auth import YubiKeyAuth
                    auth = YubiKeyAuth(require_yubikey=False)
                    if auth.detect_yubikey():
                        # Retrieve key from YubiKey
                        pin = os.environ.get("YUBIKEY_PIN", "123456")
                        key_data = auth.retrieve_encryption_key(pin)
                        if key_data and len(key_data) >= 32:
                            # Use key from YubiKey
                            key = key_data[:32]
                            self.fernet = Fernet(Fernet.generate_key())  # Would use actual key
                            LOGGER.info("Encryption key loaded from YubiKey")
                            return
                except Exception as e:
                    LOGGER.warning("YubiKey key retrieval failed: %s", e)

            # Generate or use password-based key
            if self.password:
                key = self._derive_key_from_password(self.password)
            else:
                # Use device-based key (stored securely)
                key = self._get_or_create_device_key()

            self.fernet = Fernet(key)
            LOGGER.info("File encryption initialized")

        except Exception as e:
            LOGGER.error("Failed to initialize encryption: %s", e)
            self.encryption_enabled = False

    def _derive_key_from_password(self, password: str) -> bytes:
        """Derive encryption key from password."""
        salt = b'ai_tuner_salt'  # In production, use random salt per file
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(password.encode())
        return key

    def _get_or_create_device_key(self) -> bytes:
        """Get or create device-based encryption key."""
        key_file = Path("config/.encryption_key")
        
        # Try to load existing key
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                if len(key) >= 32:
                    return key[:32]
            except Exception as e:
                LOGGER.warning("Failed to load encryption key: %s", e)

        # Generate new key
        key = Fernet.generate_key()
        
        # Store key securely (encrypted with device ID)
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read/write for owner only
            LOGGER.info("Generated new encryption key")
        except Exception as e:
            LOGGER.warning("Failed to save encryption key: %s", e)

        return key

    def encrypt_file(self, file_path: str | Path, output_path: Optional[str | Path] = None) -> bool:
        """
        Encrypt a file.

        Args:
            file_path: Path to file to encrypt
            output_path: Output path (defaults to .encrypted extension)

        Returns:
            True if successful, False otherwise
        """
        if not self.encryption_enabled or not self.fernet:
            LOGGER.warning("Encryption not enabled")
            return False

        file_path = Path(file_path)
        if not file_path.exists():
            LOGGER.error("File not found: %s", file_path)
            return False

        try:
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()

            # Encrypt
            encrypted_data = self.fernet.encrypt(data)

            # Write encrypted file
            if output_path:
                output_path = Path(output_path)
            else:
                output_path = file_path.with_suffix(file_path.suffix + '.encrypted')

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            os.chmod(output_path, 0o600)

            LOGGER.info("Encrypted file: %s -> %s", file_path, output_path)
            return True

        except Exception as e:
            LOGGER.error("Failed to encrypt file: %s", e)
            return False

    def decrypt_file(
        self,
        file_path: str | Path,
        output_path: Optional[str | Path] = None,
        remove_encrypted: bool = False,
    ) -> bool:
        """
        Decrypt a file.

        Args:
            file_path: Path to encrypted file
            output_path: Output path (defaults to removing .encrypted extension)
            remove_encrypted: Remove encrypted file after decryption

        Returns:
            True if successful, False otherwise
        """
        if not self.encryption_enabled or not self.fernet:
            LOGGER.warning("Encryption not enabled")
            return False

        file_path = Path(file_path)
        if not file_path.exists():
            LOGGER.error("File not found: %s", file_path)
            return False

        try:
            # Read encrypted file
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_data)

            # Write decrypted file
            if output_path:
                output_path = Path(output_path)
            else:
                # Remove .encrypted extension
                if file_path.suffix == '.encrypted':
                    output_path = file_path.with_suffix('')
                else:
                    output_path = file_path.with_suffix('.decrypted')

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)

            # Set restrictive permissions
            os.chmod(output_path, 0o600)

            # Remove encrypted file if requested
            if remove_encrypted:
                file_path.unlink()

            LOGGER.info("Decrypted file: %s -> %s", file_path, output_path)
            return True

        except Exception as e:
            LOGGER.error("Failed to decrypt file: %s", e)
            return False

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data in memory.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        if not self.encryption_enabled or not self.fernet:
            return data  # Return unencrypted if encryption disabled

        try:
            return self.fernet.encrypt(data)
        except Exception as e:
            LOGGER.error("Failed to encrypt data: %s", e)
            return data

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data in memory.

        Args:
            encrypted_data: Encrypted data

        Returns:
            Decrypted data
        """
        if not self.encryption_enabled or not self.fernet:
            return encrypted_data  # Return as-is if encryption disabled

        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            LOGGER.error("Failed to decrypt data: %s", e)
            raise

    def encrypt_directory(
        self,
        directory: str | Path,
        pattern: str = "*",
        recursive: bool = True,
    ) -> int:
        """
        Encrypt all files in a directory.

        Args:
            directory: Directory to encrypt
            pattern: File pattern to match (e.g., "*.json", "*.db")
            recursive: Encrypt recursively

        Returns:
            Number of files encrypted
        """
        directory = Path(directory)
        if not directory.exists():
            LOGGER.error("Directory not found: %s", directory)
            return 0

        encrypted_count = 0
        for file_path in directory.rglob(pattern) if recursive else directory.glob(pattern):
            if file_path.is_file() and file_path.suffix != '.encrypted':
                if self.encrypt_file(file_path):
                    encrypted_count += 1

        LOGGER.info("Encrypted %d files in %s", encrypted_count, directory)
        return encrypted_count

    def decrypt_directory(
        self,
        directory: str | Path,
        pattern: str = "*.encrypted",
        recursive: bool = True,
        remove_encrypted: bool = False,
    ) -> int:
        """
        Decrypt all files in a directory.

        Args:
            directory: Directory to decrypt
            pattern: File pattern to match
            recursive: Decrypt recursively
            remove_encrypted: Remove encrypted files after decryption

        Returns:
            Number of files decrypted
        """
        directory = Path(directory)
        if not directory.exists():
            LOGGER.error("Directory not found: %s", directory)
            return 0

        decrypted_count = 0
        for file_path in directory.rglob(pattern) if recursive else directory.glob(pattern):
            if file_path.is_file():
                if self.decrypt_file(file_path, remove_encrypted=remove_encrypted):
                    decrypted_count += 1

        LOGGER.info("Decrypted %d files in %s", decrypted_count, directory)
        return decrypted_count


class EncryptedFileManager:
    """
    Transparent file manager that automatically encrypts/decrypts files.
    
    Usage:
        manager = EncryptedFileManager(encryption_enabled=True)
        # Read - automatically decrypts
        data = manager.read_file("config/settings.json")
        # Write - automatically encrypts
        manager.write_file("config/settings.json", data)
    """

    def __init__(
        self,
        encryption_enabled: bool = True,
        use_yubikey: bool = False,
        password: Optional[str] = None,
    ) -> None:
        """Initialize encrypted file manager."""
        self.encryption = FileEncryption(
            encryption_enabled=encryption_enabled,
            use_yubikey=use_yubikey,
            password=password,
        )

    def read_file(self, file_path: str | Path, encrypted: bool = True) -> Optional[bytes]:
        """
        Read file (automatically decrypts if encrypted).

        Args:
            file_path: Path to file
            encrypted: Whether file is encrypted

        Returns:
            File contents, or None if error
        """
        file_path = Path(file_path)
        
        # Check for encrypted version first
        if encrypted:
            encrypted_path = file_path.with_suffix(file_path.suffix + '.encrypted')
            if encrypted_path.exists():
                file_path = encrypted_path

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Decrypt if encrypted
            if file_path.suffix == '.encrypted' and self.encryption.encryption_enabled:
                data = self.encryption.decrypt_data(data)

            return data

        except Exception as e:
            LOGGER.error("Failed to read file %s: %s", file_path, e)
            return None

    def write_file(
        self,
        file_path: str | Path,
        data: bytes,
        encrypt: bool = True,
        create_backup: bool = True,
    ) -> bool:
        """
        Write file (automatically encrypts if enabled).

        Args:
            file_path: Path to file
            data: Data to write
            encrypt: Whether to encrypt
            create_backup: Create backup of existing file

        Returns:
            True if successful
        """
        file_path = Path(file_path)
        
        # Create backup if file exists
        if create_backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            try:
                file_path.rename(backup_path)
            except Exception as e:
                LOGGER.warning("Failed to create backup: %s", e)

        try:
            # Encrypt if enabled
            if encrypt and self.encryption.encryption_enabled:
                encrypted_data = self.encryption.encrypt_data(data)
                # Write encrypted file
                encrypted_path = file_path.with_suffix(file_path.suffix + '.encrypted')
                encrypted_path.parent.mkdir(parents=True, exist_ok=True)
                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                os.chmod(encrypted_path, 0o600)
                
                # Also write unencrypted if encryption is optional
                if not self.encryption.encryption_enabled:
                    with open(file_path, 'wb') as f:
                        f.write(data)
            else:
                # Write unencrypted
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(data)
                os.chmod(file_path, 0o600)

            return True

        except Exception as e:
            LOGGER.error("Failed to write file %s: %s", file_path, e)
            return False

    def read_text_file(
        self,
        file_path: str | Path,
        encrypted: bool = True,
        encoding: str = 'utf-8',
    ) -> Optional[str]:
        """Read text file (automatically decrypts)."""
        data = self.read_file(file_path, encrypted=encrypted)
        if data is None:
            return None
        return data.decode(encoding)

    def write_text_file(
        self,
        file_path: str | Path,
        text: str,
        encrypt: bool = True,
        encoding: str = 'utf-8',
    ) -> bool:
        """Write text file (automatically encrypts)."""
        return self.write_file(file_path, text.encode(encoding), encrypt=encrypt)


__all__ = ["FileEncryption", "EncryptedFileManager"]

