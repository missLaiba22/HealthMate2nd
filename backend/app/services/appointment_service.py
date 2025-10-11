from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
import logging
from ..models.appointment import (
    AppointmentModel, AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentSlot, AppointmentStatus, DoctorAvailabilityRequest
)
from ..models.user import UserModel
from ..database import db
from .availability_service import AvailabilityService

logger = logging.getLogger(__name__)

class AppointmentService:
    """Appointment management service - handles all business logic"""
    
    def __init__(self):
        self.availability_service = AvailabilityService()
        # Create indexes for better query performance
        try:
            db.appointments.create_index([("patient_email", 1)])
            db.appointments.create_index([("doctor_email", 1)])
            db.appointments.create_index([("appointment_date", 1)])
            db.appointments.create_index([("status", 1)])
            logger.info("Successfully created indexes for appointments collection")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")

    async def create_appointment(self, appointment_data: AppointmentCreate) -> AppointmentResponse:
        """Create a new appointment with atomic operation"""
        try:
            # Check if slot is available
            if not await self._is_slot_available(
                appointment_data.doctor_email,
                appointment_data.appointment_date,
                appointment_data.appointment_time
            ):
                raise ValueError("Appointment slot is not available")
            
            # Convert to dict for MongoDB storage
            appointment_doc = AppointmentModel.to_dict(appointment_data)
            
            # Atomic operation to create appointment
            result = db.appointments.insert_one(appointment_doc)
            
            if result.inserted_id:
                logger.info(f"Appointment created: {appointment_doc['id']}")
                return AppointmentModel.from_dict(appointment_doc)
            else:
                raise Exception("Failed to create appointment")
                
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            raise

    async def get_appointment_by_id(self, appointment_id: str) -> Optional[AppointmentResponse]:
        """Get appointment by ID"""
        try:
            appointment = db.appointments.find_one({"id": appointment_id}, {"_id": 0})
            if appointment:
                return AppointmentModel.from_dict(appointment)
            return None
        except Exception as e:
            logger.error(f"Error fetching appointment: {str(e)}")
            raise

    async def get_patient_appointments(self, patient_email: str) -> List[AppointmentResponse]:
        """Get all appointments for a patient"""
        try:
            appointments = list(db.appointments.find(
                {"patient_email": patient_email},
                {"_id": 0}
            ).sort("appointment_date", -1))
            
            return [AppointmentModel.from_dict(apt) for apt in appointments if AppointmentModel.from_dict(apt)]
        except Exception as e:
            logger.error(f"Error fetching patient appointments: {str(e)}")
            raise

    async def get_doctor_appointments(self, doctor_email: str) -> List[AppointmentResponse]:
        """Get all appointments for a doctor"""
        try:
            appointments = list(db.appointments.find(
                {"doctor_email": doctor_email},
                {"_id": 0}
            ).sort("appointment_date", -1))
            
            return [AppointmentModel.from_dict(apt) for apt in appointments if AppointmentModel.from_dict(apt)]
        except Exception as e:
            logger.error(f"Error fetching doctor appointments: {str(e)}")
            raise

    async def update_appointment(self, appointment_id: str, update_data: AppointmentUpdate) -> AppointmentResponse:
        """Update an appointment"""
        try:
            # Convert update data to dict
            update_dict = AppointmentModel.update_dict(appointment_id, update_data)
            
            # Atomic operation to update appointment
            result = db.appointments.update_one(
                {"id": appointment_id},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_appointment = db.appointments.find_one({"id": appointment_id}, {"_id": 0})
                return AppointmentModel.from_dict(updated_appointment)
            else:
                raise ValueError("Appointment not found")
        except Exception as e:
            logger.error(f"Error updating appointment: {str(e)}")
            raise

    async def cancel_appointment(self, appointment_id: str) -> bool:
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
            raise

    async def get_available_slots(self, doctor_email: str, start_date: date, end_date: date) -> List[AppointmentSlot]:
        """Get available appointment slots using AvailabilityService"""
        try:
            slots = self.availability_service.get_available_slots(doctor_email, start_date, end_date)
            
            # Fill in doctor information
            doctor = UserModel.get_user_profile(doctor_email)
            for slot in slots:
                if doctor:
                    slot.doctor_name = doctor.get("name", "Unknown")
                    slot.specialization = doctor.get("specialization", "General")
                else:
                    slot.doctor_name = "Unknown"
                    slot.specialization = "General"
            
            return slots
        except Exception as e:
            logger.error(f"Error fetching available slots: {str(e)}")
            raise

    async def set_doctor_availability(self, availability_data: DoctorAvailabilityRequest) -> str:
        """Set doctor availability using AvailabilityService"""
        try:
            return self.availability_service.set_doctor_availability(availability_data)
        except Exception as e:
            logger.error(f"Error setting doctor availability: {str(e)}")
            raise

    async def get_doctors(self) -> List[Dict]:
        """Get all doctors"""
        try:
            return UserModel.get_all_doctors()
        except Exception as e:
            logger.error(f"Error fetching doctors: {str(e)}")
            raise

    async def _is_slot_available(self, doctor_email: str, appointment_date: date, appointment_time: time) -> bool:
        """Check if a specific slot is available"""
        try:
            # Check for existing appointments at the same time
            existing_appointment = db.appointments.find_one({
                "doctor_email": doctor_email,
                "appointment_date": appointment_date.isoformat(),
                "appointment_time": appointment_time.isoformat(),
                "status": {"$in": ["SCHEDULED", "CONFIRMED"]}
            })
            
            return existing_appointment is None
        except Exception as e:
            logger.error(f"Error checking slot availability: {str(e)}")
            return False

    async def get_appointment_stats(self, doctor_email: str) -> Dict:
        """Get appointment statistics for a doctor"""
        try:
            pipeline = [
                {"$match": {"doctor_email": doctor_email}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            stats = list(db.appointments.aggregate(pipeline))
            return {stat["_id"]: stat["count"] for stat in stats}
        except Exception as e:
            logger.error(f"Error getting appointment stats: {str(e)}")
            return {}

    async def get_upcoming_appointments(self, user_email: str, role: str) -> List[AppointmentResponse]:
        """Get upcoming appointments for a user"""
        try:
            today = date.today()
            query = {"appointment_date": {"$gte": today.isoformat()}}
            
            if role == "patient":
                query["patient_email"] = user_email
            elif role == "doctor":
                query["doctor_email"] = user_email
            else:
                raise ValueError("Invalid role")
            
            appointments = list(db.appointments.find(
                query,
                {"_id": 0}
            ).sort("appointment_date", 1).limit(10))
            
            return [AppointmentModel.from_dict(apt) for apt in appointments if AppointmentModel.from_dict(apt)]
        except Exception as e:
            logger.error(f"Error fetching upcoming appointments: {str(e)}")
            raise