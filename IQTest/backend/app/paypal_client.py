import os
import httpx
import uuid
import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv

logger = logging.getLogger("paypal")

# Cargar variables de entorno desde un archivo .env si existe.
# Busca un .env en la raíz del backend (../.env respecto a este archivo) o, si no, usa búsqueda estándar.
_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
try:
    if os.path.isfile(_ENV_PATH):
        load_dotenv(dotenv_path=_ENV_PATH, override=False)
    else:
        load_dotenv(override=False)
except Exception as e:  # No rompemos la app por un error leve de lectura
    logger.debug("[paypal] No se pudo cargar .env: %s", e)

# Credenciales obligatorias en producción. Si faltan, se lanzará excepción.
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

# Configuración de moneda y monto base (sobre-especificar en lógica real de carrito)
PAYPAL_CURRENCY = os.getenv("PAYPAL_CURRENCY", "MXN")
PAYPAL_AMOUNT = os.getenv("PAYPAL_AMOUNT", "20.00")

# URL de producción (sandbox eliminado para despliegue). Si se requiere sandbox, usar PAYPAL_ENV=sandbox.
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "live").lower()
if PAYPAL_ENV not in {"live", "sandbox"}:  # validación defensiva
    PAYPAL_ENV = "live"
PAYPAL_BASE_URL = "https://api-m.paypal.com" if PAYPAL_ENV == "live" else "https://api-m.sandbox.paypal.com"
PAYPAL_ORDER_URL = f"{PAYPAL_BASE_URL}/v2/checkout/orders"

# Modelos para las peticiones de creación de órdenes
class CartItem(BaseModel):
    id: str
    quantity: int

class OrderRequest(BaseModel):
    cart: List[CartItem]

async def get_access_token() -> str:
    """Obtiene un token de acceso de PayPal.

    Lanza ValueError si faltan credenciales. No hay modo simulación en producción.
    """
    if not (PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET):
        raise ValueError("Credenciales PayPal no configuradas (PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET)")

    auth = httpx.BasicAuth(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "es_MX"}
    data = {"grant_type": "client_credentials"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token", auth=auth, headers=headers, data=data, timeout=30
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as he:
            logger.error("[paypal] Error obteniendo token %s body=%s", he.response.status_code, he.response.text[:400])
            raise
        result = response.json()
        return result["access_token"]

async def verify_payment(order_id: str) -> Dict[str, Any]:
    """Verifica un pago de PayPal usando el ID de la orden.

    Si la orden no está completada se intenta capturar automáticamente.
    """
    access_token = await get_access_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PAYPAL_ORDER_URL}/{order_id}", headers=headers, timeout=30)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as he:
            logger.error("[paypal][verify_payment] HTTP %s body=%s", he.response.status_code, he.response.text[:400])
            raise
        order_details = response.json()
        if order_details.get("status") != "COMPLETED":
            capture_response = await client.post(
                f"{PAYPAL_ORDER_URL}/{order_id}/capture", headers=headers, timeout=30
            )
            try:
                capture_response.raise_for_status()
            except httpx.HTTPStatusError as he:
                logger.error("[paypal][verify_payment->capture] HTTP %s body=%s", he.response.status_code, he.response.text[:400])
                raise
            order_details = capture_response.json()
        return {
            "id": order_details["id"],
            "status": order_details["status"],
            "amount": order_details["purchase_units"][0]["amount"]["value"],
            "currency": order_details["purchase_units"][0]["amount"]["currency_code"],
        }

def _calc_amount_from_cart(cart: List[CartItem]) -> str:
    """Calcula monto total (placeholder). En implementación real sumar precios desde BD.
    De momento retorna PAYPAL_AMOUNT fijo.
    """
    return PAYPAL_AMOUNT

async def create_order(request: OrderRequest) -> Dict[str, Any]:
    """Crea una nueva orden de PayPal (producción)."""
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
                "description": "Test de IQ - Resultados detallados",
            }
        ],
        # En una SPA, estas URLs pueden ser la misma página que maneje estados.
        "application_context": {
            "return_url": os.getenv("PAYPAL_RETURN_URL", "https://example.com/return"),
            "cancel_url": os.getenv("PAYPAL_CANCEL_URL", "https://example.com/cancel"),
        },
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(PAYPAL_ORDER_URL, headers=headers, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as he:
            body_text = he.response.text
            logger.error("[paypal][create_order] HTTP %s body=%s", he.response.status_code, body_text[:500])
            raise
        return response.json()

async def capture_order(order_id: str) -> Dict[str, Any]:
    """Captura una orden de PayPal para completar el pago."""
    access_token = await get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_ORDER_URL}/{order_id}/capture", headers=headers, timeout=30
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as he:
            body_text = he.response.text
            logger.error("[paypal][capture_order] HTTP %s body=%s", he.response.status_code, body_text[:500])
            raise
        capture_details = response.json()
        if "details" in capture_details and capture_details["details"]:
            error_detail = capture_details["details"][0]
            issue = error_detail.get("issue")
            message = error_detail.get("description", "Error desconocido")
            if issue == "INSTRUMENT_DECLINED":
                return {"error": "payment_declined", "message": message, "status": "DECLINED"}
            return {"error": "payment_error", "message": message, "status": "ERROR"}
        return {
            "id": capture_details["id"],
            "status": capture_details["status"],
            "amount": capture_details["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"],
            "currency": capture_details["purchase_units"][0]["payments"]["captures"][0]["amount"]["currency_code"],
            "transaction_id": capture_details["purchase_units"][0]["payments"]["captures"][0]["id"],
            "payer": capture_details.get("payer", {}),
            "full_details": capture_details,
        }

async def paypal_debug_status() -> Dict[str, Any]:  # Conservado para diagnósticos controlados
    return {
        "env": PAYPAL_ENV,
        "client_id_present": bool(PAYPAL_CLIENT_ID),
        "base_url": PAYPAL_BASE_URL,
    }
