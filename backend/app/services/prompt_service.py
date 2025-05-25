from typing import List, Dict

class MedicalPromptEngine:
    def __init__(self):
        self.system_context = """You are a focused medical assistant AI. Keep responses brief and friendly (1-2 sentences).

Core responsibilities:
- Medical information and explanations
- Symptom discussion and assessment
- General health guidance
- Wellness and lifestyle advice
- OTC medication suggestions for mild conditions

Remember:
- Stay within medical/health domain
- Show empathy while maintaining boundaries
- Keep responses concise and clear
- Never diagnose, only suggest possibilities
- Ask follow-up questions when needed
- Only suggest OTC medications for mild conditions"""

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

        # Add OTC medication categories
        self.otc_medications = {
            'pain_relievers': {
                'acetaminophen', 'ibuprofen', 'aspirin', 'naproxen'
            },
            'cold_flu': {
                'decongestants', 'antihistamines', 'cough_suppressants',
                'expectorants', 'throat_lozenges'
            },
            'digestive': {
                'antacids', 'laxatives', 'anti-diarrheals', 'anti-nausea'
            },
            'allergy': {
                'antihistamines', 'nasal_sprays', 'eye_drops'
            },
            'topical': {
                'antibiotic_ointments', 'antifungal_creams', 'hydrocortisone',
                'pain_relieving_creams'
            }
        }

        # Add severity indicators
        self.severity_indicators = {
            'mild': {
                'slight', 'minor', 'manageable', 'bearable', 'tolerable',
                'intermittent', 'occasional'
            },
            'moderate': {
                'persistent', 'regular', 'noticeable', 'uncomfortable',
                'distracting', 'recurring'
            },
            'severe': {
                'intense', 'severe', 'debilitating', 'unbearable', 'constant',
                'worsening', 'acute', 'chronic'
            }
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
            return "I'm your medical assistant. How can I help with your health concerns?"
        
        # For health-related queries, create appropriate specialized prompts
        if any(keyword in message.lower() for keyword in ['symptom', 'feel', 'pain', 'discomfort']):
            return f"Briefly assess these symptoms: {message}"
        elif any(keyword in message.lower() for keyword in ['lifestyle', 'diet', 'exercise']):
            return f"Give brief lifestyle advice for: {message}"
        elif any(keyword in message.lower() for keyword in ['specialist', 'doctor', 'consultation']):
            return f"Briefly guide about medical consultation for: {message}"
        elif any(keyword in message.lower() for keyword in ['medicine', 'medication', 'drug', 'pill']):
            return f"Briefly assess medication query: {message}"
        
        return message

    def create_symptom_assessment_prompt(self, message: str) -> str:
        """Create a prompt for symptom assessment with follow-up questions."""
        severity = self.assess_severity(message)
        follow_up_questions = self.generate_follow_up_questions(message)
        
        prompt = f"""Help me understand these symptoms while being cautious and empathetic: {message}

Severity assessment: {severity}
Follow-up questions to ask:
{follow_up_questions}

Based on the severity, if mild, suggest appropriate OTC medications.
If moderate or severe, recommend consulting a healthcare professional."""

        return prompt

    def create_lifestyle_recommendation_prompt(self, message: str) -> str:
        return f"Suggest healthy lifestyle changes addressing: {message}"

    def create_specialist_referral_prompt(self, message: str) -> str:
        return f"Guide about medical consultation regarding: {message}"

    def create_medication_prompt(self, message: str) -> str:
        """Create a prompt for medication-related queries."""
        return f"""Assess the medication query: {message}

Consider:
1. Is this a request for OTC medication?
2. What are the symptoms being treated?
3. Are there any contraindications to consider?
4. What is the appropriate dosage and duration?
5. What are the potential side effects?

Provide a response that:
- Suggests appropriate OTC medications if applicable
- Includes dosage and usage instructions
- Mentions potential side effects
- Recommends consulting a healthcare professional if needed"""

    def assess_severity(self, message: str) -> str:
        """Assess the severity of symptoms mentioned in the message."""
        message = message.lower()
        
        # Check for severe indicators
        if any(indicator in message for indicator in self.severity_indicators['severe']):
            return "severe"
        # Check for moderate indicators
        elif any(indicator in message for indicator in self.severity_indicators['moderate']):
            return "moderate"
        # Default to mild if no severe/moderate indicators found
        return "mild"

    def generate_follow_up_questions(self, message: str) -> str:
        """Generate relevant follow-up questions based on the symptoms mentioned."""
        questions = []
        message = message.lower()
        
        # General symptom questions
        questions.append("How long have you been experiencing these symptoms?")
        questions.append("Have you had these symptoms before?")
        
        # Pain-specific questions
        if any(pain_word in message for pain_word in ['pain', 'ache', 'sore', 'discomfort']):
            questions.append("On a scale of 1-10, how would you rate the pain?")
            questions.append("Is the pain constant or does it come and go?")
        
        # Fever-related questions
        if 'fever' in message:
            questions.append("What is your current temperature?")
            questions.append("Are you experiencing any other symptoms with the fever?")
        
        # Respiratory questions
        if any(symptom in message for symptom in ['cough', 'congestion', 'runny nose', 'sore throat']):
            questions.append("Are you experiencing any difficulty breathing?")
            questions.append("Is there any mucus or phlegm?")
        
        return "\n".join(questions)

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