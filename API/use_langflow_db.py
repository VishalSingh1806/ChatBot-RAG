import chromadb
import shutil
import os

def replace_with_langflow_db():
    """Replace current ChromaDB with Langflow ChromaDB"""
    
    # Paths
    langflow_db_folder = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB"
    current_db_folder = "./chroma_db"
    
    print("🔄 Replacing ChromaDB with Langflow database...")
    
    # Step 1: Remove current database
    if os.path.exists(current_db_folder):
        try:
            shutil.rmtree(current_db_folder)
            print("✓ Deleted current ChromaDB")
        except PermissionError:
            print("❌ ChromaDB is locked. Stop the API server first with Ctrl+C")
            print("Then run this script again.")
            return False
    
    # Step 2: Copy Langflow database
    shutil.copytree(langflow_db_folder, current_db_folder)
    print("✓ Copied Langflow ChromaDB")
    
    # Step 3: Verify the copy
    try:
        client = chromadb.PersistentClient(path=current_db_folder)
        collections = client.list_collections()
        
        print(f"\n📊 Database ready with {len(collections)} collections:")
        for collection in collections:
            count = collection.count()
            print(f"  • {collection.name}: {count} items")
            
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False
    
    print("\n✅ Successfully replaced ChromaDB with Langflow database!")
    return True

if __name__ == "__main__":
    replace_with_langflow_db()