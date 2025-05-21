from openai import OpenAI
import os
from dotenv import load_dotenv
from .prompt_service import MedicalPromptEngine
from ..models.chat import ConversationHistory
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
prompt_engine = MedicalPromptEngine()

def get_conversation_history(email: str) -> ConversationHistory:
    """Get conversation history for a user."""
    logger.info(f"Getting conversation history for email: {email}")
    return ConversationHistory(email)

async def get_ai_response(message: str, email: str) -> str:
    # Get conversation history
    logger.info(f"Getting AI response for email: {email}")
    history = get_conversation_history(email)
    
    # Create appropriate prompt based on message content
    prompt = prompt_engine.create_response_prompt(message)
    
    # If not health-related, return the redirect message directly
    if not prompt_engine.is_health_related(message):
        history.add_message("user", message)
        history.add_message("assistant", prompt)
        return prompt

    # Create message list with context
    messages = [
        {"role": "system", "content": prompt_engine.system_context},
        *history.get_context(),
        {"role": "user", "content": prompt}
    ]
    
    # Get response from OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=150  # Keep responses concise
    )
    
    # Extract and process response
    ai_response = response.choices[0].message.content
    
    # Update conversation history
    history.add_message("user", message)
    history.add_message("assistant", ai_response)
    
    # Add disclaimer if needed
    return prompt_engine.add_medical_disclaimer(ai_response)
