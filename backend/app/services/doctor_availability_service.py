from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
from ..models.doctor_availability import (
    WeeklySchedule, DoctorAvailabilityModel, TimeSlot,
    DailyOverride, BlockTimeSlot, BlockTimeReason
)
from ..models.appointment import AppointmentSlot
from ..database import db
import logging

logger = logging.getLogger(__name__)

class DoctorAvailabilityService:
    """Business logic for doctor availability management"""
    
    def __init__(self):
        self.availability_model = DoctorAvailabilityModel()
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            db.doctor_schedules.create_index("doctor_email", unique=True)
            db.appointment_slots.create_index([("doctor_email", 1), ("slot_date", 1)])
            db.appointment_slots.create_index([("doctor_email", 1), ("slot_date", 1), ("slot_time", 1)], unique=True)
            db.appointment_slots.create_index([("slot_date", 1), ("is_available", 1)])
            db.daily_overrides.create_index([("doctor_email", 1), ("override_date", 1)], unique=True)
            db.daily_overrides.create_index([("override_date", 1)])
            logger.info("Database indexes created for availability system")
            
            # Clean up any existing duplicate slots
            self._cleanup_duplicate_slots()
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    def _cleanup_duplicate_slots(self):
        """Remove duplicate appointment slots"""
        try:
            # Find and remove duplicate slots
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "doctor_email": "$doctor_email",
                            "slot_date": "$slot_date",
                            "slot_time": "$slot_time"
                        },
                        "duplicates": {"$push": "$_id"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$match": {
                        "count": {"$gt": 1}
                    }
                }
            ]
            
            duplicates = list(db.appointment_slots.aggregate(pipeline))
            
            for duplicate in duplicates:
                # Keep the first one, remove the rest
                duplicate_ids = duplicate["duplicates"][1:]  # Skip the first one
                if duplicate_ids:
                    db.appointment_slots.delete_many({"_id": {"$in": duplicate_ids}})
                    logger.info(f"Removed {len(duplicate_ids)} duplicate slots for {duplicate['_id']['doctor_email']} on {duplicate['_id']['slot_date']} at {duplicate['_id']['slot_time']}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up duplicate slots: {str(e)}")
    
    def set_weekly_schedule(self, schedule_data: WeeklySchedule) -> Dict:
        """Set doctor's weekly availability schedule"""
        try:
            # Save weekly schedule
            result = self.availability_model.create_weekly_schedule(schedule_data)
            
            if result["success"]:
                # Generate slots for next 30 days
                self._generate_slots_for_period(schedule_data.doctor_email, date.today(), date.today() + timedelta(days=30))
                logger.info(f"Weekly schedule set and slots generated for {schedule_data.doctor_email}")
            
            return result
        except Exception as e:
            logger.error(f"Error setting weekly schedule: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_weekly_schedule(self, doctor_email: str) -> Optional[Dict]:
        """Get doctor's weekly schedule"""
        try:
            return self.availability_model.get_weekly_schedule(doctor_email)
        except Exception as e:
            logger.error(f"Error getting weekly schedule: {str(e)}")
            return None
    
    def get_available_slots(self, doctor_email: str, start_date: date, end_date: date) -> List[Dict]:
        """Get available appointment slots for a date range"""
        try:
            logger.info(f"Getting available slots for {doctor_email} from {start_date} to {end_date}")
            
            # Check if doctor has set their weekly schedule
            weekly_schedule = self.get_weekly_schedule(doctor_email)
            if not weekly_schedule:
                logger.info(f"No weekly schedule found for doctor: {doctor_email}")
                return []
            
            logger.info(f"Weekly schedule found for {doctor_email}")
            
            # First, ensure slots are generated for the requested period
            self._ensure_slots_generated(doctor_email, start_date, end_date)
            
            # Get available slots
            slots = self.availability_model.get_available_slots(doctor_email, start_date, end_date)
            logger.info(f"Found {len(slots)} slots for {doctor_email}")
            
            # Format slots for API response
            formatted_slots = []
            for slot in slots:
                formatted_slots.append({
                    "doctor_email": slot["doctor_email"],
                    "slot_date": slot["slot_date"],
                    "slot_time": slot["slot_time"],
                    "is_available": slot["is_available"],
                    "appointment_id": slot.get("appointment_id")
                })
            
            logger.info(f"Returning {len(formatted_slots)} formatted slots for {doctor_email}")
            return formatted_slots
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []
    
    def book_appointment_slot(self, doctor_email: str, slot_date: date, slot_time: time, appointment_id: str) -> bool:
        """Book a specific appointment slot"""
        try:
            return self.availability_model.book_slot(doctor_email, slot_date, slot_time, appointment_id)
        except Exception as e:
            logger.error(f"Error booking appointment slot: {str(e)}")
            return False
    
    def cancel_appointment_slot(self, appointment_id: str) -> bool:
        """Cancel a booked appointment slot"""
        try:
            return self.availability_model.cancel_slot(appointment_id)
        except Exception as e:
            logger.error(f"Error canceling appointment slot: {str(e)}")
            return False
    
    def _generate_slots_for_period(self, doctor_email: str, start_date: date, end_date: date):
        """Generate appointment slots for a specific period based on weekly schedule"""
        try:
            # Get doctor's weekly schedule
            weekly_schedule = self.get_weekly_schedule(doctor_email)
            if not weekly_schedule:
                logger.warning(f"No weekly schedule found for doctor: {doctor_email}")
                return
            
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%A').lower()
                
                # Check if doctor is available on this day
                day_schedule = weekly_schedule.get(day_name)
                if day_schedule and day_schedule.get("is_available", False):
                    # Generate slots for this day
                    self._generate_slots_for_day(doctor_email, current_date, day_schedule)
                
                current_date += timedelta(days=1)
                
        except Exception as e:
            logger.error(f"Error generating slots for period: {str(e)}")
    
    def _generate_slots_for_day(self, doctor_email: str, slot_date: date, day_schedule: Dict):
        """Generate slots for a specific day"""
        try:
            from datetime import datetime
            
            # Handle both HH:MM and HH:MM:SS formats
            start_time_str = day_schedule["start_time"]
            end_time_str = day_schedule["end_time"]
            
            # Try HH:MM:SS format first, then HH:MM
            try:
                start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
            except ValueError:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
            
            try:
                end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
            except ValueError:
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
            slot_duration = day_schedule.get("slot_duration_minutes", 30)
            
            # Check if slots already exist for this day
            existing_slots = list(db.appointment_slots.find({
                "doctor_email": doctor_email,
                "slot_date": slot_date.isoformat()
            }, {"_id": 0}))
            
            if existing_slots:
                logger.info(f"Slots already exist for {doctor_email} on {slot_date}")
                return
            
            # Generate slots
            slots = []
            current_time = start_time
            
            while current_time < end_time:
                # Calculate end time for this slot
                slot_start = current_time
                slot_end = self._add_minutes_to_time(current_time, slot_duration)
                
                if slot_end <= end_time:
                    slot = {
                        "doctor_email": doctor_email,
                        "slot_date": slot_date.isoformat(),
                        "slot_time": slot_start,
                        "is_available": True,
                        "appointment_id": None,
                        "created_at": datetime.utcnow()
                    }
                    slots.append(slot)
                
                current_time = slot_end
            
            # Save slots to database
            if slots:
                self.availability_model.create_appointment_slots(doctor_email, slot_date, slots)
                logger.info(f"Generated {len(slots)} slots for {doctor_email} on {slot_date}")
                
        except Exception as e:
            logger.error(f"Error generating slots for day: {str(e)}")
    
    def _ensure_slots_generated(self, doctor_email: str, start_date: date, end_date: date):
        """Ensure slots are generated for the requested period"""
        try:
            logger.info(f"Ensuring slots generated for {doctor_email} from {start_date} to {end_date}")
            
            # Get doctor's weekly schedule first
            weekly_schedule = self.get_weekly_schedule(doctor_email)
            if not weekly_schedule:
                logger.warning(f"No weekly schedule found for doctor: {doctor_email}")
                return
            
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%A').lower()
                day_schedule = weekly_schedule.get(day_name)
                
                # Check if slots exist for this date
                existing_slots = list(db.appointment_slots.find({
                    "doctor_email": doctor_email,
                    "slot_date": current_date.isoformat()
                }, {"_id": 0}))
                
                logger.info(f"Date {current_date} ({day_name}): available={day_schedule and day_schedule.get('is_available', False)}, existing_slots={len(existing_slots)}")
                
                # If doctor is available on this day and no slots exist, generate them
                if day_schedule and day_schedule.get("is_available", False) and not existing_slots:
                    logger.info(f"Generating slots for {doctor_email} on {current_date}")
                    self._generate_slots_for_day(doctor_email, current_date, day_schedule)
                # If doctor is not available on this day but slots exist, remove them
                elif (not day_schedule or not day_schedule.get("is_available", False)) and existing_slots:
                    result = db.appointment_slots.delete_many({
                        "doctor_email": doctor_email,
                        "slot_date": current_date.isoformat()
                    })
                    if result.deleted_count > 0:
                        logger.info(f"Removed {result.deleted_count} slots for {doctor_email} on {current_date} - not available")
                
                current_date += timedelta(days=1)
                
        except Exception as e:
            logger.error(f"Error ensuring slots generated: {str(e)}")
    
    def cleanup_doctor_slots(self, doctor_email: str) -> Dict:
        """Clean up all slots for a doctor and regenerate based on current weekly schedule"""
        try:
            # Remove all existing slots for this doctor
            result = db.appointment_slots.delete_many({"doctor_email": doctor_email})
            logger.info(f"Removed {result.deleted_count} existing slots for {doctor_email}")
            
            # Check if doctor has a weekly schedule
            weekly_schedule = self.get_weekly_schedule(doctor_email)
            if not weekly_schedule:
                return {
                    "success": True,
                    "message": f"No weekly schedule found for {doctor_email}. All slots removed.",
                    "slots_removed": result.deleted_count,
                    "slots_generated": 0
                }
            
            # Generate new slots for next 30 days
            from datetime import timedelta
            end_date = date.today() + timedelta(days=30)
            self._generate_slots_for_period(doctor_email, date.today(), end_date)
            
            # Count generated slots
            generated_slots = list(db.appointment_slots.find({"doctor_email": doctor_email}))
            
            return {
                "success": True,
                "message": f"Successfully cleaned up and regenerated slots for {doctor_email}",
                "slots_removed": result.deleted_count,
                "slots_generated": len(generated_slots)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up doctor slots: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _add_minutes_to_time(self, time_obj: time, minutes: int) -> time:
        """Add minutes to a time object"""
        from datetime import datetime, timedelta
        
        dt = datetime.combine(date.today(), time_obj)
        new_dt = dt + timedelta(minutes=minutes)
        return new_dt.time()
    
    def update_weekly_schedule(self, doctor_email: str, schedule_data: WeeklySchedule) -> Dict:
        """Update doctor's weekly schedule and regenerate slots"""
        try:
            # Update weekly schedule
            result = self.availability_model.create_weekly_schedule(schedule_data)
            
            if result["success"]:
                # Delete existing slots for future dates
                db.appointment_slots.delete_many({
                    "doctor_email": doctor_email,
                    "slot_date": {"$gte": date.today().isoformat()}
                })
                
                # Regenerate slots for next 30 days
                self._generate_slots_for_period(doctor_email, date.today(), date.today() + timedelta(days=30))
                logger.info(f"Weekly schedule updated and slots regenerated for {doctor_email}")
            
            return result
        except Exception as e:
            logger.error(f"Error updating weekly schedule: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def delete_weekly_schedule(self, doctor_email: str) -> bool:
        """Delete doctor's weekly schedule and all future slots"""
        try:
            # Delete weekly schedule
            db.doctor_schedules.delete_one({"doctor_email": doctor_email})
            
            # Delete all future slots
            db.appointment_slots.delete_many({
                "doctor_email": doctor_email,
                "slot_date": {"$gte": date.today().isoformat()}
            })
            
            logger.info(f"Weekly schedule and future slots deleted for {doctor_email}")
            return True
        except Exception as e:
            logger.error(f"Error deleting weekly schedule: {str(e)}")
            return False
    
    # ===== DAILY ADJUSTMENTS & BLOCK TIME FUNCTIONALITY =====
    
    def create_daily_override(self, override_data: DailyOverride) -> Dict:
        """Create or update daily override for a specific date"""
        try:
            # Validate override data
            if override_data.start_time and override_data.end_time:
                if override_data.start_time >= override_data.end_time:
                    return {"success": False, "error": "Start time must be before end time"}
            
            # Validate block time slots
            for block_slot in override_data.block_time_slots:
                if block_slot.start_time >= block_slot.end_time:
                    return {"success": False, "error": "Block time start must be before end time"}
            
            # Save daily override
            result = self.availability_model.create_daily_override(override_data)
            
            if result["success"]:
                # Regenerate slots for this specific date
                self._regenerate_slots_for_date(override_data.doctor_email, override_data.override_date)
                logger.info(f"Daily override created and slots regenerated for {override_data.doctor_email} on {override_data.override_date}")
            
            return result
        except Exception as e:
            logger.error(f"Error creating daily override: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_daily_override(self, doctor_email: str, override_date: date) -> Optional[Dict]:
        """Get daily override for a specific date"""
        try:
            return self.availability_model.get_daily_override(doctor_email, override_date)
        except Exception as e:
            logger.error(f"Error getting daily override: {str(e)}")
            return None
    
    def get_day_view(self, doctor_email: str, view_date: date) -> Dict:
        """Get complete day view including weekly schedule, daily overrides, and existing appointments"""
        try:
            day_view = self.availability_model.get_day_view(doctor_email, view_date)
            
            # Add computed availability based on weekly schedule and overrides
            day_view["computed_availability"] = self._compute_day_availability(
                doctor_email, view_date, day_view.get("weekly_schedule"), day_view.get("daily_override")
            )
            
            return day_view
        except Exception as e:
            logger.error(f"Error getting day view: {str(e)}")
            return {}
    
    def delete_daily_override(self, doctor_email: str, override_date: date) -> bool:
        """Delete daily override and regenerate slots from weekly schedule"""
        try:
            # Delete daily override
            success = self.availability_model.delete_daily_override(doctor_email, override_date)
            
            if success:
                # Regenerate slots for this date based on weekly schedule
                self._regenerate_slots_for_date(doctor_email, override_date)
                logger.info(f"Daily override deleted and slots regenerated for {doctor_email} on {override_date}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting daily override: {str(e)}")
            return False
    
    def add_block_time(self, doctor_email: str, block_date: date, block_time: BlockTimeSlot, reason: str = None) -> Dict:
        """Add block time to a specific date"""
        try:
            # Get existing daily override or create new one
            daily_override = self.get_daily_override(doctor_email, block_date)
            
            if daily_override:
                # Add to existing override
                block_time_data = {
                    "start_time": block_time.start_time.isoformat(),
                    "end_time": block_time.end_time.isoformat(),
                    "reason": block_time.reason.value,
                    "description": reason or block_time.description,
                    "is_override": True
                }
                
                # Update existing override
                db.daily_overrides.update_one(
                    {
                        "doctor_email": doctor_email,
                        "override_date": block_date.isoformat()
                    },
                    {
                        "$push": {"block_time_slots": block_time_data},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            else:
                # Create new daily override with block time
                override_data = DailyOverride(
                    doctor_email=doctor_email,
                    override_date=block_date,
                    is_available=True,
                    block_time_slots=[block_time],
                    override_reason=reason or f"Block time: {block_time.reason.value}"
                )
                return self.create_daily_override(override_data)
            
            # Regenerate slots for this date
            self._regenerate_slots_for_date(doctor_email, block_date)
            
            logger.info(f"Block time added for {doctor_email} on {block_date}")
            return {"success": True, "message": "Block time added successfully"}
            
        except Exception as e:
            logger.error(f"Error adding block time: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_available_slots_with_overrides(self, doctor_email: str, start_date: date, end_date: date) -> List[Dict]:
        """Get available slots considering daily overrides"""
        try:
            # Get daily overrides for the date range
            overrides = self.availability_model.get_daily_overrides_range(doctor_email, start_date, end_date)
            
            # Get base available slots
            base_slots = self.get_available_slots(doctor_email, start_date, end_date)
            
            # Apply overrides to filter out blocked times
            filtered_slots = []
            for slot in base_slots:
                slot_date = datetime.strptime(slot["slot_date"], "%Y-%m-%d").date()
                slot_time = datetime.strptime(slot["slot_time"], "%H:%M:%S").time()
                
                # Check if this slot is blocked by any override
                is_blocked = False
                for override in overrides:
                    if override["override_date"] == slot_date.isoformat():
                        # Check block time slots
                        for block_slot in override.get("block_time_slots", []):
                            block_start = datetime.strptime(block_slot["start_time"], "%H:%M:%S").time()
                            block_end = datetime.strptime(block_slot["end_time"], "%H:%M:%S").time()
                            
                            if block_start <= slot_time < block_end:
                                is_blocked = True
                                break
                        
                        if is_blocked:
                            break
                
                if not is_blocked:
                    filtered_slots.append(slot)
            
            return filtered_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots with overrides: {str(e)}")
            return []
    
    def _compute_day_availability(self, doctor_email: str, view_date: date, weekly_schedule: Dict, daily_override: Dict) -> Dict:
        """Compute the actual availability for a specific day considering weekly schedule and overrides"""
        try:
            day_name = view_date.strftime('%A').lower()
            
            # Start with weekly schedule
            base_availability = {
                "is_available": False,
                "start_time": None,
                "end_time": None,
                "block_times": []
            }
            
            if weekly_schedule and weekly_schedule.get(day_name):
                day_schedule = weekly_schedule[day_name]
                if day_schedule.get("is_available", False):
                    base_availability.update({
                        "is_available": True,
                        "start_time": day_schedule.get("start_time"),
                        "end_time": day_schedule.get("end_time")
                    })
            
            # Apply daily override if exists
            if daily_override:
                if not daily_override.get("is_available", True):
                    base_availability["is_available"] = False
                    base_availability["start_time"] = None
                    base_availability["end_time"] = None
                else:
                    # Override times if provided
                    if daily_override.get("start_time"):
                        base_availability["start_time"] = daily_override["start_time"]
                    if daily_override.get("end_time"):
                        base_availability["end_time"] = daily_override["end_time"]
                
                # Add block times
                base_availability["block_times"] = daily_override.get("block_time_slots", [])
            
            return base_availability
            
        except Exception as e:
            logger.error(f"Error computing day availability: {str(e)}")
            return {"is_available": False, "start_time": None, "end_time": None, "block_times": []}
    
    def _regenerate_slots_for_date(self, doctor_email: str, slot_date: date):
        """Regenerate appointment slots for a specific date considering overrides"""
        try:
            # Delete existing slots for this date
            db.appointment_slots.delete_many({
                "doctor_email": doctor_email,
                "slot_date": slot_date.isoformat()
            })
            
            # Get day view to determine actual availability
            day_view = self.get_day_view(doctor_email, slot_date)
            computed_availability = day_view.get("computed_availability", {})
            
            if computed_availability.get("is_available", False):
                # Generate slots based on computed availability
                start_time_str = computed_availability.get("start_time")
                end_time_str = computed_availability.get("end_time")
                
                if start_time_str and end_time_str:
                    # Get weekly schedule for slot duration
                    weekly_schedule = day_view.get("weekly_schedule", {})
                    slot_duration = weekly_schedule.get("slot_duration_minutes", 30)
                    
                    # Generate slots
                    self._generate_slots_for_day_with_overrides(
                        doctor_email, slot_date, start_time_str, end_time_str, 
                        slot_duration, computed_availability.get("block_times", [])
                    )
                    
        except Exception as e:
            logger.error(f"Error regenerating slots for date: {str(e)}")
    
    def _generate_slots_for_day_with_overrides(self, doctor_email: str, slot_date: date, start_time_str: str, end_time_str: str, slot_duration: int, block_times: List[Dict]):
        """Generate slots for a day considering block times"""
        try:
            from datetime import datetime
            
            # Parse times
            try:
                start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
            except ValueError:
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
            
            try:
                end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
            except ValueError:
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Generate slots
            slots = []
            current_time = start_time
            
            while current_time < end_time:
                slot_start = current_time
                slot_end = self._add_minutes_to_time(current_time, slot_duration)
                
                if slot_end <= end_time:
                    # Check if this slot overlaps with any block time
                    is_blocked = False
                    for block_time in block_times:
                        block_start = datetime.strptime(block_time["start_time"], '%H:%M:%S').time()
                        block_end = datetime.strptime(block_time["end_time"], '%H:%M:%S').time()
                        
                        # Check for overlap
                        if (slot_start < block_end and slot_end > block_start):
                            is_blocked = True
                            break
                    
                    if not is_blocked:
                        slot = {
                            "doctor_email": doctor_email,
                            "slot_date": slot_date.isoformat(),
                            "slot_time": slot_start,
                            "is_available": True,
                            "appointment_id": None,
                            "created_at": datetime.utcnow()
                        }
                        slots.append(slot)
                
                current_time = slot_end
            
            # Save slots to database
            if slots:
                self.availability_model.create_appointment_slots(doctor_email, slot_date, slots)
                logger.info(f"Generated {len(slots)} slots for {doctor_email} on {slot_date} with block time considerations")
                
        except Exception as e:
            logger.error(f"Error generating slots for day with overrides: {str(e)}")
