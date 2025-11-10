import os
import chromadb
import google.generativeai as genai
import pdfplumber
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

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
    client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        client.delete_collection("pdf_docs")
    except:
        pass
    
    collection = client.create_collection(
        name="pdf_docs",
        metadata={"hnsw:space": "cosine"}
    )
    
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
    
    if all_chunks:
        print(f"Generating Gemini embeddings for {len(all_chunks)} chunks...")
        embeddings = []
        for chunk in all_chunks:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=chunk,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        
        collection.add(
            embeddings=embeddings,
            documents=all_chunks,
            metadatas=all_metadata,
            ids=all_ids
        )
        
        print(f"Stored {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
        print("Database ready!")

if __name__ == "__main__":
    folder_path = os.getenv("PDF_DOCUMENTS_PATH", "../fwdplasticwastemanagementrules")
    
    if not os.path.isabs(folder_path):
        folder_path = os.path.abspath(folder_path)
    
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        print("Please set PDF_DOCUMENTS_PATH in .env file")
        exit()
    
    print(f"Processing PDFs from: {folder_path}")
    process_folder_pdfs(folder_path)
