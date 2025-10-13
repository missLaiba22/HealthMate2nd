from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class Message(BaseModel):
    """Message model for conversation history"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

class Conversation(BaseModel):
    """Conversation model for MongoDB storage"""
    email: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    context_window: int = 10

class ConversationHistory(BaseModel):
    """Simplified model for conversation history tracking"""
    email: str
    context_window: int = 10
    messages: List[Dict[str, str]] = []

    class Config:
        from_attributes = True

