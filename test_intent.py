from API.intent_detector import IntentDetector

# Test the intent detection
detector = IntentDetector()

test_queries = [
    "Are packaging labels considered plastic waste?",
    "I need help with EPR compliance for my company",
    "Can you help us get EPR certificate?",
    "What is plastic waste?",
    "Our organization needs recycling partner",
    "Looking for consultation on EPR"
]

for query in test_queries:
    result = detector.analyze_intent(query, [])
    print(f"\nQuery: {query}")
    print(f"Intent: {result.intent}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Should Connect: {result.should_connect}")
    print(f"Indicators: {result.indicators}")
    print("-" * 50)