#!/usr/bin/env python3
"""
Test script to verify ChromaDB setup
"""
import chromadb
import sys
import os

# Add the API directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'API'))

from config import CHROMA_DB_PATHS, COLLECTIONS

def test_chromadb():
    print("🔍 Testing ChromaDB setup...\n")

    for db_path in CHROMA_DB_PATHS:
        print(f"📁 Testing database: {db_path}")

        # Check if path exists
        if not os.path.exists(db_path):
            print(f"   ❌ Path does not exist: {db_path}")
            continue

        try:
            # Connect to the database
            client = chromadb.PersistentClient(path=db_path)
            print(f"   ✅ Connected to database")

            # Check expected collections
            expected_collections = COLLECTIONS.get(db_path, [])
            print(f"   🎯 Expected collections: {expected_collections}")

            for expected_name in expected_collections:
                try:
                    collection = client.get_collection(name=expected_name)
                    count = collection.count()
                    print(f"   ✅ Collection '{expected_name}' exists with {count} documents")
                except Exception as e:
                    print(f"   ❌ Collection '{expected_name}' not found: {e}")

            print()

        except Exception as e:
            print(f"   ❌ Error connecting to database: {e}\n")

if __name__ == "__main__":
    test_chromadb()
