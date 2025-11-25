"""
Quick test to verify demo works.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    from PySide6.QtWidgets import QApplication
    print("[OK] PySide6 imported")
except ImportError as e:
    print(f"[FAIL] PySide6 failed: {e}")
    sys.exit(1)

try:
    from services.data_simulator import DataSimulator
    print("[OK] DataSimulator imported")
except ImportError as e:
    print(f"[FAIL] DataSimulator failed: {e}")
    sys.exit(1)

try:
    from interfaces.simulated_interface import SimulatedInterface
    print("[OK] SimulatedInterface imported")
except ImportError as e:
    print(f"[FAIL] SimulatedInterface failed: {e}")
    sys.exit(1)

try:
    from ui.main import MainWindow
    print("[OK] MainWindow imported")
except ImportError as e:
    print(f"[FAIL] MainWindow failed: {e}")
    sys.exit(1)

print("\n[SUCCESS] All imports successful!")
print("You can run: python demo.py --no-voice")
print("The GUI window should open with simulated data.")

