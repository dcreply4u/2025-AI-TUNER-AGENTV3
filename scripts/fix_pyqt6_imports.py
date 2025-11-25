#!/usr/bin/env python3
"""
Fix PyQt6 imports to PySide6
Replaces all PyQt6 imports with PySide6 equivalents
"""

import os
import re
from pathlib import Path

# Mapping of PyQt5/PyQt6 to PySide6
REPLACEMENTS = [
    # PyQt6 module imports
    (r'from PyQt6\.QtCore import', 'from PySide6.QtCore import'),
    (r'from PyQt6\.QtGui import', 'from PySide6.QtGui import'),
    (r'from PyQt6\.QtWidgets import', 'from PySide6.QtWidgets import'),
    (r'from PyQt6\.QtNetwork import', 'from PySide6.QtNetwork import'),
    (r'from PyQt6\.QtWebEngineWidgets import', 'from PySide6.QtWebEngineWidgets import'),
    (r'import PyQt6', 'import PySide6'),
    
    # PyQt5 module imports
    (r'from PyQt5\.QtCore import', 'from PySide6.QtCore import'),
    (r'from PyQt5\.QtGui import', 'from PySide6.QtGui import'),
    (r'from PyQt5\.QtWidgets import', 'from PySide6.QtWidgets import'),
    (r'from PyQt5\.QtNetwork import', 'from PySide6.QtNetwork import'),
    (r'import PyQt5', 'import PySide6'),
    
    # Signal/Property names (works for both PyQt5 and PyQt6)
    (r'pyqtSignal', 'Signal'),
    (r'pyqtProperty', 'Property'),
    (r'pyqtSlot', 'Slot'),
    
    # QApplication references
    (r'PyQt6\.QtWidgets\.QApplication', 'PySide6.QtWidgets.QApplication'),
    (r'PyQt5\.QtWidgets\.QApplication', 'PySide6.QtWidgets.QApplication'),
    (r'PyQt6\.QtCore\.Qt', 'PySide6.QtCore.Qt'),
    (r'PyQt5\.QtCore\.Qt', 'PySide6.QtCore.Qt'),
]

def fix_file(file_path: Path) -> bool:
    """Fix PyQt6 imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all Python files in the project."""
    project_root = Path(__file__).parent.parent
    ui_dir = project_root / 'ui'
    services_dir = project_root / 'services'
    
    files_fixed = 0
    files_checked = 0
    
    # Find all Python files
    for directory in [ui_dir, services_dir]:
        if not directory.exists():
            continue
            
        for py_file in directory.rglob('*.py'):
            files_checked += 1
            if fix_file(py_file):
                files_fixed += 1
                print(f"Fixed: {py_file.relative_to(project_root)}")
    
    print(f"\nFixed {files_fixed} files out of {files_checked} checked")

if __name__ == '__main__':
    main()

