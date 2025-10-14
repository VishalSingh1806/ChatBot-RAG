"""
Test ChromaDB connection with the new path configuration
"""
import chromadb
from config import CHROMA_DB_PATH, COLLECTIONS

def test_chromadb_connection():
    """Test if ChromaDB connection works with the new path"""
    try:
        print(f"Testing ChromaDB connection...")
        print(f"ChromaDB Path: {CHROMA_DB_PATH}")
        
        # Initialize client
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        print("✅ ChromaDB client initialized successfully")
        
        # List existing collections
        collections = client.list_collections()
        print(f"✅ Found {len(collections)} collections:")
        for collection in collections:
            print(f"   - {collection.name}")
        
        # Try to get the main collection
        for collection_name in COLLECTIONS:
            try:
                collection = client.get_collection(name=collection_name)
                count = collection.count()
                print(f"✅ Collection '{collection_name}' has {count} documents")
            except Exception as e:
                print(f"⚠️ Collection '{collection_name}' not found: {e}")
        
        print("\n🎉 ChromaDB connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

if __name__ == "__main__":
    test_chromadb_connection()