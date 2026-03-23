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
from ..schemas import SeccionCreate, SeccionResponse, SeccionPoligonoResponse

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


@router.get("/estados")
async def list_estados(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Lista de estados únicos registrados para este tenant"""
    estados = session.exec(
        select(Seccion.estado_id, Seccion.nombre_estado).where(
            Seccion.tenant_id == tenant_id,
            Seccion.estado_id.isnot(None)
        ).distinct().order_by(Seccion.nombre_estado)
    ).all()
    return [{"estado_id": e[0], "nombre_estado": e[1]} for e in estados]


@router.get("/poligonos", response_model=List[SeccionPoligonoResponse])
async def list_secciones_poligonos(
    estado_id: Optional[int] = None,
    municipio_id: Optional[int] = None,
    distrito_id: Optional[int] = None,
    limit: int = 500,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Secciones con polígono GeoJSON y bounding box para el mapa.
    Solo devuelve secciones que tengan geojson cargado.
    """
    query = select(Seccion).where(
        Seccion.tenant_id == tenant_id,
        Seccion.geojson.isnot(None)
    )
    if estado_id is not None:
        query = query.where(Seccion.estado_id == estado_id)
    if municipio_id is not None:
        query = query.where(Seccion.municipio_id == municipio_id)
    if distrito_id is not None:
        query = query.where(Seccion.distrito_id == distrito_id)

    query = query.order_by(Seccion.seccion_numero).limit(limit)
    secciones = session.exec(query).all()

    result = []
    for s in secciones:
        try:
            seccion_int = int(s.seccion_numero)
        except (ValueError, TypeError):
            seccion_int = 0

        bbox = None
        if all(v is not None for v in [s.bbox_min_lat, s.bbox_max_lat, s.bbox_min_lon, s.bbox_max_lon]):
            bbox = {
                "min_lat": s.bbox_min_lat,
                "max_lat": s.bbox_max_lat,
                "min_lon": s.bbox_min_lon,
                "max_lon": s.bbox_max_lon,
            }

        result.append(SeccionPoligonoResponse(
            id=s.id,
            seccion=seccion_int,
            nombre_estado=s.nombre_estado,
            estado_id=s.estado_id,
            nombre_municipio=s.nombre_municipio,
            municipio_id=s.municipio_id,
            nombre_distrito=s.nombre_distrito,
            distrito_id=s.distrito_id,
            distrito_federal=s.distrito_federal,
            geojson=s.geojson,
            bbox=bbox,
        ))

    return result


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
    Columna obligatoria: seccion_numero
    Columnas opcionales: estado_id, nombre_estado, municipio_id, nombre_municipio,
                         distrito_id, nombre_distrito, distrito_federal,
                         geojson, bbox_min_lat, bbox_max_lat, bbox_min_lon, bbox_max_lon
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
            def _int(key):
                v = row.get(key, '').strip()
                return int(v) if v else None

            def _float(key):
                v = row.get(key, '').strip()
                return float(v) if v else None

            def _str(key):
                v = row.get(key, '').strip()
                return v or None

            seccion = Seccion(
                tenant_id=tenant_id,
                seccion_numero=row.get('seccion_numero', '').strip(),
                estado_id=_int('estado_id'),
                nombre_estado=_str('nombre_estado'),
                municipio_id=_int('municipio_id'),
                nombre_municipio=_str('nombre_municipio'),
                distrito_id=_int('distrito_id'),
                nombre_distrito=_str('nombre_distrito'),
                distrito_federal=_int('distrito_federal'),
                geojson=_str('geojson'),
                bbox_min_lat=_float('bbox_min_lat'),
                bbox_max_lat=_float('bbox_max_lat'),
                bbox_min_lon=_float('bbox_min_lon'),
                bbox_max_lon=_float('bbox_max_lon'),
            )
            session.add(seccion)
            created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    session.commit()

    return {
        "message": f"Importación completada: {created} secciones creadas",
        "created": created,
        "errors": errors[:20]
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
