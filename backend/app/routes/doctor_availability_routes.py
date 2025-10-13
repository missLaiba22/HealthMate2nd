from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional
from datetime import date, time
from pydantic import BaseModel
import asyncio
from ..models.doctor_availability import (
    WeeklySchedule, TimeSlot, DailyOverride, BlockTimeSlot, BlockTimeReason
)
from ..services.doctor_availability_service import DoctorAvailabilityService
from ..utils.jwt import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
availability_service = DoctorAvailabilityService()

# Request models for new endpoints
class BlockTimeRequest(BaseModel):
    start_time: time
    end_time: time
    reason: BlockTimeReason
    description: Optional[str] = None

class DailyOverrideRequest(BaseModel):
    override_date: date
    is_available: bool = True
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    override_reason: Optional[str] = None
    block_time_slots: List[BlockTimeRequest] = []

@router.post("/set-weekly-schedule", response_model=Dict)
async def set_weekly_schedule(
    schedule_data: WeeklySchedule,
    current_user=Depends(get_current_user)
):
    """Set doctor's weekly availability schedule"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can set availability"
            )
        
        # Verify doctor is setting their own schedule
        if current_user.get('sub') != schedule_data.doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only set your own availability"
            )
        
        result = availability_service.set_weekly_schedule(schedule_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Weekly schedule set successfully",
                "doctor_email": schedule_data.doctor_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to set weekly schedule")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting weekly schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/weekly-schedule/{doctor_email}", response_model=Dict)
async def get_weekly_schedule(
    doctor_email: str,
    current_user=Depends(get_current_user)
):
    """Get doctor's weekly schedule"""
    try:
        schedule = availability_service.get_weekly_schedule(doctor_email)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No weekly schedule found for this doctor"
            )
        
        return {
            "success": True,
            "schedule": schedule
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weekly schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/my-weekly-schedule", response_model=Dict)
async def get_my_weekly_schedule(
    current_user=Depends(get_current_user)
):
    """Get current doctor's weekly schedule"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can access their schedule"
            )
        
        doctor_email = current_user.get('sub')
        schedule = availability_service.get_weekly_schedule(doctor_email)
        
        if not schedule:
            return {
                "success": True,
                "schedule": None,
                "message": "No weekly schedule set yet"
            }
        
        return {
            "success": True,
            "schedule": schedule
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting my weekly schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/available-slots/{doctor_email}", response_model=Dict)
async def get_available_slots(
    doctor_email: str,
    start_date: date,
    end_date: Optional[date] = None,
    current_user=Depends(get_current_user)
):
    """Get available appointment slots for a doctor"""
    try:
        # For single date requests, use the same date for start and end
        if not end_date:
            end_date = start_date
        
        # Initialize services
        from ..services.appointment_service import AppointmentService
        appointment_service = AppointmentService()

        # Get base slots from availability service
        slots = availability_service.get_available_slots(doctor_email, start_date, end_date)
        
        # Prepare slot availability checks
        availability_checks = []
        slot_times = []
        
        for slot in slots:
            if not slot.get("is_available", False):
                continue
                
            time_str = slot.get("slot_time", "")
            if not time_str:
                continue
                
            # Convert time object to string format if needed
            slot_time = time_str if isinstance(time_str, str) else time_str.isoformat()
            
            # Add to our check lists
            availability_checks.append(
                appointment_service.is_slot_available(
                    doctor_email=doctor_email,
                    appointment_date=slot["slot_date"],
                    appointment_time=slot_time
                )
            )
            slot_times.append(slot_time)
        
        # Run all availability checks concurrently
        availability_results = await asyncio.gather(*availability_checks)
        
        # Filter slots based on availability results
        formatted_slots = [
            time for time, is_available in zip(slot_times, availability_results)
            if is_available
        ]
        
        return {
            "success": True,
            "slots": formatted_slots,
            "doctor_email": doctor_email,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/book-slot", response_model=Dict)
async def book_appointment_slot(
    doctor_email: str,
    slot_date: date,
    slot_time: time,
    appointment_id: str,
    current_user=Depends(get_current_user)
):
    """Book a specific appointment slot"""
    try:
        success = availability_service.book_appointment_slot(
            doctor_email, slot_date, slot_time, appointment_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Appointment slot booked successfully",
                "appointment_id": appointment_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to book appointment slot - slot may be unavailable"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking appointment slot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/cancel-slot/{appointment_id}", response_model=Dict)
async def cancel_appointment_slot(
    appointment_id: str,
    current_user=Depends(get_current_user)
):
    """Cancel a booked appointment slot"""
    try:
        success = availability_service.cancel_appointment_slot(appointment_id)
        
        if success:
            return {
                "success": True,
                "message": "Appointment slot canceled successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment slot not found or already canceled"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling appointment slot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/update-weekly-schedule", response_model=Dict)
async def update_weekly_schedule(
    schedule_data: WeeklySchedule,
    current_user=Depends(get_current_user)
):
    """Update doctor's weekly schedule"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can update availability"
            )
        
        # Verify doctor is updating their own schedule
        if current_user.get('sub') != schedule_data.doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own availability"
            )
        
        result = availability_service.update_weekly_schedule(schedule_data.doctor_email, schedule_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Weekly schedule updated successfully",
                "doctor_email": schedule_data.doctor_email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to update weekly schedule")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating weekly schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/delete-weekly-schedule/{doctor_email}", response_model=Dict)
async def delete_weekly_schedule(
    doctor_email: str,
    current_user=Depends(get_current_user)
):
    """Delete doctor's weekly schedule"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can delete availability"
            )
        
        # Verify doctor is deleting their own schedule
        if current_user.get('sub') != doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own availability"
            )
        
        success = availability_service.delete_weekly_schedule(doctor_email)
        
        if success:
            return {
                "success": True,
                "message": "Weekly schedule deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete weekly schedule"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting weekly schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ===== DAILY ADJUSTMENTS & BLOCK TIME ENDPOINTS =====

@router.get("/day-view/{doctor_email}", response_model=Dict)
async def get_day_view(
    doctor_email: str,
    view_date: date,
    current_user=Depends(get_current_user)
):
    """Get complete day view including weekly schedule, daily overrides, and existing appointments"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can access day view"
            )
        
        # Verify doctor is accessing their own data
        if current_user.get('sub') != doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own day view"
            )
        
        day_view = availability_service.get_day_view(doctor_email, view_date)
        
        if not day_view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Day view not found"
            )
        
        return {
            "success": True,
            "day_view": day_view
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting day view: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/create-daily-override", response_model=Dict)
async def create_daily_override(
    doctor_email: str,
    override_request: DailyOverrideRequest,
    current_user=Depends(get_current_user)
):
    """Create or update daily override for a specific date"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can create daily overrides"
            )
        
        # Verify doctor is creating their own override
        if current_user.get('sub') != doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create overrides for yourself"
            )
        
        # Convert request to DailyOverride model
        block_time_slots = []
        for bt_req in override_request.block_time_slots:
            block_time_slots.append(BlockTimeSlot(
                start_time=bt_req.start_time,
                end_time=bt_req.end_time,
                reason=bt_req.reason,
                description=bt_req.description,
                is_override=True
            ))
        
        override_data = DailyOverride(
            doctor_email=doctor_email,
            override_date=override_request.override_date,
            is_available=override_request.is_available,
            start_time=override_request.start_time,
            end_time=override_request.end_time,
            block_time_slots=block_time_slots,
            override_reason=override_request.override_reason
        )
        
        result = availability_service.create_daily_override(override_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Daily override created successfully",
                "doctor_email": doctor_email,
                "override_date": override_request.override_date.isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to create daily override")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating daily override: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/add-block-time", response_model=Dict)
async def add_block_time(
    doctor_email: str,
    block_date: date,
    block_request: BlockTimeRequest,
    current_user=Depends(get_current_user)
):
    """Add block time to a specific date"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can add block time"
            )
        
        # Verify doctor is adding block time for themselves
        if current_user.get('sub') != doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add block time for yourself"
            )
        
        # Convert request to BlockTimeSlot model
        block_time = BlockTimeSlot(
            start_time=block_request.start_time,
            end_time=block_request.end_time,
            reason=block_request.reason,
            description=block_request.description,
            is_override=True
        )
        
        result = availability_service.add_block_time(
            doctor_email, block_date, block_time, block_request.description
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Block time added successfully",
                "doctor_email": doctor_email,
                "block_date": block_date.isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to add block time")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding block time: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/delete-daily-override/{doctor_email}", response_model=Dict)
async def delete_daily_override(
    doctor_email: str,
    override_date: date,
    current_user=Depends(get_current_user)
):
    """Delete daily override and revert to weekly schedule"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can delete daily overrides"
            )
        
        # Verify doctor is deleting their own override
        if current_user.get('sub') != doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own overrides"
            )
        
        success = availability_service.delete_daily_override(doctor_email, override_date)
        
        if success:
            return {
                "success": True,
                "message": "Daily override deleted successfully",
                "doctor_email": doctor_email,
                "override_date": override_date.isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily override not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting daily override: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/available-slots-with-overrides/{doctor_email}", response_model=Dict)
async def get_available_slots_with_overrides(
    doctor_email: str,
    start_date: date,
    end_date: Optional[date] = None,
    current_user=Depends(get_current_user)
):
    """Get available appointment slots considering daily overrides"""
    try:
        # Default to 30 days if end_date not provided
        if not end_date:
            from datetime import timedelta
            end_date = start_date + timedelta(days=30)
        
        slots = availability_service.get_available_slots_with_overrides(
            doctor_email, start_date, end_date
        )
        
        return {
            "success": True,
            "slots": slots,
            "doctor_email": doctor_email,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting available slots with overrides: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/block-time-reasons", response_model=List[str])
async def get_block_time_reasons(current_user=Depends(get_current_user)):
    """Get available block time reasons"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can access block time reasons"
            )
        
        reasons = [reason.value for reason in BlockTimeReason]
        return {
            "success": True,
            "reasons": reasons
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting block time reasons: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/cleanup-slots/{doctor_email}", response_model=Dict)
async def cleanup_doctor_slots(
    doctor_email: str,
    current_user=Depends(get_current_user)
):
    """Clean up and regenerate slots for a doctor based on their current weekly schedule"""
    try:
        # Verify user is a doctor
        if current_user.get('role') != 'doctor':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can cleanup slots"
            )
        
        # Verify doctor is cleaning up their own slots
        if current_user.get('sub') != doctor_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cleanup your own slots"
            )
        
        result = availability_service.cleanup_doctor_slots(doctor_email)
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "slots_removed": result["slots_removed"],
                "slots_generated": result["slots_generated"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to cleanup slots")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up doctor slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
