"""
Configuration file for ChromaDB path and other settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Get base directory (API folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Base folder for all ChromaDB databases
DB_FOLDER = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot"

# ALL 6 CHROMADB DATABASES - Use environment variables first, then fallback to local
CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1") or os.path.join(DB_FOLDER, "chromaDB")
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2") or os.path.join(DB_FOLDER, "chromaDB1")
CHROMA_DB_PATH_3 = os.getenv("CHROMA_DB_PATH_3") or os.path.join(DB_FOLDER, "DB1")
CHROMA_DB_PATH_4 = os.getenv("CHROMA_DB_PATH_4") or os.path.join(DB_FOLDER, "Updated_DB", "Updated_DB")
CHROMA_DB_PATH_5 = os.getenv("CHROMA_DB_PATH_5") or os.path.join(BASE_DIR, "chroma_db")
CHROMA_DB_PATH_6 = os.getenv("CHROMA_DB_PATH_6") or r"C:\Users\BHAKTI\Downloads\UDB-20260112T064020Z-3-001\UDB"

# Merged database (optional - for reference)
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "merged_chromadb"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "EPR-Merged")

# ALL DATABASE PATHS - Search will query ALL 6 databases
CHROMA_DB_PATHS = [CHROMA_DB_PATH_1, CHROMA_DB_PATH_2, CHROMA_DB_PATH_3, CHROMA_DB_PATH_4, CHROMA_DB_PATH_5, CHROMA_DB_PATH_6]

# UDB path for timeline queries (2024-25, 2025-26)
UDB_PATH = CHROMA_DB_PATH_6

# Collections mapping for each database
COLLECTIONS = {
    CHROMA_DB_PATH_1: ["EPR-chatbot"],
    CHROMA_DB_PATH_2: ["EPRChatbot-1"],
    CHROMA_DB_PATH_3: ["FinalDB"],
    CHROMA_DB_PATH_4: ["updated_db"],
    CHROMA_DB_PATH_5: ["pdf_docs"],
    CHROMA_DB_PATH_6: ["Updated_DB"]  # Changed to uppercase to match new collection
}

# PDF Documents path
PDF_DOCUMENTS_PATH = os.getenv("PDF_DOCUMENTS_PATH", os.path.join(BASE_DIR, "..", "fwdplasticwastemanagementrules"))

# Reports output directory
REPORTS_OUTPUT_DIR = os.getenv("REPORTS_OUTPUT_DIR", os.path.join(BASE_DIR, "reports"))

# Ensure the ChromaDB directories exist (skip external paths)
for path in CHROMA_DB_PATHS:
    if path.startswith(BASE_DIR):  # Only create directories within project
        os.makedirs(path, exist_ok=True)

# Ensure reports directory exists
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)