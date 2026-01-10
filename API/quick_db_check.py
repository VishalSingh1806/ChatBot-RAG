"""
Quick script to check and populate the merged database
"""
import os
import sys
import chromadb

# Database path
db_path = os.path.join(os.path.dirname(__file__), "merged_chromadb")

print(f"\n{'='*70}")
print(f"Checking database at: {db_path}")
print(f"{'='*70}\n")

# Connect to database
try:
    client = chromadb.PersistentClient(path=db_path)
    print("✅ Connected to ChromaDB")

    # List collections
    collections = client.list_collections()
    print(f"\n📚 Collections found: {len(collections)}")

    if collections:
        for coll in collections:
            count = coll.count()
            print(f"  - {coll.name}: {count} documents")
    else:
        print("  ⚠️  No collections found!")
        print("\n💡 You need to run the data update to populate the database:")
        print("   python run_data_update.py")

        # Check if scraped data exists
        scraped_dir = os.path.join(os.path.dirname(__file__), "scraped_data")
        if os.path.exists(scraped_dir):
            import glob
            json_files = glob.glob(os.path.join(scraped_dir, "cpcb_data_*.json"))
            if json_files:
                print(f"\n✅ Found {len(json_files)} scraped data files")
                print("   You can update the database with:")
                print("   python auto_db_updater.py --directory ./scraped_data")
            else:
                print("\n⚠️  No scraped data files found")
                print("   Run: python run_data_update.py")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
