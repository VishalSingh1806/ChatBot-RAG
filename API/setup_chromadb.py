import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os

def setup_chromadb():
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="epr_knowledge",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Load data
    df = pd.read_csv("data/knowledge.csv")
    df = df.dropna(subset=["question", "answer"])
    df["question"] = df["question"].astype(str)
    
    # Initialize embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Prepare data for ChromaDB
    documents = df["question"].tolist()
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        metadatas.append({
            "answer": row["answer"],
            "category": row.get("category", ""),
            "intent": row.get("intent", "")
        })
        ids.append(f"doc_{idx}")
    
    # Generate embeddings
    embeddings = model.encode(documents).tolist()
    
    # Add to collection
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Added {len(documents)} documents to ChromaDB")
    return collection

if __name__ == "__main__":
    setup_chromadb()