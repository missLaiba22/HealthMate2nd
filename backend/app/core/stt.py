# app/core/stt.py

import whisper
import logging
import time
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global whisper model instance
_whisper_model = None

def get_whisper_model(model_name: str = "base"):
    """
    Load or get the Whisper model.
    Using a singleton pattern to avoid reloading the model for each request.
    """
    global _whisper_model
    if _whisper_model is None:
        logger.info(f"Loading Whisper model: {model_name}")
        start_time = time.time()
        _whisper_model = whisper.load_model(model_name)
        logger.info(f"Whisper model loaded in {time.time() - start_time:.2f} seconds")
    return _whisper_model

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes audio file using Whisper model.
    Returns the transcribed text.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        The transcribed text
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return ""
    
    try:
        logger.info(f"Transcribing audio: {audio_path}")
        start_time = time.time()
        
        model = get_whisper_model()
        result = model.transcribe(
            audio_path,
            fp16=False,  # Use CPU if GPU not available
            language="en"  # Specify language for better results
        )
        
        transcription = result['text'].strip()
        logger.info(f"Transcription completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Transcription result: '{transcription}'")
        
        return transcription
        
    except Exception as e:
        logger.exception(f"Error transcribing audio: {e}")
        return ""