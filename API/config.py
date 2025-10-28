"""
Configuration file for ChromaDB path and other settings
"""
import os

# ChromaDB Configuration - Primary database
CHROMA_DB_PATH = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB"

# ChromaDB Configuration - Secondary database (Langflow)
CHROMA_DB_PATH_LANGFLOW = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB1"

# Collection names for primary database
COLLECTIONS = ["EPR-chatbot"]

# Collection names for Langflow database (will be auto-detected)
COLLECTIONS_LANGFLOW = []  # Auto-populated from chromaDB1

# Ensure the ChromaDB directories exist
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(CHROMA_DB_PATH_LANGFLOW, exist_ok=True)