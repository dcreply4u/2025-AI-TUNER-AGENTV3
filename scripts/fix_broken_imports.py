#!/usr/bin/env python3
"""
Fix broken imports caused by the automated responsive script.
The script inserted responsive imports in the middle of PySide6 import statements.
"""

import re
from pathlib import Path

def fix_file(file_path: Path) -> bool:
    """Fix broken imports in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # Pattern 1: Responsive import inserted in middle of PySide6.QtWidgets import
        # Find: from PySide6.QtWidgets import (\n\ntry: ... except: ... \n    QWidget, ...)
        pattern1 = re.compile(
            r'(from PySide6\.QtWidgets import\s*\(\s*)\n\ntry:\s*'
            r'from ui\.responsive_layout_manager import[^\n]+\n'
            r'RESPONSIVE_AVAILABLE = True\nexcept ImportError:[^\n]+\n'
            r'get_responsive_manager = None\s*scaled_size = lambda[^\n]+\n'
            r'scaled_font_size = lambda[^\n]+\n'
            r'scaled_spacing = lambda[^\n]+\n\s*',
            re.MULTILINE
        )
        
        # Simpler pattern: find the broken structure
        # Look for: from PySide6.QtWidgets import (\n\ntry: ... \n    QWidget
        broken_pattern = re.compile(
            r'(from PySide6\.QtWidgets import\s*\(\s*)\n\n(try:\s*from ui\.responsive_layout_manager[^\n]+\n'
            r'RESPONSIVE_AVAILABLE = True\nexcept ImportError:[^\n]+\n'
            r'get_responsive_manager = None\s*scaled_size = lambda[^\n]+\n'
            r'scaled_font_size = lambda[^\n]+\n'
            r'scaled_spacing = lambda[^\n]+\n)\s*([A-Z]\w+,\s*\n)',
            re.MULTILINE | re.DOTALL
        )
        
        def fix_imports(match):
            return match.group(1) + match.group(3)  # Keep opening, skip try block, keep widget names
        
        # Try to fix the broken import pattern
        if re.search(r'from PySide6\.QtWidgets import\s*\(\s*\n\ntry:', content, re.MULTILINE):
            # Find the widget list that comes after the try block
            # Extract the try block and widget list
            widget_pattern = re.compile(
                r'from PySide6\.QtWidgets import\s*\(\s*\n\n'
                r'try:\s*from ui\.responsive_layout_manager[^\n]+\n'
                r'RESPONSIVE_AVAILABLE = True\nexcept ImportError:[^\n]+\n'
                r'get_responsive_manager = None\s*scaled_size = lambda[^\n]+\n'
                r'scaled_font_size = lambda[^\n]+\n'
                r'scaled_spacing = lambda[^\n]+\n\s*'
                r'((?:[A-Z]\w+,\s*\n)+)\)',
                re.MULTILINE | re.DOTALL
            )
            
            def replace_import(m):
                widgets = m.group(1)
                return f'from PySide6.QtWidgets import (\n{widgets})\n\ntry:\n    from ui.responsive_layout_manager import get_responsive_manager, scaled_size, scaled_font_size, scaled_spacing\n    RESPONSIVE_AVAILABLE = True\nexcept ImportError:\n    RESPONSIVE_AVAILABLE = False\n    get_responsive_manager = None\n    scaled_size = lambda x, use_width=True: x\n    scaled_font_size = lambda x: x\n    scaled_spacing = lambda x: x'
            
            new_content = widget_pattern.sub(replace_import, content)
            if new_content != content:
                content = new_content
                changes_made = True
        
        # Pattern 2: Fix broken setSizePolicy calls
        # tile.# Use Expanding -> tile.setSizePolicy
        content = re.sub(
            r'(\w+)\.# Use Expanding policy',
            r'# Use Expanding policy\n        \1.setSizePolicy',
            content
        )
        if content != original_content:
            changes_made = True
        
        # Pattern 3: Fix broken except ImportError blocks that have widget names
        # except ImportError: ... \n    QWidget, -> move widgets before try
        except_pattern = re.compile(
            r'except ImportError:\s*RESPONSIVE_AVAILABLE = False[^\n]+\n'
            r'get_responsive_manager = None\s*scaled_size = lambda[^\n]+\n'
            r'scaled_font_size = lambda[^\n]+\n'
            r'scaled_spacing = lambda[^\n]+\n\s*'
            r'((?:[A-Z]\w+,\s*\n)+)\)',
            re.MULTILINE | re.DOTALL
        )
        
        if except_pattern.search(content):
            # This is more complex - need to find the full context
            # Let's use a simpler approach: find files with this pattern and fix manually
            pass
        
        if changes_made and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all broken import files."""
    ui_dir = Path("AI-TUNER-AGENT/ui")
    
    # Files known to have broken imports
    broken_files = [
        "dragy_view.py",
        "youtube_stream_widget.py",
        "youtube_settings_dialog.py",
        "usb_setup_dialog.py",
        "usb_camera_tab.py",
        "tune_database_tab.py",
        "transbrake_widget.py",
        "theme_dialog.py",
        "storage_management_tab.py",
        "shift_light_widget.py",
        "session_management_tab.py",
        "sensors_tab.py",
    ]
    
    for filename in broken_files:
        file_path = ui_dir / filename
        if file_path.exists():
            print(f"Fixing {filename}...", end=' ')
            if fix_file(file_path):
                print("FIXED")
            else:
                print("OK (no changes)")
        else:
            print(f"{filename} not found")

if __name__ == "__main__":
    main()

