"""
Configuration file for ChromaDB path and other settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Get base directory (API folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ChromaDB Configuration - NEW MERGED DATABASE
# This is the intelligent, auto-updated database with latest CPCB data
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "merged_chromadb"))

# Collection name for the merged database
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "EPR-Merged")

# Legacy configuration (kept for backward compatibility, but not used by default)
CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1", r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB")
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2", r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB1")
CHROMA_DB_PATH_3 = os.getenv("CHROMA_DB_PATH_3", r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\DB1")

# For backward compatibility - points to new merged database
CHROMA_DB_PATHS = [CHROMA_DB_PATH]
COLLECTIONS = {
    CHROMA_DB_PATH_1: ["EPR-chatbot"],
    CHROMA_DB_PATH_2: ["EPRChatbot-1"],
    CHROMA_DB_PATH_3: ["FinalDB"]
}

# PDF Documents path
PDF_DOCUMENTS_PATH = os.getenv("PDF_DOCUMENTS_PATH", os.path.join(BASE_DIR, "..", "fwdplasticwastemanagementrules"))

# Reports output directory
REPORTS_OUTPUT_DIR = os.getenv("REPORTS_OUTPUT_DIR", os.path.join(BASE_DIR, "reports"))

# Ensure the ChromaDB directories exist
for path in CHROMA_DB_PATHS:
    os.makedirs(path, exist_ok=True)

# Ensure reports directory exists
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)