from typing import Dict, Optional
from datetime import timedelta
import logging
from ..models.user import UserModel, UserCreate, UserLogin
from ..utils.auth import hash_password, verify_password
from ..utils.jwt import create_access_token

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service handling user registration and login"""
    
    @staticmethod
    def register_user(user_data: UserCreate) -> Dict:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = UserModel.find_user_by_email(user_data.email)
            if existing_user:
                raise ValueError("Email already exists")
            
            # Hash password
            hashed_password = hash_password(user_data.password)
            
            # Create user with hashed password
            user_create_data = UserCreate(
                email=user_data.email,
                password=hashed_password,
                role=user_data.role
            )
            
            result = UserModel.create_user(user_create_data)
            return {"message": "User registered successfully", "user_id": result["id"]}
            
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise

    @staticmethod
    def login_user(login_data: UserLogin) -> Dict:
        """Authenticate user and return JWT token"""
        try:
            # Find user in database
            user = UserModel.find_user_by_email(login_data.email)
            if not user:
                raise ValueError("Invalid credentials")
            
            # Verify password
            if not verify_password(login_data.password, user["password"]):
                raise ValueError("Invalid credentials")
            
            # Create JWT token
            role = user.get("role", "user")
            token = create_access_token(
                data={
                    "sub": user["email"],
                    "email": user["email"],
                    "role": role
                },
                expires_delta=timedelta(minutes=60)
            )
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "role": role,
                "email": user["email"]
            }
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            raise
