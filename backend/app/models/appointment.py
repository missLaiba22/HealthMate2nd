from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, date, time
from enum import Enum
from ..database import db
import logging
import uuid

logger = logging.getLogger(__name__)

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"

class AppointmentBase(BaseModel):
    patient_email: EmailStr
    doctor_email: EmailStr
    appointment_date: date
    appointment_time: time
    duration_minutes: int = 30
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    id: str
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None

class AppointmentSlot(BaseModel):
    date: date
    time: time
    doctor_email: EmailStr
    doctor_name: str
    specialization: str
    is_available: bool
    duration_minutes: int = 30

class AppointmentReminder(BaseModel):
    appointment_id: str
    patient_email: EmailStr
    doctor_email: EmailStr
    appointment_date: date
    appointment_time: time
    reminder_type: str  # "confirmation", "reminder_24h", "reminder_1h"
    message: str
    sent_at: Optional[datetime] = None

class DoctorAvailabilityRequest(BaseModel):
    doctor_email: EmailStr
    day_of_week: int
    start_time: time
    end_time: time
    is_available: bool = True
    max_appointments_per_slot: int = 1
    
    class Config:
        # Allow string input for time fields and convert them
        json_encoders = {
            time: lambda v: v.isoformat() if v else None
        }

class AppointmentModel:
    """Database operations for Appointment model"""
    
    @staticmethod
    def create_appointment(appointment_data: AppointmentCreate) -> str:
        """Create a new appointment"""
        try:
            # Convert time object to string for MongoDB storage
            appointment_time = appointment_data.appointment_time
            if hasattr(appointment_time, 'isoformat'):
                appointment_time_str = appointment_time.isoformat()
            else:
                appointment_time_str = str(appointment_time)
            
            appointment_doc = {
                "id": str(uuid.uuid4()),
                "patient_email": appointment_data.patient_email,
                "doctor_email": appointment_data.doctor_email,
                "appointment_date": appointment_data.appointment_date,
                "appointment_time": appointment_time_str,
                "duration_minutes": appointment_data.duration_minutes,
                "appointment_type": appointment_data.appointment_type,
                "notes": appointment_data.notes,
                "status": AppointmentStatus.SCHEDULED,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = db.appointments.insert_one(appointment_doc)
            return appointment_doc["id"]
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            raise

    @staticmethod
    def get_appointment_by_id(appointment_id: str) -> Optional[Dict]:
        """Get appointment by ID"""
        try:
            return db.appointments.find_one({"id": appointment_id})
        except Exception as e:
            logger.error(f"Error fetching appointment: {str(e)}")
            return None

    @staticmethod
    def get_patient_appointments(patient_email: str) -> List[Dict]:
        """Get all appointments for a patient"""
        try:
            appointments = list(db.appointments.find(
                {"patient_email": patient_email},
                {"_id": 0}
            ))
            return appointments
        except Exception as e:
            logger.error(f"Error fetching patient appointments: {str(e)}")
            return []

    @staticmethod
    def get_doctor_appointments(doctor_email: str) -> List[Dict]:
        """Get all appointments for a doctor"""
        try:
            appointments = list(db.appointments.find(
                {"doctor_email": doctor_email},
                {"_id": 0}
            ))
            return appointments
        except Exception as e:
            logger.error(f"Error fetching doctor appointments: {str(e)}")
            return []

    @staticmethod
    def update_appointment(appointment_id: str, update_data: Dict) -> bool:
        """Update appointment"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = db.appointments.update_one(
                {"id": appointment_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}")
            return False

    @staticmethod
    def cancel_appointment(appointment_id: str) -> bool:
        """Cancel an appointment"""
        try:
            result = db.appointments.update_one(
                {"id": appointment_id},
                {
                    "$set": {
                        "status": AppointmentStatus.CANCELLED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return False

    @staticmethod
    def get_available_slots(doctor_email: str, start_date: date, end_date: date) -> List[Dict]:
        """Get available appointment slots for a doctor"""
        try:
            # This is a simplified implementation
            # In a real app, you'd check doctor availability and existing appointments
            slots = []
            current_date = start_date
            while current_date <= end_date:
                # Generate time slots for each day (9 AM to 5 PM, 30-minute intervals)
                for hour in range(9, 17):
                    for minute in [0, 30]:
                        slot_time = time(hour, minute)
                        slots.append({
                            "date": current_date,
                            "time": slot_time,
                            "doctor_email": doctor_email,
                            "is_available": True,
                            "duration_minutes": 30
                        })
                current_date = date(current_date.year, current_date.month, current_date.day + 1)
            return slots
        except Exception as e:
            logger.error(f"Error fetching available slots: {str(e)}")
            return []

    @staticmethod
    def set_doctor_availability(availability_data: Dict) -> str:
        """Set doctor availability"""
        try:
            availability_id = str(uuid.uuid4())
            
            # Convert time objects to strings for MongoDB storage
            start_time = availability_data["start_time"]
            end_time = availability_data["end_time"]
            
            # Handle both time objects and string inputs
            if hasattr(start_time, 'isoformat'):
                start_time_str = start_time.isoformat()
            else:
                start_time_str = str(start_time)
                
            if hasattr(end_time, 'isoformat'):
                end_time_str = end_time.isoformat()
            else:
                end_time_str = str(end_time)
            
            availability_doc = {
                "id": availability_id,
                "doctor_email": availability_data["doctor_email"],
                "day_of_week": availability_data["day_of_week"],
                "start_time": start_time_str,
                "end_time": end_time_str,
                "is_available": availability_data.get("is_available", True),
                "max_appointments_per_slot": availability_data.get("max_appointments_per_slot", 1),
                "created_at": datetime.utcnow()
            }
            db.doctor_availability.insert_one(availability_doc)
            return availability_id
        except Exception as e:
            logger.error(f"Error setting doctor availability: {str(e)}")
            raise