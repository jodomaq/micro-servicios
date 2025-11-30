import io
import os
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path


import pandas as pd

from .converter import _write_excel  # reuse the existing Excel writer

logger = logging.getLogger("converter_ai")


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


def _extract_pdf_text_by_page(pdf_path: str, max_pages: int = 10) -> List[str]:
    """Extract raw text from each page of the PDF using multiple strategies.
    
    Strategy order:
    1. pdfplumber with optimized settings for tables
    2. pdfplumber with different tolerance settings
    3. OCR with pytesseract as fallback
    """
    texts: List[str] = []
    
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = min(len(pdf.pages), max_pages)
            logger.info(f"Procesando {total_pages} páginas del PDF...")
            
            for idx, page in enumerate(pdf.pages[:max_pages], start=1):
                txt = None
                
                # Strategy 1: Table extraction with multiple table settings
                try:
                    # Try different table strategies
                    table_settings = [
                        {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                        {"vertical_strategy": "text", "horizontal_strategy": "text"},
                        {"vertical_strategy": "lines_strict", "horizontal_strategy": "lines_strict"},
                    ]
                    
                    for settings in table_settings:
                        tables = page.extract_tables(table_settings=settings)
                        if tables and any(tables):
                            # Convert tables to text format
                            table_text = []
                            for table in tables:
                                if table:
                                    for row in table:
                                        if row and any(cell for cell in row if cell):
                                            table_text.append(" | ".join([str(cell or "").strip() for cell in row]))
                            if table_text:
                                txt = "\n".join(table_text)
                                logger.debug(f"Página {idx}: Extraída usando tablas con {settings} ({len(txt)} chars)")
                                break
                except Exception as e:
                    logger.debug(f"Página {idx}: Fallo extracción de tablas: {e}")
                
                # Strategy 2: Text extraction with tight tolerances and layout
                if not txt or len(txt.strip()) < 100:
                    try:
                        txt = page.extract_text(
                            x_tolerance=1,
                            y_tolerance=1,
                            layout=True,
                            use_text_flow=True
                        ) or ""
                        if len(txt.strip()) > 100:
                            logger.debug(f"Página {idx}: Extraída con layout mode ({len(txt)} chars)")
                    except Exception as e:
                        logger.debug(f"Página {idx}: Fallo extracción con layout: {e}")
                
                # Strategy 3: Text extraction with looser tolerances
                if not txt or len(txt.strip()) < 100:
                    try:
                        txt = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                        if len(txt.strip()) > 100:
                            logger.debug(f"Página {idx}: Extraída con tolerancia alta ({len(txt)} chars)")
                    except Exception as e:
                        logger.debug(f"Página {idx}: Fallo extracción con tolerancia alta: {e}")
                
                # Strategy 4: Extract words and reconstruct
                if not txt or len(txt.strip()) < 100:
                    try:
                        words = page.extract_words(
                            x_tolerance=2,
                            y_tolerance=2,
                            keep_blank_chars=False
                        )
                        if words:
                            # Group words by top position (y-coordinate)
                            from collections import defaultdict
                            lines = defaultdict(list)
                            for word in words:
                                # Round to group words on same line
                                line_y = round(word['top'])
                                lines[line_y].append(word)
                            
                            # Sort and join
                            reconstructed = []
                            for y in sorted(lines.keys()):
                                line_words = sorted(lines[y], key=lambda w: w['x0'])
                                reconstructed.append(" ".join([w['text'] for w in line_words]))
                            

                            txt = "\n".join(reconstructed)
                            if len(txt.strip()) > 100:
                                logger.debug(f"Página {idx}: Reconstruida desde palabras ({len(txt)} chars)")
                    except Exception as e:
                        logger.debug(f"Página {idx}: Fallo reconstrucción desde palabras: {e}")
                
                # Strategy 5: OCR fallback for scanned PDFs
                if not txt or len(txt.strip()) < 100:
                    try:
                        txt = _ocr_page(page)
                        if len(txt.strip()) > 100:
                            logger.debug(f"Página {idx}: Extraída con OCR ({len(txt)} chars)")
                    except Exception as e:
                        logger.warning(f"Página {idx}: OCR falló: {e}")
                        txt = ""
                
                # Log a sample of the extracted text for debugging
                if txt and len(txt.strip()) > 10:
                    texts.append(txt)
                    sample = txt[:200].replace('\n', ' ')
                    logger.info(f"Página {idx}/{total_pages}: {len(txt)} caracteres - Muestra: {sample}...")
                else:
                    logger.warning(f"Página {idx}/{total_pages}: Contenido vacío o insuficiente (<100 chars)")
                    texts.append(txt or "")  # Keep to maintain page numbering
        
        logger.info(f"Total de páginas procesadas: {len(texts)}, con contenido útil: {len([t for t in texts if len(t.strip()) > 100])}")
        return texts
        
    except Exception as e:
        raise RuntimeError(f"No se pudo leer el PDF: {e}")


def _ocr_page(page) -> str:
    """OCR fallback using pytesseract when text extraction fails."""
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Convert page to image
        img = page.to_image(resolution=300)
        pil_img = img.original
        
        # Apply OCR
        text = pytesseract.image_to_string(pil_img, lang='spa')
        return text
    except ImportError:
        logger.debug("pytesseract no disponible, saltando OCR")
        return ""
    except Exception as e:
        logger.debug(f"Error en OCR: {e}")
        return ""


def _call_openai_for_rows(pages_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Call OpenRouter (Claude Sonnet 4.5) with the given pages payload and expect strict JSON rows.

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

    model = os.getenv("OPENAI_QA_MODEL", "google/gemini-2.0-flash-001")

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/your-org/backend_micro",
                "X-Title": "Bank Statement Converter"
            }
        )
    except Exception as e:
        raise RuntimeError(f"No se pudo inicializar OpenAI SDK: {e}")

    system = (
        "Eres un analista experto de estados de cuenta bancarios. Recibirás texto extraído de un PDF bancario (por páginas). "
        "Debes extraer SOLO los movimientos/transacciones reales y devolverlos en JSON ESTRICTO.\n\n"
        "IMPORTANTE sobre la estructura del estado de cuenta:\n"
        "- Típicamente hay DOS COLUMNAS separadas: una para CARGOS (débitos/gastos) y otra para ABONOS (créditos/ingresos)\n"
        "- Los CARGOS reducen el saldo (son negativos en contabilidad)\n"
        "- Los ABONOS aumentan el saldo (son positivos en contabilidad)\n"
        "- Algunas filas solo tienen cargo, otras solo abono, nunca ambos en la misma fila\n"
        "- Puede haber columnas de fechas (operación, cargo, liquidación)\n"
        "- Las transacciones pueden tener formato: FECHA | DESCRIPCION | REFERENCIA | CARGO | ABONO\n\n"
        "EJEMPLOS de formatos comunes:\n"
        "- '15/01 | Compra en tienda | REF123 | 150.00 | '\n"
        "- '16/01 | Depósito | | | 500.00'\n"
        "- 'Fecha Operacion | Fecha Cargo | Descripcion | Cargos | Abonos'\n\n"
        "Requisitos de salida (JSON):\n"
        "- Estructura OBLIGATORIA: {\"rows\": [ ... ]}\n"
        "- Cada elemento de rows es un objeto con estas claves (usa null si no existe en el PDF):\n"
        "  * Fecha de Operacion (string formato DD/MM/YYYY o similar)\n"
        "  * Fecha de Cargo (string)\n"
        "  * Fecha de Liquidacion (string)\n"
        "  * Descripcion (string)\n"
        "  * Referencia (string)\n"
        "  * Cargos (número positivo o null)\n"
        "  * Abonos (número positivo o null)\n"
        "  * Operacion (string/número según el PDF)\n"
        "  * Liquidacion (string/número según el PDF)\n"
        "  * Monto (número: positivo para abonos, negativo para cargos)\n\n"
        "- Para 'Cargos': extrae el valor numérico SIN signos ni símbolos ($, comas)\n"
        "- Para 'Abonos': extrae el valor numérico SIN signos ni símbolos\n"
        "- Para 'Monto': calcula como (Abonos - Cargos) o el valor que represente el impacto en el saldo\n"
        "- NO incluyas: encabezados de tabla, subtítulos, saldos totales, información del titular\n"
        "- NO inventes transacciones\n"
        "- Si NO hay transacciones en la página, devuelve: {\"rows\": []}\n"
        "- SIEMPRE devuelve JSON válido, nunca texto explicativo adicional"
    )

    user_payload = {
        "instrucciones": (
            "Analiza las siguientes páginas del estado de cuenta bancario. "
            "Extrae TODAS las transacciones que encuentres. "
            "Si una página no tiene movimientos (portada, resumen, etc.), marca rows como array vacío. "
            "Devuelve SOLO JSON válido con la estructura {\"rows\": [...]}"
        ),
        "pages": pages_payload,
    }

    # Log payload summary for debugging
    total_chars = sum(len(p.get("text", "")) for p in pages_payload)
    logger.info(f"Enviando {len(pages_payload)} páginas a IA ({total_chars} caracteres totales)")
    
    # Log first page sample
    if pages_payload:
        first_page_sample = pages_payload[0].get("text", "")[:300]
        logger.debug(f"Muestra de primera página enviada: {first_page_sample}")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            temperature=0.1,
            max_tokens=8000,  # Aumentado para documentos grandes
        )
        content = resp.choices[0].message.content
        
        logger.debug("OpenRouter response: %s", content[:1000] if content else "EMPTY")
        
        if not content or content.strip() == "":
            raise RuntimeError("OpenRouter devolvió respuesta vacía")
            
    except Exception as e:
        raise RuntimeError(f"Error llamando a OpenRouter: {e}")

    try:
        content = _strip_markdown_json(content)
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("JSON inválido recibido: %s", content[:1000] if content else "EMPTY")
        raise RuntimeError(f"La respuesta no es JSON válido: {e}")

    rows = data.get("rows")
    if not isinstance(rows, list):
        logger.error("Payload sin 'rows': %s", data)
        raise RuntimeError("La respuesta de OpenRouter no contiene 'rows' válidas.")
    
    logger.debug(f"IA devolvió {len(rows)} filas")
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
    
    # Filter out pages with insufficient content
    min_chars = 50  # Lowered threshold
    pages_with_content = [(i+1, txt) for i, txt in enumerate(pages_text) if len(txt.strip()) >= min_chars]
    
    logger.info(f"Total de páginas con texto útil (>{min_chars} chars): {len(pages_with_content)}/{len(pages_text)}")
    
    if not pages_with_content:
        raise ValueError(f"Ninguna página tiene contenido suficiente (>{min_chars} caracteres). Verifica el PDF.")

    # Build payloads in batches to control token usage
    batched_rows: List[dict] = []
    batch: List[Dict[str, Any]] = []
    
    for page_num, txt in pages_with_content:
        batch.append({"page": page_num, "text": txt})
        
        if len(batch) >= pages_per_call:
            try:
                logger.info(f"Procesando lote de páginas {batch[0]['page']}-{batch[-1]['page']} con IA...")
                rows = _call_openai_for_rows(batch)
                batched_rows.extend(rows)
                logger.info(f"Obtenidas {len(rows)} filas del lote")
            except Exception as e:
                logger.error(f"OpenAI falló en lote de páginas {batch[0]['page']}-{batch[-1]['page']}: {e}")
            batch = []
    
    # Process remaining pages
    if batch:
        try:
            logger.info(f"Procesando último lote de páginas {batch[0]['page']}-{batch[-1]['page']} con IA...")
            rows = _call_openai_for_rows(batch)
            batched_rows.extend(rows)
            logger.info(f"Obtenidas {len(rows)} filas del último lote")
        except Exception as e:
            logger.error(f"OpenAI falló en último lote: {e}")

    if not batched_rows:
        # Log detailed diagnostic info
        logger.error("La IA no devolvió movimientos. Diagnóstico:")
        logger.error(f"- Páginas procesadas: {len(pages_text)}")
        logger.error(f"- Páginas con contenido: {len(pages_with_content)}")
        for i, (pnum, txt) in enumerate(pages_with_content[:3]):  # First 3 pages
            logger.error(f"- Página {pnum} muestra: {txt[:200]}")
        raise ValueError(
            f"La IA no devolvió movimientos. "
            f"Páginas procesadas: {len(pages_with_content)}. "
            f"Verifica que el PDF contenga transacciones en formato tabular. "
            f"Considera revisar el formato del documento o ajustar la extracción."
        )

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
