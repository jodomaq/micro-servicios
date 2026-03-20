"""
Router para Encuestas Regionales
CRUD de encuestas, preguntas y respuestas con aislamiento multi-tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
import json

from ..database import get_session
from ..dependencies import get_current_tenant, get_current_user, get_current_tenant_admin
from ..models import Survey, SurveyQuestion, SurveyResponse as SurveyResponseModel, User
from ..schemas import (
    SurveyCreate, SurveyUpdate, SurveyDetailResponse,
    SurveyQuestionCreate, SurveyQuestionResponse,
    SurveyResponseCreate, SurveyResponseSchema
)

router = APIRouter(prefix="/surveys", tags=["Surveys"])


# ====================================
# SURVEY CRUD
# ====================================

@router.get("/", response_model=List[SurveyDetailResponse])
async def list_surveys(
    skip: int = 0,
    limit: int = 50,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar encuestas del tenant"""
    query = select(Survey).where(Survey.tenant_id == tenant_id)
    
    if is_active is not None:
        query = query.where(Survey.is_active == is_active)
    
    query = query.order_by(Survey.created_at.desc()).offset(skip).limit(limit)
    surveys = session.exec(query).all()
    
    result = []
    for survey in surveys:
        resp_count = session.exec(
            select(func.count(SurveyResponseModel.id)).where(
                SurveyResponseModel.survey_id == survey.id
            )
        ).one()
        
        questions = session.exec(
            select(SurveyQuestion).where(
                SurveyQuestion.survey_id == survey.id
            ).order_by(SurveyQuestion.order)
        ).all()
        
        result.append(SurveyDetailResponse(
            **survey.model_dump(),
            questions=[SurveyQuestionResponse(**q.model_dump()) for q in questions],
            response_count=resp_count
        ))
    
    return result


@router.post("/", response_model=SurveyDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(
    data: SurveyCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Crear encuesta con preguntas (solo admin)"""
    survey = Survey(
        tenant_id=tenant_id,
        title=data.title,
        description=data.description,
        start_date=data.start_date,
        end_date=data.end_date,
        is_active=True,
        created_at=datetime.utcnow()
    )
    session.add(survey)
    session.commit()
    session.refresh(survey)
    
    # Crear preguntas si se proporcionaron
    questions = []
    if data.questions:
        for i, q in enumerate(data.questions):
            question = SurveyQuestion(
                survey_id=survey.id,
                tenant_id=tenant_id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                order=q.order if q.order else i
            )
            session.add(question)
            questions.append(question)
        session.commit()
        for q in questions:
            session.refresh(q)
    
    return SurveyDetailResponse(
        **survey.model_dump(),
        questions=[SurveyQuestionResponse(**q.model_dump()) for q in questions],
        response_count=0
    )


@router.get("/{survey_id}", response_model=SurveyDetailResponse)
async def get_survey(
    survey_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener encuesta con preguntas"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    questions = session.exec(
        select(SurveyQuestion).where(
            SurveyQuestion.survey_id == survey_id
        ).order_by(SurveyQuestion.order)
    ).all()
    
    resp_count = session.exec(
        select(func.count(SurveyResponseModel.id)).where(
            SurveyResponseModel.survey_id == survey_id
        )
    ).one()
    
    return SurveyDetailResponse(
        **survey.model_dump(),
        questions=[SurveyQuestionResponse(**q.model_dump()) for q in questions],
        response_count=resp_count
    )


@router.put("/{survey_id}", response_model=SurveyDetailResponse)
async def update_survey(
    survey_id: int,
    data: SurveyUpdate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Actualizar encuesta (solo admin)"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(survey, key, value)
    
    session.add(survey)
    session.commit()
    session.refresh(survey)
    
    questions = session.exec(
        select(SurveyQuestion).where(SurveyQuestion.survey_id == survey_id).order_by(SurveyQuestion.order)
    ).all()
    
    resp_count = session.exec(
        select(func.count(SurveyResponseModel.id)).where(SurveyResponseModel.survey_id == survey_id)
    ).one()
    
    return SurveyDetailResponse(
        **survey.model_dump(),
        questions=[SurveyQuestionResponse(**q.model_dump()) for q in questions],
        response_count=resp_count
    )


@router.delete("/{survey_id}")
async def deactivate_survey(
    survey_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Desactivar encuesta (solo admin)"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    survey.is_active = False
    session.add(survey)
    session.commit()
    return {"message": "Encuesta desactivada"}


# ====================================
# QUESTIONS
# ====================================

@router.post("/{survey_id}/questions", response_model=SurveyQuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    survey_id: int,
    data: SurveyQuestionCreate,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Agregar pregunta a encuesta (solo admin)"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    question = SurveyQuestion(
        survey_id=survey_id,
        tenant_id=tenant_id,
        question_text=data.question_text,
        question_type=data.question_type,
        options=data.options,
        order=data.order
    )
    session.add(question)
    session.commit()
    session.refresh(question)
    
    return SurveyQuestionResponse(**question.model_dump())


@router.delete("/{survey_id}/questions/{question_id}")
async def delete_question(
    survey_id: int,
    question_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_tenant_admin)
):
    """Eliminar pregunta de encuesta"""
    question = session.get(SurveyQuestion, question_id)
    if not question or question.survey_id != survey_id or question.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    session.delete(question)
    session.commit()
    return {"message": "Pregunta eliminada"}


# ====================================
# RESPONSES (PÚBLICO)
# ====================================

@router.post("/{survey_id}/respond", status_code=status.HTTP_201_CREATED)
async def submit_response(
    survey_id: int,
    data: SurveyResponseCreate,
    request: Request,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant)
):
    """Registrar respuesta a encuesta (puede ser público)"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    if not survey.is_active:
        raise HTTPException(status_code=400, detail="La encuesta no está activa")
    
    # Verificar fechas
    now = datetime.utcnow()
    if survey.start_date and now < survey.start_date:
        raise HTTPException(status_code=400, detail="La encuesta aún no ha iniciado")
    if survey.end_date and now > survey.end_date:
        raise HTTPException(status_code=400, detail="La encuesta ha finalizado")
    
    # Verificar duplicado
    existing = session.exec(
        select(SurveyResponseModel).where(
            SurveyResponseModel.survey_id == survey_id,
            SurveyResponseModel.user_email == data.user_email
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya se registró una respuesta con este email"
        )
    
    response = SurveyResponseModel(
        survey_id=survey_id,
        tenant_id=tenant_id,
        user_email=data.user_email,
        section_number=data.section_number,
        administrative_unit_id=data.administrative_unit_id,
        answers=data.answers,
        device_id=data.device_id,
        ip=request.client.host if request.client else None,
        created_at=datetime.utcnow()
    )
    
    session.add(response)
    session.commit()
    session.refresh(response)
    
    return {"message": "Respuesta registrada", "response_id": response.id}


# ====================================
# RESULTS
# ====================================

@router.get("/{survey_id}/results")
async def get_survey_results(
    survey_id: int,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Obtener resultados agregados de una encuesta"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    # Obtener preguntas
    questions = session.exec(
        select(SurveyQuestion).where(
            SurveyQuestion.survey_id == survey_id
        ).order_by(SurveyQuestion.order)
    ).all()
    
    # Obtener todas las respuestas
    responses = session.exec(
        select(SurveyResponseModel).where(
            SurveyResponseModel.survey_id == survey_id
        )
    ).all()
    
    total_responses = len(responses)
    
    # Agregar resultados por pregunta
    results_by_question = []
    for question in questions:
        q_result = {
            "question_id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "total_answers": 0,
            "answers_summary": {}
        }
        
        for resp in responses:
            try:
                answers = json.loads(resp.answers) if isinstance(resp.answers, str) else resp.answers
                if str(question.id) in answers:
                    answer = answers[str(question.id)]
                    q_result["total_answers"] += 1
                    
                    if question.question_type in ("multiple_choice", "rating"):
                        answer_str = str(answer)
                        q_result["answers_summary"][answer_str] = q_result["answers_summary"].get(answer_str, 0) + 1
                    else:
                        # Para texto, solo contar
                        q_result["answers_summary"]["responses"] = q_result["answers_summary"].get("responses", 0) + 1
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
        
        results_by_question.append(q_result)
    
    return {
        "survey_id": survey_id,
        "survey_title": survey.title,
        "total_responses": total_responses,
        "results_by_question": results_by_question
    }


@router.get("/{survey_id}/responses", response_model=List[SurveyResponseSchema])
async def list_survey_responses(
    survey_id: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    """Listar respuestas individuales de una encuesta"""
    survey = session.get(Survey, survey_id)
    if not survey or survey.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    
    responses = session.exec(
        select(SurveyResponseModel).where(
            SurveyResponseModel.survey_id == survey_id
        ).order_by(SurveyResponseModel.created_at.desc()).offset(skip).limit(limit)
    ).all()
    
    return [SurveyResponseSchema(**r.model_dump()) for r in responses]
