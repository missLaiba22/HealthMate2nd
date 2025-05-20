from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.utils.jwt import get_current_user
from app.controllers.chat_controller import chat_controller

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat(request: ChatRequest, current_user=Depends(get_current_user)):
    # Extract user_id from the JWT token
    user_id = current_user["user_id"]
    response = await chat_controller(request.message, user_id)
    return {"response": response}
