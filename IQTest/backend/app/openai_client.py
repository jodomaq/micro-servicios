import os
import json
import httpx
import random
import logging
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger("openai_client")

# Cargar variables de entorno antes de leer configuraciones.
_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
try:
    if os.path.isfile(_ENV_PATH):
        load_dotenv(dotenv_path=_ENV_PATH, override=False)
    else:
        load_dotenv(override=False)
except Exception as e:
    logger.debug("[openai] No se pudo cargar .env: %s", e)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "30"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

async def evaluate_test(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evalúa las respuestas del test usando OpenAI.
    Si no hay API key configurada, genera un resultado aleatorio.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY no configurada, devolviendo mock.")
        return generate_mock_result(answers)
    
    # Preparar el mensaje para OpenAI
    prompt = prepare_prompt(answers)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "Eres un experto en psicometría y evaluación de coeficiente intelectual."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    attempt = 0
    last_error: Exception | None = None
    while attempt <= OPENAI_MAX_RETRIES:
        try:
            async with httpx.AsyncClient(timeout=OPENAI_TIMEOUT) as client:
                response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
                if response.status_code == 429:
                    raise httpx.HTTPStatusError("Rate limit", request=response.request, response=response)
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                try:
                    if "```json" in content and "```" in content.split("```json")[1]:
                        json_str = content.split("```json")[1].split("```")[0]
                        evaluation_result = json.loads(json_str)
                    else:
                        evaluation_result = json.loads(content)
                except json.JSONDecodeError:
                    logger.info("Fallo parseo JSON directo, usando heurística.")
                    evaluation_result = extract_evaluation_from_text(content, answers)
                return evaluation_result
        except httpx.HTTPStatusError as he:
            status = he.response.status_code if he.response else None
            body_snip = he.response.text[:250] if he.response and he.response.text else ""
            logger.error("OpenAI HTTP %s intento=%d body=%s", status, attempt, body_snip)
            last_error = he
            if status in {500,502,503,504,429} and attempt < OPENAI_MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
                attempt += 1
                continue
            break
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as net_err:
            logger.warning("OpenAI timeout/conexión intento=%d err=%s", attempt, net_err)
            last_error = net_err
            if attempt < OPENAI_MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
                attempt += 1
                continue
            break
        except Exception as e:
            logger.exception("Error inesperado OpenAI intento=%d", attempt)
            last_error = e
            break
    logger.warning("Fallo evaluación OpenAI tras %d intentos (%s). Usando mock.", attempt, last_error)
    return generate_mock_result(answers)

def prepare_prompt(answers: List[Dict[str, Any]]) -> str:
    """
    Prepara el prompt para enviar a OpenAI con las respuestas del usuario.
    """
    prompt = "Evalúa las siguientes respuestas de un test de coeficiente intelectual y proporciona:\n"
    prompt += "1. Una estimación del coeficiente intelectual (IQ) basada en las respuestas\n"
    prompt += "2. Una lista de fortalezas cognitivas\n"
    prompt += "3. Una lista de áreas que necesitan mejora\n"
    prompt += "4. Un informe detallado por categorías (verbal, numérico, lógico, espacial, memoria)\n\n"
    
    prompt += "Respuestas del usuario:\n"
    for i, answer in enumerate(answers, 1):
        prompt += f"Pregunta {i}: {answer['question_text']}\n"
        prompt += f"Tipo: {answer['question_type']}\n"
        prompt += f"Respuesta del usuario: {answer['answer']}\n"
        prompt += f"Respuesta correcta: {answer.get('correct_answer', 'No especificada')}\n\n"
        if answer.get('response_time_ms') is not None:
            prompt += f"Tiempo de respuesta (ms): {answer['response_time_ms']}\n\n"
    
    prompt += "Proporciona tu evaluación en formato JSON con esta estructura:\n"
    prompt += "```json\n"
    prompt += "{\n"
    prompt += '  "iq_score": 100,\n'
    prompt += '  "strengths": ["Fortaleza 1", "Fortaleza 2", ...],\n'
    prompt += '  "weaknesses": ["Debilidad 1", "Debilidad 2", ...],\n'
    prompt += '  "detailed_report": {\n'
    prompt += '    "verbal": 80,\n'
    prompt += '    "numerical": 85,\n'
    prompt += '    "logical": 90,\n'
    prompt += '    "spatial": 75,\n'
    prompt += '    "memory": 70\n'
    prompt += "  }\n"
    prompt += "}\n```"
    
    return prompt

def extract_evaluation_from_text(text: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extrae la evaluación de un texto no estructurado.
    Fallback cuando no se puede parsear el JSON de la respuesta.
    """
    # Valores por defecto
    iq_score = 100
    strengths = ["Capacidad de razonamiento", "Comprensión verbal"]
    weaknesses = ["Velocidad de procesamiento", "Memoria de trabajo"]
    detailed_report = {
        "verbal": 80,
        "numerical": 80,
        "logical": 80,
        "spatial": 80,
        "memory": 80
    }
    
    # Buscar puntaje IQ en el texto
    if "iq_score" in text.lower() or "coeficiente" in text.lower() or "puntaje" in text.lower():
        for line in text.split("\n"):
            if any(term in line.lower() for term in ["iq", "coeficiente", "puntaje"]):
                # Extraer números de la línea
                import re
                numbers = re.findall(r'\d+', line)
                if numbers and 50 <= int(numbers[0]) <= 150:
                    iq_score = int(numbers[0])
                    break
    
    # Buscar fortalezas
    if "fortalezas" in text.lower() or "strengths" in text.lower():
        strengths_section = ""
        in_strengths = False
        for line in text.split("\n"):
            if any(term in line.lower() for term in ["fortalezas:", "strengths:"]):
                in_strengths = True
                continue
            if in_strengths and line.strip() and not any(term in line.lower() for term in ["debilidades:", "weaknesses:"]):
                strengths_section += line + " "
            if in_strengths and any(term in line.lower() for term in ["debilidades:", "weaknesses:"]):
                break
        
        if strengths_section:
            # Extraer items con viñetas o números
            import re
            strength_items = re.split(r'[•\-\d+\.\*]\s+', strengths_section)
            strengths = [item.strip() for item in strength_items if item.strip()]
    
    # Buscar debilidades
    if "debilidades" in text.lower() or "weaknesses" in text.lower():
        weaknesses_section = ""
        in_weaknesses = False
        for line in text.split("\n"):
            if any(term in line.lower() for term in ["debilidades:", "weaknesses:"]):
                in_weaknesses = True
                continue
            if in_weaknesses and line.strip() and not any(term in line.lower() for term in ["informe:", "report:"]):
                weaknesses_section += line + " "
            if in_weaknesses and any(term in line.lower() for term in ["informe:", "report:"]):
                break
        
        if weaknesses_section:
            # Extraer items con viñetas o números
            import re
            weakness_items = re.split(r'[•\-\d+\.\*]\s+', weaknesses_section)
            weaknesses = [item.strip() for item in weakness_items if item.strip()]
    
    # Contar respuestas correctas por tipo
    correct_by_type = {
        "verbal": 0,
        "numerical": 0,
        "logical": 0,
        "spatial": 0,
        "mathematical": 0
    }
    
    total_by_type = {
        "verbal": 0,
        "numerical": 0,
        "logical": 0,
        "spatial": 0,
        "mathematical": 0
    }
    
    for answer in answers:
        question_type = answer["question_type"]
        if question_type == "mathematical":
            question_type = "numerical"  # Normalizar el tipo
        
        if question_type in total_by_type:
            total_by_type[question_type] += 1
            if answer.get("correct_answer") and answer["answer"] == answer["correct_answer"]:
                correct_by_type[question_type] += 1
    
    # Calcular porcentajes
    for qtype in total_by_type:
        if total_by_type[qtype] > 0:
            percentage = (correct_by_type[qtype] / total_by_type[qtype]) * 100
            detailed_report[qtype] = round(percentage)
        else:
            detailed_report[qtype] = 80  # Valor por defecto
    
    # Asegurarse de que memory existe en el informe
    if "memory" not in detailed_report:
        detailed_report["memory"] = 80
    
    return {
        "iq_score": iq_score,
        "strengths": strengths[:3],  # Limitar a 3 fortalezas
        "weaknesses": weaknesses[:3],  # Limitar a 3 debilidades
        "detailed_report": detailed_report
    }

def generate_mock_result(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Genera un resultado aleatorio para fines de demostración.
    """
    # Calcular un puntaje IQ basado en respuestas correctas
    correct_answers = sum(1 for answer in answers if answer.get("correct_answer") and answer["answer"] == answer["correct_answer"])
    total_questions = len(answers)
    
    # Porcentaje de respuestas correctas
    if total_questions > 0:
        correct_percentage = (correct_answers / total_questions)
    else:
        correct_percentage = 0.7  # Por defecto, 70%
    
    # IQ básico: 100 es el promedio, ajustado por respuestas correctas
    base_iq = 100
    iq_range = 50  # El rango de variación (desde 75 hasta 125)
    
    # Ajustar IQ basado en porcentaje correcto y algo de aleatoriedad
    # Calcular impacto por velocidad: menor tiempo promedio -> ligero aumento
    times = [a.get('response_time_ms') for a in answers if a.get('response_time_ms') is not None]
    if times:
        avg_ms = sum(times) / len(times)
        # Normalizar: asumimos 3s (3000 ms) como neutral. Más rápido aumenta, más lento reduce hasta +/-7 pts
        speed_factor = max(-7, min(7, (3000 - avg_ms) / 3000 * 7))
    else:
        speed_factor = 0
    iq_score = int(base_iq + (correct_percentage - 0.5) * iq_range + speed_factor + random.randint(-5, 5))
    
    # Limitar el IQ dentro de un rango razonable
    iq_score = max(75, min(140, iq_score))
    
    # Contar respuestas por tipo
    responses_by_type = {}
    for answer in answers:
        qtype = answer["question_type"]
        if qtype not in responses_by_type:
            responses_by_type[qtype] = {"total": 0, "correct": 0}
        
        responses_by_type[qtype]["total"] += 1
        if answer.get("correct_answer") and answer["answer"] == answer["correct_answer"]:
            responses_by_type[qtype]["correct"] += 1
    
    # Calcular fortalezas y debilidades basadas en tipos de preguntas
    strengths = []
    weaknesses = []
    detailed_report = {}
    
    for qtype, counts in responses_by_type.items():
        # Normalizar los tipos para los informes
        report_type = qtype
        if qtype == "mathematical":
            report_type = "numerical"
        
        if counts["total"] > 0:
            score = (counts["correct"] / counts["total"]) * 100
            detailed_report[report_type] = round(score)
            
            # Determinar fortalezas y debilidades
            if score >= 80:
                if qtype == "verbal":
                    strengths.append("Excelente comprensión verbal")
                elif qtype == "mathematical" or qtype == "numerical":
                    strengths.append("Fuerte capacidad numérica")
                elif qtype == "logical":
                    strengths.append("Buen razonamiento lógico")
                elif qtype == "spatial":
                    strengths.append("Buena inteligencia espacial")
            
            if score <= 60:
                if qtype == "verbal":
                    weaknesses.append("Comprensión verbal por mejorar")
                elif qtype == "mathematical" or qtype == "numerical":
                    weaknesses.append("Capacidad numérica por desarrollar")
                elif qtype == "logical":
                    weaknesses.append("Razonamiento lógico a fortalecer")
                elif qtype == "spatial":
                    weaknesses.append("Percepción espacial a mejorar")
    
    # Asegurarnos de tener al menos algunas fortalezas y debilidades
    all_strengths = [
        "Buena memoria de trabajo",
        "Razonamiento lógico efectivo",
        "Comprensión verbal sólida",
        "Excelente capacidad de abstracción",
        "Pensamiento lateral creativo"
    ]
    
    all_weaknesses = [
        "Velocidad de procesamiento por mejorar",
        "Memoria de trabajo a desarrollar",
        "Atención al detalle por fortalecer",
        "Pensamiento abstracto a mejorar",
        "Flexibilidad cognitiva a desarrollar"
    ]
    
    # Agregar fortalezas aleatorias si no hay suficientes
    while len(strengths) < 3:
        new_strength = random.choice(all_strengths)
        if new_strength not in strengths:
            strengths.append(new_strength)
    
    # Agregar debilidades aleatorias si no hay suficientes
    while len(weaknesses) < 3:
        new_weakness = random.choice(all_weaknesses)
        if new_weakness not in weaknesses:
            weaknesses.append(new_weakness)
    
    # Asegurarse de que todos los tipos necesarios estén en el informe detallado
    required_types = ["verbal", "numerical", "logical", "spatial", "memory"]
    for rtype in required_types:
        if rtype not in detailed_report:
            detailed_report[rtype] = random.randint(65, 90)
    
    return {
        "iq_score": iq_score,
        "strengths": strengths[:3],  # Limitar a 3 fortalezas
        "weaknesses": weaknesses[:3],  # Limitar a 3 debilidades
        "detailed_report": detailed_report
    }
