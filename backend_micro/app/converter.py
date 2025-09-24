import io
import os
import re
import logging
from typing import List, Optional, Tuple

import pandas as pd
from dateutil import parser as dateparser
import json

logger = logging.getLogger("converter")


def _try_import_camelot():
    try:
        import camelot  # type: ignore
        return camelot
    except Exception:
        return None


def _normalize_headers(cols: List[str]) -> List[str]:
    norm = []
    for c in cols:
        c0 = (c or "").strip().lower()
        norm.append(c0)
    return norm


def _map_columns(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Try to map incoming dataframe columns to our schema.

    Target columns: Fecha de Operacion, Fecha de Cargo, Descripcion, Monto
    """
    cols = _normalize_headers(list(df.columns))
    # Create a mapping by best-effort
    fecha_op_idx = None
    fecha_cargo_idx = None
    desc_idx = None
    monto_idx = None

    for i, c in enumerate(cols):
        if fecha_op_idx is None and ("fecha" in c and ("oper" in c or "mov" in c or "trans" in c)):
            fecha_op_idx = i
        if fecha_cargo_idx is None and ("fecha" in c and ("cargo" in c or "abono" in c or "val" in c)):
            fecha_cargo_idx = i
        if desc_idx is None and ("desc" in c or "concept" in c or "detalle" in c):
            desc_idx = i
        if monto_idx is None and ("monto" in c or "importe" in c or "cargo" == c or "abono" == c or "saldo" == c):
            monto_idx = i

    # Fallbacks
    if fecha_op_idx is None:
        for i, c in enumerate(cols):
            if c.startswith("fecha"):
                fecha_op_idx = i
                break

    if desc_idx is None:
        for i, c in enumerate(cols):
            if "desc" in c or "concept" in c:
                desc_idx = i
                break

    if monto_idx is None:
        for i, c in enumerate(cols[::-1]):  # try from right-most
            if any(k in c for k in ["monto", "importe"]):
                monto_idx = len(cols) - 1 - i
                break

    if desc_idx is None or monto_idx is None:
        return None

    # Build mapped dataframe
    def _get(col_idx: Optional[int], row):
        return row.iloc[col_idx] if col_idx is not None and col_idx < len(row) else None

    out = []
    for _, row in df.iterrows():
        try:
            fecha_op = _get(fecha_op_idx, row)
            fecha_cargo = _get(fecha_cargo_idx, row)
            descripcion = _get(desc_idx, row)
            monto = _get(monto_idx, row)
            out.append([fecha_op, fecha_cargo, descripcion, monto])
        except Exception:
            continue

    if not out:
        return None

    res = pd.DataFrame(out, columns=["Fecha de Operacion", "Fecha de Cargo", "Descripcion", "Monto"])
    return res


def _map_columns_extended(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Mapea a un esquema extendido si la tabla contiene columnas tipo banco.

    Esquema objetivo (al menos una de estas debe existir para considerar mapeo válido):
      - Fecha de Operacion
      - Fecha de Liquidacion
      - Descripcion
      - Referencia
      - Cargos
      - Abonos
      - Operacion
      - Liquidacion

    Además calcula Monto = Abonos - Cargos cuando ambas existan.
    """
    if df is None or df.empty:
        return None
    cols_raw = list(df.columns)
    cols = _normalize_headers(cols_raw)

    idx = {k: None for k in [
        "fecha_oper", "fecha_liq", "descripcion", "referencia", "cargos", "abonos", "operacion", "liquidacion"
    ]}

    def set_if(cond, key, i):
        if idx[key] is None and cond:
            idx[key] = i

    for i, c in enumerate(cols):
        # Fechas
        set_if(("fecha" in c and ("oper" in c or "ope" in c)), "fecha_oper", i)
        set_if(("fecha" in c and ("liq" in c or "liquid" in c)), "fecha_liq", i)
        # Descripcion
        set_if(("desc" in c or "descripción" in c or "descripcion" in c or "concept" in c or "detalle" in c), "descripcion", i)
        # Referencia
        set_if(("ref" in c or "referencia" in c), "referencia", i)
        # Valores
        set_if((c == "cargo" or "cargos" in c or "retiro" in c or "debit" in c), "cargos", i)
        set_if((c == "abono" or "abonos" in c or "deposit" in c or "credit" in c), "abonos", i)
        # Saldos
        set_if(("operacion" in c and "saldo" in c) or c.strip() in {"operacion", "operación"}, "operacion", i)
        set_if(("liquid" in c and "saldo" in c) or c.strip() in {"liquidacion", "liquidación"}, "liquidacion", i)

    if all(v is None for v in idx.values()):
        return None

    def _safe_get(r, col_idx):
        return r.iloc[col_idx] if col_idx is not None and col_idx < len(r) else None

    out_rows = []
    for _, r in df.iterrows():
        out_rows.append([
            _safe_get(r, idx["fecha_oper"]),
            _safe_get(r, idx["fecha_liq"]),
            _safe_get(r, idx["descripcion"]),
            _safe_get(r, idx["referencia"]),
            _safe_get(r, idx["cargos"]),
            _safe_get(r, idx["abonos"]),
            _safe_get(r, idx["operacion"]),
            _safe_get(r, idx["liquidacion"]),
        ])

    mapped = pd.DataFrame(out_rows, columns=[
        "Fecha de Operacion", "Fecha de Liquidacion", "Descripcion", "Referencia",
        "Cargos", "Abonos", "Operacion", "Liquidacion"
    ])

    # Si tenemos cargos/abonos, calculamos Monto (abonos - cargos)
    if "Cargos" in mapped.columns or "Abonos" in mapped.columns:
        def _mon(r):
            c = _coerce_amount(str(r.get("Cargos"))) if pd.notna(r.get("Cargos")) else 0.0
            a = _coerce_amount(str(r.get("Abonos"))) if pd.notna(r.get("Abonos")) else 0.0
            if c is None:
                c = 0.0
            if a is None:
                a = 0.0
            return (a or 0.0) - (c or 0.0)
        mapped["Monto"] = mapped.apply(_mon, axis=1)

    return mapped


def _merge_header_rows(df: pd.DataFrame, max_header_rows: int = 3) -> pd.DataFrame:
    """Combina 1-3 filas de encabezado en una sola fila y descarta solo las filas de encabezado reales.

    Detecta de manera heurística cuántas filas iniciales son encabezado: busca palabras clave
    típicas (fecha, descr, cargo, abono, saldo, ref) y analiza si la mayoría de celdas son texto.
    """
    if df is None or df.empty:
        return df

    def is_headerish(vals: List[object]) -> bool:
        texts = [str(v).strip() for v in vals if v is not None]
        if not texts:
            return False
        # Palabras clave comunes en encabezados
        joined = " ".join(texts).lower()
        keywords = ["fecha", "oper", "liq", "descr", "descrip", "cargo", "abono", "saldo", "ref", "referen"]
        kw_score = sum(1 for k in keywords if k in joined)
        # Porcentaje de celdas no numéricas
        nonnum = 0
        for t in texts:
            tt = t.replace(" ", "")
            if not re.fullmatch(r"[()$+\-]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?", tt):
                nonnum += 1
        ratio_nonnum = nonnum / max(1, len(texts))
        return kw_score >= 1 and ratio_nonnum >= 0.6

    # Detectar cuántas filas de encabezado hay (1..max_header_rows)
    header_row_count = 0
    for i in range(min(max_header_rows, len(df))):
        if is_headerish(list(df.iloc[i])):
            header_row_count += 1
        else:
            break
    if header_row_count == 0:
        return df

    header_parts = [list(df.iloc[i]) for i in range(header_row_count)]
    combined = []
    for col_idx in range(len(df.columns)):
        tokens = []
        for r in range(header_row_count):
            val = header_parts[r][col_idx]
            if val is not None:
                sval = str(val).strip()
                if sval and sval.lower() not in {"", "none"}:
                    tokens.append(sval)
        combined.append(" ".join(tokens).strip())

    new_df = df.copy()
    new_df.columns = combined
    new_df = new_df[header_row_count:]
    return new_df


def _pdfplumber_extract_tables(pdf_path: str, max_pages: int = 10) -> List[Tuple[int, pd.DataFrame]]:
    """Extrae tablas con pdfplumber usando estrategias de líneas.

    Devuelve una lista de tuplas (page_index_1based, DataFrame) ya con encabezados combinados (1-3 filas).
    """
    extracted: List[Tuple[int, pd.DataFrame]] = []
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages[:max_pages], start=1):
                # Primero intenta con líneas (si hay líneas en el estado)
                settings = dict(
                    vertical_strategy="lines",
                    horizontal_strategy="lines",
                    snap_tolerance=3,
                    join_tolerance=3,
                    edge_min_length=20,
                    min_words_vertical=1,
                    min_words_horizontal=1,
                )
                tables = page.extract_tables(table_settings=settings) or []
                if not tables:
                    # Fallback a estrategia de texto
                    settings_text = dict(
                        vertical_strategy="text",
                        horizontal_strategy="text",
                        intersection_tolerance=5,
                        snap_tolerance=3,
                        text_x_tolerance=2,
                        text_y_tolerance=2,
                    )
                    tables = page.extract_tables(table_settings=settings_text) or []
                for tbl in tables:
                    try:
                        df_tab = pd.DataFrame(tbl)
                        df_tab = _merge_header_rows(df_tab, max_header_rows=3)
                        extracted.append((page_idx, df_tab))
                    except Exception:
                        continue
    except Exception as e:
        logger.info("pdfplumber table extraction failed: %s", e)
    return extracted


_DATE_RE = re.compile(r"\b(\d{1,2}[-/\.](\d{1,2}|[A-Za-z]{3,})[-/\.]\d{2,4})\b")
_AMOUNT_RE = re.compile(r"([+-]?\(?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\)?)$")
_DATE_TOKEN = r"(\d{1,2})\s*[\-/\.]\s*(\d{1,2}|[A-Za-zÁÉÍÓÚÑáéíóú]{3,})"
_DATE_PREFIX_RE = re.compile(rf"^\s*{_DATE_TOKEN}(?:\s+{_DATE_TOKEN})?\b", re.IGNORECASE)


def _parse_line_text(line: str) -> Optional[Tuple[Optional[str], Optional[str], str, str]]:
    line = line.strip()
    if not line:
        return None
    # Find amount at end
    am = _AMOUNT_RE.search(line)
    if not am:
        return None
    amount_text = am.group(1)
    rest = line[: am.start()].strip()
    # Extract up to two dates from the beginning
    dates = list(_DATE_RE.finditer(rest))
    fecha_op = None
    fecha_cargo = None
    descripcion = rest
    if dates:
        # use first as op date
        first = dates[0]
        fecha_op = first.group(1)
        descripcion = rest[first.end():].strip(" -•|\t")
        if len(dates) > 1:
            second = dates[1]
            fecha_cargo = second.group(1)
            descripcion = rest[second.end():].strip(" -•|\t")
    return (fecha_op, fecha_cargo, descripcion, amount_text)


def _extract_dates_from_description_row(desc: str) -> Tuple[Optional[str], Optional[str], str]:
    """If description starts with one or two date tokens (e.g., '11/JUL 11/JUL ...'), split them."""
    m = _DATE_PREFIX_RE.search(desc or "")
    if not m:
        return None, None, desc
    # Groups: (d1, m1, d2, m2) possibly
    # Build normalized strings
    parts = desc[m.end():].strip(" -•|\t")
    d1 = f"{m.group(1)}/{m.group(2)}"
    d2 = None
    if m.lastindex and m.lastindex >= 4:
        d2 = f"{m.group(3)}/{m.group(4)}"
    return d1, d2, parts


def _postprocess_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing date columns by extracting leading date tokens from description."""
    if df is None or df.empty:
        return df
    df = df.copy()
    for idx, row in df.iterrows():
        fo = row.get("Fecha de Operacion")
        fc = row.get("Fecha de Cargo")
        desc = str(row.get("Descripcion", ""))
        if (pd.isna(fo) or not str(fo).strip()) and (pd.isna(fc) or not str(fc).strip()):
            nfo, nfc, rest = _extract_dates_from_description_row(desc)
            if nfo or nfc:
                df.at[idx, "Fecha de Operacion"] = nfo
                df.at[idx, "Fecha de Cargo"] = nfc
                df.at[idx, "Descripcion"] = rest
    return df


def _ai_quality_check(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Optionally call OpenAI to validate and normalize rows.

    Expects OPENAI_API_KEY in env and ENABLE_OPENAI_QA truthy to run. Returns a new DataFrame or None on failure.
    """
    try:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        enabled = os.getenv("ENABLE_OPENAI_QA", "0").strip() not in {"", "0", "false", "False", "no"}
        if not api_key or not enabled:
            return None

        # Limit rows to control token usage
        records = df.to_dict(orient="records")
        max_rows = int(os.getenv("OPENAI_QA_MAX_ROWS", "250"))
        payload_rows = records[:max_rows]

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        system = (
            "Eres un asistente de control de calidad de datos bancarios. "
            "Valida y normaliza filas para un Excel con columnas exactas: "
            "Fecha de Operacion, Fecha de Cargo, Descripcion, Monto. "
            "Requisitos: "
            "- Devuelve SOLO JSON con una clave 'rows' (array) y opcional 'issues' (array de strings). "
            "- Cada elemento de 'rows' debe incluir esas 4 claves exactas. "
            "- Intenta separar la(s) fecha(s) al inicio de la descripcion si vienen juntas (p. ej. '11/JUL 11/JUL ...'). "
            "- Normaliza fechas a formato ISO 'YYYY-MM-DD' si es posible (si no, deja null). "
            "- Convierte Monto a número float (negativo si hay paréntesis o signo). "
            "- Elimina texto no transaccional en 'Descripcion' (ej. encabezados no relevantes) SOLO si Monto no tiene sentido (p. ej. vacío). "
            "- No inventes transacciones.")

        user = (
            "Valida y corrige estas filas. Respóndeme SOLO con JSON válido.\n" +
            json.dumps({"rows": payload_rows}, ensure_ascii=False)
        )

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_QA_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        rows = data.get("rows")
        if not isinstance(rows, list):
            return None
        # Build DataFrame and coerce types again
        out_df = pd.DataFrame(rows, columns=["Fecha de Operacion", "Fecha de Cargo", "Descripcion", "Monto"])
        return out_df
    except Exception as e:
        logger.warning("OpenAI QA failed or disabled: %s", e)
        return None


def _coerce_amount(amount_text: str) -> Optional[float]:
    t = amount_text.replace(" ", "").replace(",", "").replace("$", "")
    # Normalize parentheses as negative
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    t = t.replace(".", "") if t.count(".") > 1 else t
    try:
        val = float(t)
        return -val if neg else val
    except Exception:
        # Try swapped decimal/comma
        try:
            t2 = amount_text.replace(".", "").replace(",", ".").replace("$", "").strip()
            neg = t2.startswith("(") and t2.endswith(")")
            t2 = t2.strip("()")
            val = float(t2)
            return -val if neg else val
        except Exception:
            return None


def _coerce_date(text: Optional[str]) -> Optional[pd.Timestamp]:
    if not text:
        return None
    try:
        dt = dateparser.parse(text, dayfirst=True, fuzzy=True)
        return pd.to_datetime(dt)
    except Exception:
        return None


def _write_excel(df: pd.DataFrame, original_df: Optional[pd.DataFrame] = None) -> bytes:
    # Clean and standardize columns
    df = df.copy()
    df.rename(columns={
        "fecha de operacion": "Fecha de Operacion",
        "fecha de cargo": "Fecha de Cargo",
        "fecha de liquidacion": "Fecha de Liquidacion",
        "descripcion": "Descripcion",
        "referencia": "Referencia",
        "cargos": "Cargos",
        "abonos": "Abonos",
        "operacion": "Operacion",
        "liquidacion": "Liquidacion",
        "monto": "Monto",
    }, inplace=True)
    # Coerce types
    df["Fecha de Operacion"] = df["Fecha de Operacion"].apply(_coerce_date)
    if "Fecha de Cargo" in df.columns:
        df["Fecha de Cargo"] = df["Fecha de Cargo"].apply(_coerce_date)
    if "Fecha de Liquidacion" in df.columns:
        df["Fecha de Liquidacion"] = df["Fecha de Liquidacion"].apply(_coerce_date)
    df["Descripcion"] = df["Descripcion"].astype(str)
    df["Monto"] = df["Monto"].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else None)
    # Coerce optional bank columns if present
    for col in ["Cargos", "Abonos", "Operacion", "Liquidacion"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else None)
    # Mantener filas con monto válido aunque la descripción esté vacía; descartar solo si Monto es NaN o 0 y descripción vacía
    df = df[~(df["Monto"].isna() & (df["Descripcion"].str.strip() == ""))].reset_index(drop=True)

    total = df["Monto"].sum() if not df.empty else 0.0

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Hoja estandarizada con totales
        df.to_excel(writer, index=False, sheet_name="Movimientos")
        # Add total row
        wb = writer.book
        ws = writer.sheets["Movimientos"]
        last_row = ws.max_row + 1
        # Encabezado de Total según columnas presentes
        # Escribimos totales para Monto y, si existen, para Cargos y Abonos
        # Buscamos índices de columnas (1-based en Excel)
        cols_map = {c: i+1 for i, c in enumerate(list(df.columns))}
        # Etiqueta total en la tercera columna si existe Descripcion, si no en la primera
        label_col = cols_map.get("Descripcion") or 1
        ws.cell(row=last_row, column=label_col, value="Total")
        # Total de Monto
        if "Monto" in df.columns:
            ws.cell(row=last_row, column=cols_map["Monto"], value=total)
        # Totales de Cargos y Abonos
        if "Cargos" in df.columns:
            try:
                total_cargos = df["Cargos"].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else 0.0).sum()
                ws.cell(row=last_row, column=cols_map["Cargos"], value=total_cargos)
            except Exception:
                pass
        if "Abonos" in df.columns:
            try:
                total_abonos = df["Abonos"].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else 0.0).sum()
                ws.cell(row=last_row, column=cols_map["Abonos"], value=total_abonos)
            except Exception:
                pass
        # Hoja de Resumen simple
        try:
            resumen = {}
            if "Cargos" in df.columns:
                resumen["Total Cargos"] = float(df["Cargos"].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else 0.0).sum())
            if "Abonos" in df.columns:
                resumen["Total Abonos"] = float(df["Abonos"].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else 0.0).sum())
            if "Monto" in df.columns:
                resumen["Total Monto"] = float(df["Monto"].apply(lambda x: float(x) if pd.notna(x) else 0.0).sum())
            if resumen:
                pd.DataFrame([{**resumen}]).T.rename(columns={0: "Valor"}).to_excel(writer, sheet_name="Resumen")
        except Exception as e:
            logger.warning("No se pudo crear hoja 'Resumen': %s", e)
        # Hoja con columnas originales detectadas (si existe)
        if original_df is not None and not original_df.empty:
            try:
                original_df.to_excel(writer, index=False, sheet_name="Original")
            except Exception as e:
                logger.warning("No se pudo escribir hoja 'Original': %s", e)
    return output.getvalue()


def _merge_preserve_columns(dfs: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Concatena tablas preservando todas las columnas detectadas (unión de encabezados)."""
    if not dfs:
        return None
    # Normaliza tipos de columnas a string para evitar conflictos
    norm = []
    for d in dfs:
        d2 = d.copy()
        d2.columns = [str(c) for c in d2.columns]
        norm.append(d2)
    try:
        all_cols = []
        seen = set()
        for d in norm:
            for c in d.columns:
                if c not in seen:
                    seen.add(c)
                    all_cols.append(c)
        aligned = []
        for d in norm:
            for c in all_cols:
                if c not in d.columns:
                    d[c] = None
            aligned.append(d[all_cols])
        return pd.concat(aligned, ignore_index=True)
    except Exception as e:
        logger.warning("No se pudo unir tablas originales: %s", e)
        return None


def _normalize_desc(text: Optional[str]) -> str:
    s = (str(text or "")).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def convert_pdf_to_excel(pdf_path: str, max_pages: int = 10) -> bytes:
    # Validate page count
    try:
        import pdfplumber  # lightweight and pure python
        with pdfplumber.open(pdf_path) as pdf:
            pages = len(pdf.pages)
    except Exception as e:
        logger.warning("Could not count pages with pdfplumber: %s", e)
        pages = None

    if pages is not None and pages > max_pages:
        raise ValueError(f"El PDF excede el máximo permitido de {max_pages} páginas (tiene {pages}).")

    # Acumuladores globales
    std_frames: List[pd.DataFrame] = []
    original_frames: List[pd.DataFrame] = []
    fallback_rows: List[Tuple[Optional[str], Optional[str], str, str]] = []

    # Strategy 1: Camelot tables (if available). No retorno temprano: combinaremos con otras estrategias y deduplicaremos.
    camelot = _try_import_camelot()
    if camelot is not None:
        try:
            tables = camelot.read_pdf(pdf_path, pages=f"1-{max_pages}", flavor="stream")
            if tables and len(tables) > 0:
                for t in tables:
                    try:
                        df_tab = t.df
                        # First row in Camelot often is header
                        df_tab.columns = df_tab.iloc[0]
                        df_tab = df_tab[1:]
                        original_frames.append(df_tab)
                        mapped_ext = _map_columns_extended(df_tab)
                        if mapped_ext is not None:
                            std_frames.append(mapped_ext)
                        else:
                            mapped = _map_columns(df_tab)
                            if mapped is not None:
                                std_frames.append(mapped)
                            else:
                                # Fallback: intentar parsear cada fila uniéndola como texto
                                for _, r in df_tab.iterrows():
                                    line = " ".join([str(x) for x in list(r.values) if pd.notna(x) and str(x).strip()])
                                    parsed = _parse_line_text(line)
                                    if parsed:
                                        fallback_rows.append(parsed)
                    except Exception:
                        continue
        except Exception as e:
            logger.info("Camelot parsing failed or not applicable: %s", e)

    # Strategy 2: Parse lines with pdfplumber
    try:
        # 2a) Antes de líneas, intentemos tablas con pdfplumber
        tables = _pdfplumber_extract_tables(pdf_path, max_pages=max_pages)
        if tables:
            for page_idx, df_tab in tables:
                try:
                    original_frames.append(df_tab)
                    mapped_ext = _map_columns_extended(df_tab)
                    if mapped_ext is not None:
                        std_frames.append(mapped_ext)
                    else:
                        mapped = _map_columns(df_tab)
                        if mapped is not None:
                            std_frames.append(mapped)
                        else:
                            # Fallback por filas
                            for _, r in df_tab.iterrows():
                                line = " ".join([str(x) for x in list(r.values) if pd.notna(x) and str(x).strip()])
                                parsed = _parse_line_text(line)
                                if parsed:
                                    fallback_rows.append(parsed)
                except Exception:
                    continue

        # 2b) Fallback final: extracción por texto línea a línea
        import pdfplumber
        rows: List[Tuple[Optional[str], Optional[str], str, str]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                for raw_line in text.splitlines():
                    parsed = _parse_line_text(raw_line)
                    if parsed:
                        rows.append(parsed)
        # Acumular también estas filas globales
        fallback_rows.extend(rows)
    except Exception as e:
        logger.error("Error leyendo PDF con pdfplumber: %s", e)

    # Si no hay nada, error
    if not std_frames and not fallback_rows:
        raise ValueError("No fue posible reconocer los movimientos del estado de cuenta. Intenta con un PDF más nítido o diferente.")

    # Concat de estandarizados (pueden tener esquemas distintos); alineamos columnas al superset
    def align_cols(d: pd.DataFrame) -> pd.DataFrame:
        cols_needed = [
            "Fecha de Operacion", "Fecha de Cargo", "Fecha de Liquidacion",
            "Descripcion", "Referencia", "Cargos", "Abonos",
            "Operacion", "Liquidacion", "Monto"
        ]
        out = d.copy()
        for c in cols_needed:
            if c not in out.columns:
                out[c] = None
        # Si no hay Monto pero hay Cargos/Abonos, calcúlalo
        if out.get("Monto").isna().all() and ("Cargos" in out.columns or "Abonos" in out.columns):
            def _mon(r):
                c = _coerce_amount(str(r.get("Cargos"))) if pd.notna(r.get("Cargos")) else 0.0
                a = _coerce_amount(str(r.get("Abonos"))) if pd.notna(r.get("Abonos")) else 0.0
                c = c or 0.0
                a = a or 0.0
                return (a) - (c)
            out["Monto"] = out.apply(_mon, axis=1)
        return out[cols_needed]

    aligned_std = [align_cols(df) for df in std_frames] if std_frames else []
    std_all = pd.concat(aligned_std, ignore_index=True) if aligned_std else pd.DataFrame(columns=[
        "Fecha de Operacion", "Fecha de Cargo", "Fecha de Liquidacion",
        "Descripcion", "Referencia", "Cargos", "Abonos",
        "Operacion", "Liquidacion", "Monto"
    ])

    # Agregar filas fallback como DataFrame básico
    if fallback_rows:
        fb_df = pd.DataFrame(fallback_rows, columns=["Fecha de Operacion", "Fecha de Cargo", "Descripcion", "Monto"])
        # Postprocess para separar fechas al inicio de la descripción
        fb_df = _postprocess_dates(fb_df)
        # Alinear columnas
        fb_df = align_cols(fb_df)
        std_all = pd.concat([std_all, fb_df], ignore_index=True)

    # Deduplicar de forma conservadora: duplicados exactos en todas las columnas
    if not std_all.empty:
        std_all = std_all.drop_duplicates().reset_index(drop=True)

    # Postprocess fechas solo si el esquema es puramente básico (no hay columnas extendidas con datos)
    basic_cols = {"Fecha de Operacion", "Fecha de Cargo", "Descripcion", "Monto"}
    non_empty_extended = any(
        col in std_all.columns and std_all[col].notna().any()
        for col in ["Referencia", "Cargos", "Abonos", "Operacion", "Liquidacion", "Fecha de Liquidacion"]
    )
    if not non_empty_extended and set(std_all.columns) >= basic_cols:
        std_all = _postprocess_dates(std_all)

    # AI QA opcional sobre todo el conjunto
    ai_df = _ai_quality_check(std_all)
    if ai_df is not None and not ai_df.empty:
        std_all = ai_df

    # Unir originales para la hoja "Original"
    merged_orig = _merge_preserve_columns(original_frames) if original_frames else None

    return _write_excel(std_all, original_df=merged_orig)
