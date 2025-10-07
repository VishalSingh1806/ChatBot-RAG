#!/usr/bin/env python3
"""
ChromaDB Management Script
"""

import chromadb
import sys

def reset_db():
    """Reset the ChromaDB database"""
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        client.delete_collection(name="epr_knowledge")
        print("Database reset successfully!")
    except:
        print("No existing database found.")

def check_db():
    """Check database status"""
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = client.get_collection(name="epr_knowledge")
        count = collection.count()
        print(f"Database contains {count} documents")
    except:
        print("Database not found. Run 'python init_db.py' to initialize.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py [reset|check]")
        return
    
    command = sys.argv[1]
    
    if command == "reset":
        reset_db()
    elif command == "check":
        check_db()
    else:
        print("Unknown command. Use 'reset' or 'check'")

if __name__ == "__main__":
    main()