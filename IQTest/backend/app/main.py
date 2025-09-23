from fastapi import FastAPI, HTTPException, Depends, Request, Response
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import List, Dict, Any

from . import models, schemas, crud, openai_client, paypal_client, logging_config
from fpdf import FPDF
from datetime import datetime
from .database import SessionLocal, init_db

logger = logging.getLogger("app")
app = FastAPI(title="IQ Test API")

# Configuración de CORS para permitir peticiones desde el frontend
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],  # Restringido para producción
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Dependency para obtener la sesión de base de datos
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

@app.on_event("startup")
async def startup():
    logging_config.configure_logging()
    await init_db()
    # Crea preguntas de prueba si no existen
    async with SessionLocal() as db:
        await crud.create_test_questions(db)

@app.get("/questions/", response_model=List[Dict[str, Any]])
async def get_questions(db: AsyncSession = Depends(get_db)):
    """
    Devuelve todas las preguntas disponibles para el test de IQ
    """
    questions = await crud.get_questions(db)
    
    result = []
    for q in questions:
        result.append({
            "id": q.id,
            "text": q.text,
            "question_type": q.question_type,
            "options": json.loads(q.options) if q.options else [],
            "difficulty": q.difficulty
        })
    
    return result

@app.post("/users/", response_model=Dict[str, Any])
async def create_user(db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo usuario anónimo y devuelve su ID
    """
    user = await crud.create_user(db)
    return {"user_id": user.id}

@app.patch("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(user_id: int, payload: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    """Actualiza nombre y/o email del usuario"""
    user = await crud.update_user(db, user_id, name=payload.name, email=payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"user_id": user.id, "name": user.name, "email": user.email}

@app.post("/submit-answers/")
async def submit_answers(answers: schemas.AnswerList, user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Recibe las respuestas del usuario y las guarda en la base de datos
    """
    try:
        await crud.save_answers(db, answers, user_id)
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al guardar respuestas: {str(e)}")

@app.post("/paypal/verify/")
async def verify_payment(payload: dict, db: AsyncSession = Depends(get_db)):
    """Verifica (o registra) un pago.

    Acepta payload flexible del frontend: {orderId, userId} (camelCase) o el esquema original.
    Si la orden ya fue capturada previamente, simplemente registra si falta el pago.
    """
    try:
        # Normalizar campos
        order_id = payload.get("orderID") or payload.get("orderId")
        user_id = payload.get("user_id") or payload.get("userId")
        if not order_id or user_id is None:
            raise HTTPException(status_code=422, detail="Faltan orderId y/o userId en el payload")

        # Obtener detalles (esto puede hacer una lectura/captura si no estaba COMPLETED)
        payment_details = await paypal_client.verify_payment(order_id)

        # Guardar pago si no existe ya (básico idempotente)
        # Reutilizamos PaypalPayment schema para persistencia
        amount_val = float(payment_details.get("amount", paypal_client.PAYPAL_AMOUNT))
        payment_schema = schemas.PaypalPayment(
            orderID=payment_details.get("id", order_id),
            user_id=int(user_id),
            amount=amount_val,
            currency=payment_details.get("currency", paypal_client.PAYPAL_CURRENCY),
            status="completed" if payment_details.get("status") == "COMPLETED" else payment_details.get("status", "unknown")
        )
        try:
            await crud.save_payment(db, payment_schema)
        except Exception as save_err:
            logger.warning("No se pudo guardar pago verificado (posible duplicado): %s", save_err)

        return {"status": "success", "payment": payment_details}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al verificar pago: {str(e)}")

@app.post("/orders", response_model=Dict[str, Any])
async def create_order(request: paypal_client.OrderRequest):
    """
    Crea una nueva orden de PayPal para iniciar el proceso de pago
    """
    try:
        order = await paypal_client.create_order(request)
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/orders/{order_id}/capture", response_model=Dict[str, Any])
async def capture_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """
    Captura una orden de PayPal para completar el pago
    """
    try:
        capture_details = await paypal_client.capture_order(order_id)
        # Si la transacción fue completada, guardamos el pago (idempotente a nivel básico)
        if capture_details.get("status") == "COMPLETED":
            try:
                amount_val = float(capture_details.get("amount", paypal_client.PAYPAL_AMOUNT))
            except (TypeError, ValueError):
                amount_val = float(paypal_client.PAYPAL_AMOUNT)
            payment_schema = schemas.PaypalPayment(
                orderID=capture_details.get("id"),
                user_id=0,  # Se actualizará en verify endpoint; o puedes pasar user en query si lo deseas
                amount=amount_val,
                currency=capture_details.get("currency", paypal_client.PAYPAL_CURRENCY),
                status="completed"
            )
            # Guardar sin bloquear si falla
            try:
                await crud.save_payment(db, payment_schema)
            except Exception as e:
                logger.warning("No se pudo guardar pago capturado automáticamente: %s", e)
        return capture_details
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/paypal/debug", response_model=Dict[str, Any])
async def paypal_debug():
    """Diagnóstico mínimo de PayPal (no expone secretos sensibles)."""
    return await paypal_client.paypal_debug_status()

@app.post("/evaluate/{user_id}", response_model=schemas.ResultResponse)
async def evaluate(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Evalúa las respuestas del usuario con OpenAI y devuelve el resultado
    """
    # Comprobar si ya existe un resultado para este usuario
    existing_result = await crud.get_result(db, user_id)
    if existing_result:
        return {
            "iq_score": existing_result.iq_score,
            "strengths": json.loads(existing_result.strengths),
            "weaknesses": json.loads(existing_result.weaknesses),
            "detailed_report": json.loads(existing_result.detailed_report),
            "certificate_url": existing_result.certificate_url
        }
    
    # Obtener respuestas del usuario
    answers = await crud.get_user_answers(db, user_id)
    if not answers:
        raise HTTPException(status_code=404, detail="No se encontraron respuestas para este usuario")
    
    # Evaluar con OpenAI
    evaluation = await openai_client.evaluate_test(answers)
    
    # Guardar resultado en la base de datos
    # Construir URL de certificado (simple slug local)
    user = await crud.get_user(db, user_id)
    name_slug = "anonimo"
    if user and user.name:
        name_slug = "-".join(user.name.lower().strip().split())[:50]
    certificate_url = f"/certificates/{user_id}-{name_slug}.pdf"

    result_data = schemas.ResultCreate(
        user_id=user_id,
        iq_score=evaluation["iq_score"],
        strengths=json.dumps(evaluation["strengths"]),
        weaknesses=json.dumps(evaluation["weaknesses"]),
        detailed_report=json.dumps(evaluation["detailed_report"]),
        certificate_url=certificate_url  # Placeholder; PDF generation pendiente
    )
    
    await crud.save_result(db, result_data)
    
    return {
        "iq_score": evaluation["iq_score"],
        "strengths": evaluation["strengths"],
        "weaknesses": evaluation["weaknesses"],
        "detailed_report": evaluation["detailed_report"],
        "certificate_url": certificate_url
    }

@app.get("/certificates/{user_id}-{slug}.pdf")
async def get_certificate_pdf(user_id: int, slug: str, db: AsyncSession = Depends(get_db)):
    result = await crud.get_result(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    strengths = json.loads(result.strengths)
    weaknesses = json.loads(result.weaknesses)
    report = json.loads(result.detailed_report)
    user = await crud.get_user(db, user_id)
    name = user.name if user and user.name else "Usuario"

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 20)
    pdf.cell(0, 15, "Certificado de Coeficiente Intelectual", ln=1, align='C')
    pdf.set_font("Helvetica", '', 14)
    pdf.cell(0, 10, f"Otorgado a: {name}", ln=1, align='C')
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"IQ: {result.iq_score}", ln=1, align='C')
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 8, "Fortalezas", ln=1)
    pdf.set_font("Helvetica", '', 11)
    for s in strengths:
        pdf.cell(0, 6, f"- {s}", ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 8, "Áreas de Mejora", ln=1)
    pdf.set_font("Helvetica", '', 11)
    for w in weaknesses:
        pdf.cell(0, 6, f"- {w}", ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 8, "Informe Detallado", ln=1)
    pdf.set_font("Helvetica", '', 11)
    for k, v in report.items():
        pdf.cell(0, 6, f"{k.capitalize()}: {v}%", ln=1)
    pdf.ln(4)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 6, f"Generado: {datetime.utcnow().isoformat()}Z", ln=1, align='R')
    pdf.cell(0, 6, f"ID Usuario: {user_id}", ln=1, align='R')

    # fpdf2 >=2.7 devuelve bytearray al usar dest='S'
    raw = pdf.output(dest='S')
    pdf_bytes = bytes(raw) if isinstance(raw, (bytearray, bytes)) else str(raw).encode('latin-1', 'ignore')
    return Response(content=pdf_bytes, media_type='application/pdf', headers={
        'Content-Disposition': f'inline; filename="certificado-{user_id}.pdf"'
    })
