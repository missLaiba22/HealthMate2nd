from fastapi import APIRouter, Depends, HTTPException
from ..models.user import UserModel
from ..utils.jwt import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Profile"])

@router.get("")
@router.get("/")
async def get_profile(current_user=Depends(get_current_user)):
    """Get user profile"""
    try:
        email = current_user.get("email") or current_user.get("sub")
        user = UserModel.get_user_profile(email)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("")
@router.put("/")
async def update_profile(profile: dict, current_user=Depends(get_current_user)):
    """Update user profile"""
    try:
        email = current_user.get("email") or current_user.get("sub")
        
        # Remove sensitive fields that shouldn't be updated through this endpoint
        profile.pop("password", None)
        profile.pop("email", None)  # Email shouldn't be changed
        profile.pop("role", None)   # Role shouldn't be changed
        
        success = UserModel.update_user(email, profile)
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")