from typing import List, Dict
from datetime import datetime
from app.database import db

class ConversationHistory:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.context_window = 10  # Keep last 10 messages for context

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history in MongoDB."""
        message = {
            "user_id": self.user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        db.conversations.insert_one(message)

    def get_context(self) -> List[Dict[str, str]]:
        """Get recent conversation context from MongoDB."""
        messages = list(
            db.conversations.find(
                {"user_id": self.user_id},
                {"_id": 0, "role": 1, "content": 1}
            )
            .sort("timestamp", -1)
            .limit(self.context_window)
        )
        # Reverse to get chronological order
        messages.reverse()
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def clear_history(self):
        """Clear conversation history for this user."""
        db.conversations.delete_many({"user_id": self.user_id})

# Create index for better query performance
db.conversations.create_index([("user_id", 1), ("timestamp", -1)]) 