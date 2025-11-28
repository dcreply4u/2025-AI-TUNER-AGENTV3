# Automatic Knowledge Ingestion Setup

## Overview

The automatic knowledge ingestion service runs continuously in the background to:
- **Automatically search** for new knowledge from the internet
- **Ingest documents** about dyno, EFI tuning, Holley EFI, nitrous, turbo tuning
- **Update the knowledge base** without manual intervention
- **Run on a schedule** (default: every 60 minutes)

## How It Works

1. **Starts Automatically**: When the AI advisor initializes, the service starts automatically
2. **Background Thread**: Runs in a daemon thread, doesn't block the main application
3. **Scheduled Ingestion**: Checks every hour (configurable) for new knowledge
4. **Smart Limits**: Limits to 50 ingestions per day to avoid rate limits
5. **Auto-Saves**: All ingested knowledge is automatically saved to the knowledge base

## Configuration

The service is configured in `services/auto_knowledge_ingestion_service.py`:

```python
AutoKnowledgeIngestionService(
    ingestion_interval_minutes=60,  # Check every hour
    max_ingestions_per_day=50,      # Daily limit
    enable_auto_population=True,    # Enable auto-population
)
```

## What Gets Ingested

The service automatically searches for:
- Dyno manuals and calculation guides
- EFI tuning guides and manuals
- Holley EFI documentation
- Nitrous tuning guides
- Turbo tuning guides
- Formula calculations and technical documentation

## Statistics

Statistics are saved to `data/auto_ingestion_stats.json`:
- Total ingestions
- Total chunks added
- Last ingestion time
- Error count
- Start time

## Manual Control

You can manually trigger ingestion:

```python
from services.auto_knowledge_ingestion_service import get_auto_ingestion_service

service = get_auto_ingestion_service()
service.trigger_manual_ingestion("custom search query")
```

## Status Check

Check service status:

```python
from services.auto_knowledge_ingestion_service import get_auto_ingestion_service

service = get_auto_ingestion_service()
stats = service.get_stats()
print(stats)
```

## Integration Points

The service starts automatically when:
1. **AI Advisor Initializes**: `services/ai_advisor_rag.py` starts it during `__init__`
2. **Demo Starts**: `demo_safe.py` starts it during application startup

## No Manual Scripts Needed!

✅ **The service runs automatically** - no need to run `ingest_knowledge_documents.py` manually
✅ **Background operation** - doesn't interfere with application performance
✅ **Self-managing** - handles errors, rate limits, and daily quotas automatically
✅ **Persistent** - continues running as long as the application is running

## Troubleshooting

If the service isn't working:
1. Check logs for errors: `logs/ai_tuner.log`
2. Verify web search is available: `WebSearchService.is_available()`
3. Check statistics file: `data/auto_ingestion_stats.json`
4. Verify imports: All required services must be available

## Disabling

To disable automatic ingestion, comment out the startup code in:
- `services/ai_advisor_rag.py` (line ~283)
- `demo_safe.py` (line ~87)

Or set `enable_auto_population=False` when creating the service.

