import chromadb
import os

# Database paths from config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "chroma_db", "drive-download-20260108T065146Z-3-001")

paths = {
    'CHROMA_DB_PATH_1': os.path.join(DB_FOLDER, "chromaDB"),
    'CHROMA_DB_PATH_2': os.path.join(DB_FOLDER, "chromaDB1"),
    'CHROMA_DB_PATH_3': os.path.join(DB_FOLDER, "DB1"),
    'CHROMA_DB_PATH_4': os.path.join(BASE_DIR, "chroma_db"),
    'CHROMA_DB_PATH_5': r"C:\Users\BHAKTI\Downloads\UDB-20260112T064020Z-3-001\UDB"
}

collections_map = {
    'CHROMA_DB_PATH_1': ["EPR-chatbot"],
    'CHROMA_DB_PATH_2': ["EPRChatbot-1"],
    'CHROMA_DB_PATH_3': ["FinalDB"],
    'CHROMA_DB_PATH_4': ["pdf_docs"],
    'CHROMA_DB_PATH_5': ["Updated_DB"]
}

print("=" * 80)
print("DATABASE VERIFICATION")
print("=" * 80)

for name, path in paths.items():
    print(f"\n{name}:")
    print(f"  Path: {path}")
    print(f"  Exists: {os.path.exists(path)}")
    
    try:
        client = chromadb.PersistentClient(path=path)
        collections = client.list_collections()
        
        if collections:
            print(f"  Collections found: {[c.name for c in collections]}")
            for c in collections:
                print(f"    - {c.name}: {c.count()} documents")
                
                # Check if expected collection exists
                expected = collections_map.get(name, [])
                if c.name in expected:
                    print(f"      ✅ Expected collection found")
                    
                    # Test query
                    try:
                        result = c.query(query_texts=["EPR"], n_results=1)
                        if result['documents'][0]:
                            print(f"      ✅ Query test passed")
                    except Exception as e:
                        print(f"      ❌ Query test failed: {e}")
        else:
            print(f"  ❌ No collections found")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 80)
print("UDB PATH CHECK (for timeline queries 2024-25, 2025-26)")
print("=" * 80)
udb_path = r"C:\Users\BHAKTI\Downloads\UDB-20260112T064020Z-3-001\UDB"
print(f"UDB Path: {udb_path}")
print(f"Exists: {os.path.exists(udb_path)}")

try:
    client = chromadb.PersistentClient(path=udb_path)
    collections = client.list_collections()
    if collections:
        for c in collections:
            print(f"  {c.name}: {c.count()} documents")
            # Test timeline query
            try:
                result = c.query(query_texts=["2024-25 timeline"], n_results=1)
                if result['documents'][0]:
                    print(f"    ✅ Has timeline data")
                    print(f"    Sample: {result['documents'][0][0][:200]}...")
            except Exception as e:
                print(f"    ❌ Timeline query failed: {e}")
    else:
        print("  ❌ No collections in UDB")
except Exception as e:
    print(f"  ❌ Error: {e}")
