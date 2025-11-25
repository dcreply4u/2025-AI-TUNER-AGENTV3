"""
Convert all documentation markdown files to PDF format with v1 suffix
Standalone script that works from any location
"""

import os
import sys
import subprocess
from pathlib import Path

def find_project_root():
    """Find the AI-TUNER-AGENT project root."""
    # Try current directory first
    current = Path.cwd()
    if (current / "docs").exists() and (current / "scripts").exists():
        return current
    
    # Try parent directories
    for parent in current.parents:
        if parent.name == "AI-TUNER-AGENT" and (parent / "docs").exists():
            return parent
    
    # Try looking for AI-TUNER-AGENT in current or parent
    if (current / "AI-TUNER-AGENT" / "docs").exists():
        return current / "AI-TUNER-AGENT"
    
    # Default to current directory
    return current

def convert_with_pandoc(md_file: Path, output_file: Path) -> bool:
    """Convert using pandoc if available."""
    try:
        result = subprocess.run(
            ['pandoc', str(md_file), '-o', str(output_file), '--pdf-engine=wkhtmltopdf'],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0 and output_file.exists():
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False

def convert_to_html(md_file: Path, output_dir: Path) -> Path:
    """Convert markdown to HTML."""
    try:
        import markdown
        
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = markdown.markdown(
            md_content,
            extensions=['fenced_code', 'tables', 'codehilite']
        )
    except ImportError:
        # Basic conversion without markdown library
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        html_content = md_content.replace('\n', '<br>\n')
    
    styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{md_file.stem}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
    
    html_file = output_dir / f"{md_file.stem}_v1.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    return html_file

def convert_html_to_pdf_with_browser(html_file: Path, pdf_file: Path) -> bool:
    """Try to convert HTML to PDF using system default browser print."""
    # This is a placeholder - actual conversion would need browser automation
    # For now, we'll create HTML files that can be manually converted
    return False

def main():
    """Convert all markdown files in docs directory to PDF."""
    # Find project root
    project_root = find_project_root()
    docs_dir = project_root / "docs"
    output_dir = project_root / "docs" / "pdf_v1"
    
    if not docs_dir.exists():
        print(f"Error: docs directory not found at {docs_dir}")
        print(f"Current directory: {Path.cwd()}")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all markdown files
    md_files = list(docs_dir.glob("*.md"))
    
    if not md_files:
        print(f"No markdown files found in {docs_dir}")
        return
    
    print(f"Found {len(md_files)} markdown files")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    # Convert each file
    success_pdf = 0
    success_html = 0
    failed = 0
    
    for md_file in sorted(md_files):
        output_file = output_dir / f"{md_file.stem}_v1.pdf"
        
        # Try pandoc first
        if convert_with_pandoc(md_file, output_file):
            print(f"[PDF] {md_file.name} -> {output_file.name} (pandoc)")
            success_pdf += 1
            continue
        
        # Fallback to HTML (can be converted to PDF manually)
        try:
            html_file = convert_to_html(md_file, output_dir)
            if html_file.exists():
                print(f"[HTML] {md_file.name} -> {html_file.name}")
                success_html += 1
            else:
                print(f"[FAIL] {md_file.name}")
                failed += 1
        except Exception as e:
            print(f"[FAIL] {md_file.name}: {e}")
            failed += 1
    
    print("-" * 60)
    print(f"Conversion complete!")
    print(f"  PDF files: {success_pdf}")
    print(f"  HTML files: {success_html}")
    print(f"  Failed: {failed}")
    print(f"  Output: {output_dir}")
    
    if success_html > 0:
        print("\nNote: HTML files can be converted to PDF:")
        print("  1. Open HTML file in browser (Chrome/Edge)")
        print("  2. Press Ctrl+P (Print)")
        print("  3. Select 'Save as PDF' as destination")
        print("  4. Save with _v1.pdf extension")
        print("\nOr install pandoc: https://pandoc.org/installing.html")

if __name__ == "__main__":
    main()
