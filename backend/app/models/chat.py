from typing import List, Dict
from datetime import datetime
from app.database import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationHistory:
    def __init__(self, email: str):
        self.email = email
        self.context_window = 10  # Keep last 10 messages for context
        logger.info(f"Initialized ConversationHistory for email: {email}")

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history in MongoDB (single doc per user)."""
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            logger.info(f"Adding message for email: {self.email}, role: {role}")
            
            # Log the MongoDB operation
            result = db.conversations.update_one(
                {"email": self.email},
                {"$push": {"messages": message}},
                upsert=True
            )
            
            # Log the result of the operation
            if result.upserted_id:
                logger.info(f"Created new conversation document for email: {self.email}")
            elif result.modified_count > 0:
                logger.info(f"Updated existing conversation for email: {self.email}")
            else:
                logger.warning(f"No changes made to conversation for email: {self.email}")
                
        except Exception as e:
            logger.error(f"Error adding message to MongoDB: {str(e)}")
            raise

    def get_context(self) -> List[Dict[str, str]]:
        """Get recent conversation context from the user's messages array."""
        try:
            logger.info(f"Getting context for email: {self.email}")
            convo = db.conversations.find_one({"email": self.email}, {"_id": 0, "messages": 1})
            
            if not convo:
                logger.info(f"No conversation found for email: {self.email}")
                return []
                
            if "messages" not in convo:
                logger.info(f"No messages found in conversation for email: {self.email}")
                return []
                
            # Get the last N messages
            messages = convo["messages"][-self.context_window:]
            logger.info(f"Retrieved {len(messages)} messages for email: {self.email}")
            return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            
        except Exception as e:
            logger.error(f"Error getting context from MongoDB: {str(e)}")
            return []

    def clear_history(self):
        """Clear conversation history for this user."""
        try:
            logger.info(f"Clearing history for email: {self.email}")
            result = db.conversations.delete_one({"email": self.email})
            if result.deleted_count > 0:
                logger.info(f"Successfully cleared history for email: {self.email}")
            else:
                logger.info(f"No history found to clear for email: {self.email}")
        except Exception as e:
            logger.error(f"Error clearing history from MongoDB: {str(e)}")
            raise

    def get_conversation(self):
        """Get the full conversation history for this user."""
        try:
            logger.info(f"Getting full conversation for email: {self.email}")
            convo = db.conversations.find_one({"email": self.email}, {"_id": 0, "messages": 1})
            if convo and "messages" in convo:
                logger.info(f"Retrieved {len(convo['messages'])} messages for email: {self.email}")
                return convo["messages"]
            logger.info(f"No conversation found for email: {self.email}")
            return []
        except Exception as e:
            logger.error(f"Error getting conversation from MongoDB: {str(e)}")
            return []

# Create index for better query performance
try:
    db.conversations.create_index([("email", 1)])
    logger.info("Successfully created index on email field in conversations collection")
except Exception as e:
    logger.error(f"Error creating index: {str(e)}") 