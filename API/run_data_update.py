"""
Complete Automation Pipeline
Scrapes CPCB data and updates ChromaDB in one go
"""

import os
import sys
from datetime import datetime
from cpcb_data_scraper import CPCBDataScraper
from auto_db_updater import AutoDBUpdater


def run_complete_update(db_path: str = None, collection_name: str = "EPR-Merged"):
    """Run complete data collection and database update"""

    print("\n" + "="*70)
    print("🤖 CPCB Automated Data Update Pipeline")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    try:
        # Step 1: Scrape data
        print("\n" + "="*70)
        print("STEP 1: Scraping CPCB Data")
        print("="*70)

        scraper = CPCBDataScraper()
        documents = scraper.scrape_all()

        if not documents:
            print("❌ No documents scraped. Exiting.")
            return False

        # Step 2: Update database
        print("\n" + "="*70)
        print("STEP 2: Updating ChromaDB")
        print("="*70)

        updater = AutoDBUpdater(db_path=db_path, collection_name=collection_name)

        # Get latest scraped file
        scraped_files = sorted([f for f in os.listdir("./scraped_data") if f.startswith("cpcb_data_")])
        if not scraped_files:
            print("❌ No scraped data files found. Exiting.")
            return False

        latest_file = os.path.join("./scraped_data", scraped_files[-1])
        added = updater.update_from_json_file(latest_file)

        # Step 3: Show results
        print("\n" + "="*70)
        print("✨ PIPELINE COMPLETE!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   - Documents scraped: {len(documents)}")
        print(f"   - Documents added to DB: {added}")
        print(f"   - Duplicates filtered: {len(documents) - added}")
        print(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Show database stats
        updater.print_stats()

        return True

    except Exception as e:
        print(f"\n❌ Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="CPCB Data Update Pipeline")
    parser.add_argument('--db-path', help='ChromaDB path (default: from config)')
    parser.add_argument('--collection', default='EPR-Merged', help='Collection name')
    parser.add_argument('--scrape-only', action='store_true', help='Only scrape, don\'t update DB')
    parser.add_argument('--update-only', action='store_true', help='Only update DB from existing scraped data')

    args = parser.parse_args()

    if args.scrape_only:
        print("🔍 Scraping data only...")
        scraper = CPCBDataScraper()
        documents = scraper.scrape_all()
        print(f"✅ Scraped {len(documents)} documents")
        return

    if args.update_only:
        print("💾 Updating database only...")
        updater = AutoDBUpdater(db_path=args.db_path, collection_name=args.collection)
        added = updater.update_from_directory()
        print(f"✅ Added {added} documents")
        return

    # Run complete pipeline
    success = run_complete_update(db_path=args.db_path, collection_name=args.collection)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
