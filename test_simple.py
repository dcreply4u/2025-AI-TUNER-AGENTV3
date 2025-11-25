"""
Test Simple Window - Minimal test to verify Qt works
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("Testing Simple Window")
print("=" * 80)

try:
    from ui.main_simple import main
    print("[OK] Imported simple main")
    main()
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)





