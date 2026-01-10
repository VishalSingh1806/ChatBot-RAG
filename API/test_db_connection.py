"""
Test script to verify ChromaDB connection and query functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from search import get_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection"""
    print("\n" + "="*70)
    print("🔍 Testing ChromaDB Connection")
    print("="*70)

    collection = get_collection()

    if not collection:
        print("❌ Failed to connect to database")
        print("\n💡 Tips:")
        print("   1. Make sure you've run: python run_data_update.py")
        print("   2. Check that the database path is correct")
        print("   3. Verify GOOGLE_API_KEY is set in .env")
        return False

    print(f"✅ Successfully connected to database!")

    # Get stats
    try:
        count = collection.count()
        print(f"\n📊 Database Statistics:")
        print(f"   - Total documents: {count}")

        # Get sample documents
        if count > 0:
            sample = collection.get(limit=5, include=['metadatas'])
            print(f"\n📝 Sample document types:")
            for metadata in sample['metadatas']:
                doc_type = metadata.get('type', 'unknown')
                source = metadata.get('source', 'unknown')
                print(f"   - Type: {doc_type}, Source: {source}")

        print("\n✅ Database is ready for use!")
        return True

    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False


def test_query():
    """Test a sample query"""
    print("\n" + "="*70)
    print("🔍 Testing Sample Query")
    print("="*70)

    from search import find_best_answer

    test_queries = [
        "What is the EPR filing deadline?",
        "How do I register for plastic EPR?",
        "What are the penalties for non-compliance?"
    ]

    for query in test_queries:
        print(f"\n❓ Query: {query}")
        result = find_best_answer(query)

        if result and result.get('answer'):
            answer = result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer']
            print(f"✅ Answer preview: {answer}")
            print(f"📊 Confidence: {result.get('source_info', {}).get('confidence_score', 'N/A')}")
        else:
            print("❌ No answer found")

    print("\n✅ Query test complete!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 ChromaDB Connection & Query Test")
    print("="*70)

    # Test 1: Connection
    connection_ok = test_connection()

    if not connection_ok:
        print("\n❌ Connection test failed. Cannot proceed with query test.")
        sys.exit(1)

    # Test 2: Queries
    test_query()

    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70)
    print("\n💡 Your chatbot is ready to use with the new database!")
