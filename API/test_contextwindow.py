from contextwindow import context_window

# Test FIFO behavior
session_id = "test_session"

print("Testing FIFO Context Window (max_size=6)")
print("=" * 40)

# Add 8 queries to test FIFO behavior
queries = [
    "What is EPR?",
    "How do I register?", 
    "What documents needed?",
    "What is the fee?",
    "How long does it take?",
    "Who needs to comply?",
    "What are penalties?",
    "Can you help me?"
]

for i, query in enumerate(queries, 1):
    context_window.add_query(session_id, query, f"Response {i}")
    context = context_window.get_context(session_id)
    
    print(f"\nAfter adding query {i}: '{query}'")
    print(f"Context size: {len(context)}")
    print("Current context:")
    for j, item in enumerate(context):
        print(f"  {j+1}. {item['user_query']}")
    
    if len(context) == 6:
        print("  → Limit reached! Next addition will remove oldest.")

print(f"\nFinal context string:")
print(context_window.get_context_string(session_id))