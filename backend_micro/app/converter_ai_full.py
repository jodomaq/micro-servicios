"""
converter_ai_full.py — Conversión IA completa de estados de cuenta PDF → Excel

Estrategia:
  1. Gemini (si GEMINI_API_KEY disponible): envía el PDF visualmente, máxima fidelidad.
  2. OpenRouter/Claude (fallback): texto extraído con posiciones X preservadas mediante
     reconstrucción columnar, eliminando la ambigüedad Cargos/Abonos.

Bug histórico corregido: extract_text() colapsaba las columnas numéricas y el modelo
no podía distinguir Cargo de Abono. Ahora se usa extract_words() + agrupamiento por Y
para reconstruir cada fila con alineación X fija (~80 chars por línea).
"""
import os
import json
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from .converter import _write_excel

logger = logging.getLogger("converter_ai_full")

ALLOWED_COLUMNS = [
    "Fecha de Operacion", "Descripcion", "Referencia",
    "Categoria", "Cargos", "Abonos", "Monto",
]
MANDATORY_COLUMNS = {"Categoria"}

# ─────────────────────────────────────────────
# Helpers de normalización
# ─────────────────────────────────────────────

def _strip_markdown_json(text: str) -> str:
    text = text.strip()
    for prefix in ("```json", "```"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _normalize_amount(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    s = s.replace(" ", "").replace("$", "")
    # Detectar separadores de miles vs decimal
    if s.count(",") > 1 or (s.count(",") == 1 and s.count(".") >= 1):
        # Coma = miles, punto = decimal  →  1,234.56
        s = s.replace(",", "")
    elif s.count(".") > 1:
        # Punto = miles, coma = decimal  →  1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif s.count(",") == 1 and s.count(".") == 0:
        # Solo coma: puede ser decimal  →  1234,56
        s = s.replace(",", ".")
    try:
        num = float(s)
        return -num if neg else num
    except Exception:
        return None


def _normalize_date(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or len(s) < 4:
        return None
    try:
        from dateutil import parser as dateparser  # type: ignore
        dt = dateparser.parse(s, dayfirst=True, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


# ─────────────────────────────────────────────
# Extracción espacial de texto
# ─────────────────────────────────────────────

def _page_to_columnar_text(page, chars_per_line: int = 90) -> str:
    """Reconstruye el texto de una página preservando la alineación de columnas.

    Usa `extract_words()` para obtener cada palabra con su posición X.
    Agrupa palabras por fila (Y cercano) y las coloca en posiciones de carácter
    proporcionales al ancho de la página.  El resultado es texto con espaciado
    fijo que el modelo puede leer como una tabla ASCII.

    Ejemplo de salida:
        Fecha       Descripción               Cargos      Abonos     Saldo
        15/01       Compra Amazon           1,500.00                8,500.00
        16/01       Depósito nómina                    5,000.00    13,500.00

    Con esto el modelo puede inferir que 1,500.00 está en la columna Cargos
    (misma X que el encabezado "Cargos") y 5,000.00 en Abonos.
    """
    try:
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            extra_attrs=["fontname", "size"],
        )
    except Exception:
        words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)

    if not words:
        return page.extract_text(x_tolerance=2, y_tolerance=2) or ""

    if len(words) < 5:
        # Muy pocas palabras — usar extracción plana para no perder contexto
        logger.debug("Página con %d palabras, usando extract_text como fallback", len(words))
        return page.extract_text(x_tolerance=2, y_tolerance=2) or ""

    page_width: float = float(page.width) if page.width else 600.0
    char_w: float = page_width / chars_per_line  # puntos por carácter

    # Agrupar por fila: round(top / y_tol) * y_tol con tolerancia de 4pt
    Y_TOL = 4.0
    rows: Dict[int, List[dict]] = defaultdict(list)
    for w in words:
        key = int(round(w["top"] / Y_TOL))
        rows[key].append(w)

    lines: List[str] = []
    for key in sorted(rows.keys()):
        row_words = sorted(rows[key], key=lambda w: w["x0"])
        buf = [" "] * chars_per_line
        for w in row_words:
            col = int(w["x0"] / char_w)
            col = max(0, min(col, chars_per_line - 1))
            text = w["text"]
            end = min(col + len(text), chars_per_line)
            for i, ch in enumerate(text[: end - col]):
                buf[col + i] = ch
        line = "".join(buf).rstrip()
        if line.strip():
            lines.append(line)

    return "\n".join(lines)


def _extract_pages_columnar(pdf_path: str, max_pages: int = 10) -> List[Dict[str, Any]]:
    """Extrae todas las páginas como texto columnar y añade métricas de relevancia."""
    import re

    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        raise RuntimeError(f"pdfplumber no disponible: {e}")

    date_re = re.compile(r"\b\d{1,2}[/\-](?:\d{1,2}|[A-Za-z]{3,})")
    amount_re = re.compile(r"\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})\b")

    pages: List[Dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages[:max_pages], start=1):
            txt = _page_to_columnar_text(page)
            date_hits = len(date_re.findall(txt))
            amount_hits = len(amount_re.findall(txt))
            pages.append({
                "page": idx,
                "text": txt,
                "date_hits": date_hits,
                "amount_hits": amount_hits,
            })

    return pages


# ─────────────────────────────────────────────
# Prompt del modelo
# ─────────────────────────────────────────────

_SYSTEM_PROMPT = """\
Eres un analista experto de estados de cuenta bancarios mexicanos.

CONTEXTO DEL TEXTO QUE RECIBES:
El texto ha sido reconstruido preservando la posición X de cada palabra, usando ~90 \
caracteres de ancho. Esto significa que la alineación horizontal SIGUE siendo válida:
- Palabras que aparecen en la misma columna X a lo largo de varias filas pertenecen \
a la misma columna de la tabla.
- Los encabezados del estado de cuenta (Cargos, Abonos, Debe, Haber, Retiros, \
Depósitos, etc.) te indican qué columna es cuál.

REGLAS DE EXTRACCIÓN (obligatorias):
1. Lee primero la fila de encabezados para saber en qué columna está cada concepto.
2. Para cada movimiento, asigna el importe a "Cargos" o "Abonos" según la columna \
del encabezado correspondiente, NO según el orden de aparición.
3. Un mismo movimiento NUNCA tiene valor en Cargos Y en Abonos al mismo tiempo.
4. Cargos = débitos, gastos, retiros (reducen el saldo).
   Abonos = créditos, depósitos, ingresos (aumentan el saldo).
5. Si el estado usa "Debe/Haber", "Retiros/Depósitos", "Débito/Crédito" o \
"Cargo/Abono" — mapea correctamente: Debe/Retiro/Débito/Cargo → Cargos; \
Haber/Depósito/Crédito/Abono → Abonos.
6. Monto = Abonos - Cargos (resultado negativo si fue un gasto, positivo si ingreso).
7. Ignora encabezados de página, totales generales, publicidad, datos del titular.
8. No inventes transacciones.
9. Categoria: clasifica en minúsculas (despensa, alimentos, servicios, transferencias,\
 retiros, combustible, entretenimiento, salud, otros).

FORMATO DE SALIDA:
{"rows": [{"Fecha de Operacion": "...", "Descripcion": "...", "Referencia": "...",\
 "Categoria": "...", "Cargos": 0.0 o null, "Abonos": 0.0 o null, "Monto": 0.0}, ...]}

Devuelve ÚNICAMENTE JSON válido. Nada fuera del JSON.
"""

_USER_TEMPLATE = """\
Analiza las siguientes páginas del estado de cuenta.
Extrae TODOS los movimientos que encuentres usando las instrucciones del sistema.
Devuelve SOLO JSON con la clave "rows".

{pages_json}
"""


# ─────────────────────────────────────────────
# Llamada a OpenRouter (Claude / texto)
# ─────────────────────────────────────────────

def _call_openrouter(
    pages: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY no está configurado.")

    model = model or os.getenv("OPENAI_FULL_MODEL", "anthropic/claude-sonnet-4-5")

    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError(f"No se pudo importar OpenAI SDK: {e}")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://micro-servicios.com.mx",
            "X-Title": "Bank Statement Converter",
        },
    )

    batch_size = int(os.getenv("FULL_CHAT_PAGES_PER_BATCH", "4"))
    all_rows: List[Dict[str, Any]] = []

    for i in range(0, len(pages), batch_size):
        batch = pages[i: i + batch_size]
        # Limitar a 12 000 chars por página para no sobrepasar tokens
        pages_payload = [
            {"page": p["page"], "text": p["text"][:12_000]}
            for p in batch
        ]
        user_content = _USER_TEMPLATE.format(
            pages_json=json.dumps({"pages": pages_payload}, ensure_ascii=False)
        )
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.05,
                max_tokens=6_000,
                timeout=120,  # 2 minutos máximo por batch
            )
            raw = resp.choices[0].message.content or ""
            raw = _strip_markdown_json(raw)
            data = json.loads(raw)
            rows = data.get("rows")
            if not isinstance(rows, list):
                raise RuntimeError("Respuesta sin 'rows' list.")
            all_rows.extend(rows)
            logger.info(
                "OpenRouter batch p%s–p%s → %d filas",
                batch[0]["page"], batch[-1]["page"], len(rows),
            )
        except json.JSONDecodeError as exc:
            logger.error("JSON inválido del modelo: %s", exc)
        except Exception as exc:
            logger.warning("Fallo batch OpenRouter p%s–p%s: %s", batch[0]["page"], batch[-1]["page"], exc)

    return all_rows


# ─────────────────────────────────────────────
# Llamada a Gemini (PDF nativo — máxima fidelidad)
# ─────────────────────────────────────────────

async def _call_gemini(
    pdf_path: str,
    model: Optional[str] = None,
    max_retries: int = 2,
) -> List[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no está configurado.")

    model = model or os.getenv("GEMINI_FULL_MODEL", "gemini-2.5-flash")
    max_mb = float(os.getenv("GEMINI_FULL_MAX_MB", "25"))
    if os.path.getsize(pdf_path) > max_mb * 1024 * 1024:
        raise ValueError(f"PDF demasiado grande para Gemini (límite {max_mb} MB).")

    try:
        import google.generativeai as genai  # type: ignore
    except Exception as e:
        raise RuntimeError(f"google-generativeai no disponible: {e}")

    genai.configure(api_key=api_key)

    import asyncio, time

    # Subir el PDF en un executor para no bloquear el event loop
    loop = asyncio.get_event_loop()
    uploaded = await loop.run_in_executor(
        None, lambda: genai.upload_file(path=pdf_path, mime_type="application/pdf")
    )

    poll_retries = int(os.getenv("GEMINI_FILE_POLLING_RETRIES", "30"))
    poll_sleep = float(os.getenv("GEMINI_FILE_POLLING_SLEEP", "2"))
    gemini_file = uploaded
    for _ in range(poll_retries):
        current = await loop.run_in_executor(None, lambda: genai.get_file(uploaded.name))
        state = getattr(current, "state", None)
        status = getattr(state, "name", "")
        if status == "ACTIVE":
            gemini_file = current
            break
        if status == "FAILED":
            raise RuntimeError("Gemini marcó el PDF como FAILED.")
        await asyncio.sleep(poll_sleep)  # no-blocking
    else:
        raise RuntimeError("Timeout esperando procesamiento de Gemini.")

    mc = genai.GenerativeModel(model_name=model, system_instruction=_SYSTEM_PROMPT)
    user_prompt = (
        "Extrae los movimientos del PDF adjunto y devuelve SOLO JSON con la clave 'rows'.\n"
        "Recuerda: usa la posición visual de las columnas para distinguir Cargos de Abonos."
    )

    last_err: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = mc.generate_content(
                [
                    {"text": user_prompt},
                    {
                        "file_data": {
                            "file_uri": gemini_file.uri,
                            "mime_type": getattr(gemini_file, "mime_type", "application/pdf"),
                        }
                    },
                ],
                generation_config={"response_mime_type": "application/json"},
            )
            raw = _strip_markdown_json(resp.text or "")
            data = json.loads(raw)
            rows = data.get("rows")
            if not isinstance(rows, list):
                raise RuntimeError("Respuesta sin 'rows' list.")
            logger.info("Gemini extrajo %d filas (intento %d)", len(rows), attempt)
            return rows
        except Exception as exc:
            last_err = exc
            logger.warning("Intento Gemini %d falló: %s", attempt, exc)

    raise RuntimeError(f"Gemini falló tras {max_retries} intentos. Último error: {last_err}")


# ─────────────────────────────────────────────
# Post-procesado y validación
# ─────────────────────────────────────────────

def _post_process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalizar importes
    for col in ("Cargos", "Abonos", "Monto"):
        if col in df.columns:
            df[col] = df[col].apply(_normalize_amount)

    # Recalcular Monto cuando falte o sea 0 y hay Cargos/Abonos
    if "Monto" in df.columns:
        for i, r in df.iterrows():
            m = r.get("Monto")
            c = r.get("Cargos") or 0.0
            a = r.get("Abonos") or 0.0
            if (m is None or (isinstance(m, float) and pd.isna(m))) and (c or a):
                df.at[i, "Monto"] = (a or 0.0) - (c or 0.0)

    # Normalizar fechas
    if "Fecha de Operacion" in df.columns:
        df["Fecha de Operacion"] = df["Fecha de Operacion"].apply(_normalize_date)

    # Categoría siempre presente y en minúsculas
    if "Categoria" not in df.columns:
        df["Categoria"] = "sin categoria"
    df["Categoria"] = df["Categoria"].apply(
        lambda v: str(v).strip().lower() if v not in (None, "", float("nan")) else "sin categoria"
    )

    return df


def _sanity_check_cargo_abono(df: pd.DataFrame) -> pd.DataFrame:
    """Heurística: si 'Cargos' tiene importes que parecen ingresos (muy altos,
    redondos) y 'Abonos' parece gastos (importes bajos variados), las columnas
    están invertidas.  Detectar y corregir automáticamente.

    Señal de inversión: la mediana de Cargos > mediana de Abonos * 5 cuando
    ambas columnas tienen suficientes filas. En un estado de cuenta normal los
    cargos individuales son menores o iguales a los abonos (nómina suele ser
    el mayor abono; gastos diarios son múltiples cargos pequeños).
    """
    if "Cargos" not in df.columns or "Abonos" not in df.columns:
        return df

    cargos = df["Cargos"].dropna()
    abonos = df["Abonos"].dropna()

    if len(cargos) < 3 or len(abonos) < 3:
        return df  # Pocos datos, no concluyente

    median_c = cargos.median()
    median_a = abonos.median()

    # Si la mediana de cargos es 5x mayor que la de abonos, sospechamos inversión
    if median_c > 0 and median_a > 0 and median_c > median_a * 5:
        logger.warning(
            "Posible inversión Cargos/Abonos detectada "
            "(median_cargos=%.2f >> median_abonos=%.2f). Intercambiando columnas.",
            median_c, median_a,
        )
        df = df.copy()
        df["Cargos"], df["Abonos"] = df["Abonos"].copy(), df["Cargos"].copy()
        # Recalcular Monto
        df["Monto"] = df.apply(
            lambda r: (r.get("Abonos") or 0.0) - (r.get("Cargos") or 0.0), axis=1
        )

    return df


def _drop_empty_columns(df: pd.DataFrame, keep: Optional[set] = None) -> pd.DataFrame:
    keep = keep or set()
    cols_to_drop = [
        col for col in df.columns
        if col not in keep
        and (
            (df[col].dtype == object and df[col].fillna("").apply(str.strip).eq("").all())
            or (df[col].dtype != object and df[col].isna().all())
        )
    ]
    return df.drop(columns=cols_to_drop) if cols_to_drop else df


# ─────────────────────────────────────────────
# Punto de entrada principal
# ─────────────────────────────────────────────

async def convert_pdf_to_excel_ai_full(pdf_path: str, model: Optional[str] = None) -> bytes:
    """Conversión IA completa (async).

    Orden de estrategias:
    1. Gemini (nativo PDF, visión) — si GEMINI_API_KEY está definida.
    2. OpenRouter/Claude con texto columnar — fallback siempre disponible.
    """
    rows: List[Dict[str, Any]] = []

    # Estrategia 1: Gemini nativo (ve el PDF como documento visual)
    prefer_gemini = os.getenv("GEMINI_API_KEY") and os.getenv("CONVERTER_PREFER_GEMINI", "1") not in ("0", "false", "no")
    if prefer_gemini:
        try:
            rows = await _call_gemini(pdf_path, model=model)
            logger.info("Conversión exitosa con Gemini (%d filas)", len(rows))
        except Exception as exc:
            logger.warning("Gemini falló, usando OpenRouter como fallback: %s", exc)
            rows = []

    # Estrategia 2: OpenRouter con texto columnar
    if not rows:
        try:
            pages = _extract_pages_columnar(pdf_path, max_pages=10)
            # Filtrar páginas sin contenido financiero relevante
            relevant = [p for p in pages if p["date_hits"] > 0 or p["amount_hits"] > 0]
            if not relevant:
                relevant = pages  # Si ninguna pasa el filtro, usar todas
            rows = _call_openrouter(relevant, model=model)
            logger.info("Conversión exitosa con OpenRouter (%d filas)", len(rows))
        except Exception as exc:
            logger.error("OpenRouter también falló: %s", exc)
            raise RuntimeError(
                f"La conversión IA falló en todas las estrategias disponibles: {exc}"
            ) from exc

    if not rows:
        raise ValueError(
            "El modelo no devolvió movimientos. Verifica que el PDF contenga "
            "transacciones en formato tabular."
        )

    # Construir DataFrame
    df = pd.DataFrame(rows)
    for c in ALLOWED_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[ALLOWED_COLUMNS]

    # Post-procesado
    df = _post_process_dataframe(df)
    df = _sanity_check_cargo_abono(df)
    df = _drop_empty_columns(df, keep=MANDATORY_COLUMNS)

    return _write_excel(df)


__all__ = ["convert_pdf_to_excel_ai_full"]
