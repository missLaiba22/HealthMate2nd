from typing import Dict, Optional, List
from datetime import datetime, time, date
from pydantic import BaseModel, EmailStr
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class BlockTimeReason(str, Enum):
    LUNCH = "lunch"
    SURGERY = "surgery"
    PERSONAL = "personal"
    MEETING = "meeting"
    EMERGENCY = "emergency"
    BREAK = "break"
    TRAINING = "training"
    OTHER = "other"

class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    is_available: bool = True

class BlockTimeSlot(BaseModel):
    start_time: time
    end_time: time
    reason: BlockTimeReason
    description: Optional[str] = None
    is_override: bool = False  # True if this overrides weekly template

class WeeklySchedule(BaseModel):
    doctor_email: EmailStr
    monday: Optional[TimeSlot] = None
    tuesday: Optional[TimeSlot] = None
    wednesday: Optional[TimeSlot] = None
    thursday: Optional[TimeSlot] = None
    friday: Optional[TimeSlot] = None
    saturday: Optional[TimeSlot] = None
    sunday: Optional[TimeSlot] = None
    slot_duration_minutes: int = 30
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DailyOverride(BaseModel):
    doctor_email: EmailStr
    override_date: date
    is_available: bool = True
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    block_time_slots: List[BlockTimeSlot] = []
    override_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DoctorAvailabilityModel:
    """Database operations for Doctor Availability - Pure data layer"""
    
    @staticmethod
    def create_weekly_schedule(schedule_data: WeeklySchedule) -> Dict:
        """Create or update doctor's weekly schedule"""
        try:
            from ..database import db
            
            def convert_timeslot_to_dict(timeslot):
                if timeslot is None:
                    return None
                return {
                    "start_time": timeslot.start_time.isoformat(),
                    "end_time": timeslot.end_time.isoformat(),
                    "is_available": timeslot.is_available
                }
            
            schedule_doc = {
                "doctor_email": schedule_data.doctor_email,
                "monday": convert_timeslot_to_dict(schedule_data.monday),
                "tuesday": convert_timeslot_to_dict(schedule_data.tuesday),
                "wednesday": convert_timeslot_to_dict(schedule_data.wednesday),
                "thursday": convert_timeslot_to_dict(schedule_data.thursday),
                "friday": convert_timeslot_to_dict(schedule_data.friday),
                "saturday": convert_timeslot_to_dict(schedule_data.saturday),
                "sunday": convert_timeslot_to_dict(schedule_data.sunday),
                "slot_duration_minutes": schedule_data.slot_duration_minutes,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Use upsert to update existing or create new
            result = db.doctor_schedules.update_one(
                {"doctor_email": schedule_data.doctor_email},
                {"$set": schedule_doc},
                upsert=True
            )
            
            logger.info(f"Weekly schedule created/updated for doctor: {schedule_data.doctor_email}")
            return {"success": True, "message": "Weekly schedule saved successfully"}
            
        except Exception as e:
            logger.error(f"Error creating weekly schedule: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_weekly_schedule(doctor_email: str) -> Optional[Dict]:
        """Get doctor's weekly schedule"""
        try:
            from ..database import db
            schedule = db.doctor_schedules.find_one({"doctor_email": doctor_email}, {"_id": 0})
            return schedule
        except Exception as e:
            logger.error(f"Error fetching weekly schedule: {str(e)}")
            return None
    
    @staticmethod
    def create_appointment_slots(doctor_email: str, slot_date: date, slots: List[Dict]) -> bool:
        """Create appointment slots for a specific date"""
        try:
            from ..database import db
            
            slot_docs = []
            for slot in slots:
                slot_doc = {
                    "doctor_email": doctor_email,
                    "slot_date": slot_date.isoformat(),
                    "slot_time": slot["slot_time"].isoformat() if hasattr(slot["slot_time"], 'isoformat') else str(slot["slot_time"]),
                    "is_available": slot["is_available"],
                    "appointment_id": slot.get("appointment_id"),
                    "created_at": datetime.utcnow()
                }
                slot_docs.append(slot_doc)
            
            if slot_docs:
                # Use upsert to prevent duplicates
                for slot_doc in slot_docs:
                    db.appointment_slots.update_one(
                        {
                            "doctor_email": slot_doc["doctor_email"],
                            "slot_date": slot_doc["slot_date"],
                            "slot_time": slot_doc["slot_time"]
                        },
                        {"$set": slot_doc},
                        upsert=True
                    )
                logger.info(f"Created/updated {len(slot_docs)} slots for {doctor_email} on {slot_date}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating appointment slots: {str(e)}")
            return False
    
    @staticmethod
    def get_available_slots(doctor_email: str, start_date: date, end_date: date) -> List[Dict]:
        """Get available appointment slots for a date range"""
        try:
            from ..database import db
            
            # Convert date objects to strings for MongoDB query
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()
            
            slots = list(db.appointment_slots.find({
                "doctor_email": doctor_email,
                "slot_date": {"$gte": start_date_str, "$lte": end_date_str},
                "is_available": True
            }, {"_id": 0}).sort("slot_date", 1).sort("slot_time", 1))
            
            return slots
        except Exception as e:
            logger.error(f"Error fetching available slots: {str(e)}")
            return []
    
    @staticmethod
    def book_slot(doctor_email: str, slot_date: date, slot_time: time, appointment_id: str) -> bool:
        """Book a specific appointment slot"""
        try:
            from ..database import db
            
            result = db.appointment_slots.update_one(
                {
                    "doctor_email": doctor_email,
                    "slot_date": slot_date.isoformat(),
                    "slot_time": slot_time.isoformat(),
                    "is_available": True
                },
                {
                    "$set": {
                        "is_available": False,
                        "appointment_id": appointment_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error booking slot: {str(e)}")
            return False
    
    @staticmethod
    def cancel_slot(appointment_id: str) -> bool:
        """Cancel a booked slot"""
        try:
            from ..database import db
            
            result = db.appointment_slots.update_one(
                {"appointment_id": appointment_id},
                {
                    "$set": {
                        "is_available": True,
                        "appointment_id": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error canceling slot: {str(e)}")
            return False
    
    @staticmethod
    def create_daily_override(override_data: DailyOverride) -> Dict:
        """Create or update daily override for a specific date"""
        try:
            from ..database import db
            
            def convert_block_time_to_dict(block_time):
                return {
                    "start_time": block_time.start_time.isoformat(),
                    "end_time": block_time.end_time.isoformat(),
                    "reason": block_time.reason.value,
                    "description": block_time.description,
                    "is_override": block_time.is_override
                }
            
            override_doc = {
                "doctor_email": override_data.doctor_email,
                "override_date": override_data.override_date.isoformat(),
                "is_available": override_data.is_available,
                "start_time": override_data.start_time.isoformat() if override_data.start_time else None,
                "end_time": override_data.end_time.isoformat() if override_data.end_time else None,
                "block_time_slots": [convert_block_time_to_dict(bt) for bt in override_data.block_time_slots],
                "override_reason": override_data.override_reason,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Use upsert to update existing or create new
            result = db.daily_overrides.update_one(
                {
                    "doctor_email": override_data.doctor_email,
                    "override_date": override_data.override_date.isoformat()
                },
                {"$set": override_doc},
                upsert=True
            )
            
            logger.info(f"Daily override created/updated for doctor: {override_data.doctor_email} on {override_data.override_date}")
            return {"success": True, "message": "Daily override saved successfully"}
            
        except Exception as e:
            logger.error(f"Error creating daily override: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_daily_override(doctor_email: str, override_date: date) -> Optional[Dict]:
        """Get daily override for a specific date"""
        try:
            from ..database import db
            override = db.daily_overrides.find_one({
                "doctor_email": doctor_email,
                "override_date": override_date.isoformat()
            }, {"_id": 0})
            return override
        except Exception as e:
            logger.error(f"Error fetching daily override: {str(e)}")
            return None
    
    @staticmethod
    def get_daily_overrides_range(doctor_email: str, start_date: date, end_date: date) -> List[Dict]:
        """Get daily overrides for a date range"""
        try:
            from ..database import db
            overrides = list(db.daily_overrides.find({
                "doctor_email": doctor_email,
                "override_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
            }, {"_id": 0}).sort("override_date", 1))
            return overrides
        except Exception as e:
            logger.error(f"Error fetching daily overrides range: {str(e)}")
            return []
    
    @staticmethod
    def delete_daily_override(doctor_email: str, override_date: date) -> bool:
        """Delete daily override for a specific date"""
        try:
            from ..database import db
            result = db.daily_overrides.delete_one({
                "doctor_email": doctor_email,
                "override_date": override_date.isoformat()
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting daily override: {str(e)}")
            return False
    
    @staticmethod
    def get_day_view(doctor_email: str, view_date: date) -> Dict:
        """Get complete day view including weekly schedule and daily overrides"""
        try:
            from ..database import db
            
            # Get weekly schedule
            weekly_schedule = DoctorAvailabilityModel.get_weekly_schedule(doctor_email)
            
            # Get daily override if exists
            daily_override = DoctorAvailabilityModel.get_daily_override(doctor_email, view_date)
            
            # Get existing appointment slots for the day
            existing_slots = list(db.appointment_slots.find({
                "doctor_email": doctor_email,
                "slot_date": view_date.isoformat()
            }, {"_id": 0}).sort("slot_time", 1))
            
            # Get day name
            day_name = view_date.strftime('%A').lower()
            
            return {
                "doctor_email": doctor_email,
                "view_date": view_date.isoformat(),
                "day_name": day_name,
                "weekly_schedule": weekly_schedule,
                "daily_override": daily_override,
                "existing_slots": existing_slots,
                "has_override": daily_override is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting day view: {str(e)}")
            return {}
