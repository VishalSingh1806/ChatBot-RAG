import chromadb
import json
import pandas as pd
from typing import List, Dict

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./chroma_db")

def import_from_json(json_file_path: str):
    """Import embeddings from JSON file"""
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Create collections
    collections = {}
    for collection_name in ["producer", "importer", "branc_owner", "general"]:
        collections[collection_name] = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    # Import data (adjust based on your JSON structure)
    for item in data:
        collection_name = item.get('collection', 'general')
        collection = collections[collection_name]
        
        collection.add(
            embeddings=[item['embedding']],
            documents=[item['text']],
            metadatas=[item.get('metadata', {})],
            ids=[item['id']]
        )

def import_from_csv(csv_file_path: str):
    """Import embeddings from CSV file"""
    df = pd.read_csv(csv_file_path)
    
    # Create collections
    collections = {}
    for collection_name in ["producer", "importer", "branc_owner", "general"]:
        collections[collection_name] = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    # Import data (adjust column names based on your CSV)
    for _, row in df.iterrows():
        collection_name = row.get('collection', 'general')
        collection = collections[collection_name]
        
        # Convert embedding string to list if needed
        embedding = eval(row['embedding']) if isinstance(row['embedding'], str) else row['embedding']
        
        collection.add(
            embeddings=[embedding],
            documents=[row['text']],
            metadatas=[{'source': row.get('source', 'unknown')}],
            ids=[row['id']]
        )

def import_from_chromadb(source_db_path: str):
    """Import from another ChromaDB instance"""
    source_client = chromadb.PersistentClient(path=source_db_path)
    
    for collection_name in ["producer", "importer", "branc_owner", "general"]:
        try:
            # Get source collection
            source_collection = source_client.get_collection(collection_name)
            
            # Create target collection
            target_collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Get all data from source
            results = source_collection.get(include=['embeddings', 'documents', 'metadatas'])
            
            # Add to target
            if results['ids']:
                target_collection.add(
                    embeddings=results['embeddings'],
                    documents=results['documents'],
                    metadatas=results['metadatas'],
                    ids=results['ids']
                )
                print(f"✓ Imported {len(results['ids'])} items to {collection_name}")
        
        except Exception as e:
            print(f"Error importing {collection_name}: {e}")

def check_langflow_collections(source_db_path: str):
    """Check what collections exist in Langflow ChromaDB"""
    source_client = chromadb.PersistentClient(path=source_db_path)
    collections = source_client.list_collections()
    
    print(f"Found {len(collections)} collections in Langflow ChromaDB:")
    for collection in collections:
        count = collection.count()
        print(f"  • {collection.name}: {count} items")
    
    return [c.name for c in collections]

def import_all_langflow_collections(source_db_path: str):
    """Import all collections from Langflow ChromaDB"""
    source_client = chromadb.PersistentClient(path=source_db_path)
    collections = source_client.list_collections()
    
    for source_collection_obj in collections:
        collection_name = source_collection_obj.name
        try:
            # Get source collection
            source_collection = source_client.get_collection(collection_name)
            
            # Create target collection
            target_collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Get all data from source
            results = source_collection.get(include=['embeddings', 'documents', 'metadatas'])
            
            # Add to target
            if results['ids']:
                target_collection.add(
                    embeddings=results['embeddings'],
                    documents=results['documents'],
                    metadatas=results['metadatas'],
                    ids=results['ids']
                )
                print(f"✓ Imported {len(results['ids'])} items to {collection_name}")
        
        except Exception as e:
            print(f"Error importing {collection_name}: {e}")

if __name__ == "__main__":
    # Import from your Langflow ChromaDB (folder containing chroma.sqlite3)
    langflow_db_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\chromaDB"
    
    print("Checking Langflow ChromaDB collections...")
    collection_names = check_langflow_collections(langflow_db_path)
    
    if collection_names:
        print("\nStarting import from Langflow ChromaDB...")
        import_all_langflow_collections(langflow_db_path)
        print("Import completed!")
    else:
        print("No collections found in Langflow ChromaDB")