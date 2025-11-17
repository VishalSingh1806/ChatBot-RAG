#!/usr/bin/env python3
"""
Test the search.py module to verify ChromaDB access
"""
import sys
import os

# Add the API directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'API'))

from search import get_collections

def test_search():
    print("🔍 Testing search.py get_collections()...\n")

    try:
        collections = get_collections()

        if collections:
            print(f"✅ Successfully retrieved {len(collections)} collection(s):\n")

            for name, collection in collections.items():
                try:
                    count = collection.count()
                    print(f"   📚 {name}: {count} documents")
                except Exception as e:
                    print(f"   ❌ {name}: Error getting count - {e}")
        else:
            print("❌ No collections found")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()
