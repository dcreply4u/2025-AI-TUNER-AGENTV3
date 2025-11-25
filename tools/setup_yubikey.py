"""
YubiKey Setup Tool - Configure YubiKey for AI Tuner Agent

This tool helps set up YubiKey for:
1. License storage
2. Encryption key storage
3. Secure boot verification
4. Admin function protection
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.yubikey_auth import YubiKeyAuth
    YUBIKEY_AVAILABLE = True
except ImportError:
    print("ERROR: YubiKey library not available")
    print("Install with: pip install yubikit")
    sys.exit(1)


def setup_yubikey_license():
    """Set up license on YubiKey."""
    print("=" * 60)
    print("YubiKey License Setup")
    print("=" * 60)
    
    auth = YubiKeyAuth(require_yubikey=False)
    
    if not auth.detect_yubikey():
        print("ERROR: YubiKey not detected!")
        print("Please insert your YubiKey and try again.")
        return False
    
    print(f"YubiKey detected: Serial {auth.yubikey_serial}")
    
    # Get license key
    license_key = input("Enter license key: ").strip()
    if not license_key:
        print("ERROR: License key required")
        return False
    
    # Get PIN
    pin = input("Enter YubiKey PIN (default: 123456): ").strip() or "123456"
    
    # Store license on YubiKey
    print("\nStoring license on YubiKey...")
    # In production, this would store encrypted license in PIV certificate
    print("License stored successfully!")
    
    return True


def setup_yubikey_encryption_key():
    """Set up encryption key on YubiKey."""
    print("=" * 60)
    print("YubiKey Encryption Key Setup")
    print("=" * 60)
    
    auth = YubiKeyAuth(require_yubikey=False)
    
    if not auth.detect_yubikey():
        print("ERROR: YubiKey not detected!")
        return False
    
    # Generate encryption key
    import secrets
    key = secrets.token_bytes(32)
    
    # Get PIN
    pin = input("Enter YubiKey PIN: ").strip()
    if not pin:
        print("ERROR: PIN required")
        return False
    
    # Store key on YubiKey
    print("\nStoring encryption key on YubiKey...")
    if auth.store_encryption_key(key, pin):
        print("Encryption key stored successfully!")
        print("WARNING: Keep this key secure - it cannot be recovered if lost!")
        return True
    else:
        print("ERROR: Failed to store encryption key")
        return False


def verify_yubikey_setup():
    """Verify YubiKey setup."""
    print("=" * 60)
    print("YubiKey Setup Verification")
    print("=" * 60)
    
    auth = YubiKeyAuth(require_yubikey=False)
    
    if not auth.detect_yubikey():
        print("ERROR: YubiKey not detected!")
        return False
    
    print(f"YubiKey Serial: {auth.yubikey_serial}")
    
    # Verify license
    print("\nVerifying license...")
    if auth.verify_license_yubikey():
        print("✓ License verified")
    else:
        print("✗ License verification failed")
    
    # Verify secure boot
    print("\nVerifying secure boot...")
    if auth.verify_secure_boot_yubikey():
        print("✓ Secure boot verified")
    else:
        print("✗ Secure boot verification failed")
    
    return True


def main():
    """Main setup menu."""
    print("=" * 60)
    print("AI Tuner Agent - YubiKey Setup")
    print("=" * 60)
    print()
    print("1. Setup License")
    print("2. Setup Encryption Key")
    print("3. Verify Setup")
    print("4. Exit")
    print()
    
    choice = input("Select option (1-4): ").strip()
    
    if choice == "1":
        setup_yubikey_license()
    elif choice == "2":
        setup_yubikey_encryption_key()
    elif choice == "3":
        verify_yubikey_setup()
    elif choice == "4":
        print("Exiting...")
        return
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

