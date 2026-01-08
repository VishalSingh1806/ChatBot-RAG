"""
Configuration file for ChromaDB path and other settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Get base directory (API folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ChromaDB Configuration - All 5 databases from local folder
DB_FOLDER = os.path.join(BASE_DIR, "chroma_db", "drive-download-20260108T065146Z-3-001")

CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1", os.path.join(DB_FOLDER, "chromaDB"))
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2", os.path.join(DB_FOLDER, "chromaDB1"))
CHROMA_DB_PATH_3 = os.getenv("CHROMA_DB_PATH_3", os.path.join(DB_FOLDER, "DB1"))
CHROMA_DB_PATH_4 = os.getenv("CHROMA_DB_PATH_4", os.path.join(DB_FOLDER, "UDB", "Updated_DB"))
CHROMA_DB_PATH_5 = os.getenv("CHROMA_DB_PATH_5", os.path.join(DB_FOLDER, "Updated_DB", "Updated_DB"))


CHROMA_DB_PATHS = [CHROMA_DB_PATH_1, CHROMA_DB_PATH_2, CHROMA_DB_PATH_3, CHROMA_DB_PATH_4, CHROMA_DB_PATH_5]

# Collection names for each database
COLLECTIONS = {
    CHROMA_DB_PATH_1: ["EPR-chatbot"],
    CHROMA_DB_PATH_2: ["EPRChatbot-1"],
    CHROMA_DB_PATH_3: ["FinalDB"],
    CHROMA_DB_PATH_4: ["updated_db"],
    CHROMA_DB_PATH_5: ["Updated_DB"]
}

# PDF Documents path
PDF_DOCUMENTS_PATH = os.getenv("PDF_DOCUMENTS_PATH", os.path.join(BASE_DIR, "..", "fwdplasticwastemanagementrules"))

# Reports output directory
REPORTS_OUTPUT_DIR = os.getenv("REPORTS_OUTPUT_DIR", os.path.join(BASE_DIR, "reports"))

# Ensure reports directory exists (ChromaDB directories already exist in the folder)
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)