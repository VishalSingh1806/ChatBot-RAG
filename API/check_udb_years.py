import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv
from chromadb import EmbeddingFunction

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        embeddings = []
        for text in input:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text
            )
            embeddings.append(result['embedding'])
        return embeddings

# Test UDB for different years
udb_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\Updated_DB"

try:
    client = chromadb.PersistentClient(path=udb_path)
    collection = client.get_collection(
        name="updated_db",
        embedding_function=GeminiEmbeddingFunction()
    )
    
    print(f"Collection has {collection.count()} documents")
    
    # Test year-specific queries
    year_queries = [
        "2024-25 deadline",
        "2025-26 deadline", 
        "2026-27 deadline",
        "filing deadline 2024-25",
        "filing deadline 2025-26",
        "annual report 2024-25",
        "annual report 2025-26"
    ]
    
    for query in year_queries:
        print(f"\n=== Query: '{query}' ===")
        results = collection.query(
            query_texts=[query],
            n_results=2
        )
        
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                print(f"Result {i+1}: {doc}")
                print("---")
        else:
            print("No results found")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()