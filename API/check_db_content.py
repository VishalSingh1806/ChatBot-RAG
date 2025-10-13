import chromadb
from config import CHROMA_DB_PATH

def check_database_content():
    """Check what's actually in the database"""
    
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("EPR-chatbot")
    
    # Get first 5 documents to see content
    sample = collection.get(limit=5, include=['documents', 'metadatas'])
    
    print(f"Total items: {collection.count()}")
    print("\nSample content:")
    for i, doc in enumerate(sample['documents']):
        print(f"\n--- Document {i+1} ---")
        print(f"Content: {doc[:200]}...")
        if sample['metadatas'] and sample['metadatas'][i]:
            print(f"Metadata: {sample['metadatas'][i]}")

if __name__ == "__main__":
    check_database_content()