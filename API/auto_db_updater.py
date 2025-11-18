"""
Automated ChromaDB Updater
Processes scraped data and adds it to ChromaDB with deduplication
"""

import os
import json
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Set
import hashlib
import numpy as np
from datetime import datetime
from tqdm import tqdm
import glob

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Import from existing modules
from config import CHROMA_DB_PATH, COLLECTION_NAME

class AutoDBUpdater:
    def __init__(self, db_path: str = None, collection_name: str = None):
        """Initialize the updater"""
        self.db_path = db_path or CHROMA_DB_PATH
        self.collection_name = collection_name or COLLECTION_NAME

        # Ensure directory exists
        os.makedirs(self.db_path, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ Connected to existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ Created new collection: {collection_name}")

        # Track for deduplication
        self.existing_hashes: Set[str] = set()
        self._load_existing_hashes()

    def _load_existing_hashes(self):
        """Load existing document hashes for deduplication"""
        print("📚 Loading existing document hashes...")
        try:
            count = self.collection.count()
            print(f"   Found {count} existing documents")

            # Get all documents in batches
            BATCH_SIZE = 1000
            for offset in range(0, count, BATCH_SIZE):
                results = self.collection.get(
                    limit=min(BATCH_SIZE, count - offset),
                    offset=offset,
                    include=['documents']
                )

                for doc in results['documents']:
                    doc_hash = self._compute_hash(doc)
                    self.existing_hashes.add(doc_hash)

            print(f"   ✅ Loaded {len(self.existing_hashes)} document hashes")
        except Exception as e:
            print(f"   ⚠️  Error loading hashes: {e}")

    def _compute_hash(self, text: str) -> str:
        """Compute hash for deduplication"""
        # Normalize text
        normalized = text.strip().lower()
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def get_gemini_embedding(self, text: str) -> List[float]:
        """Get embedding from Gemini API"""
        try:
            # Truncate if too long (max ~20k chars for embedding)
            if len(text) > 20000:
                text = text[:20000]

            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"   ⚠️  Error getting embedding: {e}")
            return None

    def is_duplicate(self, text: str) -> bool:
        """Check if document is duplicate"""
        doc_hash = self._compute_hash(text)
        return doc_hash in self.existing_hashes

    def process_document(self, doc_data: Dict) -> Dict:
        """Process a single document and prepare for insertion"""
        # Extract content
        content = doc_data.get('content', '')

        if not content or len(content) < 50:
            return None

        # Check for duplicates
        if self.is_duplicate(content):
            return None

        # Get embedding
        embedding = self.get_gemini_embedding(content)
        if not embedding:
            return None

        # Prepare metadata
        metadata = {
            "type": doc_data.get('type', 'unknown'),
            "source": doc_data.get('source', doc_data.get('source_url', 'unknown')),
            "date_added": datetime.now().isoformat(),
            "date_scraped": doc_data.get('date', 'unknown'),
        }

        # Add additional fields
        if 'query' in doc_data:
            metadata['search_query'] = doc_data['query'][:200]  # Truncate if too long

        if 'links' in doc_data and doc_data['links']:
            metadata['reference_links'] = json.dumps(doc_data['links'][:3])  # Store first 3 links

        return {
            "content": content,
            "embedding": embedding,
            "metadata": metadata,
            "hash": self._compute_hash(content)
        }

    def add_documents(self, documents: List[Dict], batch_size: int = 50):
        """Add documents to ChromaDB"""
        print(f"\n📝 Processing {len(documents)} documents...")

        processed_docs = []
        skipped = 0

        # Process documents
        for doc in tqdm(documents, desc="Processing documents"):
            processed = self.process_document(doc)
            if processed:
                processed_docs.append(processed)
            else:
                skipped += 1

        if not processed_docs:
            print("⚠️  No new documents to add (all duplicates or invalid)")
            return 0

        print(f"\n✅ Processed {len(processed_docs)} new documents")
        print(f"⏭️  Skipped {skipped} documents (duplicates or invalid)")

        # Add to ChromaDB in batches
        print(f"\n💾 Adding documents to ChromaDB...")
        added_count = 0

        for i in range(0, len(processed_docs), batch_size):
            batch = processed_docs[i:i + batch_size]

            ids = [f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{j}" for j in range(i, i + len(batch))]
            documents = [doc['content'] for doc in batch]
            embeddings = [doc['embedding'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]

            try:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                # Update hash set
                for doc in batch:
                    self.existing_hashes.add(doc['hash'])

                added_count += len(batch)
                print(f"   ✅ Added batch {i//batch_size + 1}: {added_count}/{len(processed_docs)} documents")

            except Exception as e:
                print(f"   ❌ Error adding batch {i//batch_size + 1}: {e}")

        return added_count

    def update_from_json_file(self, json_file: str) -> int:
        """Update database from a JSON file"""
        print(f"\n📂 Loading data from: {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)

            print(f"   ✅ Loaded {len(documents)} documents from JSON")

            return self.add_documents(documents)

        except Exception as e:
            print(f"   ❌ Error loading JSON file: {e}")
            return 0

    def update_from_directory(self, directory: str = "./scraped_data") -> int:
        """Update database from all JSON files in directory"""
        print("\n" + "="*70)
        print(f"📁 Updating database from directory: {directory}")
        print("="*70)

        json_files = glob.glob(os.path.join(directory, "cpcb_data_*.json"))

        if not json_files:
            print("⚠️  No JSON files found in directory")
            return 0

        print(f"   Found {len(json_files)} JSON files")

        total_added = 0
        for json_file in json_files:
            added = self.update_from_json_file(json_file)
            total_added += added

        return total_added

    def get_stats(self) -> Dict:
        """Get database statistics"""
        count = self.collection.count()

        # Get recent documents
        recent = self.collection.get(
            limit=5,
            include=['metadatas']
        )

        # Count by type
        all_docs = self.collection.get(
            include=['metadatas']
        )

        type_counts = {}
        for metadata in all_docs['metadatas']:
            doc_type = metadata.get('type', 'unknown')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        return {
            "total_documents": count,
            "document_types": type_counts,
            "recent_additions": len(recent['ids']) if recent else 0
        }

    def print_stats(self):
        """Print database statistics"""
        print("\n" + "="*70)
        print("📊 Database Statistics")
        print("="*70)

        stats = self.get_stats()

        print(f"\n📚 Total documents: {stats['total_documents']}")
        print(f"\n📑 Document types:")
        for doc_type, count in stats['document_types'].items():
            print(f"   {doc_type}: {count}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated ChromaDB Updater")
    parser.add_argument('--db-path', help='ChromaDB path (default: from config)')
    parser.add_argument('--collection', default='EPR-Merged', help='Collection name')
    parser.add_argument('--json-file', help='Update from specific JSON file')
    parser.add_argument('--directory', default='./scraped_data', help='Update from directory')
    parser.add_argument('--stats-only', action='store_true', help='Only show statistics')

    args = parser.parse_args()

    # Initialize updater
    updater = AutoDBUpdater(
        db_path=args.db_path,
        collection_name=args.collection
    )

    if args.stats_only:
        updater.print_stats()
        return

    # Update database
    if args.json_file:
        added = updater.update_from_json_file(args.json_file)
    else:
        added = updater.update_from_directory(args.directory)

    # Print results
    print("\n" + "="*70)
    print("✅ Update Complete!")
    print("="*70)
    print(f"\n📈 Added {added} new documents to database")

    # Show updated stats
    updater.print_stats()


if __name__ == "__main__":
    main()
