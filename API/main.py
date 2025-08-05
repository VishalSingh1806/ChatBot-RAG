from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging
import os
import uuid
from models import QueryRequest, QueryResponse, UserData
from search import find_best_answer
from llm_refiner import refine_with_gemini
from collect_data import collect_user_data, get_user_data_from_session, redis_client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# ✅ Load secret key for session cookies
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_for_development_only")

# Determine if running in production (e.g., on the VM with HTTPS)
IS_PRODUCTION = os.getenv("APP_ENV") == "production"

# ✅ Session middleware (registered before CORS)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    # In production (HTTPS), cookies must be 'none' and secure.
    # For local dev (HTTP), 'lax' and non-secure is required.
    same_site="none" if IS_PRODUCTION else "lax",
    https_only=IS_PRODUCTION,
    session_cookie="session",
    max_age=86400,          # 24 hours
    path="/",
)

# ✅ Apply CORS middleware
allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Server is running"}

@app.post("/session")
async def get_or_create_session(request: Request):
    """Get or create a session for the user"""
    try:
        # Debug session info
        logging.info(f"Incoming session request. Session data: {dict(request.session)}")
        
        if "session_id" not in request.session:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            logging.info(f"✅ Created new session: {session_id}")
        else:
            session_id = request.session["session_id"]
            logging.info(f"✅ Using existing session: {session_id}")

        user_data = await get_user_data_from_session(session_id)

        response_data = {
            "session_id": session_id,
            "user_data_collected": user_data is not None,
            "user_data": user_data
        }
        logging.info(f"📤 Returning session response for {session_id}")
        return response_data
        
    except Exception as e:
        logging.error(f"❌ Error in /session endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Session creation failed")

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: Request, query: QueryRequest):
    """Handle user queries and return responses"""
    try:
        if "session_id" not in request.session:
            # This is a fallback, but frontend should have established a session.
            request.session["session_id"] = str(uuid.uuid4())

        session_id = request.session["session_id"]

        # Fetch user data from session/Redis to get their name
        user_data = await get_user_data_from_session(session_id)
        user_name = user_data.get("user_name") if user_data else None

        # Get conversation history from the request
        history = query.history or []

        # Find the best answer from knowledge base
        result = find_best_answer(query.text)

        # Refine the answer with LLM, providing more context
        final_answer = refine_with_gemini(
            user_name=user_name,
            query=query.text,
            raw_answer=result["answer"],
            history=history,
            is_first_message=(len(history) == 0) # It's the first message if history is empty
        )

        return {
            "answer": final_answer,
            "similar_questions": result["suggestions"]
        }
    except Exception as e:
        logging.error(f"❌ Error in /query endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Query processing failed")

@app.post("/collect_user_data")
async def handle_user_data(request: Request, user_data: UserData):
    """Collect and store user data"""
    try:
        if "session_id" not in request.session:
            logging.warning("No session_id found in /collect_user_data request.")
            raise HTTPException(status_code=400, detail="Session not found. Please refresh the page.")

        session_id = request.session["session_id"]
        logging.info(f"Found session_id for data collection: {session_id}")
        
        user_data.session_id = session_id
        result = await collect_user_data(user_data)
        logging.info(f"✅ User data collected successfully for session: {session_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Error in /collect_user_data endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Data collection failed")


# uvicorn main:app --reload