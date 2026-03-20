"""
Pydantic schemas para validación y serialización
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ====================================
# ENUMS
# ====================================

class SubscriptionStatusEnum(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class UnitTypeEnum(str, Enum):
    STATE = "STATE"
    REGION = "REGION"
    DISTRICT = "DISTRICT"
    MUNICIPALITY = "MUNICIPALITY"
    SECTION = "SECTION"


# ====================================
# AUTH SCHEMAS
# ====================================

class GoogleAuthRequest(BaseModel):
    """Request para autenticación con Google"""
    token: str
    consent_privacy_policy: bool = True
    consent_terms: bool = True


class MicrosoftAuthRequest(BaseModel):
    """Request para autenticación con Microsoft"""
    access_token: str
    consent_privacy_policy: bool = True
    consent_terms: bool = True


class AuthResponse(BaseModel):
    """Respuesta de autenticación"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"
    tenant: "TenantBasicResponse"


# ====================================
# USER SCHEMAS
# ====================================

class UserResponse(BaseModel):
    """Respuesta con información de usuario"""
    id: int
    tenant_id: int
    email: str
    name: str
    phone: Optional[str] = None
    picture_url: Optional[str] = None
    is_tenant_admin: bool
    is_super_admin: bool
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """Crear usuario (solo para admins)"""
    email: EmailStr
    name: str
    phone: Optional[str] = None
    is_tenant_admin: bool = False


class UserUpdate(BaseModel):
    """Actualizar usuario"""
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


# ====================================
# TENANT SCHEMAS
# ====================================

class TenantBasicResponse(BaseModel):
    """Información básica del tenant"""
    id: int
    name: str
    subdomain: str
    logo_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    subscription_status: str
    max_users: int
    max_committees: int


class TenantResponse(TenantBasicResponse):
    """Información completa del tenant"""
    subscription_expires_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    contact_email: str
    contact_phone: Optional[str] = None
    created_at: datetime


class TenantCreate(BaseModel):
    """Crear tenant"""
    name: str
    subdomain: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    subscription_plan_id: int = 1
    primary_color: str = "#1976d2"
    secondary_color: str = "#dc004e"


class TenantUpdate(BaseModel):
    """Actualizar tenant"""
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


# ====================================
# COMMITTEE TYPE SCHEMAS
# ====================================

class CommitteeTypeCreate(BaseModel):
    """Crear tipo de comité"""
    name: str
    description: Optional[str] = None


class CommitteeTypeResponse(BaseModel):
    """Respuesta con tipo de comité"""
    id: int
    tenant_id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


# ====================================
# ADMINISTRATIVE UNIT SCHEMAS
# ====================================

class AdministrativeUnitCreate(BaseModel):
    """Crear unidad administrativa"""
    name: str
    code: Optional[str] = None
    unit_type: UnitTypeEnum
    parent_id: Optional[int] = None


class AdministrativeUnitResponse(BaseModel):
    """Respuesta con unidad administrativa"""
    id: int
    tenant_id: int
    name: str
    code: Optional[str] = None
    unit_type: str
    parent_id: Optional[int] = None
    created_at: datetime
    
    # Stats (calculados)
    committee_count: Optional[int] = 0
    member_count: Optional[int] = 0
    children: Optional[List["AdministrativeUnitResponse"]] = []


class UserAssignmentCreate(BaseModel):
    """Asignar usuario a unidad administrativa"""
    user_id: int
    administrative_unit_id: int
    role: int  # UserRole enum


class UserAssignmentResponse(BaseModel):
    """Respuesta de asignación"""
    id: int
    user: UserResponse
    administrative_unit: AdministrativeUnitResponse
    role: int
    created_at: datetime


# ====================================
# COMMITTEE SCHEMAS
# ====================================

class CommitteeCreate(BaseModel):
    """Crear comité"""
    name: str
    section_number: Optional[str] = None
    committee_type_id: int
    administrative_unit_id: int
    president_name: str
    president_email: Optional[EmailStr] = None
    president_phone: Optional[str] = None
    president_affiliation_key: Optional[str] = None


class CommitteeUpdate(BaseModel):
    """Actualizar comité"""
    name: Optional[str] = None
    section_number: Optional[str] = None
    committee_type_id: Optional[int] = None
    administrative_unit_id: Optional[int] = None
    president_name: Optional[str] = None
    president_email: Optional[EmailStr] = None
    president_phone: Optional[str] = None
    president_affiliation_key: Optional[str] = None


class CommitteeResponse(BaseModel):
    """Respuesta con comité"""
    id: int
    tenant_id: int
    name: str
    section_number: Optional[str] = None
    committee_type: CommitteeTypeResponse
    administrative_unit: AdministrativeUnitResponse
    president_name: str
    president_email: Optional[str] = None
    president_phone: Optional[str] = None
    president_affiliation_key: Optional[str] = None
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Estadísticas
    member_count: Optional[int] = 0


# ====================================
# COMMITTEE MEMBER SCHEMAS
# ====================================

class CommitteeMemberCreate(BaseModel):
    """Crear integrante de comité"""
    full_name: str
    ine_key: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    section_number: Optional[str] = None
    referred_by: Optional[str] = None
    
    @field_validator('ine_key')
    @classmethod
    def validate_ine_key(cls, v):
        if len(v) < 6:
            raise ValueError('La clave INE debe tener al menos 6 caracteres')
        return v.upper()


class CommitteeMemberUpdate(BaseModel):
    """Actualizar integrante"""
    full_name: Optional[str] = None
    ine_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    section_number: Optional[str] = None
    referred_by: Optional[str] = None


class CommitteeMemberResponse(BaseModel):
    """Respuesta con integrante"""
    id: int
    tenant_id: int
    committee_id: int
    full_name: str
    ine_key: str
    phone: Optional[str] = None
    email: Optional[str] = None
    section_number: Optional[str] = None
    referred_by: Optional[str] = None
    created_at: datetime


# ====================================
# DOCUMENT SCHEMAS
# ====================================

class DocumentUploadResponse(BaseModel):
    """Respuesta de subida de documento"""
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    """Lista de documentos"""
    documents: List[DocumentUploadResponse]
    total: int


# ====================================
# EVENT SCHEMAS
# ====================================

class EventCreate(BaseModel):
    """Crear evento"""
    name: str
    description: Optional[str] = None
    event_date: datetime
    location_name: Optional[str] = None
    administrative_unit_id: Optional[int] = None


class EventResponse(BaseModel):
    """Respuesta con evento"""
    id: int
    tenant_id: int
    name: str
    description: Optional[str] = None
    event_date: datetime
    location_name: Optional[str] = None
    administrative_unit_id: Optional[int] = None
    created_by_user_id: int
    is_active: bool
    created_at: datetime
    
    # Estadísticas
    attendance_count: Optional[int] = 0


# ====================================
# ATTENDANCE SCHEMAS
# ====================================

class AttendanceCreate(BaseModel):
    """Registrar asistencia"""
    provider: str
    provider_token: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[int] = None
    timezone: Optional[str] = None


class AttendanceResponse(BaseModel):
    """Respuesta de asistencia"""
    id: int
    event_id: int
    provider: str
    email: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime


# ====================================
# STATS SCHEMAS  
# ====================================

class DashboardStats(BaseModel):
    """Estadísticas del dashboard"""
    total_committees: int
    total_members: int
    total_users: int
    total_events: int
    total_attendances: int
    committees_by_type: dict
    growth_this_month: dict


# ====================================
# EVENT UPDATE SCHEMA
# ====================================

class EventUpdate(BaseModel):
    """Actualizar evento"""
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location_name: Optional[str] = None
    administrative_unit_id: Optional[int] = None
    is_active: Optional[bool] = None


# ====================================
# SURVEY SCHEMAS
# ====================================

class SurveyQuestionCreate(BaseModel):
    """Crear pregunta de encuesta"""
    question_text: str
    question_type: str = "multiple_choice"  # 'multiple_choice' | 'text' | 'rating'
    options: Optional[str] = None  # JSON string con opciones
    order: int = 0


class SurveyQuestionResponse(BaseModel):
    """Respuesta con pregunta de encuesta"""
    id: int
    survey_id: int
    question_text: str
    question_type: str
    options: Optional[str] = None
    order: int


class SurveyCreate(BaseModel):
    """Crear encuesta"""
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    questions: Optional[List[SurveyQuestionCreate]] = []


class SurveyUpdate(BaseModel):
    """Actualizar encuesta"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SurveyDetailResponse(BaseModel):
    """Respuesta detallada de encuesta"""
    id: int
    tenant_id: int
    title: str
    description: Optional[str] = None
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    questions: List[SurveyQuestionResponse] = []
    response_count: Optional[int] = 0


class SurveyResponseCreate(BaseModel):
    """Registrar respuesta a encuesta"""
    user_email: EmailStr
    section_number: Optional[str] = None
    administrative_unit_id: Optional[int] = None
    answers: str  # JSON string
    device_id: Optional[str] = None


class SurveyResponseSchema(BaseModel):
    """Respuesta del modelo SurveyResponse"""
    id: int
    survey_id: int
    user_email: str
    section_number: Optional[str] = None
    answers: str
    created_at: datetime


# ====================================
# SECCION SCHEMAS
# ====================================

class SeccionCreate(BaseModel):
    """Crear sección electoral"""
    municipio_id: Optional[int] = None
    nombre_municipio: Optional[str] = None
    distrito_id: Optional[int] = None
    nombre_distrito: Optional[str] = None
    distrito_federal: Optional[int] = None
    seccion_numero: str


class SeccionResponse(BaseModel):
    """Respuesta con sección electoral"""
    id: int
    tenant_id: int
    municipio_id: Optional[int] = None
    nombre_municipio: Optional[str] = None
    distrito_id: Optional[int] = None
    nombre_distrito: Optional[str] = None
    distrito_federal: Optional[int] = None
    seccion_numero: str


# ====================================
# SUBSCRIPTION PLAN SCHEMAS
# ====================================

class SubscriptionPlanResponse(BaseModel):
    """Respuesta con plan de suscripción"""
    id: int
    name: str
    max_users: int
    max_committees: int
    max_storage_mb: int
    price_monthly: float
    features: Optional[str] = None
    is_active: bool


# ====================================
# AUDIT LOG SCHEMAS
# ====================================

class AuditLogResponse(BaseModel):
    """Respuesta con log de auditoría"""
    id: int
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


# ====================================
# TENANT REGISTRATION (PUBLIC)
# ====================================

class TenantRegistrationSchema(BaseModel):
    """Registrar nuevo tenant (público)"""
    organization_name: str
    subdomain: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    admin_name: str
    primary_color: str = "#1976d2"
    secondary_color: str = "#dc004e"
    plan_id: int = 1

    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v):
        import re
        if not re.match(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$', v):
            raise ValueError('El subdominio debe tener 3-30 caracteres, solo letras minúsculas, números y guiones')
        return v


class TenantRegistrationResponse(BaseModel):
    """Respuesta al registrar tenant"""
    tenant_id: int
    subdomain: str
    admin_email: str
    message: str


# ====================================
# TREE STATS
# ====================================

class TreeNodeStats(BaseModel):
    """Estadísticas de un nodo del árbol jerárquico"""
    unit_id: int
    unit_name: str
    unit_type: str
    committee_count: int = 0
    member_count: int = 0
    user_count: int = 0
    children: List["TreeNodeStats"] = []


# Enable forward references
AdministrativeUnitResponse.model_rebuild()
TreeNodeStats.model_rebuild()
