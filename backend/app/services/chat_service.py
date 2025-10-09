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
api_key = os.getenv("OPENAI_API_KEY")
logger.info(f"OpenAI API key available: {bool(api_key)}")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY is required but not found")

client = OpenAI(api_key=api_key)
prompt_engine = MedicalPromptEngine()

def get_conversation_history(email: str) -> ConversationHistory:
    """Get conversation history for a user."""
    logger.info(f"Getting conversation history for email: {email}")
    return ConversationHistory(email)

async def get_ai_response(message: str, email: str) -> str:
    # Get conversation history
    logger.info(f"Getting AI response for email: {email}")
    logger.info(f"Message received: {message}")
    history = get_conversation_history(email)
    
    # FE-1: Create context-aware prompt for multi-turn conversations
    conversation_history = history.get_context()
    logger.info(f"Conversation history: {conversation_history}")
    prompt = prompt_engine.create_context_aware_prompt(message, conversation_history)
    logger.info(f"Generated prompt: {prompt[:100]}...")
    
    # If not health-related, return a proper response
    is_health = prompt_engine.is_health_related(message)
    logger.info(f"Message health-related check: {is_health} for message: {message}")
    
    if not is_health:
        logger.info(f"Message not health-related: {message}")
        # Return a proper non-health response instead of the raw prompt
        non_health_response = "I'm your medical triage assistant. How can I help with your health concerns today?"
        history.add_message("user", message)
        history.add_message("assistant", non_health_response)
        return non_health_response

    # Create message list with context
    context_messages = history.get_context()
    logger.info(f"Context messages: {context_messages}")
    
    messages = [
        {"role": "system", "content": prompt_engine.system_context},
        *context_messages,
        {"role": "user", "content": message}  # Use the original message, not the prompt
    ]
    
    logger.info(f"Final messages for OpenAI: {messages}")
    
    try:
        logger.info(f"Calling OpenAI API with {len(messages)} messages")
        logger.info(f"Messages: {messages}")
        
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
        
        logger.info(f"OpenAI API response received: {response}")
        logger.info(f"Response choices: {response.choices}")
        logger.info(f"First choice: {response.choices[0] if response.choices else 'No choices'}")
        
        # Extract and process response
        if not response.choices or len(response.choices) == 0:
            logger.error("No choices in OpenAI response")
            raise Exception("No response choices from OpenAI")
        
        ai_response = response.choices[0].message.content
        logger.info(f"Extracted AI response: {ai_response}")
        
        if not ai_response:
            logger.error("Empty AI response")
            raise Exception("Empty response from OpenAI")
        
        # Update conversation history
        history.add_message("user", message)
        history.add_message("assistant", ai_response)
        
        # Add disclaimer if needed
        final_response = prompt_engine.add_medical_disclaimer(ai_response)
        logger.info(f"Final response: {final_response}")
        return final_response
        
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        # Fallback to GPT-3.5 if GPT-4.1 fails
        try:
            logger.info("Trying GPT-3.5 fallback...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=100
            )
            logger.info(f"GPT-3.5 response: {response}")
            
            if not response.choices or len(response.choices) == 0:
                logger.error("No choices in GPT-3.5 response")
                raise Exception("No response choices from GPT-3.5")
            
            ai_response = response.choices[0].message.content
            logger.info(f"GPT-3.5 AI response: {ai_response}")
            
            if not ai_response:
                logger.error("Empty GPT-3.5 response")
                raise Exception("Empty response from GPT-3.5")
            
            history.add_message("user", message)
            history.add_message("assistant", ai_response)
            return prompt_engine.add_medical_disclaimer(ai_response)
        except Exception as fallback_error:
            logger.error(f"Fallback error: {str(fallback_error)}")
            # Return a simple response if all AI calls fail
            return "I understand you said: " + message + ". How can I help you with your health concerns?"
