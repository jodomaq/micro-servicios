# ExcelConverter

Frontend en Vite + React y backend en FastAPI (reutilizando `backend_micro`) para convertir estados de cuenta en PDF a Excel tras pago con PayPal.

## Endpoints backend
- POST `/converter/upload` -> devuelve `{ upload_id }`
- POST `/converter/paypal/create-order` -> crea orden PayPal (20 MXN por defecto)
- POST `/converter/paypal/capture-and-convert` -> body: `{ order_id, upload_id }` -> devuelve XLSX

## Variables de entorno necesarias (backend)
- `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET`
- `PAYPAL_ENV` (opcional: `sandbox` o `live`, por defecto `live`)
- `PAYPAL_CURRENCY` (default `MXN`), `PAYPAL_AMOUNT` (default `20.00`)

## Ejecutar backend
1. Crear/activar tu venv e instalar requerimientos en `backend_micro`.
2. Iniciar server: `uvicorn main:app --reload --port 8000`

## Ejecutar frontend
1. `cd ExcelConverter/frontend`
2. `npm install`
3. `npm run dev`

Crea (opcional) `.env` con:
```
VITE_API_BASE=http://localhost:8000
```
