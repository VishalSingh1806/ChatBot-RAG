import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from datetime import datetime
from typing import Dict, List
import json

class BackendNotificationSystem:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.backend_team_email = os.getenv("BACKEND_TEAM_EMAIL", os.getenv("RECIPIENT_EMAIL"))
        
    async def notify_high_engagement_user(self, session_data: Dict):
        """Notify backend team about high engagement users"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.backend_team_email]):
            logging.warning("SMTP not configured for backend notifications")
            return
            
        try:
            subject = f"🎯 High Engagement User - {session_data.get('user_name', 'Anonymous')}"
            
            # Format conversation history
            conversation_summary = ""
            if session_data.get('recent_queries'):
                conversation_summary = "\n".join([
                    f"• {query}" for query in session_data.get('recent_queries', [])[-5:]
                ])
            
            body = f"""
High engagement user detected on ReBot!

👤 User Information:
Name: {session_data.get('user_name', 'Not provided')}
Email: {session_data.get('email', 'Not provided')}
Phone: {session_data.get('phone', 'Not provided')}
Organization: {session_data.get('organization', 'Not provided')}

📊 Engagement Metrics:
Engagement Score: {session_data.get('engagement_score', 0):.1f}/10
Total Messages: {session_data.get('message_count', 0)}
Session Duration: {session_data.get('session_duration', 'Unknown')}
Primary Intent: {session_data.get('primary_intent', 'Unknown')}

💬 Recent Queries:
{conversation_summary}

🔗 Session ID: {session_data.get('session_id', 'Unknown')}
⏰ Last Active: {session_data.get('last_interaction', 'Unknown')}

This user shows strong interest in EPR services and may convert to a lead.
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.backend_team_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logging.info(f"📧 Backend notification sent for session {session_data.get('session_id')}")
            
        except Exception as e:
            logging.error(f"Failed to send backend notification: {e}")
    
    async def send_daily_engagement_summary(self, summary_data: Dict):
        """Send daily summary of user engagement patterns"""
        try:
            subject = f"📊 Daily ReBot Engagement Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
Daily ReBot Engagement Report

📈 Overall Metrics:
Total Sessions: {summary_data.get('total_sessions', 0)}
High Engagement Users: {summary_data.get('high_engagement_count', 0)}
Connection Suggestions Made: {summary_data.get('connection_suggestions', 0)}
Average Engagement Score: {summary_data.get('avg_engagement_score', 0):.1f}

🔥 Top Intents Today:
{chr(10).join([f"• {intent}: {count}" for intent, count in summary_data.get('top_intents', {}).items()])}

💡 Insights:
{summary_data.get('insights', 'No specific insights available')}
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.backend_team_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logging.info("📊 Daily engagement summary sent")
            
        except Exception as e:
            logging.error(f"Failed to send daily summary: {e}")

backend_notifications = BackendNotificationSystem()