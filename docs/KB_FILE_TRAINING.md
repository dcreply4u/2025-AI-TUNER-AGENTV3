# Knowledge Base File Training System

## Overview

The AI advisor can now **automatically learn** from questions it doesn't know! When asked a question with low confidence, it will:

1. 🔍 **Search the web** for information
2. 💾 **Save to KB files** (human-readable JSON)
3. 📚 **Add to vector store** for future searches
4. ✅ **Let you review/edit** the learned knowledge

## How It Works

### Automatic Learning Flow

```
User asks question
    ↓
AI checks knowledge base
    ↓
Low confidence? (< 0.5)
    ↓
Auto-populator searches web/forums
    ↓
Finds information
    ↓
Saves to KB file (~/.aituner/kb/topic.json)
    ↓
Adds to vector store
    ↓
Next time: AI knows the answer!
```

### KB File Structure

KB files are saved as JSON in `~/.aituner/kb/` organized by topic:

```
~/.aituner/kb/
  ├── ecu_tuning.json
  ├── fuel_system.json
  ├── boost_control.json
  ├── general.json
  └── ...
```

Each file contains:
```json
{
  "topic": "ECU Tuning",
  "updated_at": "2025-01-15T10:30:00",
  "entries": [
    {
      "question": "what is fuel pressure",
      "answer": "Fuel pressure is...",
      "source": "auto_populate",
      "url": "https://...",
      "title": "Fuel Pressure Guide",
      "confidence": 0.7,
      "keywords": ["fuel", "pressure", "tuning"],
      "topic": "Fuel System",
      "verified": false,
      "user_edited": false,
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:30:00"
    }
  ]
}
```

## Training the AI

### Method 1: Ask Questions (Automatic)

Just ask questions the AI doesn't know:

```
You: "what is the optimal fuel pressure for a turbocharged engine?"
AI: [Low confidence, searches web, learns, saves to KB file]
AI: "Based on my research, optimal fuel pressure for turbocharged engines..."
AI: "💡 I've learned about this topic and saved it for future reference."
```

The AI automatically:
- ✅ Searches the web
- ✅ Saves to KB file
- ✅ Adds to knowledge base
- ✅ Will know it next time!

### Method 2: Review and Edit KB Files

1. **List learned entries:**
   ```bash
   python manage_kb_files.py list
   ```

2. **Search for specific topics:**
   ```bash
   python manage_kb_files.py search "fuel pressure"
   ```

3. **Edit an entry:**
   ```bash
   python manage_kb_files.py edit "what is fuel pressure" "Fuel pressure is the force..."
   ```

4. **Verify correct entries:**
   ```bash
   python manage_kb_files.py verify "what is fuel pressure"
   ```

5. **Delete incorrect entries:**
   ```bash
   python manage_kb_files.py delete "what is fuel pressure"
   ```

### Method 3: Direct File Editing

You can directly edit KB files:

1. Navigate to `~/.aituner/kb/`
2. Open a topic file (e.g., `fuel_system.json`)
3. Edit entries as needed
4. Save the file
5. The AI will use your edits next time!

## KB File Manager CLI

### Commands

```bash
# List all entries
python manage_kb_files.py list

# List entries by topic
python manage_kb_files.py list "ECU Tuning"

# Search entries
python manage_kb_files.py search "fuel pressure"

# Show statistics
python manage_kb_files.py stats

# Verify an entry (mark as correct)
python manage_kb_files.py verify "what is fuel pressure"

# Edit an entry
python manage_kb_files.py edit "what is fuel pressure" "New answer here..."

# Delete an entry
python manage_kb_files.py delete "what is fuel pressure"

# Export all entries
python manage_kb_files.py export kb_backup.json

# List all topics
python manage_kb_files.py topics
```

## Training Workflow

### Recommended Workflow

1. **Ask questions** the AI doesn't know
2. **AI learns automatically** and saves to KB files
3. **Review KB files** periodically:
   ```bash
   python manage_kb_files.py list
   ```
4. **Verify correct entries:**
   ```bash
   python manage_kb_files.py verify "question"
   ```
5. **Edit incorrect entries:**
   ```bash
   python manage_kb_files.py edit "question" "correct answer"
   ```
6. **Delete bad entries:**
   ```bash
   python manage_kb_files.py delete "question"
   ```

### Quality Control

- ✅ **Verify** entries you know are correct
- ✎ **Edit** entries that need improvement
- ❌ **Delete** entries that are wrong
- 📊 **Check stats** regularly to see what's been learned

## Integration with Vector Store

KB files are automatically synced with the vector store:

- When entries are added to KB files → Added to vector store
- When entries are edited → Updated in vector store
- When entries are deleted → Removed from vector store

The AI searches both:
1. **Vector store** (for semantic search)
2. **KB files** (for exact question matches)

## Benefits

✅ **Automatic Learning**: AI learns from questions it doesn't know  
✅ **Human Reviewable**: KB files are human-readable JSON  
✅ **User Trainable**: You can edit/verify/delete entries  
✅ **Persistent**: Knowledge is saved and persists across sessions  
✅ **Organized**: Entries organized by topic  
✅ **Traceable**: Each entry has source, URL, confidence, etc.  

## Example Training Session

```
You: "what is the best AFR for turbocharged engines?"
AI: [Low confidence, searches web]
AI: "The optimal AFR for turbocharged engines is typically 11.5-12.5:1..."
AI: "💡 I've learned about this topic and saved it for future reference."

[Later...]

You: "what is the best AFR for turbocharged engines?"
AI: "The optimal AFR for turbocharged engines is typically 11.5-12.5:1..."
[High confidence, from KB file!]

[You review KB file]
python manage_kb_files.py list
# See the entry, verify it's correct
python manage_kb_files.py verify "what is the best AFR for turbocharged engines"
```

## Tips

1. **Ask specific questions** - Better for learning
2. **Review KB files regularly** - Ensure quality
3. **Verify correct entries** - Helps AI prioritize
4. **Edit incorrect entries** - Train the AI properly
5. **Delete bad entries** - Keep knowledge base clean

## File Locations

- **KB Files**: `~/.aituner/kb/`
- **Vector Store**: `~/.aituner/vector_db/`
- **Learning Data**: `~/.aituner/learning/`

## Summary

The AI advisor now **learns automatically** from questions it doesn't know! It:
- 🔍 Searches web/forums
- 💾 Saves to human-readable KB files
- 📚 Adds to vector store
- ✅ Lets you review/edit/verify

**You can train it by asking questions and reviewing the KB files!**

