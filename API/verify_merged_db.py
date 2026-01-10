"""
Merged ChromaDB Verification Script

This script verifies the integrity and quality of the merged database.
Run this after merge_chromadb.py completes successfully.
"""

import os
import chromadb
import json
from collections import Counter

MERGED_DB_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\merged_chromadb"
MERGED_COLLECTION_NAME = "EPR-Merged"


def verify_merged_database():
    """Comprehensive verification of the merged database"""
    print("\n" + "="*70)
    print("         Merged ChromaDB Verification")
    print("="*70)

    try:
        # Connect to merged database
        print(f"\n📂 Connecting to: {MERGED_DB_PATH}")
        client = chromadb.PersistentClient(path=MERGED_DB_PATH)

        # List all collections
        collections = client.list_collections()
        print(f"\n📚 Available collections: {[c.name for c in collections]}")

        # Get the merged collection
        print(f"\n🔍 Checking collection: {MERGED_COLLECTION_NAME}")
        collection = client.get_collection(name=MERGED_COLLECTION_NAME)

        # Get total count
        total_count = collection.count()
        print(f"✅ Total documents: {total_count}")

        if total_count == 0:
            print("\n❌ Warning: Merged database is empty!")
            return

        # Get all data
        print("\n📥 Loading all documents for analysis...")
        results = collection.get(
            include=['documents', 'metadatas', 'embeddings']
        )

        # Verify embeddings
        print("\n🔍 Verifying embeddings...")
        embeddings_present = sum(1 for emb in results['embeddings'] if emb is not None)
        print(f"  Documents with embeddings: {embeddings_present}/{total_count}")

        if embeddings_present < total_count:
            print(f"  ⚠️  Warning: {total_count - embeddings_present} documents missing embeddings")
        else:
            print("  ✅ All documents have embeddings")

        # Check metadata
        print("\n🔍 Analyzing metadata...")
        source_dbs = Counter()
        source_collections = Counter()
        metadata_fields = set()

        for metadata in results['metadatas']:
            if metadata:
                # Count sources
                if 'source_db' in metadata:
                    source_dbs[metadata['source_db']] += 1
                if 'source_collection' in metadata:
                    source_collections[metadata['source_collection']] += 1

                # Track all metadata fields
                metadata_fields.update(metadata.keys())

        print(f"\n  📊 Distribution by source database:")
        for db, count in source_dbs.most_common():
            percentage = (count / total_count) * 100
            print(f"    {db}: {count} documents ({percentage:.1f}%)")

        print(f"\n  📊 Distribution by source collection:")
        for coll, count in source_collections.most_common():
            percentage = (count / total_count) * 100
            print(f"    {coll}: {count} documents ({percentage:.1f}%)")

        print(f"\n  📋 Metadata fields present:")
        for field in sorted(metadata_fields):
            print(f"    - {field}")

        # Sample documents
        print("\n📄 Sample documents from merged database:")
        print("-" * 70)
        sample_size = min(3, total_count)
        sample = collection.get(limit=sample_size, include=['documents', 'metadatas'])

        for i, (doc, metadata) in enumerate(zip(sample['documents'], sample['metadatas'])):
            print(f"\nSample #{i+1}:")
            print(f"  Source DB: {metadata.get('source_db', 'Unknown')}")
            print(f"  Source Collection: {metadata.get('source_collection', 'Unknown')}")
            print(f"  Original ID: {metadata.get('original_id', 'Unknown')}")
            print(f"  Text preview: {doc[:150]}...")

        # Load merge report if available
        print("\n📊 Checking merge report...")
        report_path = os.path.join(MERGED_DB_PATH, "merge_report.json")

        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report = json.load(f)

            print("\n  Merge Statistics (from report):")
            print(f"    Original documents: {report.get('original_documents', 'N/A')}")
            print(f"    Final documents: {report.get('final_documents', 'N/A')}")
            print(f"    Duplicates removed: {report.get('duplicates_removed', 'N/A')}")
            print(f"    Deduplication rate: {report.get('deduplication_rate', 'N/A')}")
            print(f"    Similarity threshold: {report.get('similarity_threshold', 'N/A')}")

            # Verify count matches
            expected = report.get('final_documents')
            if expected and expected != total_count:
                print(f"\n  ⚠️  Warning: Document count mismatch!")
                print(f"    Expected (from report): {expected}")
                print(f"    Actual (in database): {total_count}")
            else:
                print(f"\n  ✅ Document count matches merge report")
        else:
            print("  ⚠️  merge_report.json not found")

        # Final verdict
        print("\n" + "="*70)
        print("                    VERIFICATION SUMMARY")
        print("="*70)

        issues = []

        if total_count == 0:
            issues.append("Database is empty")
        if embeddings_present < total_count:
            issues.append(f"{total_count - embeddings_present} documents missing embeddings")
        if not source_dbs:
            issues.append("No source database information in metadata")

        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ All checks passed!")
            print("\nMerged database is ready to use!")

        print("\n" + "="*70)

        return total_count > 0 and embeddings_present == total_count

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query():
    """Test a sample query on the merged database"""
    print("\n" + "="*70)
    print("         Testing Sample Query")
    print("="*70)

    try:
        client = chromadb.PersistentClient(path=MERGED_DB_PATH)
        collection = client.get_collection(name=MERGED_COLLECTION_NAME)

        # Simple test query
        test_text = "What is EPR compliance?"
        print(f"\n🔍 Test query: '{test_text}'")

        # Get Gemini embedding for the query
        import google.generativeai as genai
        from dotenv import load_dotenv

        load_dotenv()
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

        print("  Generating query embedding...")
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=test_text,
            task_type="retrieval_query"
        )
        query_embedding = result['embedding']

        # Query the database
        print("  Searching merged database...")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=['documents', 'metadatas', 'distances']
        )

        print(f"\n✅ Found {len(results['documents'][0])} results:")

        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\nResult #{i+1}:")
            print(f"  Similarity score: {1 - distance:.3f}")
            print(f"  Source: {metadata.get('source_db', 'Unknown')}")
            print(f"  Text: {doc[:200]}...")

        print("\n✅ Query test successful!")
        return True

    except Exception as e:
        print(f"\n❌ Error during query test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main verification function"""
    print("\n" + "="*70)
    print("   Merged ChromaDB Verification & Testing")
    print("="*70)

    # Step 1: Verify database structure and integrity
    verification_passed = verify_merged_database()

    if not verification_passed:
        print("\n❌ Verification failed. Please check the merge process.")
        return

    # Step 2: Test with a sample query
    print("\n")
    query_test_passed = test_query()

    # Final summary
    print("\n" + "="*70)
    print("                    FINAL VERDICT")
    print("="*70)

    if verification_passed and query_test_passed:
        print("\n✅ SUCCESS!")
        print("\nYour merged database is working correctly.")
        print("You can now use it in your chatbot application.")
        print("\nNext steps:")
        print("  1. Update config.py to use the merged database")
        print("  2. Test your chatbot with the merged data")
        print("  3. Deploy to production")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
