# app/api/ws_chat.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import tempfile
import wave
import asyncio
import os
from app.core.stt import transcribe_audio
from app.core.tts import text_to_speech
from app.core.ai_chat import generate_reply
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/voice-chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that receives raw PCM audio chunks from the Flutter client,
    wraps them into a WAV format, performs STT, generates an AI TTS response,
    and sends back the WAV audio bytes.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            try:
                # Receive raw PCM bytes (16-bit PCM, mono, 16kHz)
                pcm_bytes = await websocket.receive_bytes()

                if not pcm_bytes:
                    logger.warning("Received empty audio data")
                    continue

                logger.info(f"Received audio chunk: {len(pcm_bytes)} bytes")

                # Wrap raw PCM in WAV header
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                    with wave.open(temp_audio.name, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)  # 16-bit width -> 2 bytes
                        wav_file.setframerate(16000)  # 16kHz sample rate
                        wav_file.writeframes(pcm_bytes)
                    audio_path = temp_audio.name

                # Speech to Text
                logger.info("Transcribing audio...")
                user_text = transcribe_audio(audio_path)
                logger.info(f"User said: {user_text}")

                if not user_text or user_text.strip() == "":
                    logger.warning("Empty transcription result, skipping")
                    os.unlink(audio_path)
                    continue

                # Generate AI Response
                logger.info("Generating AI response...")
                ai_reply = generate_reply(user_text)
                logger.info(f"AI reply: {ai_reply}")

                # Text to Speech (returns WAV file path)
                logger.info("Converting to speech...")
                audio_response_path = await text_to_speech(ai_reply)

                # Read and send back the WAV bytes
                with open(audio_response_path, "rb") as f:
                    response_bytes = f.read()
                    logger.info(f"Sending audio response: {len(response_bytes)} bytes")
                    await websocket.send_bytes(response_bytes)

                # Clean up temporary files
                os.unlink(audio_path)
                os.unlink(audio_response_path)

                # Brief pause to avoid overwhelming client
                await asyncio.sleep(0.1)

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
    finally:
        # No need to explicitly close the connection here
        # as the WebSocket will be closed by the framework
        logger.info("WebSocket connection ended")
