#!/usr/bin/env python3
"""
Fix November 30, 2025 dates in PRODUCTION databases at /var/lib/chatbot/
"""

import sqlite3
import sys

def fix_database(db_path, dry_run=False):
    """Fix November 30, 2025 references in the database"""
    print(f"\n{'='*80}")
    print(f"Processing: {db_path}")
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

            # Show context
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

        conn.close()
        return updates_made

    except Exception as e:
        print(f"✗ Error: {e}")
        return 0


def main():
    # Production databases
    databases = [
        ('chromaDB', '/var/lib/chatbot/chromaDB/chroma.sqlite3'),
        ('chromaDB1', '/var/lib/chatbot/chromaDB1/chroma.sqlite3'),
        ('DB1', '/var/lib/chatbot/DB1/chroma.sqlite3'),
        ('UDB/Updated_DB', '/var/lib/chatbot/UDB/Updated_DB/chroma.sqlite3'),
        ('Updated_DB', '/var/lib/chatbot/Updated_DB/Updated_DB/chroma.sqlite3'),
        ('chroma_db', '/var/lib/chatbot/chroma_db/chroma.sqlite3'),
    ]

    print("="*80)
    print("FIXING PRODUCTION DATABASES")
    print("="*80)

    total_updated = 0
    for db_name, db_path in databases:
        try:
            count = fix_database(db_path, dry_run=False)
            total_updated += count
        except Exception as e:
            print(f"Skipping {db_name}: {e}")

    print("\n" + "="*80)
    print(f"✓ COMPLETE: Updated {total_updated} documents across all databases")
    print("="*80)


if __name__ == "__main__":
    main()
