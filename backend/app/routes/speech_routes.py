from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from ..services.speech_service import SpeechService
from ..utils.jwt import get_current_user
import logging
import tempfile
import os

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Speech"])

# Initialize service
speech_service = SpeechService()

@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """Transcribe audio to text using Whisper"""
    try:
        logger.info(f"Speech transcription request from user: {current_user.get('email', 'unknown')}")
        logger.info(f"Audio file: {audio_file.filename}, size: {audio_file.size}")
        logger.info(f"User data: {current_user}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe audio
            transcription = await speech_service.transcribe_audio(temp_file_path)
            
            return {
                "transcription": transcription,
                "filename": audio_file.filename,
                "file_size": len(content)
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/test")
async def test_speech_auth(current_user=Depends(get_current_user)):
    """Test endpoint to verify speech authentication"""
    return {
        "message": "Speech authentication working",
        "user": current_user.get("email", "unknown"),
        "role": current_user.get("role", "unknown")
    }

