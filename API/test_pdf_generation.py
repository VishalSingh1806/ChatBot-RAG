"""
Test script to verify PDF generation and email sending
"""
import os
from dotenv import load_dotenv
from session_reporter import finalize_session

load_dotenv()

# Test with an existing session ID
test_session_id = "535b2e50-9c73-4163-9953-d4c03931c59d"

print(f"🧪 Testing PDF generation for session: {test_session_id}")
print(f"📧 Email will be sent to: {os.getenv('BACKEND_TEAM_EMAIL')}")
print(f"📁 PDF will be saved in: reports/")
print()

try:
    finalize_session(test_session_id)
    print("\n✅ Test completed successfully!")
except Exception as e:
    print(f"\n❌ Test failed: {e}")
