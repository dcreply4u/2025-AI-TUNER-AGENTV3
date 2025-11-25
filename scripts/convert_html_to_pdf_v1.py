"""
Convert HTML files to PDF using multiple methods
"""

from pathlib import Path
import subprocess
import sys

def convert_with_playwright(html_file: Path, pdf_file: Path) -> bool:
    """Convert using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_file.absolute()}")
            page.pdf(path=str(pdf_file), format='A4', print_background=True)
            browser.close()
        return True
    except:
        return False

def main():
    """Convert all HTML files to PDF."""
    # Find project root
    current = Path.cwd()
    if (current / "docs" / "pdf_v1").exists():
        html_dir = current / "docs" / "pdf_v1"
    elif (current / "AI-TUNER-AGENT" / "docs" / "pdf_v1").exists():
        html_dir = current / "AI-TUNER-AGENT" / "docs" / "pdf_v1"
    else:
        print("Could not find pdf_v1 directory")
        return
    
    html_files = list(html_dir.glob("*.html"))
    
    if not html_files:
        print("No HTML files found")
        return
    
    print(f"Converting {len(html_files)} HTML files to PDF...")
    
    success = 0
    for html_file in html_files:
        pdf_file = html_dir / f"{html_file.stem.replace('_v1', '')}_v1.pdf"
        
        if convert_with_playwright(html_file, pdf_file):
            print(f"[OK] {html_file.name}")
            success += 1
        else:
            print(f"[SKIP] {html_file.name} - Install: pip install playwright && playwright install chromium")
    
    print(f"\nComplete: {success}/{len(html_files)} converted to PDF")

if __name__ == "__main__":
    main()







