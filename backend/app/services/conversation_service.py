from typing import List, Dict, Optional
from datetime import datetime
from ..models.chat import ConversationHistory, Message, Conversation
from ..database import db
import logging

logger = logging.getLogger(__name__)

class ConversationService:
    """Service layer for conversation management - handles all business logic"""
    
    def __init__(self):
        self.context_window = 10
        # Create index for better query performance
        try:
            db.conversations.create_index([("email", 1)])
            logger.info("Successfully created index on email field in conversations collection")
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")

    def add_message(self, email: str, role: str, content: str) -> bool:
        """Add a message to the conversation history in MongoDB (single doc per user)."""
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            logger.info(f"Adding message for email: {email}, role: {role}")
            
            # Use atomic operation to prevent race conditions
            result = db.conversations.update_one(
                {"email": email},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {"created_at": datetime.utcnow(), "context_window": self.context_window}
                },
                upsert=True
            )
            
            # Log the result of the operation
            if result.upserted_id:
                logger.info(f"Created new conversation document for email: {email}")
            elif result.modified_count > 0:
                logger.info(f"Updated existing conversation for email: {email}")
            else:
                logger.warning(f"No changes made to conversation for email: {email}")
            
            return True
                
        except Exception as e:
            logger.error(f"Error adding message to MongoDB: {str(e)}")
            return False

    def get_context(self, email: str) -> List[Dict[str, str]]:
        """Get recent conversation context from the user's messages array."""
        try:
            logger.info(f"Getting context for email: {email}")
            convo = db.conversations.find_one(
                {"email": email}, 
                {"_id": 0, "messages": 1}
            )
            
            if not convo or "messages" not in convo:
                logger.info(f"No conversation found for email: {email}")
                return []
                
            # Get the last N messages
            messages = convo["messages"][-self.context_window:]
            logger.info(f"Retrieved {len(messages)} messages for email: {email}")
            return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            
        except Exception as e:
            logger.error(f"Error getting context from MongoDB: {str(e)}")
            return []

    def clear_history(self, email: str) -> bool:
        """Clear conversation history for this user."""
        try:
            logger.info(f"Clearing history for email: {email}")
            result = db.conversations.delete_one({"email": email})
            if result.deleted_count > 0:
                logger.info(f"Successfully cleared history for email: {email}")
                return True
            else:
                logger.info(f"No history found to clear for email: {email}")
                return False
        except Exception as e:
            logger.error(f"Error clearing history from MongoDB: {str(e)}")
            return False

    def get_conversation(self, email: str) -> List[Dict]:
        """Get the full conversation history for this user."""
        try:
            logger.info(f"Getting full conversation for email: {email}")
            convo = db.conversations.find_one(
                {"email": email}, 
                {"_id": 0, "messages": 1}
            )
            if convo and "messages" in convo:
                logger.info(f"Retrieved {len(convo['messages'])} messages for email: {email}")
                return convo["messages"]
            logger.info(f"No conversation found for email: {email}")
            return []
        except Exception as e:
            logger.error(f"Error getting conversation from MongoDB: {str(e)}")
            return []

    def add_conversation_turn(self, email: str, user_message: str, assistant_message: str) -> bool:
        """Add a complete conversation turn (user + assistant) atomically."""
        try:
            user_msg = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow()
            }
            
            assistant_msg = {
                "role": "assistant", 
                "content": assistant_message,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"Adding conversation turn for email: {email}")
            
            # Atomic operation to add both messages
            result = db.conversations.update_one(
                {"email": email},
                {
                    "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {"created_at": datetime.utcnow(), "context_window": self.context_window}
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Created new conversation document for email: {email}")
            elif result.modified_count > 0:
                logger.info(f"Updated existing conversation for email: {email}")
            else:
                logger.warning(f"No changes made to conversation for email: {email}")
            
            return True
                
        except Exception as e:
            logger.error(f"Error adding conversation turn to MongoDB: {str(e)}")
            return False

    def get_conversation_stats(self, email: str) -> Dict:
        """Get conversation statistics for a user."""
        try:
            convo = db.conversations.find_one(
                {"email": email},
                {"_id": 0, "messages": 1, "created_at": 1, "updated_at": 1}
            )
            
            if not convo:
                return {"total_messages": 0, "created_at": None, "updated_at": None}
            
            total_messages = len(convo.get("messages", []))
            return {
                "total_messages": total_messages,
                "created_at": convo.get("created_at"),
                "updated_at": convo.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {str(e)}")
            return {"total_messages": 0, "created_at": None, "updated_at": None}

