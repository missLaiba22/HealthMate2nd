# app/core/tts.py
import edge_tts
import asyncio
import uuid
import os
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Voice options
AVAILABLE_VOICES = {
    "female": "en-US-JennyNeural",  # Default female voice
    "male": "en-US-GuyNeural",      # Male voice
}

DEFAULT_VOICE = AVAILABLE_VOICES["female"]
TEMP_DIR = tempfile.gettempdir()

async def text_to_speech(text: str, voice: str = DEFAULT_VOICE) -> str:
    """
    Converts text to speech using edge_tts and saves as a WAV file.
    Returns the path to the generated WAV file.
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (from AVAILABLE_VOICES)
        
    Returns:
        Path to the generated WAV file
    """
    if not text or text.strip() == "":
        logger.warning("Empty text provided to TTS")
        text = "I didn't get that. Could you try again?"
    
    # Sanitize text - remove any characters that might cause issues
    text = text.strip().replace("\n", " ").replace("\"", "'")
    
    # Make sure we have a valid voice
    if voice not in AVAILABLE_VOICES.values():
        voice = DEFAULT_VOICE
        
    try:
        # Create a unique filename
        output_file = os.path.join(TEMP_DIR, f"healthmate_tts_{uuid.uuid4().hex}.wav")
        
        logger.info(f"Generating speech for text: '{text[:50]}...' using voice {voice}")
        start_time = asyncio.get_event_loop().time()
        
        # Create communicate object
        communicate = edge_tts.Communicate(text, voice)
        
        # Save audio to file
        await communicate.save(output_file)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"TTS generated in {elapsed:.2f} seconds: {output_file}")
        
        return output_file
        
    except Exception as e:
        logger.exception(f"Error generating speech: {e}")
        
        # If there's an error, try to provide a fallback audio file
        # This is a simple approach - in production you might want a pre-recorded 
        # "Sorry, there was an error" audio file
        fallback_file = os.path.join(TEMP_DIR, "healthmate_tts_error.wav")
        if not os.path.exists(fallback_file):
            # Create a simple error message audio if it doesn't exist
            fallback_communicate = edge_tts.Communicate(
                "Sorry, I'm having trouble speaking right now.", 
                DEFAULT_VOICE
            )
            await fallback_communicate.save(fallback_file)
        
        return fallback_file

# Function to get available voices - can be useful for future expansion
async def get_available_voices():
    """Get all available voices from edge-tts"""
    try:
        voices = await edge_tts.list_voices()
        return voices
    except Exception as e:
        logger.exception(f"Error getting available voices: {e}")
        return []