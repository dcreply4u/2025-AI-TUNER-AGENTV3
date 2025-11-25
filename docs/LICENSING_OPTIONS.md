# Licensing System Options & Implementation Guide

## Overview

This document outlines options for implementing a licensing system that restricts software usage to demo mode unless a valid license key is provided.

## Current State

### Existing Infrastructure ✅

The codebase already has some licensing infrastructure:

1. **`core/code_protection.py`** - Basic license verification
   - License key validation
   - Device ID binding
   - YubiKey hardware support
   - Code integrity checks

2. **`core/yubikey_auth.py`** - Hardware-based licensing
   - Physical YubiKey requirement
   - License stored on hardware
   - Serial number verification

3. **Demo Mode** - Currently exists for simulation only
   - `demo.py` - Simulated data mode
   - `AITUNER_DEMO_MODE` environment variable
   - Not used for feature restrictions

## Implementation Options

### Option 1: Simple License Key System (Recommended for MVP)

**Pros:**
- Quick to implement
- No external dependencies
- Works offline
- Easy to understand

**Cons:**
- Less secure (can be reverse-engineered)
- No server-side validation
- Manual license management

**Implementation:**
- License key stored in config file or environment variable
- Cryptographic validation using device ID
- Feature flags based on license status

**Best For:** Initial release, small user base, offline operation

---

### Option 2: Server-Based License Validation

**Pros:**
- More secure
- Centralized license management
- Can revoke licenses remotely
- Usage tracking and analytics
- Supports subscription models

**Cons:**
- Requires internet connection
- Need to maintain license server
- More complex implementation
- Potential downtime issues

**Implementation:**
- License server API (FastAPI/Flask)
- Periodic online validation
- Offline grace period
- License database

**Best For:** Production deployment, subscription models, enterprise customers

---

### Option 3: Hybrid System (Recommended for Production)

**Pros:**
- Works offline with periodic online checks
- More secure than simple system
- Flexible license management
- Supports both one-time and subscription

**Cons:**
- More complex to implement
- Requires license server
- Need to handle offline scenarios

**Implementation:**
- Local license cache with cryptographic validation
- Periodic server validation (daily/weekly)
- Offline grace period (30 days)
- Automatic license refresh

**Best For:** Production deployment, best balance of security and usability

---

### Option 4: Hardware-Based (YubiKey)

**Pros:**
- Maximum security
- Cannot be copied
- Physical device required
- Enterprise-grade protection

**Cons:**
- Requires hardware purchase
- User must have YubiKey
- More expensive for users
- Less convenient

**Implementation:**
- Already implemented in `core/yubikey_auth.py`
- License stored on YubiKey
- Serial number verification

**Best For:** Enterprise customers, high-value software, maximum security requirements

---

### Option 5: Third-Party Licensing Services

**Pros:**
- Professional implementation
- Managed service
- Payment integration
- Analytics and reporting
- Support included

**Cons:**
- Monthly fees
- Less control
- Vendor lock-in
- Additional dependency

**Popular Services:**
- **LicenseSpring** - Cloud-based licensing
- **Cryptolens** - License key management
- **Gumroad** - Simple licensing + payments
- **Paddle** - Full payment + licensing solution

**Best For:** Quick launch, focus on product not infrastructure

---

## Recommended Implementation: Hybrid System

### Architecture

```
┌─────────────────┐
│  Application    │
│                 │
│  ┌───────────┐  │
│  │ License   │  │
│  │ Manager   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Local     │  │
│  │ Cache     │  │
│  └─────┬─────┘  │
│        │        │
└────────┼────────┘
         │
    ┌────▼────┐
    │ License │
    │ Server  │
    └─────────┘
```

### Features

1. **License Key Format**
   ```
   AI-TUNER-XXXX-XXXX-XXXX-XXXX
   ```
   - 4 groups of 4 characters
   - Base32 encoded
   - Contains: product code, version, features, checksum

2. **Device Binding**
   - License tied to device ID (MAC address)
   - Prevents license sharing
   - Optional: Allow N activations

3. **Feature Flags**
   - Demo mode: Limited features
   - Basic license: Core features
   - Pro license: All features
   - Enterprise: Custom features

4. **Validation Flow**
   ```
   App Start → Check Local Cache → Valid? → Yes → Full Access
                                      ↓ No
                              Check Server → Valid? → Yes → Update Cache → Full Access
                                                      ↓ No
                                              Demo Mode
   ```

5. **Offline Support**
   - Cache valid license for 30 days
   - Grace period for expired licenses
   - Automatic refresh when online

---

## Demo Mode Restrictions

### What Should Be Restricted in Demo Mode?

#### ✅ Allowed (Demo Mode):
- View all UI components
- View telemetry displays
- View settings (read-only)
- Export data (limited: max 10 exports)
- Basic AI advisor (rule-based only)
- View-only access to all tabs

#### ❌ Restricted (Demo Mode):
- **ECU Tuning**: View-only, no writes
- **Data Logging**: Limited to 5 minutes per session
- **Advanced AI**: ML models disabled
- **Cloud Sync**: Disabled
- **Video Recording**: Disabled or watermarked
- **Export**: Limited exports, watermarked
- **Racing Controls**: View-only
- **Auto Tuning**: Disabled
- **Advanced Features**: Disabled

### Implementation Strategy

1. **Feature Flags System**
   ```python
   class LicenseManager:
       def is_feature_enabled(self, feature: str) -> bool:
           if self.is_demo_mode():
               return feature in DEMO_ALLOWED_FEATURES
           return True
   ```

2. **UI Restrictions**
   - Disable buttons/controls in demo mode
   - Show "Demo Mode" badges
   - Display upgrade prompts
   - Limit data collection

3. **Functional Restrictions**
   - Time limits
   - Data limits
   - Feature limits
   - Export limits

---

## Implementation Steps

### Phase 1: License Manager (Core)

1. Create `core/license_manager.py`
   - License key validation
   - Device binding
   - Feature flags
   - Demo mode detection

2. Create `core/demo_restrictions.py`
   - Feature restrictions
   - Time limits
   - Data limits

3. Update application startup
   - Check license on startup
   - Set demo mode if no license
   - Initialize restrictions

### Phase 2: UI Integration

1. License entry dialog
   - Enter license key
   - Validate and activate
   - Show license status

2. Demo mode indicators
   - Status bar badge
   - Feature disabled styling
   - Upgrade prompts

3. Feature gating
   - Disable restricted features
   - Show upgrade messages
   - Track usage limits

### Phase 3: Server Integration (Optional)

1. License server API
   - Validation endpoint
   - Activation endpoint
   - Revocation endpoint

2. Client integration
   - Periodic validation
   - Offline cache
   - Error handling

### Phase 4: Advanced Features

1. Subscription support
   - Expiration dates
   - Auto-renewal
   - Grace periods

2. Analytics
   - Usage tracking
   - Feature usage stats
   - License analytics

---

## Code Examples

### Basic License Manager

```python
# core/license_manager.py
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional
from enum import Enum

class LicenseType(Enum):
    DEMO = "demo"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class LicenseManager:
    def __init__(self):
        self.license_file = Path("config/license.json")
        self.device_id = self._get_device_id()
        self.license_data: Optional[Dict] = None
        self.load_license()
    
    def _get_device_id(self) -> str:
        """Get unique device identifier."""
        import uuid
        return ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff)
                        for i in range(0, 8*6, 8)][::-1])
    
    def load_license(self) -> None:
        """Load license from file."""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r') as f:
                    self.license_data = json.load(f)
            except Exception:
                self.license_data = None
    
    def validate_license_key(self, license_key: str) -> bool:
        """Validate license key format and checksum."""
        # Format: AI-TUNER-XXXX-XXXX-XXXX-XXXX
        parts = license_key.split('-')
        if len(parts) != 5 or parts[0] != 'AI' or parts[1] != 'TUNER':
            return False
        
        # Validate checksum
        key_data = ''.join(parts[2:])
        checksum = self._calculate_checksum(key_data)
        return checksum == parts[-1][-1]  # Last char is checksum
    
    def activate_license(self, license_key: str) -> bool:
        """Activate license key."""
        if not self.validate_license_key(license_key):
            return False
        
        # Decode license information
        license_type = self._decode_license_type(license_key)
        
        # Save license
        self.license_data = {
            'key': license_key,
            'type': license_type.value,
            'device_id': self.device_id,
            'activated': True,
            'expires': None,  # Or decode expiration date
        }
        
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.license_file, 'w') as f:
            json.dump(self.license_data, f)
        
        return True
    
    def is_licensed(self) -> bool:
        """Check if valid license is active."""
        if not self.license_data:
            return False
        
        # Check device binding
        if self.license_data.get('device_id') != self.device_id:
            return False
        
        # Check expiration
        expires = self.license_data.get('expires')
        if expires:
            from datetime import datetime
            if datetime.fromisoformat(expires) < datetime.now():
                return False
        
        return True
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return not self.is_licensed()
    
    def get_license_type(self) -> LicenseType:
        """Get current license type."""
        if self.is_demo_mode():
            return LicenseType.DEMO
        
        license_type_str = self.license_data.get('type', 'demo')
        return LicenseType(license_type_str)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled for current license."""
        license_type = self.get_license_type()
        
        # Feature matrix
        features = {
            'ecu_tuning_write': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'advanced_ai': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'cloud_sync': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'video_recording': [LicenseType.BASIC, LicenseType.PRO, LicenseType.ENTERPRISE],
            'auto_tuning': [LicenseType.PRO, LicenseType.ENTERPRISE],
            'racing_controls': [LicenseType.PRO, LicenseType.ENTERPRISE],
        }
        
        allowed_types = features.get(feature, [])
        return license_type in allowed_types
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate checksum for license validation."""
        hash_obj = hashlib.md5(data.encode())
        return hash_obj.hexdigest()[-1].upper()
    
    def _decode_license_type(self, license_key: str) -> LicenseType:
        """Decode license type from key."""
        # Extract type from key (simplified)
        parts = license_key.split('-')
        type_code = parts[2][0]  # First char of third segment
        
        type_map = {
            'B': LicenseType.BASIC,
            'P': LicenseType.PRO,
            'E': LicenseType.ENTERPRISE,
        }
        return type_map.get(type_code, LicenseType.DEMO)
```

### Demo Restrictions Manager

```python
# core/demo_restrictions.py
from dataclasses import dataclass
from typing import Dict, Optional
import time

@dataclass
class UsageLimits:
    max_session_time: int = 300  # 5 minutes
    max_exports: int = 10
    max_data_points: int = 10000
    max_logging_time: int = 300  # 5 minutes

class DemoRestrictions:
    def __init__(self):
        self.limits = UsageLimits()
        self.session_start = time.time()
        self.export_count = 0
        self.data_point_count = 0
        self.logging_start: Optional[float] = None
    
    def can_use_feature(self, feature: str) -> tuple[bool, str]:
        """Check if feature can be used, return (allowed, reason)."""
        if feature == 'export':
            if self.export_count >= self.limits.max_exports:
                return False, f"Demo mode: Maximum {self.limits.max_exports} exports reached"
            return True, ""
        
        if feature == 'logging':
            if self.logging_start:
                elapsed = time.time() - self.logging_start
                if elapsed >= self.limits.max_logging_time:
                    return False, f"Demo mode: Maximum {self.limits.max_logging_time}s logging time reached"
            return True, ""
        
        if feature == 'data_collection':
            if self.data_point_count >= self.limits.max_data_points:
                return False, f"Demo mode: Maximum {self.limits.max_data_points} data points reached"
            return True, ""
        
        return True, ""
    
    def record_export(self) -> None:
        """Record an export operation."""
        self.export_count += 1
    
    def record_data_point(self) -> None:
        """Record a data point collection."""
        self.data_point_count += 1
    
    def start_logging(self) -> None:
        """Start logging session."""
        self.logging_start = time.time()
    
    def stop_logging(self) -> None:
        """Stop logging session."""
        self.logging_start = None
    
    def get_session_time_remaining(self) -> int:
        """Get remaining session time in seconds."""
        elapsed = time.time() - self.session_start
        remaining = self.limits.max_session_time - int(elapsed)
        return max(0, remaining)
```

### Integration Example

```python
# In main application startup
from core.license_manager import LicenseManager
from core.demo_restrictions import DemoRestrictions

license_manager = LicenseManager()
demo_restrictions = DemoRestrictions()

# Check license status
if license_manager.is_demo_mode():
    print("Running in DEMO MODE - Limited features available")
    print("Enter license key in Settings to unlock full features")
else:
    print(f"License active: {license_manager.get_license_type().value}")

# Feature gating example
def save_ecu_tuning():
    if not license_manager.is_feature_enabled('ecu_tuning_write'):
        show_message("ECU tuning write disabled in demo mode. Upgrade to unlock.")
        return
    
    # Proceed with save
    ...
```

---

## Security Considerations

### 1. License Key Security
- Use cryptographic signatures (RSA/ECDSA)
- Encode expiration dates
- Include device binding
- Prevent key sharing

### 2. Code Protection
- Obfuscate license validation code
- Use PyInstaller/Nuitka for compilation
- Anti-debugging measures
- Integrity checks

### 3. Server Validation
- HTTPS only
- Rate limiting
- Request signing
- IP whitelisting (optional)

### 4. Offline Security
- Encrypted license cache
- Time-limited offline access
- Periodic online validation
- Revocation support

---

## Recommended Approach

### For MVP/Initial Release:
**Option 1: Simple License Key System**
- Quick to implement
- Works immediately
- Can upgrade later

### For Production:
**Option 3: Hybrid System**
- Best balance of security and usability
- Supports offline operation
- Scalable to subscription model

### For Enterprise:
**Option 4: Hardware-Based (YubiKey)**
- Maximum security
- Already implemented
- Enterprise-grade

---

## Next Steps

1. **Choose implementation option** based on requirements
2. **Create license manager** with chosen approach
3. **Implement demo restrictions** for feature gating
4. **Add license UI** (entry dialog, status display)
5. **Integrate throughout app** (feature checks)
6. **Test thoroughly** (demo mode, licensed mode)
7. **Set up license server** (if using server-based option)

---

## License Key Generation

### Simple Format
```
AI-TUNER-XXXX-XXXX-XXXX-XXXX
```

### Generation Algorithm
```python
import secrets
import hashlib

def generate_license_key(license_type: str, device_id: str) -> str:
    # Generate random segments
    segments = []
    for _ in range(3):
        segment = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') 
                         for _ in range(4))
        segments.append(segment)
    
    # Add type prefix
    type_code = {'basic': 'B', 'pro': 'P', 'enterprise': 'E'}[license_type]
    segments[0] = type_code + segments[0][1:]
    
    # Calculate checksum
    key_data = ''.join(segments)
    checksum = hashlib.md5(key_data.encode()).hexdigest()[-1].upper()
    
    return f"AI-TUNER-{'-'.join(segments)}-{checksum}"
```

---

## Testing

### Test Cases

1. **No License**
   - App starts in demo mode
   - Restricted features disabled
   - Upgrade prompts shown

2. **Valid License**
   - App starts with full features
   - All features enabled
   - No restrictions

3. **Invalid License**
   - Rejected with error message
   - App remains in demo mode

4. **Expired License**
   - Falls back to demo mode
   - Shows expiration message
   - Upgrade prompt

5. **Device Mismatch**
   - License rejected
   - Shows device binding error

---

## Migration Path

### Phase 1: Basic Implementation (Week 1)
- License manager core
- Demo mode detection
- Basic feature gating

### Phase 2: UI Integration (Week 2)
- License entry dialog
- Status indicators
- Upgrade prompts

### Phase 3: Server Integration (Week 3-4)
- License server API
- Online validation
- Offline cache

### Phase 4: Advanced Features (Week 5+)
- Subscription support
- Analytics
- Advanced security

---

## Cost Considerations

### Self-Hosted (Option 1-3)
- **Development Time**: 2-4 weeks
- **Server Costs**: $10-50/month (if using server)
- **Maintenance**: Ongoing

### Third-Party (Option 5)
- **Setup Time**: 1-2 days
- **Monthly Fees**: $50-500/month
- **Transaction Fees**: 2-5% per sale
- **Maintenance**: Minimal

### Hardware (Option 4)
- **Development**: Already done
- **Hardware Cost**: $50-100 per YubiKey
- **User Cost**: Passed to customer

---

## Recommendation

**Start with Option 1 (Simple License Key)** for MVP:
- Quick implementation (1-2 days)
- Works immediately
- No external dependencies
- Can upgrade to Option 3 later

**Upgrade to Option 3 (Hybrid)** for production:
- Better security
- Server validation
- Subscription support
- Professional implementation

This gives you a working system quickly while maintaining a path to a more robust solution.










