"""
Fix database path issue - populate the merged_chromadb in API folder
Uses the scraped data to populate the correct database location
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from auto_db_updater import AutoDBUpdater
from config import CHROMA_DB_PATH, COLLECTION_NAME

print("\n" + "="*70)
print("🔧 Database Path Fix & Population Script")
print("="*70)

print(f"\n📍 Target database path: {CHROMA_DB_PATH}")
print(f"📍 Collection name: {COLLECTION_NAME}")

# Ensure the path is absolute
if not os.path.isabs(CHROMA_DB_PATH):
    CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), CHROMA_DB_PATH)
    print(f"📍 Absolute path: {CHROMA_DB_PATH}")

# Initialize updater
updater = AutoDBUpdater(db_path=CHROMA_DB_PATH, collection_name=COLLECTION_NAME)

# Update from scraped data
scraped_dir = os.path.join(os.path.dirname(__file__), "scraped_data")

if not os.path.exists(scraped_dir):
    print(f"\n❌ Scraped data directory not found: {scraped_dir}")
    print("\n💡 Run this first: python run_data_update.py")
    sys.exit(1)

import glob
json_files = glob.glob(os.path.join(scraped_dir, "cpcb_data_*.json"))

if not json_files:
    print(f"\n❌ No scraped data files found in {scraped_dir}")
    print("\n💡 Run this first: python run_data_update.py")
    sys.exit(1)

print(f"\n✅ Found {len(json_files)} scraped data files")

# Use the latest file
latest_file = sorted(json_files)[-1]
print(f"📂 Using: {latest_file}")

# Update database
added = updater.update_from_json_file(latest_file)

# Print results
print("\n" + "="*70)
print("✅ Database Population Complete!")
print("="*70)
print(f"\n📈 Added {added} documents to database")

# Show stats
updater.print_stats()

print("\n" + "="*70)
print("🚀 Your chatbot is now ready!")
print("="*70)
print("\n💡 Next steps:")
print("   1. Restart your chatbot: python main.py")
print("   2. Test with queries in your frontend")
print("="*70)
