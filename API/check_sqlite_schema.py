"""Quick script to check ChromaDB SQLite schema"""
import sqlite3

db_path = r"C:\Users\visha\Downloads\chromaDB-20251112T052425Z-1-001\chromaDB\chromaDB\chroma.sqlite3"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
for table in cursor.fetchall():
    print(f"\n{table[0]}:")
    cursor.execute(f"PRAGMA table_info({table[0]});")
    for col in cursor.fetchall():
        print(f"  {col}")

conn.close()
