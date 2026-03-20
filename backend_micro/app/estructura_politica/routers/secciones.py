"""
Router para Catálogo de Secciones Electorales
CRUD e importación masiva
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import csv
import io

from ..database import get_session
from ..dependencies import get_current_tenant, get_current_user, get_current_tenant_admin
from ..models import Seccion, User
from ..schemas import SeccionCreate, SeccionResponse

router = APIRouter(prefix="/secciones", tags=["Secciones Electorales"])


@router.get("/", response_model=List[SeccionResponse])
async def list_secciones(
    skip: int = 0,
    limit: int = 200,
    municipio_id: Optional[int] = None,
    distrito_id: Optional[int] = None,
    seccion_numero: Optional[str] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar secciones electorales con filtros"""
    query = select(Seccion).where(Seccion.tenant_id == tenant_id)
    
    if municipio_id is not None:
        query = query.where(Seccion.municipio_id == municipio_id)
    
    if distrito_id is not None:
        query = query.where(Seccion.distrito_id == distrito_id)
    
    if seccion_numero:
        query = query.where(Seccion.seccion_numero == seccion_numero)
    
    if search:
        query = query.where(
            (Seccion.nombre_municipio.contains(search)) |
            (Seccion.nombre_distrito.contains(search)) |
            (Seccion.seccion_numero.contains(search))
        )
    
    query = query.order_by(Seccion.seccion_numero).offset(skip).limit(limit)
    return session.exec(query).all()


@router.post("/", response_model=SeccionResponse, status_code=status.HTTP_201_CREATED)
async def create_seccion(
    data: SeccionCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Crear sección electoral (solo admin)"""
    seccion = Seccion(
        **data.model_dump(),
        tenant_id=tenant_id
    )
    session.add(seccion)
    session.commit()
    session.refresh(seccion)
    return seccion


@router.get("/municipios")
async def list_municipios(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Lista de municipios únicos"""
    municipios = session.exec(
        select(Seccion.municipio_id, Seccion.nombre_municipio).where(
            Seccion.tenant_id == tenant_id,
            Seccion.municipio_id.isnot(None)
        ).distinct()
    ).all()
    return [{"municipio_id": m[0], "nombre": m[1]} for m in municipios]


@router.get("/distritos")
async def list_distritos(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Lista de distritos únicos"""
    distritos = session.exec(
        select(Seccion.distrito_id, Seccion.nombre_distrito).where(
            Seccion.tenant_id == tenant_id,
            Seccion.distrito_id.isnot(None)
        ).distinct()
    ).all()
    return [{"distrito_id": d[0], "nombre": d[1]} for d in distritos]


@router.post("/bulk-import")
async def bulk_import_secciones(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """
    Importación masiva desde CSV (solo admin).
    El CSV debe tener columnas: seccion_numero,municipio_id,nombre_municipio,distrito_id,nombre_distrito,distrito_federal
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV")
    
    content = await file.read()
    text = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    
    created = 0
    errors = []
    
    for i, row in enumerate(reader, start=2):
        try:
            seccion = Seccion(
                tenant_id=tenant_id,
                seccion_numero=row.get('seccion_numero', '').strip(),
                municipio_id=int(row['municipio_id']) if row.get('municipio_id') else None,
                nombre_municipio=row.get('nombre_municipio', '').strip() or None,
                distrito_id=int(row['distrito_id']) if row.get('distrito_id') else None,
                nombre_distrito=row.get('nombre_distrito', '').strip() or None,
                distrito_federal=int(row['distrito_federal']) if row.get('distrito_federal') else None
            )
            session.add(seccion)
            created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})
    
    session.commit()
    
    return {
        "message": f"Importación completada: {created} secciones creadas",
        "created": created,
        "errors": errors[:20]  # Máximo 20 errores
    }


@router.delete("/all")
async def delete_all_secciones(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Eliminar todas las secciones del tenant (solo admin)"""
    secciones = session.exec(
        select(Seccion).where(Seccion.tenant_id == tenant_id)
    ).all()
    
    count = len(secciones)
    for s in secciones:
        session.delete(s)
    session.commit()
    
    return {"message": f"{count} secciones eliminadas"}
