import chromadb
from chromadb.utils import embedding_functions
import os

# Test UDB database access with correct embedding function
udb_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\UDB\Updated_DB"

try:
    print(f"Connecting to UDB at: {udb_path}")
    
    # Use sentence-transformers embedding function
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"  # This produces 384-dim embeddings
    )
    
    client = chromadb.PersistentClient(path=udb_path)
    
    # List all collections
    collections = client.list_collections()
    print(f"Available collections: {[col.name for col in collections]}")
    
    # Access the updated_db collection with correct embedding function
    try:
        collection = client.get_collection(
            name="updated_db",
            embedding_function=sentence_transformer_ef
        )
        count = collection.count()
        print(f"Collection 'updated_db' found with {count} documents")
        
        # Test query for timeline data
        results = collection.query(
            query_texts=["plastic waste EPR annual report filing deadline for 2024-25"],
            n_results=3
        )
        
        if results['documents'] and results['documents'][0]:
            print(f"Sample timeline data from 'updated_db':")
            for i, doc in enumerate(results['documents'][0][:2]):
                print(f"  {i+1}. {doc[:200]}...")
        else:
            print("No timeline data found")
            
    except Exception as e:
        print(f"Error accessing collection: {e}")
    
except Exception as e:
    print(f"Failed to connect to UDB: {e}")