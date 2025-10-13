from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from datetime import date, time
from ..models.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse
)
from ..services.appointment_service import AppointmentService
from ..utils.jwt import get_current_user
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Appointments"])

@router.post("/create", response_model=AppointmentResponse)
async def create_appointment(
    request: Request,
    current_user=Depends(get_current_user)
):
    """Create a new appointment"""
    try:
        # Parse JSON request body
        request_data = await request.json()
        logger.info(f"Parsed request data: {request_data}")

        # Handle time conversion
        try:
            appointment_time = time.fromisoformat(request_data['appointment_time'])
        except Exception as e:
            logger.error(f"Error parsing time: {request_data['appointment_time']}, error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid time format: {request_data['appointment_time']}")

        # Handle date conversion
        try:
            appointment_date = date.fromisoformat(request_data['appointment_date'])
        except Exception as e:
            logger.error(f"Error parsing date: {request_data['appointment_date']}, error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid date format: {request_data['appointment_date']}")

        # Create appointment data object
        appointment_data = AppointmentCreate(
            patient_email=request_data.get('patient_email', current_user['email']),
            doctor_email=request_data['doctor_email'],
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration_minutes=request_data.get('duration_minutes', 30),
            appointment_type=request_data.get('appointment_type', 'consultation'),
            notes=request_data.get('notes', '')
        )

        logger.info(f"Creating appointment for user: {current_user.get('email')}")

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
        raise HTTPException(status_code=500, detail="Internal server error")

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


