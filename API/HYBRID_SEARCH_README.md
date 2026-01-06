# Hybrid Search Engine Documentation

## Overview

The Hybrid Search Engine combines **60% LLM knowledge** with **40% database search** to provide more comprehensive and accurate responses for EPR (Extended Producer Responsibility) and plastic waste management queries.

## Features

- **Dual-Source Intelligence**: Combines LLM's broad knowledge with specific database content
- **Weighted Results**: 60% weight to LLM responses, 40% weight to database search
- **Non-Intrusive**: Existing search functionality remains unchanged
- **Configurable**: Easy to adjust weights and search modes

## API Endpoints

### New Hybrid Search Endpoint
```
POST /hybrid-query
```

**Request Body:**
```json
{
    "session_id": "optional-session-id",
    "text": "Your EPR question here",
    "history": []
}
```

**Response:**
```json
{
    "answer": "Combined LLM + Database response",
    "similar_questions": ["Related question 1", "Related question 2"],
    "intent": {
        "type": "information_request",
        "confidence": 0.85,
        "should_connect": false
    },
    "context": {
        "search_type": "hybrid",
        "llm_weight": "60%",
        "db_weight": "40%",
        "engagement_score": 0.7
    },
    "source_info": {
        "hybrid_search": true,
        "llm_weight": 0.6,
        "db_weight": 0.4
    }
}
```

### Original Search Endpoint (Unchanged)
```
POST /query
```
The original search functionality remains completely intact.

## Files Added

1. **`hybrid_search.py`** - Main hybrid search engine implementation
2. **`search_config.py`** - Configuration management for search modes
3. **`test_hybrid_search.py`** - Test script for hybrid functionality
4. **Updated `main.py`** - Added new `/hybrid-query` endpoint

## How It Works

1. **Database Search (40%)**: Uses existing ChromaDB vector search to find relevant documents
2. **LLM Knowledge (60%)**: Generates response using Gemini's knowledge about EPR and plastic waste management
3. **Intelligent Combination**: Uses LLM to merge both sources into a coherent, comprehensive answer

## Usage Examples

### Using the Hybrid Search
```python
from hybrid_search import find_hybrid_answer

result = find_hybrid_answer("What is EPR compliance?")
print(result["answer"])
```

### Testing the Functionality
```bash
python test_hybrid_search.py
```

### Configuration
```python
from search_config import search_config, SearchMode

# Switch to hybrid mode
search_config.set_search_mode(SearchMode.HYBRID)

# Adjust weights (e.g., 70% LLM, 30% DB)
search_config.set_weights(0.7, 0.3)
```

## Environment Variables

- `SEARCH_MODE`: Default search mode (`traditional`, `hybrid`, `llm_only`, `db_only`)
- `LLM_WEIGHT`: Weight for LLM responses (default: 0.6)
- `DB_WEIGHT`: Weight for database responses (default: 0.4)

## Benefits

1. **Enhanced Accuracy**: Combines specific database knowledge with LLM's broad understanding
2. **Better Coverage**: Handles queries even when database has limited information
3. **Contextual Responses**: LLM provides better context and explanation
4. **Fallback Mechanism**: If one source fails, the other can still provide answers
5. **Flexible Weighting**: Easy to adjust the balance between sources

## Integration

The hybrid search is designed to be:
- **Non-disruptive**: Existing code remains unchanged
- **Optional**: Can be used alongside traditional search
- **Configurable**: Easy to enable/disable or adjust weights
- **Extensible**: Can be enhanced with additional search sources

## Future Enhancements

- Dynamic weight adjustment based on query type
- Multiple LLM model support
- Real-time performance monitoring
- A/B testing capabilities
- Custom domain-specific fine-tuning