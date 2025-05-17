from pydantic import BaseModel, EmailStr
from typing import Optional

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
