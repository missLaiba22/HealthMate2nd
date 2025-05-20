from typing import List, Dict

class MedicalPromptEngine:
    def __init__(self):
        self.system_context = """You are Amy, a focused medical assistant AI. Your role is strictly limited to health-related topics:

1. ONLY respond to health, medical, and wellness-related queries
2. For non-health topics, politely explain that you can only discuss health matters
3. Keep responses brief and friendly (2-3 sentences)

Core responsibilities:
- Medical information and explanations
- Symptom discussion
- General health guidance
- Wellness and lifestyle advice
- Medical terminology explanation

If user asks about non-health topics (like entertainment, politics, general chat, etc.), respond:
"I'm your medical assistant, focused on helping you with health-related questions. Could we discuss your health concerns instead?"

Remember:
- Stay strictly within medical/health domain
- Show empathy while maintaining boundaries
- Keep medical disclaimers clear but brief
- Never diagnose, only suggest possibilities"""

        # Initialize comprehensive health-related keyword sets
        self.symptoms = {
            'pain', 'ache', 'sore', 'discomfort', 'fever', 'cough', 'headache',
            'nausea', 'vomiting', 'diarrhea', 'constipation', 'rash', 'swelling',
            'dizziness', 'fatigue', 'tired', 'exhausted', 'weakness', 'numbness',
            'tingling', 'stiffness', 'cramping', 'burning', 'itching', 'sneezing',
            'congestion', 'runny nose', 'sore throat', 'chest pain', 'shortness of breath'
        }
        
        self.body_parts = {
            'head', 'neck', 'shoulder', 'arm', 'elbow', 'wrist', 'hand', 'finger',
            'chest', 'back', 'spine', 'hip', 'leg', 'knee', 'ankle', 'foot', 'toe',
            'stomach', 'abdomen', 'throat', 'eye', 'ear', 'nose', 'mouth', 'tongue',
            'skin', 'muscle', 'bone', 'joint', 'heart', 'lung', 'liver', 'kidney'
        }
        
        self.medical_terms = {
            'health', 'medical', 'doctor', 'hospital', 'clinic', 'emergency',
            'treatment', 'medicine', 'medication', 'prescription', 'therapy',
            'surgery', 'procedure', 'diagnosis', 'prognosis', 'test', 'scan',
            'x-ray', 'mri', 'ct scan', 'ultrasound', 'blood test', 'urine test'
        }
        
        self.conditions = {
            'diabetes', 'hypertension', 'asthma', 'arthritis', 'depression',
            'anxiety', 'insomnia', 'allergy', 'infection', 'inflammation',
            'flu', 'cold', 'covid', 'cancer', 'heart disease', 'stroke',
            'migraine', 'ulcer', 'hernia', 'fracture', 'sprain', 'strain'
        }
        
        self.wellness = {
            'diet', 'nutrition', 'exercise', 'fitness', 'workout', 'yoga',
            'meditation', 'sleep', 'rest', 'stress', 'mental health', 'wellness',
            'lifestyle', 'healthy', 'vitamin', 'supplement', 'prevention',
            'immunity', 'weight', 'bmi', 'blood pressure', 'cholesterol'
        }

    def is_health_related(self, message: str) -> bool:
        """
        Enhanced check if the message is health-related using comprehensive keyword sets
        and context analysis.
        """
        message = message.lower()
        words = set(message.split())
        
        # Direct keyword match in any category
        all_keywords = (self.symptoms | self.body_parts | self.medical_terms |
                       self.conditions | self.wellness)
        
        # Check for exact matches
        if any(keyword in message for keyword in all_keywords):
            return True
            
        # Check for word combinations that indicate health context
        word_pairs = zip(message.split(), message.split()[1:])
        health_pairs = [
            ('feel', 'sick'), ('not', 'feeling'), ('having', 'trouble'),
            ('medical', 'advice'), ('health', 'question'), ('should', 'see'),
            ('been', 'diagnosed'), ('taking', 'medicine'), ('started', 'feeling')
        ]
        
        if any(pair in health_pairs for pair in word_pairs):
            return True
            
        # Check for question patterns about health
        health_question_starters = [
            'why do i feel', 'what causes', 'is it normal',
            'should i be concerned', 'how can i treat',
            'what should i do about', 'when should i see'
        ]
        
        if any(message.startswith(starter) for starter in health_question_starters):
            return True
            
        return False

    def create_response_prompt(self, message: str) -> str:
        """Create appropriate prompt based on message content."""
        if not self.is_health_related(message):
            return ("I notice you're asking about something outside of healthcare. "
                   "I'm your medical assistant, focused on helping you with health-related questions. "
                   "Would you like to discuss any health concerns instead?")
        
        # For health-related queries, create appropriate specialized prompts
        if any(keyword in message.lower() for keyword in ['symptom', 'feel', 'pain', 'discomfort']):
            return self.create_symptom_assessment_prompt(message)
        elif any(keyword in message.lower() for keyword in ['lifestyle', 'diet', 'exercise']):
            return self.create_lifestyle_recommendation_prompt(message)
        elif any(keyword in message.lower() for keyword in ['specialist', 'doctor', 'consultation']):
            return self.create_specialist_referral_prompt(message)
        
        return message

    def create_symptom_assessment_prompt(self, message: str) -> str:
        return f"Help me understand these symptoms while being cautious and empathetic: {message}"

    def create_lifestyle_recommendation_prompt(self, message: str) -> str:
        return f"Suggest healthy lifestyle changes addressing: {message}"

    def create_specialist_referral_prompt(self, message: str) -> str:
        return f"Guide about medical consultation regarding: {message}"

    def add_medical_disclaimer(self, response: str) -> str:
        """Add medical disclaimer if response contains medical advice."""
        if any(keyword in response.lower() for keyword in ['should', 'recommend', 'suggest', 'try', 'consider']):
            return f"{response}\n\nRemember: This is general information. Always consult healthcare professionals for medical advice."
        return response 