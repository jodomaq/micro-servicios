import os
import json
import logging
from typing import List, Dict, Any, Optional

import pandas as pd

from .converter import _write_excel

logger = logging.getLogger("converter_ai_full")


#ALLOWED_COLUMNS = [
#    "Fecha de Operacion", "Fecha de Cargo", "Fecha de Liquidacion",
#    "Descripcion", "Referencia", "Categoria", "Cargos", "Abonos",
#    "Operacion", "Liquidacion", "Monto",
#]


ALLOWED_COLUMNS = [
    "Fecha de Operacion", "Descripcion", "Referencia",
    "Categoria", "Cargos", "Abonos", "Monto",
]


MANDATORY_COLUMNS = {"Categoria"}


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


def _normalize_amount(val: Any) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    s = s.replace(' ', '')
    # Reemplazar separadores: si hay más de un punto/coma, asumir miles
    # Preferimos dejar solo el último separador decimal
    if s.count(',') > 1 or (s.count(',') == 1 and s.count('.') >= 1):
        s = s.replace('.', '').replace(',', '.')
    else:
        # Si solo hay comas, convertir a punto
        if s.count(',') == 1 and s.count('.') == 0:
            s = s.replace(',', '.')
        # Remover separadores de miles comunes
        if s.count('.') > 1:
            parts = s.split('.')
            s = ''.join(parts[:-1]) + '.' + parts[-1]
    try:
        num = float(s)
        if neg:
            num *= -1
        return num
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
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None


def _post_process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Normalizar montos y cargos/abonos
    if 'Cargos' in df.columns:
        df['Cargos_norm'] = df['Cargos'].apply(_normalize_amount)
    else:
        df['Cargos_norm'] = None
    if 'Abonos' in df.columns:
        df['Abonos_norm'] = df['Abonos'].apply(_normalize_amount)
    else:
        df['Abonos_norm'] = None
    if 'Monto' in df.columns:
        df['Monto_norm'] = df['Monto'].apply(_normalize_amount)
    else:
        df['Monto_norm'] = None

    # Recalcular Monto si ambos Cargos/Abonos están y Monto vacío
    if 'Monto' in df.columns:
        for i, r in df.iterrows():
            if (pd.isna(r.get('Monto')) or r.get('Monto') in {None, ''}) and (r.get('Cargos_norm') is not None or r.get('Abonos_norm') is not None):
                c = r.get('Cargos_norm') or 0.0
                a = r.get('Abonos_norm') or 0.0
                df.at[i, 'Monto'] = a - c
            else:
                if r.get('Monto_norm') is not None:
                    df.at[i, 'Monto'] = r.get('Monto_norm')

    # Normalizar fechas
    for col in ['Fecha de Operacion', 'Fecha de Cargo', 'Fecha de Liquidacion']:
        if col in df.columns:
            df[col] = df[col].apply(_normalize_date)

    # Limpiar columnas auxiliares
    for aux in ['Cargos_norm', 'Abonos_norm', 'Monto_norm']:
        if aux in df.columns:
            df.drop(columns=[aux], inplace=True)

    if 'Categoria' in df.columns:
        df['Categoria'] = df['Categoria'].apply(
            lambda v: str(v).strip().lower() if v not in {None, ''} else None
        )
    else:
        df['Categoria'] = None
    df['Categoria'] = df['Categoria'].fillna('sin categoria')
    return df


def _drop_empty_columns(df: pd.DataFrame, keep: Optional[set] = None) -> pd.DataFrame:
    keep = keep or set()
    cols_to_drop: List[str] = []
    for col in df.columns:
        if col in keep:
            continue
        series = df[col]
        if series.dtype == object:
            if series.fillna('').apply(lambda x: str(x).strip()).eq('').all():
                cols_to_drop.append(col)
        else:
            if series.isna().all():
                cols_to_drop.append(col)
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df

def _call_gemini_full_pdf(pdf_path: str, model: Optional[str] = None, max_retries: int = 2) -> List[Dict[str, Any]]:
    """Sube el PDF completo a Gemini y solicita extracción en JSON estricto.

    Usa el endpoint chat.completions con referencia directa al archivo.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no está configurado.")

    model = model or os.getenv("GEMINI_FULL_MODEL", "gemini-2.5-flash")

    # Tamaño razonable (evitar subir PDFs enormes que excedan límites típicos ~25MB)
    size_bytes = os.path.getsize(pdf_path)
    max_mb = float(os.getenv("GEMINI_FULL_MAX_MB", "25"))
    if size_bytes > max_mb * 1024 * 1024:
        raise ValueError(f"PDF demasiado grande ({size_bytes/1024/1024:.1f}MB) límite {max_mb}MB")

    try:
        import google.generativeai as genai  # type: ignore
    except Exception as e:
        raise RuntimeError(f"No se pudo importar Google Generative AI SDK: {e}")

    genai.configure(api_key=api_key)
    try:
        uploaded_file = genai.upload_file(path=pdf_path, mime_type="application/pdf")
    except Exception as e:
        raise RuntimeError(f"Error subiendo PDF a Gemini: {e}")

    import time
    gemini_file = uploaded_file
    for _ in range(int(os.getenv("GEMINI_FILE_POLLING_RETRIES", "30"))):
        file_state = getattr(genai.get_file(uploaded_file.name), "state", None)
        status = getattr(file_state, "name", None)
        if status == "ACTIVE":
            gemini_file = genai.get_file(uploaded_file.name)
            break
        if status == "FAILED":
            raise RuntimeError("Gemini marcó el PDF como fallido.")
        time.sleep(float(os.getenv("GEMINI_FILE_POLLING_SLEEP", "2")))
    else:
        raise RuntimeError("Timeout esperando que Gemini procese el PDF.")

    system_instructions = (
        "Eres un analista experto de estados de cuenta bancarios. Recibes un archivo PDF completo. "
        "Debes extraer únicamente las transacciones/movimientos reales en JSON estricto.\n"
    )
    system_instructions += (
        "Formato de salida: {\"rows\":[ ... ]}\n"
        "Cada objeto en rows puede incluir estas claves (usa null si no aplica y NO agregues otras):\n"
        + ", ".join(ALLOWED_COLUMNS) + "\n"
        "Reglas adicionales:\n"
        "- No inventes filas.\n"
        "- Ignora encabezados, totales generales repetidos, publicidad, notas legales.\n"
        "- Incluye solo los movimientos del periodo, ignora otras tablas o resúmenes.\n"
        "- Pon especial atención en las columnas y su alineación en el documento, ya que se podría confundir cargos con abonos.\n"
        "- Si existen Cargos y Abonos, calcula Monto = Abonos - Cargos (negativo si corresponde).\n"
        "- Si solo hay un importe claro úsalo como Monto respetando signo (paréntesis = negativo).\n"
        "- Normaliza comas/puntos a float estándar (usa punto decimal).\n"
        "- Fechas: intenta formato ISO YYYY-MM-DD; si ambiguo, deja null.\n"
        "- Referencia: valores alfanuméricos asociados a la operación (si no existe, null).\n"
        "- Categoria: clasifica el movimiento en categorías simples en minúsculas (ej. despensa, servicios, diversion, alimentos, combustible, transferencias, retiros, otros).\n"
    )
    user_prompt = (
        "Extrae los movimientos del PDF adjunto y devuelve SOLO JSON válido con la clave 'rows'. "
        "No escribas nada fuera del JSON.\n"
        "Incluye la columna 'Categoria' para cada fila con la mejor clasificación posible (usa 'otros' si no estás seguro).\n"
        "El archivo PDF está adjunto."
    )
    model_client = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_instructions,
    )
    upload_last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = model_client.generate_content(
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
            raw = (response.text or "").strip()
            raw = _strip_markdown_json(raw)
            data = json.loads(raw)
            rows = data.get("rows")
            if not isinstance(rows, list):
                raise RuntimeError("La respuesta JSON no contiene 'rows' list.")
            return rows
        except Exception as e:
            upload_last_error = e
            logger.warning("Intento %s extracción IA (Gemini) falló: %s", attempt, e)

    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Extracción IA (Gemini) falló y pdfplumber necesario para fallback: "
            f"{e}. Último error Gemini={upload_last_error}"
        )
    pages_text: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            txt = pg.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages_text.append(txt)
    batch_size = int(os.getenv("FULL_CHAT_PAGES_PER_BATCH", "5"))

    def call_batch(pages_slice: List[str]) -> List[Dict[str, Any]]:
        prompt_obj = {
            "instrucciones": user_prompt,
            "pages": [
                {"page": i + 1, "text": t[:15000]}
                for i, t in enumerate(pages_slice)
            ],
        }
        try:
            response = model_client.generate_content(
                [{"text": json.dumps(prompt_obj, ensure_ascii=False)}],
                generation_config={"response_mime_type": "application/json"},
            )
            raw = (response.text or "").strip()
            raw = _strip_markdown_json(raw)
            data = json.loads(raw)
            rows = data.get("rows")
            if not isinstance(rows, list):
                raise RuntimeError("Respuesta sin 'rows'.")
            if os.getenv("FULL_DEBUG"):
                logger.info("DEBUG batch rows=%s", len(rows))
            return rows
        except Exception as e:
            logger.warning("Falló batch Gemini fallback: %s", e)
            return []

    all_rows: List[Dict[str, Any]] = []
    current: List[str] = []
    for txt in pages_text:
        current.append(txt)
        if len(current) >= batch_size:
            all_rows.extend(call_batch(current))
            current = []
    if current:
        all_rows.extend(call_batch(current))

    if not all_rows:
        raise RuntimeError(
            "Extracción IA (Gemini) falló definitivamente o fallback no devolvió filas. "
            f"Último error Gemini={upload_last_error}"
        )
    return all_rows


def _call_openai_full_pdf(pdf_path: str, model: Optional[str] = None, max_retries: int = 2) -> List[Dict[str, Any]]:
    """Sube el PDF completo a OpenRouter y solicita extracción en JSON estricto.

    Usa el endpoint chat.completions con texto extraído del PDF.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY no está configurado.")

    model = model or os.getenv("OPENAI_FULL_MODEL", "anthropic/claude-sonnet-4.5")

    # Tamaño razonable (evitar subir PDFs enormes que excedan límites típicos ~25MB)
    size_bytes = os.path.getsize(pdf_path)
    max_mb = float(os.getenv("OPENAI_FULL_MAX_MB", "25"))
    if size_bytes > max_mb * 1024 * 1024:
        raise ValueError(f"PDF demasiado grande ({size_bytes/1024/1024:.1f}MB) límite {max_mb}MB")

    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError(f"No se pudo importar OpenAI SDK: {e}")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/your-org/backend_micro",
            "X-Title": "Bank Statement Converter"
        }
    )

    # Preparar instrucciones
    system_instructions = (
        "Eres un analista experto de estados de cuenta bancarios. Recibes un archivo PDF completo. "
        "Debes extraer únicamente las transacciones/movimientos reales en JSON estricto.\n"
        "Formato de salida: {\"rows\":[ ... ]}\n"
        "Cada objeto en rows puede incluir estas claves (usa null si no aplica y NO agregues otras):\n"
        + ", ".join(ALLOWED_COLUMNS) + "\n"
        "Reglas adicionales:\n"
        "- No inventes filas.\n"
        "- Ignora encabezados, totales generales repetidos, publicidad, notas legales.\n"
        "- Incluye solo los movimientos del periodo, ignora otras tablas o resúmenes.\n"
        "- Pon especial atención en las columnas y su alineación en el documento, ya que se podría confundir cargos con abonos.\n"
        "- Si existen Cargos y Abonos, calcula Monto = Abonos - Cargos (negativo si corresponde).\n"
        "- Si solo hay un importe claro úsalo como Monto respetando signo (paréntesis = negativo).\n"
        "- Normaliza comas/puntos a float estándar (usa punto decimal).\n"
        "- Fechas: intenta formato ISO YYYY-MM-DD; si ambiguo, deja null.\n"
        "- Referencia: valores alfanuméricos asociados a la operación (si no existe, null).\n"
        "- Categoria: clasifica el movimiento en categorías simples en minúsculas (ej. despensa, servicios, diversion, alimentos, combustible, transferencias, retiros, otros).\n"
    )

    user_prompt = (
        "Extrae los movimientos del PDF adjunto y devuelve SOLO JSON válido con la clave 'rows'. "
        "No escribas nada fuera del JSON. "
        "Incluye la columna 'Categoria' en cada fila utilizando la mejor clasificación posible (usa 'otros' si no estás seguro)."
    )

    # OpenRouter/Claude no soporta subida directa de archivos, usamos texto extraído
    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        raise RuntimeError(f"pdfplumber necesario para extracción: {e}")

    pages_text: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            txt = pg.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages_text.append(txt)

    # Dividir en lotes para evitar límites de tokens
    batch_size = int(os.getenv("FULL_CHAT_PAGES_PER_BATCH", "5"))

    def call_batch(pages_slice: List[str]) -> List[Dict[str, Any]]:
        prompt_obj = {
            "instrucciones": user_prompt,
            "pages": [
                {"page": i + 1, "text": t[:15000]}
                for i, t in enumerate(pages_slice)
            ]
        }
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": json.dumps(prompt_obj, ensure_ascii=False)},
                ],
                temperature=0.1,
                max_tokens=4000,
            )
            raw = resp.choices[0].message.content
            
            logger.debug("OpenRouter response: %s", raw[:500] if raw else "EMPTY")
            
            if not raw or raw.strip() == "":
                raise RuntimeError("OpenRouter devolvió respuesta vacía")
            
            raw = _strip_markdown_json(raw)
            data = json.loads(raw)
            rows = data.get("rows")
            if not isinstance(rows, list):
                logger.error("Payload sin 'rows': %s", data)
                raise RuntimeError("Respuesta sin 'rows'.")
            if os.getenv("FULL_DEBUG"):
                logger.info("DEBUG batch rows=%s", len(rows))
            return rows
        except json.JSONDecodeError as e:
            logger.error("JSON inválido recibido: %s", raw[:1000] if raw else "EMPTY")
            raise RuntimeError(f"La respuesta no es JSON válido: {e}")
        except Exception as e:
            logger.warning("Falló batch OpenRouter: %s", e)
            return []

    all_rows: List[Dict[str, Any]] = []
    current: List[str] = []
    for txt in pages_text:
        current.append(txt)
        if len(current) >= batch_size:
            all_rows.extend(call_batch(current))
            current = []
    if current:
        all_rows.extend(call_batch(current))

    if not all_rows:
        raise RuntimeError("OpenRouter no devolvió filas válidas.")
    return all_rows


def convert_pdf_to_excel_ai_full(pdf_path: str, model: Optional[str] = None) -> bytes:
    """Conversión FULL IA: envía el PDF completo al modelo (alto costo / máxima fidelidad)."""
    rows = _call_openai_full_pdf(pdf_path, model=model)
    # rows = _call_gemini_full_pdf(pdf_path, model=model)  # Mantener Gemini como alternativa
    df = pd.DataFrame(rows)
    # Asegurar columnas y orden
    for c in ALLOWED_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[ALLOWED_COLUMNS]
    df = _post_process_dataframe(df)
    df = _drop_empty_columns(df, keep=MANDATORY_COLUMNS)
    return _write_excel(df)


__all__ = ["convert_pdf_to_excel_ai_full"]
