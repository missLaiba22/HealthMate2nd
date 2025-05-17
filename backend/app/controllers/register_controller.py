from fastapi import HTTPException
from app.database import db
from app.utils.auth import hash_password
from app.models.user import PatientRegistration, DoctorRegistration

def register_patient_controller(data: PatientRegistration):
    if db.patients.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Patient already exists")

    db.patients.insert_one({
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "age": data.age,
        "gender": data.gender
    })

    return {"message": "Patient registered successfully"}

def register_doctor_controller(data: DoctorRegistration):
    if db.doctors.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Doctor already exists")

    db.doctors.insert_one({
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "specialization": data.specialization,
        "experience_years": data.experience_years
    })

    return {"message": "Doctor registered successfully"}
