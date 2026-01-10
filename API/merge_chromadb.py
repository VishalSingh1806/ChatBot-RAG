"""
ChromaDB Merger with Gemini-based Deduplication

This script merges 3 ChromaDB databases into one, using Gemini API to detect
and eliminate duplicate content based on semantic similarity.

Databases to merge:
1. chromaDB (collection: EPR-chatbot)
2. chromaDB1 (collection: EPRChatbot-1)
3. DB1 (collection: FinalDB)

Output: merged_chromadb (collection: EPR-Merged)
"""

import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Set
import hashlib
from tqdm import tqdm
import json

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Database paths from config
CHROMA_DB_PATH_1 = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB"
CHROMA_DB_PATH_2 = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB1"
CHROMA_DB_PATH_3 = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\DB1"

# Output merged database path
MERGED_DB_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\merged_chromadb"

# Collections in each database
COLLECTIONS = {
    CHROMA_DB_PATH_1: "EPR-chatbot",
    CHROMA_DB_PATH_2: "EPRChatbot-1",
    CHROMA_DB_PATH_3: "FinalDB"
}

MERGED_COLLECTION_NAME = "EPR-Merged"

# Similarity threshold for considering documents as duplicates (0-1, higher = more similar)
SIMILARITY_THRESHOLD = 0.95


def compute_text_hash(text: str) -> str:
    """Compute MD5 hash of text for quick exact duplicate detection"""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def get_gemini_embedding(text: str) -> List[float]:
    """Get embedding from Gemini API"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    import numpy as np
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def load_all_documents() -> List[Dict]:
    """Load all documents from all three databases"""
    print("\n" + "="*60)
    print("STEP 1: Loading documents from all databases")
    print("="*60)

    all_docs = []

    for db_path, collection_name in COLLECTIONS.items():
        try:
            print(f"\n📂 Loading from: {db_path}")
            print(f"   Collection: {collection_name}")

            client = chromadb.PersistentClient(path=db_path)
            collection = client.get_collection(name=collection_name)

            # Get all documents
            results = collection.get(include=['documents', 'metadatas', 'embeddings'])

            count = len(results['documents'])
            print(f"   ✅ Found {count} documents")

            # Store documents with source info
            for i in range(count):
                doc_data = {
                    'id': results['ids'][i] if 'ids' in results else f"doc_{i}",
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i] if results['metadatas'] and i < len(results['metadatas']) else {},
                    'embedding': results['embeddings'][i] if results['embeddings'] and i < len(results['embeddings']) else None,
                    'source_db': db_path,
                    'source_collection': collection_name
                }
                all_docs.append(doc_data)

        except Exception as e:
            print(f"   ❌ Error loading {db_path}: {e}")
            continue

    print(f"\n📊 Total documents loaded: {len(all_docs)}")
    return all_docs


def deduplicate_documents(documents: List[Dict]) -> List[Dict]:
    """
    Remove duplicates using a multi-stage approach:
    1. Exact text matching (hash-based)
    2. High semantic similarity (embedding-based with Gemini)
    """
    print("\n" + "="*60)
    print("STEP 2: Deduplicating documents")
    print("="*60)

    # Stage 1: Remove exact duplicates using hash
    print("\n🔍 Stage 1: Removing exact text duplicates...")
    seen_hashes: Set[str] = set()
    unique_docs = []
    exact_duplicates = 0

    for doc in tqdm(documents, desc="Checking exact duplicates"):
        text_hash = compute_text_hash(doc['document'])
        if text_hash not in seen_hashes:
            seen_hashes.add(text_hash)
            unique_docs.append(doc)
        else:
            exact_duplicates += 1

    print(f"   ✅ Removed {exact_duplicates} exact duplicates")
    print(f"   📊 Remaining documents: {len(unique_docs)}")

    # Stage 2: Remove semantic duplicates using embeddings
    print("\n🔍 Stage 2: Removing semantic duplicates (using Gemini)...")
    print(f"   Similarity threshold: {SIMILARITY_THRESHOLD}")

    final_docs = []
    semantic_duplicates = 0

    for i, doc in enumerate(tqdm(unique_docs, desc="Checking semantic duplicates")):
        is_duplicate = False

        # Get or generate embedding for current document
        if doc['embedding'] is None:
            print(f"\n   Generating embedding for doc {i+1}...")
            doc['embedding'] = get_gemini_embedding(doc['document'])
            if doc['embedding'] is None:
                # If embedding generation fails, keep the document to be safe
                final_docs.append(doc)
                continue

        # Compare with already accepted documents
        for existing_doc in final_docs:
            if existing_doc['embedding'] is None:
                continue

            similarity = cosine_similarity(doc['embedding'], existing_doc['embedding'])

            if similarity >= SIMILARITY_THRESHOLD:
                is_duplicate = True
                semantic_duplicates += 1

                # Log the duplicate for review
                if semantic_duplicates <= 5:  # Show first 5 duplicates
                    print(f"\n   🔄 Found semantic duplicate (similarity: {similarity:.3f})")
                    print(f"      Original: {existing_doc['document'][:100]}...")
                    print(f"      Duplicate: {doc['document'][:100]}...")
                break

        if not is_duplicate:
            final_docs.append(doc)

    print(f"\n   ✅ Removed {semantic_duplicates} semantic duplicates")
    print(f"   📊 Final unique documents: {len(final_docs)}")

    return final_docs


def create_merged_database(documents: List[Dict]):
    """Create the merged ChromaDB with deduplicated documents"""
    print("\n" + "="*60)
    print("STEP 3: Creating merged database")
    print("="*60)

    print(f"\n📁 Output path: {MERGED_DB_PATH}")
    print(f"   Collection name: {MERGED_COLLECTION_NAME}")

    # Ensure output directory exists
    os.makedirs(MERGED_DB_PATH, exist_ok=True)

    # Create new ChromaDB client
    client = chromadb.PersistentClient(path=MERGED_DB_PATH)

    # Delete existing collection if it exists
    try:
        client.delete_collection(name=MERGED_COLLECTION_NAME)
        print("   ♻️  Deleted existing collection")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=MERGED_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # Prepare data for insertion
    ids = []
    docs = []
    embeddings = []
    metadatas = []

    print("\n📝 Preparing documents for insertion...")
    for i, doc in enumerate(tqdm(documents, desc="Processing documents")):
        # Generate new ID
        new_id = f"merged_doc_{i}"
        ids.append(new_id)

        # Add document text
        docs.append(doc['document'])

        # Get or generate embedding
        if doc['embedding'] is not None:
            embeddings.append(doc['embedding'])
        else:
            print(f"\n   Generating missing embedding for doc {i}...")
            embedding = get_gemini_embedding(doc['document'])
            if embedding:
                embeddings.append(embedding)
            else:
                # Skip this document if embedding fails
                print(f"   ⚠️  Skipping doc {i} - embedding generation failed")
                ids.pop()
                docs.pop()
                continue

        # Enhanced metadata with source tracking
        metadata = doc['metadata'].copy()
        metadata['source_db'] = doc['source_db'].split('\\')[-1]  # Just the DB name
        metadata['source_collection'] = doc['source_collection']
        metadata['original_id'] = doc['id']
        metadatas.append(metadata)

    # Insert into ChromaDB in batches
    print("\n💾 Inserting documents into merged database...")
    BATCH_SIZE = 100

    for i in range(0, len(ids), BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, len(ids))

        collection.add(
            ids=ids[i:batch_end],
            documents=docs[i:batch_end],
            embeddings=embeddings[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        print(f"   Inserted batch {i//BATCH_SIZE + 1}: {batch_end}/{len(ids)} documents")

    print(f"\n✅ Successfully created merged database!")
    print(f"   Total documents: {len(ids)}")

    return collection


def generate_merge_report(original_count: int, final_count: int, output_path: str):
    """Generate a detailed merge report"""
    print("\n" + "="*60)
    print("STEP 4: Generating merge report")
    print("="*60)

    report = {
        "original_documents": original_count,
        "final_documents": final_count,
        "duplicates_removed": original_count - final_count,
        "deduplication_rate": f"{((original_count - final_count) / original_count * 100):.2f}%",
        "source_databases": list(COLLECTIONS.keys()),
        "merged_database_path": MERGED_DB_PATH,
        "collection_name": MERGED_COLLECTION_NAME,
        "similarity_threshold": SIMILARITY_THRESHOLD
    }

    report_file = os.path.join(output_path, "merge_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Merge Summary:")
    print(f"   Original documents: {original_count}")
    print(f"   Final documents: {final_count}")
    print(f"   Duplicates removed: {original_count - final_count}")
    print(f"   Deduplication rate: {report['deduplication_rate']}")
    print(f"\n📄 Report saved to: {report_file}")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("   ChromaDB Merger with Gemini Deduplication")
    print("="*60)

    # Step 1: Load all documents
    all_documents = load_all_documents()
    original_count = len(all_documents)

    if original_count == 0:
        print("\n❌ No documents found in any database!")
        return

    # Step 2: Deduplicate
    unique_documents = deduplicate_documents(all_documents)

    # Step 3: Create merged database
    merged_collection = create_merged_database(unique_documents)

    # Step 4: Generate report
    generate_merge_report(original_count, len(unique_documents), MERGED_DB_PATH)

    print("\n" + "="*60)
    print("✨ Merge completed successfully!")
    print("="*60)
    print(f"\n📂 Merged database location: {MERGED_DB_PATH}")
    print(f"📚 Collection name: {MERGED_COLLECTION_NAME}")
    print(f"📊 Total unique documents: {len(unique_documents)}")
    print("\nYou can now use this merged database in your application!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during merge: {e}")
        import traceback
        traceback.print_exc()
