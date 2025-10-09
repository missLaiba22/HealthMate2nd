from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..services.chat_service import get_ai_response
from ..utils.jwt import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

@router.post("")
@router.post("/")
async def chat(request: ChatRequest, current_user=Depends(get_current_user)):
    """Chat with AI assistant"""
    try:
        email = current_user.get("email", "unknown")
        logger.info(f"Chat request received for email: {email}")
        logger.info(f"Message: {request.message}")
        logger.info(f"User data: {current_user}")
        
        # Input validation
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        logger.info("Calling get_ai_response...")
        response = await get_ai_response(request.message, email)
        logger.info(f"AI response generated: {response[:100]}...")
        
        return {"response": response}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/test")
async def test_chat_auth(current_user=Depends(get_current_user)):
    """Test endpoint to verify chat authentication"""
    return {
        "message": "Chat authentication working",
        "user": current_user.get("email", "unknown"),
        "role": current_user.get("role", "unknown")
    }

@router.post("/simple")
async def simple_chat(request: ChatRequest, current_user=Depends(get_current_user)):
    """Simple chat endpoint that returns a basic response without AI"""
    try:
        email = current_user.get("email", "unknown")
        logger.info(f"Simple chat request from: {email}")
        logger.info(f"Message: {request.message}")
        
        # Return a simple response without AI
        simple_response = f"I heard you say: '{request.message}'. How can I help you with your health concerns?"
        
        return {"response": simple_response}
        
    except Exception as e:
        logger.error(f"Error in simple chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")