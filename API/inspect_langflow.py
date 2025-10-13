import chromadb
import numpy as np

def inspect_langflow_database():
    """Inspect Langflow database to determine embedding dimensions"""
    
    print("Inspecting Langflow database...")
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        
        for collection in collections:
            print(f"\nCollection: {collection.name}")
            print(f"Items: {collection.count()}")
            
            # Get a sample to check embedding dimensions
            sample = collection.get(limit=1, include=['embeddings', 'metadatas'])
            
            if sample['embeddings'] is not None and len(sample['embeddings']) > 0:
                embedding = sample['embeddings'][0]
                print(f"Embedding dimensions: {len(embedding)}")
                print(f"Sample metadata: {sample['metadatas'][0] if sample['metadatas'] else 'None'}")
                
                # Try to determine the model from metadata or embedding characteristics
                if len(embedding) == 768:
                    print("Likely model: sentence-transformers/all-mpnet-base-v2 or similar 768-dim model")
                elif len(embedding) == 384:
                    print("Likely model: sentence-transformers/all-MiniLM-L6-v2 or similar 384-dim model")
                elif len(embedding) == 1536:
                    print("Likely model: OpenAI text-embedding-ada-002")
                else:
                    print(f"Unknown model with {len(embedding)} dimensions")
            else:
                print("No embeddings found in sample")
                
    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_langflow_database()