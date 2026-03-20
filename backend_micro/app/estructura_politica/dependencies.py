"""
Dependencias reutilizables de FastAPI para inyectar en endpoints
"""
from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session, select
from typing import Optional
from .database import get_session
from .models import User, Tenant
from .auth import decode_jwt_token


async def get_current_tenant(request: Request) -> int:
    """
    Obtener tenant_id del request actual
    
    Args:
        request: Request de FastAPI
        
    Returns:
        ID del tenant
        
    Raises:
        HTTPException: Si no se puede identificar el tenant
    """
    if not hasattr(request.state, "tenant_id") or request.state.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el tenant. Verifique el subdominio o header X-Tenant-ID."
        )
    return request.state.tenant_id


async def get_current_tenant_obj(request: Request) -> Tenant:
    """
    Obtener objeto Tenant completo del request actual
    
    Args:
        request: Request de FastAPI
        
    Returns:
        Objeto Tenant
        
    Raises:
        HTTPException: Si no se puede identificar el tenant
    """
    if not hasattr(request.state, "tenant") or request.state.tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo identificar el tenant"
        )
    return request.state.tenant


async def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant)
) -> User:
    """
    Obtener usuario actual autenticado desde el token
    Soporta tanto JWT como tokens de desarrollo
    
    Args:
        request: Request de FastAPI
        session: Sesión de base de datos
        tenant_id: ID del tenant actual
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    # Extraer token del header Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Token requerido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    # Verificar si es un token de desarrollo
    if token.startswith("dev_token_"):
        # Formato: dev_token_{user_id}_{tenant_id}
        try:
            parts = token.split("_")
            user_id = int(parts[2])
            token_tenant_id = int(parts[3])
        except (IndexError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de desarrollo inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        # Decodificar token JWT (para producción)
        payload = decode_jwt_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("user_id")
        token_tenant_id = payload.get("tenant_id")
    
    # Verificar que el tenant del token coincida con el tenant actual
    if token_tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token no válido para este tenant"
        )
    
    # Buscar usuario en la base de datos
    user = session.exec(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )
    
    return user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verificar que el usuario actual sea Super Admin
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Usuario si es super admin
        
    Raises:
        HTTPException: Si el usuario no es super admin
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Requiere rol de Super Administrador."
        )
    return current_user


async def get_current_tenant_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verificar que el usuario actual sea Tenant Admin
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Usuario si es tenant admin
        
    Raises:
        HTTPException: Si el usuario no es tenant admin
    """
    if not current_user.is_tenant_admin and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Requiere rol de Administrador del Tenant."
        )
    return current_user


async def check_tenant_limits(
    tenant: Tenant = Depends(get_current_tenant_obj),
    session: Session = Depends(get_session)
) -> Tenant:
    """
    Verificar límites de suscripción del tenant
    
    Args:
        tenant: Tenant actual
        session: Sesión de base de datos
        
    Returns:
        Tenant si no ha excedido límites
        
    Raises:
        HTTPException: Si se han excedido los límites
    """
    from .models import User, Committee
    
    # Contar usuarios activos
    user_count = session.exec(
        select(User).where(
            User.tenant_id == tenant.id,
            User.is_active == True
        )
    ).all()
    
    if len(user_count) >= tenant.max_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite de usuarios alcanzado ({tenant.max_users}). Por favor, actualice su plan."
        )
    
    # Contar comités
    committee_count = session.exec(
        select(Committee).where(Committee.tenant_id == tenant.id)
    ).all()
    
    if len(committee_count) >= tenant.max_committees:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Límite de comités alcanzado ({tenant.max_committees}). Por favor, actualice su plan."
        )
    
    return tenant


def require_role(required_role: int):
    """
    Decorator para requerir un rol específico en una unidad administrativa
    
    Args:
        required_role: Rol mínimo requerido (UserRole enum)
        
    Returns:
        Función de dependencia
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
    ) -> User:
        # Super admin y tenant admin tienen acceso a todo
        if current_user.is_super_admin or current_user.is_tenant_admin:
            return current_user
        
        # Verificar asignaciones del usuario
        from .models import UserAssignment
        assignments = session.exec(
            select(UserAssignment).where(
                UserAssignment.user_id == current_user.id,
                UserAssignment.tenant_id == current_user.tenant_id
            )
        ).all()
        
        # Verificar si tiene el rol requerido en alguna unidad
        has_role = any(assignment.role <= required_role for assignment in assignments)
        
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Requiere rol de coordinador."
            )
        
        return current_user
    
    return role_checker
