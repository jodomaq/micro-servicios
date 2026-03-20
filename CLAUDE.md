# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Monorepo con múltiples SaaS independientes. Todos los backends están **fusionados en `backend_micro/`** como un solo servidor FastAPI. Los frontends son apps React+Vite independientes que apuntan al mismo backend.

| SaaS | Frontend | Backend (módulo) | DB |
|------|----------|-------------------|----|
| Excel Converter | `ExcelConverter/` | `backend_micro/app/` (raíz) | SQLite |
| Estructura Política | `EstructuraPolitica/{comites,dashboard,asistencia,registro}/` | `backend_micro/app/estructura_politica/` | MariaDB |
| Mesa de Regalos | `mesa_de_regalos/frontend/` | `backend_micro/app/mesa_regalos/` | MariaDB |
| IQ Test | `IQTest/frontend/` | `IQTest/backend/` (standalone) | MySQL |

## Comandos

### Backend unificado
```bash
cd backend_micro
pip install -r requirements.txt
cp .env.example .env   # rellenar credenciales
uvicorn main:app --reload --port 8000
```

### Frontend (cualquier app React)
```bash
cd <directorio-frontend>   # ej: EstructuraPolitica/comites
npm install
cp .env.example .env       # configurar VITE_API_URL=http://localhost:8000
npm run dev
npm run build              # genera dist/
```

### IQ Test (backend standalone — excepción)
```bash
cd IQTest/backend
pip install -r requirements.txt
uvicorn main:app --reload
pytest                     # tests
pytest tests/test_api.py   # test individual
```

## Arquitectura del Backend Unificado

`backend_micro/main.py` carga condicionalmente todos los módulos con `try/except`, por lo que el servidor arranca aunque falte configuración de una base de datos específica.

### Estructura de módulos
```
backend_micro/
├── main.py                          # Punto de entrada unificado
├── app/
│   ├── (Excel Converter)            # auth_routes, routes, subscription_routes, etc.
│   ├── estructura_politica/         # Sistema multi-tenant electoral
│   │   ├── config.py                # Prefijo de env: EP_
│   │   ├── database.py              # SQLModel + MySQL
│   │   ├── models.py
│   │   ├── middleware/
│   │   │   └── tenant_middleware.py # Detecta tenant por subdominio o X-Tenant-ID header
│   │   └── routers/                 # 12 routers: auth, committees, events, surveys, etc.
│   └── mesa_regalos/                # Wishlist con Mercado Libre
│       ├── core/config.py           # Prefijo de env: MR_
│       ├── core/database.py         # SQLAlchemy + MySQL
│       ├── models/
│       ├── routers/
│       └── services/                # scraper.py (ML), paypal_service.py, auth_service.py
```

### Rutas API por servicio
| Servicio | Prefijo de rutas |
|----------|-----------------|
| Excel Converter | `/auth/...`, `/converter/...`, `/subscriptions/...` |
| Estructura Política | `/api/auth/...`, `/api/committees/...`, `/api/events/...`, etc. |
| Mesa de Regalos | `/api/v1/auth/...` |
| General | `/send-email`, `/health` |

## Variables de Entorno

Todas en `backend_micro/.env` (una sola instancia). Cada servicio usa su propio prefijo para evitar conflictos:

| Prefijo | Servicio |
|---------|---------|
| *(sin prefijo)* | Excel Converter + SMTP de contacto |
| `EP_` | Estructura Política (ej: `EP_DB_HOST`, `EP_PAYPAL_CLIENT_ID`) |
| `MR_` | Mesa de Regalos (ej: `MR_DATABASE_URL`, `MR_PAYPAL_CLIENT_ID`) |

Ver `backend_micro/.env.example` para la lista completa.

## Multi-Tenancy (Estructura Política)

- `TenantMiddleware` intercepta **todos** los requests. Para rutas no-EP, falla silenciosamente y continúa.
- En desarrollo (`EP_ALLOW_LOCALHOST=true`): usa header `X-Tenant-ID` o el primer tenant activo de la DB.
- En producción: detecta tenant por subdominio (ej: `accion.micro-servicios.com.mx`).
- Todos los modelos EP incluyen `tenant_id` para aislamiento de datos.

## Estructura Política — Frontends múltiples

Cuatro apps React independientes que comparten el mismo backend:
- `comites/` — MUI 6, gestión de comités (módulo principal)
- `dashboard/` — Recharts + Leaflet, estadísticas y mapas
- `asistencia/` — control de asistencia por GPS
- `registro/` — registro de nuevos usuarios/tenants

## Mesa de Regalos — Reglas de código

- Todo texto de UI y mensajes de API **en español mexicano** (nunca inglés en la interfaz).
- Scraper solo permite `mercadolibre.com.mx` (whitelist en `services/scraper.py`).
- Modelos: `GiftTable` (no Wishlist), `Gift` (no Item).
- Commits en español.

## Convenciones

- **Python**: snake_case, type hints, imports relativos dentro de cada módulo
- **React**: componentes funcionales + hooks, PascalCase
- **No Docker/CI**: despliegue manual — backend con Uvicorn/Gunicorn, frontends con `dist/` en Vercel/Netlify/S3
