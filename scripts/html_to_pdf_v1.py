"""
Convert HTML files to PDF using browser automation
"""

import sys
from pathlib import Path

def convert_with_playwright(html_file: Path, pdf_file: Path) -> bool:
    """Convert HTML to PDF using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_file.absolute()}")
            page.pdf(path=str(pdf_file), format='A4', print_background=True)
            browser.close()
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def convert_with_selenium(html_file: Path, pdf_file: Path) -> bool:
    """Convert HTML to PDF using Selenium."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        driver = webdriver.Chrome(options=options)
        driver.get(f"file://{html_file.absolute()}")
        
        # Use Chrome's print to PDF
        print_options = {
            'printBackground': True,
            'paperFormat': 'A4'
        }
        result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
        
        import base64
        pdf_data = base64.b64decode(result['data'])
        with open(pdf_file, 'wb') as f:
            f.write(pdf_data)
        
        driver.quit()
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    """Convert all HTML files in pdf_v1 directory to PDF."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    html_dir = project_root / "docs" / "pdf_v1"
    
    if not html_dir.exists():
        print(f"HTML directory not found: {html_dir}")
        return
    
    html_files = list(html_dir.glob("*.html"))
    
    if not html_files:
        print("No HTML files found")
        return
    
    print(f"Found {len(html_files)} HTML files to convert")
    print("-" * 60)
    
    success = 0
    failed = 0
    
    for html_file in sorted(html_files):
        pdf_file = html_dir / f"{html_file.stem.replace('_v1', '')}_v1.pdf"
        
        # Try playwright first
        if convert_with_playwright(html_file, pdf_file):
            print(f"[OK] {html_file.name} -> {pdf_file.name}")
            success += 1
            continue
        
        # Try selenium
        if convert_with_selenium(html_file, pdf_file):
            print(f"[OK] {html_file.name} -> {pdf_file.name}")
            success += 1
            continue
        
        print(f"[SKIP] {html_file.name} (install playwright: pip install playwright)")
        failed += 1
    
    print("-" * 60)
    print(f"Conversion complete: {success} PDFs created, {failed} skipped")
    
    if failed > 0:
        print("\nTo convert remaining files:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print("  python scripts/html_to_pdf_v1.py")

if __name__ == "__main__":
    main()







