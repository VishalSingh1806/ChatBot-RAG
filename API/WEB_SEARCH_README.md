# Web Search Integration for Real-Time EPR Data

## 🎯 Overview

This implementation adds **real-time web search capabilities** to detect and answer time-sensitive queries (deadlines, latest updates, current notifications) with up-to-date information.

## ✅ What's Implemented (Phase 1)

### 1. **Intelligent Query Detection**
- Automatically detects time-sensitive queries:
  - Deadline-related keywords: "deadline", "last date", "due date", "extended"
  - Temporal keywords: "latest", "current", "recent", "new", "this year"
  - Year mentions: "2024-25", "2025-26", etc.
  - Filing context: "annual return", "filing", "submit"

### 2. **Hybrid Search Enhancement**
- **Normal queries**: 60% LLM + 40% Database (existing behavior)
- **Time-sensitive queries**: Web Search + Database (prioritizes real-time data)
- Automatic fallback if web search fails

### 3. **Files Created**
- `web_search_integration.py` - Core web search module
- `test_web_search.py` - Testing script for query detection
- Updated `hybrid_search.py` - Integrated web search logic
- Updated `.env` - Added search configuration

### 4. **Configuration**
```env
SEARCH_MODE=hybrid              # Enable hybrid search
WEB_SEARCH_ENABLED=true         # Enable web search for time-sensitive queries
```

## 🔍 How It Works

```
User Query: "What is the deadline for EPR filing 2024-25?"
     ↓
[1] Deadline Detection
     ↓ (✅ Time-sensitive detected)
     ↓
[2] Database Search (ChromaDB)
     ↓
[3] Web Search (Gemini with latest knowledge)
     ↓
[4] Intelligent Combination
     ↓ (Prioritizes web results for dates)
     ↓
[5] Final Answer with latest deadlines
```

## ⚠️ Important Limitation (Current Phase)

**The current implementation uses Gemini LLM's knowledge (Jan 2025 cutoff) rather than live web scraping.**

This means:
- ✅ More current than old database (up to Jan 2025)
- ✅ Detection and routing logic working
- ❌ NOT truly real-time (no live web search yet)
- ❌ Won't have updates after Jan 2025

## 🚀 Next Steps - True Real-Time Search (Phase 2)

To achieve **actual real-time web search**, integrate one of these:

### Option A: Google Programmable Search Engine (Recommended)
```python
# Add to requirements.txt
google-api-python-client

# Setup in web_search_integration.py
from googleapiclient.discovery import build

service = build("customsearch", "v1", developerKey=API_KEY)
result = service.cse().list(
    q=query,
    cx=SEARCH_ENGINE_ID,
    siteSearch="cpcb.nic.in"  # Prioritize CPCB
).execute()
```

**Cost**: 100 free searches/day, then $5/1000 queries

### Option B: SerpAPI (Easiest)
```python
# Add to requirements.txt
google-search-results

# Setup
from serpapi import GoogleSearch
params = {
    "q": query,
    "location": "India",
    "api_key": SERPAPI_KEY
}
results = GoogleSearch(params).get_dict()
```

**Cost**: 100 free searches/month, then $50/5000 searches

### Option C: Web Scraping CPCB (Free but fragile)
```python
import requests
from bs4 import BeautifulSoup

# Scrape CPCB notifications page
url = "https://cpcb.nic.in/latest-notifications/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
# Extract latest notifications
```

**Pros**: Free
**Cons**: Breaks if website changes, may violate ToS

## 📝 Testing

Run the test script to verify detection:
```bash
cd /mnt/d/AI-ChatBot/API
python test_web_search.py
```

**Expected Output**:
```
✅ TIME-SENSITIVE: What is the last date for annual report filing?
✅ TIME-SENSITIVE: When is the deadline for EPR filing 2024-25?
❌ NOT TIME-SENSITIVE: Tell me about EPR compliance
```

## 🔧 Configuration Options

### Enable/Disable Web Search
```env
WEB_SEARCH_ENABLED=true   # Use web search for time-sensitive queries
WEB_SEARCH_ENABLED=false  # Disable (fall back to normal hybrid)
```

### Adjust Search Mode
```env
SEARCH_MODE=hybrid         # Hybrid with web search support
SEARCH_MODE=traditional    # Old mode (no web search)
```

## 📊 Performance Impact

- **Time-sensitive queries**: +1-2 seconds (web search)
- **Normal queries**: No change (same speed)
- **Fallback**: Automatic if web search fails

## 🎯 Key Benefits

1. **Accurate Deadlines**: Latest CPCB notification dates
2. **No Manual Updates**: Reduces need to update ChromaDB
3. **User Trust**: Current information builds credibility
4. **Smart Routing**: Only uses web search when needed

## 📌 Recommendations

### For Production Deployment:

1. **Add Real Web Search** (Option A or B above)
2. **Monitor Usage**: Track web search API costs
3. **Cache Results**: Store recent deadline searches (24hr TTL)
4. **Error Handling**: Graceful fallback if API limits reached
5. **Logging**: Track which queries use web search

### Sample Implementation (Google Custom Search):

```python
# In web_search_integration.py

import os
from googleapiclient.discovery import build

GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def perform_real_web_search(query: str):
    """Actual web search using Google Custom Search"""
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_CSE_API_KEY)

        # Search CPCB site first
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            siteSearch="cpcb.nic.in",
            num=5
        ).execute()

        # Extract and parse results
        items = result.get('items', [])

        # Use Gemini to synthesize answer from search results
        context = "\n".join([f"{item['title']}: {item['snippet']}"
                           for item in items])

        return synthesize_answer(query, context)

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return None
```

## 🎉 Summary

✅ **Phase 1 Complete**: Detection + Routing + Gemini Knowledge
🔄 **Phase 2 Needed**: True real-time web search API integration

The foundation is ready - just needs a web search API to make it fully real-time!
