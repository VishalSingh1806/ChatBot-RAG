"""
ChromaDB Architecture Inspector
Analyzes all 5 databases to understand structure, metadata, and content
"""
import chromadb
import os
from config import CHROMA_DB_PATH_1, CHROMA_DB_PATH_2, CHROMA_DB_PATH_3, CHROMA_DB_PATH_4, CHROMA_DB_PATH_5, COLLECTIONS

def inspect_database(db_path, db_name):
    """Inspect a single ChromaDB database"""
    print(f"\n{'='*80}")
    print(f"DATABASE: {db_name}")
    print(f"Path: {db_path}")
    print(f"{'='*80}\n")

    try:
        # Check if path exists
        if not os.path.exists(db_path):
            print(f"❌ Path does not exist!")
            return

        # Connect to database
        client = chromadb.PersistentClient(path=db_path)

        # List all collections
        collections = client.list_collections()
        print(f"📚 Total Collections: {len(collections)}\n")

        if not collections:
            print("⚠️  No collections found in this database\n")
            return

        # Inspect each collection
        for coll in collections:
            print(f"📦 Collection: {coll.name}")
            print(f"   ID: {coll.id}")

            # Get collection
            collection = client.get_collection(name=coll.name)

            # Count documents
            count = collection.count()
            print(f"   📄 Total Documents: {count}")

            if count == 0:
                print(f"   ⚠️  Collection is empty\n")
                continue

            # Get sample documents (first 3)
            try:
                sample = collection.get(
                    limit=3,
                    include=['documents', 'metadatas', 'embeddings']
                )

                print(f"   🔍 Sample Documents:\n")

                for i in range(min(3, len(sample['ids']))):
                    print(f"      Document #{i+1}:")
                    print(f"      ID: {sample['ids'][i]}")

                    # Show metadata
                    if sample['metadatas'] and i < len(sample['metadatas']):
                        metadata = sample['metadatas'][i]
                        print(f"      Metadata:")
                        for key, value in metadata.items():
                            print(f"         {key}: {value}")
                    else:
                        print(f"      Metadata: None")

                    # Show document preview
                    if sample['documents'] and i < len(sample['documents']):
                        doc_preview = sample['documents'][i][:200]
                        print(f"      Content Preview: {doc_preview}...")

                    # Show embedding info
                    if sample['embeddings'] and i < len(sample['embeddings']):
                        embedding_dim = len(sample['embeddings'][i])
                        print(f"      Embedding Dimension: {embedding_dim}")

                    print()

                # Analyze metadata schema
                print(f"   📋 Metadata Schema Analysis:")
                if sample['metadatas']:
                    all_keys = set()
                    for meta in sample['metadatas'][:10]:  # Check first 10
                        if meta:
                            all_keys.update(meta.keys())

                    if all_keys:
                        print(f"      Available metadata fields: {', '.join(sorted(all_keys))}")

                        # Check for temporal fields
                        temporal_fields = ['date', 'timestamp', 'created', 'modified', 'embedding_date', 'document_date', 'fiscal_year', 'version']
                        has_temporal = any(field in key.lower() for key in all_keys for field in temporal_fields)

                        if has_temporal:
                            print(f"      ✅ Has temporal metadata")
                        else:
                            print(f"      ⚠️  No temporal metadata found")

                        # Check for versioning
                        has_version = any('version' in key.lower() or 'superseded' in key.lower() for key in all_keys)
                        if has_version:
                            print(f"      ✅ Has version/superseded fields")
                        else:
                            print(f"      ⚠️  No versioning metadata found")
                    else:
                        print(f"      ⚠️  No metadata fields found")
                else:
                    print(f"      ⚠️  No metadata available")

            except Exception as e:
                print(f"   ❌ Error getting sample documents: {e}")

            print()

    except Exception as e:
        print(f"❌ Error inspecting database: {e}\n")


def main():
    """Inspect all 5 databases"""
    print("\n" + "="*80)
    print(" CHROMADB ARCHITECTURE INSPECTION")
    print(" Analyzing all 5 databases in the system")
    print("="*80)

    databases = [
        (CHROMA_DB_PATH_1, "chromaDB (Database 1)"),
        (CHROMA_DB_PATH_2, "chromaDB1 (Database 2)"),
        (CHROMA_DB_PATH_3, "DB1 (Database 3)"),
        (CHROMA_DB_PATH_4, "UDB/Updated_DB (Database 4)"),
        (CHROMA_DB_PATH_5, "Updated_DB/Updated_DB (Database 5)"),
    ]

    # Inspect each database
    for db_path, db_name in databases:
        inspect_database(db_path, db_name)

    # Summary
    print("\n" + "="*80)
    print(" SUMMARY & RECOMMENDATIONS")
    print("="*80 + "\n")

    print("📊 Configuration from config.py:")
    print(f"   CHROMA_DB_PATH_1: {CHROMA_DB_PATH_1}")
    print(f"   CHROMA_DB_PATH_2: {CHROMA_DB_PATH_2}")
    print(f"   CHROMA_DB_PATH_3: {CHROMA_DB_PATH_3}")
    print(f"   CHROMA_DB_PATH_4: {CHROMA_DB_PATH_4}")
    print(f"   CHROMA_DB_PATH_5: {CHROMA_DB_PATH_5}")

    print(f"\n📦 Collection Mapping:")
    for db_path, collections in COLLECTIONS.items():
        print(f"   {db_path}:")
        for coll in collections:
            print(f"      - {coll}")

    print("\n💡 Next Steps:")
    print("   1. Review metadata schemas above")
    print("   2. Identify which databases are newest/oldest")
    print("   3. Check if any have temporal metadata already")
    print("   4. Plan Phase 1 collection prioritization based on findings")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
