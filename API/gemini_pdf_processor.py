import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types
import google.generativeai as genai_legacy
import chromadb
import pdfplumber

# Load environment variables
load_dotenv()

# Set up Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize Gemini client for classification using service account
client = genai.Client(
    vertexai=True,
    project=os.getenv("GOOGLE_PROJECT_ID", "epr-chatbot-443706"),
    location=os.getenv("GOOGLE_LOCATION", "us-central1"),
)

model = "gemini-2.0-flash-exp"

# Initialize ChromaDB client
from config import CHROMA_DB_PATH
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Initialize legacy Gemini for embeddings using service account
# Note: google.generativeai will automatically use GOOGLE_APPLICATION_CREDENTIALS

# Collection names - FIXED: genereal -> general
COLLECTIONS = ["producer", "importer", "branc_owner", "general"]


def translate_hindi_to_english(text: str) -> str:
    """Translate Hindi text to English using Gemini."""
    # Check if text contains Hindi characters
    if not re.search(r'[\u0900-\u097F]', text):
        return text
    
    try:
        prompt = f"Translate the following Hindi/Devanagari text to English. Keep English text as-is. Only translate the Hindi portions:\n\n{text[:1000]}"
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=512,
        )
        
        response = ""
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            response += chunk.text
        
        return response.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def clean_text(text: str) -> str:
    """Clean and normalize extracted text, translate Hindi to English."""
    # First translate Hindi to English
    text = translate_hindi_to_english(text)
    
    # Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common OCR artifacts
    text = re.sub(r'[€£¥]', '', text)
    text = re.sub(r'[xX]{2,}', '', text)  # Remove repeated x's from OCR
    text = re.sub(r'[^a-zA-Z0-9\s.,;:!?()\-/]', '', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
    
    # Remove standalone single characters
    text = re.sub(r'\b[a-zA-Z]\b', '', text)
    
    # Keep lines with substantial content
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        english_chars = len(re.findall(r'[a-zA-Z]', line))
        if english_chars > 5:  # At least 5 English characters
            clean_lines.append(line)
    
    return ' '.join(clean_lines).strip()

def extract_pdf_text(pdf_path: str) -> str:
    """Extract and clean text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Clean the extracted text
        cleaned_text = clean_text(text)
        return cleaned_text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks with sentence boundaries."""
    chunks = []
    
    # Split into sentences while preserving sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if adding this sentence exceeds chunk size
        if len(current_chunk + " " + sentence) <= chunk_size:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            # Save current chunk if it's substantial
            if len(current_chunk.strip()) > 50:
                chunks.append(current_chunk.strip())
            
            # Start new chunk with current sentence
            current_chunk = sentence
    
    # Add the last chunk
    if len(current_chunk.strip()) > 50:
        chunks.append(current_chunk.strip())
    
    # Apply overlap by creating overlapping chunks
    if len(chunks) > 1:
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            overlapped_chunks.append(chunk)
            
            # Create overlap with next chunk if exists
            if i < len(chunks) - 1:
                # Take last part of current chunk and first part of next chunk
                current_words = chunk.split()
                next_words = chunks[i + 1].split()
                
                if len(current_words) > 10 and len(next_words) > 10:
                    overlap_chunk = " ".join(current_words[-5:] + next_words[:5])
                    if len(overlap_chunk) > 50:
                        overlapped_chunks.append(overlap_chunk)
        
        return overlapped_chunks
    
    return chunks


def classify_pdf_with_gemini(pdf_text: str, pdf_filename: str) -> Tuple[str, str]:
    """
    Use Gemini to understand PDF content and classify it into one of the collections.
    Returns: (collection_name, summary)
    """
    # Limit text for classification to avoid token limits
    sample_text = pdf_text[:5000] if len(pdf_text) > 5000 else pdf_text

    prompt_text = f"""You are an expert document classifier for EPR (Extended Producer Responsibility) and plastic waste management documents.

Document Filename: {pdf_filename}

Document Content (first 5000 characters):
---
{sample_text}
---

Your task is to:
1. Analyze this document and classify it into ONE of these categories:
   - "producer": Documents related to producers, manufacturers, product manufacturing, production processes
   - "importer": Documents about imports, import regulations, customs, foreign trade, importers
   - "branc_owner": Documents about brand owners, brands, brand management, trademark holders
   - "general": General EPR information, rules, regulations, compliance, or any other documents that don't fit the above categories

2. Provide a brief 2-3 sentence summary of what this document is about.

Respond in EXACTLY this format:
CATEGORY: [one of: producer, importer, branc_owner, general]
SUMMARY: [your 2-3 sentence summary]

Do not include any other text or explanation."""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
    ]

    config = types.GenerateContentConfig(
        temperature=0.3,  # Lower temperature for more consistent classification
        top_p=0.95,
        max_output_tokens=512,
    )

    try:
        response = ""
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            response += chunk.text

        # Parse response - FIXED: Better mapping logic
        lines = response.strip().split('\n')
        category = "general"  # Default fallback
        summary = "Document content summary not available."

        for line in lines:
            if line.startswith("CATEGORY:"):
                cat = line.replace("CATEGORY:", "").strip().lower()
                # Map to valid collection names
                if cat in ["producer"]:
                    category = "producer"
                elif cat in ["importer"]:
                    category = "importer"
                elif cat in ["branc_owner", "brand_owner"]:
                    category = "branc_owner"
                else:
                    category = "general"
            elif line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()

        return category, summary

    except Exception as e:
        print(f"Error classifying PDF with Gemini: {e}")
        return "general", "Classification failed - defaulted to general category."


def setup_collections():
    """Create or get all required ChromaDB collections."""
    collections = {}

    for collection_name in COLLECTIONS:
        try:
            # Delete existing collection if it exists (to handle dimension mismatch)
            try:
                chroma_client.delete_collection(name=collection_name)
                print(f"✓ Deleted existing '{collection_name}' collection")
            except:
                pass  # Collection doesn't exist, which is fine
            
            # Create new collection
            collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            collections[collection_name] = collection
            print(f"✓ Collection '{collection_name}' ready")
        except Exception as e:
            print(f"Error setting up collection '{collection_name}': {e}")

    return collections


def process_pdf_to_collection(
    pdf_path: str,
    pdf_filename: str,
    collections: Dict,
    pdf_index: int
) -> Dict[str, int]:
    """
    Process a single PDF: classify it, chunk it, embed it, and store in appropriate collection.
    Returns: Dictionary with collection name and number of chunks stored.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_filename}")
    print(f"{'='*60}")

    # Step 1: Extract text from PDF
    print("Step 1: Extracting text from PDF...")
    pdf_text = extract_pdf_text(pdf_path)

    if not pdf_text:
        print(f"✗ No text extracted from {pdf_filename}")
        return {"collection": "none", "chunks": 0}

    print(f"✓ Extracted {len(pdf_text)} characters")

    # Step 2: Classify PDF using Gemini
    print("Step 2: Classifying document with Gemini...")
    collection_name, summary = classify_pdf_with_gemini(pdf_text, pdf_filename)
    print(f"✓ Classification: {collection_name.upper()}")
    print(f"✓ Summary: {summary}")

    # Step 3: Chunk the text
    print("Step 3: Chunking text...")
    chunks = chunk_text(pdf_text)
    print(f"✓ Created {len(chunks)} chunks")

    # Step 4: Generate embeddings using Gemini
    print("Step 4: Generating embeddings using Gemini text-embedding-004...")
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        try:
            result = genai_legacy.embed_content(
                model="models/text-embedding-004",
                content=chunk,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{len(chunks)} embeddings")
                
        except Exception as e:
            print(f"Error generating embedding for chunk {i}: {e}")
            # Add zero vector as fallback (text-embedding-004 uses 768 dimensions)
            embeddings.append([0.0] * 768)
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    
    # Safety check - ensure we have embeddings
    if not embeddings:
        print(f"✗ No embeddings generated for {pdf_filename}")
        return {"collection": "none", "chunks": 0}

    # Step 5: Store in appropriate collection
    print(f"Step 5: Storing in '{collection_name}' collection...")
    collection = collections[collection_name]

    # Prepare metadata and IDs
    metadatas = []
    ids = []
    for j, chunk in enumerate(chunks):
        metadatas.append({
            "source": pdf_filename,
            "chunk_id": j,
            "pdf_index": pdf_index,
            "summary": summary,
            "total_chunks": len(chunks)
        })
        ids.append(f"{collection_name}_pdf_{pdf_index}_chunk_{j}")

    # Final validation before storing
    if len(embeddings) != len(chunks):
        print(f"✗ Mismatch: {len(embeddings)} embeddings vs {len(chunks)} chunks")
        return {"collection": "none", "chunks": 0}
    
    try:
        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✓ Stored {len(chunks)} chunks in '{collection_name}' collection")
        return {"collection": collection_name, "chunks": len(chunks)}

    except Exception as e:
        print(f"✗ Error storing chunks: {e}")
        print(f"Debug: embeddings={len(embeddings)}, chunks={len(chunks)}")
        return {"collection": collection_name, "chunks": 0}


def process_pdf_folder(folder_path: str):
    """
    Main function to process all PDFs in a folder.
    """
    print("\n" + "="*60)
    print("GEMINI-POWERED PDF PROCESSOR")
    print("="*60)

    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"✗ Error: Folder not found: {folder_path}")
        return

    # Get all PDF files
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"✗ No PDF files found in: {folder_path}")
        return

    print(f"\n✓ Found {len(pdf_files)} PDF files")
    print(f"✓ Folder: {folder_path}")

    # Setup collections
    print(f"\nSetting up ChromaDB collections...")
    collections = setup_collections()

    if not collections:
        print("✗ Error: Could not setup collections")
        return

    # Process each PDF
    results = {col: 0 for col in COLLECTIONS}
    total_chunks = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(folder_path, pdf_file)

        print(f"\n[{i}/{len(pdf_files)}]")
        result = process_pdf_to_collection(pdf_path, pdf_file, collections, i)

        # Only count if collection is valid (not "none")
        if result["collection"] in results:
            results[result["collection"]] += 1
        total_chunks += result["chunks"]

    # Print summary
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"\nTotal PDFs processed: {len(pdf_files)}")
    print(f"Total chunks created: {total_chunks}")
    print("\nDistribution by collection:")
    for collection_name in COLLECTIONS:
        count = results[collection_name]
        print(f"  • {collection_name.upper()}: {count} PDFs")

    # Test queries on each collection
    print("\n" + "="*60)
    print("TESTING COLLECTIONS")
    print("="*60)

    test_query = "EPR compliance"
    for collection_name in COLLECTIONS:
        collection = collections[collection_name]
        try:
            count = collection.count()
            print(f"\n{collection_name.upper()} collection:")
            print(f"  • Total chunks: {count}")

            if count > 0:
                # Test query using Gemini embeddings
                try:
                    query_result = genai_legacy.embed_content(
                        model="models/text-embedding-004",
                        content=test_query
                    )
                    results = collection.query(
                        query_embeddings=[query_result['embedding']],
                        n_results=min(2, count)
                    )
                    print(f"  • Test query: '{test_query}'")
                    print(f"  • Results found: {len(results['documents'][0])}")
                except Exception as e:
                    print(f"  ✗ Error testing query: {e}")
        except Exception as e:
            print(f"  ✗ Error querying collection: {e}")


def main():
    """Main entry point for the script."""
    # Default path (user should modify this)
    default_folder_path = r"C:\Users\BHAKTI\OneDrive\Desktop\ReCircle\EPR ChatBot\ChatBot-RAG\fwdplasticwastemanagementrules"

    # Check if path is provided as command line argument
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input(f"Enter the path to PDF folder (default: {default_folder_path}): ").strip()
        if not folder_path:
            folder_path = default_folder_path

    # Process the folder
    process_pdf_folder(folder_path)


if __name__ == "__main__":
    main()
