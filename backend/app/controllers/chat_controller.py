from fastapi import HTTPException
from app.services.chat_service import get_ai_response

async def chat_controller(message: str, user_id: str) -> str:
    # Input validation
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Check for emergency keywords
    emergency_keywords = ['emergency', 'urgent', 'severe pain', 'heart attack', 'stroke', 
                         'bleeding', 'unconscious', 'suicide', 'life-threatening']
    
    if any(keyword in message.lower() for keyword in emergency_keywords):
        emergency_message = ("IMPORTANT: If this is a medical emergency, immediately call your "
                           "local emergency services (911 in the US) or go to the nearest "
                           "emergency room. Do not wait for an AI response.")
        try:
            ai_response = await get_ai_response(message, user_id)
            return f"{emergency_message}\n\n{ai_response}"
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request. "
                       "If this is a medical emergency, please seek immediate medical attention."
            )
    
    try:
        return await get_ai_response(message, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again."
        )
