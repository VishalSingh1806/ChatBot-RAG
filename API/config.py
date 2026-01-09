"""
Configuration file for ChromaDB path and other settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Get base directory (API folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Base folder for all ChromaDB databases (fallback only)
DB_FOLDER = os.path.join(BASE_DIR, "chroma_db", "drive-download-20260108T065146Z-3-001")

# ALL 5 CHROMADB DATABASES - Use environment variables first, then fallback to local
# Priority: /var/lib/chatbot paths (from .env in Docker) > local paths
CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1") or os.path.join(DB_FOLDER, "chromaDB")
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2") or os.path.join(DB_FOLDER, "chromaDB1")
CHROMA_DB_PATH_3 = os.getenv("CHROMA_DB_PATH_3") or os.path.join(DB_FOLDER, "DB1")
CHROMA_DB_PATH_4 = os.getenv("CHROMA_DB_PATH_4") or os.path.join(DB_FOLDER, "UDB", "Updated_DB")
CHROMA_DB_PATH_5 = os.getenv("CHROMA_DB_PATH_5") or os.path.join(DB_FOLDER, "Updated_DB", "Updated_DB")

# Merged database (optional - for reference)
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "merged_chromadb"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "EPR-Merged")

# ALL DATABASE PATHS - Search will query ALL 5 databases
CHROMA_DB_PATHS = [CHROMA_DB_PATH_1, CHROMA_DB_PATH_2, CHROMA_DB_PATH_3, CHROMA_DB_PATH_4, CHROMA_DB_PATH_5]

# Collections mapping for each database
COLLECTIONS = {
    CHROMA_DB_PATH_1: ["EPR-chatbot"],
    CHROMA_DB_PATH_2: ["EPRChatbot-1"],
    CHROMA_DB_PATH_3: ["FinalDB"],
    CHROMA_DB_PATH_4: ["updated_db"],
    CHROMA_DB_PATH_5: ["updated_db"]
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