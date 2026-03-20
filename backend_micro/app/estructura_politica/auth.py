"""
Sistema de autenticación con OAuth2 (Google y Microsoft) y JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
from .config import settings
from .models import User
from sqlmodel import Session, select


def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear token JWT
    
    Args:
        data: Datos a encode en el token
        expires_delta: Tiempo de expiración
        
    Returns:
        Token JWT string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_jwt_token(token: str) -> Optional[Dict]:
    """
    Decodificar y validar token JWT
    
    Args:
        token: Token JWT
        
    Returns:
        Payload del token o None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_google_token(token: str) -> Optional[Dict]:
    """
    Verificar token de Google OAuth
    
    Args:
        token: Token de Google
        
    Returns:
        Información del usuario de Google o None si es inválido
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # Verificar el issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
        
        return {
            'provider': 'google',
            'provider_user_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', '')
        }
    except Exception as e:
        print(f"Error verificando token de Google: {e}")
        return None


def verify_microsoft_token(token: str) -> Optional[Dict]:
    """
    Verificar token de Microsoft/Azure AD OAuth
    
    Args:
        token: Access token de Microsoft
        
    Returns:
        Información del usuario de Microsoft o None si es inválido
    """
    try:
        # Obtener información del usuario desde Microsoft Graph API
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers=headers
        )
        
        if response.status_code != 200:
            return None
        
        user_info = response.json()
        
        return {
            'provider': 'microsoft',
            'provider_user_id': user_info['id'],
            'email': user_info.get('mail') or user_info.get('userPrincipalName'),
            'name': user_info.get('displayName', ''),
            'picture': ''  # Microsoft Graph requiere llamada separada para foto
        }
    except Exception as e:
        print(f"Error verificando token de Microsoft: {e}")
        return None


def get_or_create_user(
    session: Session,
    tenant_id: int,
    provider_info: Dict,
    ip_address: str = None,
    user_agent: str = None
) -> User:
    """
    Obtener o crear usuario desde información de OAuth provider
    
    Args:
        session: Sesión de base de datos
        tenant_id: ID del tenant
        provider_info: Información del provider (Google/Microsoft)
        ip_address: IP del usuario (para consent)
        user_agent: User agent (para consent)
        
    Returns:
        Usuario (existente o nuevo)
    """
    provider = provider_info['provider']
    email = provider_info['email']
    
    # Buscar usuario existente por email en el tenant
    user = session.exec(
        select(User).where(
            User.tenant_id == tenant_id,
            User.email == email
        )
    ).first()
    
    if user:
        # Actualizar último login
        user.last_login_at = datetime.utcnow()
        
        # Actualizar provider ID si no existe
        if provider == 'google' and not user.google_id:
            user.google_id = provider_info['provider_user_id']
        elif provider == 'microsoft' and not user.microsoft_id:
            user.microsoft_id = provider_info['provider_user_id']
        
        # Actualizar foto si cambió
        if provider_info.get('picture'):
            user.picture_url = provider_info['picture']
        
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        # Crear nuevo usuario
        user = User(
            tenant_id=tenant_id,
            email=email,
            name=provider_info['name'],
            picture_url=provider_info.get('picture'),
            google_id=provider_info['provider_user_id'] if provider == 'google' else None,
            microsoft_id=provider_info['provider_user_id'] if provider == 'microsoft' else None,
            is_active=True,
            last_login_at=datetime.utcnow()
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Registrar consentimiento inicial
        from .models import UserConsent
        consent = UserConsent(
            user_id=user.id,
            tenant_id=tenant_id,
            consent_type='privacy_policy',
            consent_given=True,
            consent_text='Política de Privacidad v1.0',
            consent_version='v1.0',
            ip_address=ip_address,
            user_agent=user_agent,
            consented_at=datetime.utcnow()
        )
        session.add(consent)
        session.commit()
    
    # Registrar en audit log
    from .models import AuditLog
    audit = AuditLog(
        user_id=user.id,
        tenant_id=tenant_id,
        action='login',
        resource_type='User',
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow()
    )
    session.add(audit)
    session.commit()
    
    return user


def create_user_jwt(user: User) -> str:
    """
    Crear JWT para un usuario
    
    Args:
        user: Usuario
        
    Returns:
        Token JWT
    """
    token_data = {
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "is_super_admin": user.is_super_admin,
        "is_tenant_admin": user.is_tenant_admin
    }
    
    return create_jwt_token(token_data)
