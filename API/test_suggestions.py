"""
Test script to verify contextual suggestions are working properly
"""
from search import generate_related_questions

def test_contextual_suggestions():
    """Test different query types to see if suggestions are contextual"""
    
    test_cases = [
        {
            "query": "What documents are needed for EPR registration?",
            "expected_context": "registration"
        },
        {
            "query": "How do I meet my EPR compliance targets?",
            "expected_context": "compliance"
        },
        {
            "query": "What are the penalties for EPR non-compliance?",
            "expected_context": "penalty"
        },
        {
            "query": "How is plastic waste recycled?",
            "expected_context": "recycling"
        },
        {
            "query": "What are producer responsibilities under EPR?",
            "expected_context": "producer"
        },
        {
            "query": "How do importers comply with EPR?",
            "expected_context": "importer"
        },
        {
            "query": "What services does ReCircle offer?",
            "expected_context": "recircle"
        }
    ]
    
    print("🧪 Testing Contextual Suggestions Generation")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_context = test_case["expected_context"]
        
        print(f"\n[Test {i}] Query: {query}")
        print(f"Expected Context: {expected_context}")
        
        suggestions = generate_related_questions(query)
        
        print("Generated Suggestions:")
        for j, suggestion in enumerate(suggestions, 1):
            print(f"  {j}. {suggestion}")
        
        # Check if suggestions are contextually relevant
        query_lower = query.lower()
        suggestions_text = " ".join(suggestions).lower()
        
        contextual_match = False
        if expected_context == "registration" and any(word in suggestions_text for word in ["register", "registration", "documents", "certificate"]):
            contextual_match = True
        elif expected_context == "compliance" and any(word in suggestions_text for word in ["compliance", "target", "meet", "achieve"]):
            contextual_match = True
        elif expected_context == "penalty" and any(word in suggestions_text for word in ["penalty", "fine", "non-compliance", "avoid"]):
            contextual_match = True
        elif expected_context == "recycling" and any(word in suggestions_text for word in ["recycle", "recycling", "waste", "disposal"]):
            contextual_match = True
        elif expected_context == "producer" and any(word in suggestions_text for word in ["producer", "manufacturer", "production"]):
            contextual_match = True
        elif expected_context == "importer" and any(word in suggestions_text for word in ["import", "importer", "imported"]):
            contextual_match = True
        elif expected_context == "recircle" and any(word in suggestions_text for word in ["recircle", "services", "help"]):
            contextual_match = True
        
        status = "✅ CONTEXTUAL" if contextual_match else "❌ GENERIC"
        print(f"Result: {status}")
    
    print("\n" + "=" * 60)
    print("🎉 Contextual Suggestions Test Complete!")

if __name__ == "__main__":
    test_contextual_suggestions()