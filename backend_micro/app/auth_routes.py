"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .auth import verify_google_token, get_or_create_user, create_jwt_token, require_user
from .schemas import GoogleAuthRequest, AuthResponse, UserResponse
from .models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with Google ID token
    """
    # Verify Google token
    google_info = await verify_google_token(request.credential)
    
    # Get or create user
    user = get_or_create_user(db, google_info)
    
    # Create JWT token
    token = create_jwt_token(user.id, user.email)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(require_user)):
    """
    Get current authenticated user info
    """
    return user

@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should delete token)
    """
    return {"message": "Logged out successfully"}
