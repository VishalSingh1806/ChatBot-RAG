from API.intent_detector import IntentDetector

# Test samples for intent detection
detector = IntentDetector()

# Test cases with expected outcomes
test_cases = [
    # Should trigger connection after 4-5 messages
    {
        "conversation": [
            "What is EPR?",
            "How does EPR compliance work?", 
            "Our company needs to understand EPR requirements",
            "Can you help us with EPR implementation?",
            "We are looking for EPR consultation"
        ],
        "expected": "Should suggest connection after message 4-5"
    },
    
    # High engagement - immediate connection
    {
        "conversation": [
            "Our organization urgently needs EPR certificate",
            "We have an audit coming up next week"
        ],
        "expected": "Should suggest connection immediately (urgent + business)"
    },
    
    # Business context - progressive engagement
    {
        "conversation": [
            "What is plastic waste management?",
            "My company produces plastic packaging", 
            "We need compliance guidance",
            "How can we get EPR registration?"
        ],
        "expected": "Should suggest connection after message 4"
    },
    
    # Service-specific interest
    {
        "conversation": [
            "How to get EPR certificate?",
            "What documents are needed for registration?",
            "Can you assist with the process?"
        ],
        "expected": "Should suggest connection after message 3"
    },
    
    # Low engagement - general questions
    {
        "conversation": [
            "What is plastic?",
            "Is plastic bad?",
            "What are alternatives?"
        ],
        "expected": "Should NOT suggest connection yet"
    }
]

print("🧪 TESTING INTENT DETECTION\n" + "="*50)

for i, test_case in enumerate(test_cases, 1):
    print(f"\n📋 TEST CASE {i}: {test_case['expected']}")
    print("-" * 40)
    
    history = []
    for j, query in enumerate(test_case['conversation']):
        # Build history for context
        if j > 0:
            history.append({"role": "user", "text": test_case['conversation'][j-1]})
            history.append({"role": "bot", "text": "Response"})
        
        result = detector.analyze_intent(query, history)
        engagement = detector._calculate_engagement_score(query.lower(), history)
        
        print(f"Message {j+1}: {query}")
        print(f"  Intent: {result.intent} (confidence: {result.confidence:.2f})")
        print(f"  Engagement: {engagement:.1f}/10")
        print(f"  Should Connect: {'✅ YES' if result.should_connect else '❌ NO'}")
        print()

print("\n" + "="*50)
print("🎯 QUICK TEST QUERIES (single messages):")
print("-" * 50)

quick_tests = [
    "Our company needs EPR compliance help",  # Should connect
    "We are looking for recycling partners",   # Should connect  
    "What is plastic waste?",                  # Should NOT connect
    "Can you help us get certificate?",       # Should connect
    "I need urgent assistance with audit",    # Should connect
    "How does recycling work?",               # Should NOT connect
]

for query in quick_tests:
    result = detector.analyze_intent(query, [])
    print(f"'{query}' → {'✅' if result.should_connect else '❌'} ({result.intent})")