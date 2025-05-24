import whisper
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        # Load the Whisper model (using base model for faster inference)
        logger.info("Initializing Whisper model...")
        self.model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully")
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using Whisper
        """
        try:
            # Convert to Path object for better path handling
            audio_path = Path(audio_file_path)
            logger.info(f"Starting transcription of file: {audio_path}")
            
            # Verify file exists and is readable
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            if not os.access(str(audio_path), os.R_OK):
                raise PermissionError(f"Cannot read audio file: {audio_path}")
            
            # Get file size
            file_size = audio_path.stat().st_size
            logger.info(f"Audio file size: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError("Audio file is empty")
            
            # Ensure the file is still accessible
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file became inaccessible: {audio_path}")
            
            # Transcribe the audio file
            logger.info("Starting Whisper transcription...")
            result = self.model.transcribe(str(audio_path))
            logger.info("Transcription completed successfully")
            
            if not result or "text" not in result:
                raise ValueError("Transcription failed - no text in result")
            
            return result["text"]
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str):
        """
        Clean up temporary audio file
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Successfully removed temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temp file: {str(e)}")
            raise

# Create a singleton instance
speech_service = SpeechService() 