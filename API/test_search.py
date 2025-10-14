from search import find_best_answer

def test_search():
    """Test search functionality with Langflow database"""
    
    test_queries = [
        "What are EPR rules?",
        "plastic waste management",
        "producer responsibility"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)
        
        result = find_best_answer(query)
        
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Source: {result['source_info']}")
        print(f"Suggestions: {len(result['suggestions'])}")

if __name__ == "__main__":
    test_search()