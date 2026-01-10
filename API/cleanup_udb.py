import chromadb

UDB_PATH = r"c:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\UDB"

client = chromadb.PersistentClient(path=UDB_PATH)

# Delete old lowercase collection
try:
    client.delete_collection(name="updated_db")
    print("Deleted old 'updated_db' collection")
except Exception as e:
    print(f"Could not delete: {e}")

# List remaining collections
print("\nRemaining collections:")
collections = client.list_collections()
for col in collections:
    print(f"- {col.name}: {col.count()} documents")
