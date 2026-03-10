import os
import logging
from datetime import datetime
from typing import Dict
from brevo_service import brevo_service

class NotificationSystem:
    def __init__(self):
        pass

    async def send_hot_lead_alert(self, lead_data: Dict):
        """Send hot lead alert via Brevo email AND log to terminal"""
        # Log to terminal
        logging.info(f"""
🔥 HOT LEAD DETECTED!

URGENT: High-interest lead detected!

👤 Contact Details:
Name: {lead_data.get('user_name', 'Not provided')}
Email: {lead_data.get('email', 'Not provided')}
Phone: {lead_data.get('phone', 'Not provided')}
Organization: {lead_data.get('organization', 'Not provided')}

📊 Lead Score: {lead_data.get('lead_score', 0)}/100
🔥 High Interest Queries: {lead_data.get('high_interest_queries', 0)}
💬 Total Queries: {lead_data.get('total_queries', 0)}

⏰ Last Active: {lead_data.get('last_interaction', 'Unknown')}
        """)

        # Send email via Brevo
        email_sent = await brevo_service.send_hot_lead_alert(lead_data)
        if email_sent:
            logging.info(f"✅ Hot lead email sent via Brevo for {lead_data.get('user_name', 'Unknown')}")
        else:
            logging.warning(f"⚠️ Hot lead email failed, but logged for {lead_data.get('user_name', 'Unknown')}")

notification_system = NotificationSystem()
