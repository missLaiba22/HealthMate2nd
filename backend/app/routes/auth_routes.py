from fastapi import APIRouter, Depends
from app.models.user import UserCreate, UserLogin
from app.controllers.auth_controller import register_user, login_user
from app.utils.jwt import verify_token

router = APIRouter()

@router.post("/signup")
def signup(user: UserCreate):
    return register_user(user)

@router.post("/login")
def login(user: UserLogin):
    return login_user(user)

# ✅ Protected route demo
@router.get("/protected")
def protected_route(user_data: dict = Depends(verify_token)):
    return {
        "message": "You are authorized!",
        "user_info": user_data
    }
