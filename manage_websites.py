#!/usr/bin/env python3
"""
Website List Manager CLI
Command-line tool to manage the website list.
"""

import sys
import argparse
from services.website_list_manager import WebsiteListManager
from services.ai_advisor_rag import RAGAIAdvisor

def list_websites(manager: WebsiteListManager, enabled_only: bool = False):
    """List all websites."""
    websites = manager.get_websites(enabled_only=enabled_only)
    
    if not websites:
        print("No websites in list.")
        return
    
    print(f"\n{'='*70}")
    print(f"Website List ({len(websites)} websites)")
    print(f"{'='*70}\n")
    
    for i, site in enumerate(websites, 1):
        status = "✓" if site.enabled else "✗"
        print(f"{i}. {status} {site.name}")
        print(f"   URL: {site.url}")
        print(f"   Category: {site.category}")
        print(f"   Description: {site.description}")
        print(f"   Chunks: {site.chunks_added}")
        print(f"   Ingested: {site.ingest_count} times")
        if site.last_ingested:
            from datetime import datetime
            last = datetime.fromtimestamp(site.last_ingested).strftime("%Y-%m-%d %H:%M")
            print(f"   Last ingested: {last}")
        print()


def add_website(manager: WebsiteListManager, url: str, name: str, description: str = "", category: str = "forum"):
    """Add a website."""
    success = manager.add_website(url, name, description, category)
    if success:
        print(f"✓ Added website: {name}")
    else:
        print(f"✗ Website already exists: {url}")


def remove_website(manager: WebsiteListManager, url: str):
    """Remove a website."""
    success = manager.remove_website(url)
    if success:
        print(f"✓ Removed website: {url}")
    else:
        print(f"✗ Website not found: {url}")


def show_stats(manager: WebsiteListManager):
    """Show statistics."""
    stats = manager.get_stats()
    print(f"\n{'='*70}")
    print("Website List Statistics")
    print(f"{'='*70}\n")
    print(f"Total websites: {stats['total_websites']}")
    print(f"Enabled: {stats['enabled_websites']}")
    print(f"Categories: {stats['categories']}")
    print(f"Total chunks added: {stats['total_chunks_added']}")
    print(f"Websites ingested: {stats['websites_ingested']}")


def ingest_websites(advisor: RAGAIAdvisor, enabled_only: bool = True):
    """Ingest websites from list."""
    print("\n" + "="*70)
    print("Ingesting Websites from List")
    print("="*70 + "\n")
    
    result = advisor.ingest_websites_from_list(enabled_only=enabled_only)
    
    if "error" in result:
        print(f"✗ Error: {result['error']}")
        return
    
    print(f"\nIngestion Summary:")
    print(f"  Total websites: {result['total']}")
    print(f"  Successful: {result['successful']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Total chunks: {result['total_chunks']}")
    
    if result['details']:
        print(f"\nDetails:")
        for detail in result['details']:
            status = "✓" if detail['status'] == 'success' else "✗"
            print(f"  {status} {detail['name']}")
            if detail['status'] == 'success':
                print(f"    Chunks: {detail.get('chunks', 0)}")
            else:
                errors = detail.get('errors', detail.get('error', 'Unknown error'))
                print(f"    Error: {errors}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Manage website list for AI advisor")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all websites')
    list_parser.add_argument('--enabled-only', action='store_true', help='Only show enabled websites')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a website')
    add_parser.add_argument('url', help='Website URL')
    add_parser.add_argument('name', help='Website name')
    add_parser.add_argument('--description', default='', help='Description')
    add_parser.add_argument('--category', default='forum', help='Category (forum, documentation, blog)')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a website')
    remove_parser.add_argument('url', help='Website URL to remove')
    
    # Stats command
    subparsers.add_parser('stats', help='Show statistics')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest websites from list')
    ingest_parser.add_argument('--all', action='store_true', help='Ingest all websites (including disabled)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = WebsiteListManager()
    
    if args.command == 'list':
        list_websites(manager, enabled_only=args.enabled_only)
    elif args.command == 'add':
        add_website(manager, args.url, args.name, args.description, args.category)
    elif args.command == 'remove':
        remove_website(manager, args.url)
    elif args.command == 'stats':
        show_stats(manager)
    elif args.command == 'ingest':
        advisor = RAGAIAdvisor()
        ingest_websites(advisor, enabled_only=not args.all)


if __name__ == "__main__":
    main()

