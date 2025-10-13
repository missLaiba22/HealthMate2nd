from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from ..services.scan_service import ScanAnalysisService
from ..services.segmentation_service import SegmentationService
from ..services.breast_segmentation_service import BreastSegmentationService
from ..models.scan_report import ScanReportCreate, ScanReportResponse, ScanReportUpdate, ScanReportModel
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
    logger.info(f"Brain MRI segmentation request received - User: {current_user.get('sub', 'Unknown')}")
    logger.info(f"Request data - FLAIR image length: {len(request.flair_image)}, T1CE image length: {len(request.t1ce_image)}")
    
    try:
        logger.info("Starting brain MRI dual modality segmentation...")
        result = await segmentation_service.segment_dual_modality(
            request.flair_image, 
            request.t1ce_image
        )
        
        # Auto-save scan report if segmentation was successful
        if result.get("success", False):
            try:
                from datetime import datetime
                from ..models.scan_report import ScanReportCreate
                
                # Extract patient email from current user
                patient_email = current_user.get('sub', 'unknown@example.com')
                
                # Create scan report data with null safety
                report_data = ScanReportCreate(
                    patient_email=patient_email,
                    scan_type="brain_mri",
                    scan_date=datetime.utcnow(),
                    segmentation_data=result.get("class_statistics", {}),
                    insights=result.get("insights", []) or [],
                    recommendations=result.get("recommendations", []) or [],
                    segmentation_overlay=result.get("segmentation_result", "") or ""
                )
                
                # Save to database
                report_result = ScanReportModel.create_scan_report(report_data)
                if report_result.get("success"):
                    result["report_id"] = report_result.get("report_id")
                    logger.info(f"Scan report saved with ID: {report_result.get('report_id')}")
                else:
                    logger.warning(f"Failed to save scan report: {report_result.get('error')}")
                    
            except Exception as save_error:
                logger.error(f"Error saving scan report: {str(save_error)}")
                # Don't fail the main request if report saving fails
        
        logger.info("Brain MRI segmentation completed successfully")
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
    logger.info(f"Breast segmentation request received - User: {current_user.get('sub', 'Unknown')}")
    logger.info(f"Request data - Image length: {len(request.image_data)}")
    
    try:
        logger.info("Starting breast ultrasound segmentation...")
        result = await breast_segmentation_service.segment_breast_ultrasound(request.image_data)
        
        # Auto-save scan report if segmentation was successful
        if result.get("success", False):
            try:
                from datetime import datetime
                from ..models.scan_report import ScanReportCreate
                
                # Extract patient email from current user
                patient_email = current_user.get('sub', 'unknown@example.com')
                
                # Create scan report data with null safety
                report_data = ScanReportCreate(
                    patient_email=patient_email,
                    scan_type="breast_ultrasound",
                    scan_date=datetime.utcnow(),
                    segmentation_data={
                        "statistics": result.get("statistics", {}) or {},
                        "measurements": result.get("measurements", {}) or {}
                    },
                    insights=result.get("insights", []) or [],
                    recommendations=result.get("recommendations", []) or [],
                    segmentation_overlay=result.get("segmentation_mask", "") or ""
                )
                
                # Save to database
                report_result = ScanReportModel.create_scan_report(report_data)
                if report_result.get("success"):
                    result["report_id"] = report_result.get("report_id")
                    logger.info(f"Scan report saved with ID: {report_result.get('report_id')}")
                else:
                    logger.warning(f"Failed to save scan report: {report_result.get('error')}")
                    
            except Exception as save_error:
                logger.error(f"Error saving scan report: {str(save_error)}")
                # Don't fail the main request if report saving fails
        
        logger.info("Breast segmentation completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error segmenting breast scan: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Scan Report Routes
@router.post("/reports/create", response_model=dict)
async def create_scan_report(
    report_data: ScanReportCreate,
    current_user=Depends(get_current_user)
):
    """Create a new scan report"""
    try:
        result = ScanReportModel.create_scan_report(report_data)
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
    except Exception as e:
        logger.error(f"Error creating scan report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/reports/patient/{patient_email}", response_model=List[dict])
async def get_patient_reports(
    patient_email: str,
    current_user=Depends(get_current_user)
):
    """Get all scan reports for a patient"""
    try:
        reports = ScanReportModel.get_patient_reports(patient_email)
        return reports
    except Exception as e:
        logger.error(f"Error fetching patient reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/reports/{report_id}", response_model=dict)
async def get_report_by_id(
    report_id: str,
    current_user=Depends(get_current_user)
):
    """Get a specific scan report by ID"""
    try:
        report = ScanReportModel.find_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/reports/{report_id}/overlay", response_model=dict)
async def get_report_overlay(
    report_id: str,
    current_user=Depends(get_current_user)
):
    """Get segmentation overlay for a specific report"""
    try:
        report = ScanReportModel.get_report_overlay(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        return {
            "success": True,
            "overlay": report["segmentation_overlay"],
            "scan_type": report["scan_type"],
            "scan_date": report["scan_date"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report overlay: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/reports/{report_id}", response_model=dict)
async def update_scan_report(
    report_id: str,
    update_data: ScanReportUpdate,
    current_user=Depends(get_current_user)
):
    """Update a scan report"""
    try:
        success = ScanReportModel.update_report(report_id, update_data)
        if success:
            return {"success": True, "message": "Report updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found or no changes made"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/reports/{report_id}", response_model=dict)
async def delete_scan_report(
    report_id: str,
    current_user=Depends(get_current_user)
):
    """Delete a scan report"""
    try:
        success = ScanReportModel.delete_report(report_id)
        if success:
            return {"success": True, "message": "Report deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
