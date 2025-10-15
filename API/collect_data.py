from fastapi import HTTPException
from fastapi.responses import JSONResponse
from models import UserData
from datetime import datetime
import redis
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Redis client
try:
    redis_host = os.getenv("REDIS_HOST", "localhost")  # Fallback only if not defined
    redis_client = redis.StrictRedis(host=redis_host, port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logging.info(f"✅ Redis client initialized and connected to {redis_host}")
except Exception as e:
    logging.error(f"❌ Failed to initialize Redis client: {e}")
    redis_client = None


# Email batch storage
email_batch = []
# batch_size = 5
batch_size = 1  # Increased for more realistic batching
batch_lock = asyncio.Lock()

# SMTP Config (from env or fallback)
SMTP_SERVER = os.getenv("SMTP_SERVER")
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
except (ValueError, TypeError):
    logging.error("❌ Invalid SMTP_PORT in .env file. Must be an integer. Defaulting to 587.")
    SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

SMTP_ENABLED = all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, RECIPIENT_EMAIL])

if SMTP_ENABLED:
    logging.info(f"📨 SMTP config loaded. Emails will be sent to {RECIPIENT_EMAIL}.")
else:
    logging.warning("⚠️ SMTP configuration is incomplete. Email sending is disabled.")


async def get_user_data_from_session(session_id: str):
    """Checks Redis for existing user data for a given session ID."""
    if not redis_client:
        return None
    try:
        session_key = f"session:{session_id}"
        if redis_client.exists(session_key) and redis_client.hget(session_key, "user_data_collected") == "true":
            user_data = redis_client.hgetall(session_key)
            logging.info(f"✅ Found existing user data for session {session_id}")
            return user_data
    except redis.exceptions.ConnectionError as e:
        logging.error(f"❌ Redis connection error in get_user_data_from_session: {e}")
    except Exception as e:
        logging.error(f"❌ Exception in get_user_data_from_session: {e}", exc_info=True)
    return None


async def collect_user_data(user_data: UserData):
    if not redis_client:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")

    try:
        logging.info(f"📥 Received form submission for session: {user_data.session_id}")

        session_key = f"session:{user_data.session_id}"

        # Use a single hset call with a mapping for better performance
        user_data_map = {
            "user_data_collected": "true",
            "user_name": user_data.name,
            "email": user_data.email,
            "phone": user_data.phone,
            "organization": user_data.organization,
            "last_interaction": datetime.utcnow().isoformat(),
        }
        redis_client.hmset(session_key, mapping=user_data_map)
        logging.info(f"✅ Data saved to Redis for key: {session_key}")

        session_id = user_data.session_id

        # ✅ Return session_id for chatbot to use (no individual email)
        return JSONResponse(
            content={"message": "User data collected successfully", "session_id": session_id},
            status_code=200,
        )

    except redis.exceptions.ConnectionError as e:
        logging.error(f"❌ Redis connection error in collect_user_data: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable.")
    except Exception as e:
        logging.error(f"❌ Exception in collect_user_data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"❌ Failed to collect user data: {str(e)}")


async def send_email_batch(batch: list):
    if not batch:
        return

    try:
        logging.info(f"📧 Preparing to send email for a batch of {len(batch)} user(s).")

        # Create a single summary email for the entire batch for efficiency
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = f"New User Registrations Batch ({len(batch)} users)"

        body_parts = [f"A new batch of {len(batch)} user(s) registered at {datetime.utcnow().isoformat()} UTC:\n"]
        for i, user_data in enumerate(batch, 1):
            # Check if this is a hot lead
            hot_lead_indicator = ""
            if redis_client:
                try:
                    session_key = f"session:{user_data.get('session_id', '')}"
                    if redis_client.exists(session_key):
                        lead_key = f"lead:{user_data.get('session_id', '')}"
                        if redis_client.exists(lead_key):
                            lead_data = redis_client.hgetall(lead_key)
                            if lead_data.get('hot_lead') == 'true':
                                hot_lead_indicator = " 🔥 HOT LEAD"
                            elif int(lead_data.get('lead_score', 0)) >= 15:
                                hot_lead_indicator = " ⭐ HIGH INTEREST"
                except Exception:
                    pass
            
            part = f"""
                    -------------------
                    User #{i}{hot_lead_indicator}
                    Name: {user_data.get('name', 'N/A')}
                    Email: {user_data.get('email', 'N/A')}
                    Phone: {user_data.get('phone', 'N/A')}
                    Organization: {user_data.get('organization', 'N/A')}
                    """
            body_parts.append(part)

        msg.attach(MIMEText("\n".join(body_parts), "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            logging.info(f"✅ Email batch sent successfully for {len(batch)} user(s).")

    except Exception as e:
        logging.error(f"❌ Failed to send email batch. Data for this batch may be lost. Error: {e}", exc_info=True)
        # In a production system, you might want to re-queue the batch here,
        # for example, by writing it to a "failed_batches" log or back into Redis.
