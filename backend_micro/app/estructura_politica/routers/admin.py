"""
Router para Panel de Super Administrador
Gestión global de tenants, usuarios y monitoreo
Solo accesible por SUPER_ADMIN
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from ..database import get_session
from ..dependencies import get_current_super_admin, get_current_user
from ..models import (
    Tenant, User, Committee, CommitteeMember, Event, Attendance,
    Survey, SurveyResponse, SubscriptionPlan, Payment, AuditLog
)
from ..schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantBasicResponse,
    UserResponse, SubscriptionPlanResponse, AuditLogResponse
)

router = APIRouter(prefix="/admin", tags=["Super Admin"])


# ====================================
# TENANT MANAGEMENT
# ====================================

@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 50,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Listar todos los tenants con estadísticas"""
    query = select(Tenant)
    
    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)
    
    if search:
        query = query.where(
            (Tenant.name.contains(search)) |
            (Tenant.subdomain.contains(search)) |
            (Tenant.contact_email.contains(search))
        )
    
    query = query.offset(skip).limit(limit)
    tenants = session.exec(query).all()
    return tenants


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Crear nuevo tenant"""
    # Verificar subdominio único
    existing = session.exec(
        select(Tenant).where(Tenant.subdomain == data.subdomain)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El subdominio ya está en uso"
        )
    
    # Verificar plan existe
    plan = session.get(SubscriptionPlan, data.subscription_plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de suscripción no encontrado"
        )
    
    tenant = Tenant(
        name=data.name,
        subdomain=data.subdomain,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        subscription_plan_id=data.subscription_plan_id,
        primary_color=data.primary_color,
        secondary_color=data.secondary_color,
        max_users=plan.max_users,
        max_committees=plan.max_committees,
        max_storage_mb=plan.max_storage_mb,
        subscription_status="trial",
        trial_ends_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Obtener detalle de un tenant con estadísticas"""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Actualizar tenant"""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    
    tenant.updated_at = datetime.utcnow()
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


@router.delete("/tenants/{tenant_id}")
async def deactivate_tenant(
    tenant_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Desactivar tenant (soft delete)"""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    tenant.is_active = False
    tenant.updated_at = datetime.utcnow()
    session.add(tenant)
    session.commit()
    return {"message": f"Tenant '{tenant.name}' desactivado"}


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Reactivar un tenant"""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    tenant.is_active = True
    tenant.updated_at = datetime.utcnow()
    session.add(tenant)
    session.commit()
    return {"message": f"Tenant '{tenant.name}' activado"}


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Estadísticas detalladas de un tenant"""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado"
        )
    
    user_count = session.exec(
        select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_active == True)
    ).one()
    
    committee_count = session.exec(
        select(func.count(Committee.id)).where(Committee.tenant_id == tenant_id)
    ).one()
    
    member_count = session.exec(
        select(func.count(CommitteeMember.id)).where(CommitteeMember.tenant_id == tenant_id)
    ).one()
    
    event_count = session.exec(
        select(func.count(Event.id)).where(Event.tenant_id == tenant_id)
    ).one()
    
    attendance_count = session.exec(
        select(func.count(Attendance.id)).where(Attendance.tenant_id == tenant_id)
    ).one()
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "users": user_count,
        "committees": committee_count,
        "members": member_count,
        "events": event_count,
        "attendances": attendance_count,
        "max_users": tenant.max_users,
        "max_committees": tenant.max_committees,
        "subscription_status": tenant.subscription_status,
        "subscription_plan": tenant.subscription_plan.name if tenant.subscription_plan else None
    }


# ====================================
# GLOBAL STATS
# ====================================

@router.get("/stats")
async def get_global_stats(
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Métricas globales del sistema"""
    total_tenants = session.exec(select(func.count(Tenant.id))).one()
    active_tenants = session.exec(
        select(func.count(Tenant.id)).where(Tenant.is_active == True)
    ).one()
    total_users = session.exec(select(func.count(User.id))).one()
    total_committees = session.exec(select(func.count(Committee.id))).one()
    total_members = session.exec(select(func.count(CommitteeMember.id))).one()
    total_events = session.exec(select(func.count(Event.id))).one()
    total_attendances = session.exec(select(func.count(Attendance.id))).one()
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_users": total_users,
        "total_committees": total_committees,
        "total_members": total_members,
        "total_events": total_events,
        "total_attendances": total_attendances
    }


# ====================================
# ALL USERS (GLOBAL)
# ====================================

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    tenant_id: Optional[int] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Listar usuarios de todos los tenants"""
    query = select(User)
    
    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)
    
    if search:
        query = query.where(
            (User.name.contains(search)) |
            (User.email.contains(search))
        )
    
    query = query.offset(skip).limit(limit)
    return session.exec(query).all()


# ====================================
# AUDIT LOGS
# ====================================

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = None,
    action: Optional[str] = None,
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Ver logs de auditoría"""
    query = select(AuditLog)
    
    if tenant_id:
        query = query.where(AuditLog.tenant_id == tenant_id)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    return session.exec(query).all()


# ====================================
# SUBSCRIPTION PLANS
# ====================================

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Listar planes de suscripción"""
    return session.exec(select(SubscriptionPlan)).all()


@router.put("/tenants/{tenant_id}/plan")
async def update_tenant_plan(
    tenant_id: int,
    plan_id: int = Query(...),
    session: Session = Depends(get_session),
    admin: User = Depends(get_current_super_admin)
):
    """Cambiar plan de suscripción de un tenant"""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    plan = session.get(SubscriptionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    tenant.subscription_plan_id = plan_id
    tenant.max_users = plan.max_users
    tenant.max_committees = plan.max_committees
    tenant.max_storage_mb = plan.max_storage_mb
    tenant.updated_at = datetime.utcnow()
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return {"message": f"Plan actualizado a '{plan.name}'", "tenant": tenant}
