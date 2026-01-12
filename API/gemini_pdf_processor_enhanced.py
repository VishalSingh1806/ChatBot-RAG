"""
Enhanced PDF Processor with Temporal Metadata
Adds date, version, and fiscal year metadata to embeddings

Usage:
    python gemini_pdf_processor_enhanced.py
"""
import os
import chromadb
import google.generativeai as genai
import pdfplumber
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


def extract_document_date(filename: str, file_path: str) -> str:
    """
    Extract document date from filename or file metadata

    Patterns recognized:
    - EPR_Rules_2024.pdf -> 2024
    - PWM_Rules_2024-25.pdf -> 2024-25
    - Notification_20240115.pdf -> 2024-01-15
    - Version_v2.0_2024.pdf -> 2024
    """
    # Try to find year in filename
    year_match = re.search(r'(20\d{2})', filename)
    if year_match:
        year = year_match.group(1)

        # Check if it's a fiscal year pattern
        fy_match = re.search(r'(20\d{2}[-_]?\d{2})', filename)
        if fy_match:
            return fy_match.group(1).replace('_', '-')

        # Check for full date pattern YYYYMMDD
        date_match = re.search(r'(20\d{2})(\d{2})(\d{2})', filename)
        if date_match:
            return f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"

        return year

    # Fallback to file modification time
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except:
        return datetime.now().strftime('%Y-%m-%d')


def extract_fiscal_year(filename: str) -> str:
    """
    Extract fiscal year from filename

    Patterns:
    - 2024-25, 2024_25, 202425 -> 2024-25
    - FY2024-25 -> 2024-25
    - 2024 -> 2024-25 (assume current FY)
    """
    # Try FY pattern first
    fy_match = re.search(r'(?:FY)?[_\s]?(20\d{2})[-_]?(20)?(\d{2})', filename, re.IGNORECASE)
    if fy_match:
        year1 = fy_match.group(1)
        year2 = fy_match.group(3)
        return f"{year1}-{year2}"

    # Try simple year
    year_match = re.search(r'(20\d{2})', filename)
    if year_match:
        year = int(year_match.group(1))
        # Assume fiscal year (April to March)
        return f"{year}-{str(year + 1)[-2:]}"

    # Default to current FY
    current_year = datetime.now().year
    current_month = datetime.now().month
    if current_month >= 4:  # April onwards
        return f"{current_year}-{str(current_year + 1)[-2:]}"
    else:
        return f"{current_year - 1}-{str(current_year)[-2:]}"


def extract_version(filename: str) -> str:
    """
    Extract version from filename

    Patterns:
    - v2.0, v2, Version_2.0 -> 2.0
    - _rev3 -> 3.0
    - (2) -> 2.0
    """
    # Try version pattern
    version_match = re.search(r'[vV](?:ersion)?[_\s]?(\d+\.?\d*)', filename)
    if version_match:
        return version_match.group(1)

    # Try revision pattern
    rev_match = re.search(r'[rR]ev[_\s]?(\d+)', filename)
    if rev_match:
        return f"{rev_match.group(1)}.0"

    # Try parentheses pattern
    paren_match = re.search(r'\((\d+)\)', filename)
    if paren_match:
        return f"{paren_match.group(1)}.0"

    return "1.0"


def extract_regulation_type(filename: str) -> str:
    """Extract regulation type from filename"""
    filename_lower = filename.lower()

    if 'pwm' in filename_lower or 'plastic' in filename_lower:
        return 'Plastic_Waste_Management'
    elif 'ewaste' in filename_lower or 'e-waste' in filename_lower:
        return 'E_Waste_Management'
    elif 'battery' in filename_lower:
        return 'Battery_Management'
    elif 'epr' in filename_lower:
        return 'EPR_General'
    elif 'notification' in filename_lower:
        return 'CPCB_Notification'
    elif 'guideline' in filename_lower:
        return 'Guidelines'
    else:
        return 'General'


def chunk_text(text, chunk_size=280, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def extract_pdf_text(pdf_path):
    """Extract text from PDF"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text


def process_folder_pdfs_with_metadata(folder_path, collection_name="pdf_docs_enhanced", db_path="./chroma_db_enhanced"):
    """
    Process PDFs and add comprehensive metadata

    Metadata added:
    - source: PDF filename
    - chunk_id: Chunk number
    - document_date: Date from filename or file metadata
    - embedding_date: Current date (when embedded)
    - fiscal_year: Fiscal year extracted from filename
    - version: Document version
    - regulation_type: Type of regulation
    - is_superseded: False (can be updated later)
    """
    print(f"🚀 Starting enhanced PDF processing...")
    print(f"📁 Folder: {folder_path}")
    print(f"💾 Database: {db_path}")
    print(f"📦 Collection: {collection_name}\n")

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=db_path)

    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
        print(f"🗑️  Deleted existing collection '{collection_name}'")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"✅ Created collection '{collection_name}'\n")

    # Get PDF files
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"❌ No PDF files found in {folder_path}")
        return

    print(f"📄 Found {len(pdf_files)} PDF files\n")

    all_chunks = []
    all_metadata = []
    all_ids = []
    embedding_date = datetime.now().strftime('%Y-%m-%d')

    # Process each PDF
    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(folder_path, pdf_file)

        print(f"[{i+1}/{len(pdf_files)}] Processing: {pdf_file}")

        # Extract metadata from filename
        doc_date = extract_document_date(pdf_file, pdf_path)
        fiscal_year = extract_fiscal_year(pdf_file)
        version = extract_version(pdf_file)
        reg_type = extract_regulation_type(pdf_file)

        print(f"    📅 Document Date: {doc_date}")
        print(f"    📊 Fiscal Year: {fiscal_year}")
        print(f"    🔢 Version: {version}")
        print(f"    📋 Type: {reg_type}")

        # Extract text
        text = extract_pdf_text(pdf_path)
        chunks = chunk_text(text)

        print(f"    ✂️  Created {len(chunks)} chunks")

        # Create metadata for each chunk
        for j, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": pdf_file,
                "chunk_id": j,
                "document_date": doc_date,
                "embedding_date": embedding_date,
                "fiscal_year": fiscal_year,
                "version": version,
                "regulation_type": reg_type,
                "is_superseded": False  # Can be updated later via admin tool
            })
            all_ids.append(f"doc_{i}_{j}")

        print(f"    ✅ Done\n")

    # Generate embeddings
    if all_chunks:
        print(f"\n🔮 Generating Gemini embeddings for {len(all_chunks)} chunks...")
        print("⏳ This may take a few minutes...\n")

        embeddings = []
        for idx, chunk in enumerate(all_chunks):
            if idx % 100 == 0:
                print(f"   Progress: {idx}/{len(all_chunks)} embeddings...")

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=chunk,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])

        # Add to collection
        collection.add(
            embeddings=embeddings,
            documents=all_chunks,
            metadatas=all_metadata,
            ids=all_ids
        )

        print(f"\n✅ Successfully stored {len(all_chunks)} chunks from {len(pdf_files)} PDFs")
        print(f"💾 Database location: {db_path}")
        print(f"📦 Collection name: {collection_name}")
        print(f"\n🎉 Database ready with enhanced metadata!\n")

        # Show sample metadata
        print("📋 Sample metadata:")
        sample_meta = all_metadata[0]
        for key, value in sample_meta.items():
            print(f"   {key}: {value}")


def mark_documents_as_superseded(db_path: str, collection_name: str, fiscal_year: str = None, filename_pattern: str = None):
    """
    Admin tool to mark documents as superseded

    Usage:
        # Mark all FY 2023-24 documents as superseded
        mark_documents_as_superseded("./chroma_db", "pdf_docs", fiscal_year="2023-24")

        # Mark specific documents
        mark_documents_as_superseded("./chroma_db", "pdf_docs", filename_pattern="old_rules")
    """
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name=collection_name)

    # Build filter
    where_filter = {"is_superseded": False}

    if fiscal_year:
        where_filter["fiscal_year"] = fiscal_year

    # Get matching documents
    results = collection.get(
        where=where_filter,
        include=['metadatas']
    )

    # Filter by filename pattern if provided
    ids_to_update = []
    for idx, metadata in enumerate(results['metadatas']):
        if filename_pattern:
            if filename_pattern.lower() in metadata.get('source', '').lower():
                ids_to_update.append(results['ids'][idx])
        else:
            ids_to_update.append(results['ids'][idx])

    if not ids_to_update:
        print(f"❌ No documents found matching criteria")
        return

    # Update documents
    for doc_id in ids_to_update:
        # Get current metadata
        doc = collection.get(ids=[doc_id], include=['metadatas'])
        current_meta = doc['metadatas'][0]

        # Update superseded flag
        current_meta['is_superseded'] = True

        collection.update(
            ids=[doc_id],
            metadatas=[current_meta]
        )

    print(f"✅ Marked {len(ids_to_update)} documents as superseded")
    print(f"   Fiscal Year: {fiscal_year or 'Any'}")
    print(f"   Pattern: {filename_pattern or 'Any'}")


if __name__ == "__main__":
    # Get folder path from environment or use default
    folder_path = os.getenv("PDF_DOCUMENTS_PATH", "../fwdplasticwastemanagementrules")

    if not os.path.isabs(folder_path):
        folder_path = os.path.abspath(folder_path)

    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        print("💡 Please set PDF_DOCUMENTS_PATH in .env file")
        exit()

    # Process PDFs with enhanced metadata
    process_folder_pdfs_with_metadata(
        folder_path=folder_path,
        collection_name="pdf_docs_enhanced",
        db_path="./chroma_db_enhanced"
    )

    print("\n" + "="*80)
    print("Next steps:")
    print("1. Test the enhanced search: python search_with_recency.py")
    print("2. Update main.py to use find_best_answer_with_priority()")
    print("3. Mark old documents as superseded when new regulations arrive")
    print("="*80)
