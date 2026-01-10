import chromadb
import os

db_paths = [
    r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\API\chroma_db\drive-download-20260108T065146Z-3-001\UDB\Updated_DB",
    r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\API\chroma_db\drive-download-20260108T065146Z-3-001\Updated_DB\Updated_DB"
]

for db_path in db_paths:
    print(f"\n{'='*80}")
    print(f"Checking: {db_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(db_path):
        print("Path does not exist")
        continue
    
    print("Path exists")
    
    # Check for chroma.sqlite3
    sqlite_path = os.path.join(db_path, "chroma.sqlite3")
    if os.path.exists(sqlite_path):
        size = os.path.getsize(sqlite_path)
        print(f"chroma.sqlite3 found, size: {size} bytes")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        print(f"Collections found: {len(collections)}")
        
        for coll in collections:
            print(f"  - {coll.name}: {coll.count()} documents")
            
    except Exception as e:
        print(f"Error: {e}")
