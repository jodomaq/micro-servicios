import io
import os
import json
import logging
from typing import List, Optional, Dict, Any

import pandas as pd

from .converter import _write_excel  # reuse the existing Excel writer

logger = logging.getLogger("converter_ai")


def _extract_pdf_text_by_page(pdf_path: str, max_pages: int = 10) -> List[str]:
    """Extract raw text from each page of the PDF. If pdfplumber fails, raise an error.

    Note: We keep this minimal. The IA will do the parsing; this function only exposes text to the model.
    """
    try:
        import pdfplumber
        texts: List[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:max_pages]:
                txt = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                texts.append(txt)
        return texts
    except Exception as e:
        raise RuntimeError(f"No se pudo leer el PDF: {e}")


def _call_openai_for_rows(pages_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Call OpenAI Chat Completions with the given pages payload and expect strict JSON rows.

    Returns a list of row dicts. Keys allowed (the model may return a subset):
    - Fecha de Operacion
    - Fecha de Cargo
    - Fecha de Liquidacion
    - Descripcion
    - Referencia
    - Cargos
    - Abonos
    - Operacion
    - Liquidacion
    - Monto
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY no está configurado en el entorno.")

    model = os.getenv("OPENAI_QA_MODEL", "anthropic/claude-opus-4.5")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except Exception as e:
        raise RuntimeError(f"No se pudo inicializar OpenAI: {e}")

    system = (
        "Eres un analista de estados de cuenta bancarios. Recibirás texto crudo de un PDF (por páginas). "
        "Debes extraer SOLO los movimientos reales y devolverlos en un JSON ESTRICTO.\n"
        "Requisitos de salida (JSON):\n"
        "- Estructura: {\"rows\": [ ... ]}\n"
        "- Cada elemento de rows es un objeto con estas claves (usa null si no aplica):\n"
        "  Fecha de Operacion, Fecha de Cargo, Fecha de Liquidacion, Descripcion, Referencia, Cargos, Abonos, Operacion, Liquidacion, Monto\n"
        "- No incluyas encabezados, subtítulos, ni textos no transaccionales.\n"
        "- Si ves columnas Cargos/Abonos, usa valores numéricos y calcula Monto como positivo para abonos y negativo para cargos si lo puedes inferir.\n"
        "- Si solo hay un importe por fila, úsalo como Monto (respeta el signo si hay paréntesis o -).\n"
        "- Respeta el contenido: no inventes transacciones."
    )

    user_payload = {
        "instrucciones": (
            "Extrae los movimientos del estado de cuenta. Cada página viene como texto. "
            "Devuelve únicamente JSON válido con la clave 'rows'."
        ),
        "pages": pages_payload,
    }

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=0.1,
    )
    content = resp.choices[0].message.content
    data = json.loads(content)
    rows = data.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("La respuesta de OpenAI no contiene 'rows' válidas.")
    return rows


def convert_pdf_to_excel_ai(pdf_path: str, max_pages: int = 10, pages_per_call: int = 3) -> bytes:
    """IA-only conversion: read PDF, send text to OpenAI, get JSON rows, and build Excel.

    - pdf_path: path to the PDF
    - max_pages: limit number of pages processed
    - pages_per_call: number of pages to group per OpenAI call (avoid token limits)
    """
    pages_text = _extract_pdf_text_by_page(pdf_path, max_pages=max_pages)
    if not pages_text:
        raise ValueError("No se obtuvo texto del PDF.")

    # Build payloads in batches to control token usage
    batched_rows: List[dict] = []
    batch: List[Dict[str, Any]] = []
    for i, txt in enumerate(pages_text, start=1):
        batch.append({"page": i, "text": txt})
        if len(batch) >= pages_per_call:
            try:
                rows = _call_openai_for_rows(batch)
                batched_rows.extend(rows)
            except Exception as e:
                logger.warning("OpenAI fallo en un lote de paginas %s-%s: %s", batch[0]["page"], batch[-1]["page"], e)
            batch = []
    if batch:
        rows = _call_openai_for_rows(batch)
        batched_rows.extend(rows)

    if not batched_rows:
        raise ValueError("La IA no devolvió movimientos. Revisa la calidad del PDF o aumenta max_pages.")

    # Normalize to DataFrame with expected columns; unknown keys are ignored
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

    # Let the shared writer handle coercion and totals
    return _write_excel(df)
