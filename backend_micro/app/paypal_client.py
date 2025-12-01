import os
import httpx
import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv

logger = logging.getLogger("paypal")

# Load .env from repo root if available
try:
    load_dotenv(override=False)
except Exception:
    pass

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_CURRENCY = os.getenv("PAYPAL_CURRENCY", "MXN")
PAYPAL_AMOUNT = os.getenv("PAYPAL_AMOUNT", "20.00")
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "live").lower()
if PAYPAL_ENV not in {"live", "sandbox"}:
    PAYPAL_ENV = "live"
PAYPAL_BASE_URL = "https://api-m.paypal.com" if PAYPAL_ENV == "live" else "https://api-m.sandbox.paypal.com"
PAYPAL_ORDER_URL = f"{PAYPAL_BASE_URL}/v2/checkout/orders"


class CartItem(BaseModel):
    id: str
    quantity: int = 1


class OrderRequest(BaseModel):
    cart: List[CartItem]


async def get_access_token() -> str:
    if not (PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET):
        raise ValueError("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET not configured")
    auth = httpx.BasicAuth(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "es_MX"}
    data = {"grant_type": "client_credentials"}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{PAYPAL_BASE_URL}/v1/oauth2/token", auth=auth, headers=headers, data=data, timeout=30)
        r.raise_for_status()
        return r.json()["access_token"]


def _calc_amount_from_cart(cart: List[CartItem]) -> str:
    # Flat price for conversion service
    return PAYPAL_AMOUNT


async def create_order(request: OrderRequest) -> Dict[str, Any]:
    access_token = await get_access_token()
    amount = _calc_amount_from_cart(request.cart)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": PAYPAL_CURRENCY, "value": amount},
                "description": "Conversión de estado de cuenta a Excel",
            }
        ],
        "application_context": {
            "return_url": os.getenv("PAYPAL_RETURN_URL", "https://example.com/return"),
            "cancel_url": os.getenv("PAYPAL_CANCEL_URL", "https://example.com/cancel"),
        },
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(PAYPAL_ORDER_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()


async def capture_order(order_id: str) -> Dict[str, Any]:
    access_token = await get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{PAYPAL_ORDER_URL}/{order_id}/capture", headers=headers, timeout=30)
        r.raise_for_status()
        details = r.json()
        # normalize
        try:
            capture = details["purchase_units"][0]["payments"]["captures"][0]
            return {
                "id": details.get("id"),
                "status": details.get("status"),
                "amount": capture["amount"]["value"],
                "currency": capture["amount"]["currency_code"],
                "transaction_id": capture.get("id"),
                "payer": details.get("payer", {}),
                "full_details": details,
            }
        except Exception:
            return {"status": details.get("status", "UNKNOWN"), "full_details": details}


# Subscription functions
async def create_subscription_plan(plan_name: str, amount: str) -> Dict[str, Any]:
    """Create a PayPal subscription plan (product + billing plan)"""
    access_token = await get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    # Create product
    product_payload = {
        "name": plan_name,
        "description": f"Suscripción mensual: {plan_name}",
        "type": "SERVICE",
        "category": "SOFTWARE"
    }
    
    async with httpx.AsyncClient() as client:
        # Create product
        product_response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/catalogs/products",
            headers=headers,
            json=product_payload,
            timeout=30
        )
        product_response.raise_for_status()
        product_data = product_response.json()
        product_id = product_data["id"]
        
        # Create billing plan
        plan_payload = {
            "product_id": product_id,
            "name": plan_name,
            "description": f"Suscripción mensual: {plan_name}",
            "billing_cycles": [
                {
                    "frequency": {
                        "interval_unit": "MONTH",
                        "interval_count": 1
                    },
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,  # Infinite
                    "pricing_scheme": {
                        "fixed_price": {
                            "value": amount,
                            "currency_code": PAYPAL_CURRENCY
                        }
                    }
                }
            ],
            "payment_preferences": {
                "auto_bill_outstanding": True,
                "payment_failure_threshold": 3
            }
        }
        
        plan_response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/billing/plans",
            headers=headers,
            json=plan_payload,
            timeout=30
        )
        plan_response.raise_for_status()
        return plan_response.json()


async def create_subscription(plan_name: str, amount: str) -> Dict[str, Any]:
    """Create a PayPal subscription"""
    # For simplicity, we'll create a new plan each time
    # In production, you'd want to cache/reuse plan IDs
    plan_data = await create_subscription_plan(plan_name, amount)
    plan_id = plan_data["id"]
    
    access_token = await get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    
    subscription_payload = {
        "plan_id": plan_id,
        "application_context": {
            "brand_name": "Excel Converter",
            "locale": "es-MX",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "SUBSCRIBE_NOW",
            "return_url": os.getenv("PAYPAL_RETURN_URL", "https://example.com/return"),
            "cancel_url": os.getenv("PAYPAL_CANCEL_URL", "https://example.com/cancel"),
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/billing/subscriptions",
            headers=headers,
            json=subscription_payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()


async def get_subscription_details(subscription_id: str) -> Dict[str, Any]:
    """Get PayPal subscription details"""
    access_token = await get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()


async def cancel_subscription(subscription_id: str, reason: str = "User requested cancellation") -> Dict[str, Any]:
    """Cancel a PayPal subscription"""
    access_token = await get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    payload = {
        "reason": reason
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}/cancel",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return {"status": "cancelled"}
