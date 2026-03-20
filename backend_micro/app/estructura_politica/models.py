"""
Modelos de base de datos con SQLModel
Todos los modelos incluyen tenant_id para aislamiento multi-tenant
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ====================================
# ENUMS
# ====================================

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class UnitType(str, Enum):
    STATE = "STATE"
    REGION = "REGION"
    DISTRICT = "DISTRICT"
    MUNICIPALITY = "MUNICIPALITY"
    SECTION = "SECTION"


class UserRole(int, Enum):
    COORDINADOR_ESTATAL = 1
    DELEGADO_REGIONAL = 2
    COORDINADOR_DISTRITAL = 3
    COORDINADOR_MUNICIPAL = 4
    COORDINADOR_SECCIONAL = 5
    PRESIDENTE_COMITE = 6
    CAPTURISTA = 7


class ConsentType(str, Enum):
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"


class ARCORequestType(str, Enum):
    ACCESS = "access"
    RECTIFY = "rectify"
    DELETE = "delete"
    OPPOSE = "oppose"
    PORTABILITY = "portability"


class ARCORequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


# ====================================
# SUBSCRIPTION PLANS
# ====================================

class SubscriptionPlan(SQLModel, table=True):
    """Planes de suscripción disponibles"""
    __tablename__ = "subscription_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, index=True)  # 'Básico', 'Intermedio', 'Premium', 'Enterprise'
    max_users: int = Field(default=5)
    max_committees: int = Field(default=50)
    max_storage_mb: int = Field(default=1024)  # 1 GB
    price_monthly: float = Field(default=499.0)
    features: Optional[str] = Field(default=None)  # JSON string
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tenants: List["Tenant"] = Relationship(back_populates="subscription_plan")


# ====================================
# TENANTS (CLIENTES)
# ====================================

class Tenant(SQLModel, table=True):
    """Cliente/Organización política que usa el sistema"""
    __tablename__ = "tenants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    subdomain: str = Field(max_length=100, unique=True, index=True)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    primary_color: str = Field(default="#1976d2", max_length=7)
    secondary_color: str = Field(default="#dc004e", max_length=7)
    is_active: bool = Field(default=True, index=True)
    
    # Subscription
    subscription_plan_id: int = Field(foreign_key="subscription_plans.id")
    subscription_status: str = Field(default="trial", max_length=20)  # SubscriptionStatus
    subscription_expires_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    
    # PayPal
    paypal_subscription_id: Optional[str] = Field(default=None, max_length=100)
    
    # Limits
    max_users: int = Field(default=5)
    max_committees: int = Field(default=50)
    max_storage_mb: int = Field(default=1024)
    
    # Contact
    contact_email: str = Field(max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    subscription_plan: Optional[SubscriptionPlan] = Relationship(back_populates="tenants")
    users: List["User"] = Relationship(back_populates="tenant")
    administrative_units: List["AdministrativeUnit"] = Relationship(back_populates="tenant")
    committees: List["Committee"] = Relationship(back_populates="tenant")


# ====================================
# USERS
# ====================================

class User(SQLModel, table=True):
    """Usuarios del sistema (vinculados a un tenant)"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    email: str = Field(max_length=200, index=True)  # Único dentro del tenant
    name: str = Field(max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    picture_url: Optional[str] = Field(default=None, max_length=500)
    
    # OAuth providers
    google_id: Optional[str] = Field(default=None, max_length=200)
    microsoft_id: Optional[str] = Field(default=None, max_length=200)
    
    # Roles (pueden tener múltiples roles vía UserAssignment)
    is_tenant_admin: bool = Field(default=False)
    is_super_admin: bool = Field(default=False)  # Super admin del sistema SaaS
    
    # Status
    is_active: bool = Field(default=True, index=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="users")
    assignments: List["UserAssignment"] = Relationship(back_populates="user")
    consents: List["UserConsent"] = Relationship(back_populates="user")
    arco_requests: List["ARCORequest"] = Relationship(back_populates="user")


# ====================================
# ADMINISTRATIVE UNITS (JERARQUÍA)
# ====================================

class AdministrativeUnit(SQLModel, table=True):
    """Unidades administrativas jerárquicas"""
    __tablename__ = "administrative_units"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    name: str = Field(max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)
    unit_type: str = Field(max_length=20, index=True)  # UnitType enum
    parent_id: Optional[int] = Field(default=None, foreign_key="administrative_units.id")
    
    # Referencias opcionales a tabla Seccion
    seccion_municipio_id: Optional[int] = None
    seccion_distrito_id: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="administrative_units")
    assignments: List["UserAssignment"] = Relationship(back_populates="administrative_unit")
    committees: List["Committee"] = Relationship(back_populates="administrative_unit")


# ====================================
# USER ASSIGNMENTS (ROLES EN JERARQUÍA)
# ====================================

class UserAssignment(SQLModel, table=True):
    """Asignación de usuarios a unidades administrativas con roles"""
    __tablename__ = "user_assignments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    administrative_unit_id: int = Field(foreign_key="administrative_units.id", index=True)
    
    role: int = Field(default=7)  # UserRole enum
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="assignments")
    administrative_unit: Optional[AdministrativeUnit] = Relationship(back_populates="assignments")


# ====================================
# COMMITTEE TYPES
# ====================================

class CommitteeType(SQLModel, table=True):
    """Tipos de comité configurables por tenant"""
    __tablename__ = "committee_types"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    committees: List["Committee"] = Relationship(back_populates="committee_type")


# ====================================
# COMMITTEES
# ====================================

class Committee(SQLModel, table=True):
    """Comités registrados"""
    __tablename__ = "committees"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    name: str = Field(max_length=200)
    section_number: Optional[str] = Field(default=None, max_length=50)
    committee_type_id: int = Field(foreign_key="committee_types.id")
    administrative_unit_id: int = Field(foreign_key="administrative_units.id", index=True)
    
    # Datos del presidente
    president_name: str = Field(max_length=200)
    president_email: Optional[str] = Field(default=None, max_length=200)
    president_phone: Optional[str] = Field(default=None, max_length=20)
    president_affiliation_key: Optional[str] = Field(default=None, max_length=50)
    
    # Usuario responsable que creó el comité
    created_by_user_id: int = Field(foreign_key="users.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="committees")
    committee_type: Optional[CommitteeType] = Relationship(back_populates="committees")
    administrative_unit: Optional[AdministrativeUnit] = Relationship(back_populates="committees")
    members: List["CommitteeMember"] = Relationship(back_populates="committee")
    documents: List["CommitteeDocument"] = Relationship(back_populates="committee")


# ====================================
# COMMITTEE MEMBERS
# ====================================

class CommitteeMember(SQLModel, table=True):
    """Integrantes de comités (hasta 10 por comité)"""
    __tablename__ = "committee_members"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    committee_id: int = Field(foreign_key="committees.id", index=True)
    
    full_name: str = Field(max_length=200)
    ine_key: str = Field(max_length=50, index=True)  # Único
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    section_number: Optional[str] = Field(default=None, max_length=50)
    referred_by: Optional[str] = Field(default=None, max_length=200)  # Político que lo invitó
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    committee: Optional[Committee] = Relationship(back_populates="members")


# ====================================
# COMMITTEE DOCUMENTS
# ====================================

class CommitteeDocument(SQLModel, table=True):
    """Documentos subidos por comité"""
    __tablename__ = "committee_documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    committee_id: int = Field(foreign_key="committees.id", index=True)
    
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(default=0)  # bytes
    mime_type: Optional[str] = Field(default=None, max_length=100)
    
    uploaded_by_user_id: int = Field(foreign_key="users.id")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    committee: Optional[Committee] = Relationship(back_populates="documents")


# ====================================
# EVENTS
# ====================================

class Event(SQLModel, table=True):
    """Eventos para registro de asistencia"""
    __tablename__ = "events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    event_date: datetime
    location_name: Optional[str] = Field(default=None, max_length=200)
    administrative_unit_id: Optional[int] = Field(default=None, foreign_key="administrative_units.id")
    
    created_by_user_id: int = Field(foreign_key="users.id")
    is_active: bool = Field(default=True, index=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    attendances: List["Attendance"] = Relationship(back_populates="event")


# ====================================
# ATTENDANCE
# ====================================

class Attendance(SQLModel, table=True):
    """Registro de asistencia a eventos"""
    __tablename__ = "attendances"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    
    provider: str = Field(max_length=20)  # 'google' | 'microsoft'
    provider_user_id: str = Field(max_length=200)
    email: str = Field(max_length=200)
    name: str = Field(max_length=200)
    
    # Tracking
    device_id: Optional[str] = Field(default=None, max_length=200)
    user_agent: Optional[str] = Field(default=None)
    ip: Optional[str] = Field(default=None, max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[int] = None
    timezone: Optional[str] = Field(default=None, max_length=50)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    event: Optional[Event] = Relationship(back_populates="attendances")


# ====================================
# SURVEYS
# ====================================

class Survey(SQLModel, table=True):
    """Encuestas"""
    __tablename__ = "surveys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    title: str = Field(max_length=200)
    description: Optional[str] = None
    is_active: bool = Field(default=True, index=True)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    questions: List["SurveyQuestion"] = Relationship(back_populates="survey")
    responses: List["SurveyResponse"] = Relationship(back_populates="survey")


class SurveyQuestion(SQLModel, table=True):
    """Preguntas de encuesta"""
    __tablename__ = "survey_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    survey_id: int = Field(foreign_key="surveys.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    question_text: str
    question_type: str = Field(max_length=50)  # 'multiple_choice' | 'text' | 'rating'
    options: Optional[str] = None  # JSON
    order: int = Field(default=0)
    
    # Relationships
    survey: Optional[Survey] = Relationship(back_populates="questions")


class SurveyResponse(SQLModel, table=True):
    """Respuestas a encuestas"""
    __tablename__ = "survey_responses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    survey_id: int = Field(foreign_key="surveys.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    user_email: str = Field(max_length=200)
    section_number: Optional[str] = Field(default=None, max_length=50)
    administrative_unit_id: Optional[int] = Field(default=None, foreign_key="administrative_units.id")
    
    answers: str  # JSON
    device_id: Optional[str] = Field(default=None, max_length=200)
    ip: Optional[str] = Field(default=None, max_length=50)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    survey: Optional[Survey] = Relationship(back_populates="responses")


# ====================================
# PAYMENTS
# ====================================

class Payment(SQLModel, table=True):
    """Historial de pagos"""
    __tablename__ = "payments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", index=True)
    
    paypal_order_id: Optional[str] = Field(default=None, max_length=100)
    paypal_payer_id: Optional[str] = Field(default=None, max_length=100)
    paypal_subscription_id: Optional[str] = Field(default=None, max_length=100)
    
    amount: float
    currency: str = Field(default="MXN", max_length=3)
    status: str = Field(max_length=20, index=True)  # PaymentStatus
    payment_method: str = Field(default="paypal", max_length=50)
    
    plan_id: Optional[int] = Field(default=None, foreign_key="subscription_plans.id")
    payment_date: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class PaymentWebhookLog(SQLModel, table=True):
    """Log de webhooks de PayPal"""
    __tablename__ = "payment_webhook_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    webhook_event_id: str = Field(max_length=100, unique=True)
    event_type: str = Field(max_length=100, index=True)
    payload: str  # JSON completo del webhook
    processed: bool = Field(default=False, index=True)
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ====================================
# USER CONSENTS (GDPR/LGPD)
# ====================================

class UserConsent(SQLModel, table=True):
    """Registro de consentimientos de usuarios"""
    __tablename__ = "user_consents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    consent_type: str = Field(max_length=50)  # ConsentType
    consent_given: bool = Field(default=True)
    consent_text: Optional[str] = None  # Versión del texto aceptado
    consent_version: str = Field(max_length=10)
    
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = None
    
    consented_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="consents")


# ====================================
# ARCO REQUESTS
# ====================================

class ARCORequest(SQLModel, table=True):
    """Solicitudes de derechos ARCO"""
    __tablename__ = "arco_requests"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    request_type: str = Field(max_length=20)  # ARCORequestType
    status: str = Field(default="pending", max_length=20)  # ARCORequestStatus
    details: Optional[str] = None
    response: Optional[str] = None
    
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="arco_requests")


# ====================================
# AUDIT LOG
# ====================================

class AuditLog(SQLModel, table=True):
    """Log de auditoría de acciones"""
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", index=True)
    
    action: str = Field(max_length=100)  # 'login', 'data_access', 'data_modification', 'data_deletion'
    resource_type: Optional[str] = Field(default=None, max_length=50)
    resource_id: Optional[int] = None
    details: Optional[str] = None
    
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# ====================================
# SECCION (CATÁLOGO ELECTORAL)
# ====================================

class Seccion(SQLModel, table=True):
    """Catálogo de secciones electorales (opcional)"""
    __tablename__ = "secciones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    
    municipio_id: Optional[int] = None
    nombre_municipio: Optional[str] = Field(default=None, max_length=200)
    distrito_id: Optional[int] = None
    nombre_distrito: Optional[str] = Field(default=None, max_length=200)
    distrito_federal: Optional[int] = None
    seccion_numero: str = Field(max_length=50, index=True)
