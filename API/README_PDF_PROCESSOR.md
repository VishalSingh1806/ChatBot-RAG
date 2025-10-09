# Gemini-Powered PDF Processor

This script processes PDF files using Google's Gemini AI to classify and embed documents into ChromaDB collections.

## Features

- **Intelligent Classification**: Uses Gemini AI to understand PDF content and automatically classify documents into categories
- **4 ChromaDB Collections**: Automatically organizes PDFs into:
  - `producer` - Documents about producers and manufacturers
  - `imports` - Import-related documents and regulations
  - `brand_owners` - Brand ownership and brand management documents
  - `general` - General EPR compliance and other documents
- **Automatic Embedding**: Creates embeddings using SentenceTransformer for semantic search
- **Batch Processing**: Processes entire folders of PDFs automatically
- **Detailed Logging**: Shows progress and results for each PDF processed

## Prerequisites

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- google-genai
- chromadb
- sentence-transformers
- pdfplumber
- python-dotenv

## Environment Setup

Ensure your `.env` file has the required Google Cloud credentials:

```env
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_API_KEY=your-api-key
```

## Usage

### Method 1: Command Line Argument

```bash
cd API
python gemini_pdf_processor.py "/path/to/your/pdf/folder"
```

### Method 2: Interactive Input

```bash
cd API
python gemini_pdf_processor.py
```

Then enter the path when prompted.

### Method 3: Import as Module

```python
from gemini_pdf_processor import process_pdf_folder

# Process a folder of PDFs
process_pdf_folder("/path/to/your/pdf/folder")
```

## How It Works

For each PDF file, the script:

1. **Extracts Text**: Uses pdfplumber to extract all text from the PDF
2. **Classifies with Gemini**: Sends the document to Gemini AI for intelligent classification
3. **Chunks Text**: Splits the text into overlapping chunks for better embedding
4. **Generates Embeddings**: Uses SentenceTransformer to create vector embeddings
5. **Stores in ChromaDB**: Saves chunks with metadata in the appropriate collection

## Output

The script provides detailed output including:

- Progress for each PDF
- Classification results
- Number of chunks created
- Summary statistics by collection
- Test queries to verify the collections

Example output:

```
============================================================
GEMINI-POWERED PDF PROCESSOR
============================================================

✓ Found 50 PDF files
✓ Folder: /path/to/pdfs

Setting up ChromaDB collections...
✓ Collection 'producer' ready
✓ Collection 'imports' ready
✓ Collection 'brand_owners' ready
✓ Collection 'general' ready

[1/50]
============================================================
Processing: document1.pdf
============================================================
Step 1: Extracting text from PDF...
✓ Extracted 5420 characters
Step 2: Classifying document with Gemini...
✓ Classification: PRODUCER
✓ Summary: This document outlines producer responsibilities...
Step 3: Chunking text...
✓ Created 6 chunks
Step 4: Generating embeddings...
✓ Generated 6 embeddings
Step 5: Storing in 'producer' collection...
✓ Stored 6 chunks in 'producer' collection

...

============================================================
PROCESSING COMPLETE
============================================================

Total PDFs processed: 50
Total chunks created: 342

Distribution by collection:
  • PRODUCER: 18 PDFs
  • IMPORTS: 12 PDFs
  • BRAND_OWNERS: 8 PDFs
  • GENERAL: 12 PDFs
```

## ChromaDB Storage

All collections are stored in `./chroma_db` directory with persistent storage.

Each chunk includes metadata:
- `source`: Original PDF filename
- `chunk_id`: Chunk number within the PDF
- `pdf_index`: Index of the PDF in processing order
- `summary`: Gemini-generated summary of the document
- `total_chunks`: Total number of chunks from this PDF

## Querying Collections

After processing, you can query the collections:

```python
import chromadb
from sentence_transformers import SentenceTransformer

# Connect to ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("producer")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Query
query = "What are producer responsibilities?"
query_embedding = model.encode([query]).tolist()
results = collection.query(
    query_embeddings=query_embedding,
    n_results=5
)

# Print results
for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
    print(f"Source: {metadata['source']}")
    print(f"Content: {doc}")
    print("-" * 60)
```

## Configuration

You can adjust the following parameters in the script:

- `chunk_size`: Size of text chunks (default: 1000 characters)
- `overlap`: Overlap between chunks (default: 200 characters)
- `model`: Gemini model to use (default: "gemini-1.5-flash")
- `temperature`: Gemini temperature for classification (default: 0.3)

## Troubleshooting

### PDF Text Extraction Issues

If some PDFs fail to extract text:
- Ensure PDFs are not scanned images (use OCR if needed)
- Check PDF file permissions
- Verify PDFs are not corrupted

### Gemini API Errors

If classification fails:
- Check your Google Cloud credentials
- Verify API quotas and limits
- Ensure network connectivity

### ChromaDB Issues

If storage fails:
- Check disk space
- Verify write permissions for `./chroma_db` directory
- Try deleting and recreating collections

## Notes

- Processing time depends on PDF size and number of files
- Large PDFs are sampled (first 5000 characters) for classification
- Collections persist across runs - rerunning will add new documents
- To reset collections, delete the `./chroma_db` directory
