"""
ChromaDB Inspector

This script inspects the three ChromaDB databases and provides detailed statistics
before merging. Use this to understand what you're working with.
"""

import os
import chromadb
from collections import defaultdict

# Database paths - Use absolute Windows paths
import os
BASE_DOWNLOAD_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB"

CHROMA_DB_PATH_1 = os.path.join(BASE_DOWNLOAD_PATH, "chromaDB")
CHROMA_DB_PATH_2 = os.path.join(BASE_DOWNLOAD_PATH, "chromaDB1")
CHROMA_DB_PATH_3 = os.path.join(BASE_DOWNLOAD_PATH, "DB1")

# Try to detect collection names automatically
COLLECTIONS = {
    CHROMA_DB_PATH_1: ["EPR-chatbot", "pdf_docs"],  # Common collection names
    CHROMA_DB_PATH_2: ["EPRChatbot-1", "pdf_docs"],
    CHROMA_DB_PATH_3: ["FinalDB", "pdf_docs"]
}


def inspect_database(db_path: str, collection_names: list):
    """Inspect a single ChromaDB database"""
    db_name = os.path.basename(db_path)
    print("\n" + "="*70)
    print(f"Database: {db_name}")
    print(f"Path: {db_path}")
    print("="*70)

    # Check if path exists
    if not os.path.exists(db_path):
        print(f"❌ Path does not exist: {db_path}")
        return 0

    try:
        # Connect to database with error handling
        print(f"\n🔌 Connecting to database...")
        client = chromadb.PersistentClient(path=db_path)

        # List all collections
        all_collections = client.list_collections()
        collection_list = [c.name for c in all_collections]
        print(f"\n📚 Available collections: {collection_list}")

        if not collection_list:
            print("⚠️  No collections found in this database")
            return 0

        # Find the first matching collection from our list
        collection_name = None
        for coll_name in collection_names:
            if coll_name in collection_list:
                collection_name = coll_name
                break

        # If no match, use the first available collection
        if not collection_name:
            collection_name = collection_list[0]
            print(f"\n⚠️  Using first available collection: {collection_name}")

        # Get the collection
        print(f"\n🔍 Inspecting collection: {collection_name}")
        collection = client.get_collection(name=collection_name)

        # Get collection info
        count = collection.count()
        print(f"\n📊 Total documents: {count}")

        # Get sample documents
        if count > 0:
            results = collection.get(
                limit=min(5, count),
                include=['documents', 'metadatas', 'embeddings']
            )

            print(f"\n📄 Sample documents (showing first {len(results['documents'])}):")
            print("-" * 70)

            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"\nDocument #{i+1}:")
                print(f"  Text preview: {doc[:150]}...")
                print(f"  Metadata: {metadata}")
                print(f"  Has embedding: {'Yes' if results['embeddings'][i] else 'No'}")

            # Get metadata statistics
            print(f"\n📋 Metadata statistics:")
            metadata_keys = defaultdict(set)
            all_results = collection.get(include=['metadatas'])

            for metadata in all_results['metadatas']:
                if metadata:
                    for key, value in metadata.items():
                        metadata_keys[key].add(str(value))

            for key, values in metadata_keys.items():
                print(f"  {key}: {len(values)} unique values")
                if len(values) <= 5:
                    print(f"    Values: {list(values)}")

        else:
            print("\n⚠️  No documents found in this collection")

        return count

    except Exception as e:
        print(f"\n❌ Error inspecting database: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Try to provide helpful suggestions
        if "PanicException" in str(type(e)) or "range start index" in str(e):
            print("\n💡 This looks like a ChromaDB corruption or version mismatch issue.")
            print("   Possible solutions:")
            print("   1. The database may be from a different ChromaDB version")
            print("   2. Try copying the database to a local path (shorter path)")
            print("   3. Check if you have the latest chromadb package")
            print("      Run: pip install --upgrade chromadb")

        return 0


def main():
    """Main inspection function"""
    print("\n" + "="*70)
    print("           ChromaDB Inspector - Database Analysis")
    print("="*70)

    total_docs = 0
    db_stats = {}

    # Inspect each database
    for db_path, collection_names in COLLECTIONS.items():
        count = inspect_database(db_path, collection_names)
        total_docs += count
        db_stats[os.path.basename(db_path)] = count

    # Summary
    print("\n" + "="*70)
    print("                         SUMMARY")
    print("="*70)

    for db_name, count in db_stats.items():
        print(f"  {db_name}: {count} documents")

    print(f"\n  📊 Total documents across all databases: {total_docs}")

    print("\n" + "="*70)
    print("Next steps:")
    print("  1. Review the data above")
    print("  2. Run merge_chromadb.py to merge and deduplicate")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Inspection interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()
