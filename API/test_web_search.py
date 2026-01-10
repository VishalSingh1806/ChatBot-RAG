"""
Test script for web search integration
"""

from web_search_integration import web_search_engine

def test_deadline_detection():
    """Test if deadline queries are properly detected"""
    print("=" * 60)
    print("Testing Deadline Query Detection")
    print("=" * 60)

    test_queries = [
        "What is the last date for annual report filing?",
        "When is the deadline for EPR filing 2024-25?",
        "What are the latest deadlines for plastic EPR?",
        "Tell me about EPR compliance",  # Should NOT trigger
        "What is ReCircle?",  # Should NOT trigger
        "Extended deadline for FY 2024-25",
        "Due date for annual return submission"
    ]

    for query in test_queries:
        is_time_sensitive = web_search_engine.is_time_sensitive_query(query)
        status = "✅ TIME-SENSITIVE" if is_time_sensitive else "❌ NOT TIME-SENSITIVE"
        print(f"\n{status}")
        print(f"Query: {query}")

    print("\n" + "=" * 60)

def test_web_search():
    """Test actual web search functionality"""
    print("\n" + "=" * 60)
    print("Testing Web Search Functionality")
    print("=" * 60)

    test_query = "What is the deadline for EPR annual return filing for FY 2024-25?"

    print(f"\nQuery: {test_query}")
    print("\nSearching...")

    result = web_search_engine.search_latest_info(test_query)

    if result:
        print("\n✅ Web search successful!")
        print(f"\nSource: {result.get('source')}")
        print(f"Real-time: {result.get('is_real_time')}")
        print(f"Timestamp: {result.get('timestamp')}")
        print(f"\nAnswer:\n{result.get('answer')[:500]}...")  # First 500 chars
    else:
        print("\n❌ Web search failed")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Test 1: Deadline detection
    test_deadline_detection()

    # Test 2: Web search (requires API key and may take a moment)
    print("\n\nPress Enter to test actual web search (requires Gemini API)...")
    input()
    test_web_search()

    print("\n✅ All tests completed!")
