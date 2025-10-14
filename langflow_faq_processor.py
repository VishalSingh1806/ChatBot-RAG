from langflow import CustomComponent
from langflow.field_typing import Data
import pandas as pd
import chromadb
from typing import List

class FAQProcessor(CustomComponent):
    display_name = "FAQ CSV to ChromaDB"
    description = "Process FAQ CSV and store embeddings in ChromaDB"
    
    def build_config(self):
        return {
            "csv_path": {
                "display_name": "CSV File Path",
                "field_type": "str",
                "required": True,
                "placeholder": "./data/epr_faqs.csv"
            },
            "collection_name": {
                "display_name": "Collection Name", 
                "field_type": "str",
                "value": "epr_faqs"
            },
            "chroma_path": {
                "display_name": "ChromaDB Path",
                "field_type": "str", 
                "value": "./chroma_db"
            }
        }
    
    def build(self, csv_path: str, collection_name: str, chroma_path: str) -> Data:
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            client.delete_collection(collection_name)
        except:
            pass
            
        collection = client.create_collection(name=collection_name)
        
        # Process FAQs
        documents = []
        metadatas = []
        ids = []
        
        for _, row in df.iterrows():
            combined_text = f"Q: {row['question']}\nA: {row['answer']}"
            documents.append(combined_text)
            metadatas.append({
                'question': str(row['question']),
                'answer': str(row['answer']),
                'category': str(row.get('category', '')),
                'faq_id': str(row.get('id', len(ids)))
            })
            ids.append(f"faq_{len(ids)}")
        
        # Add to ChromaDB
        collection.add(
            documents=documents,
            metadatas=metadatas, 
            ids=ids
        )
        
        return Data(value=f"Processed {len(documents)} FAQs into ChromaDB")