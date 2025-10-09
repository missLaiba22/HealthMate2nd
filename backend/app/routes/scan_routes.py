from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..services.scan_service import ScanAnalysisService
from ..services.segmentation_service import SegmentationService
from ..services.breast_segmentation_service import BreastSegmentationService
from ..utils.jwt import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Scan Analysis"])

class ScanRequest(BaseModel):
    image_data: str
    scan_type: str
    target_area: str

class SegmentRequest(BaseModel):
    image_data: str

class TwoModalityRequest(BaseModel):
    flair_image: str
    t1ce_image: str

class BreastSegmentRequest(BaseModel):
    image_data: str

# Initialize services
scan_service = ScanAnalysisService()
segmentation_service = SegmentationService()
breast_segmentation_service = BreastSegmentationService()

@router.post("/analyze")
async def analyze_medical_scan(
    request: ScanRequest,
    current_user=Depends(get_current_user)
):
    """Analyze a medical scan"""
    try:
        result = await scan_service.analyze_scan(
            request.image_data, 
            request.scan_type, 
            request.target_area
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/segment")
async def segment_scan(
    request: SegmentRequest,
    current_user=Depends(get_current_user)
):
    """Segment a medical scan"""
    try:
        result = await segmentation_service.segment_image(request.image_data)
        return result
        
    except Exception as e:
        logger.error(f"Error segmenting scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/segment/two-modalities")
async def segment_two_modalities(
    request: TwoModalityRequest,
    current_user=Depends(get_current_user)
):
    """Segment brain scan with two modalities (FLAIR and T1CE)"""
    try:
        result = await segmentation_service.segment_dual_modality(
            request.flair_image, 
            request.t1ce_image
        )
        return result
        
    except Exception as e:
        logger.error(f"Error segmenting dual modality: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/segment/breast")
async def segment_breast_scan(
    request: BreastSegmentRequest,
    current_user=Depends(get_current_user)
):
    """Segment breast ultrasound scan"""
    try:
        result = await breast_segmentation_service.segment_breast_ultrasound(request.image_data)
        return result
        
    except Exception as e:
        logger.error(f"Error segmenting breast scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
