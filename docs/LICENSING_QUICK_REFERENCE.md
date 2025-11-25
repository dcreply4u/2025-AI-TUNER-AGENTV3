# Licensing System - Quick Reference

## Quick Summary

**Current Status:** Basic license infrastructure exists, but no demo mode restrictions implemented.

**Recommended Approach:** Start with Simple License Key System (Option 1), upgrade to Hybrid System (Option 3) for production.

## Options Comparison

| Option | Security | Complexity | Cost | Best For |
|-------|----------|------------|------|----------|
| **1. Simple Key** | Low-Medium | Low | Free | MVP, Quick Launch |
| **2. Server-Based** | High | Medium | $10-50/mo | Production, Subscriptions |
| **3. Hybrid** | High | Medium-High | $10-50/mo | **Recommended** |
| **4. YubiKey** | Very High | Low | $50-100/key | Enterprise |
| **5. Third-Party** | High | Low | $50-500/mo | Fast Launch |

## Implementation Checklist

### Phase 1: Basic License System (1-2 days)
- [ ] Create `core/license_manager.py`
- [ ] Create `core/demo_restrictions.py`
- [ ] Add license entry dialog
- [ ] Add license status indicator
- [ ] Implement feature gating

### Phase 2: Demo Mode Restrictions (1 day)
- [ ] Disable ECU write operations
- [ ] Limit data logging (5 min sessions)
- [ ] Limit exports (10 max)
- [ ] Disable advanced AI features
- [ ] Disable cloud sync
- [ ] Add "Demo Mode" badges

### Phase 3: Server Integration (Optional, 1-2 weeks)
- [ ] Create license server API
- [ ] Implement online validation
- [ ] Add offline cache
- [ ] Add periodic validation

## Quick Start Code

```python
# In main application startup
from core.license_manager import LicenseManager

license_manager = LicenseManager()

if license_manager.is_demo_mode():
    print("DEMO MODE - Limited features")
else:
    print(f"Licensed: {license_manager.get_license_type().value}")

# Feature check
if license_manager.is_feature_enabled('ecu_tuning_write'):
    # Allow ECU writes
    pass
else:
    # Show demo mode message
    pass
```

## Demo Mode Restrictions

### ✅ Allowed
- View all UI
- View telemetry
- View settings (read-only)
- Basic AI advisor
- Limited exports (10 max)

### ❌ Restricted
- ECU tuning writes
- Advanced AI (ML models)
- Cloud sync
- Video recording
- Auto tuning
- Racing controls (write)
- Unlimited data logging

## License Key Format

```
AI-TUNER-XXXX-XXXX-XXXX-XXXX
```

Example: `AI-TUNER-B123-A456-C789-D012`

## Files to Create/Modify

1. **New Files:**
   - `core/license_manager.py` - License validation
   - `core/demo_restrictions.py` - Usage limits
   - `ui/license_dialog.py` - License entry UI

2. **Modify:**
   - `demo.py` - Add license check
   - `ui/main_container.py` - Add license status
   - Feature modules - Add license checks

## See Also

- [Full Licensing Options Document](LICENSING_OPTIONS.md)
- [Code Protection System](../core/code_protection.py)
- [YubiKey Integration](YUBIKEY_INTEGRATION.md)










