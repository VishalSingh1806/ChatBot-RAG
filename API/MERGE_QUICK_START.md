# ChromaDB Merge - Quick Start

## 🚀 3 Simple Steps to Merge Your Databases

### Prerequisites
- Python 3.8+ installed
- Gemini API key set in `.env` file
- Required packages: `chromadb`, `google-generativeai`, `python-dotenv`, `tqdm`, `numpy`

---

## Step 1: Inspect (Optional, 2 minutes)

See what you're working with:

```bash
cd API
python inspect_chromadb.py
```

**What you'll see:**
- Number of documents in each database
- Sample documents
- Metadata structure

---

## Step 2: Merge (10-30 minutes)

Run the merge with automatic deduplication:

```bash
python merge_chromadb.py
```

**What happens:**
1. ✅ Loads all 3 databases
2. ✅ Removes exact duplicates (hash-based)
3. ✅ Removes semantic duplicates (Gemini AI)
4. ✅ Creates merged database at: `merged_chromadb`
5. ✅ Generates `merge_report.json`

**Progress indicators:**
```
📂 Loading documents... (Stage 1)
🔍 Removing duplicates... (Stage 2)
💾 Creating merged DB... (Stage 3)
📊 Generating report... (Stage 4)
✨ Done!
```

---

## Step 3: Verify (2 minutes)

Confirm everything worked:

```bash
python verify_merged_db.py
```

**Checks performed:**
- ✅ Database exists and is accessible
- ✅ All documents have embeddings
- ✅ Source tracking metadata present
- ✅ Document count matches report
- ✅ Sample query works correctly

---

## 🎯 Expected Results

### Before Merge:
- 3 separate databases
- Potentially many duplicates
- Complex multi-database queries

### After Merge:
- 1 unified database
- No duplicates (exact or semantic)
- Simple single-collection queries
- Faster search performance

---

## 📊 Typical Output

### Merge Statistics:
```
Original documents: 2,977
Final documents: 2,520
Duplicates removed: 457 (15.35%)
```

### Source Distribution:
```
chromaDB: 1,105 docs (43.8%)
chromaDB1: 891 docs (35.4%)
DB1: 524 docs (20.8%)
```

---

## 🔧 Using the Merged Database

Update your `config.py`:

```python
# Before
CHROMA_DB_PATHS = [
    r"...\chromaDB",
    r"...\chromaDB1",
    r"...\DB1"
]

# After
CHROMA_DB_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\merged_chromadb"
COLLECTION_NAME = "EPR-Merged"
```

Update your `search.py`:

```python
# Now use single merged collection
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection(name="EPR-Merged")

# Search all data in one query
results = collection.query(
    query_embeddings=[embedding],
    n_results=5
)
```

---

## ⚙️ Configuration (Optional)

Adjust deduplication sensitivity in `merge_chromadb.py`:

```python
# Line 38
SIMILARITY_THRESHOLD = 0.95  # Default

# Options:
# 0.90 = More aggressive (removes more)
# 0.95 = Balanced (recommended)
# 0.98 = Conservative (keeps more)
```

---

## 🐛 Troubleshooting

**Error: "Collection not found"**
- Check database paths are correct
- Run `inspect_chromadb.py` to see available collections

**Error: "API key not found"**
- Verify `GOOGLE_API_KEY` is in your `.env` file

**Merge is slow**
- Normal for large datasets (10K+ docs)
- Gemini API calls take time
- Expected: ~2-3 minutes per 1,000 documents

**High duplicate rate (>30%)**
- Review sample duplicates in output
- Consider increasing similarity threshold
- This might be normal if you had lots of redundant data

---

## 📁 Output Files

After merge, you'll have:

1. **`merged_chromadb/`** - The merged database directory
2. **`merge_report.json`** - Detailed statistics
3. Console logs with progress and samples

---

## ✅ Quick Checklist

- [ ] Ran `inspect_chromadb.py` to understand data
- [ ] Ran `merge_chromadb.py` successfully
- [ ] Reviewed `merge_report.json`
- [ ] Ran `verify_merged_db.py` - all checks passed
- [ ] Updated `config.py` to use merged database
- [ ] Tested chatbot with merged data
- [ ] Backed up original databases (optional)

---

## 🎉 You're Done!

Your merged database is ready to use. The chatbot will now query a single, deduplicated database for better performance and consistency.

**Questions?** Check `CHROMADB_MERGE_GUIDE.md` for detailed documentation.

---

**Quick Commands:**
```bash
# 1. Inspect
python inspect_chromadb.py

# 2. Merge
python merge_chromadb.py

# 3. Verify
python verify_merged_db.py
```

That's it! 🚀
