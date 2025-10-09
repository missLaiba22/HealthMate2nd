from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import asyncio
from ..models.appointment import AppointmentReminder, AppointmentResponse, AppointmentStatus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@healthmate.com")
        self.app_name = "HealthMate"
        
        # In-memory storage for sent reminders (replace with database in production)
        self.sent_reminders: Dict[str, AppointmentReminder] = {}

    async def send_appointment_confirmation(self, appointment: AppointmentResponse) -> bool:
        """
        Send appointment confirmation email to patient.
        """
        try:
            subject = f"Appointment Confirmed - {self.app_name}"
            message = self._create_confirmation_message(appointment)
            
            success = await self._send_email(
                to_email=appointment.patient_email,
                subject=subject,
                message=message
            )
            
            if success:
                # Record the sent reminder
                reminder = AppointmentReminder(
                    appointment_id=appointment.id,
                    patient_email=appointment.patient_email,
                    doctor_email=appointment.doctor_email,
                    appointment_date=appointment.appointment_date,
                    appointment_time=appointment.appointment_time,
                    reminder_type="confirmation",
                    message=message,
                    sent_at=datetime.now()
                )
                self.sent_reminders[f"{appointment.id}_confirmation"] = reminder
                
                logger.info(f"Appointment confirmation sent to {appointment.patient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {str(e)}")
            return False

    async def send_appointment_reminder_24h(self, appointment: AppointmentResponse) -> bool:
        """
        Send 24-hour appointment reminder.
        """
        try:
            subject = f"Appointment Reminder - Tomorrow - {self.app_name}"
            message = self._create_24h_reminder_message(appointment)
            
            success = await self._send_email(
                to_email=appointment.patient_email,
                subject=subject,
                message=message
            )
            
            if success:
                # Record the sent reminder
                reminder = AppointmentReminder(
                    appointment_id=appointment.id,
                    patient_email=appointment.patient_email,
                    doctor_email=appointment.doctor_email,
                    appointment_date=appointment.appointment_date,
                    appointment_time=appointment.appointment_time,
                    reminder_type="reminder_24h",
                    message=message,
                    sent_at=datetime.now()
                )
                self.sent_reminders[f"{appointment.id}_24h"] = reminder
                
                logger.info(f"24h appointment reminder sent to {appointment.patient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending 24h appointment reminder: {str(e)}")
            return False

    async def send_appointment_reminder_1h(self, appointment: AppointmentResponse) -> bool:
        """
        Send 1-hour appointment reminder.
        """
        try:
            subject = f"Appointment Starting Soon - {self.app_name}"
            message = self._create_1h_reminder_message(appointment)
            
            success = await self._send_email(
                to_email=appointment.patient_email,
                subject=subject,
                message=message
            )
            
            if success:
                # Record the sent reminder
                reminder = AppointmentReminder(
                    appointment_id=appointment.id,
                    patient_email=appointment.patient_email,
                    doctor_email=appointment.doctor_email,
                    appointment_date=appointment.appointment_date,
                    appointment_time=appointment.appointment_time,
                    reminder_type="reminder_1h",
                    message=message,
                    sent_at=datetime.now()
                )
                self.sent_reminders[f"{appointment.id}_1h"] = reminder
                
                logger.info(f"1h appointment reminder sent to {appointment.patient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending 1h appointment reminder: {str(e)}")
            return False

    async def send_appointment_cancellation(self, appointment: AppointmentResponse) -> bool:
        """
        Send appointment cancellation notification.
        """
        try:
            subject = f"Appointment Cancelled - {self.app_name}"
            message = self._create_cancellation_message(appointment)
            
            success = await self._send_email(
                to_email=appointment.patient_email,
                subject=subject,
                message=message
            )
            
            if success:
                logger.info(f"Appointment cancellation sent to {appointment.patient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending appointment cancellation: {str(e)}")
            return False

    async def send_medication_reminder(self, patient_email: str, medications: List[str], 
                                     appointment: AppointmentResponse) -> bool:
        """
        Send medication reminder based on appointment and prescribed medications.
        """
        try:
            subject = f"Medication Reminder - {self.app_name}"
            message = self._create_medication_reminder_message(medications, appointment)
            
            success = await self._send_email(
                to_email=patient_email,
                subject=subject,
                message=message
            )
            
            if success:
                logger.info(f"Medication reminder sent to {patient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending medication reminder: {str(e)}")
            return False

    async def schedule_appointment_reminders(self, appointment: AppointmentResponse):
        """
        Schedule all necessary reminders for an appointment.
        """
        try:
            # Schedule 24-hour reminder
            appointment_datetime = datetime.combine(appointment.appointment_date, appointment.appointment_time)
            reminder_24h_time = appointment_datetime - timedelta(hours=24)
            
            # Schedule 1-hour reminder
            reminder_1h_time = appointment_datetime - timedelta(hours=1)
            
            # Schedule the reminders (in production, use a task queue like Celery)
            if reminder_24h_time > datetime.now():
                await self._schedule_reminder(reminder_24h_time, self.send_appointment_reminder_24h, appointment)
            
            if reminder_1h_time > datetime.now():
                await self._schedule_reminder(reminder_1h_time, self.send_appointment_reminder_1h, appointment)
            
            logger.info(f"Appointment reminders scheduled for {appointment.id}")
            
        except Exception as e:
            logger.error(f"Error scheduling appointment reminders: {str(e)}")

    async def _schedule_reminder(self, reminder_time: datetime, reminder_func, appointment: AppointmentResponse):
        """
        Schedule a reminder to be sent at a specific time.
        In production, this would use a proper task scheduler.
        """
        try:
            delay = (reminder_time - datetime.now()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
                await reminder_func(appointment)
        except Exception as e:
            logger.error(f"Error in scheduled reminder: {str(e)}")

    async def _send_email(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send email using SMTP.
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured. Email not sent.")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(message, 'html'))
            
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def _create_confirmation_message(self, appointment: AppointmentResponse) -> str:
        """Create HTML confirmation message."""
        return f"""
        <html>
        <body>
            <h2>Appointment Confirmed</h2>
            <p>Dear Patient,</p>
            <p>Your appointment has been confirmed with the following details:</p>
            <ul>
                <li><strong>Date:</strong> {appointment.appointment_date}</li>
                <li><strong>Time:</strong> {appointment.appointment_time}</li>
                <li><strong>Duration:</strong> {appointment.duration_minutes} minutes</li>
                <li><strong>Type:</strong> {appointment.appointment_type}</li>
                <li><strong>Urgency:</strong> {appointment.urgency_level}</li>
            </ul>
            <p>Please arrive 10 minutes before your scheduled time.</p>
            <p>If you need to reschedule or cancel, please contact us as soon as possible.</p>
            <p>Best regards,<br>{self.app_name} Team</p>
        </body>
        </html>
        """

    def _create_24h_reminder_message(self, appointment: AppointmentResponse) -> str:
        """Create HTML 24-hour reminder message."""
        return f"""
        <html>
        <body>
            <h2>Appointment Reminder - Tomorrow</h2>
            <p>Dear Patient,</p>
            <p>This is a reminder that you have an appointment tomorrow:</p>
            <ul>
                <li><strong>Date:</strong> {appointment.appointment_date}</li>
                <li><strong>Time:</strong> {appointment.appointment_time}</li>
                <li><strong>Duration:</strong> {appointment.duration_minutes} minutes</li>
            </ul>
            <p>Please prepare any relevant medical documents or questions you may have.</p>
            <p>If you need to reschedule, please contact us immediately.</p>
            <p>Best regards,<br>{self.app_name} Team</p>
        </body>
        </html>
        """

    def _create_1h_reminder_message(self, appointment: AppointmentResponse) -> str:
        """Create HTML 1-hour reminder message."""
        return f"""
        <html>
        <body>
            <h2>Appointment Starting Soon</h2>
            <p>Dear Patient,</p>
            <p>Your appointment is scheduled to start in 1 hour:</p>
            <ul>
                <li><strong>Time:</strong> {appointment.appointment_time}</li>
                <li><strong>Duration:</strong> {appointment.duration_minutes} minutes</li>
            </ul>
            <p>Please ensure you are ready and have all necessary documents.</p>
            <p>Best regards,<br>{self.app_name} Team</p>
        </body>
        </html>
        """

    def _create_cancellation_message(self, appointment: AppointmentResponse) -> str:
        """Create HTML cancellation message."""
        return f"""
        <html>
        <body>
            <h2>Appointment Cancelled</h2>
            <p>Dear Patient,</p>
            <p>Your appointment has been cancelled:</p>
            <ul>
                <li><strong>Date:</strong> {appointment.appointment_date}</li>
                <li><strong>Time:</strong> {appointment.appointment_time}</li>
            </ul>
            <p>If you need to reschedule, please contact us to book a new appointment.</p>
            <p>Best regards,<br>{self.app_name} Team</p>
        </body>
        </html>
        """

    def _create_medication_reminder_message(self, medications: List[str], appointment: AppointmentResponse) -> str:
        """Create HTML medication reminder message."""
        medication_list = "\n".join([f"<li>{med}</li>" for med in medications])
        
        return f"""
        <html>
        <body>
            <h2>Medication Reminder</h2>
            <p>Dear Patient,</p>
            <p>Please remember to take your prescribed medications:</p>
            <ul>
                {medication_list}
            </ul>
            <p>Your next appointment is scheduled for {appointment.appointment_date} at {appointment.appointment_time}.</p>
            <p>If you have any questions about your medications, please contact your doctor.</p>
            <p>Best regards,<br>{self.app_name} Team</p>
        </body>
        </html>
        """

    async def get_sent_reminders(self, appointment_id: str) -> List[AppointmentReminder]:
        """Get all sent reminders for an appointment."""
        reminders = []
        for key, reminder in self.sent_reminders.items():
            if reminder.appointment_id == appointment_id:
                reminders.append(reminder)
        return reminders

    async def send_bulk_reminders(self, appointments: List[AppointmentResponse], reminder_type: str):
        """
        Send bulk reminders for multiple appointments.
        """
        try:
            success_count = 0
            for appointment in appointments:
                if reminder_type == "confirmation":
                    success = await self.send_appointment_confirmation(appointment)
                elif reminder_type == "24h":
                    success = await self.send_appointment_reminder_24h(appointment)
                elif reminder_type == "1h":
                    success = await self.send_appointment_reminder_1h(appointment)
                else:
                    continue
                
                if success:
                    success_count += 1
            
            logger.info(f"Bulk reminders sent: {success_count}/{len(appointments)}")
            return success_count
            
        except Exception as e:
            logger.error(f"Error sending bulk reminders: {str(e)}")
            return 0


