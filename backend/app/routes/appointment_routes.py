from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from datetime import date
from ..models.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentSlot, DoctorAvailabilityRequest
)
from ..services.appointment_service import AppointmentService
from ..utils.jwt import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Appointments"])

@router.post("/create", response_model=AppointmentResponse)
async def create_appointment(
    request: Request,
    current_user=Depends(get_current_user)
):
    """Create a new appointment"""
    try:
        # Get raw request body for debugging
        body = await request.body()
        logger.info(f"Raw request body: {body}")
        
        # Parse JSON manually to see what's being sent
        import json
        try:
            request_data = json.loads(body)
            logger.info(f"Parsed request data: {request_data}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Create AppointmentCreate object manually
        from ..models.appointment import AppointmentCreate
        from datetime import date, time
        
        # Handle time conversion
        appointment_time = request_data.get('appointment_time', '')
        if isinstance(appointment_time, str):
            try:
                time_parts = appointment_time.split(':')
                if len(time_parts) >= 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    appointment_time = time(hour, minute)
                else:
                    appointment_time = time.fromisoformat(appointment_time)
            except Exception as e:
                logger.error(f"Error parsing time: {appointment_time}, error: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid time format: {appointment_time}")
        
        # Handle date conversion
        appointment_date = request_data.get('appointment_date', '')
        if isinstance(appointment_date, str):
            try:
                appointment_date = date.fromisoformat(appointment_date)
            except Exception as e:
                logger.error(f"Error parsing date: {appointment_date}, error: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid date format: {appointment_date}")
        
        # Create appointment data object
        appointment_data = AppointmentCreate(
            patient_email=request_data.get('patient_email', '') or current_user['email'],
            doctor_email=request_data.get('doctor_email', ''),
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=request_data.get('duration_minutes', 30),
            appointment_type=request_data.get('appointment_type', 'consultation'),
            notes=request_data.get('notes', '')
        )
        
        logger.info(f"Creating appointment for user: {current_user.get('email')}")
        logger.info(f"Appointment data: {appointment_data}")
        
        # Ensure the request is from the patient themselves or a doctor
        if current_user['role'] not in ['patient', 'doctor']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # If patient is creating, ensure they're creating for themselves
        if current_user['role'] == 'patient' and appointment_data.patient_email != current_user['email']:
            raise HTTPException(status_code=403, detail="Patients can only create appointments for themselves")
        
        appointment_service = AppointmentService()
        return await appointment_service.create_appointment(appointment_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        logger.error(f"Appointment data received: {appointment_data}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/patient/{patient_email}", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    patient_email: str,
    current_user=Depends(get_current_user)
):
    """Get appointments for a patient"""
    try:
        # Ensure user can only access their own appointments
        if current_user['role'] == 'patient' and patient_email != current_user['email']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        appointment_service = AppointmentService()
        return await appointment_service.get_patient_appointments(patient_email)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/doctor/{doctor_email}", response_model=List[AppointmentResponse])
async def get_doctor_appointments(
    doctor_email: str,
    current_user=Depends(get_current_user)
):
    """Get appointments for a doctor"""
    try:
        # Ensure user can only access their own appointments
        if current_user['role'] == 'doctor' and doctor_email != current_user['email']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        appointment_service = AppointmentService()
        return await appointment_service.get_doctor_appointments(doctor_email)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching doctor appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/slots/{doctor_email}", response_model=List[AppointmentSlot])
async def get_available_slots(
    doctor_email: str,
    start_date: date,
    end_date: date,
    current_user=Depends(get_current_user)
):
    """Get available appointment slots for a doctor"""
    try:
        appointment_service = AppointmentService()
        return await appointment_service.get_available_slots(doctor_email, start_date, end_date)
        
    except Exception as e:
        logger.error(f"Error fetching available slots: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdate,
    current_user=Depends(get_current_user)
):
    """Update an appointment"""
    try:
        appointment_service = AppointmentService()
        return await appointment_service.update_appointment(appointment_id, update_data)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    current_user=Depends(get_current_user)
):
    """Cancel an appointment"""
    try:
        appointment_service = AppointmentService()
        success = await appointment_service.cancel_appointment(appointment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {"message": "Appointment cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/availability")
async def set_doctor_availability(
    availability_data: DoctorAvailabilityRequest,
    current_user=Depends(get_current_user)
):
    """Set doctor availability"""
    try:
        # Only doctors can set their availability
        if current_user['role'] != 'doctor':
            raise HTTPException(status_code=403, detail="Only doctors can set availability")
        
        # Ensure doctor is setting their own availability
        if availability_data.doctor_email != current_user['email']:
            raise HTTPException(status_code=403, detail="Can only set your own availability")
        
        appointment_service = AppointmentService()
        availability_id = await appointment_service.set_doctor_availability(availability_data)
        return {"message": "Availability set successfully", "availability_id": availability_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting doctor availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/doctors")
async def get_doctors(current_user=Depends(get_current_user)):
    """Get all doctors"""
    try:
        appointment_service = AppointmentService()
        return await appointment_service.get_doctors()
        
    except Exception as e:
        logger.error(f"Error fetching doctors: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/my-appointments")
async def get_my_appointments(current_user=Depends(get_current_user)):
    """Get current user's appointments"""
    try:
        email = current_user["email"]
        role = current_user["role"]
        
        appointment_service = AppointmentService()
        if role == "patient":
            return await appointment_service.get_patient_appointments(email)
        elif role == "doctor":
            return await appointment_service.get_doctor_appointments(email)
        else:
            raise HTTPException(status_code=403, detail="Access denied")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching my appointments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/my-availability")
async def get_my_availability(current_user=Depends(get_current_user)):
    """Get current doctor's availability"""
    try:
        if current_user["role"] != "doctor":
            raise HTTPException(status_code=403, detail="Only doctors can view availability")
        
        # This would need to be implemented in the service
        return {"message": "Availability endpoint - to be implemented"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/time-slots")
async def get_time_slots(
    doctor_email: str,
    date: str,
    current_user=Depends(get_current_user)
):
    """Get time slots for a doctor on a specific date"""
    try:
        from datetime import datetime
        appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        logger.info(f"Getting time slots for doctor: {doctor_email}, date: {appointment_date}")
        
        # Get available slots for the date
        appointment_service = AppointmentService()
        slots = await appointment_service.get_available_slots(doctor_email, appointment_date, appointment_date)
        
        logger.info(f"Found {len(slots)} slots for doctor: {doctor_email}")
        
        # Convert slots to time strings
        time_slots = []
        for slot in slots:
            if slot.is_available:
                time_slots.append(slot.time.strftime("%H:%M"))
                logger.info(f"Available slot: {slot.time.strftime('%H:%M')}")
        
        logger.info(f"Returning {len(time_slots)} available time slots")
        return {"time_slots": time_slots}
        
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching time slots: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

