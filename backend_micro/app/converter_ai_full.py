import os
import json
import logging
from typing import List, Dict, Any, Optional

import pandas as pd

from .converter import _write_excel

logger = logging.getLogger("converter_ai_full")


ALLOWED_COLUMNS = [
    "Fecha de Operacion", "Fecha de Cargo", "Fecha de Liquidacion",
    "Descripcion", "Referencia", "Cargos", "Abonos",
    "Operacion", "Liquidacion", "Monto",
]


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
    return df


def _call_openai_full_pdf(pdf_path: str, model: Optional[str] = None, max_retries: int = 2) -> List[Dict[str, Any]]:
    """Sube el PDF completo a OpenAI y solicita extracción en JSON estricto.

    Usa el endpoint Responses (más flexible) con referencia directa al archivo.
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

    client = OpenAI(api_key=api_key)

    # Si el SDK no soporta responses, hacemos fallback a chat.completions con texto plano
    has_responses = hasattr(client, "responses")

    if has_responses:
        try:
            upload = client.files.create(file=open(pdf_path, "rb"), purpose="assistants")
        except Exception as e:
            raise RuntimeError(f"Error subiendo PDF a OpenAI: {e}")

    system_instructions = (
        "Eres un analista experto de estados de cuenta bancarios. Recibes un archivo PDF completo. "
        "Debes extraer únicamente las transacciones/movimientos reales en JSON estricto.\n"
        "Formato de salida: {\"rows\":[ ... ]}\n"
        "Cada objeto en rows puede incluir estas claves (usa null si no aplica y NO agregues otras):\n"
        + ", ".join(ALLOWED_COLUMNS) + "\n"
        "Reglas adicionales:\n"
        "- No inventes filas.\n"
        "- Ignora encabezados, totales generales repetidos, publicidad, notas legales.\n"
        "- Si existen Cargos y Abonos, calcula Monto = Abonos - Cargos (negativo si corresponde).\n"
        "- Si solo hay un importe claro úsalo como Monto respetando signo (paréntesis = negativo).\n"
        "- Normaliza comas/puntos a float estándar (usa punto decimal).\n"
        "- Fechas: intenta formato ISO YYYY-MM-DD; si ambiguo, deja null.\n"
        "- Referencia: valores alfanuméricos asociados a la operación (si no existe, null).\n"
    )

    user_prompt = (
        "Extrae los movimientos del PDF adjunto y devuelve SOLO JSON válido con la clave 'rows'. "
        "No escribas nada fuera del JSON."
    )

    if has_responses:
        # Flujo Responses API
        input_blocks = [
            {"role": "system", "content": [{"type": "text", "text": system_instructions}]},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "file", "file_id": upload.id}
            ]}
        ]

        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = client.responses.create(
                    model=model,
                    input=input_blocks,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                text_parts: List[str] = []
                for item in getattr(resp, "output", []) or []:
                    content = getattr(item, "content", None)
                    if not content:
                        continue
                    for c in content:
                        if getattr(c, "type", None) in {"output_text", "text"}:
                            txt = getattr(c, "text", None)
                            if txt:
                                text_parts.append(txt)
                raw = "\n".join(text_parts).strip()
                if not raw:
                    raw = getattr(resp, "output_text", "").strip()
                data = json.loads(raw)
                rows = data.get("rows")
                if not isinstance(rows, list):
                    raise RuntimeError("La respuesta JSON no contiene 'rows' list.")
                return rows
            except Exception as e:  # noqa: BLE001
                last_error = e
                logger.warning("Intento %s extracción IA (responses) falló: %s", attempt, e)
        raise RuntimeError(f"Extracción IA (responses) falló definitivamente: {last_error}")

    # Fallback: leer texto completo del PDF y usar chat.completions
    try:
        import pdfplumber  # type: ignore
    except Exception as e:
        raise RuntimeError(f"pdfplumber necesario para fallback: {e}")

    pages_text: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            txt = pg.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages_text.append(txt)

    # Construir bloques de texto (riesgo alto de tokens, pero solicitado)
    # Si muy grande, dividimos cada N páginas en lotes.
    batch_size = int(os.getenv("FULL_CHAT_PAGES_PER_BATCH", "5"))
    model_chat = model  # reutilizamos mismo nombre

    try:
        from openai import OpenAI  # type: ignore  # (ya importado, redundante)
    except Exception:
        pass

    def call_batch(pages_slice: List[str]) -> List[Dict[str, Any]]:
        prompt_obj = {
            "instrucciones": user_prompt,
            "pages": [
                {"page": i + 1, "text": t[:15000]}  # recorte defensivo por página
                for i, t in enumerate(pages_slice)
            ]
        }
        system_prompt = system_instructions
        try:
            # Algunos modelos no aceptan temperature distinto al default; probamos sin temperature primero
            try:
                resp = client.chat.completions.create(
                    model=model_chat,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(prompt_obj, ensure_ascii=False)},
                    ],
                )
            except Exception as e1:  # reintento con temperature=1 si fallo no relacionado
                # Si el error menciona temperature inválida, reintentar con model por defecto
                msg = str(e1)
                if 'temperature' in msg.lower():
                    resp = client.chat.completions.create(
                        model=model_chat,
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": json.dumps(prompt_obj, ensure_ascii=False)},
                        ],
                        temperature=1,
                    )
                else:
                    raise
            raw = resp.choices[0].message.content
            data = json.loads(raw)
            rows = data.get("rows")
            if not isinstance(rows, list):
                raise RuntimeError("Respuesta sin 'rows'.")
            if os.getenv("FULL_DEBUG"):
                logger.info("DEBUG batch rows=%s", len(rows))
            return rows
        except Exception as e:
            logger.warning("Falló batch chat completions: %s", e)
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
        raise RuntimeError("Fallback chat completions no devolvió filas.")
    return all_rows


def convert_pdf_to_excel_ai_full(pdf_path: str, model: Optional[str] = None) -> bytes:
    """Conversión FULL IA: envía el PDF completo al modelo (alto costo / máxima fidelidad)."""
    rows = _call_openai_full_pdf(pdf_path, model=model)
    df = pd.DataFrame(rows)
    # Asegurar columnas y orden
    for c in ALLOWED_COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[ALLOWED_COLUMNS]
    df = _post_process_dataframe(df)
    return _write_excel(df)


__all__ = ["convert_pdf_to_excel_ai_full"]
