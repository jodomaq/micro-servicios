"""
Servicio de integración con PayPal REST API para suscripciones Premium.

Funcionalidades:
- Obtener Access Token (OAuth2 Client Credentials)
- Crear enlace de suscripción para un usuario
- Procesar webhook de activación de suscripción
"""

import logging

import httpx
from sqlalchemy.orm import Session

from app.mesa_regalos.core.config import settings
from app.mesa_regalos.models.models import User

logger = logging.getLogger(__name__)


class PayPalError(Exception):
    """Error durante la comunicación con PayPal."""

    pass


async def get_access_token() -> str:
    """
    Obtiene un Access Token de PayPal usando Client Credentials (OAuth2).

    Returns:
        Token de acceso válido para realizar llamadas a la API de PayPal.

    Raises:
        PayPalError: Si no se puede obtener el token.
    """
    url = f"{settings.paypal_base_url}/v1/oauth2/token"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data={"grant_type": "client_credentials"},
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise PayPalError(f"No se pudo obtener el token de PayPal: {e}") from e

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise PayPalError("La respuesta de PayPal no contiene access_token.")

    return access_token


async def create_subscription_link(user_id: int) -> str:
    """
    Crea una suscripción en PayPal y devuelve la URL de aprobación.

    El usuario será redirigido a esta URL para completar el pago.
    Al finalizar, PayPal lo enviará de regreso a la URL de éxito.

    Args:
        user_id: ID del usuario que se suscribe.

    Returns:
        URL de aprobación de PayPal donde el usuario completa el pago.

    Raises:
        PayPalError: Si no se puede crear la suscripción.
    """
    token = await get_access_token()
    url = f"{settings.paypal_base_url}/v1/billing/subscriptions"

    payload = {
        "plan_id": settings.PAYPAL_PLAN_ID,
        "application_context": {
            "brand_name": "Mesa de Regalos",
            "locale": "es-MX",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "SUBSCRIBE_NOW",
            "return_url": f"{settings.FRONTEND_URL}/exito?user_id={user_id}",
            "cancel_url": f"{settings.FRONTEND_URL}/cancelado",
        },
        "custom_id": str(user_id),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise PayPalError(f"No se pudo crear la suscripción en PayPal: {e}") from e

    data = response.json()

    # Buscar el link de aprobación en la respuesta
    for link in data.get("links", []):
        if link.get("rel") == "approve":
            return link["href"]

    raise PayPalError("No se encontró la URL de aprobación en la respuesta de PayPal.")


def process_webhook(payload: dict, db: Session) -> None:
    """
    Procesa un evento de webhook de PayPal.

    Cuando se recibe un evento de tipo BILLING.SUBSCRIPTION.ACTIVATED,
    se actualiza el usuario correspondiente a is_premium = True.

    Args:
        payload: Cuerpo del evento de webhook enviado por PayPal.
        db: Sesión de base de datos.

    Nota:
        En producción, se debe verificar la firma del webhook antes de procesar.
        Ver: https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature
    """
    event_type = payload.get("event_type", "")

    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        resource = payload.get("resource", {})
        subscription_id = resource.get("id")
        custom_id = resource.get("custom_id")  # user_id que enviamos al crear

        if not custom_id:
            logger.warning("Webhook de PayPal sin custom_id: %s", subscription_id)
            return

        try:
            user_id = int(custom_id)
        except (ValueError, TypeError):
            logger.error("custom_id inválido en webhook de PayPal: %s", custom_id)
            return

        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_premium = True
            user.paypal_subscription_id = subscription_id
            db.commit()
            logger.info(
                "Usuario %s activado como Premium (suscripción: %s)",
                user_id,
                subscription_id,
            )
        else:
            logger.warning(
                "Usuario %s no encontrado al procesar webhook de PayPal", user_id
            )

    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        resource = payload.get("resource", {})
        custom_id = resource.get("custom_id")

        if custom_id:
            try:
                user_id = int(custom_id)
            except (ValueError, TypeError):
                return

            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.is_premium = False
                db.commit()
                logger.info("Suscripción cancelada para usuario %s", user_id)
