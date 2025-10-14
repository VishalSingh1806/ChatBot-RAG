# EPR ChatBot RAG System

An AI-powered chatbot for Extended Producer Responsibility (EPR) compliance guidance using Retrieval-Augmented Generation (RAG).

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ChatBot-RAG
   ```

2. **Install dependencies**
   ```bash
   pip install -r API/requirements.txt
   ```

3. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and credentials
   ```

4. **Database setup**
   ```bash
   cd API
   python setup_chromadb.py
   python gemini_pdf_processor.py  # Process PDF documents
   ```

5. **Run the application**
   ```bash
   # Backend
   cd API
   python main.py

   # Frontend (in another terminal)
   cd frontend
   npm install
   npm run dev
   ```

## Configuration

- Copy `.env.example` to `.env` and configure:
  - `GOOGLE_API_KEY`: Your Google Gemini API key
  - `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials JSON
  - Other API keys as needed

## Project Structure

```
ChatBot-RAG/
├── API/                    # Backend FastAPI application
│   ├── data/              # CSV data files (excluded from git)
│   ├── chroma_db/         # ChromaDB database (excluded from git)
│   ├── main.py            # FastAPI server
│   ├── search.py          # RAG search functionality
│   └── ...
├── frontend/              # React frontend
├── fwdplasticwastemanagementrules/  # PDF documents (excluded from git)
└── .env.example          # Environment variables template
```

## Features

- **RAG-based Q&A**: Contextual answers from EPR knowledge base
- **Contextual suggestions**: Smart follow-up questions based on query type
- **Company information**: ReCircle contact details for assistance queries
- **Multi-collection search**: Searches across multiple document collections

## Notes

- Large files (PDFs, database) are excluded from Git
- Sensitive files (.env, credentials) are gitignored
- Use `.env.example` as template for environment setup