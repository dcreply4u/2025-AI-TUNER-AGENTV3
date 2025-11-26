# Knowledge Base Manager

## Overview

The Knowledge Base Manager allows you to populate the AI advisor's knowledge base with:
- **Documents** (PDF, TXT, DOCX, JSON)
- **Websites** (scrape and index web pages)
- **Forum Posts** (search forums and index relevant posts)

## Features

### 1. Document Ingestion

Supports multiple file formats:
- **PDF**: Extracts text from PDF documents
- **DOCX**: Extracts text and tables from Word documents
- **TXT/MD**: Plain text and Markdown files
- **JSON**: Structured data files

Documents are automatically split into chunks (max 1000 chars) with overlap for better context.

### 2. Web Scraping

Scrapes websites and extracts:
- Main content text
- Removes navigation, scripts, and styles
- Splits into searchable chunks
- Preserves metadata (URL, domain, timestamp)

### 3. Forum Search

Searches forums for relevant posts:
- Supports common forum patterns (phpBB, vBulletin, etc.)
- Extracts post content
- Adds search query as metadata
- Limits results to prevent overload

## Usage

### From Python Code

```python
from services.ai_advisor_rag import RAGAIAdvisor

# Initialize advisor
advisor = RAGAIAdvisor()

# Add a document
result = advisor.add_document(
    "/path/to/manual.pdf",
    metadata={"topic": "ECU Tuning", "author": "John Doe"}
)
print(f"Added {result['chunks_added']} chunks")

# Add a website
result = advisor.add_website(
    "https://example.com/tuning-guide",
    metadata={"topic": "Tuning Guide"}
)
print(f"Added {result['chunks_added']} chunks")

# Search a forum
result = advisor.search_forum(
    "https://forum.example.com",
    "fuel pressure tuning",
    max_posts=10
)
print(f"Added {result['posts_added']} posts")

# Get statistics
stats = advisor.get_knowledge_base_stats()
print(f"Total entries: {stats['total_entries']}")
```

### From Command Line

```bash
# Test the knowledge base manager
python3 test_knowledge_base.py
```

## API Methods

### `add_document(file_path, metadata=None)`

Add a document to the knowledge base.

**Parameters:**
- `file_path` (str): Path to document file
- `metadata` (dict, optional): Additional metadata

**Returns:**
- `dict`: Result with `success`, `chunks_added`, and `errors`

**Example:**
```python
result = advisor.add_document("tuning_manual.pdf")
```

### `add_website(url, metadata=None)`

Scrape and add a website to the knowledge base.

**Parameters:**
- `url` (str): URL to scrape
- `metadata` (dict, optional): Additional metadata

**Returns:**
- `dict`: Result with `success`, `chunks_added`, and `errors`

**Example:**
```python
result = advisor.add_website("https://example.com/guide")
```

### `search_forum(forum_url, search_query, max_posts=10)`

Search a forum and add results to knowledge base.

**Parameters:**
- `forum_url` (str): Base URL of forum
- `search_query` (str): Search query
- `max_posts` (int): Maximum posts to retrieve

**Returns:**
- `dict`: Result with `success`, `posts_added`, and `errors`

**Example:**
```python
result = advisor.search_forum(
    "https://forum.example.com",
    "boost control",
    max_posts=5
)
```

### `get_knowledge_base_stats()`

Get knowledge base statistics.

**Returns:**
- `dict`: Statistics including `total_entries`

**Example:**
```python
stats = advisor.get_knowledge_base_stats()
```

## Dependencies

Required packages:
- `PyPDF2>=3.0.0` - PDF parsing
- `python-docx>=1.0.0` - DOCX parsing
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - XML/HTML parser
- `requests` - HTTP requests (already in requirements)

Install with:
```bash
pip install PyPDF2 python-docx beautifulsoup4 lxml
```

## Architecture

```
KnowledgeBaseManager
    ├── DocumentIngester
    │   ├── PDF Parser
    │   ├── DOCX Parser
    │   ├── Text Parser
    │   └── JSON Parser
    ├── WebScraper
    │   ├── URL Scraper
    │   └── Forum Search
    └── VectorKnowledgeStore
        └── ChromaDB
```

## Best Practices

1. **Document Metadata**: Always provide meaningful metadata (topic, author, date) for better searchability

2. **Forum URLs**: Use the base forum URL, not individual post URLs

3. **Chunk Size**: Documents are automatically chunked (1000 chars) with overlap (200 chars) for context

4. **Error Handling**: Always check the `success` field and handle `errors` appropriately

5. **Rate Limiting**: Be respectful when scraping websites - add delays between requests if needed

## Examples

### Add ECU Tuning Manual
```python
advisor.add_document(
    "ecu_tuning_manual.pdf",
    metadata={
        "topic": "ECU Tuning",
        "type": "manual",
        "vehicle": "Dodge Challenger"
    }
)
```

### Scrape Tuning Forum
```python
advisor.search_forum(
    "https://www.hptuners.com/forum",
    "hellcat supercharger",
    max_posts=20
)
```

### Add Multiple Documents
```python
documents = [
    "tuning_basics.pdf",
    "advanced_tuning.docx",
    "troubleshooting.txt"
]

for doc in documents:
    result = advisor.add_document(doc)
    print(f"{doc}: {result['chunks_added']} chunks")
```

## Troubleshooting

**PDF parsing fails:**
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Check if PDF is encrypted or corrupted

**Web scraping fails:**
- Check internet connection
- Verify URL is accessible
- Some sites block scrapers - may need headers/cookies

**Forum search returns 0 posts:**
- Forum may use non-standard search patterns
- Try different forum URL formats
- Check if forum requires authentication

## Future Enhancements

- [ ] Support for more document formats (EPUB, RTF, etc.)
- [ ] Automatic forum pattern detection
- [ ] Caching of scraped content
- [ ] Scheduled updates for websites
- [ ] Content deduplication
- [ ] Image OCR for scanned documents

