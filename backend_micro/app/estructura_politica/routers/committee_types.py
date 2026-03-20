"""
Router para gestión de tipos de comité configurables por tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from ..database import get_session
from ..dependencies import (
    get_current_tenant,
    get_current_user,
    get_current_tenant_admin
)
from ..models import CommitteeType, User, Committee
from ..schemas import CommitteeTypeCreate, CommitteeTypeResponse


router = APIRouter(prefix="/committee-types", tags=["Committee Types"])


@router.get("/", response_model=List[CommitteeTypeResponse])
async def list_committee_types(
    include_inactive: bool = False,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Listar tipos de comité del tenant
    """
    query = select(CommitteeType).where(CommitteeType.tenant_id == tenant_id)
    
    if not include_inactive:
        query = query.where(CommitteeType.is_active == True)
    
    types = session.exec(query).all()
    return types


@router.post("/", response_model=CommitteeTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_committee_type(
    type_data: CommitteeTypeCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Crear nuevo tipo de comité
    Solo para administradores del tenant
    """
    # Verificar que no exista ya un tipo con el mismo nombre
    existing = session.exec(
        select(CommitteeType).where(
            CommitteeType.tenant_id == tenant_id,
            CommitteeType.name == type_data.name
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un tipo de comité con ese nombre"
        )
    
    # Crear tipo
    committee_type = CommitteeType(
        **type_data.model_dump(),
        tenant_id=tenant_id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    session.add(committee_type)
    session.commit()
    session.refresh(committee_type)
    
    return committee_type


@router.get("/{type_id}", response_model=CommitteeTypeResponse)
async def get_committee_type(
    type_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener tipo de comité por ID"""
    committee_type = session.get(CommitteeType, type_id)
    
    if not committee_type or committee_type.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de comité no encontrado"
        )
    
    return committee_type


@router.put("/{type_id}", response_model=CommitteeTypeResponse)
async def update_committee_type(
    type_id: int,
    type_data: CommitteeTypeCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Actualizar tipo de comité
    Solo para administradores
    """
    committee_type = session.get(CommitteeType, type_id)
    
    if not committee_type or committee_type.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de comité no encontrado"
        )
    
    # Actualizar campos
    committee_type.name = type_data.name
    if type_data.description:
        committee_type.description = type_data.description
    
    session.add(committee_type)
    session.commit()
    session.refresh(committee_type)
    
    return committee_type


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_committee_type(
    type_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Desactivar tipo de comité (soft delete)
    No se puede eliminar si hay comités usando este tipo
    """
    committee_type = session.get(CommitteeType, type_id)
    
    if not committee_type or committee_type.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de comité no encontrado"
        )
    
    # Verificar si hay comités usando este tipo
    committees = session.exec(
        select(Committee).where(Committee.committee_type_id == type_id)
    ).all()
    
    if committees:
        # Soft delete - solo desactivar
        committee_type.is_active = False
        session.add(committee_type)
        session.commit()
    else:
        # Eliminar completamente si no hay comités
        session.delete(committee_type)
        session.commit()
    
    return None
