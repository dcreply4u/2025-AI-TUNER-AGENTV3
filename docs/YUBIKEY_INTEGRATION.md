# YubiKey Integration Guide

## Overview

YubiKey provides hardware-based security for the AI Tuner Agent, making it nearly impossible to steal or copy the codebase without the physical YubiKey device.

## Features

### 1. Hardware License Validation
- Application requires physical YubiKey to start
- License stored on YubiKey (cannot be copied)
- Serial number verification

### 2. Secure Boot Verification
- YubiKey stores boot verification key
- Ensures system hasn't been tampered with
- Hardware-based integrity check

### 3. Encryption Key Storage
- Critical encryption keys stored on YubiKey
- Keys cannot be extracted without physical access
- PIN-protected access

### 4. Admin Function Protection
- Sensitive operations require YubiKey touch
- Physical confirmation for admin functions
- Two-factor authentication

### 5. Code Integrity
- YubiKey verifies code hasn't been modified
- Prevents unauthorized changes
- Hardware-based verification

## Setup

### 1. Install YubiKey Library

```bash
pip install yubikit
```

### 2. Configure YubiKey

Run the setup tool:

```bash
python tools/setup_yubikey.py
```

Options:
1. **Setup License** - Store license on YubiKey
2. **Setup Encryption Key** - Store encryption keys
3. **Verify Setup** - Verify configuration

### 3. Enable YubiKey Requirement

Set environment variables:

```bash
export AI_TUNER_REQUIRE_YUBIKEY=true
export AI_TUNER_YUBIKEY_SERIAL=12345678  # Optional: specific serial
```

Or in code:

```python
from core.code_protection import CodeProtection

protection = CodeProtection(
    require_yubikey=True,
    yubikey_serial="12345678",  # Optional
)
```

## Usage

### Application Startup

With YubiKey required, application will:
1. Detect YubiKey on startup
2. Verify license stored on YubiKey
3. Verify secure boot
4. Only start if all checks pass

### Admin Functions

Require YubiKey for sensitive operations:

```python
from core.yubikey_auth import YubiKeyAuth

auth = YubiKeyAuth(require_yubikey=True)

# Require YubiKey touch for admin operation
if auth.require_admin_yubikey("ECU_TUNING"):
    # Perform admin operation
    pass
```

### Encryption Key Management

Store and retrieve encryption keys:

```python
# Store key
auth.store_encryption_key(key_data, pin="123456")

# Retrieve key
key = auth.retrieve_encryption_key(pin="123456")
```

## Security Benefits

### Without YubiKey
- Code can be copied
- License can be bypassed
- Keys can be extracted
- Code can be modified

### With YubiKey
- ✅ Code protected (requires physical device)
- ✅ License hardware-bound
- ✅ Keys stored securely
- ✅ Code integrity verified
- ✅ Admin functions protected

## Deployment

### Production Setup

1. **Configure YubiKey per device**
   - Each device gets unique YubiKey
   - License stored on YubiKey
   - Encryption keys stored on YubiKey

2. **Enable YubiKey requirement**
   ```bash
   export AI_TUNER_REQUIRE_YUBIKEY=true
   ```

3. **Deploy protected build**
   - Use `tools/build_protected.py` to create executable
   - Combine with read-only filesystem
   - YubiKey provides additional layer

4. **Test setup**
   - Verify YubiKey detection
   - Test license verification
   - Verify admin functions

## Troubleshooting

### YubiKey Not Detected

1. Check YubiKey is inserted
2. Check USB connection
3. Verify yubikit library installed
4. Check permissions (may need udev rules on Linux)

### License Verification Failed

1. Verify license stored on YubiKey
2. Check YubiKey serial matches
3. Verify PIN is correct
4. Re-run setup tool

### Secure Boot Failed

1. Verify secure boot key stored
2. Check system hasn't been modified
3. Re-verify with setup tool

## Best Practices

1. **Use unique YubiKey per device**
   - Prevents key sharing
   - Enables device tracking

2. **Store backup keys securely**
   - YubiKey can be lost/damaged
   - Keep encrypted backups

3. **Rotate keys periodically**
   - Update encryption keys
   - Refresh licenses

4. **Monitor YubiKey usage**
   - Log all YubiKey operations
   - Alert on suspicious activity

## Integration with Code Protection

YubiKey integrates with the code protection system:

```python
from core.code_protection import CodeProtection

protection = CodeProtection(
    require_yubikey=True,
    yubikey_serial="12345678",
)

# Enforces:
# - YubiKey detection
# - License verification
# - Secure boot
# - Code integrity
# - Runtime protection
```

## Support

For YubiKey issues:
- Check YubiKey documentation
- Verify yubikit installation
- Test with setup tool
- Check system logs

---

**This is a CRITICAL security feature for production deployment!**

