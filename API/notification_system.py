import os
import logging
from datetime import datetime
from typing import Dict

class NotificationSystem:
    def __init__(self):
        pass
        
    async def send_hot_lead_alert(self, lead_data: Dict):
        """Log hot lead to terminal"""
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
        logging.info(f"🚨 Hot lead alert logged for {lead_data.get('user_name', 'Unknown')}")

notification_system = NotificationSystem()
