from pydantic import BaseModel
from typing import List, Optional, Dict


class QueryRequest(BaseModel):
    session_id: Optional[str] = None
    text: str
    history: Optional[List[Dict[str, str]]] = []

class UserData(BaseModel):
    session_id: Optional[str] = None
    name: str
    email: str
    phone: str
    organization: str

class IntentInfo(BaseModel):
    type: str
    confidence: float
    should_connect: bool

class QueryResponse(BaseModel):
    answer: str
    similar_questions: Optional[List[str]] = None
    intent: Optional[IntentInfo] = None