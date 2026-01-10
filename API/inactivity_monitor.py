import asyncio
import logging
from datetime import datetime, timedelta
from collect_data import redis_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
INACTIVITY_THRESHOLD_MINUTES = int(os.getenv("INACTIVITY_THRESHOLD_MINUTES", 60))

def send_thank_you_email(user_email: str, user_name: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = user_email
        msg["Subject"] = "Thank You for Chatting with Us"

        body = f"""Dear {user_name},

Thank you for chatting with us. For more details or assistance, please feel free to contact us.

Contact Information:
Address: 3rd Floor, APML Tower, Vishveshwar Nagar Rd, Yashodham, Goregaon, Mumbai, Maharashtra 400063
Phone: +91 90042 40004
Email: {os.getenv('CONTACT_EMAIL', 'info@recircle.in')}

Best regards,
Team Recircle"""

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logging.info(f"✅ Thank you email sent to {user_email}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send thank you email: {e}")
        return False

async def monitor_inactivity():
    logging.info("🔍 Inactivity monitor started - checking every 60 seconds (only new sessions)")
    checked_sessions = set()
    
    while True:
        try:
            await asyncio.sleep(60)
            
            session_keys = redis_client.keys("session:*")
            for key in session_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                if ":chat" in key_str or ":thankyou_sent" in key_str or ":monitor_inactivity" in key_str:
                    continue
                
                session_id = key_str.split(":")[1]
                
                # Only monitor sessions that are marked for monitoring
                monitor_key = f"session:{session_id}:monitor_inactivity"
                if not redis_client.exists(monitor_key):
                    continue
                
                thankyou_key = f"session:{session_id}:thankyou_sent"
                if redis_client.exists(thankyou_key):
                    continue
                
                session_data = redis_client.hgetall(key)
                if not session_data:
                    continue
                
                last_interaction = session_data.get(b"last_interaction") or session_data.get("last_interaction")
                if not last_interaction:
                    continue
                
                if isinstance(last_interaction, bytes):
                    last_interaction = last_interaction.decode()
                
                last_time = datetime.fromisoformat(last_interaction)
                time_diff = datetime.utcnow() - last_time
                
                if time_diff >= timedelta(minutes=INACTIVITY_THRESHOLD_MINUTES):
                    user_email = (session_data.get(b"email") or session_data.get("email") or b"").decode() if isinstance(session_data.get(b"email") or session_data.get("email"), bytes) else session_data.get("email", "")
                    user_name = (session_data.get(b"user_name") or session_data.get("user_name") or b"").decode() if isinstance(session_data.get(b"user_name") or session_data.get("user_name"), bytes) else session_data.get("user_name", "User")
                    
                    # Send thank you email only once (check flag)
                    if user_email and not redis_client.exists(thankyou_key):
                        logging.info(f"📧 Sending thank you email to {user_name} ({user_email}) after {INACTIVITY_THRESHOLD_MINUTES} min inactivity")
                        if send_thank_you_email(user_email, user_name):
                            redis_client.set(thankyou_key, "1", ex=86400)
                            logging.info(f"✅ Thank you email sent and flag set for session {session_id}")
                    
                    # Send PDF to backend team (can be sent multiple times)
                    backend_sent_key = f"session:{session_id}:backend_sent"
                    if not redis_client.exists(backend_sent_key):
                        logging.info(f"📊 Sending PDF to backend team for session {session_id}")
                        from session_reporter import finalize_session
                        finalize_session(session_id)
                        redis_client.set(backend_sent_key, "1", ex=3600)  # 1 hour expiry
                        logging.info(f"✅ PDF sent to backend team for session {session_id}")
                        
        except Exception as e:
            logging.error(f"❌ Error in inactivity monitor: {e}")
