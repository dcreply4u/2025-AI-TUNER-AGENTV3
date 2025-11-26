# Google Search API Setup Guide

## Quick Start

### 1. Get Google API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "Custom Search JSON API":
   - Navigate to "APIs & Services" > "Library"
   - Search for "Custom Search JSON API"
   - Click "Enable"
4. Create API Key:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - **Important**: Restrict the key to "Custom Search JSON API" only
   - Copy the API key

### 2. (Optional) Create Custom Search Engine

For better results on tuning forums:

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Add sites to search:
   ```
   bimmerforums.com/*
   gtplanet.net/*
   dragstuff.com/*
   torquecars.com/*
   hptuners.com/*
   ecutek.com/*
   ```
4. Click "Create"
5. Copy the **Search Engine ID (CX)** from the control panel

### 3. Configure in AI Tuner

#### Option A: Environment Variables (Recommended)

Add to your `.env` file or export:
```bash
export GOOGLE_SEARCH_API_KEY=your_api_key_here
export GOOGLE_SEARCH_ENGINE_ID=your_cx_here  # Optional
```

#### Option B: System Environment

**Windows (PowerShell):**
```powershell
$env:GOOGLE_SEARCH_API_KEY="your_api_key_here"
$env:GOOGLE_SEARCH_ENGINE_ID="your_cx_here"
```

**Linux/Mac:**
```bash
export GOOGLE_SEARCH_API_KEY=your_api_key_here
export GOOGLE_SEARCH_ENGINE_ID=your_cx_here
```

### 4. Install Dependencies

```bash
pip install google-api-python-client>=2.100.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 5. Test Installation

```bash
python test_google_search.py
```

## Usage

### Automatic (Recommended)

The `WebSearchService` will automatically use Google API if:
- API key is set
- Google API is available
- Quota not exceeded

No code changes needed! Just set the environment variables.

### Manual Usage

```python
from services.google_search_service import GoogleSearchService

# Initialize
service = GoogleSearchService()

# General search
results = service.search("ECU tuning fuel pressure", max_results=5)

# Custom search (if CX configured)
results = service.search(
    "boost control tuning",
    max_results=5,
    use_custom_search=True
)

# Forum-specific search
results = service.search_forum(
    "fuel pressure",
    "bimmerforums.com",
    max_results=5
)
```

## Cost Management

### Free Tier
- **100 queries per day** = FREE
- Perfect for development and light usage

### Paid Tier
- **$5 per 1,000 queries** after free tier
- Daily limit: 10,000 queries

### Cost Optimization Tips

1. **Caching**: Results are cached for 1 hour (already implemented)
2. **Smart Routing**: Use Google for important queries, DuckDuckGo for general
3. **Custom Search**: Use custom engines for forum searches (better results, same cost)
4. **Monitor Usage**: Check quota status regularly

### Check Quota Status

```python
from services.web_search_service import WebSearchService

service = WebSearchService()
quota = service.get_google_quota_status()
if quota:
    print(f"Remaining: {quota['remaining']}/{quota['daily_limit']}")
```

## Troubleshooting

### "Google Search API not available"
- Check API key is set: `echo $GOOGLE_SEARCH_API_KEY`
- Verify API is enabled in Google Cloud Console
- Check internet connection

### "Quota exceeded"
- Free tier: 100 queries/day (resets at midnight PST)
- Wait for reset or upgrade to paid tier
- System will automatically fallback to DuckDuckGo

### "No results found"
- Check query is valid
- For custom search: Verify sites are indexed by Google
- Try general search instead of custom

### Import Errors
```bash
pip install google-api-python-client
```

## Integration with AI Advisor

The RAG advisor automatically uses Google Search when:
- Local knowledge base has low confidence
- Question is about vehicle specs
- Question needs current/recent information

No changes needed to `ai_advisor_rag.py` - it uses `WebSearchService` which now includes Google API!

## Benefits

✅ **Reliability**: Official API, won't break like scrapers  
✅ **Quality**: Better ranking and relevance  
✅ **Structured Data**: Clean JSON with all metadata  
✅ **Custom Search**: Focus on tuning forums  
✅ **Legal**: Compliant with Google's ToS  
✅ **Free Tier**: 100 queries/day free  

## Fallback Behavior

If Google API is unavailable or quota exceeded:
1. Automatically falls back to DuckDuckGo
2. No errors or crashes
3. Seamless user experience

## Next Steps

1. ✅ Set up API key
2. ✅ (Optional) Create custom search engine
3. ✅ Test with `test_google_search.py`
4. ✅ Monitor usage and costs
5. ✅ Enjoy better search results!

