from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PlanTypeEnum(str, Enum):
    """Plan types enum"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    google_id: str
    picture: Optional[str] = None

class UserResponse(UserBase):
    id: int
    google_id: str
    picture: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Subscription schemas
class SubscriptionBase(BaseModel):
    plan_type: PlanTypeEnum

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(SubscriptionBase):
    id: int
    user_id: int
    status: str
    conversions_limit: int
    conversions_used: int
    price: float
    currency: str
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    amount: float
    currency: str = "MXN"

class PaymentCreate(PaymentBase):
    payment_type: str
    description: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: int
    user_id: Optional[int] = None
    payment_type: str
    paypal_order_id: Optional[str] = None
    paypal_subscription_id: Optional[str] = None
    status: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Conversion schemas
class ConversionResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    upload_id: str
    filename: Optional[str] = None
    pages_count: Optional[int] = None
    conversion_method: Optional[str] = None
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Dashboard schemas
class UserDashboard(BaseModel):
    user: UserResponse
    active_subscription: Optional[SubscriptionResponse] = None
    conversions_remaining: Optional[int] = None
    recent_conversions: List[ConversionResponse] = []
    total_conversions: int = 0

# Plan info
class PlanInfo(BaseModel):
    plan_type: PlanTypeEnum
    conversions: int
    price: float
    currency: str = "MXN"
    description: str
