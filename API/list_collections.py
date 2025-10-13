import chromadb
from config import CHROMA_DB_PATH

def list_collections():
    """List all collections in ChromaDB"""
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        collections = client.list_collections()
        print(f"Available collections:")
        for collection in collections:
            count = collection.count()
            print(f"  - {collection.name}: {count} items")
    except Exception as e:
        print(f"Error listing collections: {e}")

if __name__ == "__main__":
    list_collections()