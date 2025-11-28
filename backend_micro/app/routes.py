import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pydantic import BaseModel

from .converter_ai_vision_2 import convert_pdf_to_excel_ai_vision_2
from .converter_ai_vision import convert_pdf_to_excel_ai_vision
from .converter_ai_full import convert_pdf_to_excel_ai_full
from .paypal_client import create_order, capture_order, OrderRequest, CartItem

logger = logging.getLogger("routes")

router = APIRouter(prefix="/converter", tags=["excel-converter"])


class CreateOrderBody(BaseModel):
    # front can pass an optional id, but we just send a fixed cart with one item
    pass


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Formato inválido: solo PDF")
    # store temporarily
    tmp_dir = os.path.join(os.getcwd(), "tmp_uploads")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_id = str(uuid.uuid4())
    pdf_path = os.path.join(tmp_dir, f"{tmp_id}.pdf")
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Archivo vacío")
        with open(pdf_path, "wb") as f:
            f.write(content)
        # return token to reference later
        return {"upload_id": tmp_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload error: %s", e)
        raise HTTPException(status_code=500, detail="Error al subir el archivo")


@router.post("/paypal/create-order")
async def paypal_create_order(_: CreateOrderBody):
    try:
        data = await create_order(OrderRequest(cart=[CartItem(id="excel_conversion", quantity=1)]))
        return JSONResponse(content=data)
    except Exception as e:
        logger.error("PayPal create order error: %s", e)
        raise HTTPException(status_code=500, detail="Error creando la orden de PayPal")


class CaptureBody(BaseModel):
    order_id: str
    upload_id: str


@router.post("/paypal/capture-and-convert")
async def paypal_capture_and_convert(body: CaptureBody):
    try:
        details = await capture_order(body.order_id)
        status = details.get("status")
        if status not in {"COMPLETED", "CAPTURED"}:
            raise HTTPException(status_code=402, detail="Pago no completado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PayPal capture error: %s", e)
        raise HTTPException(status_code=500, detail="Error capturando pago de PayPal")

    # Proceed to convert
    tmp_dir = os.path.join(os.getcwd(), "tmp_uploads")
    pdf_path = os.path.join(tmp_dir, f"{body.upload_id}.pdf")
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado, vuelve a subir el PDF")
    try:
        # Estrategia FULL (PDF completo) para máxima fidelidad
        excel_bytes = convert_pdf_to_excel_ai_full(pdf_path)
    except Exception as e:
        logger.error("Conversion error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # clean up temp file
        try:
            os.remove(pdf_path)
        except Exception:
            pass

    filename = "estado_cuenta.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class ConvertBody(BaseModel):
    """Body for direct conversion without payment (testing mode)."""
    upload_id: str


@router.post("/convert")
async def convert_without_payment(body: ConvertBody):
    """
    Directly convert the previously uploaded PDF to Excel without PayPal capture.
    Intended for local/testing flows used by the frontend.
    """
    tmp_dir = os.path.join(os.getcwd(), "tmp_uploads")
    pdf_path = os.path.join(tmp_dir, f"{body.upload_id}.pdf")
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado, vuelve a subir el PDF")
    try:
        excel_bytes = convert_pdf_to_excel_ai_vision_2(pdf_path)
    except Exception as e:
        logger.error("Conversion error (no-paypal): %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        try:
            os.remove(pdf_path)
        except Exception:
            pass

    filename = "estado_cuenta.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
