import chromadb
from sentence_transformers import SentenceTransformer
import os

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./chroma_db")
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_collection():
    try:
        return client.get_collection(name="pdf_docs")  # Changed from "epr_knowledge"
    except:
        print("PDF collection not found. Run pdf_processor.py first.")
        return None

def find_best_answer(user_query: str) -> dict:
    collection = get_collection()
    if not collection:
        return {
            "answer": "Database not ready. Please process PDF first.",
            "suggestions": []
        }
    
    # Query ChromaDB
    results = collection.query(
        query_texts=[user_query],
        n_results=4
    )
    
    if not results['documents'][0]:
        return {
            "answer": "I don't have information about that topic.",
            "suggestions": []
        }
    
    # Get main answer and suggestions
    answer = results['documents'][0][0]  # First chunk as answer
    similar_questions = results['documents'][0][1:4]  # Next 3 as suggestions
    
    return {
        "answer": answer,
        "suggestions": similar_questions
    }
