"""
Router para registro de Asistencia a Eventos
Incluye endpoints públicos (sin auth JWT) y protegidos
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import io

from ..database import get_session
from ..dependencies import get_current_tenant, get_current_user
from ..models import Event, Attendance, User
from ..schemas import AttendanceCreate, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/register/{event_code}", status_code=status.HTTP_201_CREATED)
async def register_attendance(
    event_code: str,
    data: AttendanceCreate,
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Registrar asistencia a un evento (endpoint público).
    El event_code tiene formato: {tenant_id}-{event_id}
    """
    try:
        parts = event_code.split("-")
        tenant_id = int(parts[0])
        event_id = int(parts[1])
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Código de evento inválido")
    
    # Verificar que el evento existe y está activo
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id or not event.is_active:
        raise HTTPException(status_code=404, detail="Evento no encontrado o inactivo")
    
    # Para dev-login, extraer datos directamente
    email = ""
    name = ""
    provider_user_id = ""
    
    if data.provider == "dev":
        # Modo desarrollo: extraer email del token
        email = data.provider_token
        name = data.provider_token.split("@")[0] if "@" in data.provider_token else data.provider_token
        provider_user_id = data.provider_token
    elif data.provider == "google":
        # Verificar token de Google
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
            from ..config import settings
            idinfo = id_token.verify_oauth2_token(
                data.provider_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            email = idinfo.get("email", "")
            name = idinfo.get("name", "")
            provider_user_id = idinfo.get("sub", "")
        except Exception:
            raise HTTPException(status_code=401, detail="Token de Google inválido")
    elif data.provider == "microsoft":
        try:
            import requests as http_requests
            headers = {"Authorization": f"Bearer {data.provider_token}"}
            resp = http_requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Token de Microsoft inválido")
            user_data = resp.json()
            email = user_data.get("mail") or user_data.get("userPrincipalName", "")
            name = user_data.get("displayName", "")
            provider_user_id = user_data.get("id", "")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Error verificando token de Microsoft")
    else:
        raise HTTPException(status_code=400, detail="Proveedor de autenticación no soportado")
    
    # Verificar duplicado (mismo email, mismo evento)
    existing = session.exec(
        select(Attendance).where(
            Attendance.event_id == event_id,
            Attendance.email == email
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya se registró asistencia con este email para este evento"
        )
    
    # Crear registro de asistencia
    attendance = Attendance(
        tenant_id=tenant_id,
        event_id=event_id,
        provider=data.provider,
        provider_user_id=provider_user_id,
        email=email,
        name=name,
        device_id=None,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy,
        timezone=data.timezone,
        created_at=datetime.utcnow()
    )
    
    session.add(attendance)
    session.commit()
    session.refresh(attendance)
    
    return AttendanceResponse(
        id=attendance.id,
        event_id=attendance.event_id,
        provider=attendance.provider,
        email=attendance.email,
        name=attendance.name,
        latitude=attendance.latitude,
        longitude=attendance.longitude,
        created_at=attendance.created_at
    )


@router.get("/event/{event_id}", response_model=List[AttendanceResponse])
async def list_attendances(
    event_id: int,
    skip: int = 0,
    limit: int = 200,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar asistentes de un evento (protegido)"""
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    attendances = session.exec(
        select(Attendance).where(
            Attendance.event_id == event_id,
            Attendance.tenant_id == tenant_id
        ).order_by(Attendance.created_at.desc()).offset(skip).limit(limit)
    ).all()
    
    return [
        AttendanceResponse(
            id=a.id,
            event_id=a.event_id,
            provider=a.provider,
            email=a.email,
            name=a.name,
            latitude=a.latitude,
            longitude=a.longitude,
            created_at=a.created_at
        ) for a in attendances
    ]


@router.get("/event/{event_id}/count")
async def count_attendances(
    event_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Contar asistentes de un evento"""
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    count = session.exec(
        select(func.count(Attendance.id)).where(Attendance.event_id == event_id)
    ).one()
    
    return {"event_id": event_id, "attendance_count": count}


@router.get("/event/{event_id}/export")
async def export_attendances(
    event_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Exportar asistentes a formato Excel"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    attendances = session.exec(
        select(Attendance).where(
            Attendance.event_id == event_id,
            Attendance.tenant_id == tenant_id
        ).order_by(Attendance.created_at)
    ).all()
    
    # Crear Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Asistencia"
    
    # Headers
    headers = ["#", "Nombre", "Email", "Proveedor", "Latitud", "Longitud", "Fecha/Hora"]
    ws.append(headers)
    
    for i, a in enumerate(attendances, 1):
        ws.append([
            i, a.name, a.email, a.provider,
            a.latitude, a.longitude,
            a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
        ])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"asistencia_{event.name}_{event_id}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/event-info/{event_code}")
async def get_event_info_public(
    event_code: str,
    session: Session = Depends(get_session)
):
    """Obtener información pública de un evento (sin auth)"""
    try:
        parts = event_code.split("-")
        tenant_id = int(parts[0])
        event_id = int(parts[1])
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Código de evento inválido")
    
    event = session.get(Event, event_id)
    if not event or event.tenant_id != tenant_id or not event.is_active:
        raise HTTPException(status_code=404, detail="Evento no encontrado o inactivo")
    
    att_count = session.exec(
        select(func.count(Attendance.id)).where(Attendance.event_id == event_id)
    ).one()
    
    return {
        "event_id": event.id,
        "name": event.name,
        "description": event.description,
        "event_date": event.event_date,
        "location_name": event.location_name,
        "attendance_count": att_count,
        "tenant_id": tenant_id
    }
