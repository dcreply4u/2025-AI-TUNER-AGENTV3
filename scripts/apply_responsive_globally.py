#!/usr/bin/env python3
"""
Script to apply responsive UI principles globally across the application.
This script updates widgets to use responsive sizing, spacing, and layouts.
"""

import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def update_widget_file(file_path: Path) -> bool:
    """Update a widget file to use responsive functions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = False
        
        # Check if responsive imports are already present
        has_responsive_import = 'from ui.responsive_layout_manager import' in content
        
        # Add responsive imports if not present and file uses QWidget/QVBoxLayout/QHBoxLayout
        if not has_responsive_import and any(x in content for x in ['QWidget', 'QVBoxLayout', 'QHBoxLayout', 'QSizePolicy']):
            # Find the last import statement
            import_pattern = r'(from PySide6\.QtWidgets import[^\n]+\n)'
            matches = list(re.finditer(import_pattern, content))
            if matches:
                last_import = matches[-1]
                insert_pos = last_import.end()
                # Add responsive imports
                responsive_import = (
                    "\n"
                    "try:\n"
                    "    from ui.responsive_layout_manager import get_responsive_manager, scaled_size, scaled_font_size, scaled_spacing\n"
                    "    RESPONSIVE_AVAILABLE = True\n"
                    "except ImportError:\n"
                    "    RESPONSIVE_AVAILABLE = False\n"
                    "    get_responsive_manager = None\n"
                    "    scaled_size = lambda x, use_width=True: x\n"
                    "    scaled_font_size = lambda x: x\n"
                    "    scaled_spacing = lambda x: x\n"
                )
                content = content[:insert_pos] + responsive_import + content[insert_pos:]
                changes_made = True
        
        # Replace fixed pixel values in setSpacing calls
        spacing_pattern = r'setSpacing\((\d+)\)'
        def replace_spacing(match):
            value = int(match.group(1))
            return f'setSpacing(scaled_spacing({value}))'
        
        if re.search(spacing_pattern, content):
            content = re.sub(spacing_pattern, replace_spacing, content)
            changes_made = True
        
        # Replace fixed pixel values in setContentsMargins calls
        margins_pattern = r'setContentsMargins\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)'
        def replace_margins(match):
            values = [int(match.group(i)) for i in range(1, 5)]
            return f'setContentsMargins({", ".join(f"scaled_spacing({v})" for v in values)})'
        
        if re.search(margins_pattern, content):
            content = re.sub(margins_pattern, replace_margins, content)
            changes_made = True
        
        # Replace fixed font sizes in stylesheets (font-size: XXpx)
        font_size_pattern = r'font-size:\s*(\d+)px'
        def replace_font_size(match):
            value = int(match.group(1))
            return f'font-size: {{scaled_font_size({value})}}px'
        
        # Only replace if not already using a variable
        if re.search(font_size_pattern, content) and '{scaled_font_size' not in content:
            # More careful replacement - only in stylesheet strings
            def replace_in_stylesheet(match):
                full_match = match.group(0)
                value = int(match.group(1))
                return f'font-size: {{{{scaled_font_size({value})}}}}px'
            
            # Find stylesheet strings and replace within them
            stylesheet_pattern = r'setStyleSheet\(["\']([^"\']*font-size:\s*(\d+)px[^"\']*)["\']\)'
            def replace_stylesheet(match):
                stylesheet = match.group(1)
                new_stylesheet = re.sub(font_size_pattern, lambda m: f'{{scaled_font_size({m.group(1)})}}px', stylesheet)
                return f'setStyleSheet("{new_stylesheet}")'
            
            # This is complex - let's do a simpler approach
            # Just add a comment suggesting manual update
            if 'font-size:' in content and 'scaled_font_size' not in content:
                # Add a comment at the top if not already there
                if '# TODO: Apply responsive font sizing' not in content:
                    # Find first class definition
                    class_pattern = r'(class \w+\([^:]+\):)'
                    class_match = re.search(class_pattern, content)
                    if class_match:
                        insert_pos = class_match.start()
                        comment = "\n        # TODO: Apply responsive font sizing to stylesheets\n"
                        content = content[:insert_pos] + comment + content[insert_pos:]
                        changes_made = True
        
        # Replace fixed sizes in setMinimumSize, setMaximumSize, resize
        size_patterns = [
            (r'setMinimumSize\((\d+),\s*(\d+)\)', 'setMinimumSize'),
            (r'setMaximumSize\((\d+),\s*(\d+)\)', 'setMaximumSize'),
            (r'resize\((\d+),\s*(\d+)\)', 'resize'),
        ]
        
        for pattern, func_name in size_patterns:
            def make_replacer(fname):
                def replacer(match):
                    w = int(match.group(1))
                    h = int(match.group(2))
                    return f'{fname}(scaled_size({w}), scaled_size({h}, use_width=False))'
                return replacer
            
            if re.search(pattern, content):
                content = re.sub(pattern, make_replacer(func_name), content)
                changes_made = True
        
        # Ensure QSizePolicy.Expanding is used for flexible widgets
        if 'setSizePolicy' in content and 'QSizePolicy.Policy.Expanding' not in content:
            # Add comment suggesting to use Expanding policy
            if '# TODO: Use QSizePolicy.Expanding for responsive widgets' not in content:
                # Find setSizePolicy calls
                policy_pattern = r'(setSizePolicy\([^)]+\))'
                if re.search(policy_pattern, content):
                    # Add comment before first occurrence
                    first_match = re.search(policy_pattern, content)
                    if first_match:
                        insert_pos = first_match.start()
                        comment = "# Use Expanding policy for responsive behavior\n        "
                        content = content[:insert_pos] + comment + content[insert_pos:]
                        changes_made = True
        
        if changes_made and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to apply responsive principles globally."""
    ui_dir = project_root / "ui"
    
    if not ui_dir.exists():
        print(f"UI directory not found: {ui_dir}")
        return
    
    widget_files = list(ui_dir.glob("*.py"))
    
    print(f"Found {len(widget_files)} widget files to process")
    print("=" * 60)
    
    updated_count = 0
    for widget_file in widget_files:
        if widget_file.name.startswith('_'):
            continue
        
        print(f"Processing: {widget_file.name}...", end=' ')
        if update_widget_file(widget_file):
            print("UPDATED")
            updated_count += 1
        else:
            print("OK (no changes needed)")
    
    print("=" * 60)
    print(f"Updated {updated_count} files")
    print("\nNote: Some manual updates may be needed for:")
    print("  - Complex stylesheet strings with font-size")
    print("  - Widget-specific responsive configurations")
    print("  - Graph widgets (use configure_graph_responsive)")


if __name__ == "__main__":
    main()

