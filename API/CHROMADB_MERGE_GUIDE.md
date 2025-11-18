## ChromaDB Merge Guide

Complete guide for merging three ChromaDB databases with intelligent deduplication using Gemini AI.

---

## 📋 Overview

You have **3 separate ChromaDB databases** that need to be merged into one:

| Database | Location | Collection | Purpose |
|----------|----------|------------|---------|
| chromaDB | `C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB` | EPR-chatbot | Original database |
| chromaDB1 | `C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB1` | EPRChatbot-1 | Secondary database |
| DB1 | `C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\DB1` | FinalDB | Third database |

**Output:** `merged_chromadb` (Collection: EPR-Merged)

---

## 🎯 Features

### Intelligent Deduplication

The merge script uses a **2-stage deduplication** approach:

1. **Stage 1: Exact Text Matching**
   - Uses MD5 hashing for fast detection
   - Removes documents with identical text (case-insensitive)

2. **Stage 2: Semantic Similarity (Gemini AI)**
   - Uses Google Gemini embeddings
   - Compares semantic meaning, not just text
   - Configurable similarity threshold (default: 95%)
   - Keeps the first occurrence, removes duplicates

### Why Gemini for Deduplication?

- **Semantic Understanding**: Detects similar content even if worded differently
- **Accuracy**: Better than simple text matching
- **Context-Aware**: Understands meaning, not just keywords
- **Production-Ready**: Uses the same Gemini embeddings as your chatbot

---

## 🚀 Quick Start

### Step 1: Inspect Databases (Optional but Recommended)

First, understand what you're working with:

```bash
cd /mnt/d/AI-ChatBot/API
python inspect_chromadb.py
```

This will show you:
- ✅ Number of documents in each database
- ✅ Sample documents from each collection
- ✅ Metadata structure
- ✅ Total documents to merge

**Expected Output:**
```
Database: chromaDB
Collection: EPR-chatbot
📊 Total documents: 1,234

Database: chromaDB1
Collection: EPRChatbot-1
📊 Total documents: 987

Database: DB1
Collection: FinalDB
📊 Total documents: 756

Total documents across all databases: 2,977
```

---

### Step 2: Run the Merge Script

```bash
cd /mnt/d/AI-ChatBot/API
python merge_chromadb.py
```

**What happens:**

1. **Loading Phase** (1-2 minutes)
   ```
   📂 Loading from: chromaDB
   ✅ Found 1,234 documents

   📂 Loading from: chromaDB1
   ✅ Found 987 documents

   📂 Loading from: DB1
   ✅ Found 756 documents

   📊 Total documents loaded: 2,977
   ```

2. **Deduplication Phase** (5-15 minutes depending on size)
   ```
   Stage 1: Removing exact text duplicates...
   ✅ Removed 312 exact duplicates
   📊 Remaining documents: 2,665

   Stage 2: Removing semantic duplicates (using Gemini)...
   Similarity threshold: 0.95
   ✅ Removed 145 semantic duplicates
   📊 Final unique documents: 2,520
   ```

3. **Merging Phase** (2-5 minutes)
   ```
   📁 Output path: merged_chromadb
   Collection name: EPR-Merged

   💾 Inserting documents into merged database...
   Inserted batch 1: 100/2,520 documents
   Inserted batch 2: 200/2,520 documents
   ...
   ✅ Successfully created merged database!
   ```

4. **Report Generation**
   ```
   📊 Merge Summary:
   Original documents: 2,977
   Final documents: 2,520
   Duplicates removed: 457
   Deduplication rate: 15.35%

   📄 Report saved to: merge_report.json
   ```

---

## ⚙️ Configuration Options

You can customize the merge behavior by editing `merge_chromadb.py`:

### 1. Similarity Threshold

```python
# Line 38
SIMILARITY_THRESHOLD = 0.95  # Default: 95% similar = duplicate
```

**Options:**
- `0.90` - More aggressive (removes more duplicates, may remove similar-but-different content)
- `0.95` - Balanced (recommended)
- `0.98` - Conservative (keeps more content, removes only near-identical)

### 2. Batch Size

```python
# Line 195 (in create_merged_database function)
BATCH_SIZE = 100  # Documents per batch
```

Adjust if you have memory issues:
- Smaller (50) = Slower but uses less memory
- Larger (200) = Faster but needs more memory

### 3. Output Location

```python
# Line 29
MERGED_DB_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\merged_chromadb"
```

Change to save the merged database elsewhere.

---

## 📊 Understanding the Merge Report

After merging, a `merge_report.json` file is created with details:

```json
{
  "original_documents": 2977,
  "final_documents": 2520,
  "duplicates_removed": 457,
  "deduplication_rate": "15.35%",
  "source_databases": [
    "chromaDB",
    "chromaDB1",
    "DB1"
  ],
  "merged_database_path": "merged_chromadb",
  "collection_name": "EPR-Merged",
  "similarity_threshold": 0.95
}
```

**Key Metrics:**
- **original_documents**: Total before deduplication
- **final_documents**: Unique documents after deduplication
- **duplicates_removed**: Number of duplicates eliminated
- **deduplication_rate**: Percentage of duplicates removed

---

## 🔍 Verifying the Merged Database

After merging, verify the result:

```python
import chromadb

# Connect to merged database
client = chromadb.PersistentClient(
    path=r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\merged_chromadb"
)

# Get collection
collection = client.get_collection(name="EPR-Merged")

# Check count
print(f"Total documents: {collection.count()}")

# Get a sample
sample = collection.get(limit=5, include=['documents', 'metadatas'])
for i, (doc, meta) in enumerate(zip(sample['documents'], sample['metadatas'])):
    print(f"\nDoc {i+1}:")
    print(f"  Text: {doc[:100]}...")
    print(f"  Source DB: {meta.get('source_db')}")
    print(f"  Source Collection: {meta.get('source_collection')}")
```

---

## 🔧 Using the Merged Database in Your Application

### Option 1: Update config.py

Update your `config.py` to use the merged database:

```python
# Old (multiple databases)
CHROMA_DB_PATH_1 = r"...\chromaDB"
CHROMA_DB_PATH_2 = r"...\chromaDB1"
CHROMA_DB_PATH_3 = r"...\DB1"

# New (single merged database)
CHROMA_DB_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\merged_chromadb"
COLLECTION_NAME = "EPR-Merged"
```

### Option 2: Update search.py

Update your search logic to query the single merged collection:

```python
import chromadb

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection(name="EPR-Merged")

# Now search across all merged data
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)
```

---

## 🐛 Troubleshooting

### Error: "Collection not found"

**Problem:** The collection name doesn't exist in the database.

**Solution:**
1. Run `inspect_chromadb.py` to see available collections
2. Update collection names in `merge_chromadb.py` if needed

### Error: "Gemini API key not found"

**Problem:** `GOOGLE_API_KEY` not set in environment.

**Solution:**
```bash
# Check .env file has:
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Merge is very slow

**Possible causes:**
1. **Large dataset**: Normal for thousands of documents
2. **API rate limits**: Gemini has rate limits
3. **Network issues**: Gemini API calls need internet

**Solutions:**
- Reduce `SIMILARITY_THRESHOLD` to skip some semantic checks
- Increase `BATCH_SIZE` for faster insertion
- Run during off-peak hours

### High deduplication rate (>30%)

**Analysis:** This might indicate:
- ✅ Good news: Lots of duplicates were found and removed
- ⚠️ Possible issue: Threshold too low, removing valid content

**Action:**
1. Review sample duplicates in console output
2. If threshold seems too aggressive, increase to 0.98
3. Re-run merge with adjusted settings

---

## 📈 Performance Expectations

### Time Estimates

| Database Size | Stage 1 (Exact) | Stage 2 (Semantic) | Total Time |
|---------------|-----------------|---------------------|------------|
| 1,000 docs | 10 seconds | 2-3 minutes | ~3 minutes |
| 5,000 docs | 30 seconds | 10-15 minutes | ~15 minutes |
| 10,000 docs | 1 minute | 20-30 minutes | ~30 minutes |

**Note:** Stage 2 uses Gemini API, so speed depends on:
- Your internet connection
- Gemini API response time
- Number of comparisons needed

### Memory Usage

- **Small (<5K docs)**: ~500 MB RAM
- **Medium (5-10K)**: ~1-2 GB RAM
- **Large (>10K)**: ~2-4 GB RAM

---

## ✅ Checklist

Before running the merge:

- [ ] All three database paths are correct
- [ ] `GOOGLE_API_KEY` is set in `.env`
- [ ] Ran `inspect_chromadb.py` to understand data
- [ ] Decided on similarity threshold
- [ ] Have enough disk space for merged database
- [ ] Backed up original databases (optional but recommended)

After running the merge:

- [ ] Merge completed without errors
- [ ] `merge_report.json` generated
- [ ] Verified document count makes sense
- [ ] Tested sample queries on merged database
- [ ] Updated application config to use merged database

---

## 🎉 Next Steps

After successful merge:

1. **Test the merged database** with sample queries
2. **Update your application** to use the merged database
3. **Deploy** the merged database to production
4. **Archive** old databases (keep as backup)
5. **Monitor** chatbot performance with merged data

---

## 📞 Support

If you encounter issues:
- Check the console output for detailed error messages
- Review `merge_report.json` for statistics
- Verify all database paths are accessible
- Ensure Gemini API key is valid

---

**Created:** 2024-11-17
**Version:** 1.0
**Requires:** Python 3.8+, chromadb, google-generativeai, python-dotenv, tqdm, numpy
