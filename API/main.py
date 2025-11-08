from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import logging
import os
import uuid
import asyncio
from datetime import datetime
from models import QueryRequest, QueryResponse, UserData
from search import find_best_answer
from llm_refiner import refine_with_gemini
from collect_data import collect_user_data, get_user_data_from_session, redis_client
from lead_manager import lead_manager
from session_reporter import finalize_session
from session_monitor import start_monitor

# --------------------------------------------------------
# APP CONFIG
# --------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 Starting EPR ChatBot API")
    asyncio.create_task(start_monitor())
    logging.info("✅ Background session monitor started")
    yield
    logging.info("🛑 Shutting down EPR ChatBot API")

app = FastAPI(lifespan=lifespan)
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_for_development_only")
IS_PRODUCTION = os.getenv("APP_ENV") == "production"

# --------------------------------------------------------
# Middleware setup
# --------------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="none" if IS_PRODUCTION else "lax",
    https_only=IS_PRODUCTION,
    session_cookie="session",
    max_age=86400,
    path="/",
)

allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://34.173.78.39",
    "http://34.173.78.39:8080",
    "http://34.173.78.39:80",
    "http://rebot.recircle.in",
    "https://rebot.recircle.in",
    "http://rebot.recircle.in:80",
    "https://rebot.recircle.in:443",
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
        return {
            "session_id": session_id,
            "user_data_collected": user_data is not None,
            "user_data": user_data
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
        
        result = find_best_answer(query.text, intent_result)
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
            redis_client.expire(chat_key, 86400)
            chat_count = redis_client.llen(chat_key)
            logging.info(f"💬 Saved chat to Redis. Total messages: {chat_count}")
            
            # ✅ FIX: Update session last_interaction timestamp
            session_key = f"session:{session_id}"
            if redis_client.exists(session_key):
                redis_client.hset(session_key, "last_interaction", datetime.utcnow().isoformat())
                logging.info(f"⏰ Updated last_interaction for session {session_id}")
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

        return {
            "answer": final_answer,
            "similar_questions": result["suggestions"],
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
        return await collect_user_data(user_data)
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
