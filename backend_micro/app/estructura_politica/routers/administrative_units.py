"""
Router para gestión de unidades administrativas jerárquicas
STATE → REGION → DISTRICT → MUNICIPALITY → SECTION
"""
from fastapi import APIRouter, Depends, HTTPException, status
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
    AdministrativeUnit,
    UserAssignment,
    User,
    Committee,
    CommitteeMember,
    UnitType
)
from ..schemas import (
    AdministrativeUnitCreate,
    AdministrativeUnitResponse,
    UserAssignmentCreate,
    UserAssignmentResponse,
    UserResponse
)


router = APIRouter(prefix="/administrative-units", tags=["Administrative Units"])


# ====================================
# ADMINISTRATIVE UNITS CRUD
# ====================================

@router.get("/", response_model=List[AdministrativeUnitResponse])
async def list_administrative_units(
    unit_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    include_children: bool = False,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Listar unidades administrativas del tenant
    
    - Filtrar por tipo (STATE, REGION, DISTRICT, MUNICIPALITY, SECTION)
    - Filtrar por padre (para obtener hijos de una unidad)
    - Opción de incluir árbol completo de hijos
    """
    query = select(AdministrativeUnit).where(AdministrativeUnit.tenant_id == tenant_id)
    
    if unit_type:
        query = query.where(AdministrativeUnit.unit_type == unit_type)
    
    if parent_id is not None:
        query = query.where(AdministrativeUnit.parent_id == parent_id)
    elif parent_id is None and not unit_type:
        # Si no se especifica parent_id ni tipo, mostrar solo raíz (STATE)
        query = query.where(AdministrativeUnit.parent_id == None)
    
    units = session.exec(query).all()
    
    result = []
    for unit in units:
        # Contar comités y miembros recursivamente
        committee_count, member_count = count_unit_stats_recursive(session, unit.id)
        
        unit_response = AdministrativeUnitResponse(
            **unit.model_dump(),
            committee_count=committee_count,
            member_count=member_count,
            children=[]
        )
        
        # Incluir hijos si se solicitó
        if include_children:
            unit_response.children = get_children_recursive(session, unit.id, tenant_id)
        
        result.append(unit_response)
    
    return result


@router.get("/tree", response_model=List[AdministrativeUnitResponse])
async def get_administrative_tree(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener árbol completo de unidades administrativas
    Retorna desde la raíz (STATE) con todos los hijos anidados
    """
    # Obtener unidades raíz (sin padre)
    root_units = session.exec(
        select(AdministrativeUnit).where(
            AdministrativeUnit.tenant_id == tenant_id,
            AdministrativeUnit.parent_id == None
        )
    ).all()
    
    result = []
    for unit in root_units:
        committee_count, member_count = count_unit_stats_recursive(session, unit.id)
        
        unit_response = AdministrativeUnitResponse(
            **unit.model_dump(),
            committee_count=committee_count,
            member_count=member_count,
            children=get_children_recursive(session, unit.id, tenant_id)
        )
        result.append(unit_response)
    
    return result


@router.post("/", response_model=AdministrativeUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_administrative_unit(
    unit_data: AdministrativeUnitCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Crear unidad administrativa
    Solo para administradores del tenant
    """
    # Validar que el padre existe si se proporcionó
    if unit_data.parent_id:
        parent = session.get(AdministrativeUnit, unit_data.parent_id)
        if not parent or parent.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidad padre no encontrada"
            )
        
        # Validar jerarquía lógica
        validate_hierarchy(parent.unit_type, unit_data.unit_type.value)
    
    # Crear unidad
    unit = AdministrativeUnit(
        **unit_data.model_dump(),
        tenant_id=tenant_id,
        created_at=datetime.utcnow()
    )
    
    session.add(unit)
    session.commit()
    session.refresh(unit)
    
    return AdministrativeUnitResponse(
        **unit.model_dump(),
        committee_count=0,
        member_count=0,
        children=[]
    )


@router.get("/{unit_id}", response_model=AdministrativeUnitResponse)
async def get_administrative_unit(
    unit_id: int,
    include_children: bool = True,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener unidad administrativa por ID"""
    unit = session.get(AdministrativeUnit, unit_id)
    
    if not unit or unit.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad administrativa no encontrada"
        )
    
    committee_count, member_count = count_unit_stats_recursive(session, unit.id)
    
    children = []
    if include_children:
        children = get_children_recursive(session, unit.id, tenant_id)
    
    return AdministrativeUnitResponse(
        **unit.model_dump(),
        committee_count=committee_count,
        member_count=member_count,
        children=children
    )


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_administrative_unit(
    unit_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Eliminar unidad administrativa
    Solo si no tiene comités ni hijos
    """
    unit = session.get(AdministrativeUnit, unit_id)
    
    if not unit or unit.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad administrativa no encontrada"
        )
    
    # Verificar que no tenga hijos
    children = session.exec(
        select(AdministrativeUnit).where(AdministrativeUnit.parent_id == unit_id)
    ).all()
    
    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar una unidad con sub-unidades"
        )
    
    # Verificar que no tenga comités
    committees = session.exec(
        select(Committee).where(Committee.administrative_unit_id == unit_id)
    ).all()
    
    if committees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar una unidad con comités asignados"
        )
    
    session.delete(unit)
    session.commit()
    
    return None


# ====================================
# USER ASSIGNMENTS (COORDINADORES)
# ====================================

@router.get("/{unit_id}/assignments", response_model=List[UserAssignmentResponse])
async def list_unit_assignments(
    unit_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Listar coordinadores asignados a una unidad administrativa
    """
    # Verificar que la unidad existe
    unit = session.get(AdministrativeUnit, unit_id)
    if not unit or unit.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad administrativa no encontrada"
        )
    
    assignments = session.exec(
        select(UserAssignment).where(
            UserAssignment.administrative_unit_id == unit_id,
            UserAssignment.tenant_id == tenant_id
        )
    ).all()
    
    result = []
    for assignment in assignments:
        result.append(UserAssignmentResponse(
            id=assignment.id,
            user=UserResponse(**assignment.user.model_dump()),
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


@router.post("/{unit_id}/assignments", response_model=UserAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_unit(
    unit_id: int,
    assignment_data: UserAssignmentCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Asignar coordinador a unidad administrativa
    Solo para administradores del tenant
    """
    # Verificar unidad
    unit = session.get(AdministrativeUnit, unit_id)
    if not unit or unit.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad administrativa no encontrada"
        )
    
    # Verificar usuario
    user = session.get(User, assignment_data.user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que el usuario no esté ya asignado a esta unidad
    existing = session.exec(
        select(UserAssignment).where(
            UserAssignment.user_id == assignment_data.user_id,
            UserAssignment.administrative_unit_id == unit_id
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
        user_id=assignment_data.user_id,
        administrative_unit_id=unit_id,
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


@router.delete("/{unit_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_assignment(
    unit_id: int,
    assignment_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Remover asignación de coordinador
    """
    assignment = session.get(UserAssignment, assignment_id)
    
    if not assignment or assignment.tenant_id != tenant_id or assignment.administrative_unit_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    session.delete(assignment)
    session.commit()
    
    return None


# ====================================
# HELPER FUNCTIONS
# ====================================

def get_children_recursive(session: Session, parent_id: int, tenant_id: int) -> List[AdministrativeUnitResponse]:
    """Obtener hijos recursivamente"""
    children_units = session.exec(
        select(AdministrativeUnit).where(
            AdministrativeUnit.parent_id == parent_id,
            AdministrativeUnit.tenant_id == tenant_id
        )
    ).all()
    
    result = []
    for child in children_units:
        committee_count, member_count = count_unit_stats_recursive(session, child.id)
        
        child_response = AdministrativeUnitResponse(
            **child.model_dump(),
            committee_count=committee_count,
            member_count=member_count,
            children=get_children_recursive(session, child.id, tenant_id)
        )
        result.append(child_response)
    
    return result


def count_unit_stats_recursive(session: Session, unit_id: int) -> tuple:
    """
    Contar comités y miembros recursivamente
    Retorna (committee_count, member_count)
    """
    # Obtener IDs de esta unidad y todas sus descendientes
    unit_ids = get_descendant_ids(session, unit_id)
    unit_ids.append(unit_id)
    
    # Contar comités
    committee_count = session.exec(
        select(func.count(Committee.id)).where(
            Committee.administrative_unit_id.in_(unit_ids)
        )
    ).one()
    
    # Contar miembros de esos comités
    committee_ids_query = select(Committee.id).where(
        Committee.administrative_unit_id.in_(unit_ids)
    )
    committee_ids = [row for row in session.exec(committee_ids_query).all()]
    
    member_count = 0
    if committee_ids:
        member_count = session.exec(
            select(func.count(CommitteeMember.id)).where(
                CommitteeMember.committee_id.in_(committee_ids)
            )
        ).one()
    
    return committee_count, member_count


def get_descendant_ids(session: Session, parent_id: int) -> List[int]:
    """Obtener IDs de todos los descendientes recursivamente"""
    children = session.exec(
        select(AdministrativeUnit).where(AdministrativeUnit.parent_id == parent_id)
    ).all()
    
    descendant_ids = []
    for child in children:
        descendant_ids.append(child.id)
        descendant_ids.extend(get_descendant_ids(session, child.id))
    
    return descendant_ids


def validate_hierarchy(parent_type: str, child_type: str):
    """Validar que la jerarquía sea lógica"""
    valid_hierarchies = {
        "STATE": ["REGION"],
        "REGION": ["DISTRICT"],
        "DISTRICT": ["MUNICIPALITY"],
        "MUNICIPALITY": ["SECTION"],
        "SECTION": []
    }
    
    if child_type not in valid_hierarchies.get(parent_type, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Jerarquía inválida: {parent_type} no puede tener hijos de tipo {child_type}"
        )
