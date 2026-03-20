# PROMPT PARA DESARROLLO DE SISTEMA MULTI-TENANT DE GESTIÓN POLÍTICO-ELECTORAL

## ARQUITECTURA GENERAL DEL SISTEMA

Desarrolla un sistema completo de gestión político-electoral con arquitectura **multi-tenant (SaaS)** que permita a múltiples clientes (organizaciones políticas) usar la misma plataforma de manera aislada, cada uno con su propio espacio, datos, configuración visual (logotipos, colores) y usuarios.

### STACK TECNOLÓGICO

**Backend:**
- Python 3.10+ con FastAPI
- Base de datos: MariaDB/MySQL con PyMySQL
- SQLModel para ORM
- Autenticación OAuth2 (Google y Microsoft/Azure AD)
- JWT para tokens
- Estructura modular con routers

**Frontend:**
- **Frontend 1 - "comites"**: React 18+ con Vite, Material-UI (MUI), OAuth Google/Microsoft
- **Frontend 2 - "dashboard"**: React 19+ con Vite, diseño personalizado, React Query, Recharts, Leaflet
- **Frontend 3 - "asistencia"**: React 19+ con Vite, minimalista para captura de asistencias
- Diseño responsivo mobile-first
- Navegación con menú hamburguesa estilo Material Design

**DevOps:**
- Servidor: Debian 12 VPS
- Web Server: Nginx
- Base de datos: MariaDB
- Despliegue separado para cada frontend

---

## PRINCIPIOS DE ARQUITECTURA MULTI-TENANT

### 1. MODELO DE DATOS MULTI-TENANT

**Tabla Principal: `Tenant` (Cliente/Organización)**
```sql
- id (PK)
- name: Nombre de la organización política
- subdomain: Subdominio único (ej: "partido-accion.micro-servicios.com.mx")
- logo_url: URL del logotipo del cliente
- primary_color: Color primario en hex (ej: "#1976d2")
- secondary_color: Color secundario en hex
- is_active: Estado activo/inactivo
- subscription_plan: Plan de suscripción (básico, intermedio, premium)
- subscription_expires_at: Fecha de expiración de la suscripción
- max_users: Límite de usuarios según plan
- max_committees: Límite de comités según plan
- created_at: Fecha de creación
- contact_email: Email de contacto del cliente
- contact_phone: Teléfono de contacto
```

**TODAS las tablas del sistema DEBEN incluir:**
- `tenant_id` (FK a Tenant) con índice
- Restricción: Todas las consultas DEBEN filtrar por `tenant_id` automáticamente

**Implementación de Aislamiento:**
1. Usar dependencia FastAPI que inyecte `tenant_id` automáticamente en todas las operaciones
2. Middleware que identifique el tenant por:
   - Subdominio (preferido)
   - Header HTTP personalizado (`X-Tenant-ID`)
   - Parámetro en token JWT
3. Validación estricta: Un usuario de un tenant NO puede acceder a datos de otro

### 2. GESTIÓN DE USUARIOS MULTI-TENANT

**Tabla: `User`**
```sql
- id (PK)
- tenant_id (FK, index) → CRÍTICO para aislamiento
- email: Único DENTRO del tenant (no global)
- name: Nombre completo
- phone: Teléfono celular
- picture_url: URL de foto de perfil
- created_at
- last_login_at
- is_active
```

**Roles y Permisos:**
- SUPER_ADMIN: Administrador global del sistema SaaS (no pertenece a ningún tenant)
- TENANT_ADMIN: Administrador del cliente/organización
- COORDINADOR_ESTATAL
- DELEGADO_REGIONAL
- COORDINADOR_DISTRITAL
- COORDINADOR_MUNICIPAL
- COORDINADOR_SECCIONAL
- PRESIDENTE_COMITE
- CAPTURISTA

### 3. ESTRUCTURA DE CARPETAS DEL PROYECTO

```
/proyecto-raiz
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py (TODOS con tenant_id)
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── dependencies.py (incluye get_current_tenant)
│   │   ├── middleware/
│   │   │   └── tenant_middleware.py
│   │   └── routers/
│   │       ├── admin.py (gestión de tenants - solo SUPER_ADMIN)
│   │       ├── committees.py
│   │       ├── documents.py
│   │       ├── attendance.py
│   │       ├── dashboard.py
│   │       ├── committee_types.py
│   │       └── ocr.py
│   ├── scripts/
│   │   ├── create_database.py
│   │   ├── populate_administrative_units.py
│   │   └── create_tenant.py (script para nuevos clientes)
│   ├── uploads/ (organizar por tenant: uploads/{tenant_id}/)
│   ├── requirements.txt
│   └── .env.example
├── comites/ (Frontend principal)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── CommitteeForm.jsx
│   │   │   ├── CommitteeList.jsx
│   │   │   ├── CommitteeExplorer.jsx
│   │   │   ├── MemberForm.jsx
│   │   │   ├── DocumentUpload.jsx
│   │   │   └── TenantThemeProvider.jsx (NUEVO - tema dinámico)
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx
│   │   │   └── TenantContext.jsx (NUEVO)
│   │   ├── services/
│   │   │   ├── api.js (con tenant_id en headers)
│   │   │   └── auth.js
│   │   └── App.jsx
│   └── package.json
├── dashboard/ (Frontend administrativo/estadístico)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AdministrativeTreeView.jsx
│   │   │   ├── StatsCards.jsx
│   │   │   ├── Charts.jsx
│   │   │   └── MapView.jsx
│   │   └── App.jsx
│   └── package.json
├── asistencia/ (Frontend de asistencia a eventos)
│   ├── src/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## MÓDULOS DEL SISTEMA

### MÓDULO 1: REGISTRO DE COMITÉS Y PROMOVIDOS

**Características:**

1. **Registro de Comités**
   - Nombre del comité
   - Número de sección
   - Tipo de comité (validado contra tabla CommitteeType configurable por tenant)
   - Responsable (nombre del usuario que crea el comité)
   - Vinculación a unidad administrativa jerárquica
   - Datos del presidente: nombre, email, teléfono, clave de afiliación

2. **Registro de Integrantes** (10 personas por comité)
   - Formulario validado con React Hook Form + Yup
   - Campos:
     * Nombre completo
     * Clave INE (única)
     * Teléfono celular
     * Email de Gmail
     * Número de sección
     * Nombre del político que lo invitó

3. **Gestión de Documentos**
   - Ícono de clip por comité
   - Subida de imágenes desde cámara del dispositivo
   - Almacenamiento en `uploads/{tenant_id}/{committee_id}/`
   - Vista previa e impresión de actas

4. **Estructura Jerárquica de Unidades Administrativas**

**Tabla: `AdministrativeUnit`**
```sql
- id (PK)
- tenant_id (FK, index)
- name: Nombre de la unidad (ej: "Distrito 1", "Morelia")
- code: Código oficial (ej: número de sección)
- unit_type: ENUM ('STATE','REGION','DISTRICT','MUNICIPALITY','SECTION')
- parent_id: FK a sí misma (auto-referencia)
- created_at
- seccion_municipio_id: Referencia a tabla Seccion (opcional)
- seccion_distrito_id: Referencia a tabla Seccion (opcional)
```

**Jerarquía:**
```
COORDINACIÓN ESTATAL (STATE)
  └── COORDINADORES REGIONALES (REGION)
        └── COORDINADORES DISTRITALES (DISTRICT)
              └── COORDINADORES MUNICIPALES (MUNICIPALITY)
                    └── COORDINADORES SECCIONALES / COMITÉS (SECTION)
                          └── PROMOTORES DEL VOTO (CommitteeMember)
                                └── PERSONAS PROMOVIDAS
```

**Tabla: `UserAssignment`**
```sql
- id (PK)
- tenant_id (FK, index)
- user_id (FK)
- administrative_unit_id (FK)
- role: INT (1=Coord. Estatal, 2=Delegado Regional, 3=Coord. Distrital, etc.)
- created_at
```

5. **Tabla Seccion (Catálogo Electoral - opcional)**
```sql
- id (PK)
- tenant_id (FK, index)
- municipio: ID del municipio
- nombre_municipio
- distrito: ID del distrito
- nombre_distrito
- distrito_federal
```

**Script de Población:**
- Leer datos de archivo CSV o base de datos externa
- Poblar automáticamente la jerarquía de unidades administrativas
- Sincronizar con tabla Seccion

---

### MÓDULO 2: ASISTENCIA A EVENTOS

**Frontend Independiente: "asistencia"**

**Características:**
1. Acceso público por enlace único por evento
2. Registro de asistencia mediante:
   - OAuth Google o Microsoft
   - Captura automática de:
     * Email del asistente
     * Ubicación GPS (latitude, longitude, accuracy)
     * Device ID (fingerprinting)
     * User Agent
     * IP del dispositivo
     * Timezone
3. Tabla: `Attendance`
   ```sql
   - id (PK)
   - tenant_id (FK, index)
   - event_id (FK a tabla Event)
   - provider: 'google' | 'microsoft'
   - provider_user_id
   - email
   - name
   - device_id
   - user_agent
   - ip
   - latitude (DECIMAL)
   - longitude (DECIMAL)
   - accuracy (INT)
   - timezone
   - created_at
   ```

4. Tabla: `Event`
   ```sql
   - id (PK)
   - tenant_id (FK, index)
   - name: Nombre del evento
   - description
   - event_date
   - location_name
   - administrative_unit_id (FK - opcional)
   - created_by (FK a User)
   - is_active
   - created_at
   ```

---

### MÓDULO 3: ENCUESTAS REGIONALES

**Características:**
1. Encuesta pública con autenticación OAuth
2. Tabla: `Survey`
   ```sql
   - id (PK)
   - tenant_id (FK, index)
   - title
   - description
   - is_active
   - start_date
   - end_date
   - created_at
   ```

3. Tabla: `SurveyQuestion`
   ```sql
   - id (PK)
   - survey_id (FK)
   - tenant_id (FK, index)
   - question_text
   - question_type: 'multiple_choice' | 'text' | 'rating'
   - options: JSON (para opciones de respuesta)
   - order
   ```

4. Tabla: `SurveyResponse`
   ```sql
   - id (PK)
   - survey_id (FK)
   - tenant_id (FK, index)
   - user_email
   - section_number: Sección del encuestado
   - administrative_unit_id (FK - opcional)
   - answers: JSON
   - device_id
   - ip
   - created_at
   ```

---

### MÓDULO 4: DASHBOARD ESTADÍSTICO

**Frontend Independiente: "dashboard"**

**Sub-módulos:**

#### 4.1 Dashboard de Comités
- Comités por municipio, distrito, sección (vista de árbol expandible)
- Comités por coordinador
- Promovidos por referente político
- Gráficas con Recharts:
  * Comités por tipo
  * Crecimiento temporal
  * Distribución territorial

#### 4.2 Dashboard de Asistencia
- Listado de asistentes por evento
- Cantidad de asistentes por evento
- Mapa interactivo (Leaflet) con puntos de eventos realizados
- Heatmap de asistencia por región

#### 4.3 Dashboard de Encuestas
- Listado de tópicos y preferencias
- Cantidad de encuestados
- Resultados por pregunta (gráficas)
- Análisis por región/sección

#### 4.4 Vista de Árbol Jerárquico
- Componente `AdministrativeTreeView.jsx`
- Expandible/colapsable con símbolo '+'
- Muestra contadores recursivos:
  * Número de comités en cada nivel
  * Número de integrantes en cada nivel
  * Usuarios asignados por nivel
- Filtros por tipo de unidad

---

## IMPLEMENTACIÓN DE MULTI-TENANCY

### Backend

**1. Middleware de Tenant** (`app/middleware/tenant_middleware.py`)
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extraer tenant por subdominio
        host = request.headers.get("host", "")
        subdomain = host.split(".")[0]
        
        # O por header
        tenant_header = request.headers.get("X-Tenant-ID")
        
        # Validar y cargar tenant
        # ... lógica de validación ...
        
        request.state.tenant_id = tenant_id
        request.state.tenant = tenant_obj
        
        response = await call_next(request)
        return response
```

**2. Dependencia para Inyección** (`app/dependencies.py`)
```python
from fastapi import Depends, HTTPException, Request

async def get_current_tenant(request: Request):
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=400, detail="Tenant no identificado")
    return request.state.tenant_id

async def get_current_tenant_obj(request: Request):
    if not hasattr(request.state, "tenant"):
        raise HTTPException(status_code=400, detail="Tenant no identificado")
    return request.state.tenant
```

**3. Uso en Routers**
```python
@router.get("/committees")
async def get_committees(
    tenant_id: int = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    committees = session.exec(
        select(Committee).where(
            Committee.tenant_id == tenant_id
        )
    ).all()
    return committees
```

**4. Configuración de Uploads por Tenant**
```python
# En config.py
UPLOAD_DIR = "uploads"

def get_tenant_upload_dir(tenant_id: int):
    path = f"{UPLOAD_DIR}/{tenant_id}"
    os.makedirs(path, exist_ok=True)
    return path
```

### Frontend

**1. TenantContext** (`comites/src/contexts/TenantContext.jsx`)
```javascript
import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const TenantContext = createContext();

export const TenantProvider = ({ children }) => {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Detectar tenant por subdominio o localStorage
    const loadTenant = async () => {
      try {
        const subdomain = window.location.hostname.split('.')[0];
        const response = await axios.get(`/api/tenant/by-subdomain/${subdomain}`);
        setTenant(response.data);
      } catch (error) {
        console.error('Error loading tenant:', error);
      } finally {
        setLoading(false);
      }
    };
    loadTenant();
  }, []);

  return (
    <TenantContext.Provider value={{ tenant, loading }}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => useContext(TenantContext);
```

**2. TenantThemeProvider** (`comites/src/components/TenantThemeProvider.jsx`)
```javascript
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { useTenant } from '../contexts/TenantContext';

export const TenantThemeProvider = ({ children }) => {
  const { tenant } = useTenant();

  const theme = createTheme({
    palette: {
      primary: {
        main: tenant?.primary_color || '#1976d2',
      },
      secondary: {
        main: tenant?.secondary_color || '#dc004e',
      },
    },
  });

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};
```

**3. Configuración de API con Tenant** (`comites/src/services/api.js`)
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Interceptor para añadir tenant_id en headers
api.interceptors.request.use((config) => {
  const tenantId = localStorage.getItem('tenant_id');
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }
  
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});

export default api;
```

---

## SISTEMA DE AUTENTICACIÓN

### Backend

**Soporte para:**
1. Google OAuth2
2. Microsoft/Azure AD OAuth2

**Configuración** (`.env`)
```bash
# Google OAuth
GOOGLE_CLIENT_ID=tu_client_id
GOOGLE_CLIENT_SECRET=tu_client_secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=tu_client_id
MICROSOFT_CLIENT_SECRET=tu_client_secret
MICROSOFT_TENANT_ID=common

# JWT
SECRET_KEY=tu_secret_key_muy_seguro
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**Flujo de Autenticación:**
1. Usuario hace login con Google/Microsoft en frontend
2. Frontend recibe token de proveedor
3. Frontend envía token a backend: `POST /auth/google` o `POST /auth/microsoft`
4. Backend valida token con proveedor
5. Backend busca/crea usuario en la base de datos (filtrando por tenant_id)
6. Backend genera JWT propio con claims: `user_id`, `tenant_id`, `email`, `roles`
7. Frontend almacena JWT y lo usa en todas las requests

---

## REQUISITOS DE DISEÑO

### Diseño Responsivo Mobile-First
- 90% de usuarios en dispositivos móviles
- Menú hamburguesa estilo Material Design
- Breakpoints: móvil (< 768px), tablet (768-1024px), desktop (> 1024px)

### Experiencia de Usuario
- Interfaz sencilla y amigable
- Formularios validados con mensajes claros
- Feedback visual (spinners, toasts, snackbars)
- Navegación intuitiva

### Personalización Visual por Tenant
- Logotipo personalizado en AppBar
- Colores primario y secundario configurables
- Nombre de la organización en títulos

---

## PANEL DE SUPER ADMINISTRADOR

**Acceso:** Solo usuarios con rol `SUPER_ADMIN` (no pertenecen a ningún tenant)

**Funcionalidades:**
1. **Gestión de Tenants (Clientes)**
   - Crear nuevo tenant
   - Editar configuración (colores, logos, nombre)
   - Activar/desactivar tenant
   - Gestionar suscripciones y límites
   - Ver estadísticas por tenant

2. **Gestión de Usuarios del Sistema**
   - Ver todos los usuarios de todos los tenants
   - Crear SUPER_ADMIN adicionales
   - Auditoría de accesos

3. **Monitoreo Global**
   - Dashboard con métricas agregadas
   - Estado de suscripciones
   - Uso de recursos por tenant

**Router:** `/super-admin/*` (con verificación de rol SUPER_ADMIN)

---

## PANEL DE ADMINISTRADOR DE TENANT

**Acceso:** Usuarios con rol `TENANT_ADMIN` dentro de su tenant

**Funcionalidades:**
1. **Gestión de Usuarios del Tenant**
   - Crear usuarios
   - Asignar roles
   - Desactivar usuarios

2. **Configuración de Tipos de Comité**
   - Agregar/editar tipos personalizados (maestros, transportistas, etc.)

3. **Gestión de Unidades Administrativas**
   - Ver jerarquía completa
   - Crear/editar unidades
   - Asignar coordinadores

4. **Asignaciones Jerárquicas**
   - Asignar usuarios a unidades administrativas con roles específicos

5. **Configuración Visual**
   - Subir logotipo
   - Configurar colores

**Router:** `/admin/*` (con verificación de `tenant_id` y rol TENANT_ADMIN)

---

## SCRIPTS DE INICIALIZACIÓN

### 1. Crear Base de Datos
```bash
cd backend
python scripts/create_database.py
```

### 2. Crear Primer Tenant (Cliente)
```bash
python scripts/create_tenant.py \
  --name "Partido Acción" \
  --subdomain "accion" \
  --admin-email "admin@partidoaccion.com" \
  --admin-name "José Domínguez"
```

**Este script debe:**
- Crear registro en tabla Tenant
- Crear usuario TENANT_ADMIN
- Crear estructura básica (estado por defecto)
- Generar credenciales de acceso

### 3. Poblar Unidades Administrativas (por tenant)
```bash
python scripts/populate_administrative_units.py --tenant-id 1 --csv-file secciones.csv
```

**Este script debe:**
- Leer CSV con datos de secciones, distritos, municipios
- Crear jerarquía automáticamente
- Vincular con tabla Seccion

---

## DEPENDENCIAS PRINCIPALES

### Backend (`requirements.txt`)
```
fastapi==0.111.0
uvicorn==0.30.1
sqlmodel==0.0.21
python-multipart==0.0.9
PyJWT==2.9.0
google-auth==2.33.0
google-auth-oauthlib==1.2.1
msal==1.30.0
python-dotenv==1.0.1
email-validator==2.2.0
Pillow==10.4.0
requests==2.31.0
mariadb>=1.1,<2
pymysql>=1.0,<2
openpyxl==3.1.5
fpdf2==2.7.9
```

### Frontend `comites` (`package.json`)
```json
{
  "dependencies": {
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0",
    "@mui/icons-material": "^6.0.0",
    "@mui/material": "^6.0.0",
    "@react-oauth/google": "^0.12.1",
    "@azure/msal-browser": "^3.11.1",
    "@azure/msal-react": "^2.0.16",
    "axios": "^1.7.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.53.0",
    "yup": "^1.4.0"
  }
}
```

### Frontend `dashboard` (`package.json`)
```json
{
  "dependencies": {
    "@react-oauth/google": "^0.11.1",
    "@tanstack/react-query": "^5.60.3",
    "axios": "^1.7.7",
    "leaflet": "^1.9.4",
    "react": "^19.1.1",
    "react-dom": "^19.1.1",
    "react-icons": "^5.2.1",
    "recharts": "^2.12.7"
  }
}
```

---

## PLAN DE SUSCRIPCIÓN Y LÍMITES

### Tabla: `SubscriptionPlan`
```sql
- id (PK)
- name: 'Básico' | 'Intermedio' | 'Premium' | 'Enterprise'
- max_users: Límite de usuarios
- max_committees: Límite de comités
- max_storage_mb: Límite de almacenamiento
- price_monthly: Precio mensual
- features: JSON (características incluidas)
```

### Validación de Límites en Backend
Antes de crear usuarios o comités, verificar:
```python
def check_tenant_limits(tenant_id: int, session: Session):
    tenant = session.get(Tenant, tenant_id)
    
    # Verificar usuarios
    user_count = session.exec(
        select(func.count(User.id)).where(User.tenant_id == tenant_id)
    ).one()
    
    if user_count >= tenant.max_users:
        raise HTTPException(
            status_code=403,
            detail=f"Límite de usuarios alcanzado ({tenant.max_users})"
        )
```

---

## SISTEMA DE REGISTRO Y PAGO CON PAYPAL

### Visión General

El sistema debe permitir que nuevas organizaciones políticas se registren de manera **autónoma** (self-service) y contraten el servicio mediante PayPal. El flujo completo incluye:

1. Registro de nuevo tenant (cliente)
2. Selección de plan de suscripción
3. Pago mediante PayPal
4. Activación automática del tenant
5. Gestión de renovaciones y cancelaciones

---

### 1. FRONTEND DE REGISTRO PÚBLICO

**Landing Page** (`landinpage/` o nueva carpeta `registro/`)

Crear un sitio web público (sin autenticación) en el dominio principal: `micro-servicios.com.mx`

**Páginas requeridas:**

#### 1.1 Página Principal (`/`)
- Hero section con descripción del sistema
- Características principales del producto
- Planes de suscripción con precios
- Testimonios (opcional)
- Call-to-action: "Comenzar Ahora" → redirige a `/registro`

#### 1.2 Página de Planes (`/planes`)
Tabla comparativa con los planes:

| Característica | Básico | Intermedio | Premium | Enterprise |
|----------------|--------|------------|---------|------------|
| **Precio mensual** | $499 MXN | $999 MXN | $1,999 MXN | Contactar |
| Usuarios | 5 | 20 | 50 | Ilimitados |
| Comités | 50 | 200 | 1,000 | Ilimitados |
| Almacenamiento | 1 GB | 5 GB | 20 GB | Ilimitado |
| Soporte | Email | Email + Chat | Prioritario | Dedicado |
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Módulo Asistencia | ✗ | ✓ | ✓ | ✓ |
| Módulo Encuestas | ✗ | ✗ | ✓ | ✓ |
| API Access | ✗ | ✗ | ✓ | ✓ |

Botón por plan: "Seleccionar Plan" → redirige a `/registro?plan=basico`

#### 1.3 Página de Registro (`/registro`)

**Formulario de Registro del Tenant:**

```javascript
// Campos del formulario
{
  // Información de la Organización
  organizationName: string,        // Nombre de la organización
  subdomain: string,               // Subdominio deseado (validar unicidad)
  contactName: string,             // Nombre completo del responsable
  contactEmail: string,            // Email (será el TENANT_ADMIN)
  contactPhone: string,            // Teléfono de contacto
  
  // Plan seleccionado
  selectedPlan: 'basico' | 'intermedio' | 'premium',
  
  // Personalización
  primaryColor: string,            // Color primario (selector de color)
  secondaryColor: string,          // Color secundario
  logo: File,                      // Subida de logotipo (opcional en registro)
  
  // Términos
  acceptTerms: boolean,            // Aceptación de términos y condiciones
  acceptPrivacy: boolean,          // Aceptación de política de privacidad
}
```

**Validaciones:**
- Subdominio: único, solo letras minúsculas y guiones, 3-30 caracteres
- Email: formato válido y único
- Teléfono: formato válido
- Plan: debe existir en catálogo

**Vista previa en tiempo real:**
- Mostrar URL final: `{subdomain}.micro-servicios.com.mx`
- Mostrar preview de colores seleccionados

#### 1.4 Proceso de Registro

**Flujo:**

1. Usuario completa formulario → Click "Continuar al Pago"
2. Frontend valida formulario y disponibilidad de subdominio
3. Frontend envía datos a backend: `POST /api/public/register-tenant`
4. Backend crea tenant con estado `pending_payment`
5. Backend responde con `tenant_id` y `payment_token`
6. Frontend redirige a PayPal con los datos del plan
7. Usuario completa pago en PayPal
8. PayPal redirige de vuelta con confirmación
9. Webhook de PayPal notifica al backend
10. Backend activa el tenant (`is_active = true`)
11. Backend envía email de bienvenida con credenciales de acceso
12. Usuario puede acceder a `{subdomain}.micro-servicios.com.mx`

---

### 2. INTEGRACIÓN CON PAYPAL

**Dependencia Backend:**
```python
# requirements.txt
paypalrestsdk==1.13.1
# O usar requests directamente con PayPal REST API
```

**Configuración** (`.env`)
```bash
# PayPal Configuration
PAYPAL_MODE=sandbox  # 'sandbox' o 'live'
PAYPAL_CLIENT_ID=tu_client_id
PAYPAL_CLIENT_SECRET=tu_client_secret
PAYPAL_WEBHOOK_ID=tu_webhook_id

# URLs de retorno
PAYPAL_RETURN_URL=https://micro-servicios.com.mx/registro/exito
PAYPAL_CANCEL_URL=https://micro-servicios.com.mx/registro/cancelado
```

#### 2.1 Modelos de Datos para Pagos

**Tabla: `Payment`**
```sql
- id (PK)
- tenant_id (FK a Tenant, nullable hasta que se confirme pago)
- paypal_order_id: ID de orden de PayPal
- paypal_payer_id: ID del pagador en PayPal
- paypal_subscription_id: ID de suscripción (para pagos recurrentes)
- amount: DECIMAL (monto pagado)
- currency: VARCHAR (MXN, USD, etc.)
- status: ENUM ('pending', 'completed', 'failed', 'refunded', 'cancelled')
- payment_method: 'paypal'
- plan_id (FK a SubscriptionPlan)
- payment_date: DATETIME
- created_at
- updated_at
```

**Tabla: `PaymentWebhookLog`**
```sql
- id (PK)
- webhook_event_id: ID del evento de PayPal
- event_type: Tipo de evento (PAYMENT.SALE.COMPLETED, etc.)
- payload: JSON (todo el payload del webhook)
- processed: BOOLEAN
- processed_at: DATETIME
- created_at
```

**Actualizar Tabla `Tenant`:**
```sql
-- Agregar campos relacionados con pagos
- paypal_subscription_id: VARCHAR (ID de suscripción activa)
- subscription_status: ENUM ('trial', 'active', 'past_due', 'cancelled', 'suspended')
- trial_ends_at: DATETIME (7 días de prueba gratis)
- next_billing_date: DATETIME
- last_payment_date: DATETIME
```

#### 2.2 Endpoints de PayPal

**Router: `/api/public/` (sin autenticación para registro)**

```python
# app/routers/public.py

@router.post("/register-tenant")
async def register_tenant(data: TenantRegistrationSchema):
    """
    Paso 1: Crear tenant en estado 'pending_payment'
    """
    # Validar que el subdominio no exista
    # Crear registro en Tenant con is_active=False
    # Crear usuario TENANT_ADMIN con estado inactivo
    # Generar token de pago
    # Retornar tenant_id y payment_token

@router.post("/paypal/create-order")
async def create_paypal_order(tenant_id: int, plan_id: int):
    """
    Crear orden de pago en PayPal
    """
    # Obtener detalles del plan
    # Crear orden en PayPal API
    # Guardar en tabla Payment con status='pending'
    # Retornar order_id para que frontend redirija a PayPal

@router.post("/paypal/capture-order")
async def capture_paypal_order(order_id: str):
    """
    Capturar pago después de aprobación del usuario
    """
    # Capturar orden en PayPal API
    # Actualizar Payment status='completed'
    # Activar Tenant (is_active=True)
    # Activar usuario TENANT_ADMIN
    # Enviar email de bienvenida
    # Retornar credenciales de acceso

@router.post("/paypal/webhook")
async def paypal_webhook(request: Request):
    """
    Recibir notificaciones de PayPal (pagos, renovaciones, cancelaciones)
    """
    # Validar firma del webhook
    # Guardar en PaymentWebhookLog
    # Procesar según event_type:
    #   - PAYMENT.SALE.COMPLETED: Renovación exitosa
    #   - BILLING.SUBSCRIPTION.CANCELLED: Cancelación de suscripción
    #   - BILLING.SUBSCRIPTION.SUSPENDED: Suspender tenant
    # Actualizar estado del tenant
```

**Router: `/api/subscription/` (con autenticación para gestión)**

```python
# app/routers/subscription.py

@router.get("/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant_obj)
):
    """
    Obtener estado actual de la suscripción del tenant
    """
    # Retornar plan actual, fecha de vencimiento, estado de pago

@router.post("/upgrade")
async def upgrade_subscription(
    new_plan_id: int,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant_obj)
):
    """
    Cambiar a un plan superior (upgrade)
    """
    # Crear nueva orden de PayPal con diferencia prorrateada
    # Actualizar suscripción

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant_obj)
):
    """
    Cancelar suscripción (al final del período actual)
    """
    # Cancelar en PayPal
    # Marcar tenant para desactivación en la fecha de vencimiento
```

#### 2.3 Flujo de Pago con PayPal (Frontend)

```javascript
// registro/src/pages/Checkout.jsx

const handlePayment = async () => {
  // 1. Crear orden en backend
  const { data } = await axios.post('/api/public/paypal/create-order', {
    tenant_id: registeredTenantId,
    plan_id: selectedPlanId
  });
  
  // 2. Redirigir a PayPal
  window.location.href = data.approval_url;
};

// En página de retorno: /registro/exito
const handlePaymentSuccess = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const orderId = urlParams.get('token');
  
  // 3. Capturar pago
  const { data } = await axios.post('/api/public/paypal/capture-order', {
    order_id: orderId
  });
  
  // 4. Mostrar mensaje de éxito y credenciales
  // Enviar email de confirmación
};
```

#### 2.4 Configuración de Webhooks en PayPal

**Eventos a suscribir:**
- `PAYMENT.SALE.COMPLETED` - Pago completado
- `PAYMENT.SALE.REFUNDED` - Reembolso procesado
- `BILLING.SUBSCRIPTION.CREATED` - Suscripción creada
- `BILLING.SUBSCRIPTION.ACTIVATED` - Suscripción activada
- `BILLING.SUBSCRIPTION.UPDATED` - Suscripción actualizada
- `BILLING.SUBSCRIPTION.CANCELLED` - Suscripción cancelada
- `BILLING.SUBSCRIPTION.SUSPENDED` - Suscripción suspendida
- `BILLING.SUBSCRIPTION.PAYMENT.FAILED` - Fallo en pago de renovación

**URL del Webhook:** `https://api.micro-servicios.com.mx/api/public/paypal/webhook`

---

### 3. PERÍODO DE PRUEBA GRATUITO

**Opción:** Ofrecer 7 días de prueba sin necesidad de pago

**Implementación:**
```python
@router.post("/register-trial")
async def register_trial_tenant(data: TenantRegistrationSchema):
    """
    Crear tenant con período de prueba de 7 días
    """
    # Crear tenant con:
    # - is_active = True
    # - subscription_status = 'trial'
    # - trial_ends_at = now() + 7 days
    # - Límites del plan Básico
    
    # Crear usuario TENANT_ADMIN activo
    # Enviar email de bienvenida con recordatorio de prueba
```

**Tarea programada (Cron Job):**
```python
# Ejecutar diariamente
def check_trial_expirations():
    """
    Verificar tenants con prueba expirada y sin pago
    """
    expired_trials = session.exec(
        select(Tenant).where(
            Tenant.subscription_status == 'trial',
            Tenant.trial_ends_at < datetime.now(),
            Tenant.paypal_subscription_id == None
        )
    ).all()
    
    for tenant in expired_trials:
        # Enviar email de recordatorio de pago
        # Después de 3 días: suspender (is_active = False)
        # Después de 30 días: eliminar datos (opcional)
```

---

### 4. GESTIÓN DE SUSCRIPCIONES (Panel de Tenant Admin)

**Componente Frontend:** `SubscriptionManager.jsx`

**Funcionalidades:**
1. Ver plan actual y características
2. Ver próxima fecha de facturación
3. Historial de pagos
4. Botón "Actualizar Plan" (upgrade/downgrade)
5. Botón "Cancelar Suscripción"
6. Actualizar método de pago en PayPal

**Mockup:**
```
┌─────────────────────────────────────────┐
│ Mi Suscripción                          │
├─────────────────────────────────────────┤
│ Plan Actual: Premium ($1,999 MXN/mes)  │
│ Estado: Activa ✓                        │
│ Próxima facturación: 15 Enero 2026      │
│                                          │
│ [Actualizar Plan] [Cancelar Suscripción]│
│                                          │
│ Historial de Pagos:                     │
│ ┌─────────────────────────────────────┐ │
│ │ 15 Dic 2025   $1,999 MXN   ✓        │ │
│ │ 15 Nov 2025   $1,999 MXN   ✓        │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

### 5. NOTIFICACIONES POR EMAIL

**Eventos que envían email:**

1. **Registro exitoso:**
   - Asunto: "¡Bienvenido a [Nombre del Sistema]!"
   - Contenido: Credenciales de acceso, URL personalizada, primeros pasos

2. **Pago confirmado:**
   - Asunto: "Pago procesado correctamente"
   - Contenido: Recibo, detalles del plan, próxima facturación

3. **Recordatorio de prueba (día 5 de 7):**
   - Asunto: "Quedan 2 días de prueba gratuita"
   - Contenido: Invitación a suscribirse

4. **Renovación próxima (3 días antes):**
   - Asunto: "Tu suscripción se renovará pronto"
   - Contenido: Recordatorio de cargo próximo

5. **Fallo en renovación:**
   - Asunto: "Problema con el pago de tu suscripción"
   - Contenido: Instrucciones para actualizar método de pago

6. **Suscripción cancelada:**
   - Asunto: "Confirmación de cancelación"
   - Contenido: Acceso hasta fecha de vencimiento, proceso de exportación de datos

**Dependencia:**
```python
# requirements.txt
python-jose[cryptography]==3.3.0
sendgrid==6.11.0  # O usar SMTP directo
```

---

## POLÍTICA DE CONFIDENCIALIDAD Y PROTECCIÓN DE DATOS

### Visión General

El sistema debe cumplir con normativas de protección de datos personales:
- **GDPR** (Reglamento General de Protección de Datos - Europa)
- **LGPD** (Lei Geral de Proteção de Dados - Brasil)
- **LFPDPPP** (Ley Federal de Protección de Datos Personales en Posesión de los Particulares - México)

---

### 1. PÁGINA DE POLÍTICA DE PRIVACIDAD

**URL:** `https://micro-servicios.com.mx/privacidad`

**Contenido mínimo requerido:**

```markdown
# Política de Privacidad

Última actualización: [Fecha]

## 1. Responsable del Tratamiento
[Nombre de la empresa]
[Dirección]
[Email de contacto]
[Teléfono]

## 2. Datos Personales que Recopilamos

### 2.1 Datos de Registro
- Nombre completo
- Correo electrónico
- Teléfono celular
- Foto de perfil (opcional)

### 2.2 Datos de Integrantes de Comités
- Nombre completo
- Clave de INE
- Teléfono celular
- Correo electrónico
- Número de sección electoral
- Referente político

### 2.3 Datos Técnicos
- Dirección IP
- Geolocalización (eventos de asistencia)
- Tipo de dispositivo
- Navegador utilizado

## 3. Finalidad del Tratamiento
Los datos personales serán utilizados para:
- Gestión de comités políticos
- Organización de eventos y registro de asistencias
- Análisis estadístico de promoción del voto
- Comunicaciones relacionadas con el servicio

## 4. Base Legal
El tratamiento se basa en:
- Consentimiento expreso del titular
- Ejecución de contrato de prestación de servicios
- Interés legítimo del responsable

## 5. Compartir Información
NO compartimos datos personales con terceros, excepto:
- Proveedores de servicios (hosting, email)
- Autoridades cuando sea legalmente requerido

## 6. Derechos del Titular (ARCO)
Tienes derecho a:
- **Acceder** a tus datos personales
- **Rectificar** datos inexactos
- **Cancelar** tu cuenta y datos
- **Oponerte** al tratamiento de tus datos
- **Portabilidad** de tus datos

Para ejercer estos derechos, contacta: [email]

## 7. Seguridad de los Datos
Implementamos medidas técnicas y organizativas:
- Cifrado de datos en tránsito (HTTPS/TLS)
- Autenticación mediante OAuth2
- Copias de seguridad periódicas
- Acceso restringido a datos

## 8. Retención de Datos
Los datos se conservan mientras:
- La cuenta esté activa
- Sea necesario para cumplir obligaciones legales
- Tras solicitud de eliminación: 30 días para backup

## 9. Cookies
Utilizamos cookies para:
- Mantener sesión activa
- Estadísticas de uso (Google Analytics - opcional)

Puedes desactivar cookies en tu navegador.

## 10. Cambios a esta Política
Notificaremos cambios por email con 15 días de anticipación.

## 11. Contacto
Para dudas sobre privacidad: [email de privacidad]
```

**Implementar en Frontend:**
- Link en footer de todas las páginas
- Checkbox obligatorio en formularios de registro
- Modal emergente con resumen de política

---

### 2. PÁGINA DE TÉRMINOS Y CONDICIONES

**URL:** `https://micro-servicios.com.mx/terminos`

**Contenido:**
- Definición del servicio
- Responsabilidades del cliente (tenant)
- Limitaciones de responsabilidad
- Propiedad intelectual
- Causas de suspensión del servicio
- Jurisdicción y ley aplicable

---

### 3. CONSENTIMIENTOS EN LA BASE DE DATOS

**Tabla: `UserConsent`**
```sql
- id (PK)
- user_id (FK a User)
- tenant_id (FK a Tenant)
- consent_type: ENUM ('privacy_policy', 'terms_of_service', 'data_processing', 'marketing')
- consent_given: BOOLEAN
- consent_text: TEXT (versión del texto aceptado)
- consent_version: VARCHAR (ej: "v1.2")
- ip_address: VARCHAR
- user_agent: TEXT
- consented_at: DATETIME
- revoked_at: DATETIME (nullable)
```

**Registrar consentimientos:**
```python
@router.post("/auth/google")
async def google_auth(token: str, consent_data: ConsentSchema):
    # ... autenticación ...
    
    # Registrar consentimiento
    consent = UserConsent(
        user_id=user.id,
        tenant_id=tenant_id,
        consent_type='privacy_policy',
        consent_given=True,
        consent_text=CURRENT_PRIVACY_POLICY_TEXT,
        consent_version='v1.0',
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent'),
        consented_at=datetime.now()
    )
    session.add(consent)
    session.commit()
```

---

### 4. DERECHOS ARCO (ACCESO, RECTIFICACIÓN, CANCELACIÓN, OPOSICIÓN)

**Endpoint:** `/api/user/arco-request`

```python
@router.post("/arco-request")
async def create_arco_request(
    request_type: str,  # 'access', 'rectify', 'delete', 'oppose'
    details: str,
    current_user: User = Depends(get_current_user)
):
    """
    Procesar solicitud de derechos ARCO
    """
    # Crear ticket/solicitud
    # Notificar a administrador del tenant
    # Plazo de respuesta: 20 días hábiles (según LFPDPPP)
```

**Tabla: `ARCORequest`**
```sql
- id (PK)
- user_id (FK)
- tenant_id (FK)
- request_type: ENUM ('access', 'rectify', 'delete', 'oppose', 'portability')
- status: ENUM ('pending', 'in_progress', 'completed', 'rejected')
- details: TEXT
- response: TEXT (nullable)
- requested_at: DATETIME
- responded_at: DATETIME (nullable)
```

#### 4.1 Implementar Exportación de Datos (Derecho de Acceso)

**Endpoint:** `/api/user/export-my-data`

```python
@router.get("/export-my-data")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant)
):
    """
    Generar archivo JSON con todos los datos del usuario
    """
    data = {
        'user': user_dict,
        'committees': committees_list,
        'assignments': assignments_list,
        'attendance': attendance_list,
        'consents': consents_list
    }
    
    # Generar archivo JSON
    # Retornar como descarga
```

#### 4.2 Implementar Eliminación de Cuenta (Derecho de Cancelación)

**Endpoint:** `/api/user/delete-account`

```python
@router.delete("/delete-account")
async def delete_user_account(
    confirm: bool,
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar cuenta y datos personales (GDPR "Right to be Forgotten")
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="Debe confirmar la eliminación")
    
    # Anonimizar datos en lugar de eliminar (para integridad referencial)
    user.name = f"Usuario Eliminado {user.id}"
    user.email = f"deleted_{user.id}@deleted.local"
    user.phone = None
    user.picture_url = None
    user.is_active = False
    
    # Eliminar asignaciones
    # Registrar en log de auditoría
    # Enviar confirmación por email
```

---

### 5. AVISO DE PRIVACIDAD SIMPLIFICADO

**Componente:** `PrivacyNotice.jsx` (Modal o Banner)

Mostrar en:
- Primer inicio de sesión
- Formularios de registro de integrantes
- Captura de asistencia con geolocalización

**Texto ejemplo:**
```
Al usar este servicio, aceptas que recopilemos y procesemos tus datos personales 
(nombre, email, teléfono) para la gestión de comités políticos.

Puedes consultar nuestra [Política de Privacidad completa aquí].

☐ Acepto el tratamiento de mis datos personales
☐ Acepto recibir comunicaciones relacionadas con el servicio
```

---

### 6. SEGURIDAD Y CIFRADO

Implementar:

1. **HTTPS/TLS obligatorio** en producción
2. **Cifrado de datos sensibles** en base de datos:
   ```python
   from cryptography.fernet import Fernet
   
   # Cifrar clave INE antes de guardar
   ine_encrypted = cipher.encrypt(ine_key.encode())
   ```

3. **Hashing de passwords** (si se implementa auth por contraseña):
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   ```

4. **Logs de auditoría:**
   ```sql
   -- Tabla: AuditLog
   - id (PK)
   - user_id (FK, nullable)
   - tenant_id (FK, nullable)
   - action: VARCHAR (ej: 'login', 'data_access', 'data_modification', 'data_deletion')
   - resource_type: VARCHAR (ej: 'User', 'Committee', 'CommitteeMember')
   - resource_id: INT
   - ip_address
   - user_agent
   - created_at
   ```

---

### 7. CUMPLIMIENTO GDPR/LGPD

**Checklist de cumplimiento:**

- ✅ Política de privacidad clara y accesible
- ✅ Consentimiento explícito y registrado
- ✅ Derechos ARCO implementados
- ✅ Exportación de datos en formato legible
- ✅ Eliminación/anonimización de datos
- ✅ Cifrado de datos en tránsito y reposo
- ✅ Logs de auditoría
- ✅ Designación de responsable de protección de datos (DPO)
- ✅ Evaluación de impacto en protección de datos (DPIA)
- ✅ Notificación de brechas de seguridad (72 horas)

**Documentar:**
- Crear archivo `PRIVACY_COMPLIANCE.md` con:
  - Inventario de datos personales procesados
  - Medidas de seguridad implementadas
  - Procedimientos ante brechas de seguridad
  - Contacto del responsable de privacidad

---

### 8. COMPONENTE FRONTEND: Gestión de Privacidad

**Página:** `/mi-cuenta/privacidad`

**Opciones para el Usuario:**

1. **Ver mis datos**
   - Botón: "Descargar mis datos" → Genera JSON con toda la información

2. **Gestionar consentimientos**
   - Tabla con checkboxes:
     * ☑ Uso de datos para gestión de comités (obligatorio)
     * ☐ Comunicaciones de marketing
     * ☐ Análisis de uso para mejoras del servicio

3. **Eliminar mi cuenta**
   - Botón: "Eliminar mi cuenta permanentemente"
   - Modal de confirmación con advertencias
   - Requiere escribir "ELIMINAR" para confirmar

4. **Historial de accesos**
   - Tabla con últimos inicios de sesión (IP, dispositivo, fecha)

5. **Solicitudes ARCO**
   - Formulario para nueva solicitud
   - Estado de solicitudes anteriores

---

## SEGURIDAD

### 1. Aislamiento de Datos
- **TODAS** las consultas DEBEN incluir filtro por `tenant_id`
- Usar dependencias de FastAPI para inyectar `tenant_id` automáticamente
- Validar que `tenant_id` del token JWT coincide con el del recurso solicitado

### 2. Autenticación Robusta
- OAuth2 con Google y Microsoft
- Tokens JWT con expiración
- Refresh tokens (opcional pero recomendado)

### 3. Autorización por Roles
- Verificar roles antes de permitir operaciones sensibles
- Jerarquía de permisos clara

### 4. Protección de Archivos
- Uploads organizados por `tenant_id`
- Verificar pertenencia antes de servir archivos
- No exponer rutas absolutas en URLs

### 5. Rate Limiting
- Implementar límites de requests por tenant
- Prevenir abuso de API

### 6. Validación de Entrada
- Usar Pydantic schemas para validar todos los inputs
- Sanitizar datos antes de almacenar

---

## DEPLOYMENT

### Backend
```bash
# En servidor Debian 12
cd /var/www/backend
source venv/bin/activate
pip install -r requirements.txt

# Configurar systemd service
sudo nano /etc/systemd/system/api-comites.service

# Iniciar servicio
sudo systemctl start api-comites
sudo systemctl enable api-comites
```

### Frontends con Nginx
```nginx
# Configuración para múltiples subdominios
server {
    listen 80;
    server_name *.tudominio.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location / {
        root /var/www/comites/dist;
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 80;
    server_name dashboard.tudominio.com;

    location / {
        root /var/www/dashboard/dist;
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 80;
    server_name asistencia.tudominio.com;

    location / {
        root /var/www/asistencia/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## DIAGRAMAS CLAVE

### Flujo de Login Multi-Tenant
```
1. Usuario accede a subdominio: accion.tudominio.com
2. Frontend detecta tenant por subdominio
3. Frontend carga configuración visual del tenant (logo, colores)
4. Usuario hace login con Google/Microsoft
5. Token enviado a backend con tenant_id en header
6. Backend valida token + tenant
7. Backend genera JWT con user_id + tenant_id
8. Frontend almacena JWT y tenant_id
9. Todas las requests incluyen tenant_id
```

### Estructura de Datos Jerárquica
```
Tenant (Cliente Político)
  └── AdministrativeUnit (STATE)
        └── AdministrativeUnit (REGION)
              └── AdministrativeUnit (DISTRICT)
                    └── AdministrativeUnit (MUNICIPALITY)
                          └── AdministrativeUnit (SECTION)
                                └── Committee
                                      └── CommitteeMember
```

---

## DOCUMENTACIÓN ADICIONAL REQUERIDA

Al completar el sistema, generar:

1. **README.md principal** con:
   - Descripción del sistema
   - Requisitos de instalación
   - Pasos de configuración
   - Comandos de deployment

2. **API_DOCUMENTATION.md** con:
   - Todos los endpoints documentados
   - Ejemplos de requests/responses
   - Códigos de error

3. **ADMIN_GUIDE.md** con:
   - Guía para SUPER_ADMIN
   - Guía para TENANT_ADMIN
   - Procesos de onboarding de nuevos clientes

4. **USER_GUIDE.md** con:
   - Manual de uso para coordinadores
   - Manual de uso para capturistas
   - FAQ

---

## PRIORIDADES DE DESARROLLO

### Fase 1: Core Multi-Tenant
1. Configurar base de datos con tenant_id en todas las tablas
2. Implementar middleware de tenant
3. Crear sistema de autenticación OAuth
4. Panel de super admin para crear tenants

### Fase 2: Módulo de Comités
1. CRUD de comités con aislamiento por tenant
2. Registro de integrantes
3. Subida de documentos
4. Estructura jerárquica de unidades

### Fase 3: Módulo de Asistencia
1. Frontend de asistencia
2. Captura de geolocalización
3. Gestión de eventos

### Fase 4: Módulo de Encuestas
1. Creador de encuestas
2. Frontend público para responder
3. Análisis de resultados

### Fase 5: Dashboard y Reportes
1. Vistas de árbol jerárquico
2. Gráficas con Recharts
3. Mapas con Leaflet
4. Exportación de datos (Excel, PDF)

### Fase 6: Optimización y Deployment
1. Testing exhaustivo de aislamiento
2. Optimización de queries
3. Configuración de producción
4. Documentación completa

---

## CRITERIOS DE ÉXITO

El sistema estará completo cuando:

✅ **Multi-Tenancy:**
- Múltiples clientes pueden usar el sistema simultáneamente sin ver datos de otros
- Cada cliente tiene su logotipo y colores personalizados
- Los límites de suscripción se aplican correctamente

✅ **Funcionalidad:**
- Los 4 módulos (Comités, Asistencia, Encuestas, Dashboard) funcionan completamente
- La jerarquía de unidades administrativas es navegable y funcional
- Los reportes y estadísticas son precisos

✅ **Seguridad:**
- No hay fugas de datos entre tenants
- La autenticación OAuth funciona correctamente
- Los roles y permisos se respetan

✅ **UX:**
- La interfaz es intuitiva en móviles
- Los formularios tienen validación clara
- La navegación es fluida

✅ **Documentación:**
- Existe documentación completa para administradores y usuarios
- El código está comentado y es mantenible

---

## NOTAS FINALES

- **Prioriza el aislamiento de datos**: Es CRÍTICO que los datos de un tenant NUNCA sean accesibles por otro
- **Optimiza para móvil**: La mayoría de usuarios estarán en dispositivos móviles
- **Diseño escalable**: El sistema debe soportar crecimiento en número de tenants y usuarios
- **Monitoreo**: Implementar logs y métricas para detectar problemas tempranamente
- **Backup**: Estrategia de respaldo de datos por tenant

---

**IMPORTANTE:** Este prompt debe servir como especificación completa. El agente de IA debe seguir estas instrucciones al pie de la letra, implementando cada componente con la arquitectura multi-tenant desde el inicio. NO crear primero un sistema single-tenant y luego migrar; debe ser multi-tenant desde la primera línea de código.
