from fastapi import HTTPException
from services.chat_service import get_ai_response

async def chat_controller(message: str) -> str:
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return await get_ai_response(message)
