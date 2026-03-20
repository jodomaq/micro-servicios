"""
Router para gestión de usuarios y roles (Admin Dashboard)
Incluye alta/baja de coordinadores, asignación de roles y jerarquías
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from ..database import get_session
from ..dependencies import (
    get_current_tenant,
    get_current_user,
    get_current_tenant_admin
)
from ..models import (
    User,
    UserAssignment,
    AdministrativeUnit,
    Committee,
    UserRole
)
from ..schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserAssignmentCreate,
    UserAssignmentResponse,
    AdministrativeUnitResponse
)


router = APIRouter(prefix="/users", tags=["Users"])


# ====================================
# USER MANAGEMENT (ADMIN DASHBOARD)
# ====================================

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[int] = None,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Listar usuarios del tenant
    Solo para administradores
    """
    query = select(User).where(User.tenant_id == tenant_id)
    
    if search:
        query = query.where(
            (User.name.contains(search)) |
            (User.email.contains(search))
        )
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Filtrar por rol via UserAssignment
    if role is not None:
        user_ids_with_role = session.exec(
            select(UserAssignment.user_id).where(
                UserAssignment.tenant_id == tenant_id,
                UserAssignment.role == role
            )
        ).all()
        
        if user_ids_with_role:
            query = query.where(User.id.in_(user_ids_with_role))
        else:
            return []  # No hay usuarios con ese rol
    
    query = query.offset(skip).limit(limit)
    users = session.exec(query).all()
    
    return [UserResponse(**user.model_dump()) for user in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Crear usuario manualmente
    Solo para administradores (para crear coordinadores sin OAuth)
    """
    # Verificar que el email no exista en el tenant
    existing = session.exec(
        select(User).where(
            User.tenant_id == tenant_id,
            User.email == user_data.email
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email en este tenant"
        )
    
    # Crear usuario
    user = User(
        **user_data.model_dump(),
        tenant_id=tenant_id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(**user.model_dump())


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener usuario por ID"""
    user = session.get(User, user_id)
    
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return UserResponse(**user.model_dump())


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Actualizar usuario
    Solo para administradores
    """
    user = session.get(User, user_id)
    
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar solo campos proporcionados
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(**user.model_dump())


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Desactivar usuario (soft delete)
    Solo para administradores
    """
    user = session.get(User, user_id)
    
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No permitir desactivar al usuario actual
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivarse a sí mismo"
        )
    
    user.is_active = False
    session.add(user)
    session.commit()
    
    return None


# ====================================
# USER ASSIGNMENTS (COORDINADORES)
# ====================================

@router.get("/{user_id}/assignments", response_model=List[UserAssignmentResponse])
async def get_user_assignments(
    user_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener todas las asignaciones de un usuario
    (jerarquías y roles que tiene)
    """
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    assignments = session.exec(
        select(UserAssignment).where(
            UserAssignment.user_id == user_id,
            UserAssignment.tenant_id == tenant_id
        )
    ).all()
    
    result = []
    for assignment in assignments:
        result.append(UserAssignmentResponse(
            id=assignment.id,
            user=UserResponse(**user.model_dump()),
            administrative_unit=AdministrativeUnitResponse(
                **assignment.administrative_unit.model_dump(),
                committee_count=0,
                member_count=0,
                children=[]
            ),
            role=assignment.role,
            created_at=assignment.created_at
        ))
    
    return result


@router.post("/{user_id}/assignments", response_model=UserAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_unit(
    user_id: int,
    assignment_data: UserAssignmentCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Asignar usuario a unidad administrativa con rol
    (Hacer coordinador de una región/distrito/municipio/sección)
    Solo para administradores
    """
    # Verificar usuario
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar unidad administrativa
    unit = session.get(AdministrativeUnit, assignment_data.administrative_unit_id)
    if not unit or unit.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad administrativa no encontrada"
        )
    
    # Verificar que no exista ya esta asignación
    existing = session.exec(
        select(UserAssignment).where(
            UserAssignment.user_id == user_id,
            UserAssignment.administrative_unit_id == assignment_data.administrative_unit_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está asignado a esta unidad"
        )
    
    # Crear asignación
    assignment = UserAssignment(
        tenant_id=tenant_id,
        user_id=user_id,
        administrative_unit_id=assignment_data.administrative_unit_id,
        role=assignment_data.role,
        created_at=datetime.utcnow()
    )
    
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    
    return UserAssignmentResponse(
        id=assignment.id,
        user=UserResponse(**user.model_dump()),
        administrative_unit=AdministrativeUnitResponse(
            **unit.model_dump(),
            committee_count=0,
            member_count=0,
            children=[]
        ),
        role=assignment.role,
        created_at=assignment.created_at
    )


@router.delete("/{user_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_assignment(
    user_id: int,
    assignment_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Remover asignación de coordinador
    Solo para administradores
    """
    assignment = session.get(UserAssignment, assignment_id)
    
    if not assignment or assignment.tenant_id != tenant_id or assignment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    session.delete(assignment)
    session.commit()
    
    return None


# ====================================
# USER STATISTICS
# ====================================

@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas del usuario
    - Número de comités bajo su coordinación
    - Número de integrantes bajo su coordinación
    - Unidades administrativas a su cargo
    """
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Obtener asignaciones
    assignments = session.exec(
        select(UserAssignment).where(
            UserAssignment.user_id == user_id,
            UserAssignment.tenant_id == tenant_id
        )
    ).all()
    
    # Contar comités creados directamente
    committees_created = session.exec(
        select(func.count(Committee.id)).where(
            Committee.created_by_user_id == user_id,
            Committee.tenant_id == tenant_id
        )
    ).one()
    
    # Para cada asignación, contar comités en esa jerarquía
    total_committees_in_hierarchy = 0
    total_members_in_hierarchy = 0
    
    for assignment in assignments:
        # Obtener todas las unidades descendientes
        unit_ids = get_descendant_unit_ids(session, assignment.administrative_unit_id)
        unit_ids.append(assignment.administrative_unit_id)
        
        # Contar comités
        committee_count = session.exec(
            select(func.count(Committee.id)).where(
                Committee.administrative_unit_id.in_(unit_ids)
            )
        ).one()
        
        total_committees_in_hierarchy += committee_count
        
        # Contar miembros
        from ..models import CommitteeMember
        committee_ids = session.exec(
            select(Committee.id).where(Committee.administrative_unit_id.in_(unit_ids))
        ).all()
        
        if committee_ids:
            member_count = session.exec(
                select(func.count(CommitteeMember.id)).where(
                    CommitteeMember.committee_id.in_(committee_ids)
                )
            ).one()
            total_members_in_hierarchy += member_count
    
    return {
        "user_id": user_id,
        "user_name": user.name,
        "user_email": user.email,
        "assignments_count": len(assignments),
        "committees_created": committees_created,
        "committees_in_hierarchy": total_committees_in_hierarchy,
        "members_in_hierarchy": total_members_in_hierarchy,
        "assignments": [
            {
                "unit_id": a.administrative_unit_id,
                "unit_name": a.administrative_unit.name,
                "role": a.role
            }
            for a in assignments
        ]
    }


# ====================================
# HELPER FUNCTIONS
# ====================================

def get_descendant_unit_ids(session: Session, parent_id: int) -> List[int]:
    """Obtener IDs de todos los descendientes recursivamente"""
    children = session.exec(
        select(AdministrativeUnit).where(AdministrativeUnit.parent_id == parent_id)
    ).all()
    
    descendant_ids = []
    for child in children:
        descendant_ids.append(child.id)
        descendant_ids.extend(get_descendant_unit_ids(session, child.id))
    
    return descendant_ids
