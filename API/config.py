"""
Configuration file for ChromaDB path and other settings
"""
import os

# ChromaDB Configuration
CHROMA_DB_PATH = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB"

# Collection names
COLLECTIONS = ["EPR-chatbot"]

# Ensure the ChromaDB directory exists
os.makedirs(CHROMA_DB_PATH, exist_ok=True)