from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional
import base64
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ScanAnalysisService:
    def __init__(self):
        self.scan_types = {
            'xray': 'X-ray',
            'mri': 'MRI',
            'ct': 'CT Scan'
        }
        
        self.target_areas = {
            'lung': 'Lung',
            'brain': 'Brain',
            'breast': 'Breast',
            'liver': 'Liver',
            'kidney': 'Kidney'
        }

    async def analyze_scan(self, image_data: str, scan_type: str, target_area: str) -> Dict:
        """
        Analyze a medical scan image using OpenAI's Vision API
        """
        try:
            # Validate scan type and target area
            if scan_type not in self.scan_types:
                raise ValueError(f"Invalid scan type. Must be one of {list(self.scan_types.keys())}")
            if target_area not in self.target_areas:
                raise ValueError(f"Invalid target area. Must be one of {list(self.target_areas.keys())}")

            # Prepare the image for analysis
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(scan_type, target_area)
            
            # Call OpenAI Vision API
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical imaging specialist AI. Analyze the provided medical scan and identify any potential abnormalities or concerns. Be specific but cautious in your analysis."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            # Process and structure the response
            analysis = response.choices[0].message.content
            return {
                "scan_type": self.scan_types[scan_type],
                "target_area": self.target_areas[target_area],
                "analysis": analysis,
                "recommendations": self._generate_recommendations(analysis),
                "risk_level": self._assess_risk_level(analysis)
            }

        except Exception as e:
            logger.error(f"Error analyzing scan: {str(e)}")
            raise

    def _create_analysis_prompt(self, scan_type: str, target_area: str) -> str:
        """Create a specific prompt for the scan analysis"""
        return f"""Please analyze this {self.scan_types[scan_type]} of the {self.target_areas[target_area]}.
        Focus on:
        1. Any visible abnormalities or concerning patterns
        2. Potential signs of cancer or other serious conditions
        3. Overall image quality and clarity
        4. Any areas that require further investigation
        
        Provide a detailed but clear analysis that a patient can understand."""

    def _generate_recommendations(self, analysis: str) -> List[str]:
        """Generate recommendations based on the analysis"""
        recommendations = [
            "Consult with a healthcare provider for professional interpretation",
            "Keep a record of this analysis for future reference",
            "Schedule a follow-up appointment if any concerns are identified"
        ]
        
        # Add specific recommendations based on analysis content
        if "abnormal" in analysis.lower() or "concern" in analysis.lower():
            recommendations.append("Consider seeking a second opinion from a specialist")
        if "follow-up" in analysis.lower():
            recommendations.append("Schedule a follow-up scan as recommended")
            
        return recommendations

    def _assess_risk_level(self, analysis: str) -> str:
        """Assess the risk level based on the analysis"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ["severe", "critical", "urgent", "immediate"]):
            return "High"
        elif any(word in analysis_lower for word in ["moderate", "concerning", "abnormal"]):
            return "Medium"
        else:
            return "Low" 