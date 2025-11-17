import chromadb
from config import CHROMA_DB_PATH, COLLECTION_NAME

# Check what collections exist
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collections = client.list_collections()

print(f"ChromaDB Path: {CHROMA_DB_PATH}")
print(f"Expected Collection: {COLLECTION_NAME}")
print(f"Available Collections: {[c.name for c in collections]}")

for collection in collections:
    print(f"\nCollection: {collection.name}")
    print(f"  Count: {collection.count()}")
    if collection.count() > 0:
        # Get a sample document
        sample = collection.peek(limit=1)
        if sample['documents']:
            print(f"  Sample doc: {sample['documents'][0][:100]}...")