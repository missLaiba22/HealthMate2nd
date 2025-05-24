from fastapi import APIRouter, Depends
from app.utils.jwt import get_current_user
from app.database import db

router = APIRouter(tags=["Profile"])

@router.get("/")
def get_profile(current_user=Depends(get_current_user)):
    print("[DEBUG] current_user:", current_user)
    email = current_user.get("email") or current_user.get("sub")
    user = db.users.find_one({"email": email}, {"_id": 0, "password": 0})
    return user

@router.put("/")
def update_profile(profile: dict, current_user=Depends(get_current_user)):
    print("[DEBUG] current_user:", current_user)
    email = current_user.get("email") or current_user.get("sub")
    db.users.update_one({"email": email}, {"$set": profile})
    return {"message": "Profile updated"} 