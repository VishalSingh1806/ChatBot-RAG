#!/usr/bin/env python3
"""Test script to send a test email via Brevo"""

import asyncio
import sys
sys.path.insert(0, '/home/apps/ChatBot-RAG/API')

from brevo_service import brevo_service

async def send_test_email():
    """Send a test email to verify Brevo integration"""
    test_data = {
        "session_id": "test-session-123",
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890",
        "organization": "Test Organization"
    }

    print("🧪 Sending test email via Brevo...")
    result = await brevo_service.send_form_submission_notification(test_data)

    if result:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Failed to send test email. Check logs for details.")

    return result

if __name__ == "__main__":
    asyncio.run(send_test_email())
