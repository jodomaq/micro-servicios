"""
Router para gestión de Eventos
CRUD completo con aislamiento multi-tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import secrets

from ..database import get_session
from ..dependencies import get_current_tenant, get_current_user, get_current_tenant_admin
from ..models import Event, Attendance, User, AdministrativeUnit
from ..schemas import EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=List[EventResponse])
async def list_events(
    skip: int = 0,
    limit: int = 50,
    is_active: Optional[bool] = None,
    administrative_unit_id: Optional[int] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar eventos del tenant"""
    query = select(Event).where(Event.tenant_id == tenant_id)
    
    if is_active is not None:
        query = query.where(Event.is_active == is_active)
    
    if administrative_unit_id:
        query = query.where(Event.administrative_unit_id == administrative_unit_id)
    
    query = query.order_by(Event.event_date.desc()).offset(skip).limit(limit)
    events = session.exec(query).all()
    
    result = []
    for event in events:
        att_count = session.exec(
            select(func.count(Attendance.id)).where(Attendance.event_id == event.id)
        ).one()
        result.append(EventResponse(
            **event.model_dump(),
            attendance_count=att_count
        ))
    return result


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Crear nuevo evento"""
    if data.administrative_unit_id:
        unit = session.get(AdministrativeUnit, data.administrative_unit_id)
        if not unit or unit.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Unidad administrativa no encontrada")
    
    event = Event(
        **data.model_dump(),
        tenant_id=tenant_id,
        created_by_user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    
    return EventResponse(**event.model_dump(), attendance_count=0)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener evento por ID"""
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    att_count = session.exec(
        select(func.count(Attendance.id)).where(Attendance.event_id == event.id)
    ).one()
    
    return EventResponse(**event.model_dump(), attendance_count=att_count)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Actualizar evento"""
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    
    session.add(event)
    session.commit()
    session.refresh(event)
    
    att_count = session.exec(
        select(func.count(Attendance.id)).where(Attendance.event_id == event.id)
    ).one()
    
    return EventResponse(**event.model_dump(), attendance_count=att_count)


@router.delete("/{event_id}")
async def deactivate_event(
    event_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Desactivar evento (soft delete)"""
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    event.is_active = False
    session.add(event)
    session.commit()
    return {"message": "Evento desactivado"}


@router.get("/{event_id}/link")
async def get_event_link(
    event_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Generar enlace público único para registro de asistencia"""
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    # El código del evento = tenant_id-event_id codificado
    event_code = f"{tenant_id}-{event_id}"
    
    return {
        "event_id": event_id,
        "event_code": event_code,
        "link": f"/asistencia/evento/{event_code}"
    }
