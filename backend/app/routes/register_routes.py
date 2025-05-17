from fastapi import APIRouter
from app.models.user import PatientRegistration, DoctorRegistration
from app.controllers.register_controller import (
    register_patient_controller,
    register_doctor_controller
)

router = APIRouter()

@router.post("/patient")
def register_patient(data: PatientRegistration):
    return register_patient_controller(data)

@router.post("/doctor")
def register_doctor(data: DoctorRegistration):
    return register_doctor_controller(data)
