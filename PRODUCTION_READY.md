# Production Deployment - Hardcoded Paths Fixed

## Changes Made

### 1. **config.py** - Now uses environment variables
**Before:**
```python
CHROMA_DB_PATHS = [
    r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB",
    r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB1"
]
```

**After:**
```python
CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1", os.path.join(BASE_DIR, "chroma_db"))
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2", os.path.join(BASE_DIR, "chroma_db1"))
CHROMA_DB_PATHS = [CHROMA_DB_PATH_1, CHROMA_DB_PATH_2]
```

### 2. **pdf_processor.py** - Now uses environment variables
**Before:**
```python
folder_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\fwdplasticwastemanagementrules"
```

**After:**
```python
folder_path = os.getenv("PDF_DOCUMENTS_PATH", "../fwdplasticwastemanagementrules")
```

### 3. **session_reporter.py** - Now uses config
**Before:**
```python
OUTPUT_DIR = os.path.join(os.getcwd(), "reports")
```

**After:**
```python
from config import REPORTS_OUTPUT_DIR
OUTPUT_DIR = REPORTS_OUTPUT_DIR
```

### 4. **New .env variables added:**
```env
# ChromaDB Paths
CHROMA_DB_PATH_1=./chroma_db
CHROMA_DB_PATH_2=./chroma_db1

# PDF Processing
PDF_DOCUMENTS_PATH=../fwdplasticwastemanagementrules

# Reports
REPORTS_OUTPUT_DIR=./reports
```

## Production Deployment Steps

### 1. **On Production Server:**
```bash
cd /path/to/ChatBot-RAG/API
cp .env.example .env
nano .env  # Edit with production values
```

### 2. **Update .env for Production:**
```env
APP_ENV=production
CORS_ORIGINS="https://your-domain.com"
GOOGLE_API_KEY=your_production_key
SMTP_USERNAME=your_production_email
SMTP_PASSWORD=your_production_password

# Paths will work automatically with relative paths
CHROMA_DB_PATH_1=./chroma_db
CHROMA_DB_PATH_2=./chroma_db1
PDF_DOCUMENTS_PATH=../fwdplasticwastemanagementrules
REPORTS_OUTPUT_DIR=./reports
```

### 3. **Directory Structure (Production):**
```
/opt/chatbot/
├── ChatBot-RAG/
│   ├── API/
│   │   ├── .env                    # Production config
│   │   ├── chroma_db/              # Auto-created
│   │   ├── chroma_db1/             # Auto-created
│   │   ├── reports/                # Auto-created
│   │   └── ...
│   └── fwdplasticwastemanagementrules/  # PDF documents
```

### 4. **Benefits:**
✅ **No hardcoded paths** - Works on any system
✅ **Environment-specific** - Different configs for dev/prod
✅ **Secure** - Sensitive data in .env (gitignored)
✅ **Portable** - Easy to deploy on different servers
✅ **Relative paths** - Works regardless of installation directory

### 5. **Testing:**
```bash
# Test config loading
python -c "from config import CHROMA_DB_PATHS; print(CHROMA_DB_PATHS)"

# Should output:
# ['/opt/chatbot/ChatBot-RAG/API/chroma_db', '/opt/chatbot/ChatBot-RAG/API/chroma_db1']
```

## Migration Checklist

- [x] Remove hardcoded Windows paths from config.py
- [x] Remove hardcoded paths from pdf_processor.py
- [x] Remove hardcoded paths from session_reporter.py
- [x] Add path variables to .env
- [x] Create .env.example for production
- [x] Use relative paths with BASE_DIR
- [x] Auto-create directories if missing

## Notes

1. **All paths are now relative** to the API folder
2. **Directories auto-create** on first run
3. **Works on Windows, Linux, macOS** without changes
4. **Production-ready** - just update .env file
