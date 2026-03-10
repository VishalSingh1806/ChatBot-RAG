import os
import logging
from typing import Dict
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from datetime import datetime


class BrevoEmailService:
    """
    Service for sending transactional emails using Brevo API
    Sends individual emails for hot leads and high engagement notifications
    """

    def __init__(self):
        self.api_key = os.getenv('BREVO_API_KEY')
        self.sender_email = os.getenv('BREVO_SENDER_EMAIL', 'tech@recircle.in')
        self.sender_name = os.getenv('BREVO_SENDER_NAME', 'Recircle Chatbot')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', 'vishal.singh@recircle.in')

        if not self.api_key:
            logging.warning("BREVO_API_KEY not found. Email sending disabled.")
            self.api_instance = None
        else:
            # Configure API
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.api_key
            self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            logging.info("Brevo Email Service initialized")

    def _create_html_email(self, subject: str, data: Dict) -> str:
        """Create formatted HTML email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .section h2 {{ color: #667eea; margin-top: 0; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                .info-row {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                .label {{ font-weight: bold; display: inline-block; min-width: 150px; color: #555; }}
                .value {{ color: #333; }}
                .score-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; background: #ff4444; color: white; }}
                .queries {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-top: 10px; }}
                .query-item {{ padding: 5px 0; color: #555; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔥 {subject}</h1>
            </div>
            <div class="content">
        """

        # Contact Information
        html += '<div class="section"><h2>👤 Contact Details</h2>'
        html += f'<div class="info-row"><span class="label">Name:</span> <span class="value">{data.get("user_name", "Not provided")}</span></div>'
        html += f'<div class="info-row"><span class="label">Email:</span> <span class="value">{data.get("email", "Not provided")}</span></div>'
        html += f'<div class="info-row"><span class="label">Phone:</span> <span class="value">{data.get("phone", "Not provided")}</span></div>'
        html += f'<div class="info-row"><span class="label">Organization:</span> <span class="value">{data.get("organization", "Not provided")}</span></div>'
        html += '</div>'

        # Metrics
        html += '<div class="section"><h2>📊 Metrics</h2>'
        if 'lead_score' in data:
            html += f'<div class="info-row"><span class="label">Lead Score:</span> <span class="score-badge">{data["lead_score"]}/100</span></div>'
        if 'engagement_score' in data:
            html += f'<div class="info-row"><span class="label">Engagement Score:</span> <span class="value">{data["engagement_score"]:.1f}/10</span></div>'
        if 'total_queries' in data:
            html += f'<div class="info-row"><span class="label">Total Messages:</span> <span class="value">{data["total_queries"]}</span></div>'
        if 'high_interest_queries' in data:
            html += f'<div class="info-row"><span class="label">High Interest Queries:</span> <span class="value">{data["high_interest_queries"]}</span></div>'
        if 'primary_intent' in data:
            html += f'<div class="info-row"><span class="label">Primary Intent:</span> <span class="value">{data["primary_intent"]}</span></div>'
        html += '</div>'

        # Recent Queries
        if data.get('recent_queries'):
            queries = data['recent_queries']
            if isinstance(queries, list) and queries:
                html += '<div class="section"><h2>💬 Recent Queries</h2><div class="queries">'
                for query in queries[-5:]:
                    html += f'<div class="query-item">• {query}</div>'
                html += '</div></div>'

        # Session Info
        html += '<div class="section"><h2>⏰ Session Info</h2>'
        if data.get('last_interaction'):
            html += f'<div class="info-row"><span class="label">Last Active:</span> <span class="value">{data["last_interaction"]}</span></div>'
        if data.get('session_id'):
            html += f'<div class="info-row"><span class="label">Session ID:</span> <span class="value">{data["session_id"]}</span></div>'
        html += '</div>'

        html += f"""
            </div>
            <div style="text-align: center; padding: 20px; color: #777; font-size: 12px;">
                Recircle Chatbot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        return html

    async def send_hot_lead_alert(self, lead_data: Dict) -> bool:
        """Send hot lead alert email"""
        if not self.api_instance:
            logging.warning("Brevo not initialized. Skipping email.")
            return False

        try:
            subject = f"🔥 HOT LEAD: {lead_data.get('user_name', 'Unknown')} - Score: {lead_data.get('lead_score', 0)}"
            html_content = self._create_html_email(subject, lead_data)

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": self.recipient_email}],
                sender={"email": self.sender_email, "name": self.sender_name},
                subject=subject,
                html_content=html_content
            )

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logging.info(f"✅ Hot lead email sent via Brevo: {api_response.message_id}")
            return True

        except ApiException as e:
            logging.error(f"❌ Brevo API error: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Error sending email: {e}", exc_info=True)
            return False

    async def send_high_engagement_notification(self, session_data: Dict) -> bool:
        """Send high engagement notification"""
        if not self.api_instance:
            logging.warning("Brevo not initialized. Skipping email.")
            return False

        try:
            user_name = session_data.get('user_name', 'Anonymous')
            subject = f"🎯 High Engagement: {user_name}"
            html_content = self._create_html_email(subject, session_data)

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": self.recipient_email}],
                sender={"email": self.sender_email, "name": self.sender_name},
                subject=subject,
                html_content=html_content
            )

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logging.info(f"✅ Engagement email sent via Brevo: {api_response.message_id}")
            return True

        except ApiException as e:
            logging.error(f"❌ Brevo API error: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Error sending email: {e}", exc_info=True)
            return False

    async def send_form_submission_notification(self, user_data: Dict) -> bool:
        """Send email notification for each form submission"""
        if not self.api_instance:
            logging.warning("Brevo not initialized. Skipping email.")
            return False

        try:
            user_name = user_data.get('name', 'Unknown')
            subject = f"📋 New Form Submission: {user_name}"

            # Create simple HTML email for form submission
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .section h2 {{ color: #667eea; margin-top: 0; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                    .info-row {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
                    .label {{ font-weight: bold; display: inline-block; min-width: 150px; color: #555; }}
                    .value {{ color: #333; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📋 New User Registration</h1>
                </div>
                <div class="content">
                    <div class="section">
                        <h2>👤 Contact Details</h2>
                        <div class="info-row"><span class="label">Name:</span> <span class="value">{user_data.get('name', 'Not provided')}</span></div>
                        <div class="info-row"><span class="label">Email:</span> <span class="value">{user_data.get('email', 'Not provided')}</span></div>
                        <div class="info-row"><span class="label">Phone:</span> <span class="value">{user_data.get('phone', 'Not provided')}</span></div>
                        <div class="info-row"><span class="label">Organization:</span> <span class="value">{user_data.get('organization', 'Not provided')}</span></div>
                    </div>
                    <div class="section">
                        <h2>⏰ Submission Info</h2>
                        <div class="info-row"><span class="label">Session ID:</span> <span class="value">{user_data.get('session_id', 'Unknown')}</span></div>
                        <div class="info-row"><span class="label">Submitted At:</span> <span class="value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</span></div>
                    </div>
                </div>
                <div style="text-align: center; padding: 20px; color: #777; font-size: 12px;">
                    Recircle Chatbot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </body>
            </html>
            """

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": self.recipient_email}],
                sender={"email": self.sender_email, "name": self.sender_name},
                subject=subject,
                html_content=html
            )

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logging.info(f"✅ Form submission email sent via Brevo: {api_response.message_id}")
            return True

        except ApiException as e:
            logging.error(f"❌ Brevo API error: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Error sending form submission email: {e}", exc_info=True)
            return False


# Global instance
brevo_service = BrevoEmailService()
