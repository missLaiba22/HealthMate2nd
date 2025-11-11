import whisper
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        # Load the Whisper model (using small.en model for better English accuracy)
        logger.info("Initializing Whisper model (English-optimized)...")
        try:
            self.model = whisper.load_model("small.en")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            # Fallback to base model if small.en fails
            logger.info("Attempting to load base model as fallback...")
            self.model = whisper.load_model("base")
            logger.info("Base Whisper model loaded successfully")
        
        # Set optimized transcription options for medical conversations
        self.transcribe_options = {
            "language": "en",  # Force English language
            "temperature": 0.0,  # Use greedy decoding for consistency
            "no_speech_threshold": 0.2,  # More sensitive to speech detection
            "logprob_threshold": -1.0,  # Allow lower confidence predictions
            "compression_ratio_threshold": 2.4,
            "condition_on_previous_text": False,  # Don't rely on previous context to avoid errors
            "initial_prompt": "Medical symptoms, health questions, appointment scheduling: ",  # Medical context
        }
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using optimized Whisper approach with API compatibility fix
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
            
            # Preprocess audio for better transcription
            processed_audio_path = await self._preprocess_audio(audio_path)
            
            # Use compatibility-safe transcription approach
            logger.info("Starting Whisper transcription with compatibility mode...")
            result = await self._safe_transcribe(processed_audio_path)
            
            # Clean up temporary processed file if different from original
            if processed_audio_path != audio_path:
                try:
                    os.unlink(processed_audio_path)
                except:
                    pass
            
            if result and "text" in result:
                transcribed_text = result["text"].strip()
                logger.info(f"Raw transcription result: '{transcribed_text}'")
                
                # Clean up the transcribed text
                cleaned_text = self._clean_transcription(transcribed_text)
                
                if cleaned_text and len(cleaned_text) > 0:
                    logger.info(f"Final cleaned transcription: '{cleaned_text}'")
                    return cleaned_text
                else:
                    logger.warning("Transcription returned empty text after cleaning")
                    return "I didn't catch that clearly. Could you please speak again?"
            else:
                logger.error("No text found in transcription result")
                logger.error(f"Full result: {result}")
                raise ValueError("No text in transcription result")
            
        except Exception as e:
            logger.error(f"Transcription failed with error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Return a helpful error message instead of random mock text
            return "I'm having trouble hearing you clearly. Please try speaking again."
    
    async def _safe_transcribe(self, audio_path: Path) -> dict:
        """
        Safe transcription method that handles API compatibility issues
        """
        try:
            # Try the direct approach first (works with most versions)
            logger.info("Attempting direct transcription...")
            
            # Use minimal options to avoid compatibility issues
            basic_options = {
                "language": "en",
                "temperature": 0.0,
            }
            
            result = self.model.transcribe(str(audio_path), **basic_options)
            logger.info("Direct transcription successful")
            return result
            
        except TypeError as e:
            logger.warning(f"Direct transcription failed with TypeError: {e}")
            logger.info("Trying compatibility mode...")
            
            # Fallback: use the most basic transcription call
            try:
                result = self.model.transcribe(str(audio_path))
                logger.info("Basic transcription successful")
                return result
            except Exception as e2:
                logger.error(f"Basic transcription also failed: {e2}")
                raise e2
                
        except Exception as e:
            logger.error(f"Transcription failed with: {e}")
            raise

    async def _preprocess_audio(self, audio_path: Path) -> Path:
        """
        Preprocess audio file for better transcription quality
        Returns path to processed file (may be same as input if no processing needed)
        """
        try:
            # Try to use soundfile for audio preprocessing if available
            try:
                import soundfile as sf
                import numpy as np
                
                logger.info("Preprocessing audio with soundfile...")
                
                # Read audio data
                data, sample_rate = sf.read(str(audio_path))
                logger.info(f"Original audio: sample_rate={sample_rate}, shape={data.shape}")
                
                # Normalize audio to prevent clipping
                if len(data) > 0:
                    max_val = np.abs(data).max()
                    if max_val > 0:
                        data = data / max_val * 0.8  # Leave some headroom
                
                # Create temporary processed file
                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', prefix='processed_')
                os.close(temp_fd)  # Close the file descriptor
                
                # Write processed audio
                sf.write(temp_path, data, sample_rate)
                logger.info(f"Audio preprocessed and saved to: {temp_path}")
                
                return Path(temp_path)
                
            except ImportError:
                logger.info("soundfile not available, using original audio file")
                return audio_path
            except Exception as e:
                logger.warning(f"Audio preprocessing failed: {e}, using original file")
                return audio_path
                
        except Exception as e:
            logger.error(f"Error in audio preprocessing: {e}")
            return audio_path

    def _clean_transcription(self, text: str) -> str:
        """Clean and normalize transcribed text"""
        if not text:
            return ""
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove filler words and speech artifacts
        filler_words = ["um", "uh", "er", "ah", "hmm"]
        for filler in filler_words:
            text = text.replace(f" {filler} ", " ")
            text = text.replace(f"{filler} ", "")
            text = text.replace(f" {filler}", "")
        
        # Fix common contractions
        contractions = {
            "gonna": "going to",
            "wanna": "want to", 
            "gotta": "got to",
            "lemme": "let me",
            "gimme": "give me",
            "dunno": "don't know"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        # Clean up multiple spaces
        text = " ".join(text.split())
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        return text
    

    
 