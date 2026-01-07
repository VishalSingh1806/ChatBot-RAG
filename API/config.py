"""
Configuration file for ChromaDB path and other settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Get base directory (API folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ChromaDB Configuration - All 5 databases
CHROMA_DB_PATH_1 = os.getenv("CHROMA_DB_PATH_1", r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB")
CHROMA_DB_PATH_2 = os.getenv("CHROMA_DB_PATH_2", r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB1")
CHROMA_DB_PATH_3 = os.getenv("CHROMA_DB_PATH_3", r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\DB1")
CHROMA_DB_PATH_4 = os.getenv("CHROMA_DB_PATH_4", r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\Updated_DB")
CHROMA_DB_PATH_5 = os.getenv("CHROMA_DB_PATH_5", r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\Updated_DB\Updated_DB")

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

# Ensure the ChromaDB directories exist
for path in CHROMA_DB_PATHS:
    os.makedirs(path, exist_ok=True)

# Ensure reports directory exists
os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)