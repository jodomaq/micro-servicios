"""
Router de autenticación: registro, login y Google OAuth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.mesa_regalos.core.database import get_db
from app.mesa_regalos.models.models import User
from app.mesa_regalos.services.auth_service import (
    create_access_token,
    hash_password,
    verify_google_token,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


# ─── Esquemas ────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "is_premium": user.is_premium,
    }


# ─── Endpoints ───────────────────────────────────────────────


@router.post("/registro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario con email y contraseña."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con este correo electrónico.",
        )

    user = User(
        email=body.email,
        name=body.name or body.email.split("@")[0],
        password_hash=hash_password(body.password),
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return AuthResponse(access_token=token, user=_user_to_dict(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión con email y contraseña."""
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return AuthResponse(access_token=token, user=_user_to_dict(user))


@router.post("/google", response_model=AuthResponse)
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión o registrarse con Google."""
    google_info = verify_google_token(body.credential)
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de Google no es válido.",
        )

    email = google_info["email"]
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Registro automático con Google
        user = User(
            email=email,
            name=google_info.get("name", ""),
            avatar_url=google_info.get("picture", ""),
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return AuthResponse(access_token=token, user=_user_to_dict(user))
