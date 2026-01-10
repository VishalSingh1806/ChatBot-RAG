import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

UDB_PATH = r"c:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\UDB"

client = chromadb.PersistentClient(path=UDB_PATH)
collection = client.get_collection(name="Updated_DB")

print(f"Total documents in UDB: {collection.count()}\n")

# Test query
query = "What is annual report filing date for year 2024-25"
print(f"Query: {query}\n")

# Generate embedding
result = genai.embed_content(
    model="models/text-embedding-004",
    content=query,
    task_type="retrieval_query"
)
query_embedding = result['embedding']

# Search
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

print("Search Results:")
print("="*80)
for i, doc in enumerate(results['documents'][0]):
    distance = results['distances'][0][i]
    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
    print(f"\nResult {i+1}:")
    print(f"Distance: {distance:.4f}")
    print(f"Metadata: {metadata}")
    print(f"Document: {doc}")
    print("-"*80)
