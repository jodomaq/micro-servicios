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
