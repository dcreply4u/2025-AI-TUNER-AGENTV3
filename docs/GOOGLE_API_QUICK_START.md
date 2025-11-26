# Google Search API - Quick Start (When Ready)

## ⚡ Quick Setup (5 minutes)

### Step 1: Get API Key
1. Go to: https://console.cloud.google.com/
2. Create/select project
3. Enable "Custom Search JSON API"
4. Create API Key → Restrict to "Custom Search JSON API"
5. Copy the key

### Step 2: Set Environment Variable

**Windows PowerShell:**
```powershell
$env:GOOGLE_SEARCH_API_KEY="your_key_here"
```

**Or add to `.env` file:**
```
GOOGLE_SEARCH_API_KEY=your_key_here
```

### Step 3: Install Dependency
```bash
pip install google-api-python-client
```

### Step 4: Test
```bash
python test_google_search.py
```

## ✅ That's It!

The AI advisor will automatically use Google API once the key is set. No code changes needed!

## 📝 Optional: Custom Search Engine

For better results on tuning forums:
1. Go to: https://programmablesearchengine.google.com/
2. Create search engine
3. Add sites: `bimmerforums.com/*`, `gtplanet.net/*`, etc.
4. Get Search Engine ID (CX)
5. Set: `GOOGLE_SEARCH_ENGINE_ID=your_cx_here`

## 💡 Until Then

The system will automatically use DuckDuckGo (free, unlimited) as a fallback. Everything works, just without the premium Google results.

