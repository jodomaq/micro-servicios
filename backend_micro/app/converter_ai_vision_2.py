"""Advanced PDF bank statement to Excel converter using GPT-4 Vision support.

This module focuses on precision-first extraction combining PyMuPDF text parsing,
OpenAI GPT-4 Vision reasoning, and Pydantic validation to normalise heterogeneous
Mexican bank statement layouts into a consistent ledger structure.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Sequence

import pandas as pd
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from .converter import _write_excel

logger = logging.getLogger("converter_ai_vision_2")


def _strip_markdown_json(text: str) -> str:
    """Remove markdown code block formatting from JSON responses."""
    text = text.strip()
    # Remove ```json at the start
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    # Remove ``` at the end
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class StatementEntry(BaseModel):
    fecha: datetime
    descripcion: str
    referencia: str
    monto: float
    categoria: str
    moneda: Optional[str] = None

    # Normalise date strings to timezone-naive ISO strings
    @field_validator("fecha", mode="before")
    def _parse_fecha(cls, value: object) -> datetime:
        if value in (None, "", "null"):
            raise ValueError("fecha vacía")
        if isinstance(value, datetime):
            return value
        try:
            # dateutil is not a hard dependency; implement simple parser fallback
            from dateutil import parser as dateparser  # type: ignore

            dt = dateparser.parse(str(value), dayfirst=False, yearfirst=False, fuzzy=True)
        except Exception as exc:  # pragma: no cover - guard against parser absence
            raise ValueError(f"no se pudo interpretar la fecha: {value}") from exc
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @field_validator("descripcion", "categoria", mode="before")
    def _clean_string(cls, value: object) -> str:
        text = _clean_str(value)
        if not text:
            raise ValueError("texto requerido")
        return text

    @field_validator("referencia", mode="before")
    def _clean_ref(cls, value: object) -> str:
        text = _clean_str(value)
        if not text:
            # Referencias demasiado ruidosas terminan como string vacío pero obligamos a algo.
            # Se usa placeholder para preservar consistencia del dataframe.
            return "SIN-REF"
        return text

    @field_validator("monto", mode="before")
    def _parse_amount(cls, value: object) -> float:
        amount = _parse_monetary_value(value)
        if amount is None:
            raise ValueError("monto inválido")
        return amount

    @field_validator("moneda", mode="before")
    def _normalize_currency(cls, value: object) -> Optional[str]:
        if value in (None, "", "null"):
            return None
        return _clean_currency(value)

    @model_validator(mode="after")
    def _ensure_cargo_sign(cls, model: "StatementEntry") -> "StatementEntry":
        monto = model.monto
        if monto is None:
            return model
        descripcion = model.descripcion.lower()
        # For cards, cargos frequently labelled "cargo", "retiro", etc.
        if any(token in descripcion for token in ("cargo", "retiro", "compra")) and monto > 0:
            model.monto = -abs(monto)
        if any(token in descripcion for token in ("abono", "deposito", "pago")) and monto < 0:
            model.monto = abs(monto)
        return model


class StatementPayload(BaseModel):
    rows: List[StatementEntry]


@dataclass
class PageContent:
    page_number: int
    text: str
    image_data_url: Optional[str]
    metadata: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_str(value: object) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean_currency(value: object) -> str:
    text = str(value).strip().upper()
    mapping = {
        "M.N.": "MXN",
        "MN": "MXN",
        "MEX": "MXN",
        "$": "MXN",
        "USD$": "USD",
        "US$": "USD",
    }
    return mapping.get(text, re.sub(r"[^A-Z]", "", text) or "MXN")


_AMOUNT_TOKEN = re.compile(r"[+-]?\s*\(?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\s*\)?")
_CURRENCY_HINT = re.compile(r"\b(MXN?|USD|EUR|CAD|GBP|M\.?N\.?|US\$|\$)\b", re.IGNORECASE)


def _parse_monetary_value(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    match = _AMOUNT_TOKEN.search(text)
    if not match:
        match = _AMOUNT_TOKEN.search(text.replace(" ", ""))
    if not match:
        # Allow GPT outputs like "-1234.56 MXN"
        try:
            return float(text)
        except ValueError:
            return None
    token = match.group(0)
    token = token.replace(" ", "")
    token = token.replace(",", "") if token.count(",") and token.count(".") else token.replace(",", ".")
    negative = token.startswith("-") or "(" in token
    clean = token.replace("(", "").replace(")", "").replace("+", "")
    try:
        value_float = float(clean)
    except ValueError:
        return None
    return -abs(value_float) if negative else value_float


def _chunk_pages(pages: Sequence[PageContent], chunk_size: int) -> Iterable[List[PageContent]]:
    batch: List[PageContent] = []
    for page in pages:
        batch.append(page)
        if len(batch) == chunk_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _truncate_for_prompt(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars - 500]
    tail = text[-400:]
    return head + "\n...\n" + tail


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------


def _extract_pdf_content(pdf_path: str, max_pages: Optional[int] = None, dpi: int = 180) -> List[PageContent]:
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - library missing in runtime
        raise RuntimeError("PyMuPDF (fitz) es requerido para la estrategia vision_2") from exc

    pages: List[PageContent] = []
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    limit = min(total_pages, max_pages) if max_pages else total_pages
    for idx in range(limit):
        page = doc[idx]
        text = page.get_text("text") or ""
        try:
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            png_bytes = pix.tobytes("png")
            b64 = base64.b64encode(png_bytes).decode("ascii")
            image_url = f"data:image/png;base64,{b64}"
        except Exception as exc:
            logger.debug("No se pudo renderizar la página %s: %s", idx + 1, exc)
            image_url = None
        currency_hint = None
        match = _CURRENCY_HINT.search(text)
        if match:
            currency_hint = match.group(0).upper()
        pages.append(
            PageContent(
                page_number=idx + 1,
                text=text,
                image_data_url=image_url,
                metadata={
                    "currency_hint": currency_hint,
                    "chars": len(text),
                    "has_tables": bool(page.search_for("Saldo")),
                },
            )
        )
    doc.close()
    if not pages:
        raise ValueError("No se pudo extraer contenido del PDF")
    return pages


# ---------------------------------------------------------------------------
# OpenAI interaction
# ---------------------------------------------------------------------------


def _call_openai_vision(batch: Sequence[PageContent]) -> List[dict]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY no está configurado")
    vision_model = os.getenv("OPENAI_FULL_MODEL", "anthropic/claude-sonnet-4.5")
    temperature = float(os.getenv("OPENAI_VISION_TEMPERATURE", "0.0"))

    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError(f"No se pudo importar OpenAI SDK: {exc}")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/your-org/backend_micro",
            "X-Title": "Bank Statement Converter"
        }
    )

    instructions = {
        "task": "Extraer movimientos bancarios detallados",
        "output_schema": {
            "rows": [
                {
                    "fecha": "YYYY-MM-DD",
                    "descripcion": "texto sin saltos duplicados",
                    "referencia": "alfanumérico",
                    "monto": "numero decimal (negativo cargos / positivo abonos)",
                    "categoria": "clasificación automática",
                    "moneda": "opcional (MXN, USD, etc.)",
                }
            ]
        },
        "rules": [
            "Normaliza todas las fechas a formato ISO local (YYYY-MM-DD)",
            "Unifica descripciones multi-línea en una sola cadena",
            "No inventes transacciones; ignora encabezados, totales y notas",
            "Usa signo negativo en cargos, positivo en abonos",
            "Incluye moneda sólo si se menciona explícitamente",
            "Para referencias largas conserva todo el identificador",
            "Identifica categoría basada en el tipo de movimiento (ej. 'Pago tarjeta', 'ATM', 'Transferencia')",
            "Indica 'categoria': 'Sin clasificar' si no estás seguro",
        ],
    }

    user_content: List[dict] = [
        {
            "type": "text",
            "text": json.dumps(instructions, ensure_ascii=False),
        }
    ]

    for page in batch:
        page_payload = {
            "pagina": page.page_number,
            "texto": _truncate_for_prompt(page.text),
            "pistas": page.metadata,
        }
        user_content.append({"type": "text", "text": json.dumps(page_payload, ensure_ascii=False)})
        if page.image_data_url:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": page.image_data_url},
            })

    try:
        response = client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un analista experto en estados de cuenta mexicanos. "
                        "Devuelve siempre JSON con la clave 'rows'. "
                        "Prioriza precisión sobre velocidad y nunca inventes datos."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            max_tokens=4000,
        )
    except Exception as exc:
        raise RuntimeError(f"Fallo al llamar OpenRouter: {exc}")

    content = response.choices[0].message.content
    logger.debug("OpenRouter response content: %s", content[:500] if content else "EMPTY")
    
    if not content or content.strip() == "":
        raise RuntimeError("OpenRouter devolvió respuesta vacía")

    try:
        content = _strip_markdown_json(content)
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("JSON inválido recibido: %s", content[:1000])
        raise RuntimeError(f"OpenRouter devolvió JSON inválido: {exc}")

    rows = payload.get("rows")
    if not isinstance(rows, list):
        logger.error("Payload recibido sin 'rows': %s", payload)
        raise RuntimeError("La respuesta de OpenRouter no incluye 'rows'")
    return rows


# ---------------------------------------------------------------------------
# Validation / post-processing
# ---------------------------------------------------------------------------


def _validate_rows(raw_rows: Sequence[dict]) -> List[StatementEntry]:
    valid_entries: List[StatementEntry] = []
    for idx, row in enumerate(raw_rows, start=1):
        try:
            entry = StatementEntry(**row)
            valid_entries.append(entry)
        except ValidationError as err:
            logger.debug("Fila descartada (%s): %s", idx, err)
    return valid_entries


def _entries_to_dataframe(entries: Sequence[StatementEntry]) -> pd.DataFrame:
    if not entries:
        raise ValueError("No hay movimientos válidos tras la validación")
    data = []
    for entry in entries:
        row = entry.dict()
        fecha_iso = entry.fecha.strftime("%Y-%m-%d")
        row.update({"fecha": fecha_iso})
        data.append(row)
    df = pd.DataFrame(data)
    df.sort_values(by="fecha", inplace=True)
    df.reset_index(drop=True, inplace=True)
    # Normalise columns and rename to pipeline schema
    df.rename(columns={
        "fecha": "Fecha de Operacion",
        "descripcion": "Descripcion",
        "referencia": "Referencia",
        "monto": "Monto",
        "categoria": "Categoria",
        "moneda": "Moneda",
    }, inplace=True)
    ordered_cols = ["Fecha de Operacion", "Descripcion", "Referencia", "Monto", "Categoria"]
    if "Moneda" in df.columns and df["Moneda"].notna().any():
        ordered_cols.append("Moneda")
    df = df[ordered_cols]
    df["Categoria"].fillna("Sin clasificar", inplace=True)
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def convert_pdf_to_excel_ai_vision_2(
    pdf_path: str,
    *,
    max_pages: Optional[int] = None,
    pages_per_call: int = 2,
) -> bytes:
    """Convert a bank statement PDF into an Excel spreadsheet using GPT-4 Vision.

    Parameters
    ----------
    pdf_path:
        Absolute path to the PDF statement.
    max_pages:
        Optional limit of pages processed, useful for massive statements.
    pages_per_call:
        Controls batching to the OpenAI API to balance token usage vs. context.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")
    if pages_per_call <= 0:
        raise ValueError("pages_per_call debe ser > 0")

    pages = _extract_pdf_content(pdf_path, max_pages=max_pages)

    raw_rows: List[dict] = []
    for batch in _chunk_pages(pages, pages_per_call):
        try:
            batch_rows = _call_openai_vision(batch)
            raw_rows.extend(batch_rows)
        except Exception as exc:
            logger.error("Error procesando batch %s-%s: %s", batch[0].page_number, batch[-1].page_number, exc)
            continue

    if not raw_rows:
        raise ValueError("No se obtuvieron filas desde OpenAI Vision")

    entries = _validate_rows(raw_rows)
    if not entries:
        raise ValueError("Todas las filas fueron inválidas tras validación Pydantic")

    df = _entries_to_dataframe(entries)

    # `original_df` guards: we store a reference view for auditoría si se requiere.
    try:
        original_df = pd.DataFrame(raw_rows)
    except Exception:
        original_df = None

    return _write_excel(df, original_df=original_df)


__all__ = ["convert_pdf_to_excel_ai_vision_2"]
