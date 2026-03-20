"""
Router para gestión de comités (MÓDULO PRIORITARIO)
Incluye CRUD completo con aislamiento multi-tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import os
import shutil

from ..database import get_session
from ..dependencies import (
    get_current_tenant,
    get_current_user,
    get_current_tenant_obj,
    check_tenant_limits
)
from ..models import (
    Committee,
    CommitteeMember,
    CommitteeType,
    CommitteeDocument,
    AdministrativeUnit,
    User,
    Tenant
)
from ..schemas import (
    CommitteeCreate,
    CommitteeUpdate,
    CommitteeResponse,
    CommitteeMemberCreate,
    CommitteeMemberUpdate,
    CommitteeMemberResponse,
    DocumentUploadResponse,
    AdministrativeUnitResponse,
    CommitteeTypeResponse
)
from ..config import get_committee_upload_dir


router = APIRouter(prefix="/committees", tags=["Committees"])


# ====================================
# COMMITTEE CRUD
# ====================================

@router.get("/", response_model=List[CommitteeResponse])
async def list_committees(
    skip: int = 0,
    limit: int = 100,
    committee_type_id: Optional[int] = None,
    administrative_unit_id: Optional[int] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Listar comités del tenant
    - Filtros opcionales por tipo, unidad administrativa y búsqueda
    - Paginación con skip y limit
    """
    query = select(Committee).where(Committee.tenant_id == tenant_id)
    
    # Aplicar filtros
    if committee_type_id:
        query = query.where(Committee.committee_type_id == committee_type_id)
    
    if administrative_unit_id:
        query = query.where(Committee.administrative_unit_id == administrative_unit_id)
    
    if search:
        query = query.where(
            (Committee.name.contains(search)) |
            (Committee.president_name.contains(search))
        )
    
    # Paginación
    query = query.offset(skip).limit(limit)
    
    committees = session.exec(query).all()
    
    # Enriquecer con relaciones y stats
    result = []
    for committee in committees:
        # Contar miembros
        member_count = session.exec(
            select(func.count(CommitteeMember.id)).where(
                CommitteeMember.committee_id == committee.id
            )
        ).one()
        
        # Convertir objetos relacionados a diccionarios
        committee_type_dict = committee.committee_type.model_dump() if committee.committee_type else None
        admin_unit_dict = committee.administrative_unit.model_dump() if committee.administrative_unit else None
        
        result.append(CommitteeResponse(
            **committee.model_dump(),
            committee_type=committee_type_dict,
            administrative_unit=admin_unit_dict,
            member_count=member_count
        ))
    
    return result


@router.post("/", response_model=CommitteeResponse, status_code=status.HTTP_201_CREATED)
async def create_committee(
    committee_data: CommitteeCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(check_tenant_limits)
):
    """
    Crear nuevo comité
    - Verifica límites de suscripción
    - Asigna automáticamente al usuario creador
    """
    # Verificar que el tipo de comité existe y pertenece al tenant
    committee_type = session.get(CommitteeType, committee_data.committee_type_id)
    if not committee_type or committee_type.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de comité no encontrado"
        )
    
    # Verificar que la unidad administrativa existe y pertenece al tenant
    admin_unit = session.get(AdministrativeUnit, committee_data.administrative_unit_id)
    if not admin_unit or admin_unit.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad administrativa no encontrada"
        )
    
    # Crear comité
    committee = Committee(
        **committee_data.model_dump(),
        tenant_id=tenant_id,
        created_by_user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    
    session.add(committee)
    session.commit()
    session.refresh(committee)
    
    return CommitteeResponse(
        **committee.model_dump(),
        committee_type=committee.committee_type,
        administrative_unit=committee.administrative_unit,
        member_count=0
    )


@router.get("/{committee_id}", response_model=CommitteeResponse)
async def get_committee(
    committee_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener comité por ID"""
    committee = session.get(Committee, committee_id)
    
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    # Contar miembros
    member_count = session.exec(
        select(func.count(CommitteeMember.id)).where(
            CommitteeMember.committee_id == committee.id
        )
    ).one()
    
    return CommitteeResponse(
        **committee.model_dump(),
        committee_type=committee.committee_type,
        administrative_unit=committee.administrative_unit,
        member_count=member_count
    )


@router.put("/{committee_id}", response_model=CommitteeResponse)
async def update_committee(
    committee_id: int,
    committee_data: CommitteeUpdate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Actualizar comité"""
    committee = session.get(Committee, committee_id)
    
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    # Actualizar solo los campos proporcionados
    update_data = committee_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(committee, key, value)
    
    committee.updated_at = datetime.utcnow()
    
    session.add(committee)
    session.commit()
    session.refresh(committee)
    
    member_count = session.exec(
        select(func.count(CommitteeMember.id)).where(
            CommitteeMember.committee_id == committee.id
        )
    ).one()
    
    return CommitteeResponse(
        **committee.model_dump(),
        committee_type=committee.committee_type,
        administrative_unit=committee.administrative_unit,
        member_count=member_count
    )


@router.delete("/{committee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_committee(
    committee_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar comité
    - Solo para tenant admin
    - Elimina en cascada miembros y documentos
    """
    if not current_user.is_tenant_admin and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar comités"
        )
    
    committee = session.get(Committee, committee_id)
    
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    # Eliminar miembros
    members = session.exec(
        select(CommitteeMember).where(CommitteeMember.committee_id == committee_id)
    ).all()
    for member in members:
        session.delete(member)
    
    # Eliminar documentos
    documents = session.exec(
        select(CommitteeDocument).where(CommitteeDocument.committee_id == committee_id)
    ).all()
    for doc in documents:
        # Eliminar archivo físico
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        session.delete(doc)
    
    # Eliminar comité
    session.delete(committee)
    session.commit()
    
    return None


# ====================================
# COMMITTEE MEMBERS
# ====================================

@router.get("/{committee_id}/members", response_model=List[CommitteeMemberResponse])
async def list_committee_members(
    committee_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar integrantes del comité"""
    # Verificar que el comité existe y pertenece al tenant
    committee = session.get(Committee, committee_id)
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    members = session.exec(
        select(CommitteeMember).where(CommitteeMember.committee_id == committee_id)
    ).all()
    
    return members


@router.post("/{committee_id}/members", response_model=CommitteeMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_committee_member(
    committee_id: int,
    member_data: CommitteeMemberCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Agregar integrante al comité
    - Máximo 10 integrantes por comité
    - Clave INE debe ser única
    """
    # Verificar comité
    committee = session.get(Committee, committee_id)
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    # Verificar límite de 10 integrantes
    member_count = session.exec(
        select(func.count(CommitteeMember.id)).where(
            CommitteeMember.committee_id == committee_id
        )
    ).one()
    
    if member_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El comité ya tiene el máximo de 10 integrantes"
        )
    
    # Verificar que la clave INE no exista en el tenant
    existing_member = session.exec(
        select(CommitteeMember).where(
            CommitteeMember.tenant_id == tenant_id,
            CommitteeMember.ine_key == member_data.ine_key.upper()
        )
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave INE ya está registrada en otro comité"
        )
    
    # Crear integrante
    member = CommitteeMember(
        **member_data.model_dump(),
        tenant_id=tenant_id,
        committee_id=committee_id,
        created_at=datetime.utcnow()
    )
    
    session.add(member)
    session.commit()
    session.refresh(member)
    
    return member


@router.put("/{committee_id}/members/{member_id}", response_model=CommitteeMemberResponse)
async def update_committee_member(
    committee_id: int,
    member_id: int,
    member_data: CommitteeMemberUpdate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Actualizar integrante del comité"""
    member = session.get(CommitteeMember, member_id)
    
    if not member or member.tenant_id != tenant_id or member.committee_id != committee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integrante no encontrado"
        )
    
    # Actualizar campos
    update_data = member_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)
    
    session.add(member)
    session.commit()
    session.refresh(member)
    
    return member


@router.delete("/{committee_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_committee_member(
    committee_id: int,
    member_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Eliminar integrante del comité"""
    if not current_user.is_tenant_admin and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar integrantes"
        )
    
    member = session.get(CommitteeMember, member_id)
    
    if not member or member.tenant_id != tenant_id or member.committee_id != committee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integrante no encontrado"
        )
    
    session.delete(member)
    session.commit()
    
    return None


# ====================================
# COMMITTEE DOCUMENTS
# ====================================

@router.get("/{committee_id}/documents", response_model=List[DocumentUploadResponse])
async def list_committee_documents(
    committee_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar documentos del comité"""
    committee = session.get(Committee, committee_id)
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    documents = session.exec(
        select(CommitteeDocument).where(CommitteeDocument.committee_id == committee_id)
    ).all()
    
    return documents


@router.post("/{committee_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_committee_document(
    committee_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Subir documento al comité
    - Acepta imágenes y PDFs
    - Guarda en uploads/{tenant_id}/committees/{committee_id}/
    """
    committee = session.get(Committee, committee_id)
    if not committee or committee.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comité no encontrado"
        )
    
    # Validar tipo de archivo
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido. Solo imágenes y PDF."
        )
    
    # Crear directorio
    upload_dir = get_committee_upload_dir(tenant_id, committee_id)
    
    # Generar nombre de archivo único
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar archivo: {str(e)}"
        )
    
    # Obtener tamaño del archivo
    file_size = os.path.getsize(file_path)
    
    # Crear registro en base de datos
    document = CommitteeDocument(
        tenant_id=tenant_id,
        committee_id=committee_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by_user_id=current_user.id,
        uploaded_at=datetime.utcnow()
    )
    
    session.add(document)
    session.commit()
    session.refresh(document)
    
    return document


@router.delete("/{committee_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_committee_document(
    committee_id: int,
    document_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Eliminar documento del comité"""
    document = session.get(CommitteeDocument, document_id)
    
    if not document or document.tenant_id != tenant_id or document.committee_id != committee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Eliminar archivo físico
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Eliminar registro
    session.delete(document)
    session.commit()
    
    return None
