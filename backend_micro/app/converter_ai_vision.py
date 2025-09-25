import os
import io
import json
import base64
import logging
from typing import List, Dict, Any, Optional

import pandas as pd

from .converter import _write_excel  # reutilizamos el writer existente

logger = logging.getLogger("converter_ai_vision")


# =============================
# Extracción de texto enriquecida
# =============================
def _extract_pdf_text_by_page_enriched(pdf_path: str, max_pages: int = 10) -> List[Dict[str, Any]]:
    """Extrae texto y métricas heurísticas por página usando pdfplumber.

    Métricas:
      - numeric_ratio: proporción de dígitos respecto al total de caracteres
      - date_hits: nº de patrones de fecha simples (dd/mm o dd-mmm)
      - has_currency: presencia de símbolos de moneda (mxn, usd, $)
    """
    import re
    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        raise RuntimeError(f"pdfplumber no disponible: {e}")

    date_re = re.compile(r"\b\d{1,2}[/-](?:\d{1,2}|[A-Za-z]{3,})[/-]\d{2,4}\b")
    currency_re = re.compile(r"[$]|USD|MXN", re.IGNORECASE)

    pages: List[Dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages[:max_pages], start=1):
            txt = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            total_chars = len(txt) or 1
            digit_chars = sum(c.isdigit() for c in txt)
            numeric_ratio = digit_chars / total_chars
            date_hits = len(date_re.findall(txt))
            has_currency = bool(currency_re.search(txt))
            pages.append({
                "page": idx,
                "text": txt,
                "numeric_ratio": numeric_ratio,
                "date_hits": date_hits,
                "has_currency": has_currency,
            })
    return pages


def _select_financial_pages(pages: List[Dict[str, Any]],
                            min_numeric_ratio: float = 0.08,
                            min_date_hits: int = 1) -> List[Dict[str, Any]]:
    """Filtra páginas candidatas a contener movimientos.

    Regla: se mantiene la página si cumple alguno:
      - numeric_ratio >= min_numeric_ratio
      - date_hits >= min_date_hits
      - has_currency True
    Si ninguna pasa el filtro, devolvemos todas para evitar perder información.
    """
    selected = [p for p in pages if (
        p.get("numeric_ratio", 0) >= min_numeric_ratio
        or p.get("date_hits", 0) >= min_date_hits
        or p.get("has_currency")
    )]
    return selected or pages


# =============================
# Renderizado de página a imagen (para visión)
# =============================
def _render_page_image_base64(pdf_path: str, page_number_1based: int, dpi: int = 150) -> Optional[str]:
    """Renderiza una página a PNG y la devuelve como data URL base64.

    Si PyMuPDF (pymupdf) no está instalado y la página necesita visión, devolvemos None.
    """
    try:
        import fitz  # type: ignore
    except Exception:
        logger.info("PyMuPDF no instalado; se omiten imágenes para visión.")
        return None

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_number_1based - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png_bytes = pix.tobytes("png")
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logger.warning("No se pudo renderizar página %s: %s", page_number_1based, e)
        return None


# =============================
# Llamada a OpenAI
# =============================
def _call_openai_for_rows_vision(
    pages_payload: List[Dict[str, Any]],
    image_data_urls: Optional[List[str]] = None,
    force_vision: bool = False,
    model_text: str = "gpt-4o-mini",
    model_vision: str = "gpt-4o-mini"  # gpt-4o-mini soporta visión; ajustar si se usa otro modelo
) -> List[Dict[str, Any]]:
    """Invoca OpenAI combinando texto (pages_payload) y opcionalmente imágenes.

    Emplea el endpoint de chat.completions para mantener consistencia con el código actual.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurado.")

    # Import dinámico para seguir el patrón del proyecto
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError(f"No se pudo importar OpenAI SDK: {e}")

    client = OpenAI(api_key=api_key)

    use_vision = force_vision or (image_data_urls and len(image_data_urls) > 0)
    model = model_vision if use_vision else model_text

    system = (
        "Eres un analista de estados de cuenta. Devuelves SOLO JSON estricto {\"rows\":[...]}. "
        "No inventes datos. Normaliza fechas a YYYY-MM-DD si es posible; si no, null. "
        "Si hay columnas Cargos/Abonos calcula Monto = Abonos - Cargos (negativo para cargos si procede)."
    )

    # Construimos el bloque de contenido del usuario
    user_content: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": json.dumps({
                "instrucciones": "Extrae movimientos reales. Ignora encabezados y totales de resumen duplicados.",
                "pages": pages_payload,
            }, ensure_ascii=False)
        }
    ]

    if use_vision and image_data_urls:
        for data_url in image_data_urls:
            # Estructura esperada: {"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}
            user_content.append({
                "type": "image_url",
                "image_url": {"url": data_url}
            })

    try:
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )
        content = resp.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Error llamando a OpenAI: {e}")

    try:
        data = json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Respuesta no es JSON válido: {e}")

    rows = data.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("La respuesta de OpenAI no contiene 'rows' válidas.")
    return rows


# =============================
# Función principal pública
# =============================
def convert_pdf_to_excel_ai_vision(
    pdf_path: str,
    max_pages: int = 10,
    pages_per_call: int = 3,
    heuristic_filter: bool = True,
    use_vision_for_low_conf: bool = True,
    low_conf_numeric_ratio: float = 0.04,
) -> bytes:
    """Convierte un estado de cuenta PDF a Excel usando IA con heurísticas y visión opcional.

    Pasos:
      1. Extrae texto enriquecido por página.
      2. Filtra páginas financieras (heurística) si heuristic_filter=True.
      3. Agrupa en lotes de pages_per_call para controlar tokens.
      4. Si alguna página del lote tiene numeric_ratio < low_conf_numeric_ratio y use_vision_for_low_conf=True,
         renderiza imagen y llama al modelo con soporte de visión.
      5. Ensambla DataFrame canonizado y escribe Excel reutilizando _write_excel.
    """
    pages = _extract_pdf_text_by_page_enriched(pdf_path, max_pages=max_pages)
    if not pages:
        raise ValueError("No se obtuvo texto del PDF.")

    if heuristic_filter:
        pages = _select_financial_pages(pages)

    batched_rows: List[Dict[str, Any]] = []
    batch: List[Dict[str, Any]] = []

    def flush_batch():
        nonlocal batch, batched_rows
        if not batch:
            return
        # Determinar si alguna página necesita visión
        needs_vision = False
        images: List[str] = []
        if use_vision_for_low_conf:
            for p in batch:
                if p.get("numeric_ratio", 0) < low_conf_numeric_ratio:
                    needs_vision = True
                    data_url = _render_page_image_base64(pdf_path, p["page"])  # puede devolver None
                    if data_url:
                        images.append(data_url)

        try:
            rows = _call_openai_for_rows_vision(
                pages_payload=[{"page": p["page"], "text": p["text"]} for p in batch],
                image_data_urls=images if needs_vision and images else None,
                force_vision=needs_vision,
            )
            batched_rows.extend(rows)
        except Exception as e:
            logger.warning(
                "OpenAI falló lote %s-%s: %s",
                batch[0]["page"], batch[-1]["page"], e
            )
        batch = []

    for p in pages:
        batch.append(p)
        if len(batch) >= pages_per_call:
            flush_batch()

    if batch:
        flush_batch()

    if not batched_rows:
        raise ValueError("La IA no devolvió movimientos. Revisa la calidad del PDF o parámetros.")

    # Normalizamos columnas esperadas
    cols = [
        "Fecha de Operacion", "Fecha de Cargo", "Fecha de Liquidacion",
        "Descripcion", "Referencia", "Cargos", "Abonos",
        "Operacion", "Liquidacion", "Monto",
    ]
    df = pd.DataFrame(batched_rows)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]

    return _write_excel(df)


__all__ = ["convert_pdf_to_excel_ai_vision"]
