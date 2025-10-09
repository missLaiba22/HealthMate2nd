from fastapi import APIRouter, HTTPException, Depends
from ..models.user import UserCreate, UserLogin
from ..services.auth_service import AuthService
from ..utils.jwt import verify_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

@router.post("/signup")
async def signup(user: UserCreate):
    """Register a new user"""
    try:
        return AuthService.register_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
async def login(user: UserLogin):
    """Login user and return JWT token"""
    try:
        return AuthService.login_user(user)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/protected")
async def protected_route(user_data: dict = Depends(verify_token)):
    """Protected route for testing authentication"""
    return {
        "message": "You are authorized!",
        "user_info": user_data
    }