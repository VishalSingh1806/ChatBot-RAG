"""
Configuration file for ChromaDB path and other settings
"""
import os

# ChromaDB Configuration
# Use environment variable or default to /app/chroma_db for Docker
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/app/chroma_db")

# Collection names
COLLECTIONS = ["EPR-chatbot"]

# Ensure the ChromaDB directory exists
os.makedirs(CHROMA_DB_PATH, exist_ok=True)