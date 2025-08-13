import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from datetime import datetime
from typing import Dict

class NotificationSystem:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sales_email = os.getenv("SALES_TEAM_EMAIL", os.getenv("RECIPIENT_EMAIL"))
        
    async def send_hot_lead_alert(self, lead_data: Dict):
        """Send immediate email alert for hot leads"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.sales_email]):
            logging.warning("SMTP not configured for hot lead alerts")
            return
            
        try:
            subject = f"🔥 HOT LEAD ALERT - {lead_data.get('user_name', 'Unknown User')}"
            
            body = f"""
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

🎯 Recent Intent: {lead_data.get('recent_intents', [])[-1] if lead_data.get('recent_intents') else 'None'}

ACTION REQUIRED: Contact this lead within 2 hours for best conversion rates!

Chat Session: {lead_data.get('session_id', 'Unknown')}
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.sales_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logging.info(f"🚨 Hot lead alert sent for {lead_data.get('user_name', 'Unknown')}")
            
        except Exception as e:
            logging.error(f"Failed to send hot lead alert: {e}")

notification_system = NotificationSystem()