from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.jwt import get_current_user
from app.controllers.scan_controller import analyze_scan
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["Scan Analysis"])

class ScanRequest(BaseModel):
    image_data: str
    scan_type: str
    target_area: str

@router.post("/analyze")
async def analyze_medical_scan(
    request: ScanRequest,
    current_user=Depends(get_current_user)
):
    """
    Endpoint to analyze medical scans
    """
    try:
        logger.info(f"Scan analysis request received from user: {current_user['email']}")
        result = await analyze_scan(
            request.image_data,
            request.scan_type,
            request.target_area
        )
        return result
    except Exception as e:
        logger.error(f"Error in scan analysis endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        ) 