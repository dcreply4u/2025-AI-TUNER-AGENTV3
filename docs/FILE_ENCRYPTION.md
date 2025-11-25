# File Encryption Guide

## Overview

The AI Tuner Agent includes comprehensive file encryption capabilities to protect:
- Configuration files
- Data logs
- Database files
- User settings
- Sensitive telemetry data

## Features

### 1. Transparent Encryption
- Files automatically encrypted/decrypted on read/write
- No code changes needed - works transparently
- Supports both encrypted and plain files

### 2. Multiple Encryption Methods
- **YubiKey**: Hardware-based key storage (most secure)
- **Password**: User-provided password
- **Device Key**: Automatic device-based key (no password needed)

### 3. Selective Encryption
- Choose which directories to encrypt
- Encrypt existing files on demand
- Decrypt files when needed

## Usage

### Enable Encryption via UI

1. Click **"Encryption"** button in main window
2. Check **"Enable file encryption"**
3. Choose encryption method:
   - **YubiKey**: Requires YubiKey hardware
   - **Password**: Enter encryption password
   - **Device Key**: Automatic (recommended)
4. Select directories to encrypt:
   - Configuration files
   - Data logs
   - Database files
5. Click **"OK"** to save

### Encrypt Existing Files

1. Open Encryption Settings
2. Click **"Encrypt Existing Files..."**
3. Select directory
4. Enter file pattern (e.g., `*.json`, `*.db`, `*`)
5. Files will be encrypted with `.encrypted` extension

### Decrypt Files

1. Open Encryption Settings
2. Click **"Decrypt Existing Files..."**
3. Select directory with encrypted files
4. Files will be decrypted (`.encrypted` extension removed)

## Programmatic Usage

### Basic Encryption

```python
from core.file_encryption import FileEncryption

# Initialize encryption
encryption = FileEncryption(
    encryption_enabled=True,
    use_yubikey=False,  # Set to True for YubiKey
    password="your-password",  # Optional
)

# Encrypt a file
encryption.encrypt_file("config/settings.json")

# Decrypt a file
encryption.decrypt_file("config/settings.json.encrypted")
```

### Transparent File Manager

```python
from core.file_encryption import EncryptedFileManager

# Initialize manager
manager = EncryptedFileManager(
    encryption_enabled=True,
    use_yubikey=False,
)

# Read file (automatically decrypts)
data = manager.read_text_file("config/settings.json")

# Write file (automatically encrypts)
manager.write_text_file("config/settings.json", json_data)
```

### With Config Manager

```python
from core.config_manager import ConfigManager
from core.file_encryption import EncryptedFileManager

# Create encryption manager
encryption_manager = EncryptedFileManager(encryption_enabled=True)

# Use with config manager
config = ConfigManager(encryption_manager=encryption_manager)

# Config files are automatically encrypted/decrypted
config.save_profile("my_car", profile)
```

## Encryption Methods

### 1. YubiKey (Most Secure)

**Pros:**
- Hardware-based security
- Keys cannot be extracted
- Physical device required

**Cons:**
- Requires YubiKey hardware
- Setup required

**Setup:**
```bash
python tools/setup_yubikey.py
```

### 2. Password-Based

**Pros:**
- No hardware required
- User controls password

**Cons:**
- Password must be remembered
- Less secure if password weak

**Usage:**
```python
encryption = FileEncryption(
    encryption_enabled=True,
    password="strong-password-here",
)
```

### 3. Device Key (Automatic)

**Pros:**
- No password needed
- Automatic setup
- Device-specific

**Cons:**
- Key stored on device
- Less secure if device compromised

**Usage:**
```python
encryption = FileEncryption(encryption_enabled=True)
# Key automatically generated and stored
```

## Security Considerations

### Best Practices

1. **Use YubiKey for production**
   - Most secure option
   - Keys stored on hardware

2. **Strong passwords**
   - Minimum 16 characters
   - Mix of letters, numbers, symbols

3. **Backup encryption keys**
   - Store keys securely
   - Can't recover files without keys

4. **Regular key rotation**
   - Change keys periodically
   - Re-encrypt files with new keys

### What Gets Encrypted

- **Configuration files**: `config/*.json`
- **Data logs**: `logs/*.csv`, `logs/*.log`
- **Database files**: `*.db`, `*.sqlite`
- **User settings**: `config/user_settings.json`

### What Doesn't Get Encrypted

- **Application code**: Not encrypted (use code protection)
- **Temporary files**: Not encrypted
- **Video files**: Optional (large files, slower)

## Troubleshooting

### "Encryption not enabled"

**Solution:**
- Check `cryptography` library installed: `pip install cryptography`
- Verify encryption is enabled in settings

### "Failed to decrypt file"

**Possible causes:**
- Wrong password
- YubiKey not present
- Corrupted encrypted file
- Wrong encryption key

**Solution:**
- Verify password/YubiKey
- Check file integrity
- Restore from backup

### "Permission denied"

**Solution:**
- Check file permissions
- Run with appropriate user
- Check encryption key file permissions

## Integration with Code Protection

File encryption works with code protection:

```python
from core.code_protection import CodeProtection
from core.file_encryption import EncryptedFileManager

# Code protection
protection = CodeProtection(require_yubikey=True)

# File encryption (uses YubiKey if available)
encryption = EncryptedFileManager(
    encryption_enabled=True,
    use_yubikey=True,
)
```

## Environment Variables

```bash
# Enable encryption
export AI_TUNER_ENCRYPTION_ENABLED=true

# Use YubiKey
export AI_TUNER_USE_YUBIKEY=true

# Encryption password (if not using YubiKey)
export AI_TUNER_ENCRYPTION_PASSWORD=your-password

# YubiKey PIN
export YUBIKEY_PIN=123456
```

## Performance

- **Encryption overhead**: ~5-10% for small files
- **Large files**: May be slower (consider selective encryption)
- **Memory usage**: Minimal (streaming encryption)

## Backup and Recovery

### Backup Encryption Keys

```python
# Save key to secure location
key = encryption._get_or_create_device_key()
# Store securely (encrypted backup, secure storage, etc.)
```

### Recover Encrypted Files

1. Restore encryption key
2. Initialize encryption with key
3. Decrypt files

**WARNING**: Without the encryption key, encrypted files cannot be recovered!

---

**File encryption is CRITICAL for protecting sensitive data on hardware devices!**

