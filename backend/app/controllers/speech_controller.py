from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.speech_service import speech_service
import os
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe audio file using Whisper
    """
    temp_file_path = None
    try:
        # Create a temporary directory if it doesn't exist
        temp_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "temp_audio"
        temp_dir.mkdir(exist_ok=True)
        
        # Create a unique filename with .wav extension
        temp_file_path = temp_dir / f"temp_audio_{os.urandom(8).hex()}.wav"
        logger.info(f"Created temporary file path: {temp_file_path}")
        
        # Read the uploaded file content
        content = await audio_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file received")
        
        # Write the content to the temporary file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        
        # Verify the file was written correctly
        if not temp_file_path.exists():
            raise HTTPException(status_code=500, detail="Failed to create temporary file")
        
        file_size = temp_file_path.stat().st_size
        logger.info(f"Temporary file created successfully. Size: {file_size} bytes")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe the audio
        logger.info(f"Starting transcription of file: {temp_file_path}")
        transcription = await speech_service.transcribe_audio(str(temp_file_path))
        logger.info("Transcription completed successfully")
        
        return {"text": transcription}

    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}") 