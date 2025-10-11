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

class ConversationHistory:
    """Pure data model for conversation history - no business logic"""
    def __init__(self, email: str):
        self.email = email
        self.context_window = 10
        logger.info(f"Initialized ConversationHistory for email: {email}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for MongoDB storage"""
        return {
            "email": self.email,
            "context_window": self.context_window
        }