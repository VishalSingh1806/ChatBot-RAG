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

# ALL 6 CHROMADB DATABASES - Use environment variables first, then fallback to local
CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1") or os.path.join(DB_FOLDER, "chromaDB")
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2") or os.path.join(DB_FOLDER, "chromaDB1")
CHROMA_DB_PATH_3 = os.getenv("CHROMA_DB_PATH_3") or os.path.join(DB_FOLDER, "DB1")
CHROMA_DB_PATH_4 = os.getenv("CHROMA_DB_PATH_4") or os.path.join(DB_FOLDER, "Updated_DB", "Updated_DB")
CHROMA_DB_PATH_5 = os.getenv("CHROMA_DB_PATH_5") or os.path.join(BASE_DIR, "chroma_db")
CHROMA_DB_PATH_6 = os.getenv("CHROMA_DB_PATH_6") or os.path.join(DB_FOLDER, "UDB", "Updated_DB")

# Merged database (optional - for reference)
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(BASE_DIR, "merged_chromadb"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "EPR-Merged")

# ALL DATABASE PATHS - Search will query ALL 6 databases
CHROMA_DB_PATHS = [CHROMA_DB_PATH_1, CHROMA_DB_PATH_2, CHROMA_DB_PATH_3, CHROMA_DB_PATH_4, CHROMA_DB_PATH_5, CHROMA_DB_PATH_6]

# Database priority order (Newest → Oldest) for recency-based search
# Used for priority-based early stopping search to prioritize most recent data
DB_PRIORITY_ORDER = [
    {"path": CHROMA_DB_PATH_6, "priority": 1, "description": "UDB (Updated Database - Timeline Data)", "recency": "newest"},
    {"path": CHROMA_DB_PATH_4, "priority": 2, "description": "Updated_DB", "recency": "very_recent"},
    {"path": CHROMA_DB_PATH_5, "priority": 3, "description": "chroma_db local (PDF Documents)", "recency": "recent"},
    {"path": CHROMA_DB_PATH_3, "priority": 4, "description": "DB1 (Final Database)", "recency": "older"},
    {"path": CHROMA_DB_PATH_2, "priority": 5, "description": "chromaDB1 (EPR Chatbot 1)", "recency": "old"},
    {"path": CHROMA_DB_PATH_1, "priority": 6, "description": "chromaDB (Original EPR Chatbot)", "recency": "oldest"}
]

# Enable/disable priority-based early stopping search
# Set to false to revert to traditional search (all databases)
ENABLE_PRIORITY_SEARCH = os.getenv("ENABLE_PRIORITY_SEARCH", "true").lower() == "true"

# Distance threshold for early stopping (when to stop searching older databases)
# Regular queries: Stop if match found with distance < threshold
# Timeline queries: Use separate threshold for 2024-25, 2025-26 queries
EARLY_STOP_THRESHOLD = float(os.getenv("EARLY_STOP_THRESHOLD", "1.5"))
EARLY_STOP_THRESHOLD_TIMELINE = float(os.getenv("EARLY_STOP_THRESHOLD_TIMELINE", "2.0"))

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

# Ensure the ChromaDB directories exist
for path in CHROMA_DB_PATHS:
    os.makedirs(path, exist_ok=True)

# Ensure reports directory exists
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)