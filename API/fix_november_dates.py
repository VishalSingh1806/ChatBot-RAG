#!/usr/bin/env python3
"""
Script to fix incorrect November 30, 2025 dates in ChromaDB databases.
Replaces them with the correct final deadline: 31st January 2026
"""

import sqlite3
import sys

def fix_database(db_path, dry_run=False):
    """
    Fix November 30, 2025 references in the database

    Args:
        db_path: Path to the chroma.sqlite3 file
        dry_run: If True, only show what would be changed without making changes
    """
    print(f"\n{'='*80}")
    print(f"Processing: {db_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will make changes)'}")
    print('='*80)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Find documents with "30th November 2025" or "November 30, 2025"
        cursor.execute("""
            SELECT id, string_value
            FROM embedding_metadata
            WHERE (string_value LIKE '%30th November 2025%'
                OR string_value LIKE '%November 30, 2025%'
                OR string_value LIKE '%November 30th, 2025%')
            AND string_value LIKE '%2024-25%'
            AND string_value LIKE '%Annual Return%'
        """)

        results = cursor.fetchall()

        if not results:
            print("✓ No documents with incorrect November 30, 2025 deadline found")
            conn.close()
            return 0

        print(f"\nFound {len(results)} documents with November 30, 2025 deadline")

        updates_made = 0
        for row_id, text in results:
            print(f"\n--- Document ID: {row_id} ---")

            # Show context around the date
            text_lower = text.lower()
            idx = text_lower.find('november')
            if idx != -1:
                start = max(0, idx - 100)
                end = min(len(text), idx + 200)
                print(f"BEFORE: ...{text[start:end]}...")

            # Replace the dates
            new_text = text
            new_text = new_text.replace("30th November 2025", "31st January 2026")
            new_text = new_text.replace("November 30, 2025", "January 31, 2026")
            new_text = new_text.replace("November 30th, 2025", "January 31st, 2026")

            # Also update the explanation to mention it's the latest extension
            if "extended" in new_text.lower() and "november" not in new_text.lower():
                # Show what changed
                idx = new_text.lower().find('31')
                if idx != -1:
                    start = max(0, idx - 100)
                    end = min(len(text), idx + 200)
                    print(f"AFTER:  ...{new_text[start:end]}...")

                if not dry_run:
                    cursor.execute("""
                        UPDATE embedding_metadata
                        SET string_value = ?
                        WHERE id = ?
                    """, (new_text, row_id))
                    updates_made += 1
                    print("✓ Updated")
                else:
                    print("✓ Would update (dry run)")
                    updates_made += 1

        if not dry_run and updates_made > 0:
            conn.commit()
            print(f"\n✓ Successfully updated {updates_made} documents")
        elif dry_run:
            print(f"\n✓ Dry run complete - would update {updates_made} documents")

        conn.close()
        return updates_made

    except Exception as e:
        print(f"✗ Error: {e}")
        return 0


def main():
    # Databases to fix
    databases = [
        ('Updated_DB', 'chroma_db/drive-download-20260108T065146Z-3-001/Updated_DB/Updated_DB/chroma.sqlite3'),
        ('merged_chromadb', 'merged_chromadb/chroma.sqlite3'),
        ('Updated_DB (CORRECT folder)', 'chroma_db/drive-download-CORRECT/Updated_DB/Updated_DB/chroma.sqlite3')
    ]

    # First run in dry-run mode to see what would be changed
    print("\n" + "="*80)
    print("PHASE 1: DRY RUN - Checking what would be changed")
    print("="*80)

    total_to_update = 0
    for db_name, db_path in databases:
        try:
            count = fix_database(db_path, dry_run=True)
            total_to_update += count
        except Exception as e:
            print(f"Skipping {db_name}: {e}")

    if total_to_update == 0:
        print("\n✓ No updates needed - all databases have correct dates!")
        return

    # Ask for confirmation
    print("\n" + "="*80)
    print(f"PHASE 2: Ready to update {total_to_update} documents")
    print("="*80)

    response = input("\nProceed with updates? (yes/no): ").strip().lower()

    if response == 'yes':
        print("\n" + "="*80)
        print("PHASE 2: LIVE RUN - Making changes")
        print("="*80)

        total_updated = 0
        for db_name, db_path in databases:
            try:
                count = fix_database(db_path, dry_run=False)
                total_updated += count
            except Exception as e:
                print(f"Error updating {db_name}: {e}")

        print("\n" + "="*80)
        print(f"✓ COMPLETE: Updated {total_updated} documents across all databases")
        print("="*80)
    else:
        print("\n✗ Update cancelled by user")


if __name__ == "__main__":
    main()
