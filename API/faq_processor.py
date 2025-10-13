import pandas as pd
import chromadb
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from config import CHROMA_DB_PATH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def process_faqs_to_chromadb():
    """Process FAQ CSV and add to ChromaDB for better search"""
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        # Delete existing FAQ collection if it exists
        client.delete_collection("epr_faqs")
    except:
        pass
    
    # Create new FAQ collection
    faq_collection = client.create_collection(
        name="epr_faqs",
        metadata={"description": "EPR FAQ collection for enhanced search"}
    )
    
    # Read FAQ CSV
    df = pd.read_csv('./data/epr_faqs.csv')
    
    documents = []
    metadatas = []
    ids = []
    
    for index, row in df.iterrows():
        # Combine question and answer for better context
        combined_text = f"Q: {row['question']}\nA: {row['answer']}"
        
        documents.append(combined_text)
        metadatas.append({
            'question': row['question'],
            'answer': row['answer'],
            'category': row['category'],
            'priority': row['priority'],
            'keywords': row['keywords'],
            'faq_id': str(row['id'])
        })
        ids.append(f"faq_{row['id']}")
    
    # Generate embeddings and add to collection
    logger.info(f"Processing {len(documents)} FAQs...")
    
    # Add documents in batches
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        faq_collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        
        logger.info(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    
    logger.info("✅ FAQ processing completed!")
    return faq_collection

def search_faqs(query: str, n_results: int = 5):
    """Search FAQs using ChromaDB"""
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        faq_collection = client.get_collection("epr_faqs")
    except:
        logger.error("FAQ collection not found. Run process_faqs_to_chromadb() first.")
        return []
    
    results = faq_collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    faqs = []
    if results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i] if results['distances'] else 0
            
            faqs.append({
                'question': metadata['question'],
                'answer': metadata['answer'],
                'category': metadata['category'],
                'priority': metadata['priority'],
                'confidence': round(1 - distance, 4),
                'faq_id': metadata['faq_id']
            })
    
    return faqs

if __name__ == "__main__":
    # Process FAQs when script is run directly
    process_faqs_to_chromadb()