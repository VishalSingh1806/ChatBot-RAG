import chromadb

db_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\API\chroma_db"

print(f"Checking: {db_path}")

try:
    client = chromadb.PersistentClient(path=db_path)
    collections = client.list_collections()
    
    print(f"Collections found: {len(collections)}")
    
    for coll in collections:
        count = coll.count()
        print(f"  - {coll.name}: {count} documents")
        
except Exception as e:
    print(f"Error: {e}")
