import chromadb

UDB_PATH = r"c:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\UDB"

client = chromadb.PersistentClient(path=UDB_PATH)

print("All collections in UDB:")
collections = client.list_collections()
for col in collections:
    print(f"- {col.name}: {col.count()} documents")
