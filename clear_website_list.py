#!/usr/bin/env python3
"""
Clear Website List

Removes all website entries from the website list since we're using Google search instead.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("CLEARING WEBSITE LIST")
print("="*80)
print()

try:
    from services.website_list_manager import WebsiteListManager
    
    # Initialize manager
    manager = WebsiteListManager()
    
    # Get current count
    current_count = len(manager.websites)
    print(f"Current websites in list: {current_count}")
    
    if current_count > 0:
        # List websites
        print("\nWebsites to be removed:")
        for url, entry in manager.websites.items():
            print(f"  - {entry.name} ({url})")
        
        # Clear all
        print(f"\nClearing all {current_count} websites...")
        removed = manager.clear_all_websites()
        
        print(f"✓ Successfully removed {removed} websites")
        print("\nNote: The advisor will now use Google search instead of forum scraping.")
        print("This is faster and more reliable.")
    else:
        print("✓ Website list is already empty")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("DONE")
print("="*80)

