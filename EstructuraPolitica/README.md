# Sistema Multi-Tenant de Gestión Político-Electoral

Sistema SaaS multi-tenant completo para gestión político-electoral con arquitectura moderna, seguridad robusta, integración de pagos con PayPal, y cumplimiento de normativas de privacidad (GDPR, LGPD, LFPDPPP).

## 🏗️ Arquitectura

- **Backend**: FastAPI + SQLModel + MariaDB/MySQL
- **Frontend Principal**: React 18 + Material-UI + Vite
- **Frontend Dashboard**: React 19 + Recharts + Leaflet + Vite
- **Frontend Asistencia**: React 19 + Vite (minimalista)
- **Autenticación**: OAuth2 (Google y Microsoft) + JWT
- **Pagos**: PayPal REST API
- **Multi-Tenancy**: Aislamiento por `tenant_id` en todas las tablas

## 📋 Características Principales

### Módulos del Sistema

1. **Comités y Promovidos** (✅ IMPLEMENTADO)
   - Registro de comités con jerarquía administrativa
   - Gestión de 10 integrantes por comité
   - Upload de documentos
   - Validación de clave INE única

2. **Asistencia a Eventos** (🔜 PRÓXIMO)
   - Registro con OAuth
   - Geolocalización GPS
   - Device fingerprinting

3. **Encuestas Regionales** (🔜 PRÓXIMO)
   - Creador de encuestas
   - Vista pública para responder
   - Analytics por región

4. **Dashboard Estadístico** (🔜 PRÓXIMO)
   - Vista de árbol jerárquico
   - Gráficas con Recharts
   - Mapas interactivos con Leaflet
   - Exportación de datos

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.10+
- MariaDB/MySQL 8.0+
- Node.js 18+
- npm o yarn

### Configuración del Backend

1. **Clonar y configurar entorno virtual**:
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**:
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Configuraciones requeridas en `.env`**:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY` (generar una clave segura)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`
- `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`

4. **Crear base de datos y datos iniciales**:
```bash
python scripts/create_database.py
```

Esto creará:
- Todas las tablas necesarias
- 4 planes de suscripción (Básico, Intermedio, Premium, Enterprise)
- 1 tenant demo (subdomain: `demo`)
- 1 usuario admin demo
- 1 super administrador

5. **Iniciar servidor de desarrollo**:
```bash
uvicorn app.main:app --reload
```

El API estará disponible en: `http://localhost:8000`
- Documentación interactiva: `http://localhost:8000/docs`
- Documentación alternativa: `http://localhost:8000/redoc`

### Configuración del Frontend (Próximo)

```bash
cd comites
npm install
npm run dev
```

## 📁 Estructura del Proyecto

```
EstructuraPolitica/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Aplicación FastAPI principal
│   │   ├── config.py            # Configuración centralizada
│   │   ├── database.py          # Conexión a BD
│   │   ├── models.py            # Modelos SQLModel (multi-tenant)
│   │   ├── schemas.py           # Schemas Pydantic
│   │   ├── auth.py              # OAuth2 + JWT
│   │   ├── dependencies.py      # Dependencias reutilizables
│   │   ├── middleware/
│   │   │   └── tenant_middleware.py
│   │   └── routers/
│   │       ├── committees.py    # ✅ IMPLEMENTADO
│   │       ├── admin.py         # 🔜 Próximo
│   │       ├── users.py
│   │       ├── events.py
│   │       └── ...
│   ├── scripts/
│   │   ├── create_database.py   # ✅ IMPLEMENTADO
│   │   ├── create_tenant.py
│   │   └── populate_administrative_units.py
│   ├── uploads/                 # Archivos por tenant
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── comites/                     # 🔜 Frontend React + MUI
├── dashboard/                   # 🔜 Frontend Dashboard
├── asistencia/                  # 🔜 Frontend Asistencia
└── landing/                     # 🔜 Landing page + Registro
```

## 🗄️ Base de Datos

### Tablas Principales

Todas las tablas incluyen `tenant_id` para aislamiento multi-tenant:

- **Tenants & Suscripciones**: `tenants`, `subscription_plans`, `payments`
- **Usuarios**: `users`, `user_assignments`, `user_consents`, `arco_requests`
- **Jerarquía**: `administrative_units` (STATE → REGION → DISTRICT → MUNICIPALITY → SECTION)
- **Comités**: `committees`, `committee_members`, `committee_types`, `committee_documents`
- **Eventos**: `events`, `attendances`
- **Encuestas**: `surveys`, `survey_questions`, `survey_responses`
- **Auditoría**: `audit_logs`, `payment_webhook_logs`

## 🔐 Seguridad y Multi-Tenancy

### Aislamiento de Datos

1. **Middleware de Tenant**: Identifica tenant por:
   - Subdominio (ej: `accion.micro-servicios.com.mx`)
   - Header `X-Tenant-ID` (development)

2. **Validación Automática**: Todas las queries incluyen filtro por `tenant_id`

3. **Dependencias de Seguridad**:
   - `get_current_tenant()`: Obtiene tenant actual
   - `get_current_user()`: Usuario autenticado con validación de tenant
   - `get_current_tenant_admin()`: Valida rol de admin
   - `check_tenant_limits()`: Verifica límites de suscripción

### Autenticación

- OAuth2 con Google y Microsoft
- JWT propios con claims: `user_id`, `tenant_id`, `email`, `roles`
- Registro automático de consentimientos (GDPR/LGPD)
- Audit logs de todos los logins

## 📡 API Endpoints

### Comités (✅ IMPLEMENTADO)

```
GET    /api/committees              # Listar comités (con filtros)
POST   /api/committees              # Crear comité
GET    /api/committees/{id}         # Obtener comité
PUT    /api/committees/{id}         # Actualizar comité
DELETE /api/committees/{id}         # Eliminar comité

GET    /api/committees/{id}/members         # Listar integrantes
POST   /api/ committees/{id}/members         # Agregar integrante
PUT    /api/committees/{id}/members/{mid}   # Actualizar integrante
DELETE /api/committees/{id}/members/{mid}   # Eliminar integrante

GET    /api/committees/{id}/documents       # Listar documentos
POST   /api/committees/{id}/documents       # Subir documento
DELETE /api/committees/{id}/documents/{did} # Eliminar documento
```

**Headers requeridos**:
- `Authorization: Bearer {jwt_token}`
- `X-Tenant-ID: {tenant_id}` (opcional, se detecta por subdomain)

### Próximos Endpoints

- `/api/auth/*` - Autenticación OAuth
- `/api/admin/*` - Panel de administración
- `/api/users/*` - Gestión de usuarios
- `/api/administrative-units/*` - Unidades administrativas
- `/api/events/*` - Eventos
- `/api/attendance/*` - Asistencia
- `/api/surveys/*` - Encuestas
- `/api/dashboard/*` - Estadísticas
- `/api/public/*` - Endpoints públicos (registro, PayPal)

## 🎨 Personalización por Tenant

Cada tenant puede configurar:
- **Logo**: URL de logotipo personalizado
- **Colores**: Primario y secundario (hex)
- **Nombre**: Nombre de la organización
- **Features**: Módulos habilitados según plan

## 💳 Planes de Suscripción

| Plan | Precio/mes | Usuarios | Comités | Almacenamiento | Módulos |
|------|-----------|----------|---------|----------------|---------|
| Básico | $499 MXN | 5 | 50 | 1 GB | Dashboard |
| Intermedio | $999 MXN | 20 | 200 | 5 GB | Dashboard + Asistencia |
| Premium | $1,999 MXN | 50 | 1,000 | 20 GB | Todos + API |
| Enterprise | Contactar | Ilimitado | Ilimitado | Ilimitado | Todo + Custom |

## 📊 Estado del Proyecto

### ✅ Completado (Fase 1 + Comités Backend)

- [x] Estructura de proyecto
- [x] Configuración de base de datos
- [x] Modelos SQLModel completos con multi-tenancy
- [x] Middleware de identificación de tenant
- [x] Sistema de autenticación OAuth2 (Google/Microsoft)
- [x] Dependencias de seguridad y autorización
- [x] Router completo de comités (CRUD + members + documents)
- [x] Script de inicialización de base de datos

### 🔜 Próximos Pasos

1. Completar routers de backend:
   - `auth.py` - Login con OAuth
   - `admin.py` - Panel de super admin
   - `users.py` - Gestión de usuarios
   - `administrative_units.py` - Jerarquía
   - `committee_types.py` - Tipos de comité
   - `events.py` - Eventos
   - `attendance.py` - Asistencia
   - `surveys.py` - Encuestas
   - `dashboard.py` - Estadísticas
   - `public.py` - Registro y PayPal
   - `paypal.py` - Integración de pagos
   - `privacy.py` - ARCO y privacidad

2. Implementar frontends:
   - Frontend "comites" (React 18 + MUI)
   - Frontend "dashboard" (React 19 + Recharts)
   - Frontend "asistencia" (React 19 minimalista)
   - Landing page + Registro público

3. Testing y deployment
4. Documentación completa

## 📚 Documentación

-  [API Documentation](docs/API_DOCUMENTATION.md) (🔜 Próximo)
- [Admin Guide](docs/ADMIN_GUIDE.md) (🔜 Próximo)
- [User Guide](docs/USER_GUIDE.md) (🔜 Próximo)
- [Privacy Compliance](docs/PRIVACY_COMPLIANCE.md) (🔜 Próximo)

## 🤝 Soporte

Para soporte técnico o consultas:
- Email: soporte@micro-servicios.com.mx
- Documentación: https://docs.micro-servicios.com.mx

## 📝 Licencia

Propietario - Todos los derechos reservados

---

**Desarrollado con** ❤️ **usando FastAPI, React, y tecnologías modernas**
