import os
import logging
from datetime import datetime
from typing import Dict, List
import json

class BackendNotificationSystem:
    def __init__(self):
        pass
        
    async def notify_high_engagement_user(self, session_data: Dict):
        """Log high engagement user to terminal"""
        conversation_summary = ""
        if session_data.get('recent_queries'):
            conversation_summary = "\n".join([
                f"• {query}" for query in session_data.get('recent_queries', [])[-5:]
            ])
        
        logging.info(f"""
🎯 HIGH ENGAGEMENT USER!

👤 User Information:
Name: {session_data.get('user_name', 'Not provided')}
Email: {session_data.get('email', 'Not provided')}
Phone: {session_data.get('phone', 'Not provided')}
Organization: {session_data.get('organization', 'Not provided')}

📊 Engagement Metrics:
Engagement Score: {session_data.get('engagement_score', 0):.1f}/10
Total Messages: {session_data.get('message_count', 0)}
Primary Intent: {session_data.get('primary_intent', 'Unknown')}

💬 Recent Queries:
{conversation_summary}
        """)
        logging.info(f"📧 High engagement logged for session {session_data.get('session_id')}")
    
    async def send_daily_engagement_summary(self, summary_data: Dict):
        """Log daily summary to terminal"""
        logging.info(f"""
📊 DAILY ENGAGEMENT SUMMARY - {datetime.now().strftime('%Y-%m-%d')}

📈 Overall Metrics:
Total Sessions: {summary_data.get('total_sessions', 0)}
High Engagement Users: {summary_data.get('high_engagement_count', 0)}
Connection Suggestions Made: {summary_data.get('connection_suggestions', 0)}
Average Engagement Score: {summary_data.get('avg_engagement_score', 0):.1f}

🔥 Top Intents Today:
{chr(10).join([f"• {intent}: {count}" for intent, count in summary_data.get('top_intents', {}).items()])}
        """)
        logging.info("📊 Daily engagement summary logged")

backend_notifications = BackendNotificationSystem()
