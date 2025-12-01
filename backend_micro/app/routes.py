import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from .converter_ai_vision_2 import convert_pdf_to_excel_ai_vision_2
from .converter_ai_vision import convert_pdf_to_excel_ai_vision
from .converter_ai_full import convert_pdf_to_excel_ai_full
from .converterIA import convert_pdf_to_excel_ai
from .paypal_client import create_order, capture_order, OrderRequest, CartItem, create_subscription_plan, create_subscription
from .database import get_db
from .auth import get_current_user
from .models import User, Payment, Conversion, PlanType
from .subscription_manager import (
    check_conversion_available, increment_conversion_count, 
    create_subscription as create_user_subscription, get_plan_config
)

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
async def paypal_capture_and_convert(
    body: CaptureBody,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    """Capture PayPal payment and convert PDF to Excel"""
    try:
        details = await capture_order(body.order_id)
        status = details.get("status")
        if status not in {"COMPLETED", "CAPTURED"}:
            raise HTTPException(status_code=402, detail="Pago no completado")
        
        # Record payment
        payment = Payment(
            user_id=user.id if user else None,
            payment_type="one_time",
            paypal_order_id=body.order_id,
            amount=float(details.get("amount", 20.0)),
            currency=details.get("currency", "MXN"),
            status="completed",
            description="Conversión única de PDF a Excel"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
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
        
        # Record conversion
        conversion = Conversion(
            user_id=user.id if user else None,
            payment_id=payment.id,
            upload_id=body.upload_id,
            filename=f"{body.upload_id}.pdf",
            conversion_method="ai_full",
            success=True
        )
        db.add(conversion)
        db.commit()
        
    except Exception as e:
        logger.error("Conversion error: %s", e)
        
        # Record failed conversion
        conversion = Conversion(
            user_id=user.id if user else None,
            payment_id=payment.id,
            upload_id=body.upload_id,
            filename=f"{body.upload_id}.pdf",
            conversion_method="ai_full",
            success=False,
            error_message=str(e)
        )
        db.add(conversion)
        db.commit()
        
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
async def convert_without_payment(
    body: ConvertBody,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    """
    Convert PDF to Excel - checks for subscription or requires payment
    """
    # Check if user has subscription with available conversions
    can_convert, subscription, message = check_conversion_available(db, user)
    
    if not can_convert:
        raise HTTPException(status_code=402, detail=message)
    
    tmp_dir = os.path.join(os.getcwd(), "tmp_uploads")
    pdf_path = os.path.join(tmp_dir, f"{body.upload_id}.pdf")
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado, vuelve a subir el PDF")
    
    try:
        excel_bytes = convert_pdf_to_excel_ai(pdf_path)
        
        # Record conversion
        conversion = Conversion(
            user_id=user.id if user else None,
            upload_id=body.upload_id,
            filename=f"{body.upload_id}.pdf",
            conversion_method="ai",
            success=True
        )
        db.add(conversion)
        
        # Increment subscription counter
        if subscription:
            increment_conversion_count(db, subscription)
        
        db.commit()
        
    except Exception as e:
        logger.error("Conversion error (subscription): %s", e)
        
        # Record failed conversion
        conversion = Conversion(
            user_id=user.id if user else None,
            upload_id=body.upload_id,
            filename=f"{body.upload_id}.pdf",
            conversion_method="ai",
            success=False,
            error_message=str(e)
        )
        db.add(conversion)
        db.commit()
        
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


# Subscription endpoints
class SubscriptionCreateBody(BaseModel):
    plan_type: str  # basic, standard, premium


@router.post("/subscription/create")
async def create_subscription_endpoint(
    body: SubscriptionCreateBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a PayPal subscription for the user"""
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión para suscribirte")
    
    # Validate plan type
    try:
        plan_type = PlanType(body.plan_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de plan inválido")
    
    config = get_plan_config(plan_type)
    
    try:
        # Create PayPal subscription
        subscription_data = await create_subscription(
            plan_name=config["description"],
            amount=str(config["price"])
        )
        
        # Create subscription in database
        subscription = create_user_subscription(
            db=db,
            user_id=user.id,
            plan_type=plan_type,
            paypal_subscription_id=subscription_data.get("id")
        )
        
        return {
            "subscription": subscription,
            "paypal_data": subscription_data
        }
    except Exception as e:
        logger.error("Error creating subscription: %s", e)
        raise HTTPException(status_code=500, detail="Error creando la suscripción")


class SubscriptionApproveBody(BaseModel):
    subscription_id: str  # PayPal subscription ID
    plan_type: str


@router.post("/subscription/approve")
async def approve_subscription(
    body: SubscriptionApproveBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Approve and activate a PayPal subscription"""
    if not user:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    
    try:
        plan_type = PlanType(body.plan_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de plan inválido")
    
    # Create or update subscription in database
    subscription = create_user_subscription(
        db=db,
        user_id=user.id,
        plan_type=plan_type,
        paypal_subscription_id=body.subscription_id
    )
    
    # Record payment
    config = get_plan_config(plan_type)
    payment = Payment(
        user_id=user.id,
        payment_type="subscription",
        paypal_subscription_id=body.subscription_id,
        amount=config["price"],
        currency="MXN",
        status="completed",
        description=f"Suscripción {config['description']}"
    )
    db.add(payment)
    db.commit()
    
    return {"message": "Suscripción activada exitosamente", "subscription": subscription}
