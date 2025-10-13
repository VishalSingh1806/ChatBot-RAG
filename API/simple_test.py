from search import find_best_answer

def simple_test():
    """Simple test of search functionality"""
    
    query = "EPR rules"
    print(f"Testing query: {query}")
    
    result = find_best_answer(query)
    
    print(f"Found answer: {len(result['answer'])} characters")
    print(f"Collection: {result['source_info']['collection_name']}")
    print(f"Confidence: {result['source_info']['confidence_score']}")
    print(f"Results found: {result['source_info']['total_results_found']}")
    print("SUCCESS: Langflow database integration working!")

if __name__ == "__main__":
    simple_test()