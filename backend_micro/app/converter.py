import io
import os
import re
import logging
from typing import List, Optional, Tuple

import pandas as pd
from dateutil import parser as dateparser

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


_DATE_RE = re.compile(r"\b(\d{1,2}[-/\.](\d{1,2}|[A-Za-z]{3,})[-/\.]\d{2,4})\b")
_AMOUNT_RE = re.compile(r"([+-]?\(?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})\)?)$")


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


def _write_excel(df: pd.DataFrame) -> bytes:
    # Clean and standardize columns
    df = df.copy()
    df.rename(columns={
        "fecha de operacion": "Fecha de Operacion",
        "fecha de cargo": "Fecha de Cargo",
        "descripcion": "Descripcion",
        "monto": "Monto",
    }, inplace=True)
    # Coerce types
    df["Fecha de Operacion"] = df["Fecha de Operacion"].apply(_coerce_date)
    df["Fecha de Cargo"] = df["Fecha de Cargo"].apply(_coerce_date)
    df["Descripcion"] = df["Descripcion"].astype(str)
    df["Monto"] = df["Monto"].apply(lambda x: _coerce_amount(str(x)) if pd.notna(x) else None)
    df = df.dropna(subset=["Descripcion", "Monto"]).reset_index(drop=True)

    total = df["Monto"].sum() if not df.empty else 0.0

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Movimientos")
        # Add total row
        wb = writer.book
        ws = writer.sheets["Movimientos"]
        last_row = ws.max_row + 1
        ws.cell(row=last_row, column=3, value="Total")
        ws.cell(row=last_row, column=4, value=total)
    return output.getvalue()


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

    # Strategy 1: Camelot tables (if available)
    camelot = _try_import_camelot()
    if camelot is not None:
        try:
            tables = camelot.read_pdf(pdf_path, pages=f"1-{max_pages}", flavor="stream")
            if tables and len(tables) > 0:
                collected: List[pd.DataFrame] = []
                for t in tables:
                    df = t.df
                    # First row in Camelot often is header
                    df.columns = df.iloc[0]
                    df = df[1:]
                    mapped = _map_columns(df)
                    if mapped is not None:
                        collected.append(mapped)
                if collected:
                    merged = pd.concat(collected, ignore_index=True)
                    return _write_excel(merged)
        except Exception as e:
            logger.info("Camelot parsing failed or not applicable: %s", e)

    # Strategy 2: Parse lines with pdfplumber
    try:
        import pdfplumber
        rows: List[Tuple[Optional[str], Optional[str], str, str]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                for raw_line in text.splitlines():
                    parsed = _parse_line_text(raw_line)
                    if parsed:
                        rows.append(parsed)
        if rows:
            df = pd.DataFrame(rows, columns=["Fecha de Operacion", "Fecha de Cargo", "Descripcion", "Monto"])
            return _write_excel(df)
    except Exception as e:
        logger.error("Error leyendo PDF con pdfplumber: %s", e)

    raise ValueError("No fue posible reconocer los movimientos del estado de cuenta. Intenta con un PDF más nítido o diferente.")
