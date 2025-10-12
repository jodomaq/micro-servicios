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
    """Sube el PDF completo a OpenAI y solicita extracción en JSON estricto.

    Usa el endpoint Responses (más flexible) con referencia directa al archivo.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurado.")

    model = model or os.getenv("OPENAI_FULL_MODEL", "gpt-5-mini")

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

    # Preparar instrucciones (se usan en el flujo Responses)
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

    if has_responses:
        # Intentar subir el PDF al cliente OpenAI para obtener un file_id compatible
        upload_obj = None
        upload_id: Optional[str] = None
        try:
            with open(pdf_path, "rb") as fh:
                # Intentar varios métodos comunes de SDK para subir archivos, probando distintos propósitos comunes
                purposes = ["responses", "assistants", "user_data"]
                for purpose in purposes:
                    fh.seek(0)
                    if hasattr(client, "files"):
                        files_client = client.files
                        if hasattr(files_client, "create") and upload_obj is None:
                            try:
                                upload_obj = files_client.create(file=fh, purpose=purpose)
                            except TypeError:
                                fh.seek(0)
                                upload_obj = files_client.create(
                                    file=fh,
                                    purpose=purpose,
                                    file_name=os.path.basename(pdf_path),
                                )
                            except Exception:
                                upload_obj = None
                        if upload_obj is None and hasattr(files_client, "upload"):
                            fh.seek(0)
                            try:
                                upload_obj = files_client.upload(file=fh, purpose=purpose)
                            except TypeError:
                                fh.seek(0)
                                upload_obj = files_client.upload(
                                    file=fh,
                                    purpose=purpose,
                                    file_name=os.path.basename(pdf_path),
                                )
                            except Exception:
                                upload_obj = None
                    if upload_obj is None and hasattr(client, "upload_file"):
                        fh.seek(0)
                        try:
                            upload_obj = client.upload_file(file=fh, purpose=purpose)
                        except TypeError:
                            fh.seek(0)
                            upload_obj = client.upload_file(
                                file=fh,
                                purpose=purpose,
                                file_name=os.path.basename(pdf_path),
                            )
                        except Exception:
                            upload_obj = None
                    if upload_obj is not None:
                        break
        except Exception as e:
            # No bloquear aquí; se intentará enviar sin archivo si el SDK lo permite,
            # pero registramos el intento.
            logger.warning("No se pudo subir archivo para Responses API: %s", e)
            upload_obj = None

        # Extraer un identificador robusto del objeto de subida (distintos SDKs devuelven diferentes formas)
        if upload_obj is not None:
            if isinstance(upload_obj, dict):
                upload_id = upload_obj.get("id") or upload_obj.get("file_id") or upload_obj.get("name")
            else:
                upload_id = getattr(upload_obj, "id", None) or getattr(upload_obj, "file_id", None) or getattr(upload_obj, "name", None)

        # Construir bloques de entrada, incluyendo el archivo solo si logramos un id
        user_content = [{"type": "input_text", "text": user_prompt}]
        if upload_id:
            user_content.append({"type": "input_file", "file_id": upload_id})
        input_blocks = [
            {"role": "system", "content": [{"type": "input_text", "text": system_instructions}]},
            {"role": "user", "content": user_content}
        ]

        use_response_format = True
        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            kwargs: Dict[str, Any] = {
                "model": model,
                "input": input_blocks,
            }
            if use_response_format:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                resp = client.responses.create(**kwargs)
                raw = (getattr(resp, "output_text", None) or "").strip()
                if not raw:
                    # Fallback a lectura manual de bloques de salida
                    text_parts: List[str] = []
                    for item in getattr(resp, "output", []) or []:
                        content = getattr(item, "content", None)
                        if not content:
                            continue
                        for c in content:
                            if getattr(c, "type", None) == "output_text":
                                txt = getattr(c, "text", None)
                                if txt:
                                    text_parts.append(txt)
                    raw = "\n".join(text_parts).strip()
                data = json.loads(raw)
                rows = data.get("rows")
                if not isinstance(rows, list):
                    raise RuntimeError("La respuesta JSON no contiene 'rows' list.")
                return rows
            except TypeError as e:
                if use_response_format and "response_format" in str(e):
                    use_response_format = False
                    last_error = e
                    logger.warning(
                        "Intento %s responses sin response_format por incompatibilidad SDK.",
                        attempt,
                    )
                    continue
                raise
            except Exception as e:  # noqa: BLE001
                last_error = e
                logger.warning("Intento %s extracción IA (responses) falló: %s", attempt, e)
        raise RuntimeError(f"Extracción IA (responses) falló definitivamente: {last_error}")

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
                kwargs_chat: Dict[str, Any] = {
                    "model": model_chat,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(prompt_obj, ensure_ascii=False)},
                    ],
                }
                use_response_format_chat = True
                if use_response_format_chat:
                    kwargs_chat["response_format"] = {"type": "json_object"}
                resp = client.chat.completions.create(**kwargs_chat)
            except TypeError as e1:
                if "response_format" in str(e1):
                    kwargs_chat.pop("response_format", None)
                    resp = client.chat.completions.create(**kwargs_chat)
                else:
                    raise
            except Exception as e1:
                logger.warning("Falló batch chat completions: %s", e1)
                return []
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
    #rows = _call_openai_full_pdf(pdf_path, model=model)
    rows = _call_gemini_full_pdf(pdf_path, model=model)
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
