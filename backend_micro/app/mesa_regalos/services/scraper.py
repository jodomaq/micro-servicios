"""
Servicio de scraping para productos de Mercado Libre México.

Extrae título, imagen y precio de una URL de producto y genera
el enlace de afiliado correspondiente usando ML_CAMP_ID.
"""

from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.mesa_regalos.core.config import settings

# Dominios permitidos para prevenir SSRF
_DOMINIOS_PERMITIDOS = {
    "mercadolibre.com.mx",
    "www.mercadolibre.com.mx",
    "articulo.mercadolibre.com.mx",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-MX,es;q=0.9",
}


class ScraperError(Exception):
    """Error durante el scraping de un producto."""

    pass


def _validar_url(url: str) -> None:
    """Valida que la URL pertenezca a un dominio permitido de Mercado Libre."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ScraperError("La URL debe usar protocolo http o https.")
    if parsed.hostname not in _DOMINIOS_PERMITIDOS:
        raise ScraperError(
            "Solo se permiten URLs de Mercado Libre México (mercadolibre.com.mx)."
        )


def _generar_url_afiliado(url_original: str) -> str:
    """
    Convierte una URL de producto de ML en un enlace de afiliado.

    Formato de redirección del programa de afiliados de Mercado Libre:
    https://www.mercadolibre.com.mx/jm/click?item_id=&matt_tool={CAMP_ID}&redirect_url={URL_ENCODED}
    """
    url_encoded = quote(url_original, safe="")
    camp_id = settings.ML_CAMP_ID
    return (
        f"https://www.mercadolibre.com.mx/jm/click"
        f"?matt_tool={camp_id}"
        f"&matt_word=&matt_source=&matt_campaign_id="
        f"&redirect_url={url_encoded}"
    )


async def scrape_mercadolibre(url: str) -> dict:
    """
    Extrae la información de un producto de Mercado Libre México.

    Args:
        url: URL del producto en mercadolibre.com.mx

    Returns:
        Diccionario con: title, image_url, price, original_url, affiliate_url

    Raises:
        ScraperError: Si la URL no es válida o ocurre un error al extraer datos.
    """
    _validar_url(url)

    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, follow_redirects=True, timeout=15.0
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise ScraperError(f"No se pudo acceder a la URL: {e}") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Extraer og:title
    og_title = soup.find("meta", property="og:title")
    title = og_title["content"].strip() if og_title and og_title.get("content") else None

    # Extraer og:image
    og_image = soup.find("meta", property="og:image")
    image_url = og_image["content"].strip() if og_image and og_image.get("content") else None

    # Extraer precio — intentar múltiples selectores de ML
    price = None

    # Intento 1: meta tag con itemprop="price"
    meta_price = soup.find("meta", attrs={"itemprop": "price"})
    if meta_price and meta_price.get("content"):
        try:
            price = float(meta_price["content"])
        except (ValueError, TypeError):
            pass

    # Intento 2: span con clase de precio de ML
    if price is None:
        price_tag = soup.find("span", class_="andes-money-amount__fraction")
        if price_tag:
            raw = price_tag.get_text(strip=True).replace(",", "").replace(".", "")
            try:
                price = float(raw)
            except (ValueError, TypeError):
                pass

    # Generar URL de afiliado
    affiliate_url = _generar_url_afiliado(url)

    return {
        "title": title,
        "image_url": image_url,
        "price": price,
        "original_url": url,
        "affiliate_url": affiliate_url,
    }
