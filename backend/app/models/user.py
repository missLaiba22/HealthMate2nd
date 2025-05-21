from pydantic import BaseModel, EmailStr
from typing import Optional, List

# Generic user registration (used for auth)
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # "doctor" or "patient"

# Login model
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Specific to patient registration
class PatientRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: int
    gender: str  # e.g., "male", "female", "other"

# Specific to doctor registration
class DoctorRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str
    specialization: str
    experience_years: int

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    date_of_birth: str
    gender: str
    contact_number: str
    role: str  # 'patient' or 'doctor'
    share_health_data: Optional[bool] = False
    receive_notifications: Optional[bool] = False

class PatientProfile(UserBase):
    medical_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    emergency_contact: Optional[str] = None

class DoctorProfile(UserBase):
    medical_license_number: Optional[str] = None
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
