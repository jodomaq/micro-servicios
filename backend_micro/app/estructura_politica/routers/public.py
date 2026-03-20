"""
Router para endpoints públicos (sin autenticación JWT)
Registro de tenants, verificación de subdominios, info de planes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta

from ..database import get_session
from ..models import Tenant, User, SubscriptionPlan
from ..schemas import (
    TenantRegistrationSchema,
    TenantRegistrationResponse,
    SubscriptionPlanResponse
)

router = APIRouter(prefix="/public", tags=["Public"])


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_available_plans(
    session: Session = Depends(get_session)
):
    """Obtener planes de suscripción disponibles (público)"""
    plans = session.exec(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
    ).all()
    return plans


@router.get("/check-subdomain/{subdomain}")
async def check_subdomain_availability(
    subdomain: str,
    session: Session = Depends(get_session)
):
    """Verificar disponibilidad de subdominio"""
    import re
    if not re.match(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$', subdomain):
        return {
            "available": False,
            "message": "Formato inválido. Use 3-30 caracteres: letras minúsculas, números y guiones"
        }
    
    existing = session.exec(
        select(Tenant).where(Tenant.subdomain == subdomain)
    ).first()
    
    return {
        "available": existing is None,
        "subdomain": subdomain,
        "message": "Disponible" if not existing else "No disponible"
    }


@router.post("/register-tenant", response_model=TenantRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    data: TenantRegistrationSchema,
    session: Session = Depends(get_session)
):
    """
    Registrar nuevo tenant en modo trial (7 días de prueba).
    Crea el tenant, el usuario admin y la estructura básica.
    """
    # Verificar subdominio único
    existing = session.exec(
        select(Tenant).where(Tenant.subdomain == data.subdomain)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El subdominio ya está en uso"
        )
    
    # Verificar email único (no otro tenant con mismo admin email)
    existing_email = session.exec(
        select(Tenant).where(Tenant.contact_email == data.contact_email)
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una organización con este email de contacto"
        )
    
    # Obtener plan
    plan = session.get(SubscriptionPlan, data.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de suscripción no encontrado")
    
    # Crear tenant en modo trial
    tenant = Tenant(
        name=data.organization_name,
        subdomain=data.subdomain,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        subscription_plan_id=data.plan_id,
        primary_color=data.primary_color,
        secondary_color=data.secondary_color,
        max_users=plan.max_users,
        max_committees=plan.max_committees,
        max_storage_mb=plan.max_storage_mb,
        subscription_status="trial",
        is_active=True,
        trial_ends_at=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow()
    )
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    # Crear usuario admin del tenant
    admin_user = User(
        tenant_id=tenant.id,
        email=data.contact_email,
        name=data.admin_name,
        phone=data.contact_phone,
        is_tenant_admin=True,
        is_super_admin=False,
        is_active=True,
        created_at=datetime.utcnow()
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    
    return TenantRegistrationResponse(
        tenant_id=tenant.id,
        subdomain=tenant.subdomain,
        admin_email=admin_user.email,
        message=f"Organización '{tenant.name}' creada exitosamente. Tiene 7 días de prueba gratuita."
    )


@router.get("/tenant/by-subdomain/{subdomain}")
async def get_tenant_by_subdomain(
    subdomain: str,
    session: Session = Depends(get_session)
):
    """Obtener información pública de un tenant por subdominio"""
    tenant = session.exec(
        select(Tenant).where(Tenant.subdomain == subdomain, Tenant.is_active == True)
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "subdomain": tenant.subdomain,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "secondary_color": tenant.secondary_color
    }
