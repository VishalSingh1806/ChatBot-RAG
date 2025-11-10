# Git Push Guide

## Files Excluded from Git (Already in .gitignore)

### Sensitive Files
- `.env` files (credentials, API keys)
- `*credentials*.json`, `*key*.json`
- `*.pem`, `*.p12`, `*.crt`

### Heavy Files
- `chroma_db/` (vector database)
- `fwdplasticwastemanagementrules/` (PDF documents)
- `API/reports/` (generated PDF reports)
- `*.pdf` files
- Large CSV files (except `epr_faqs.csv`)

### Build/Generated Files
- `__pycache__/`, `*.pyc`
- `node_modules/`
- `frontend/dist/`
- `venv/`, `env/`

## Files INCLUDED in Git

✅ `API/data/epr_faqs.csv` - FAQ questions database
✅ `.env.example` - Template for environment variables
✅ All Python source code (`.py` files)
✅ Frontend source code (`.tsx`, `.ts`, `.jsx`, `.js`)
✅ Configuration files (`requirements.txt`, `package.json`)
✅ Documentation (`README.md`)

## Git Commands to Push Code

### First Time Setup
```bash
cd "C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG"

# Initialize git (if not already done)
git init

# Add remote repository
git remote add origin <your-github-repo-url>
```

### Push Code
```bash
# Check what files will be committed
git status

# Add all files (respects .gitignore)
git add .

# Commit with message
git commit -m "Initial commit: EPR ChatBot with RAG system"

# Push to GitHub
git push -u origin main
```

### Update Code Later
```bash
# Check changes
git status

# Add changes
git add .

# Commit
git commit -m "Your commit message here"

# Push
git push
```

## Verify Before Pushing

Check that sensitive files are NOT staged:
```bash
git status
```

Should NOT see:
- `.env`
- `chroma_db/`
- `reports/`
- PDF files
- Large CSV files

## Setup on New Machine

1. Clone repository:
```bash
git clone <your-repo-url>
cd ChatBot-RAG
```

2. Copy `.env.example` to `.env`:
```bash
cd API
cp .env.example .env
```

3. Edit `.env` with actual credentials

4. Install dependencies:
```bash
# Backend
pip install -r API/requirements.txt

# Frontend
cd frontend
npm install
```

5. Setup databases:
```bash
cd API
python setup_chromadb.py
python gemini_pdf_processor.py
```

## Important Notes

- Never commit `.env` files with real credentials
- Use `.env.example` as template for others
- Large files (PDFs, databases) should be shared separately
- Keep `epr_faqs.csv` in Git as it's needed for FAQ suggestions
