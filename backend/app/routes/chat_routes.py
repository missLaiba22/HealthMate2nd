from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.utils.jwt import get_current_user
from app.controllers.chat_controller import chat_controller, ChatRequest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])

@router.post("")
@router.post("/")
async def chat(request: ChatRequest, current_user=Depends(get_current_user)):
    # Extract email from the JWT token
    email = current_user["email"]
    logger.info(f"Chat request received for email: {email}")
    response = await chat_controller(request, email)
    return {"response": response}
