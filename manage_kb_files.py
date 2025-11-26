#!/usr/bin/env python3
"""
Knowledge Base File Manager CLI

Allows users to review, edit, and manage KB files that the AI advisor learns.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.knowledge_base_file_manager import KnowledgeBaseFileManager, KBEntry


def print_entry(entry: KBEntry, index: int = None):
    """Print a KB entry."""
    prefix = f"{index}. " if index is not None else ""
    verified = "✓" if entry.verified else "○"
    edited = "✎" if entry.user_edited else ""
    
    print(f"\n{prefix}{verified} {edited} Q: {entry.question}")
    print(f"   A: {entry.answer[:200]}...")
    print(f"   Topic: {entry.topic} | Source: {entry.source} | Confidence: {entry.confidence:.2f}")
    if entry.url:
        print(f"   URL: {entry.url}")
    if entry.keywords:
        print(f"   Keywords: {', '.join(entry.keywords[:5])}")


def list_entries(kb_manager: KnowledgeBaseFileManager, topic: str = None):
    """List all entries."""
    if topic:
        entries = kb_manager.get_entries_by_topic(topic)
        print(f"\n=== Entries in '{topic}' ===")
    else:
        entries = list(kb_manager.entries.values())
        print(f"\n=== All Entries ({len(entries)}) ===")
    
    if not entries:
        print("No entries found.")
        return
    
    for i, entry in enumerate(entries, 1):
        print_entry(entry, i)


def search_entries(kb_manager: KnowledgeBaseFileManager, query: str):
    """Search entries."""
    results = kb_manager.search_entries(query)
    print(f"\n=== Search Results for '{query}' ({len(results)}) ===")
    
    if not results:
        print("No results found.")
        return
    
    for i, entry in enumerate(results, 1):
        print_entry(entry, i)


def show_stats(kb_manager: KnowledgeBaseFileManager):
    """Show KB statistics."""
    stats = kb_manager.get_stats()
    print("\n=== Knowledge Base Statistics ===")
    print(f"Total Entries: {stats['total_entries']}")
    print(f"Topics: {stats['topics']}")
    print(f"Verified: {stats['verified_entries']}")
    print(f"User Edited: {stats['user_edited_entries']}")
    print(f"\nBy Source:")
    for source, count in stats['entries_by_source'].items():
        print(f"  {source}: {count}")
    print(f"\nBy Topic:")
    for topic, count in stats['entries_by_topic'].items():
        print(f"  {topic}: {count}")


def verify_entry(kb_manager: KnowledgeBaseFileManager, question: str):
    """Verify an entry."""
    if kb_manager.verify_entry(question, verified=True):
        print(f"✓ Verified entry: {question[:50]}...")
    else:
        print(f"✗ Entry not found: {question[:50]}...")


def edit_entry(kb_manager: KnowledgeBaseFileManager, question: str, answer: str = None, topic: str = None):
    """Edit an entry."""
    if kb_manager.edit_entry(question, answer=answer, topic=topic):
        print(f"✓ Updated entry: {question[:50]}...")
    else:
        print(f"✗ Entry not found: {question[:50]}...")


def delete_entry(kb_manager: KnowledgeBaseFileManager, question: str):
    """Delete an entry."""
    if kb_manager.delete_entry(question):
        print(f"✓ Deleted entry: {question[:50]}...")
    else:
        print(f"✗ Entry not found: {question[:50]}...")


def export_to_json(kb_manager: KnowledgeBaseFileManager, output_file: str):
    """Export all entries to JSON."""
    data = {
        "entries": [entry.__dict__ for entry in kb_manager.entries.values()],
        "topics": kb_manager.get_all_topics(),
        "stats": kb_manager.get_stats()
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Exported {len(kb_manager.entries)} entries to {output_file}")


def main():
    """Main CLI."""
    kb_manager = KnowledgeBaseFileManager()
    
    if len(sys.argv) < 2:
        print("""
Knowledge Base File Manager

Usage:
  python manage_kb_files.py <command> [args...]

Commands:
  list [topic]              - List all entries (optionally by topic)
  search <query>             - Search entries
  stats                      - Show statistics
  verify <question>          - Verify an entry
  edit <question> [answer]   - Edit an entry
  delete <question>          - Delete an entry
  export <file.json>        - Export all entries to JSON
  topics                     - List all topics

Examples:
  python manage_kb_files.py list
  python manage_kb_files.py list "ECU Tuning"
  python manage_kb_files.py search "fuel pressure"
  python manage_kb_files.py stats
  python manage_kb_files.py verify "what is fuel pressure"
  python manage_kb_files.py edit "what is fuel pressure" "Fuel pressure is..."
  python manage_kb_files.py delete "what is fuel pressure"
  python manage_kb_files.py export kb_backup.json
  python manage_kb_files.py topics
        """)
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "list":
            topic = sys.argv[2] if len(sys.argv) > 2 else None
            list_entries(kb_manager, topic)
        
        elif command == "search":
            if len(sys.argv) < 3:
                print("Error: Please provide a search query")
                return
            query = " ".join(sys.argv[2:])
            search_entries(kb_manager, query)
        
        elif command == "stats":
            show_stats(kb_manager)
        
        elif command == "verify":
            if len(sys.argv) < 3:
                print("Error: Please provide a question")
                return
            question = " ".join(sys.argv[2:])
            verify_entry(kb_manager, question)
        
        elif command == "edit":
            if len(sys.argv) < 3:
                print("Error: Please provide a question")
                return
            question = " ".join(sys.argv[2:-1]) if len(sys.argv) > 3 else sys.argv[2]
            answer = sys.argv[-1] if len(sys.argv) > 3 else None
            edit_entry(kb_manager, question, answer=answer)
        
        elif command == "delete":
            if len(sys.argv) < 3:
                print("Error: Please provide a question")
                return
            question = " ".join(sys.argv[2:])
            delete_entry(kb_manager, question)
        
        elif command == "export":
            if len(sys.argv) < 3:
                print("Error: Please provide output file")
                return
            export_to_json(kb_manager, sys.argv[2])
        
        elif command == "topics":
            topics = kb_manager.get_all_topics()
            print("\n=== Topics ===")
            for topic in topics:
                count = len(kb_manager.get_entries_by_topic(topic))
                print(f"  {topic}: {count} entries")
        
        else:
            print(f"Unknown command: {command}")
            print("Run without arguments to see usage.")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

