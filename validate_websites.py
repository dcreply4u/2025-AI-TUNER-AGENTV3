#!/usr/bin/env python3
"""
Validate Website URLs
Quick script to check if website URLs are accessible.
"""

import requests
from services.website_list_manager import WebsiteListManager

def validate_url(url: str) -> tuple[bool, str]:
    """Validate a URL is accessible."""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return True, f"✓ Accessible (Status: {response.status_code})"
        else:
            return False, f"✗ Status: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "✗ Timeout"
    except requests.exceptions.ConnectionError:
        return False, "✗ Connection Error"
    except Exception as e:
        return False, f"✗ Error: {str(e)[:50]}"

def main():
    """Validate all websites in the list."""
    print("=" * 70)
    print("Website URL Validation")
    print("=" * 70 + "\n")
    
    manager = WebsiteListManager()
    websites = manager.get_websites()
    
    print(f"Validating {len(websites)} websites...\n")
    
    results = []
    for site in websites:
        print(f"Checking: {site.name}")
        print(f"  URL: {site.url}")
        accessible, message = validate_url(site.url)
        print(f"  {message}\n")
        results.append((site.name, site.url, accessible, message))
    
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70 + "\n")
    
    accessible_count = sum(1 for _, _, accessible, _ in results if accessible)
    print(f"Accessible: {accessible_count}/{len(results)}")
    
    if accessible_count < len(results):
        print("\nInaccessible websites:")
        for name, url, accessible, message in results:
            if not accessible:
                print(f"  ✗ {name}: {url}")
                print(f"    {message}")

if __name__ == "__main__":
    main()

