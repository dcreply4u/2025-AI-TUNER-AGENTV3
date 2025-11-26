# Auto Knowledge Population

## Overview

The Auto Knowledge Populator is an intelligent system that **automatically populates the knowledge base** when it detects gaps or low confidence answers. This creates a self-improving AI advisor that learns and expands its knowledge autonomously.

## How It Works

### Detection Phase
1. **Low Confidence Detection**: When an answer has confidence < 0.5
2. **Gap Frequency Check**: Only acts on recurring gaps (2+ occurrences by default)
3. **Knowledge Gap Identification**: Uses the learning system to identify patterns

### Population Phase
1. **Forum Search**: Searches enabled forums from the website list
2. **Web Search**: Falls back to general web search if forums don't yield results
3. **Knowledge Addition**: Automatically adds found information to the vector store
4. **Tracking**: Records success/failure for learning

## Features

✅ **Automatic**: No manual intervention required
✅ **Intelligent**: Only populates for recurring gaps
✅ **Multi-Source**: Tries forums first, then web search
✅ **Safe**: Respects thresholds and limits
✅ **Trackable**: Full logging and statistics

## Configuration

```python
auto_populator = AutoKnowledgePopulator(
    learning_system=learning_system,
    website_ingestion_service=website_ingestion_service,
    knowledge_base_manager=knowledge_base_manager,
    web_search_service=web_search_service,
    auto_populate_enabled=True,      # Enable/disable
    confidence_threshold=0.5,        # Trigger below this confidence
    min_gap_frequency=2              # Minimum gap occurrences
)
```

## Example Flow

```
User asks: "how do I tune fuel pressure for turbo"
    ↓
Advisor answers with confidence: 0.30 (low)
    ↓
Auto-populator detects low confidence
    ↓
Checks gap frequency: 1st occurrence (skip)
    ↓
User asks same question again
    ↓
Advisor answers with confidence: 0.30 (low)
    ↓
Auto-populator detects: 2nd occurrence (threshold met)
    ↓
Searches forums: HP Tuners, Xtreme Racing, etc.
    ↓
Finds relevant posts
    ↓
Adds to knowledge base: 15 chunks
    ↓
Next time user asks: Confidence 0.75! ✓
```

## Statistics

Get auto-population stats:

```python
stats = advisor.auto_populator.get_stats()
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Success Rate: {stats['success_rate']:.1%}")
```

## Benefits

1. **Self-Improving**: System gets smarter over time
2. **Automatic**: No manual knowledge base updates needed
3. **Targeted**: Only fills actual gaps, not random content
4. **Efficient**: Uses existing forum/web infrastructure
5. **Safe**: Multiple safeguards prevent spam/errors

## Limitations & Considerations

### Current Limitations
- Requires 2+ occurrences before auto-populating (prevents one-off gaps)
- Limited to enabled forums in website list
- Web search may find less relevant content than forums
- Some forums may require authentication

### Best Practices
1. **Ingest Websites First**: Run `manage_websites.py ingest` to populate initial knowledge
2. **Monitor Stats**: Check auto-population success rate
3. **Review Gaps**: Periodically review knowledge gaps
4. **Adjust Thresholds**: Tune `confidence_threshold` and `min_gap_frequency` as needed

## Integration

The auto-populator is **automatically integrated** into the RAG advisor. It runs after every low-confidence answer.

To enable/disable:
```python
advisor.auto_populator.auto_populate_enabled = True/False
```

## Future Enhancements

- [ ] User feedback integration (auto-populate on negative feedback)
- [ ] Scheduled background population
- [ ] Quality scoring for auto-populated content
- [ ] Deduplication of similar content
- [ ] Multi-language support
- [ ] Content expiration/refresh

## Is This "Too Much"?

**Not at all!** This is actually a **best practice** in modern AI systems:

1. **Active Learning**: Standard technique in ML/AI
2. **RAG Enhancement**: Common pattern for improving RAG systems
3. **Self-Healing**: Makes the system more robust
4. **Scalable**: Grows knowledge base organically

The safeguards (frequency threshold, confidence check) ensure it's **safe and targeted**, not random or spammy.

## Testing

Test the auto-populator:

```python
# Ask a question that's not in knowledge base
response = advisor.answer("how to tune fuel pressure for turbo")
print(f"Confidence: {response.confidence}")

# Ask again (triggers auto-population on 2nd occurrence)
response = advisor.answer("how to tune fuel pressure for turbo")
print(f"Confidence: {response.confidence}")  # Should be higher!

# Check stats
stats = advisor.auto_populator.get_stats()
print(stats)
```

