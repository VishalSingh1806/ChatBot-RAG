"""
Script to verify ChromaDB databases and collections
"""
import chromadb
from config import CHROMA_DB_PATHS, COLLECTIONS
import os

print("=" * 80)
print("CHROMADB DATABASE VERIFICATION")
print("=" * 80)

total_docs = 0

for i, db_path in enumerate(CHROMA_DB_PATHS, 1):
    print(f"\n{'='*80}")
    print(f"DATABASE {i}: {db_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(db_path):
        print(f"[ERROR] PATH DOES NOT EXIST")
        continue
    
    print(f"[OK] Path exists")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        all_collections = client.list_collections()
        
        if not all_collections:
            print(f"[WARNING] No collections found")
            continue
        
        print(f"\n[Collections] Found: {len(all_collections)}")
        
        for collection in all_collections:
            print(f"\n  Collection: {collection.name}")
            
            try:
                count = collection.count()
                total_docs += count
                print(f"  Documents: {count}")
                
                expected_collections = COLLECTIONS.get(db_path, [])
                if collection.name in expected_collections:
                    print(f"  Status: CONFIGURED IN config.py")
                else:
                    print(f"  Status: NOT in config.py (Expected: {expected_collections})")
                
                if count > 0:
                    sample = collection.peek(limit=1)
                    if sample and sample.get('documents'):
                        doc_text = sample['documents'][0][:80].replace('\n', ' ')
                        print(f"  Sample: {doc_text}...")
                        
            except Exception as e:
                print(f"  [ERROR] {str(e)[:100]}")
    
    except Exception as e:
        print(f"[ERROR] {str(e)[:100]}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nTotal databases configured: {len(CHROMA_DB_PATHS)}")
print(f"Total documents across all databases: {total_docs}")
print(f"\nExpected collections per database:")
for db_path, collections in COLLECTIONS.items():
    db_name = os.path.basename(db_path)
    print(f"  {db_name}: {collections}")
