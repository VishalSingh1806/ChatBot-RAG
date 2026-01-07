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

# Analyze UDB data for year mappings
udb_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\Updated_DB"

try:
    client = chromadb.PersistentClient(path=udb_path)
    collection = client.get_collection(
        name="updated_db",
        embedding_function=GeminiEmbeddingFunction()
    )
    
    print("=== ANALYZING UDB DATA FOR YEAR MAPPINGS ===\n")
    
    # Get all documents to analyze
    all_results = collection.get()
    
    print(f"Total documents: {len(all_results['documents'])}\n")
    
    # Analyze each document for year information
    for i, doc in enumerate(all_results['documents']):
        print(f"Document {i+1}:")
        print(f"Content: {doc}")
        print("---\n")
        
        # Look for year patterns
        if '2024' in doc or '2025' in doc or '2026' in doc:
            print(f"*** CONTAINS YEAR INFO ***")
            if 'FY 202425' in doc or '2024-25' in doc or '20242025' in doc:
                print("-> Contains 2024-25 info")
            if 'FY 202526' in doc or '2025-26' in doc or '20252026' in doc:
                print("-> Contains 2025-26 info")
            if '31 January 2026' in doc:
                print("-> Contains deadline: 31 January 2026")
            print("---\n")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()