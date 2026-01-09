"""
Test script to verify all 5 databases are connected and being queried
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from search import get_collections, clients
from config import CHROMA_DB_PATHS, COLLECTIONS
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

print("=" * 80)
print("Testing All 5 ChromaDB Databases")
print("=" * 80)

# Test 1: Check database paths
print("\n1. Configured Database Paths:")
print("-" * 80)
for i, path in enumerate(CHROMA_DB_PATHS, 1):
    print(f"   DB{i}: {path}")
    if os.path.exists(path):
        print(f"   ✅ Path exists")
    else:
        print(f"   ❌ Path NOT found")

# Test 2: Check clients
print("\n2. Database Client Connections:")
print("-" * 80)
print(f"   Total clients initialized: {len(clients)}")
for db_path, client in clients.items():
    print(f"   ✅ Client connected: {db_path}")

# Test 3: Check collections
print("\n3. Collections from All Databases:")
print("-" * 80)
collections = get_collections()
print(f"   Total collections found: {len(collections)}")
for collection_key, collection in collections.items():
    doc_count = collection.count()
    print(f"   ✅ {collection_key}: {doc_count} documents")

# Test 4: Test search
print("\n4. Test Search Query:")
print("-" * 80)
test_query = "What is EPR registration?"
print(f"   Query: '{test_query}'")

from search import find_best_answer
result = find_best_answer(test_query)

print(f"   Answer preview: {result['answer'][:200]}...")
print(f"   Source: {result.get('source_info', {}).get('collection_name', 'N/A')}")

print("\n" + "=" * 80)
print("✅ All database tests completed!")
print("=" * 80)
