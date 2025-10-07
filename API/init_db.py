#!/usr/bin/env python3
"""
Initialize ChromaDB with EPR knowledge base
Run this script once to set up the database
"""

from setup_chromadb import setup_chromadb
import os

def main():
    print("Initializing ChromaDB...")
    
    # Check if data file exists
    if not os.path.exists("data/knowledge.csv"):
        print("Error: data/knowledge.csv not found!")
        return
    
    # Setup ChromaDB
    collection = setup_chromadb()
    print("ChromaDB initialized successfully!")
    
    # Test query
    results = collection.query(
        query_texts=["What is EPR?"],
        n_results=1
    )
    
    if results['documents'][0]:
        print(f"Test query successful: {results['documents'][0][0][:50]}...")
    else:
        print("Warning: No results found for test query")

if __name__ == "__main__":
    main()