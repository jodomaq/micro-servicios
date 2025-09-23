# Excel Converter Backend (FastAPI)

Nuevos endpoints incluidos bajo el prefijo `/converter`:

- POST `/converter/upload` — Acepta un `file` (PDF) y devuelve `{ upload_id }`.
- POST `/converter/paypal/create-order` — Crea una orden de PayPal por $20 MXN.
- POST `/converter/paypal/capture-and-convert` — Cuerpo: `{ order_id, upload_id }`. Verifica/captura el pago y devuelve un archivo XLSX.

Requisitos de entorno (variables):
- `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET`
- `PAYPAL_ENV` (`live` o `sandbox`, por defecto `live`)
- `PAYPAL_CURRENCY` (default `MXN`)
- `PAYPAL_AMOUNT` (default `20.00`)

Instalación de dependencias (desde `backend_micro`):
```
pip install -r requirements.txt
```

Ejecutar localmente:
```
uvicorn main:app --reload --port 8000
```

Notas:
- Límite de 10 páginas por PDF.
- Se intenta primero extraer tablas (Camelot). Si no, se hace parsing de líneas (pdfplumber).
- El Excel generado incluye columnas: Fecha de Operacion, Fecha de Cargo, Descripcion, Monto y al final una fila con el Total.