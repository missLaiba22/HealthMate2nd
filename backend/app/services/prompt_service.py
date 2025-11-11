from typing import List, Dict

class MedicalPromptEngine:
    def __init__(self):
        self.system_context = """You are a MEDICAL TRIAGE ASSISTANT AI specialized exclusively in health and medical conversations. Keep responses conversational and brief (1-2 sentences).

STRICT MEDICAL FOCUS:
- ONLY respond to health, medical, wellness, symptom, or injury-related topics
- If a message is not about health/medical topics, politely redirect to medical concerns
- Do NOT engage with non-medical topics even if they appear in medical conversation context
- Do NOT try to connect non-medical messages to previous medical discussions

Core Medical Triage Features:
FE-1: Maintain context in multi-turn conversations for coherent medical discussions
FE-2: Conduct symptom assessments and provide diagnostic suggestions based on user inputs
FE-3: Offer lifestyle recommendations (diet, exercise) tailored to symptoms and health insights
FE-4: Advise users to consult specific medical specialists when symptoms indicate professional medical advice

Medical Response Guidelines:
- Show empathy while maintaining professional boundaries
- Keep responses conversational and clear
- Never diagnose, only suggest possibilities and next steps
- Ask follow-up questions to maintain medical context
- Guide users to appropriate specialists when needed
- Provide lifestyle advice based on symptoms

Non-Medical Message Response:
- If message is clearly not health-related, respond: "I'm a medical triage assistant. Please share your health concerns or medical questions so I can assist you properly."
- Do NOT attempt to relate non-medical topics to previous medical discussions"""

        

    def is_health_related(self, message: str, conversation_history: list = None) -> bool:
        """
        Intelligent health-related detection using OpenAI's natural language understanding.
        This leverages the AI model's capability to understand context and medical relevance
        without needing to maintain exhaustive keyword lists.
        """
        try:
            from openai import OpenAI
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Build context from conversation history if available
            context_info = ""
            if conversation_history and len(conversation_history) > 0:
                recent_messages = [msg.get('content', '') for msg in conversation_history[-3:] 
                                 if msg.get('role') == 'user']
                if recent_messages:
                    context_info = f"\nRecent conversation context: {' | '.join(recent_messages)}"
            
            # Create a strict prompt for health relevance detection
            health_detection_prompt = f"""You are a medical triage assistant. Determine if the following message is DIRECTLY related to health, medical concerns, symptoms, injuries, or wellness.

Message: "{message}"{context_info}

STRICT RULES:
- Only classify as HEALTH if the message itself contains health/medical content
- Do NOT classify as HEALTH just because of previous medical conversation context
- The message must be asking about health, describing symptoms, or requesting medical advice
- General statements, greetings, or unrelated topics should be NOT_HEALTH

Examples:
✅ HEALTH:
- "My cut is getting worse"
- "I feel dizzy" 
- "Should I see a doctor?"
- "How do I treat this wound?"

❌ NOT_HEALTH:
- "I have a present to give" (even if discussing injury before)
- "I'll warn you" (even in medical context)
- "What's the weather?"
- "How are you?"
- "Thank you"

Respond with ONLY: "HEALTH" or "NOT_HEALTH"

Response:"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": health_detection_prompt}],
                max_tokens=10,
                temperature=0.0
            )
            
            result = response.choices[0].message.content.strip().upper()
            return "HEALTH" in result
            
        except Exception as e:
            # Fallback to strict keyword detection if OpenAI fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"OpenAI health detection failed: {e}, using strict fallback")
            
            # Strict fallback - only clear medical terms
            direct_health_indicators = [
                'pain', 'hurt', 'ache', 'sick', 'ill', 'fever', 'cough', 'headache',
                'cut', 'wound', 'injury', 'bleeding', 'bleed', 'bruise', 'burn',
                'doctor', 'hospital', 'medicine', 'medication', 'treatment',
                'symptom', 'symptoms', 'feel sick', 'feel ill', 'not feeling well',
                'health problem', 'medical help', 'see a doctor', 'emergency'
            ]
            
            # Only return True if message contains clear health indicators
            message_lower = message.lower()
            return any(indicator in message_lower for indicator in direct_health_indicators)

    def create_response_prompt(self, message: str) -> str:
        """Create appropriate prompt based on message content for medical triage."""
        if not self.is_health_related(message):
            return "I'm your medical triage assistant. How can I help with your health concerns today?"
        
        # FE-2: Symptom assessment and diagnostic suggestions
        if any(keyword in message.lower() for keyword in ['symptom', 'feel', 'pain', 'discomfort', 'ache']):
            return f"Conduct a symptom assessment for: {message}. Ask follow-up questions to understand the context better."
        
        # FE-3: Lifestyle recommendations
        elif any(keyword in message.lower() for keyword in ['lifestyle', 'diet', 'exercise', 'nutrition', 'fitness']):
            return f"Provide lifestyle recommendations addressing: {message}. Include diet and exercise suggestions."
        
        # FE-4: Specialist consultation guidance
        elif any(keyword in message.lower() for keyword in ['specialist', 'doctor', 'consultation', 'see a doctor']):
            return f"Guide about medical consultation for: {message}. Suggest appropriate specialists if needed."
        
        # General health concerns
        else:
            return f"Provide medical triage guidance for: {message}. Assess symptoms and suggest next steps."

    def create_context_aware_prompt(self, message: str, conversation_history: List[Dict]) -> str:
        """FE-1: Create context-aware prompts for multi-turn conversations."""
        if not conversation_history:
            return self.create_response_prompt(message)
        
        # Build context from conversation history
        context_summary = self._build_context_summary(conversation_history)
        
        # Create context-aware prompt for AI processing
        return f"""Based on our previous conversation about: {context_summary}
        
Current message: {message}

Maintain context and provide coherent medical triage guidance. If this is a follow-up to previous symptoms, reference them appropriately."""

    def _build_context_summary(self, conversation_history: List[Dict]) -> str:
        """Build a summary of conversation context."""
        recent_topics = []
        for msg in conversation_history[-3:]:  # Last 3 messages for context
            if msg.get('role') == 'user':
                recent_topics.append(msg.get('content', ''))
        
        return " | ".join(recent_topics) if recent_topics else "No previous context"

    def add_medical_disclaimer(self, response: str) -> str:
        """Add medical disclaimer only for responses containing specific medical advice."""
        # Keywords that indicate medical advice requiring disclaimer
        medical_advice_keywords = {
            'take', 'use', 'apply', 'prescribe', 'recommend', 'suggest',
            'medication', 'medicine', 'drug', 'treatment', 'therapy',
            'dosage', 'dose', 'side effects', 'contraindications'
        }
        
        # Check if response contains medical advice
        if any(keyword in response.lower() for keyword in medical_advice_keywords):
            return f"{response}\nNote: Consult healthcare professionals for medical advice."
        
        return response 