#!/usr/bin/env python3
"""
Fix broken responsive imports inserted by automated script.
The script inserted try/except blocks in the middle of existing try/except blocks.
"""

import os
import re
from pathlib import Path

UI_DIR = Path(__file__).parent.parent / "ui"

RESPONSIVE_IMPORT_PATTERN = r"""try:
    from ui\.responsive_layout_manager import get_responsive_manager, scaled_size, scaled_font_size, scaled_spacing
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False
    get_responsive_manager = None
    scaled_size = lambda x, use_width=True: x
    scaled_font_size = lambda x: x
    scaled_spacing = lambda x: x"""

RESPONSIVE_IMPORT_CLEAN = """try:
    from ui.responsive_layout_manager import get_responsive_manager, scaled_size, scaled_font_size, scaled_spacing
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False
    get_responsive_manager = None
    scaled_size = lambda x, use_width=True: x
    scaled_font_size = lambda x: x
    scaled_spacing = lambda x: x"""

def fix_file(filepath):
    """Fix a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Pattern 1: Responsive import inserted in middle of incomplete try/except
        # Look for: except ImportError:\n    try:\n        from PySide6...\n\n    try:\n        from ui.responsive...
        # This is broken - the responsive try should be at module level
        
        # Pattern 2: Responsive import with broken indentation inside method
        # Look for: \n        try:\n    from ui.responsive... (wrong indentation)
        
        # Pattern 3: Responsive import with orphaned except
        # Look for: ...scaled_spacing = lambda x: x\n    except ImportError: (orphaned except)
        
        # Fix pattern: Move responsive imports to top of file (after standard imports)
        # Find where standard imports end
        lines = content.split('\n')
        fixed_lines = []
        responsive_import_found = False
        responsive_import_lines = []
        in_broken_block = False
        skip_until_except = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Detect broken responsive import block
            if 'from ui.responsive_layout_manager import' in line:
                # Check if this is in a broken location
                if i > 0 and lines[i-1].strip() == 'try:':
                    # This is the broken pattern - skip the entire broken block
                    responsive_import_found = True
                    # Skip the try line
                    i += 1
                    # Collect responsive import lines
                    while i < len(lines) and not (lines[i].strip().startswith('except ImportError:') and 'scaled_spacing' in lines[i-1] if i > 0 else False):
                        if 'from ui.responsive_layout_manager' in lines[i] or 'RESPONSIVE_AVAILABLE' in lines[i] or 'scaled_size' in lines[i] or 'scaled_font_size' in lines[i] or 'scaled_spacing' in lines[i] or 'get_responsive_manager' in lines[i] or lines[i].strip() == 'try:' or lines[i].strip() == 'except ImportError:':
                            if 'from ui.responsive_layout_manager' in lines[i] or 'RESPONSIVE_AVAILABLE' in lines[i] or 'scaled_size' in lines[i] or 'scaled_font_size' in lines[i] or 'scaled_spacing' in lines[i] or 'get_responsive_manager' in lines[i]:
                                responsive_import_lines.append(lines[i])
                        i += 1
                    # Skip the except block
                    if i < len(lines) and 'except ImportError:' in lines[i]:
                        i += 1
                        # Skip lambda definitions
                        while i < len(lines) and ('lambda' in lines[i] or lines[i].strip() == '' or lines[i].strip().startswith('RESPONSIVE') or lines[i].strip().startswith('get_responsive') or lines[i].strip().startswith('scaled_')):
                            i += 1
                    continue
            
            # Skip orphaned except blocks after responsive imports
            if line.strip() == 'except ImportError:' and i > 0:
                # Check if previous non-empty line was part of responsive import
                prev_idx = i - 1
                while prev_idx >= 0 and lines[prev_idx].strip() == '':
                    prev_idx -= 1
                if prev_idx >= 0 and ('scaled_spacing' in lines[prev_idx] or 'RESPONSIVE' in lines[prev_idx]):
                    # This is an orphaned except - skip it and its block
                    i += 1
                    while i < len(lines) and (lines[i].strip().startswith('from PyQt') or lines[i].strip().startswith('from PySide') or lines[i].strip() == ''):
                        i += 1
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        # If we found responsive imports, add them at the top (after standard imports)
        if responsive_import_found or responsive_import_lines:
            # Find insertion point (after imports, before first class/def)
            insert_idx = 0
            for idx, line in enumerate(fixed_lines):
                if line.strip().startswith('class ') or (line.strip().startswith('def ') and not line.strip().startswith('def __')):
                    insert_idx = idx
                    break
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""') and not line.strip().startswith("'''") and not line.strip().startswith('from ') and not line.strip().startswith('import ') and not line.strip().startswith('try:') and not line.strip().startswith('except'):
                    # This might be the start of code
                    if idx > 0:
                        insert_idx = idx
                        break
            
            # Insert responsive imports
            if insert_idx > 0:
                fixed_lines.insert(insert_idx, '')
                fixed_lines.insert(insert_idx, RESPONSIVE_IMPORT_CLEAN)
                fixed_lines.insert(insert_idx, '')
        
        fixed_content = '\n'.join(fixed_lines)
        
        # Additional cleanup: Remove broken patterns
        # Pattern: incomplete try blocks
        fixed_content = re.sub(r'except ImportError:\s+try:\s+from PySide6[^\n]+\n\s+try:', 'except ImportError:', fixed_content, flags=re.MULTILINE)
        
        # Pattern: orphaned except after responsive
        fixed_content = re.sub(r'scaled_spacing = lambda[^\n]+\n\s+except ImportError:', 'scaled_spacing = lambda x: x', fixed_content, flags=re.MULTILINE)
        
        if fixed_content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Fix all UI files."""
    fixed_count = 0
    error_count = 0
    
    for py_file in UI_DIR.glob("*.py"):
        if fix_file(py_file):
            print(f"Fixed: {py_file.name}")
            fixed_count += 1
        else:
            # Try to compile to check for errors
            import py_compile
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                print(f"Still has errors: {py_file.name} - {e}")
                error_count += 1
    
    print(f"\nFixed {fixed_count} files")
    if error_count > 0:
        print(f"Still {error_count} files with errors")

if __name__ == "__main__":
    main()



