import chromadb
from config import CHROMA_DB_PATHS, COLLECTIONS
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*70)
print(f"TESTING ALL {len(CHROMA_DB_PATHS)} CHROMADB DATABASES")
print("="*70)

for i, db_path in enumerate(CHROMA_DB_PATHS, 1):
    print(f"\n[DB {i}] Path: {db_path}")
    print("-"*70)
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        all_collections = client.list_collections()
        
        if not all_collections:
            print(f"  ❌ No collections found")
            continue
            
        print(f"  ✅ Found {len(all_collections)} collection(s):")
        
        for collection in all_collections:
            count = collection.count()
            print(f"     - {collection.name}: {count} documents")
            
            # Check if this collection is in our COLLECTIONS config
            expected_collections = COLLECTIONS.get(db_path, [])
            if collection.name in expected_collections:
                print(f"       ✅ Matches config")
            else:
                print(f"       ⚠️  Not in config (expected: {expected_collections})")
                
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
