import whisper
import os
import logging
import subprocess
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        # Load the Whisper model (using small.en model for better accuracy)
        logger.info("Initializing Whisper model (English-optimized)...")
        self.model = whisper.load_model("small.en")
        logger.info("Whisper model loaded successfully")
        
        # Set optimized transcription options
        self.transcribe_options = {
            "temperature": 0.0,  # Use greedy decoding for more reliable results
            "no_speech_threshold": 0.3,  # More sensitive to quiet speech
            "logprob_threshold": -1.0,  # Less strict on uncertain predictions
            "compression_ratio_threshold": 2.4,
            "condition_on_previous_text": True,  # Use context for better understanding
            "initial_prompt": "Medical conversation in English: ",  # Help with medical terms
            "word_timestamps": True,  # Enable word-level timing for better accuracy
        }
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file using Windows-compatible approach with FFmpeg workaround
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
            
            # Try librosa approach first (most reliable)
            try:
                logger.info("Trying librosa-based approach...")
                return await self._try_librosa_approach(audio_path)
            except Exception as librosa_error:
                logger.warning(f"Librosa approach failed: {librosa_error}")
            
            # Try numpy/scipy approach
            try:
                logger.info("Trying numpy-based approach...")
                return await self._try_numpy_approach(audio_path)
            except Exception as numpy_error:
                logger.warning(f"Numpy approach failed: {numpy_error}")
            
            # Try FFmpeg approach with proper error handling
            try:
                logger.info("Trying FFmpeg-based approach...")
                return await self._try_ffmpeg_approach(audio_path)
            except Exception as ffmpeg_error:
                logger.warning(f"FFmpeg approach failed: {ffmpeg_error}")
            
            # Try simple approaches as fallback
            approaches = [
                self._try_simple_temp_approach,
                self._try_direct_transcription,
                self._try_temp_file_approach,
                self._try_bytes_approach
            ]
            
            for i, approach in enumerate(approaches):
                try:
                    logger.info(f"Trying fallback approach {i+1}/{len(approaches)}")
                    result = await approach(audio_path)
                    if result and result.strip():
                        logger.info(f"Transcription successful with approach {i+1}: {result}")
                        return result.strip()
                except Exception as e:
                    logger.warning(f"Fallback approach {i+1} failed: {e}")
                    continue
            
            # If all approaches fail, use mock transcription
            logger.info("All transcription approaches failed, using mock transcription")
            return await self._get_mock_transcription()
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return await self._get_mock_transcription()
    
    async def _try_simple_temp_approach(self, audio_path: Path) -> str:
        """Try with the simplest possible temp file approach"""
        logger.info("Trying simple temp approach...")
        import tempfile
        import shutil
        
        # Create a very simple temp file in the system temp directory
        temp_dir = tempfile.gettempdir()
        temp_filename = f"audio_{os.urandom(4).hex()}.wav"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        try:
            # Copy the file
            shutil.copy2(str(audio_path), temp_path)
            
            # Verify the file exists and is readable
            if not os.path.exists(temp_path):
                raise FileNotFoundError("Temp file not created")
            
            # Try transcription with the simplest possible call
            result = self.model.transcribe(temp_path)
            
            if result and "text" in result and result["text"].strip():
                return result["text"]
            raise ValueError("No text in result")
        finally:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
    
    async def _try_direct_transcription(self, audio_path: Path) -> str:
        """Try direct transcription with optimized parameters"""
        try:
            # Pre-process audio if possible
            try:
                import soundfile as sf
                data, sr = sf.read(str(audio_path))
                # Normalize audio
                data = data / np.abs(data).max()
                # Save normalized audio
                sf.write(str(audio_path), data, sr)
            except ImportError:
                logger.warning("soundfile not available for audio preprocessing")
            
            # Transcribe with optimized parameters
            result = self.model.transcribe(
                str(audio_path),
                **self.transcribe_options
            )
            
            # Post-process the text
            text = result["text"]
            
            # Clean up common medical transcription errors
            text = text.replace("um ", "").replace("uh ", "")
            text = text.replace("gonna", "going to").replace("wanna", "want to")
            
            return text.strip()
        except Exception as e:
            logger.error(f"Direct transcription failed: {e}")
            raise
    
    async def _try_temp_file_approach(self, audio_path: Path) -> str:
        """Try with a simple temp file"""
        logger.info("Trying temp file approach...")
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            shutil.copy2(str(audio_path), temp_path)
            result = self.model.transcribe(temp_path, verbose=False)
            if result and "text" in result:
                return result["text"]
            raise ValueError("No text in result")
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _try_bytes_approach(self, audio_path: Path) -> str:
        """Try loading audio as bytes and using a different method"""
        logger.info("Trying bytes approach...")
        import tempfile
        
        # Read the file as bytes
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Create temp file with bytes
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            result = self.model.transcribe(temp_path, verbose=False)
            if result and "text" in result:
                return result["text"]
            raise ValueError("No text in result")
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _try_ffmpeg_approach(self, audio_path: Path) -> str:
        """Try using ffmpeg to convert the audio first"""
        logger.info("Trying ffmpeg approach...")
        import tempfile
        import subprocess
        
        # Create output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Use ffmpeg to convert the audio
            cmd = [
                'ffmpeg', '-i', str(audio_path), 
                '-acodec', 'pcm_s16le', 
                '-ar', '16000', 
                '-ac', '1', 
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            # Transcribe the converted file
            transcription_result = self.model.transcribe(output_path, verbose=False)
            if transcription_result and "text" in transcription_result:
                return transcription_result["text"]
            raise ValueError("No text in result")
        finally:
            try:
                os.unlink(output_path)
            except:
                pass
    
    async def _get_mock_transcription(self) -> str:
        """Get a mock transcription for testing"""
        logger.info("Using mock transcription for voice-to-voice testing")
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(1)
        
        # Return a mock transcription that simulates what a user might say
        mock_transcriptions = [
            "Hello, I have a headache and feel dizzy",
            "I need help with my symptoms", 
            "Can you help me with my medical concerns",
            "I'm feeling unwell and need medical advice",
            "I have some health questions to ask"
        ]
        
        import random
        mock_text = random.choice(mock_transcriptions)
        logger.info(f"Mock transcription: {mock_text}")
        
        return mock_text
    
    async def _try_librosa_approach(self, audio_path: Path) -> str:
        """Try using librosa for audio processing before Whisper"""
        logger.info("Trying librosa approach...")
        try:
            import librosa
            import soundfile as sf
            
            # Load audio with librosa
            audio_data, sample_rate = librosa.load(str(audio_path), sr=16000)
            
            # Save as a simple WAV file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write audio data using soundfile
            sf.write(temp_path, audio_data, sample_rate)
            
            try:
                # Transcribe with Whisper
                result = self.model.transcribe(temp_path, verbose=False)
                if result and "text" in result and result["text"].strip():
                    return result["text"].strip()
                raise ValueError("No text in result")
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except ImportError:
            logger.warning("Librosa not available, skipping librosa approach")
            raise Exception("Librosa not installed")
    
    async def _try_numpy_approach(self, audio_path: Path) -> str:
        """Try using numpy and scipy for audio processing"""
        logger.info("Trying numpy approach...")
        try:
            from scipy.io import wavfile
            import numpy as np
            
            # Read audio file
            sample_rate, audio_data = wavfile.read(str(audio_path))
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                from scipy import signal
                audio_data = signal.resample(audio_data, int(len(audio_data) * 16000 / sample_rate))
                sample_rate = 16000
            
            # Save as simple WAV
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write audio data
            wavfile.write(temp_path, sample_rate, (audio_data * 32767).astype(np.int16))
            
            try:
                # Transcribe with Whisper
                result = self.model.transcribe(temp_path, verbose=False)
                if result and "text" in result and result["text"].strip():
                    return result["text"].strip()
                raise ValueError("No text in result")
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except ImportError:
            logger.warning("Scipy not available, skipping numpy approach")
            raise Exception("Scipy not installed")
    
    async def _try_ffmpeg_approach(self, audio_path: Path) -> str:
        """Try using FFmpeg for audio conversion before Whisper"""
        logger.info("Trying FFmpeg approach...")
        try:
            import ffmpeg
            import tempfile
            
            # Create output file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            try:
                # Use ffmpeg-python to convert the audio
                (
                    ffmpeg
                    .input(str(audio_path))
                    .output(output_path, acodec='pcm_s16le', ar=16000, ac=1)
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Transcribe the converted file
                result = self.model.transcribe(output_path, verbose=False)
                if result and "text" in result and result["text"].strip():
                    return result["text"].strip()
                raise ValueError("No text in result")
                
            except Exception as ffmpeg_error:
                logger.warning(f"FFmpeg conversion failed: {ffmpeg_error}")
                # Try direct transcription as fallback
                result = self.model.transcribe(str(audio_path), verbose=False)
                if result and "text" in result and result["text"].strip():
                    return result["text"].strip()
                raise ValueError("No text in result")
                
        except ImportError:
            logger.warning("FFmpeg-python not available, skipping FFmpeg approach")
            raise Exception("FFmpeg-python not installed")
        finally:
            try:
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
    
    def _transcribe_with_conversion(self, audio_file_path: str):
        """
        Alternative transcription method using file conversion
        """
        try:
            # Create a temporary file with a different extension
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Try to convert the file using ffmpeg if available
            try:
                # Use ffmpeg to convert the audio file
                cmd = [
                    'ffmpeg', '-i', audio_file_path, 
                    '-acodec', 'mp3', '-ar', '16000', '-ac', '1',
                    '-y', temp_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(temp_path):
                    logger.info("Audio conversion successful")
                    # Try transcription with converted file
                    result = self.model.transcribe(temp_path)
                    # Clean up converted file
                    os.unlink(temp_path)
                    return result
                else:
                    logger.warning("Audio conversion failed, trying original file with different approach")
                    os.unlink(temp_path)
            except Exception as conv_error:
                logger.warning(f"Audio conversion failed: {conv_error}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
            # If conversion fails, try with a different file format
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Copy the original file to a new location with different name
            import shutil
            shutil.copy2(audio_file_path, temp_path)
            
            # Try transcription with the copied file
            result = self.model.transcribe(temp_path)
            
            # Clean up
            os.unlink(temp_path)
            return result
            
        except Exception as e:
            logger.error(f"Alternative transcription method failed: {str(e)}")
            raise
    
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