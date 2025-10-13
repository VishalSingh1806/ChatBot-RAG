import chromadb
import shutil
import os
from sentence_transformers import SentenceTransformer

def integrate_langflow_database():
    """Complete integration of Langflow database with current project"""
    
    print("Integrating Langflow database...")
    
    # Step 1: Stop any running processes and replace database
    langflow_db_folder = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB"
    current_db_folder = "./chroma_db"
    
    try:
        if os.path.exists(current_db_folder):
            shutil.rmtree(current_db_folder)
        shutil.copytree(langflow_db_folder, current_db_folder)
        print("Database replaced successfully")
    except Exception as e:
        print(f"Database replacement failed: {e}")
        return False
    
    # Step 2: Verify database and get collection info
    try:
        client = chromadb.PersistentClient(path=current_db_folder)
        collections = client.list_collections()
        
        print(f"\nFound {len(collections)} collections:")
        for collection in collections:
            count = collection.count()
            print(f"  - {collection.name}: {count} items")
            
        if not collections:
            print("No collections found")
            return False
            
        collection_names = [c.name for c in collections]
        
    except Exception as e:
        print(f"Database verification failed: {e}")
        return False
    
    # Step 3: Test embedding compatibility
    try:
        print("\nTesting embedding compatibility...")
        model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        test_embedding = model.encode(["test query"]).tolist()[0]
        
        # Test query on first collection
        test_collection = client.get_collection(collection_names[0])
        results = test_collection.query(
            query_embeddings=[test_embedding],
            n_results=1
        )
        
        if results['documents'][0]:
            print("Embedding compatibility confirmed (384 dimensions)")
        else:
            print("No results found, but embedding dimensions match")
            
    except Exception as e:
        print(f"Embedding test failed: {e}")
        return False
    
    # Step 4: Update search.py configuration
    search_config = f'''
# Updated configuration for Langflow integration
COLLECTIONS = {collection_names}

# Use sentence-transformers for 384-dimensional embeddings
def generate_query_embedding(query_text):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode([query_text])[0].tolist()
'''
    
    print(f"\nConfiguration for search.py:")
    print(f"   Collections: {collection_names}")
    print(f"   Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384 dims)")
    print(f"   Confidence threshold: 0.2 (very permissive)")
    
    print("\nLangflow database integration completed!")
    print("\nNext steps:")
    print("1. Install: pip install sentence-transformers")
    print("2. Update search.py with sentence-transformers")
    print("3. Restart API server: uvicorn main:app --reload")
    
    return True

if __name__ == "__main__":
    integrate_langflow_database()