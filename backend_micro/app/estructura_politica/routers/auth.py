"""
Router de autenticación (OAuth deshabilitado para desarrollo)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select
from typing import Optional
from pydantic import BaseModel

from ..database import get_session
from ..dependencies import get_current_tenant, get_current_user
# OAuth comentado para desarrollo
# from ..auth import (
#     verify_google_token,
#     verify_microsoft_token,
#     get_or_create_user,
#     create_user_jwt
# )
from ..models import User, Tenant
from ..schemas import (
    # GoogleAuthRequest,
    # MicrosoftAuthRequest,
    AuthResponse,
    UserResponse,
    TenantBasicResponse
)


# Schema simple para login de desarrollo
class DevLoginRequest(BaseModel):
    email: str
    tenant_id: int = 1


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ====================================
# DESARROLLO: Login simple sin OAuth
# ====================================

@router.post("/dev-login", response_model=AuthResponse)
async def dev_login(
    login_data: DevLoginRequest,
    session: Session = Depends(get_session)
):
    """
    Login de desarrollo (sin OAuth)
    Busca un usuario por email en el tenant especificado
    """
    # Buscar usuario
    statement = select(User).where(
        User.email == login_data.email,
        User.tenant_id == login_data.tenant_id
    )
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario {login_data.email} no encontrado en el tenant {login_data.tenant_id}"
        )
    
    # Obtener tenant
    tenant = session.get(Tenant, login_data.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    # Crear un token simple (solo para desarrollo)
    # En producción esto debería ser un JWT real
    access_token = f"dev_token_{user.id}_{user.tenant_id}"
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user.model_dump()),
        tenant=TenantBasicResponse(**tenant.model_dump())
    )


# ====================================
# OAuth endpoints (COMENTADOS)
# ====================================

# @router.post("/google", response_model=AuthResponse)
# async def google_login(
#     auth_data: GoogleAuthRequest,
#     request: Request,
#     session: Session = Depends(get_session),
#     tenant_id: int = Depends(get_current_tenant)
# ):
#     """
#     Autenticación con Google OAuth
#     """
#     provider_info = verify_google_token(auth_data.token)
#     
#     if not provider_info:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token de Google inválido"
#         )
#     
#     ip_address = request.client.host if request.client else None
#     user_agent = request.headers.get("user-agent")
#     
#     user = get_or_create_user(
#         session=session,
#         tenant_id=tenant_id,
#         provider_info=provider_info,
#         ip_address=ip_address,
#         user_agent=user_agent
#     )
#     
#     tenant = session.get(Tenant, tenant_id)
#     access_token = create_user_jwt(user)
#     
#     return AuthResponse(
#         access_token=access_token,
#         token_type="bearer",
#         user=UserResponse(**user.model_dump()),
#         tenant=TenantBasicResponse(**tenant.model_dump())
#     )


# @router.post("/microsoft", response_model=AuthResponse)
# async def microsoft_login(
#     auth_data: MicrosoftAuthRequest,
#     request: Request,
#     session: Session = Depends(get_session),
#     tenant_id: int = Depends(get_current_tenant)
# ):
#     """
#     Autenticación con Microsoft/Azure AD OAuth
#     """
#     provider_info = verify_microsoft_token(auth_data.access_token)
#     
#     if not provider_info:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token de Microsoft inválido"
#         )
#     
#     ip_address = request.client.host if request.client else None
#     user_agent = request.headers.get("user-agent")
#     
#     user = get_or_create_user(
#         session=session,
#         tenant_id=tenant_id,
#         provider_info=provider_info,
#         ip_address=ip_address,
#         user_agent=user_agent
#     )
#     
#     tenant = session.get(Tenant, tenant_id)
#     access_token = create_user_jwt(user)
#     
#     return AuthResponse(
#         access_token=access_token,
#         token_type="bearer",
#         user=UserResponse(**user.model_dump()),
#         tenant=TenantBasicResponse(**tenant.model_dump())
#     )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información del usuario actual autenticado
    """
    return UserResponse(**current_user.model_dump())


@router.get("/tenant", response_model=TenantBasicResponse)
async def get_current_tenant_info(
    request: Request,
    tenant_id: int = Depends(get_current_tenant),
    session: Session = Depends(get_session)
):
    """
    Obtener información del tenant actual
    """
    tenant = session.get(Tenant, tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    return TenantBasicResponse(**tenant.model_dump())


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout del usuario
    
    Nota: Como usamos JWT stateless, el logout es del lado del cliente
    (eliminar el token). Este endpoint es principalmente para registro de auditoría.
    """
    # Aquí podrías agregar el token a una blacklist si lo deseas
    # O simplemente registrar el logout en audit log
    
    from ..models import AuditLog
    from datetime import datetime
    from ..database import get_session
    
    return {
        "message": "Logout exitoso. Elimine el token del cliente.",
        "user_id": current_user.id
    }
