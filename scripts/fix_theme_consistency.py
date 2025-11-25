"""Fix theme consistency in main_container.py - replace all dark theme with light theme"""
import re
from pathlib import Path

file_path = Path(__file__).parent.parent / "ui" / "main_container.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replacements: (old, new)
replacements = [
    # Colors
    ('color: #ffffff', 'color: #2c3e50'),
    ('color:#ffffff', 'color: #2c3e50'),
    ('background-color: #2a2a2a', 'background-color: #ffffff'),
    ('background-color:#2a2a2a', 'background-color: #ffffff'),
    ('background-color: #1a1a1a', 'background-color: #e8e9ea'),
    ('background-color:#1a1a1a', 'background-color: #e8e9ea'),
    ('background-color: #0a0a0a', 'background-color: #ffffff'),
    ('background-color:#0a0a0a', 'background-color: #ffffff'),
    # Borders
    ('border: 1px solid #404040', 'border: 1px solid #bdc3c7'),
    ('border:1px solid #404040', 'border: 1px solid #bdc3c7'),
    ('border: 2px solid #404040', 'border: 2px solid #bdc3c7'),
    ('border:2px solid #404040', 'border: 2px solid #bdc3c7'),
    # Gridlines
    ('gridline-color: #404040', 'gridline-color: #bdc3c7'),
    ('gridline-color:#404040', 'gridline-color: #bdc3c7'),
]

# Apply replacements
for old, new in replacements:
    content = content.replace(old, new)

# Also fix QGroupBox styles that might have dark backgrounds
content = re.sub(
    r'(QGroupBox\s*\{[^}]*background-color:\s*#ffffff;)',
    r'\1',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Ensure all QGroupBox have white background
content = re.sub(
    r'(QGroupBox\s*\{[^}]*font-size:[^}]*font-weight:[^}]*color:\s*#2c3e50;[^}]*border:[^}]*border-radius:[^}]*margin-top:[^}]*padding-top:[^}]*)(\})',
    r'\1\n                background-color: #ffffff;\2',
    content,
    flags=re.MULTILINE | re.DOTALL
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed theme consistency in {file_path}")
print("Replaced dark theme colors with light theme colors")




