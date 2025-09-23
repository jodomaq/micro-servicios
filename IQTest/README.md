# IQ Test App (Producción)

Aplicación full-stack para administrar un test de IQ y entregar un informe detallado con pago mediante PayPal y evaluación (real o simulada) vía OpenAI.

## Stack
Backend: FastAPI, SQLAlchemy async, MySQL/MariaDB, httpx
Frontend: React + Vite, Axios, PayPal JS SDK

## Estructura
```
backend/app/*.py
frontend/src/*
```

## Variables de Entorno Backend (`backend/.env`)
```
DATABASE_URL=mysql+aiomysql://USER:PASS@HOST/iqtest
OPENAI_API_KEY=sk-xxxxx              # Opcional: si falta se genera resultado mock
PAYPAL_CLIENT_ID=live_client_id
PAYPAL_CLIENT_SECRET=live_client_secret
PAYPAL_CURRENCY=MXN
PAYPAL_AMOUNT=20.00
PAYPAL_ENV=live                      # live | sandbox
FRONTEND_ORIGIN=https://midominio.com
PAYPAL_RETURN_URL=https://midominio.com/pago-ok
PAYPAL_CANCEL_URL=https://midominio.com/pago-cancelado
```

## Variables Frontend (`frontend/.env`)
```
VITE_API_BASE=/api
VITE_PAYPAL_CLIENT_ID=live_client_id_publico
```

## Instalación Rápida
```
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:
```
cd frontend
npm install
npm run build
```
Servir `frontend/dist` tras un reverse proxy que dirija `/api/` al backend.

## Endpoints Principales
POST /users/
POST /submit-answers/?user_id=
POST /evaluate/{user_id}
POST /orders
POST /orders/{order_id}/capture
POST /paypal/verify/
GET  /questions/

## Notas de Producción
- CORS restringido a `FRONTEND_ORIGIN`.
- Eliminado modo de simulación PayPal (falla si faltan credenciales).
- `openai_client` produce mock si no hay API key (puedes desactivarlo exigiendo la variable).
- Logging estructurado recomendado (agregar `LOG_LEVEL` y configurar `logging.basicConfig`).

## Hardening / Mejoras Sugeridas
- Añadir autenticación y rate limiting.
- Generación real de PDF para `certificate_url` server-side.
- Tests automáticos (unit + integración) para flujos críticos.
- Persistir versión de preguntas y permitir recalcular resultados.

## Flujo Básico
1. Crear usuario anónimo.
2. Enviar respuestas (`submit-answers`).
3. Crear orden PayPal y capturar pago.
4. Verificar pago (`/paypal/verify/`).
5. Evaluar test (`/evaluate/{user_id}`).
6. Mostrar resultado y permitir descargar certificado (frontend genera PDF).

## Licencia
Uso interno / educativo (ajustar según necesidades).
