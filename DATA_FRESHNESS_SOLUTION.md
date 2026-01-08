# Data Freshness & Versioning Strategy for EPR ChatBot

## Problem Statement
When CPCB updates EPR rules and new documents are embedded, the chatbot sometimes retrieves old/outdated information instead of the latest data. Current metadata only stores `source` (filename) and `chunk_id`, with no temporal information.

---

## Solution Approaches (Ranked by Effectiveness)

### ✅ **RECOMMENDED: Approach 1 - Metadata-Based Recency Filtering**

**Best for:** Your use case with regulatory updates

#### Implementation Strategy:

1. **Add Temporal Metadata** when embedding documents:
   ```python
   metadata = {
       "source": pdf_file,
       "chunk_id": j,
       "document_date": "2024-01-15",      # Date from document/filename
       "embedding_date": "2025-01-08",      # Date when embedded
       "fiscal_year": "2024-25",            # For EPR rules
       "version": "v2.0",                   # Document version
       "is_superseded": False,              # Flag for old rules
       "regulation_type": "PWM_Rules"       # Plastic Waste Management
   }
   ```

2. **Weighted Scoring Algorithm** (Recency + Relevance):
   ```python
   final_score = (semantic_similarity * 0.7) + (recency_score * 0.3)

   # Recency score calculation:
   recency_score = 1.0 - (days_since_embedding / max_age_days)

   # Example:
   # - Document embedded today: recency_score = 1.0
   # - Document embedded 180 days ago: recency_score = 0.5 (if max_age = 365)
   # - Document embedded 365 days ago: recency_score = 0.0
   ```

3. **Filter Superseded Documents**:
   ```python
   # In search query, add metadata filter
   results = collection.query(
       query_embeddings=[query_embedding],
       n_results=10,
       where={"is_superseded": False}  # Exclude old rules
   )
   ```

#### Pros:
- ✅ Balances relevance and recency
- ✅ Simple to implement
- ✅ Keeps historical data for reference
- ✅ Fine-grained control

#### Cons:
- ⚠️ Requires re-embedding existing documents with metadata
- ⚠️ Need to manually mark superseded documents

---

### Approach 2 - Collection-Based Versioning

**Best for:** Clear separation of different time periods

#### Implementation:
```python
# Separate collections by fiscal year
collections = {
    "EPR_FY_2025-26": newest_collection,
    "EPR_FY_2024-25": current_collection,
    "EPR_FY_2023-24": old_collection
}

# Search priority: newest first
def search_with_fallback(query):
    # Try newest collection first
    results = search_collection("EPR_FY_2025-26", query)

    if len(results) < threshold:
        # Fallback to previous year
        results += search_collection("EPR_FY_2024-25", query)

    return results
```

#### Pros:
- ✅ Clean separation
- ✅ Easy to manage versions
- ✅ Can disable old collections entirely

#### Cons:
- ⚠️ Multiple database searches (slower)
- ⚠️ Harder to search across years
- ⚠️ More storage overhead

---

### Approach 3 - Delete-and-Replace Strategy

**Best for:** When historical data is not needed

#### Implementation:
```python
# When new regulation is released:
1. Identify old documents by filename pattern or metadata
2. Delete old documents from collection
3. Add new documents

# Example:
collection.delete(where={"regulation_type": "PWM_Rules", "fiscal_year": "2023-24"})
collection.add(new_documents_with_metadata)
```

#### Pros:
- ✅ Simplest approach
- ✅ No confusion from old data
- ✅ Smallest database size

#### Cons:
- ⚠️ Lose historical information
- ⚠️ Can't answer "what changed" questions
- ⚠️ Risky (accidental deletion)

---

### Approach 4 - Hybrid Boost Strategy

**Best for:** Advanced use cases with complex scoring

#### Implementation:
```python
def calculate_final_score(result):
    # Base semantic similarity
    semantic_score = 1 - result['distance']

    # Recency boost
    days_old = (datetime.now() - result['metadata']['embedding_date']).days
    recency_multiplier = max(0.5, 1.0 - (days_old / 730))  # Decay over 2 years

    # Fiscal year boost (prefer current FY)
    fy_boost = 1.5 if result['metadata']['fiscal_year'] == current_fy else 1.0

    # Superseded penalty
    superseded_penalty = 0.3 if result['metadata']['is_superseded'] else 1.0

    # Combined score
    final_score = semantic_score * recency_multiplier * fy_boost * superseded_penalty

    return final_score
```

#### Pros:
- ✅ Most sophisticated
- ✅ Multiple ranking signals
- ✅ Can fine-tune weights

#### Cons:
- ⚠️ Complex to implement
- ⚠️ Requires experimentation to tune
- ⚠️ Harder to debug

---

## Recommended Implementation Plan

### Phase 1: Immediate Quick Fix (1-2 hours)
```python
# Add to search.py - filter by collection priority
def get_collections():
    # Prioritize newest databases first
    priority_order = [
        CHROMA_DB_PATH_5,  # Updated_DB (newest)
        CHROMA_DB_PATH_4,  # UDB
        CHROMA_DB_PATH_3,  # DB1
        CHROMA_DB_PATH_2,  # chromaDB1
        CHROMA_DB_PATH_1,  # chromaDB (oldest)
    ]

    # Search in priority order, boost newer collections
    ...
```

### Phase 2: Add Metadata to New Embeddings (3-5 hours)
1. Update `gemini_pdf_processor.py` to add date metadata
2. Extract document date from filename or content
3. Add embedding timestamp
4. Mark fiscal year from filename patterns

### Phase 3: Implement Recency Scoring (5-8 hours)
1. Modify search.py to calculate recency scores
2. Implement weighted scoring (70% relevance, 30% recency)
3. Add configurable weights in config.py

### Phase 4: Create Superseding System (8-12 hours)
1. Build admin tool to mark documents as superseded
2. Automatically detect newer versions by filename
3. Update search to filter superseded docs
4. Add version tracking

---

## Code Examples

### Enhanced PDF Processor with Metadata
```python
import os
from datetime import datetime
import re

def extract_document_date(filename):
    """Extract date from filename patterns like 'EPR_Rules_2024.pdf'"""
    patterns = [
        r'(\d{4})',           # Year: 2024
        r'(\d{4})-(\d{2})',   # FY: 2024-25
        r'_v(\d+\.?\d*)',     # Version: v2.0
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(0)

    # Fallback to file modification date
    return datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%Y-%m-%d')

def process_folder_pdfs_with_metadata(folder_path):
    """Enhanced version with temporal metadata"""
    # ... existing code ...

    for i, pdf_file in enumerate(pdf_files):
        doc_date = extract_document_date(pdf_file)
        fiscal_year = extract_fiscal_year(pdf_file)

        for j, chunk in enumerate(chunks):
            all_metadata.append({
                "source": pdf_file,
                "chunk_id": j,
                "document_date": doc_date,
                "embedding_date": datetime.now().strftime('%Y-%m-%d'),
                "fiscal_year": fiscal_year,
                "is_superseded": False,
                "version": extract_version(pdf_file) or "1.0"
            })
```

### Enhanced Search with Recency Scoring
```python
def find_best_answer_with_recency(user_query: str) -> dict:
    """Search with recency-weighted scoring"""

    # Get embedding
    query_embedding = genai.embed_content(...)['embedding']

    all_results = []

    # Query all collections
    for collection_name, collection in collections.items():
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={"is_superseded": False}  # Filter superseded docs
        )

        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]

            # Calculate recency score
            embedding_date = datetime.strptime(metadata.get('embedding_date', '2020-01-01'), '%Y-%m-%d')
            days_old = (datetime.now() - embedding_date).days
            recency_score = max(0, 1.0 - (days_old / 365))  # 1 year decay

            # Calculate fiscal year bonus
            current_fy = "2024-25"  # Get from config
            fy_bonus = 1.3 if metadata.get('fiscal_year') == current_fy else 1.0

            # Weighted final score
            semantic_score = 1 - distance
            final_score = (semantic_score * 0.7) + (recency_score * 0.3)
            final_score *= fy_bonus

            all_results.append({
                'document': doc,
                'score': final_score,
                'metadata': metadata,
                'recency_score': recency_score,
                'semantic_score': semantic_score
            })

    # Sort by final score (highest first)
    all_results.sort(key=lambda x: x['score'], reverse=True)

    # Return top result
    best_result = all_results[0]

    return {
        "answer": best_result['document'],
        "source_info": {
            "source": best_result['metadata']['source'],
            "fiscal_year": best_result['metadata']['fiscal_year'],
            "document_date": best_result['metadata']['document_date'],
            "recency_score": best_result['recency_score'],
            "semantic_score": best_result['semantic_score'],
            "final_score": best_result['score']
        }
    }
```

### Admin Tool to Mark Superseded Documents
```python
def mark_documents_as_superseded(collection, pattern, fiscal_year):
    """Mark old documents as superseded when new version is available"""

    # Get all documents matching pattern
    results = collection.get(
        where={
            "fiscal_year": fiscal_year,
            "regulation_type": pattern
        }
    )

    # Update metadata to mark as superseded
    for doc_id in results['ids']:
        collection.update(
            ids=[doc_id],
            metadatas=[{"is_superseded": True}]
        )

    print(f"Marked {len(results['ids'])} documents as superseded")
```

---

## Configuration Settings

Add to `config.py`:
```python
# Data freshness settings
RECENCY_WEIGHT = 0.3           # 30% weight to recency
RELEVANCE_WEIGHT = 0.7         # 70% weight to semantic similarity
MAX_DOCUMENT_AGE_DAYS = 365    # Documents older than 1 year get 0 recency score
CURRENT_FISCAL_YEAR = "2024-25"
FY_BOOST_MULTIPLIER = 1.3      # Boost current FY results by 30%

# Superseded document handling
EXCLUDE_SUPERSEDED = True      # Filter out superseded documents
SHOW_RECENCY_INFO = True       # Show recency info in responses
```

---

## Testing Strategy

1. **Create Test Cases**:
   ```python
   # Test old vs new document retrieval
   def test_recency_preference():
       query = "annual report deadline 2024-25"

       # Should return document from 2024, not 2022
       result = find_best_answer_with_recency(query)

       assert result['source_info']['fiscal_year'] == "2024-25"
       assert result['source_info']['is_superseded'] == False
   ```

2. **A/B Testing**: Compare results with/without recency scoring

3. **Monitor Metrics**:
   - Average recency score of returned results
   - Number of superseded documents retrieved
   - User satisfaction with answer freshness

---

## Migration Plan

### Step 1: Backup Current Data
```bash
cp -r API/chroma_db API/chroma_db_backup_$(date +%Y%m%d)
```

### Step 2: Re-embed with Metadata
```python
# Run enhanced processor on all PDFs
python gemini_pdf_processor_enhanced.py
```

### Step 3: Gradual Rollout
- Week 1: Add metadata to new embeddings only
- Week 2: Implement basic recency filtering
- Week 3: Add weighted scoring
- Week 4: Enable superseded document filtering

---

## Monitoring & Maintenance

### Weekly Tasks:
- Review newly added documents
- Mark superseded regulations
- Update current fiscal year in config

### Monthly Tasks:
- Analyze recency score distribution
- Tune weights if needed
- Archive very old documents

### Quarterly Tasks:
- Re-embed all documents with updated metadata
- Clean up superseded documents
- Performance optimization

---

## Cost Considerations

**Embedding Costs** (Google Gemini text-embedding-004):
- Free tier: 1,500 requests/day
- After: $0.00025 per 1000 characters

**Storage Costs**:
- Each metadata field adds ~100 bytes per chunk
- 10,000 chunks × 100 bytes = 1 MB (negligible)

**Recommendation**: Metadata approach has minimal cost impact

---

## Summary

**Best Solution for Your Use Case:**

1. **Immediate**: Prioritize newer collections in search order
2. **Short-term**: Add date metadata to new embeddings
3. **Long-term**: Implement weighted recency scoring (70% relevance + 30% recency)
4. **Maintenance**: Build tool to mark superseded documents

**Expected Improvement:**
- 80-90% reduction in outdated information being returned
- Automatic preference for current fiscal year regulations
- Clear versioning for compliance documentation

**Implementation Time:** 2-3 weeks for full solution
