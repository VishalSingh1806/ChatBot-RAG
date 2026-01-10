"""
Direct SQLite ChromaDB Inspector

This bypasses ChromaDB's client and reads directly from SQLite database files.
Use this if the regular inspect script has errors.
"""

import sqlite3
import os
import json

BASE_DOWNLOAD_PATH = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB"

DATABASES = {
    "chromaDB": os.path.join(BASE_DOWNLOAD_PATH, "chromaDB", "chroma.sqlite3"),
    "chromaDB1": os.path.join(BASE_DOWNLOAD_PATH, "chromaDB1", "chroma.sqlite3"),
    "DB1": os.path.join(BASE_DOWNLOAD_PATH, "DB1", "chroma.sqlite3"),
}


def inspect_sqlite_db(db_name: str, db_path: str):
    """Directly inspect ChromaDB SQLite file"""
    print("\n" + "="*70)
    print(f"Database: {db_name}")
    print(f"Path: {db_path}")
    print("="*70)

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return 0

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📚 Tables in database: {[t[0] for t in tables]}")

        # Get collections
        cursor.execute("SELECT * FROM collections;")
        collections = cursor.fetchall()

        if not collections:
            print("⚠️  No collections found")
            return 0

        print(f"\n📂 Collections ({len(collections)}):")
        for coll in collections:
            print(f"   {coll}")

        # Get document count from embeddings table
        total_docs = 0
        try:
            cursor.execute("SELECT COUNT(*) FROM embeddings;")
            count = cursor.fetchone()[0]
            total_docs = count
            print(f"\n📊 Total embeddings/documents: {count}")
        except Exception as e:
            print(f"⚠️  Could not count embeddings: {e}")

        # Try to get some sample metadata
        try:
            cursor.execute("SELECT * FROM embedding_metadata LIMIT 5;")
            metadata_samples = cursor.fetchall()
            if metadata_samples:
                print(f"\n📄 Sample metadata (first 5):")
                for i, meta in enumerate(metadata_samples):
                    print(f"   {i+1}. {meta}")
        except Exception as e:
            print(f"⚠️  Could not read metadata: {e}")

        # Try to get sample documents
        try:
            cursor.execute("SELECT * FROM embedding_fulltext_search LIMIT 3;")
            docs = cursor.fetchall()
            if docs:
                print(f"\n📝 Sample documents:")
                for i, doc in enumerate(docs):
                    # Doc might be in different columns, show all
                    print(f"\n   Document {i+1}:")
                    if len(doc) > 1 and doc[1]:
                        text = str(doc[1])[:150]
                        print(f"      {text}...")
        except Exception as e:
            print(f"⚠️  Could not read documents: {e}")

        conn.close()
        return total_docs

    except Exception as e:
        print(f"\n❌ Error reading database: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """Main inspection function"""
    print("\n" + "="*70)
    print("   Direct SQLite ChromaDB Inspector")
    print("="*70)
    print("\nThis tool reads ChromaDB files directly via SQLite,")
    print("bypassing ChromaDB client issues.\n")

    total_docs = 0
    db_stats = {}

    for db_name, db_path in DATABASES.items():
        count = inspect_sqlite_db(db_name, db_path)
        total_docs += count
        db_stats[db_name] = count

    # Summary
    print("\n" + "="*70)
    print("                         SUMMARY")
    print("="*70)

    for db_name, count in db_stats.items():
        print(f"  {db_name}: {count} documents")

    print(f"\n  📊 Total documents across all databases: {total_docs}")

    print("\n" + "="*70)
    if total_docs > 0:
        print("✅ Databases are accessible via SQLite")
        print("\nNext steps:")
        print("  1. If regular ChromaDB client works, use merge_chromadb.py")
        print("  2. If you get errors, we may need to export/reimport the data")
    else:
        print("⚠️  No documents found or databases are empty")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Inspection interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
