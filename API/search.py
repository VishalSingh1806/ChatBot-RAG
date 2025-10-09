import chromadb
from sentence_transformers import SentenceTransformer
import os

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./chroma_db")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Collection names
COLLECTIONS = ["producer", "importer", "branc_owner", "genereal"]

def get_collections():
    """Get all available collections"""
    collections = {}
    for collection_name in COLLECTIONS:
        try:
            collections[collection_name] = client.get_collection(name=collection_name)
        except Exception as e:
            print(f"Collection '{collection_name}' not found: {e}")
    
    if not collections:
        print("No collections found. Run gemini_pdf_processor.py first.")
    
    return collections

def find_best_answer(user_query: str) -> dict:
    collections = get_collections()
    if not collections:
        return {
            "answer": "Database not ready. Please process PDFs first using gemini_pdf_processor.py.",
            "suggestions": []
        }
    
    all_results = []
    
    # Query all collections
    for collection_name, collection in collections.items():
        try:
            results = collection.query(
                query_texts=[user_query],
                n_results=2  # Get 2 results from each collection
            )
            
            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    all_results.append({
                        'document': doc,
                        'distance': results['distances'][0][i] if results['distances'] else 0,
                        'collection': collection_name,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    })
        except Exception as e:
            print(f"Error querying collection '{collection_name}': {e}")
    
    if not all_results:
        return {
            "answer": "I don't have information about that topic.",
            "suggestions": []
        }
    
    # Sort by distance (lower is better)
    all_results.sort(key=lambda x: x['distance'])
    
    # Get main answer and suggestions
    answer = all_results[0]['document']  # Best match as answer
    suggestions = [result['document'] for result in all_results[1:4]]  # Next 3 as suggestions
    
    return {
        "answer": answer,
        "suggestions": suggestions
    }
