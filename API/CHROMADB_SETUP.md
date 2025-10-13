# ChromaDB Configuration Update

## Changes Made

The ChromaDB path has been updated to use the correct location:

**New Path**: `C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB`

## Files Updated

1. **config.py** - New centralized configuration file
2. **search.py** - Main search functionality
3. **setup_chromadb.py** - Database setup script
4. **check_db_content.py** - Database content checker
5. **manage_db.py** - Database management utilities
6. **gemini_pdf_processor.py** - PDF processing and embedding
7. **test_chromadb_connection.py** - New test script

## Testing the Connection

Run the test script to verify ChromaDB is working:

```bash
python test_chromadb_connection.py
```

## Expected Collections

The system expects to find the following collection:
- `EPR-chatbot` - Main knowledge base collection

## Troubleshooting

If you encounter issues:

1. Ensure the ChromaDB directory exists at the specified path
2. Check that the collection `EPR-chatbot` contains data
3. Verify that the embeddings are properly generated
4. Run the test script to diagnose connection issues

## Next Steps

1. Verify the ChromaDB contains the expected data
2. Test search functionality with sample queries
3. Ensure the chatbot can retrieve relevant information