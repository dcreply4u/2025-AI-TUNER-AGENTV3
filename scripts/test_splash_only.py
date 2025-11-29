#!/usr/bin/env python3
"""Simple test script to verify splash screen works."""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault("DISPLAY", ":0")

from PySide6.QtWidgets import QApplication
from ui.startup_splash import show_startup_splash_if_available
import time

print("=" * 60)
print("SPLASH SCREEN TEST")
print("=" * 60)

app = QApplication(sys.argv)
print("[OK] QApplication created")

# Process events to ensure QApplication is ready
for _ in range(3):
    app.processEvents()

print("\n[TEST] Creating splash screen...")
splash = show_startup_splash_if_available()

if splash:
    print(f"[OK] Splash created: {splash}")
    print(f"[INFO] Splash size: {splash.width()}x{splash.height()}")
    print(f"[INFO] Splash position: {splash.pos().x()}, {splash.pos().y()}")
    print(f"[INFO] Splash visible: {splash.isVisible()}")
    
    # Process events to show splash
    for _ in range(5):
        app.processEvents()
        time.sleep(0.1)
    
    print("\n[TEST] Splash should be visible now")
    print("[INFO] Waiting 3 seconds...")
    time.sleep(3)
    
    print("\n[TEST] Closing splash...")
    splash.hide()
else:
    print("[ERROR] Splash creation failed!")

app.quit()
print("\n[OK] Test completed")

