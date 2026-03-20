"""
Router para Dashboard Estadístico
Proporciona datos agregados para gráficas, mapas y reportes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import Optional
from datetime import datetime, timedelta

from ..database import get_session
from ..dependencies import get_current_tenant, get_current_user
from ..models import (
    Committee, CommitteeMember, CommitteeType, User,
    AdministrativeUnit, UserAssignment, Event, Attendance,
    Survey, SurveyResponse as SurveyResponseModel
)
from ..schemas import DashboardStats, TreeNodeStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Estadísticas generales del tenant"""
    total_committees = session.exec(
        select(func.count(Committee.id)).where(Committee.tenant_id == tenant_id)
    ).one()
    
    total_members = session.exec(
        select(func.count(CommitteeMember.id)).where(CommitteeMember.tenant_id == tenant_id)
    ).one()
    
    total_users = session.exec(
        select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_active == True)
    ).one()
    
    total_events = session.exec(
        select(func.count(Event.id)).where(Event.tenant_id == tenant_id)
    ).one()
    
    total_attendances = session.exec(
        select(func.count(Attendance.id)).where(Attendance.tenant_id == tenant_id)
    ).one()
    
    # Comités por tipo
    type_stats = session.exec(
        select(CommitteeType.name, func.count(Committee.id)).join(
            Committee, Committee.committee_type_id == CommitteeType.id
        ).where(
            CommitteeType.tenant_id == tenant_id
        ).group_by(CommitteeType.name)
    ).all()
    committees_by_type = {name: count for name, count in type_stats}
    
    # Crecimiento este mes
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    new_committees = session.exec(
        select(func.count(Committee.id)).where(
            Committee.tenant_id == tenant_id,
            Committee.created_at >= start_of_month
        )
    ).one()
    
    new_members = session.exec(
        select(func.count(CommitteeMember.id)).where(
            CommitteeMember.tenant_id == tenant_id,
            CommitteeMember.created_at >= start_of_month
        )
    ).one()
    
    new_users = session.exec(
        select(func.count(User.id)).where(
            User.tenant_id == tenant_id,
            User.created_at >= start_of_month
        )
    ).one()
    
    return DashboardStats(
        total_committees=total_committees,
        total_members=total_members,
        total_users=total_users,
        total_events=total_events,
        total_attendances=total_attendances,
        committees_by_type=committees_by_type,
        growth_this_month={
            "committees": new_committees,
            "members": new_members,
            "users": new_users
        }
    )


@router.get("/committees/by-type")
async def committees_by_type(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Comités agrupados por tipo"""
    stats = session.exec(
        select(
            CommitteeType.id,
            CommitteeType.name,
            func.count(Committee.id).label("count")
        ).outerjoin(
            Committee, Committee.committee_type_id == CommitteeType.id
        ).where(
            CommitteeType.tenant_id == tenant_id,
            CommitteeType.is_active == True
        ).group_by(CommitteeType.id, CommitteeType.name)
    ).all()
    
    return [{"type_id": s[0], "type_name": s[1], "count": s[2]} for s in stats]


@router.get("/committees/by-unit")
async def committees_by_unit(
    unit_type: Optional[str] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Comités agrupados por unidad administrativa"""
    query = select(
        AdministrativeUnit.id,
        AdministrativeUnit.name,
        AdministrativeUnit.unit_type,
        func.count(Committee.id).label("count")
    ).outerjoin(
        Committee, Committee.administrative_unit_id == AdministrativeUnit.id
    ).where(
        AdministrativeUnit.tenant_id == tenant_id
    )
    
    if unit_type:
        query = query.where(AdministrativeUnit.unit_type == unit_type)
    
    query = query.group_by(
        AdministrativeUnit.id, AdministrativeUnit.name, AdministrativeUnit.unit_type
    )
    
    stats = session.exec(query).all()
    return [{"unit_id": s[0], "unit_name": s[1], "unit_type": s[2], "count": s[3]} for s in stats]


@router.get("/committees/by-coordinator")
async def committees_by_coordinator(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Comités por coordinador (usuario creador)"""
    stats = session.exec(
        select(
            User.id,
            User.name,
            func.count(Committee.id).label("count")
        ).join(
            Committee, Committee.created_by_user_id == User.id
        ).where(
            User.tenant_id == tenant_id
        ).group_by(User.id, User.name)
    ).all()
    
    return [{"user_id": s[0], "user_name": s[1], "count": s[2]} for s in stats]


@router.get("/committees/growth")
async def committees_growth(
    months: int = 6,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Crecimiento de comités por mes"""
    now = datetime.utcnow()
    result = []
    
    for i in range(months - 1, -1, -1):
        # Calcular inicio y fin del mes
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        count = session.exec(
            select(func.count(Committee.id)).where(
                Committee.tenant_id == tenant_id,
                Committee.created_at >= start,
                Committee.created_at < end
            )
        ).one()
        
        result.append({
            "month": start.strftime("%Y-%m"),
            "label": start.strftime("%b %Y"),
            "count": count
        })
    
    return result


@router.get("/attendance/by-event")
async def attendance_by_event(
    limit: int = 20,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Asistentes por evento"""
    stats = session.exec(
        select(
            Event.id,
            Event.name,
            Event.event_date,
            func.count(Attendance.id).label("count")
        ).outerjoin(
            Attendance, Attendance.event_id == Event.id
        ).where(
            Event.tenant_id == tenant_id
        ).group_by(
            Event.id, Event.name, Event.event_date
        ).order_by(Event.event_date.desc()).limit(limit)
    ).all()
    
    return [
        {"event_id": s[0], "event_name": s[1], "event_date": s[2], "attendance_count": s[3]}
        for s in stats
    ]


@router.get("/attendance/map-data")
async def attendance_map_data(
    event_id: Optional[int] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Puntos geográficos de asistencia para mapa Leaflet"""
    query = select(
        Attendance.latitude,
        Attendance.longitude,
        Attendance.name,
        Attendance.email,
        Event.name.label("event_name"),
        Event.event_date
    ).join(
        Event, Event.id == Attendance.event_id
    ).where(
        Attendance.tenant_id == tenant_id,
        Attendance.latitude.isnot(None),
        Attendance.longitude.isnot(None)
    )
    
    if event_id:
        query = query.where(Attendance.event_id == event_id)
    
    points = session.exec(query).all()
    
    return [
        {
            "lat": p[0],
            "lng": p[1],
            "name": p[2],
            "email": p[3],
            "event_name": p[4],
            "event_date": p[5]
        }
        for p in points
    ]


@router.get("/surveys/summary")
async def surveys_summary(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Resumen de encuestas"""
    surveys = session.exec(
        select(Survey).where(Survey.tenant_id == tenant_id).order_by(Survey.created_at.desc())
    ).all()
    
    result = []
    for survey in surveys:
        resp_count = session.exec(
            select(func.count(SurveyResponseModel.id)).where(
                SurveyResponseModel.survey_id == survey.id
            )
        ).one()
        
        q_count = session.exec(
            select(func.count(SurveyQuestion.id)).where(
                SurveyQuestion.survey_id == survey.id
            )
        ).one()
        
        result.append({
            "survey_id": survey.id,
            "title": survey.title,
            "is_active": survey.is_active,
            "response_count": resp_count,
            "question_count": q_count,
            "start_date": survey.start_date,
            "end_date": survey.end_date
        })
    
    return result


@router.get("/tree-stats")
async def tree_stats(
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Contadores recursivos por nivel jerárquico"""
    # Obtener unidades raíz (sin padre)
    root_units = session.exec(
        select(AdministrativeUnit).where(
            AdministrativeUnit.tenant_id == tenant_id,
            AdministrativeUnit.parent_id == None
        )
    ).all()
    
    def build_tree_node(unit):
        # Contar comités directos
        committee_count = session.exec(
            select(func.count(Committee.id)).where(
                Committee.administrative_unit_id == unit.id
            )
        ).one()
        
        # Contar miembros directos
        member_count = session.exec(
            select(func.count(CommitteeMember.id)).join(
                Committee, Committee.id == CommitteeMember.committee_id
            ).where(Committee.administrative_unit_id == unit.id)
        ).one()
        
        # Contar usuarios asignados
        user_count = session.exec(
            select(func.count(UserAssignment.id)).where(
                UserAssignment.administrative_unit_id == unit.id
            )
        ).one()
        
        # Hijos recursivos
        children_units = session.exec(
            select(AdministrativeUnit).where(
                AdministrativeUnit.parent_id == unit.id
            )
        ).all()
        
        children = [build_tree_node(child) for child in children_units]
        
        # Sumar stats de hijos
        total_committees = committee_count + sum(c.committee_count for c in children)
        total_members = member_count + sum(c.member_count for c in children)
        total_users = user_count + sum(c.user_count for c in children)
        
        return TreeNodeStats(
            unit_id=unit.id,
            unit_name=unit.name,
            unit_type=unit.unit_type,
            committee_count=total_committees,
            member_count=total_members,
            user_count=total_users,
            children=children
        )
    
    tree = [build_tree_node(unit) for unit in root_units]
    return tree


@router.get("/members/by-referrer")
async def members_by_referrer(
    limit: int = 20,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Promovidos por referente político"""
    stats = session.exec(
        select(
            CommitteeMember.referred_by,
            func.count(CommitteeMember.id).label("count")
        ).where(
            CommitteeMember.tenant_id == tenant_id,
            CommitteeMember.referred_by.isnot(None),
            CommitteeMember.referred_by != ""
        ).group_by(
            CommitteeMember.referred_by
        ).order_by(func.count(CommitteeMember.id).desc()).limit(limit)
    ).all()
    
    return [{"referrer": s[0], "count": s[1]} for s in stats]
