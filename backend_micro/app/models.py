from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class PlanType(enum.Enum):
    """Subscription plan types"""
    BASIC = "basic"      # 200 conversions for $200 MXN
    STANDARD = "standard"  # 400 conversions for $300 MXN
    PREMIUM = "premium"   # 600 conversions for $350 MXN

class User(Base):
    """User model for authentication with Google"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    google_id = Column(String(255), unique=True, index=True)
    picture = Column(String(500))  # Google profile picture URL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    conversions = relationship("Conversion", back_populates="user", cascade="all, delete-orphan")

class Subscription(Base):
    """Subscription model for monthly plans"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    status = Column(String(50), default="active")  # active, cancelled, expired
    conversions_limit = Column(Integer, nullable=False)  # 200, 400, or 600
    conversions_used = Column(Integer, default=0)
    price = Column(Float, nullable=False)  # 200, 300, or 350 MXN
    currency = Column(String(10), default="MXN")
    paypal_subscription_id = Column(String(255))  # PayPal subscription ID
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)  # Monthly renewal
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")

class Payment(Base):
    """Payment model for one-time and subscription payments"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous payments
    payment_type = Column(String(50), nullable=False)  # one_time, subscription
    paypal_order_id = Column(String(255))
    paypal_subscription_id = Column(String(255))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MXN")
    status = Column(String(50), nullable=False)  # completed, pending, failed, refunded
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")

class Conversion(Base):
    """Conversion tracking model"""
    __tablename__ = "conversions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous conversions
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    upload_id = Column(String(255), nullable=False)  # UUID of uploaded file
    filename = Column(String(500))
    file_size = Column(Integer)  # Size in bytes
    pages_count = Column(Integer)
    conversion_method = Column(String(50))  # ai_full, ai_vision, etc.
    success = Column(Boolean, default=True)
    error_message = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversions")
