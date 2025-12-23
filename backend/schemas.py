from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    messages: List[Message]

class UpdateGoalsRequest(BaseModel):
    goals: str

class UpdateKnowledgeRequest(BaseModel):
    category: str
    content: str

class UpdateDescriptionRequest(BaseModel):
    description: str
