from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import uuid
from models import QueryRequest, QueryResponse, UserData
from search import find_best_answer
from llm_refiner import refine_with_gemini
from collect_data import collect_user_data, get_user_data_from_session

app = FastAPI()

# ✅ Load secret key for session cookies
SECRET_KEY = os.getenv("SECRET_KEY", "a_default_secret_key_for_development_only")

# ✅ Apply CORS middleware FIRST — before session
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],  # Multiple frontend URLs for flexibility
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight response for 1 hour
)

# ✅ Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",         # Good for localhost
    https_only=False,        # Required for local dev over HTTP
    session_cookie="session",
    max_age=86400,          # 24 hours
    path="/",
    domain=None             # Allow any domain for localhost
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
        print(f"🔍 Session data: {dict(request.session)}")
        print(f"🔍 Headers: {dict(request.headers)}")
        
        if "session_id" not in request.session:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            print(f"✅ Created new session: {session_id}")
        else:
            session_id = request.session["session_id"]
            print(f"✅ Using existing session: {session_id}")

        user_data = await get_user_data_from_session(session_id)

        response_data = {
            "session_id": session_id,
            "user_data_collected": user_data is not None,
            "user_data": user_data
        }
        
        print(f"📤 Returning session response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"❌ Error in session endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Session creation failed")

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: Request, query: QueryRequest):
    """Handle user queries and return responses"""
    try:
        if "session_id" not in request.session:
            request.session["session_id"] = str(uuid.uuid4())

        session_id = request.session["session_id"]
        result = find_best_answer(query.text)
        final_answer = refine_with_gemini(query.text, result["answer"])

        return {
            "answer": final_answer,
            "similar_questions": result["suggestions"]
        }
    except Exception as e:
        print(f"❌ Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail="Query processing failed")

@app.post("/collect_user_data")
async def handle_user_data(request: Request, user_data: UserData):
    """Collect and store user data"""
    try:
        # Debug session info
        print(f"🔍 collect_user_data - Session data: {dict(request.session)}")
        print(f"🔍 collect_user_data - Headers: {dict(request.headers)}")
        
        if "session_id" not in request.session:
            print("❌ No session_id found in session")
            print(f"🔍 Available session keys: {list(request.session.keys())}")
            raise HTTPException(status_code=400, detail="Session not found. Please refresh the page.")

        session_id = request.session["session_id"]
        print(f"✅ Found session_id: {session_id}")
        
        user_data.session_id = session_id
        result = await collect_user_data(user_data)
        print(f"✅ User data collected successfully for session: {session_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in collect_user_data endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Data collection failed")

# Add explicit OPTIONS handlers for problematic endpoints
@app.options("/session")
async def options_session():
    """Handle OPTIONS request for session endpoint"""
    return {"message": "OK"}

@app.options("/collect_user_data")
async def options_collect_user_data():
    """Handle OPTIONS request for collect_user_data endpoint"""
    return {"message": "OK"}

@app.options("/query")
async def options_query():
    """Handle OPTIONS request for query endpoint"""
    return {"message": "OK"}

# uvicorn main:app --reload --host localhost --port 8000
