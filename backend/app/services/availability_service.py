from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
from ..models.appointment import DoctorAvailabilityRequest, AppointmentSlot
from ..database import db
import uuid
import logging

logger = logging.getLogger(__name__)

class AvailabilityService:
    """Service layer for doctor availability management - handles all business logic"""
    
    def __init__(self):
        # Create indexes for better query performance
        try:
            db.doctor_availability.create_index([("doctor_email", 1), ("day_of_week", 1)])
            db.doctor_availability.create_index([("doctor_email", 1), ("is_available", 1)])
            logger.info("Successfully created indexes for doctor_availability collection")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")

    def set_doctor_availability(self, availability_data: DoctorAvailabilityRequest) -> str:
        """Set doctor availability with atomic operation"""
        try:
            availability_id = str(uuid.uuid4())
            
            # Convert time objects to strings for MongoDB storage
            start_time = availability_data.start_time
            end_time = availability_data.end_time
            
            start_time_str = start_time.isoformat() if hasattr(start_time, 'isoformat') else str(start_time)
            end_time_str = end_time.isoformat() if hasattr(end_time, 'isoformat') else str(end_time)
            
            availability_doc = {
                "id": availability_id,
                "doctor_email": availability_data.doctor_email,
                "day_of_week": availability_data.day_of_week,
                "start_time": start_time_str,
                "end_time": end_time_str,
                "is_available": availability_data.is_available,
                "max_appointments_per_slot": availability_data.max_appointments_per_slot,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Use upsert to prevent duplicate availability entries
            result = db.doctor_availability.update_one(
                {
                    "doctor_email": availability_data.doctor_email,
                    "day_of_week": availability_data.day_of_week,
                    "start_time": start_time_str
                },
                {"$set": availability_doc},
                upsert=True
            )
            
            logger.info(f"Availability set for doctor: {availability_data.doctor_email}")
            return availability_id
            
        except Exception as e:
            logger.error(f"Error setting doctor availability: {str(e)}")
            raise

    def get_doctor_availability(self, doctor_email: str) -> List[Dict]:
        """Get doctor's availability schedule"""
        try:
            availability = list(db.doctor_availability.find(
                {"doctor_email": doctor_email, "is_available": True},
                {"_id": 0}
            ))
            logger.info(f"Retrieved {len(availability)} availability entries for doctor: {doctor_email}")
            
            # Debug: Log the structure of availability entries
            if availability:
                logger.info(f"Sample availability entry: {availability[0]}")
                logger.info(f"All availability entries: {availability}")
            
            return availability
            
        except Exception as e:
            logger.error(f"Error getting doctor availability: {str(e)}")
            return []

    def get_available_slots(self, doctor_email: str, start_date: date, end_date: date) -> List[AppointmentSlot]:
        """Get available appointment slots for a doctor within date range"""
        try:
            logger.info(f"Getting available slots for doctor: {doctor_email}, from {start_date} to {end_date}")
            
            # Get doctor's availability schedule
            availability = self.get_doctor_availability(doctor_email)
            logger.info(f"Found {len(availability)} availability entries for doctor: {doctor_email}")
            
            # Get existing appointments for the date range
            existing_appointments = list(db.appointments.find(
                {
                    "doctor_email": doctor_email,
                    "appointment_date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    },
                    "status": {"$in": ["SCHEDULED", "CONFIRMED", "scheduled", "confirmed"]}
                },
                {"_id": 0, "appointment_date": 1, "appointment_time": 1}
            ))
            logger.info(f"Found {len(existing_appointments)} existing appointments")
            
            # Generate available slots
            slots = []
            current_date = start_date
            
            while current_date <= end_date:
                day_of_week = current_date.weekday()
                logger.info(f"Processing date: {current_date}, day of week: {day_of_week}")
                
                # Find availability for this day of week
                day_availability = [
                    av for av in availability 
                    if av.get("day_of_week") == day_of_week
                ]
                logger.info(f"Found {len(day_availability)} availability entries for day {day_of_week}")
                
                # Debug: Log the availability structure
                if availability:
                    logger.info(f"Sample availability entry: {availability[0]}")
                    logger.info(f"Available keys: {list(availability[0].keys())}")
                
                # If no availability found for this day, try to use any available entry as fallback
                if not day_availability and availability:
                    logger.info(f"No availability found for day {day_of_week}, using first available entry as fallback")
                    day_availability = [availability[0]]  # Use first available entry
                
                for av in day_availability:
                    logger.info(f"Processing availability: {av}")
                    
                    # Check if required fields exist
                    if "start_time" not in av or "end_time" not in av:
                        logger.error(f"Missing required fields in availability: {av}")
                        continue
                    
                    # Generate time slots for this availability period
                    time_slots = self._generate_time_slots(
                        av["start_time"], 
                        av["end_time"], 
                        av.get("max_appointments_per_slot", 1)
                    )
                    logger.info(f"Generated {len(time_slots)} time slots")
                    
                    for time_slot in time_slots:
                        # Check if slot is already booked
                        is_available = not self._is_slot_booked(
                            current_date, 
                            time_slot, 
                            existing_appointments
                        )
                        
                        slots.append(AppointmentSlot(
                            date=current_date,
                            time=time_slot,
                            doctor_email=doctor_email,
                            doctor_name="",  # Will be filled by calling service
                            specialization="",  # Will be filled by calling service
                            is_available=is_available,
                            duration_minutes=30
                        ))
                
                current_date = date(current_date.year, current_date.month, current_date.day + 1)
            
            logger.info(f"Generated {len(slots)} total slots for doctor: {doctor_email}")
            return slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []

    def _generate_time_slots(self, start_time_str: str, end_time_str: str, max_appointments: int) -> List[time]:
        """Generate time slots between start and end time"""
        try:
            # Handle different time formats
            if isinstance(start_time_str, str):
                if ':' in start_time_str:
                    time_parts = start_time_str.split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2]) if len(time_parts) > 2 else 0
                        start_time = time(hour, minute, second)
                    else:
                        start_time = time.fromisoformat(start_time_str)
                else:
                    start_time = time.fromisoformat(start_time_str)
            else:
                start_time = start_time_str
                
            if isinstance(end_time_str, str):
                if ':' in end_time_str:
                    time_parts = end_time_str.split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2]) if len(time_parts) > 2 else 0
                        end_time = time(hour, minute, second)
                    else:
                        end_time = time.fromisoformat(end_time_str)
                else:
                    end_time = time.fromisoformat(end_time_str)
            else:
                end_time = end_time_str
            
            slots = []
            current_time = start_time
            
            while current_time < end_time:
                slots.append(current_time)
                # Add 30 minutes for next slot
                current_datetime = datetime.combine(date.today(), current_time)
                next_datetime = current_datetime + timedelta(minutes=30)
                current_time = next_datetime.time()
            
            logger.info(f"Generated {len(slots)} time slots from {start_time} to {end_time}")
            return slots
            
        except Exception as e:
            logger.error(f"Error generating time slots: {str(e)}")
            return []

    def _is_slot_booked(self, appointment_date: date, time_slot: time, existing_appointments: List[Dict]) -> bool:
        """Check if a time slot is already booked"""
        date_str = appointment_date.isoformat()
        time_str = time_slot.isoformat()
        
        for appointment in existing_appointments:
            if (appointment["appointment_date"] == date_str and 
                appointment["appointment_time"] == time_str):
                return True
        return False

    def update_availability(self, availability_id: str, update_data: Dict) -> bool:
        """Update doctor availability"""
        try:
            result = db.doctor_availability.update_one(
                {"id": availability_id},
                {
                    "$set": {
                        **update_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated availability: {availability_id}")
                return True
            else:
                logger.warning(f"No availability found to update: {availability_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating availability: {str(e)}")
            return False

    def delete_availability(self, availability_id: str) -> bool:
        """Delete doctor availability"""
        try:
            result = db.doctor_availability.delete_one({"id": availability_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted availability: {availability_id}")
                return True
            else:
                logger.warning(f"No availability found to delete: {availability_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting availability: {str(e)}")
            return False

