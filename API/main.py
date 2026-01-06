from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

load_dotenv()

import uuid
import asyncio
from datetime import datetime
from models import QueryRequest, QueryResponse, UserData
from search import find_best_answer
from llm_refiner import refine_with_gemini
from collect_data import collect_user_data, get_user_data_from_session, redis_client
from lead_manager import lead_manager
from session_reporter import finalize_session, generate_user_pdf
from session_monitor import start_monitor
from inactivity_monitor import monitor_inactivity

# --------------------------------------------------------
# APP CONFIG
# --------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 Starting EPR ChatBot API")
    asyncio.create_task(start_monitor())
    asyncio.create_task(monitor_inactivity())
    logging.info("✅ Background monitors started")
    yield
    logging.info("🛑 Shutting down EPR ChatBot API")

app = FastAPI(lifespan=lifespan)
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_for_development_only")
IS_PRODUCTION = os.getenv("APP_ENV") == "production"

# --------------------------------------------------------
# Middleware setup
# --------------------------------------------------------
SESSION_EXPIRY_DAYS = int(os.getenv("SESSION_EXPIRY_DAYS", 30))
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="none" if IS_PRODUCTION else "lax",
    https_only=IS_PRODUCTION,
    session_cookie="session",
    max_age=SESSION_EXPIRY_DAYS * 86400,
    path="/",
)

allow_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://34.93.109.253",
    "http://34.93.109.253:8080",
    "http://34.93.109.253:80",
    "http://rebot.recircle.in",
    "https://rebot.recircle.in",
    "http://rebot.recircle.in:80",
    "https://rebot.recircle.in:443",
    "http://recircle.in",
    "https://recircle.in",
    "http://www.recircle.in",
    "https://www.recircle.in",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
# Routes
# --------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Server is running"}

@app.post("/session")
async def get_or_create_session(request: Request):
    try:
        if "session_id" not in request.session:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            logging.info(f"✅ Created new session: {session_id}")
        else:
            session_id = request.session["session_id"]
        
        user_data = await get_user_data_from_session(session_id)
        
        # Retrieve chat history if user is returning
        chat_history = []
        if user_data:
            chat_key = f"session:{session_id}:chat"
            if redis_client.exists(chat_key):
                raw_messages = redis_client.lrange(chat_key, 0, -1)
                for msg in raw_messages:
                    if msg.startswith("User: "):
                        chat_history.append({"role": "user", "text": msg[6:]})
                    elif msg.startswith("Bot: "):
                        chat_history.append({"role": "bot", "text": msg[5:]})
                logging.info(f"📜 Retrieved {len(chat_history)} messages for session {session_id}")
        
        return {
            "session_id": session_id,
            "user_data_collected": user_data is not None,
            "user_data": user_data,
            "chat_history": chat_history
        }
    except Exception as e:
        logging.error(f"❌ Session creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Session creation failed")

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: Request, query: QueryRequest):
    """Handles user query + logs chat + generates answer"""
    try:
        if "session_id" not in request.session:
            request.session["session_id"] = str(uuid.uuid4())
        session_id = request.session["session_id"]

        user_data = await get_user_data_from_session(session_id)
        user_name = user_data.get("user_name") if user_data else None
        history = query.history or []

        # Detect intent first for better question generation
        from intent_detector import intent_detector
        intent_result = intent_detector.analyze_intent(query.text, history)
        
        # Get previous suggestions from Redis
        suggestions_key = f"session:{session_id}:suggestions"
        previous_suggestions = redis_client.lrange(suggestions_key, 0, -1) or []
        
        result = find_best_answer(query.text, intent_result, previous_suggestions)
        final_answer, intent_result, user_context = refine_with_gemini(
            user_name=user_name,
            query=query.text,
            raw_answer=result["answer"],
            history=history,
            is_first_message=(len(history) == 0),
            session_id=session_id,
            source_info=result.get("source_info", {})
        )

        from intent_detector import intent_detector
        engagement_score = intent_detector._calculate_engagement_score(query.text.lower(), history)

        # ✅ Save chat to Redis for PDF report
        try:
            chat_key = f"session:{session_id}:chat"
            redis_client.rpush(chat_key, f"User: {query.text}")
            redis_client.rpush(chat_key, f"Bot: {final_answer}")
            redis_client.expire(chat_key, SESSION_EXPIRY_DAYS * 86400)
            chat_count = redis_client.llen(chat_key)
            logging.info(f"💬 Saved chat to Redis. Total messages: {chat_count}")
            
            # ✅ Update session last_interaction timestamp (don't reset thank you flag)
            session_key = f"session:{session_id}"
            
            if redis_client.exists(session_key):
                redis_client.hset(session_key, "last_interaction", datetime.utcnow().isoformat())
                logging.info(f"⏰ Updated last_interaction for session {session_id}")
                
                # Reset backend notification flag to allow new PDF after 60 min inactivity
                backend_sent_key = f"session:{session_id}:backend_sent"
                if redis_client.exists(backend_sent_key):
                    redis_client.delete(backend_sent_key)
                    logging.info(f"🔄 User resumed - reset backend notification flag for session {session_id}")
        except Exception as chat_err:
            logging.error(f"❌ Could not save chat logs: {chat_err}", exc_info=True)

        # Track user intent
        await lead_manager.track_user_intent(
            session_id=session_id,
            intent_result=intent_result,
            query=query.text,
            user_data=user_data,
            engagement_score=engagement_score
        )

        # Check if query is off-topic (not EPR/ReCircle related)
        query_lower = query.text.lower()
        off_topic_keywords = ['weather', 'sports', 'movie', 'music', 'food', 'game', 'joke', 'story', 'news', 'politics']
        is_off_topic = any(keyword in query_lower for keyword in off_topic_keywords)
        
        # Don't show suggestions for off-topic queries
        suggestions = [] if is_off_topic else result["suggestions"]
        
        # Store new suggestions in Redis (excluding "Connect me to ReCircle")
        if suggestions:
            for suggestion in suggestions:
                if suggestion != "Connect me to ReCircle":
                    redis_client.rpush(suggestions_key, suggestion)
            redis_client.expire(suggestions_key, SESSION_EXPIRY_DAYS * 86400)
        
        return {
            "answer": final_answer,
            "similar_questions": suggestions,
            "intent": {
                "type": intent_result.intent,
                "confidence": intent_result.confidence,
                "should_connect": intent_result.should_connect
            },
            "context": {
                "industry": user_context.get('industry'),
                "urgency": user_context.get('urgency'),
                "engagement_score": engagement_score
            },
            "source_info": result.get("source_info", {})
        }

    except Exception as e:
        logging.error(f"❌ Error in /query endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Query processing failed")

@app.post("/collect_user_data")
async def handle_user_data(request: Request, user_data: UserData):
    try:
        if "session_id" not in request.session:
            raise HTTPException(status_code=400, detail="Session not found")
        session_id = request.session["session_id"]
        user_data.session_id = session_id
        result = await collect_user_data(user_data)
        
        # Mark this session for inactivity monitoring
        monitor_key = f"session:{session_id}:monitor_inactivity"
        redis_client.set(monitor_key, datetime.utcnow().isoformat(), ex=SESSION_EXPIRY_DAYS * 86400)
        
        # Also set initial last_interaction timestamp
        session_key = f"session:{session_id}"
        redis_client.hset(session_key, "last_interaction", datetime.utcnow().isoformat())
        
        # Retrieve chat history for returning users
        chat_history = []
        chat_key = f"session:{session_id}:chat"
        if redis_client.exists(chat_key):
            raw_messages = redis_client.lrange(chat_key, 0, -1)
            for msg in raw_messages:
                if msg.startswith("User: "):
                    chat_history.append({"role": "user", "text": msg[6:]})
                elif msg.startswith("Bot: "):
                    chat_history.append({"role": "bot", "text": msg[5:]})
        
        logging.info(f"✅ Session {session_id} marked for inactivity monitoring")
        
        # Convert result to dict if it's a JSONResponse
        if hasattr(result, 'body'):
            import json
            result_dict = json.loads(result.body)
        else:
            result_dict = result
        
        return {**result_dict, "chat_history": chat_history}
    except Exception as e:
        logging.error(f"❌ Error collecting user data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Data collection failed")

@app.get("/debug/chat/{session_id}")
async def debug_chat_logs(session_id: str):
    """Debug endpoint to check chat logs in Redis"""
    try:
        chat_key = f"session:{session_id}:chat"
        exists = redis_client.exists(chat_key)
        count = redis_client.llen(chat_key)
        messages = redis_client.lrange(chat_key, 0, -1)
        return {
            "session_id": session_id,
            "chat_key": chat_key,
            "exists": bool(exists),
            "message_count": count,
            "messages": messages
        }
    except Exception as e:
        logging.error(f"❌ Debug error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_chat/{session_id}")
async def download_chat(session_id: str):
    try:
        logging.info(f"📥 Download request for session: {session_id}")
        pdf_path = generate_user_pdf(session_id)
        if not pdf_path:
            logging.error(f"❌ No chat data found for session {session_id}")
            raise HTTPException(status_code=404, detail="No chat data found")
        if not os.path.exists(pdf_path):
            logging.error(f"❌ PDF file not found at {pdf_path}")
            raise HTTPException(status_code=404, detail="PDF generation failed")
        logging.info(f"✅ Sending PDF: {pdf_path}")
        return FileResponse(pdf_path, media_type="application/pdf", filename="Discussion_with_ReCircle.pdf")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Error downloading chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger_contact_intent")
async def trigger_contact_intent(request: Request):
    """Immediately send data to backend when user clicks contact button"""
    try:
        if "session_id" not in request.session:
            raise HTTPException(status_code=400, detail="Session not found")
        session_id = request.session["session_id"]
        
        logging.info(f"📞 Contact button clicked for session {session_id}")
        
        # Get user data
        user_data = await get_user_data_from_session(session_id)
        user_name = user_data.get("user_name", "User") if user_data else "User"
        
        # Mark as contact intent and send immediately
        lead_key = f"lead:{session_id}"
        redis_client.hset(lead_key, "contact_clicked", "true")
        redis_client.hset(lead_key, "contact_timestamp", datetime.utcnow().isoformat())
        redis_client.hset(lead_key, "priority", "high")
        
        # Send PDF report immediately to backend team
        finalize_session(session_id)
        
        # Return response for user
        contact_email = os.getenv("CONTACT_EMAIL", "info@recircle.in")
        response_message = f"Thank you for your interest! Our ReCircle team has been notified and will reach out to you shortly. Meanwhile, you can connect with us on:\n\n🌐 Website: https://recircle.in/\n📞 Call us: 9004240004\n📧 Email: {contact_email}\n\nYou can also continue asking questions while you wait!"
        
        logging.info(f"✅ Backend notified + user response sent for session {session_id}")
        return {
            "status": "success",
            "message": response_message
        }
    except Exception as e:
        logging.error(f"❌ Error triggering contact intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send contact request")

@app.post("/end_session")
async def end_chat_session(request: Request):
    try:
        if "session_id" not in request.session:
            raise HTTPException(status_code=400, detail="Session not found")
        session_id = request.session["session_id"]
        
        # Debug: Check chat logs before finalizing
        chat_key = f"session:{session_id}:chat"
        chat_count = redis_client.llen(chat_key)
        logging.info(f"🔍 Finalizing session {session_id} with {chat_count} chat messages")
        
        finalize_session(session_id)
        return {"status": "success", "message": f"PDF report generated and emailed for session {session_id}"}
    except Exception as e:
        logging.error(f"❌ Error finalizing session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to finalize session")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
