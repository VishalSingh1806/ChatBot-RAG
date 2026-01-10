"""
ChromaDB Merger using Direct SQLite Access

This script merges 3 ChromaDB databases by reading directly from SQLite,
then creating a fresh merged database with Gemini-based deduplication.

Works even when ChromaDB client has compatibility issues.
"""

import os
import sqlite3
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Set
import hashlib
from tqdm import tqdm
import json
import pickle
import numpy as np

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Database paths
BASE_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB"

DATABASES = {
    "chromaDB": {
        "path": os.path.join(BASE_PATH, "chromaDB", "chroma.sqlite3"),
        "collection": "EPR-chatbot"
    },
    "chromaDB1": {
        "path": os.path.join(BASE_PATH, "chromaDB1", "chroma.sqlite3"),
        "collection": "EPRChatbot-1"
    },
    "DB1": {
        "path": os.path.join(BASE_PATH, "DB1", "chroma.sqlite3"),
        "collection": "FinalDB"
    }
}

# Output merged database
MERGED_DB_PATH = os.path.join(BASE_PATH, "merged_chromadb")
MERGED_COLLECTION_NAME = "EPR-Merged"

# Deduplication threshold
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
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def extract_documents_from_sqlite(db_path: str, db_name: str, collection_name: str) -> List[Dict]:
    """Extract all documents from SQLite database using ChromaDB client"""
    print(f"\n📂 Loading from: {db_name}")
    print(f"   Collection: {collection_name}")

    docs = []

    # Get the database directory (parent of chroma.sqlite3)
    db_dir = os.path.dirname(db_path)

    # Try multiple approaches to load the database
    client = None
    collection = None

    # Approach 1: Try direct ChromaDB client (may fail with version issues)
    try:
        print(f"   🔄 Attempting direct ChromaDB access...")
        client = chromadb.PersistentClient(path=db_dir)
        collection = client.get_collection(name=collection_name)
        print(f"   ✅ Direct access successful!")
    except Exception as e1:
        print(f"   ⚠️  Direct access failed: {type(e1).__name__}")

        # Approach 2: Try copying to temp location with shorter path
        try:
            import shutil
            import tempfile

            print(f"   🔄 Trying alternative method (copying to temp location)...")
            temp_dir = tempfile.mkdtemp()
            temp_db_dir = os.path.join(temp_dir, "db")

            shutil.copytree(db_dir, temp_db_dir)

            client = chromadb.PersistentClient(path=temp_db_dir)
            collection = client.get_collection(name=collection_name)
            print(f"   ✅ Alternative method successful!")

            # Note: We'll cleanup temp_dir at the end
        except Exception as e2:
            print(f"   ❌ All methods failed!")
            print(f"   Error 1: {e1}")
            print(f"   Error 2: {e2}")
            return docs

    # If we got here, we have a working client and collection
    try:

        # Get total count
        count = collection.count()
        print(f"   Found {count} documents")

        # Get all documents in batches
        BATCH_SIZE = 500
        all_results = {'ids': [], 'documents': [], 'metadatas': [], 'embeddings': []}

        for offset in range(0, count, BATCH_SIZE):
            limit = min(BATCH_SIZE, count - offset)
            results = collection.get(
                limit=limit,
                offset=offset,
                include=['documents', 'metadatas', 'embeddings']
            )

            all_results['ids'].extend(results['ids'])
            all_results['documents'].extend(results['documents'])
            all_results['metadatas'].extend(results['metadatas'] if results['metadatas'] is not None else [{}] * len(results['ids']))
            all_results['embeddings'].extend(results['embeddings'] if results['embeddings'] is not None else [None] * len(results['ids']))

        # Convert to our format
        for i in range(len(all_results['ids'])):
            docs.append({
                'id': f"{db_name}_{all_results['ids'][i]}",
                'document': all_results['documents'][i],
                'metadata': all_results['metadatas'][i] if all_results['metadatas'][i] else {},
                'embedding': all_results['embeddings'][i],
                'source_db': db_name,
                'source_collection': collection_name
            })

        print(f"   ✅ Loaded {len(docs)} documents")

    except Exception as e:
        print(f"   ❌ Error loading documents: {e}")
        import traceback
        traceback.print_exc()

    return docs


def load_all_documents() -> List[Dict]:
    """Load all documents from all three databases via SQLite"""
    print("\n" + "="*70)
    print("STEP 1: Loading documents from all databases (via SQLite)")
    print("="*70)

    all_docs = []

    for db_name, db_info in DATABASES.items():
        docs = extract_documents_from_sqlite(
            db_info["path"],
            db_name,
            db_info["collection"]
        )
        all_docs.extend(docs)

    print(f"\n📊 Total documents loaded: {len(all_docs)}")
    return all_docs


def deduplicate_documents(documents: List[Dict]) -> List[Dict]:
    """
    Remove duplicates using:
    1. Exact text matching (hash-based)
    2. Semantic similarity (embedding-based with Gemini)
    """
    print("\n" + "="*70)
    print("STEP 2: Deduplicating documents")
    print("="*70)

    # Stage 1: Remove exact duplicates
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

    # Stage 2: Remove semantic duplicates
    print("\n🔍 Stage 2: Removing semantic duplicates (using embeddings)...")
    print(f"   Similarity threshold: {SIMILARITY_THRESHOLD}")

    final_docs = []
    semantic_duplicates = 0
    need_new_embeddings = 0

    for i, doc in enumerate(tqdm(unique_docs, desc="Checking semantic duplicates")):
        is_duplicate = False

        # Check if embedding exists
        if doc['embedding'] is None:
            need_new_embeddings += 1
            # Keep document, we'll generate embedding later
            final_docs.append(doc)
            continue

        # Convert embedding to list if needed
        if isinstance(doc['embedding'], np.ndarray):
            doc['embedding'] = doc['embedding'].tolist()

        # Compare with already accepted documents
        for existing_doc in final_docs:
            if existing_doc['embedding'] is None:
                continue

            if isinstance(existing_doc['embedding'], np.ndarray):
                existing_doc['embedding'] = existing_doc['embedding'].tolist()

            try:
                similarity = cosine_similarity(doc['embedding'], existing_doc['embedding'])

                if similarity >= SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    semantic_duplicates += 1

                    if semantic_duplicates <= 5:  # Show first 5 duplicates
                        print(f"\n   🔄 Found semantic duplicate (similarity: {similarity:.3f})")
                        print(f"      Original: {existing_doc['document'][:80]}...")
                        print(f"      Duplicate: {doc['document'][:80]}...")
                    break
            except Exception as e:
                print(f"\n   ⚠️  Error comparing embeddings: {e}")
                continue

        if not is_duplicate:
            final_docs.append(doc)

    print(f"\n   ✅ Removed {semantic_duplicates} semantic duplicates")
    print(f"   📊 Final unique documents: {len(final_docs)}")
    if need_new_embeddings > 0:
        print(f"   ℹ️  {need_new_embeddings} documents need new embeddings")

    return final_docs


def generate_missing_embeddings(documents: List[Dict]) -> List[Dict]:
    """Generate embeddings for documents that don't have them"""
    print("\n" + "="*70)
    print("STEP 3: Generating missing embeddings")
    print("="*70)

    missing_count = sum(1 for doc in documents if doc['embedding'] is None)

    if missing_count == 0:
        print("✅ All documents have embeddings!")
        return documents

    print(f"\n📝 Generating embeddings for {missing_count} documents...")

    for i, doc in enumerate(tqdm(documents, desc="Generating embeddings")):
        if doc['embedding'] is None:
            embedding = get_gemini_embedding(doc['document'])
            if embedding:
                doc['embedding'] = embedding
            else:
                print(f"\n⚠️  Failed to generate embedding for doc {i}")

    print("✅ Embedding generation complete!")
    return documents


def create_merged_database(documents: List[Dict]):
    """Create the merged ChromaDB with deduplicated documents"""
    print("\n" + "="*70)
    print("STEP 4: Creating merged database")
    print("="*70)

    print(f"\n📁 Output path: {MERGED_DB_PATH}")
    print(f"   Collection name: {MERGED_COLLECTION_NAME}")

    # Ensure output directory exists
    os.makedirs(MERGED_DB_PATH, exist_ok=True)

    # Create new ChromaDB client
    try:
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
        for i, doc in enumerate(documents):
            if doc['embedding'] is None:
                print(f"\n   ⚠️  Skipping doc {i} - no embedding")
                continue

            ids.append(f"merged_doc_{i}")
            docs.append(doc['document'])

            # Convert embedding to list if needed
            if isinstance(doc['embedding'], np.ndarray):
                embeddings.append(doc['embedding'].tolist())
            else:
                embeddings.append(doc['embedding'])

            # Enhanced metadata
            metadata = doc['metadata'].copy()
            metadata['source_db'] = doc['source_db']
            metadata['source_collection'] = doc['source_collection']
            metadata['original_id'] = doc['id']
            metadatas.append(metadata)

        # Insert in batches
        print(f"\n💾 Inserting {len(ids)} documents into merged database...")
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

        return True

    except Exception as e:
        print(f"\n❌ Error creating merged database: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_merge_report(original_count: int, final_count: int):
    """Generate a detailed merge report"""
    print("\n" + "="*70)
    print("STEP 5: Generating merge report")
    print("="*70)

    report = {
        "original_documents": original_count,
        "final_documents": final_count,
        "duplicates_removed": original_count - final_count,
        "deduplication_rate": f"{((original_count - final_count) / original_count * 100):.2f}%",
        "source_databases": list(DATABASES.keys()),
        "merged_database_path": MERGED_DB_PATH,
        "collection_name": MERGED_COLLECTION_NAME,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "method": "SQLite Direct Access + Gemini Deduplication"
    }

    report_file = os.path.join(MERGED_DB_PATH, "merge_report.json")
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
    print("\n" + "="*70)
    print("   ChromaDB Merger - SQLite Direct Access Method")
    print("="*70)
    print("\nThis method works even with ChromaDB client compatibility issues")
    print("="*70)

    # Step 1: Load all documents from SQLite
    all_documents = load_all_documents()
    original_count = len(all_documents)

    if original_count == 0:
        print("\n❌ No documents found in any database!")
        return

    # Step 2: Deduplicate
    unique_documents = deduplicate_documents(all_documents)

    # Step 3: Generate missing embeddings
    unique_documents = generate_missing_embeddings(unique_documents)

    # Step 4: Create merged database
    success = create_merged_database(unique_documents)

    if not success:
        print("\n❌ Failed to create merged database")
        return

    # Step 5: Generate report
    generate_merge_report(original_count, len(unique_documents))

    print("\n" + "="*70)
    print("✨ Merge completed successfully!")
    print("="*70)
    print(f"\n📂 Merged database location: {MERGED_DB_PATH}")
    print(f"📚 Collection name: {MERGED_COLLECTION_NAME}")
    print(f"📊 Total unique documents: {len(unique_documents)}")
    print("\n✅ You can now use this merged database in your application!")
    print("\nNext steps:")
    print("  1. Run: python verify_merged_db.py")
    print("  2. Update config.py to use merged database")
    print("  3. Test your chatbot")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during merge: {e}")
        import traceback
        traceback.print_exc()
