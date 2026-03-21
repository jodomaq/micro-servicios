from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from . import models, schemas

logger = logging.getLogger("iqtest.crud")

# Ruta al banco de preguntas JSON (relativa a este módulo)
_QUESTIONS_JSON = Path(__file__).parent.parent.parent.parent / "IQTest" / "files" / "iq_test_50_questions.json"

# Funciones CRUD para User
async def create_user(db: AsyncSession) -> models.User:
    """Crea un nuevo usuario anónimo"""
    db_user = models.User()
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Obtiene un usuario por su ID"""
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    return result.scalars().first()

async def update_user(db: AsyncSession, user_id: int, name: Optional[str] = None, email: Optional[str] = None) -> Optional[models.User]:
    """Actualiza campos simples de un usuario"""
    user = await get_user(db, user_id)
    if not user:
        return None
    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    await db.commit()
    await db.refresh(user)
    return user

# Funciones CRUD para Question
async def create_question(db: AsyncSession, question: schemas.QuestionCreate) -> models.Question:
    """Crea una nueva pregunta"""
    options_json = json.dumps(question.options)
    db_question = models.Question(
        text=question.text,
        question_type=question.question_type,
        options=options_json,
        correct_answer=question.correct_answer,
        difficulty=question.difficulty
    )
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question

async def get_questions(db: AsyncSession) -> List[models.Question]:
    """Obtiene todas las preguntas disponibles"""
    result = await db.execute(select(models.Question)
                              .order_by(func.random())
                              .limit(20))
    return result.scalars().all()

async def create_test_questions(db: AsyncSession) -> None:
    """Siembra las preguntas del banco JSON si la tabla está vacía.

    Carga primero desde IQTest/files/iq_test_50_questions.json (50 preguntas).
    Si el archivo no existe, usa el conjunto mínimo de respaldo (9 preguntas).
    """
    result = await db.execute(select(func.count()).select_from(models.Question))
    if result.scalar() > 0:
        return

    raw_questions: List[Dict[str, Any]] = []

    # Intentar cargar desde el JSON externo
    if _QUESTIONS_JSON.exists():
        try:
            data = json.loads(_QUESTIONS_JSON.read_text(encoding="utf-8"))
            raw_questions = data.get("questions", [])
            logger.info("Banco de preguntas cargado desde %s (%d preguntas)", _QUESTIONS_JSON, len(raw_questions))
        except Exception as exc:
            logger.warning("No se pudo leer %s: %s — usando preguntas de respaldo", _QUESTIONS_JSON, exc)
            raw_questions = []

    # Respaldo si no hay JSON
    if not raw_questions:
        logger.info("Usando banco de preguntas de respaldo (9 preguntas)")
        raw_questions = _FALLBACK_QUESTIONS

    for q in raw_questions:
        # options puede ser una lista o un string JSON "[\"A\", \"B\"]"
        opts = q.get("options", [])
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except Exception:
                opts = [opts]

        question = schemas.QuestionCreate(
            text=q["text"],
            question_type=q.get("question_type", "logical"),
            options=opts,
            correct_answer=q["correct_answer"],
            difficulty=float(q.get("difficulty", 1.0)),
        )
        await create_question(db, question)

    logger.info("Base de datos sembrada con %d preguntas", len(raw_questions))


# Preguntas de respaldo si el archivo JSON no está disponible
_FALLBACK_QUESTIONS: List[Dict[str, Any]] = [
    {"text": "¿Qué número continúa la secuencia? 2, 4, 8, 16, ...",
     "options": ["24", "32", "30", "64"], "correct_answer": "32",
     "question_type": "logical", "difficulty": 1.0},
    {"text": "Si todos los zorros son astutos y algunos astutos son rápidos, entonces:",
     "options": ["Todos los zorros son rápidos", "Algunos zorros son rápidos",
                 "Ningún zorro es rápido", "No se puede determinar"],
     "correct_answer": "No se puede determinar", "question_type": "logical", "difficulty": 1.5},
    {"text": "Si A=1, B=2, C=3... ¿cuánto vale CEREBRO?",
     "options": ["64", "66", "68", "70"], "correct_answer": "66",
     "question_type": "logical", "difficulty": 1.2},
    {"text": "Identifica la palabra que no pertenece al grupo:",
     "options": ["Manzana", "Plátano", "Tomate", "Zanahoria"],
     "correct_answer": "Zanahoria", "question_type": "verbal", "difficulty": 1.0},
    {"text": "Completa la analogía: Libro es a Leer como Comida es a...",
     "options": ["Cocinar", "Comer", "Hambre", "Restaurante"],
     "correct_answer": "Comer", "question_type": "verbal", "difficulty": 1.0},
    {"text": "¿Cuál es la raíz cuadrada de 144?",
     "options": ["12", "14", "16", "18"], "correct_answer": "12",
     "question_type": "mathematical", "difficulty": 1.0},
    {"text": "Si x + y = 10 y x - y = 4, ¿cuánto vale x?",
     "options": ["5", "6", "7", "8"], "correct_answer": "7",
     "question_type": "mathematical", "difficulty": 1.3},
    {"text": "¿Qué figura completa la secuencia: cuadrado, círculo, triángulo, ...?",
     "options": ["Cuadrado", "Triángulo", "Círculo", "Hexágono"],
     "correct_answer": "Cuadrado", "question_type": "spatial", "difficulty": 1.2},
    {"text": "Si doblas este patrón en cruz, ¿qué forma obtendrás?",
     "options": ["Cubo", "Pirámide", "Cilindro", "Cono"],
     "correct_answer": "Cubo", "question_type": "spatial", "difficulty": 1.5},
]

# Funciones CRUD para Response/Answer
async def save_answers(db: AsyncSession, answers: schemas.AnswerList, user_id: int) -> None:
    """Guarda las respuestas de un usuario"""
    # Verificar que el usuario existe
    user = await get_user(db, user_id)
    if not user:
        user = await create_user(db)
        user_id = user.id
    
    # Guardar cada respuesta
    for answer in answers.answers:
        db_response = models.Response(
            user_id=user_id,
            question_id=answer.questionId,
            answer=answer.answer
        )
        db.add(db_response)
    
    await db.commit()

async def get_user_answers(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    """Obtiene las respuestas de un usuario con las preguntas correspondientes"""
    # Consulta para obtener respuestas y preguntas relacionadas
    result = await db.execute(
        select(models.Response, models.Question)
        .join(models.Question, models.Response.question_id == models.Question.id)
        .filter(models.Response.user_id == user_id)
    )
    
    rows = result.all()
    answers = []
    
    for response, question in rows:
        answers.append({
            "question_id": question.id,
            "question_text": question.text,
            "question_type": question.question_type,
            "answer": response.answer,
            "correct_answer": question.correct_answer
        })
    
    return answers

# Funciones CRUD para Result
async def save_result(db: AsyncSession, result: schemas.ResultCreate) -> models.Result:
    """Guarda el resultado de la evaluación"""
    db_result = models.Result(
        user_id=result.user_id,
        iq_score=result.iq_score,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        detailed_report=result.detailed_report,
        certificate_url=result.certificate_url
    )
    db.add(db_result)
    await db.commit()
    await db.refresh(db_result)
    return db_result

async def get_result(db: AsyncSession, user_id: int) -> Optional[models.Result]:
    """Obtiene el resultado de un usuario"""
    result = await db.execute(select(models.Result).filter(models.Result.user_id == user_id))
    return result.scalars().first()

# Funciones CRUD para Payment
async def save_payment(db: AsyncSession, payment: schemas.PaypalPayment) -> models.Payment:
    """Guarda la información de un pago"""
    db_payment = models.Payment(
        user_id=payment.user_id,
        paypal_order_id=payment.orderID,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment

async def get_payment(db: AsyncSession, payment_id: int) -> Optional[models.Payment]:
    """Obtiene un pago por su ID"""
    result = await db.execute(select(models.Payment).filter(models.Payment.id == payment_id))
    return result.scalars().first()

async def get_user_payment(db: AsyncSession, user_id: int) -> Optional[models.Payment]:
    """Obtiene el último pago de un usuario"""
    result = await db.execute(
        select(models.Payment)
        .filter(models.Payment.user_id == user_id)
        .order_by(models.Payment.created_at.desc())
    )
    return result.scalars().first()
