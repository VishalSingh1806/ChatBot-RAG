#!/usr/bin/env python3
"""
Script to check and restore ChromaDB collection metadata.
The vector data (.bin files) exists but collections table might be empty.
"""

import chromadb
from chromadb.config import Settings
import os
import sqlite3

# Database configurations matching config.py
DB_CONFIGS = [
    {
        "name": "chromaDB",
        "path": "/var/lib/chatbot/chromaDB",
        "collection_name": "EPR-chatbot",
        "uuid_dir": "29407d2d-4b8b-429b-826c-9a2cfe975a18"
    },
    {
        "name": "chromaDB1",
        "path": "/var/lib/chatbot/chromaDB1",
        "collection_name": "EPRChatbot-1",
        "uuid_dir": "cf1472e4-bb6c-4c46-821e-950fff4cb75c"
    },
    {
        "name": "DB1",
        "path": "/var/lib/chatbot/DB1",
        "collection_name": "FinalDB",
        "uuid_dir": "f9974a67-b3ee-4c4f-9e37-eab174e6522f"
    },
    {
        "name": "UDB",
        "path": "/var/lib/chatbot/UDB/Updated_DB",
        "collection_name": "updated_db",
        "uuid_dir": "3c028811-f1f3-4938-86dd-77b46b7f580f"
    },
    {
        "name": "Updated_DB",
        "path": "/var/lib/chatbot/Updated_DB/Updated_DB",
        "collection_name": "EPR-Merged",
        "uuid_dir": "200d8b92-f179-4e71-b5f5-2e2d9e83406f"
    }
]

def check_database(db_config):
    """Check a single database for collections and vector data"""
    print(f"\n{'='*60}")
    print(f"Checking: {db_config['name']}")
    print(f"Path: {db_config['path']}")
    print(f"Expected collection: {db_config['collection_name']}")
    print(f"{'='*60}")

    # Check if path exists
    if not os.path.exists(db_config['path']):
        print(f"❌ Path does not exist!")
        return False

    # Check for SQLite database
    sqlite_path = os.path.join(db_config['path'], 'chroma.sqlite3')
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at {sqlite_path}")
        return False

    print(f"✅ SQLite database exists")

    # Check for vector data directory
    vector_dir = os.path.join(db_config['path'], db_config['uuid_dir'])
    if os.path.exists(vector_dir):
        files = os.listdir(vector_dir)
        print(f"✅ Vector data directory exists with {len(files)} files:")
        for f in files:
            file_path = os.path.join(vector_dir, f)
            size = os.path.getsize(file_path)
            print(f"   - {f}: {size:,} bytes")
    else:
        print(f"❌ Vector data directory not found: {vector_dir}")
        # Try to find any UUID directories
        dirs = [d for d in os.listdir(db_config['path']) if os.path.isdir(os.path.join(db_config['path'], d))]
        if dirs:
            print(f"   Found directories: {dirs}")

    # Check SQLite database contents
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()

        # Check collections table
        cursor.execute("SELECT COUNT(*) FROM collections")
        col_count = cursor.fetchone()[0]
        print(f"\n📊 Collections in database: {col_count}")

        if col_count > 0:
            cursor.execute("SELECT name, id FROM collections")
            for name, col_id in cursor.fetchall():
                print(f"   - {name} (ID: {col_id})")
        else:
            print("   ⚠️  No collections found in database!")

        # Check segments table
        cursor.execute("SELECT COUNT(*) FROM segments")
        seg_count = cursor.fetchone()[0]
        print(f"📊 Segments in database: {seg_count}")

        conn.close()

    except Exception as e:
        print(f"❌ Error reading SQLite database: {e}")
        return False

    # Try to connect with ChromaDB client
    try:
        print(f"\n🔌 Attempting ChromaDB connection...")
        client = chromadb.PersistentClient(
            path=db_config['path'],
            settings=Settings(allow_reset=False, anonymized_telemetry=False)
        )

        collections = client.list_collections()
        print(f"✅ ChromaDB client connected")
        print(f"📚 Collections visible to ChromaDB: {len(collections)}")

        for col in collections:
            print(f"   - {col.name}: {col.count()} documents")

        if len(collections) == 0 and col_count == 0:
            print(f"\n⚠️  ISSUE FOUND: Collections table is empty but vector data exists!")
            print(f"   This suggests the database was reset or corrupted.")
            print(f"   Vector data directory: {vector_dir}")
            return False

    except Exception as e:
        print(f"❌ Error connecting with ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def main():
    print("="*60)
    print("ChromaDB Collection Metadata Check")
    print("="*60)

    issues = []

    for db_config in DB_CONFIGS:
        success = check_database(db_config)
        if not success:
            issues.append(db_config['name'])

    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if issues:
        print(f"❌ Found issues in {len(issues)} database(s):")
        for db_name in issues:
            print(f"   - {db_name}")
        print(f"\nRECOMMENDATION:")
        print(f"The ChromaDB collections table is empty but vector data exists.")
        print(f"This means the databases need to be repopulated from source PDFs.")
        print(f"Please run the PDF processor to recreate the collections.")
    else:
        print(f"✅ All databases look healthy!")

if __name__ == "__main__":
    main()
