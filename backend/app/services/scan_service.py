import logging
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScanAnalysisService:
    """
    Service for medical scan analysis using U-Net segmentation models.
    This service coordinates with segmentation services for brain and breast analysis.
    """
    
    def __init__(self):
        self.supported_scan_types = {
            'mri': 'MRI',
            'ultrasound': 'Ultrasound'
        }
        
        self.supported_target_areas = {
            'brain': 'Brain',
            'breast': 'Breast'
        }

    async def analyze_scan(self, image_data: str, scan_type: str, target_area: str) -> Dict:
        """
        Analyze a medical scan image using U-Net segmentation models.
        Currently supports brain MRI and breast ultrasound segmentation.
        """
        try:
            # Validate scan type and target area
            if scan_type not in self.supported_scan_types:
                raise ValueError(f"Invalid scan type. Must be one of {list(self.supported_scan_types.keys())}")
            if target_area not in self.supported_target_areas:
                raise ValueError(f"Invalid target area. Must be one of {list(self.supported_target_areas.keys())}")

            # Route to appropriate segmentation service
            if target_area == 'brain' and scan_type == 'mri':
                return {
                    "scan_type": self.supported_scan_types[scan_type],
                    "target_area": self.supported_target_areas[target_area],
                    "message": "Brain MRI analysis requires dual-modality segmentation. Please use the /scan/segment/two-modalities endpoint with FLAIR and T1CE images.",
                    "recommended_endpoint": "/scan/segment/two-modalities"
                }
            elif target_area == 'breast' and scan_type == 'ultrasound':
                return {
                    "scan_type": self.supported_scan_types[scan_type],
                    "target_area": self.supported_target_areas[target_area],
                    "message": "Breast ultrasound analysis requires specialized segmentation. Please use the /scan/segment/breast endpoint.",
                    "recommended_endpoint": "/scan/segment/breast"
                }
            else:
                return {
                    "scan_type": self.supported_scan_types[scan_type],
                    "target_area": self.supported_target_areas[target_area],
                    "message": "This scan type and target area combination is not supported for general analysis. Please use the appropriate segmentation endpoint.",
                    "supported_combinations": [
                        "MRI + Brain → /scan/segment/two-modalities",
                        "Ultrasound + Breast → /scan/segment/breast"
                    ]
                }

        except Exception as e:
            logger.error(f"Error in scan analysis: {str(e)}")
            raise 