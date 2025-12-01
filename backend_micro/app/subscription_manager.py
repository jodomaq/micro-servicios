"""
Subscription management utilities
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .models import User, Subscription, Conversion, PlanType

# Plan configurations
PLAN_CONFIGS = {
    PlanType.BASIC: {
        "conversions": 200,
        "price": 200.00,
        "description": "Plan Básico - 200 conversiones mensuales"
    },
    PlanType.STANDARD: {
        "conversions": 400,
        "price": 300.00,
        "description": "Plan Estándar - 400 conversiones mensuales"
    },
    PlanType.PREMIUM: {
        "conversions": 600,
        "price": 350.00,
        "description": "Plan Premium - 600 conversiones mensuales"
    }
}

def get_plan_config(plan_type: PlanType) -> dict:
    """Get configuration for a plan type"""
    return PLAN_CONFIGS.get(plan_type)

def get_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    """Get user's active subscription"""
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()

def create_subscription(
    db: Session, 
    user_id: int, 
    plan_type: PlanType,
    paypal_subscription_id: Optional[str] = None
) -> Subscription:
    """Create a new subscription for user"""
    config = get_plan_config(plan_type)
    
    # Cancel any existing active subscriptions
    existing = get_active_subscription(db, user_id)
    if existing:
        existing.status = "cancelled"
    
    # Create new subscription
    end_date = datetime.utcnow() + timedelta(days=30)
    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        status="active",
        conversions_limit=config["conversions"],
        conversions_used=0,
        price=config["price"],
        currency="MXN",
        paypal_subscription_id=paypal_subscription_id,
        start_date=datetime.utcnow(),
        end_date=end_date
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    return subscription

def check_conversion_available(db: Session, user: Optional[User]) -> tuple[bool, Optional[Subscription], str]:
    """
    Check if user can perform a conversion.
    Returns: (can_convert, subscription, message)
    """
    if not user:
        # Anonymous users must pay per conversion
        return False, None, "Debes pagar por esta conversión o suscribirte"
    
    # Check for active subscription
    subscription = get_active_subscription(db, user.id)
    
    if not subscription:
        return False, None, "No tienes una suscripción activa. Paga por esta conversión o suscríbete"
    
    # Check if subscription has available conversions
    if subscription.conversions_used >= subscription.conversions_limit:
        return False, subscription, f"Has alcanzado el límite de {subscription.conversions_limit} conversiones este mes"
    
    return True, subscription, "Conversión disponible"

def increment_conversion_count(db: Session, subscription: Subscription):
    """Increment the conversion count for a subscription"""
    subscription.conversions_used += 1
    db.commit()
    db.refresh(subscription)

def get_conversions_remaining(subscription: Optional[Subscription]) -> Optional[int]:
    """Get remaining conversions for a subscription"""
    if not subscription:
        return None
    return subscription.conversions_limit - subscription.conversions_used

def cancel_subscription(db: Session, subscription_id: int, user_id: int):
    """Cancel a subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == user_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    
    subscription.status = "cancelled"
    db.commit()
    db.refresh(subscription)
    
    return subscription

def renew_subscription(db: Session, subscription: Subscription):
    """Renew a subscription for another month"""
    subscription.start_date = datetime.utcnow()
    subscription.end_date = datetime.utcnow() + timedelta(days=30)
    subscription.conversions_used = 0
    subscription.status = "active"
    
    db.commit()
    db.refresh(subscription)
    
    return subscription
