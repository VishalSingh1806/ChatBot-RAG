from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    session_id: Optional[str] = None
    text: str

class UserData(BaseModel):
    session_id: Optional[str] = None
    name: str
    email: str
    phone: str
    organization: str

class QueryResponse(BaseModel):
    answer: str
    similar_questions: Optional[List[str]] = None