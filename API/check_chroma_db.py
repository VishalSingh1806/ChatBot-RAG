import chromadb
import os

db_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\API\chroma_db"

print(f"Checking: {db_path}")
print(f"Path exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        print(f"\nCollections found: {len(collections)}")
        
        for coll in collections:
            count = coll.count()
            print(f"\n  Collection: {coll.name}")
            print(f"  Documents: {count}")
            
            if count > 0:
                sample = coll.peek(limit=1)
                if sample and sample.get('documents'):
                    doc_text = sample['documents'][0][:80].replace('\n', ' ')
                    print(f"  Sample: {doc_text}...")
                    
    except Exception as e:
        print(f"Error: {e}")
