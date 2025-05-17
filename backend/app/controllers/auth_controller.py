from app.database import db
from app.models.user import UserCreate
 # Adjusted import path; ensure models/user.py exists and defines UserCreate
from app.utils.auth import hash_password, verify_password
from fastapi import HTTPException
from app.utils.jwt import create_access_token
from datetime import timedelta

def register_user(user: UserCreate):
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    db.users.insert_one({
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role
    })
    return {"message": "User registered"}


def login_user(user):
    db_user = db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    role = db_user.get("role", "user")  # default to 'user' if not set
    
    token = create_access_token(
        data={
            "sub": db_user["email"],
            "role": role
        },
        expires_delta=timedelta(minutes=60)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role  # ✅ Add this line so frontend can read it
    }


