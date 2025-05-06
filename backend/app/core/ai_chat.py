# app/core/ai_chat.py

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# System prompt that gives context to the AI about being a health assistant
SYSTEM_PROMPT = """You are HealthMate, a friendly AI health assistant.
Your role is to provide helpful information about general health topics, 
wellness advice, and healthy lifestyle suggestions.
Keep responses concise and conversational.
Do not provide specific medical diagnosis or treatment advice.
If asked about serious medical issues, suggest consulting a healthcare professional."""

class AIChat:
    def __init__(self, model="tinyllama", api_url="http://localhost:11435/api/generate"):
        self.model = model
        self.api_url = api_url
        self.conversation_history = []
        self.timeout = 30.0  # seconds
        
    def _build_prompt(self, user_text: str) -> str:
        """
        Build a prompt with conversation history and system context.
        """
        if not self.conversation_history:
            # First message - include system prompt
            full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_text}\nHealthMate:"
        else:
            # Build history
            history = "\n".join(self.conversation_history[-4:])  # Keep last 4 exchanges
            full_prompt = f"{history}\nUser: {user_text}\nHealthMate:"
            
        return full_prompt
        
    def generate_reply(self, user_text: str) -> str:
        """
        Generates an AI reply using Ollama's model.
        Returns the AI's response text.
        """
        if not user_text or user_text.strip() == "":
            return "I didn't catch that. Could you please repeat?"
            
        prompt = self._build_prompt(user_text)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 150,  # Keep responses concise for voice
        }
        
        try:
            logger.info(f"Sending request to Ollama: {self.model}")
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.api_url, json=payload)
                
            if response.status_code != 200:
                logger.error(f"Error from Ollama API: {response.status_code} {response.text}")
                return "Sorry, I'm having trouble connecting to my brain right now."
                
            data = response.json()
            ai_response = data.get('response', '').strip()
            
            # Update conversation history
            self.conversation_history.append(f"User: {user_text}")
            self.conversation_history.append(f"HealthMate: {ai_response}")
            
            # Keep history from growing too large
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
                
            return ai_response
                
        except httpx.TimeoutException:
            logger.error("Request to Ollama timed out")
            return "Sorry, it's taking me longer than expected to think. Could you try again?"
            
        except Exception as e:
            logger.exception(f"Error generating AI response: {e}")
            return "I'm having trouble processing your request right now. Let's try again."

# Singleton instance
_ai_chat = None

def get_ai_chat() -> AIChat:
    """Get or create the AI chat instance"""
    global _ai_chat
    if _ai_chat is None:
        _ai_chat = AIChat()
    return _ai_chat

def generate_reply(user_text: str) -> str:
    """
    Generate a reply to the user's text.
    This is the main function to be used by other modules.
    """
    ai = get_ai_chat()
    return ai.generate_reply(user_text)
