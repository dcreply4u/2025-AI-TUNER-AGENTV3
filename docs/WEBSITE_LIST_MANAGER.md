# Website List Manager

## Overview

The Website List Manager allows you to maintain a curated list of websites that the AI advisor can ingest or reference. This makes it easy to manage sources of knowledge without hardcoding URLs.

## Features

- ✅ **Add/Remove Websites**: Manage your website list
- ✅ **Categorization**: Organize websites by category (forum, documentation, blog, etc.)
- ✅ **Enable/Disable**: Control which websites are ingested
- ✅ **Tracking**: Track ingestion history and chunk counts
- ✅ **Default Websites**: Pre-populated with popular tuning forums

## Default Websites

The system comes with these default websites pre-configured:

1. **Xtreme Racing Tuning Forum** - `https://www.xtremeracingtuning.com/forum/`
2. **HP Academy Forum** - `https://www.hpacademy.com/forum/`
3. **HP Tuners Forum** - `https://forum.hptuners.com/`
4. **JB4 Tech** - `https://www.jb4tech.com/`
5. **RC Tech Forum** - `https://www.rctech.net/forum/`

## Usage

### Command Line Interface

```bash
# List all websites
python3 manage_websites.py list

# List only enabled websites
python3 manage_websites.py list --enabled-only

# Add a website
python3 manage_websites.py add "https://example.com/forum" "Example Forum" --description "Tuning forum" --category "forum"

# Remove a website
python3 manage_websites.py remove "https://example.com/forum"

# Show statistics
python3 manage_websites.py stats

# Ingest all enabled websites
python3 manage_websites.py ingest

# Ingest all websites (including disabled)
python3 manage_websites.py ingest --all
```

### From Python Code

```python
from services.ai_advisor_rag import RAGAIAdvisor

advisor = RAGAIAdvisor()

# Add a website to the list
advisor.add_website_to_list(
    url="https://example.com/forum",
    name="Example Forum",
    description="Tuning forum",
    category="forum"
)

# Remove a website
advisor.remove_website_from_list("https://example.com/forum")

# Get website list
websites = advisor.get_website_list(enabled_only=True)
for site in websites:
    print(f"{site['name']}: {site['url']}")

# Ingest all websites from list
result = advisor.ingest_websites_from_list(enabled_only=True)
print(f"Ingested {result['successful']} websites")

# Get statistics
stats = advisor.get_website_list_stats()
print(f"Total websites: {stats['total_websites']}")
```

## API Methods

### `add_website_to_list(url, name, description="", category="forum", metadata=None)`

Add a website to the list.

**Returns:** `{"success": bool, "message": str}`

### `remove_website_from_list(url)`

Remove a website from the list.

**Returns:** `{"success": bool, "message": str}`

### `get_website_list(enabled_only=False, category=None)`

Get list of websites.

**Returns:** List of website dictionaries

### `ingest_websites_from_list(enabled_only=True, category=None)`

Ingest all websites from the list.

**Returns:** Summary dictionary with:
- `total`: Total websites processed
- `successful`: Successfully ingested
- `failed`: Failed to ingest
- `total_chunks`: Total chunks added
- `details`: Per-website details

### `get_website_list_stats()`

Get website list statistics.

**Returns:** Statistics dictionary

## Storage

Website list is stored in: `~/.aituner/website_list.json`

Format:
```json
{
  "https://example.com/forum": {
    "url": "https://example.com/forum",
    "name": "Example Forum",
    "description": "Tuning forum",
    "category": "forum",
    "enabled": true,
    "last_ingested": 1234567890.0,
    "ingest_count": 1,
    "chunks_added": 150,
    "added_at": 1234567890.0,
    "metadata": {}
  }
}
```

## Testing

Run the test script to verify everything works:

```bash
python3 test_website_ingestion.py
```

This will:
1. Show the website list
2. Test ingestion (optional)
3. Test search functionality

## Best Practices

1. **Use Descriptive Names**: Give websites clear, descriptive names
2. **Categorize Properly**: Use consistent categories (forum, documentation, blog)
3. **Enable/Disable**: Disable websites that are no longer relevant
4. **Regular Updates**: Periodically re-ingest websites to get fresh content
5. **Monitor Stats**: Check statistics to see which websites are most useful

## Troubleshooting

**Website not ingesting:**
- Check if website is enabled
- Verify URL is accessible
- Check logs for specific errors

**Search not finding content:**
- Ensure websites have been ingested
- Check knowledge base stats: `advisor.get_knowledge_base_stats()`
- Verify search query matches content

**CLI command not found:**
- Ensure you're in the project directory
- Check file permissions: `chmod +x manage_websites.py`

