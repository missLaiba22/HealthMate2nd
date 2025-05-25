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
    
    try:
        # Get response from OpenAI using GPT-4.1
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",  # Using GPT-4.1
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=100,   # Reduced token limit for shorter responses
            top_p=0.9,        # Nucleus sampling for better response quality
            frequency_penalty=0.3,  # Reduce repetition
            presence_penalty=0.3,   # Encourage diverse responses
            response_format={"type": "text"},  # Ensure text responses
            seed=42  # For consistent responses
        )
        
        # Extract and process response
        ai_response = response.choices[0].message.content
        
        # Update conversation history
        history.add_message("user", message)
        history.add_message("assistant", ai_response)
        
        # Add disclaimer if needed
        return prompt_engine.add_medical_disclaimer(ai_response)
        
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        # Fallback to GPT-3.5 if GPT-4.1 fails
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=100
            )
            ai_response = response.choices[0].message.content
            history.add_message("user", message)
            history.add_message("assistant", ai_response)
            return prompt_engine.add_medical_disclaimer(ai_response)
        except Exception as fallback_error:
            logger.error(f"Fallback error: {str(fallback_error)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a few moments."
