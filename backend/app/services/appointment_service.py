from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
import logging
from ..models.appointment import (
    AppointmentModel, AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentSlot, AppointmentStatus, DoctorAvailabilityRequest
)
from ..models.user import UserModel

logger = logging.getLogger(__name__)

class AppointmentService:
    """Appointment management service"""
    
    @staticmethod
    def _convert_time_string_to_time(time_str: str) -> time:
        """Convert time string back to time object"""
        try:
            if isinstance(time_str, str):
                # Handle ISO format time strings (HH:MM:SS)
                if ':' in time_str:
                    time_parts = time_str.split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2]) if len(time_parts) > 2 else 0
                        return time(hour, minute, second)
                # Handle other string formats
                return time.fromisoformat(time_str)
            return time_str
        except Exception:
            # If conversion fails, return a default time
            return time(9, 0)
    
    @staticmethod
    def _convert_appointment_data(apt_data: Dict) -> Dict:
        """Convert appointment data from database format to Pydantic model format"""
        converted_data = apt_data.copy()
        
        # Convert time string back to time object if needed
        if 'appointment_time' in converted_data and isinstance(converted_data['appointment_time'], str):
            converted_data['appointment_time'] = AppointmentService._convert_time_string_to_time(converted_data['appointment_time'])
        
        return converted_data
    
    @staticmethod
    async def create_appointment(appointment_data: AppointmentCreate) -> AppointmentResponse:
        """Create a new appointment"""
        try:
            # Create appointment in database
            appointment_id = AppointmentModel.create_appointment(appointment_data)
            
            # Get appointment details
            appointment = AppointmentModel.get_appointment_by_id(appointment_id)
            if not appointment:
                raise ValueError("Failed to create appointment")
            
            # Get doctor and patient names
            doctor = UserModel.get_user_profile(appointment_data.doctor_email)
            patient = UserModel.get_user_profile(appointment_data.patient_email)
            
            return AppointmentResponse(
                id=appointment["id"],
                patient_email=appointment["patient_email"],
                doctor_email=appointment["doctor_email"],
                appointment_date=appointment["appointment_date"],
                appointment_time=appointment["appointment_time"],
                duration_minutes=appointment["duration_minutes"],
                appointment_type=appointment["appointment_type"],
                notes=appointment["notes"],
                status=appointment["status"],
                created_at=appointment["created_at"],
                updated_at=appointment["updated_at"],
                doctor_name=doctor.get("name") if doctor else None,
                patient_name=patient.get("name") if patient else None
            )
            
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            raise

    @staticmethod
    async def get_patient_appointments(patient_email: str) -> List[AppointmentResponse]:
        """Get all appointments for a patient"""
        try:
            appointments = AppointmentModel.get_patient_appointments(patient_email)
            converted_appointments = [AppointmentService._convert_appointment_data(apt) for apt in appointments]
            return [AppointmentResponse(**apt) for apt in converted_appointments]
        except Exception as e:
            logger.error(f"Error fetching patient appointments: {str(e)}")
            raise

    @staticmethod
    async def get_doctor_appointments(doctor_email: str) -> List[AppointmentResponse]:
        """Get all appointments for a doctor"""
        try:
            appointments = AppointmentModel.get_doctor_appointments(doctor_email)
            converted_appointments = [AppointmentService._convert_appointment_data(apt) for apt in appointments]
            return [AppointmentResponse(**apt) for apt in converted_appointments]
        except Exception as e:
            logger.error(f"Error fetching doctor appointments: {str(e)}")
            raise

    @staticmethod
    async def get_available_slots(doctor_email: str, start_date: date, end_date: date) -> List[AppointmentSlot]:
        """Get available appointment slots"""
        try:
            slots_data = AppointmentModel.get_available_slots(doctor_email, start_date, end_date)
            doctor = UserModel.get_user_profile(doctor_email)
            
            slots = []
            for slot_data in slots_data:
                slots.append(AppointmentSlot(
                    date=slot_data["date"],
                    time=slot_data["time"],
                    doctor_email=slot_data["doctor_email"],
                    doctor_name=doctor.get("name", "Unknown") if doctor else "Unknown",
                    specialization=doctor.get("specialization", "General") if doctor else "General",
                    is_available=slot_data["is_available"],
                    duration_minutes=slot_data["duration_minutes"]
                ))
            return slots
        except Exception as e:
            logger.error(f"Error fetching available slots: {str(e)}")
            raise

    @staticmethod
    async def update_appointment(appointment_id: str, update_data: AppointmentUpdate) -> AppointmentResponse:
        """Update an appointment"""
        try:
            # Convert Pydantic model to dict
            update_dict = update_data.dict(exclude_unset=True)
            
            # Convert time objects to strings for MongoDB storage
            if 'appointment_time' in update_dict and update_dict['appointment_time']:
                if hasattr(update_dict['appointment_time'], 'isoformat'):
                    update_dict['appointment_time'] = update_dict['appointment_time'].isoformat()
                else:
                    update_dict['appointment_time'] = str(update_dict['appointment_time'])
            
            # Update in database
            success = AppointmentModel.update_appointment(appointment_id, update_dict)
            if not success:
                raise ValueError("Appointment not found or update failed")
            
            # Get updated appointment
            appointment = AppointmentModel.get_appointment_by_id(appointment_id)
            if not appointment:
                raise ValueError("Appointment not found")
            
            # Convert appointment data for Pydantic model
            converted_appointment = AppointmentService._convert_appointment_data(appointment)
            return AppointmentResponse(**converted_appointment)
            
        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}")
            raise

    @staticmethod
    async def cancel_appointment(appointment_id: str) -> bool:
        """Cancel an appointment"""
        try:
            return AppointmentModel.cancel_appointment(appointment_id)
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            raise

    @staticmethod
    async def set_doctor_availability(availability_data: DoctorAvailabilityRequest) -> str:
        """Set doctor availability"""
        try:
            # Convert the Pydantic model to dict and handle time serialization
            availability_dict = availability_data.dict()
            
            # Convert time objects to strings for MongoDB compatibility
            if 'start_time' in availability_dict and availability_dict['start_time']:
                if hasattr(availability_dict['start_time'], 'isoformat'):
                    availability_dict['start_time'] = availability_dict['start_time'].isoformat()
                else:
                    availability_dict['start_time'] = str(availability_dict['start_time'])
                    
            if 'end_time' in availability_dict and availability_dict['end_time']:
                if hasattr(availability_dict['end_time'], 'isoformat'):
                    availability_dict['end_time'] = availability_dict['end_time'].isoformat()
                else:
                    availability_dict['end_time'] = str(availability_dict['end_time'])
            
            return AppointmentModel.set_doctor_availability(availability_dict)
        except Exception as e:
            logger.error(f"Error setting doctor availability: {str(e)}")
            raise

    @staticmethod
    async def get_doctors() -> List[Dict]:
        """Get all doctors"""
        try:
            return UserModel.get_all_doctors()
        except Exception as e:
            logger.error(f"Error fetching doctors: {str(e)}")
            raise