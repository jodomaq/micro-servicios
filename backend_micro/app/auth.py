"""
Authentication utilities for Google OAuth 2.0
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, Header
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .database import get_db
from .models import User
from .schemas import UserCreate

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

_raw_secret = os.getenv("JWT_SECRET", "")
if not _raw_secret or len(_raw_secret) < 32 or _raw_secret == "your-secret-key-change-in-production":
    import sys, logging as _log
    _log.getLogger(__name__).critical(
        "JWT_SECRET no está configurado o es inseguro (mínimo 32 caracteres). "
        "El servidor no arrancará sin esta variable."
    )
    sys.exit(1)
JWT_SECRET: str = _raw_secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 30  # 30 días

def create_jwt_token(user_id: int, email: str) -> str:
    """Create a JWT token for authenticated user"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def verify_google_token(credential: str) -> dict:
    """Verify Google ID token and return user info"""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth no configurado")
    
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Check issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer')
        
        return {
            "google_id": idinfo['sub'],
            "email": idinfo['email'],
            "name": idinfo.get('name'),
            "picture": idinfo.get('picture')
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token de Google inválido: {str(e)}")

def get_or_create_user(db: Session, google_info: dict) -> User:
    """Get existing user or create new one from Google info"""
    # Try to find by google_id first
    user = db.query(User).filter(User.google_id == google_info["google_id"]).first()
    
    if not user:
        # Try to find by email
        user = db.query(User).filter(User.email == google_info["email"]).first()
        
        if user:
            # Update with Google ID
            user.google_id = google_info["google_id"]
            user.picture = google_info.get("picture")
            if google_info.get("name"):
                user.name = google_info["name"]
        else:
            # Create new user
            user = User(
                email=google_info["email"],
                name=google_info.get("name"),
                google_id=google_info["google_id"],
                picture=google_info.get("picture")
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
    
    return user

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token (optional)"""
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    token = authorization.split(" ")[1]
    payload = verify_jwt_token(token)
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return user

async def require_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """Require authenticated user (raises 401 if not authenticated)"""
    user = await get_current_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return user
