"""
Subscription routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .database import get_db
from .auth import require_user, get_current_user
from .schemas import (
    SubscriptionCreate, SubscriptionResponse, UserDashboard, 
    ConversionResponse, PlanInfo, PlanTypeEnum
)
from .models import User, Subscription, Conversion, PlanType
from .subscription_manager import (
    get_active_subscription, create_subscription, cancel_subscription,
    get_conversions_remaining, get_plan_config, PLAN_CONFIGS
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.get("/plans", response_model=List[PlanInfo])
async def get_plans():
    """Get available subscription plans"""
    plans = []
    for plan_type, config in PLAN_CONFIGS.items():
        plans.append(PlanInfo(
            plan_type=plan_type.value,
            conversions=config["conversions"],
            price=config["price"],
            description=config["description"]
        ))
    return plans

@router.get("/my-subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get current user's active subscription"""
    subscription = get_active_subscription(db, user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No tienes una suscripción activa")
    return subscription

@router.get("/dashboard", response_model=UserDashboard)
async def get_dashboard(
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Get user dashboard with subscription and conversion stats"""
    subscription = get_active_subscription(db, user.id)
    
    # Get recent conversions
    recent_conversions = db.query(Conversion).filter(
        Conversion.user_id == user.id
    ).order_by(Conversion.created_at.desc()).limit(10).all()
    
    # Get total conversions
    total_conversions = db.query(Conversion).filter(
        Conversion.user_id == user.id
    ).count()
    
    return {
        "user": user,
        "active_subscription": subscription,
        "conversions_remaining": get_conversions_remaining(subscription),
        "recent_conversions": recent_conversions,
        "total_conversions": total_conversions
    }

@router.delete("/{subscription_id}")
async def cancel_my_subscription(
    subscription_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Cancel user's subscription"""
    subscription = cancel_subscription(db, subscription_id, user.id)
    return {"message": "Suscripción cancelada", "subscription": subscription}
