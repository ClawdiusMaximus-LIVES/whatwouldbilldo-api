from pydantic import BaseModel
from typing import Optional

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class AskRequest(BaseModel):
    message: str
    conversation_history: list[Message] = []
    user_name: Optional[str] = None

class Citation(BaseModel):
    source: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    similarity: float

class CrisisResource(BaseModel):
    name: str
    contact: str

class AskResponse(BaseModel):
    response: Optional[str] = None
    citations: list[Citation] = []
    crisis: bool = False
    crisis_message: Optional[str] = None
    crisis_resources: list[CrisisResource] = []

class HealthResponse(BaseModel):
    status: str
    passages_count: int

class DailyReflectionResponse(BaseModel):
    passage: str
    source: str
    reflection: str
