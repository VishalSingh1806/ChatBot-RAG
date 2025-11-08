"""
Test script for the Gemini PDF Processor

This script demonstrates how to use the PDF processor and test the collections.
"""

import os
from gemini_pdf_processor import process_pdf_folder, setup_collections
from sentence_transformers import SentenceTransformer
import chromadb
from config import CHROMA_DB_PATH


def test_collections():
    """Test querying all collections."""
    print("\n" + "="*60)
    print("TESTING CHROMADB COLLECTIONS")
    print("="*60)

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    collections = ["producer", "imports", "brand_owners", "general"]

    test_queries = [
        "What are the producer responsibilities?",
        "Tell me about import regulations",
        "Who are the brand owners?",
        "EPR compliance requirements"
    ]

    for collection_name in collections:
        print(f"\n{'='*60}")
        print(f"Collection: {collection_name.upper()}")
        print(f"{'='*60}")

        try:
            collection = client.get_collection(collection_name)
            count = collection.count()
            print(f"Total chunks in collection: {count}")

            if count > 0:
                # Test each query
                for query in test_queries:
                    print(f"\nQuery: '{query}'")
                    query_embedding = model.encode([query]).tolist()

                    results = collection.query(
                        query_embeddings=query_embedding,
                        n_results=min(3, count)
                    )

                    if results['documents'][0]:
                        print(f"Found {len(results['documents'][0])} results:")
                        for i, (doc, metadata) in enumerate(zip(
                            results['documents'][0],
                            results['metadatas'][0]
                        ), 1):
                            print(f"\n  Result {i}:")
                            print(f"  Source: {metadata.get('source', 'Unknown')}")
                            print(f"  Summary: {metadata.get('summary', 'N/A')}")
                            print(f"  Content preview: {doc[:200]}...")
                    else:
                        print("  No results found")
            else:
                print(f"Collection '{collection_name}' is empty")

        except Exception as e:
            print(f"Error accessing collection '{collection_name}': {e}")


def main():
    """Main test function."""
    print("="*60)
    print("GEMINI PDF PROCESSOR - TEST SCRIPT")
    print("="*60)

    print("\nOptions:")
    print("1. Process PDFs from a folder")
    print("2. Test existing collections")
    print("3. Both")

    choice = input("\nEnter your choice (1/2/3): ").strip()

    if choice == "1" or choice == "3":
        folder_path = input("\nEnter the path to PDF folder: ").strip()
        if folder_path and os.path.exists(folder_path):
            process_pdf_folder(folder_path)
        else:
            print(f"Invalid folder path: {folder_path}")
            return

    if choice == "2" or choice == "3":
        test_collections()


if __name__ == "__main__":
    main()
