#!/usr/bin/env python3
"""
Test script for Google Search API integration.

Tests:
1. Google Search API initialization
2. General web search
3. Custom search engine (if configured)
4. Forum-specific search
5. Quota management
6. Fallback to DuckDuckGo
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)

LOGGER = logging.getLogger(__name__)


def test_google_search_service():
    """Test Google Search Service directly."""
    print("\n" + "="*60)
    print("Testing Google Search Service")
    print("="*60)
    
    try:
        from services.google_search_service import GoogleSearchService
        
        # Initialize service
        print("\n1. Initializing Google Search Service...")
        service = GoogleSearchService()
        
        if not service.is_available:
            print("   ❌ Google Search API not available")
            print("   💡 Set GOOGLE_SEARCH_API_KEY environment variable")
            return False
        
        print("   ✅ Google Search API initialized")
        
        # Check quota status
        print("\n2. Checking quota status...")
        quota = service.get_quota_status()
        print(f"   Available: {quota['available']}")
        print(f"   Daily used: {quota['daily_used']}/{quota['daily_limit']}")
        print(f"   Remaining: {quota['remaining']}")
        print(f"   Custom search: {quota['custom_search_enabled']}")
        
        # Test general search
        print("\n3. Testing general web search...")
        results = service.search("what is fuel pressure in ECU tuning", max_results=3)
        if results:
            print(f"   ✅ Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result.title}")
                print(f"      {result.url}")
                print(f"      {result.snippet[:100]}...")
        else:
            print("   ❌ No results")
        
        # Test custom search (if available)
        if service.enable_custom_search:
            print("\n4. Testing custom search engine...")
            results = service.search(
                "ECU tuning fuel pressure",
                max_results=3,
                use_custom_search=True
            )
            if results:
                print(f"   ✅ Found {len(results)} results from custom search")
            else:
                print("   ⚠️  No results from custom search")
        
        # Test forum search
        print("\n5. Testing forum-specific search...")
        results = service.search_forum(
            "fuel pressure tuning",
            "bimmerforums.com",
            max_results=3
        )
        if results:
            print(f"   ✅ Found {len(results)} results from forum")
        else:
            print("   ⚠️  No results from forum (may not be indexed)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_search_service_integration():
    """Test WebSearchService with Google API integration."""
    print("\n" + "="*60)
    print("Testing WebSearchService Integration")
    print("="*60)
    
    try:
        from services.web_search_service import WebSearchService
        
        # Initialize with Google preference
        print("\n1. Initializing WebSearchService (prefer Google)...")
        service = WebSearchService(enable_search=True, prefer_google=True)
        
        if not service.is_available():
            print("   ❌ Web search not available")
            return False
        
        print("   ✅ Web search available")
        
        # Check Google status
        if service.google_search:
            quota = service.get_google_quota_status()
            if quota:
                print(f"   Google API: {quota['remaining']} queries remaining")
        
        # Test search
        print("\n2. Testing search...")
        result = service.search("what is boost pressure in turbo tuning", max_results=3)
        if result:
            print(f"   ✅ Found {len(result.results)} results")
            print(f"   Source: {result.results[0].source}")
            for i, r in enumerate(result.results[:2], 1):
                print(f"   {i}. {r.title}")
        else:
            print("   ❌ No results")
        
        # Test specification lookup
        print("\n3. Testing specification lookup...")
        result = service.lookup_specification("Dodge Hellcat fuel pressure")
        if result:
            print(f"   ✅ Found {len(result.results)} results")
            print(f"   Source: {result.results[0].source}")
        else:
            print("   ❌ No results")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback():
    """Test fallback to DuckDuckGo when Google unavailable."""
    print("\n" + "="*60)
    print("Testing Fallback to DuckDuckGo")
    print("="*60)
    
    try:
        from services.web_search_service import WebSearchService
        
        # Initialize without Google (force DuckDuckGo)
        print("\n1. Initializing WebSearchService (DuckDuckGo only)...")
        service = WebSearchService(enable_search=True, prefer_google=False)
        
        if not service.is_available():
            print("   ❌ Web search not available")
            return False
        
        print("   ✅ Web search available")
        
        # Test search
        print("\n2. Testing search (should use DuckDuckGo)...")
        result = service.search("ECU tuning basics", max_results=3)
        if result:
            print(f"   ✅ Found {len(result.results)} results")
            print(f"   Source: {result.results[0].source}")
        else:
            print("   ❌ No results")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Google Search API Integration Tests")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    if not api_key:
        print("\n⚠️  GOOGLE_SEARCH_API_KEY not set")
        print("   Some tests will be skipped")
        print("   Set it with: export GOOGLE_SEARCH_API_KEY=your_key")
    else:
        print(f"\n✅ GOOGLE_SEARCH_API_KEY found: {api_key[:10]}...")
    
    # Check for custom search engine ID
    cx = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    if cx:
        print(f"✅ GOOGLE_SEARCH_ENGINE_ID found: {cx[:10]}...")
    else:
        print("⚠️  GOOGLE_SEARCH_ENGINE_ID not set (custom search disabled)")
    
    # Run tests
    results = []
    
    if api_key:
        results.append(("Google Search Service", test_google_search_service()))
    
    results.append(("WebSearchService Integration", test_web_search_service_integration()))
    results.append(("DuckDuckGo Fallback", test_fallback()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Some tests failed (may be expected if API key not set)")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

