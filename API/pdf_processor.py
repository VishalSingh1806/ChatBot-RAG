import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer
import pdfplumber

def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

def chunk_text(text, chunk_size=280, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks

def process_folder_pdfs(folder_path):
    # Initialize
    client = chromadb.PersistentClient(path="./chroma_db")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Create collection
    try:
        client.delete_collection("pdf_docs")
    except:
        pass
    
    collection = client.create_collection(
        name="pdf_docs",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Get all PDF files from folder
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"Processing {pdf_file}...")
        
        text = extract_pdf_text(pdf_path)
        chunks = chunk_text(text)
        
        for j, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": pdf_file,
                "chunk_id": j
            })
            all_ids.append(f"doc_{i}_{j}")
    
    # Generate embeddings and store
    if all_chunks:
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = model.encode(all_chunks).tolist()
        collection.add(
            embeddings=embeddings,
            documents=all_chunks,
            metadatas=all_metadata,
            ids=all_ids
        )
        
        print(f"✅ Stored {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
        
        # Test query
        results = collection.query(query_texts=["EPR"], n_results=2)
        print(f"Test query found: {len(results['documents'][0])} results")

if __name__ == "__main__":
    folder_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\fwdplasticwastemanagementrules"
    
    if not os.path.exists(folder_path):
        print("Folder not found!")
        exit()
    
    process_folder_pdfs(folder_path)
