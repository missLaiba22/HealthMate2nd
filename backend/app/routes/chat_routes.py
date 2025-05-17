from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from utils.jwt import get_current_user  # adjust if named differently
from controllers.chat_controller import chat_controller

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

@router.post("/")
async def chat(request: ChatRequest, current_user=Depends(get_current_user)):
    response = await chat_controller(request.message)
    return {"response": response}
