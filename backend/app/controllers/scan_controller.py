from fastapi import APIRouter, HTTPException
from app.services.scan_service import ScanAnalysisService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

scan_service = ScanAnalysisService()

@router.post("/analyze")
async def analyze_scan(image_data: str, scan_type: str, target_area: str):
    """
    Controller function to handle scan analysis requests
    """
    try:
        logger.info(f"Received scan analysis request for {scan_type} of {target_area}")
        
        # Input validation
        if not image_data:
            raise HTTPException(status_code=400, detail="Image data is required")
        if not scan_type:
            raise HTTPException(status_code=400, detail="Scan type is required")
        if not target_area:
            raise HTTPException(status_code=400, detail="Target area is required")

        # Perform the analysis
        result = await scan_service.analyze_scan(image_data, scan_type, target_area)
        
        logger.info(f"Successfully analyzed {scan_type} of {target_area}")
        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing scan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analyzing the scan. Please try again."
        ) 