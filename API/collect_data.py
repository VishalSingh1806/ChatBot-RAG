from fastapi import HTTPException
from fastapi.responses import JSONResponse
from models import UserData
from datetime import datetime
import redis
import asyncio
import os
from dotenv import load_dotenv
import logging
from brevo_service import brevo_service

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

RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")


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

        # ✅ Send email via Brevo in background (non-blocking)
        form_data = {
            "session_id": session_id,
            "name": user_data.name,
            "email": user_data.email,
            "phone": user_data.phone,
            "organization": user_data.organization
        }
        asyncio.create_task(brevo_service.send_form_submission_notification(form_data))
        logging.info(f"📧 Brevo email task queued for session: {session_id}")

        # ✅ Return session_id for chatbot to use (immediate response)
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
