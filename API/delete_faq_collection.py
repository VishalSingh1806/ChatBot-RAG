import chromadb
from config import CHROMA_DB_PATH

def delete_faq_collection():
    """Delete only the FAQ collection, keeping PDF embeddings"""
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        # Delete FAQ collection
        client.delete_collection(name="epr_faqs")
        print("✅ Deleted 'epr_faqs' collection successfully")
    except Exception as e:
        print(f"❌ Error deleting FAQ collection: {e}")
    
    # List remaining collections
    try:
        collections = client.list_collections()
        print(f"\n📋 Remaining collections:")
        for collection in collections:
            print(f"  - {collection.name}")
    except Exception as e:
        print(f"Error listing collections: {e}")

if __name__ == "__main__":
    delete_faq_collection()