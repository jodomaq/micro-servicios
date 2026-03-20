"""
Servicio de autenticación: hashing de contraseñas, JWT y verificación de Google OAuth.
"""

from datetime import datetime, timedelta, timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.mesa_regalos.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hashea una contraseña con bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica que una contraseña coincida con su hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Genera un JWT con los datos proporcionados."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decodifica y valida un JWT. Devuelve None si es inválido."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def verify_google_token(credential: str) -> dict | None:
    """
    Verifica un ID token de Google y devuelve la info del usuario.

    Returns:
        Diccionario con email, name, picture si es válido; None si no.
    """
    try:
        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        if id_info.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            return None

        return {
            "email": id_info["email"],
            "name": id_info.get("name", ""),
            "picture": id_info.get("picture", ""),
        }
    except ValueError:
        return None
