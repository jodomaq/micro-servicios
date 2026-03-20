# Guía de Prueba del Sistema

## Backend API - Pruebas Iniciales

### 1. Iniciar el Backend

```powershell
# Desde d:\DEV\EstructuraPolitica\backend

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias (primera vez)
pip install -r requirements.txt

# Configurar .env
# Copiar .env.example a .env y editar con tus credenciales
copy .env.example .env
notepad .env

# Inicializar base de datos (primera vez)
python scripts\create_database.py

# Iniciar servidor
uvicorn app.main:app --reload
```

El servidor estará en: **http://localhost:8000**

### 2. Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Pruebas con datos demo

El script `create_database.py` crea:
- Tenant: subdomain="demo"
- Usuario admin: email="admin@demo.com"
- Super admin: email="superadmin@micro-servicios.com.mx"

### 4. Headers Requeridos

Para todas las requests (excepto públicas):

```http
X-Tenant-ID: 1
Authorization: Bearer {jwt_token}
```

En desarrollo, si usas localhost, el middleware acepta `X-Tenant-ID` en el header.

---

## Endpoints Implementados

### Autenticación (`/api/auth`)

#### Login con Google
```http
POST /api/auth/google
Content-Type: application/json
X-Tenant-ID: 1

{
  "token": "google_id_token_here",
  "consent_privacy_policy": true,
  "consent_terms": true
}
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "name": "Usuario Demo",
    ...
  },
  "tenant": {
    "id": 1,
    "name": "Organización Demo",
    ...
  }
}
```

#### Login con Microsoft
```http
POST /api/auth/microsoft
Content-Type: application/json
X-Tenant-ID: 1

{
  "access_token": "microsoft_access_token_here",
  "consent_privacy_policy": true,
  "consent_terms": true
}
```

#### Obtener usuario actual
```http
GET /api/auth/me
Authorization: Bearer {token}
X-Tenant-ID: 1
```

---

### Tipos de Comité (`/api/committee-types`)

#### Listar tipos
```http
GET /api/committee-types
Authorization: Bearer {token}
X-Tenant-ID: 1
```

#### Crear tipo
```http
POST /api/committee-types
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "name": "Comité de Maestros",
  "description": "Comité de educadores"
}
```

---

### Unidades Administrativas (`/api/administrative-units`)

#### Obtener árbol completo
```http
GET /api/administrative-units/tree
Authorization: Bearer {token}
X-Tenant-ID: 1
```

#### Crear unidad (ejemplo: Estado)
```http
POST /api/administrative-units
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "name": "Michoacán",
  "code": "MIC",
  "unit_type": "STATE",
  "parent_id": null
}
```

#### Crear sub-unidad (ejemplo: Región)
```http
POST /api/administrative-units
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "name": "Región 1 - Morelia",
  "code": "R1",
  "unit_type": "REGION",
  "parent_id": 1
}
```

#### Asignar coordinador a unidad
```http
POST /api/administrative-units/1/assignments
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "user_id": 2,
  "administrative_unit_id": 1,
  "role": 1
}
```

**Roles disponibles:**
- 1 = COORDINADOR_ESTATAL
- 2 = DELEGADO_REGIONAL
- 3 = COORDINADOR_DISTRITAL
- 4 = COORDINADOR_MUNICIPAL
- 5 = COORDINADOR_SECCIONAL
- 6 = PRESIDENTE_COMITE
- 7 = CAPTURISTA

---

### Comités (`/api/committees`)

#### Listar comités
```http
GET /api/committees?skip=0&limit=10
Authorization: Bearer {token}
X-Tenant-ID: 1
```

**Filtros opcionales:**
- `committee_type_id`: Filtrar por tipo
- `administrative_unit_id`: Filtrar por unidad administrativa
- `search`: Búsqueda en nombre y presidente

#### Crear comité
```http
POST /api/committees
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "name": "Comité Sección 001",
  "section_number": "001",
  "committee_type_id": 1,
  "administrative_unit_id": 5,
  "president_name": "Juan Pérez",
  "president_email": "juan@example.com",
  "president_phone": "+52 443 123 4567",
  "president_affiliation_key": "ABC123"
}
```

#### Agregar integrante (máximo 10)
```http
POST /api/committees/1/members
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "full_name": "María González",
  "ine_key": "GOMR850315MMCNZR09",
  "phone": "+52 443 987 6543",
  "email": "maria@gmail.com",
  "section_number": "001",
  "referred_by": "Pedro Martínez"
}
```

#### Subir documento
```http
POST /api/committees/1/documents
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: multipart/form-data

file: [seleccionar archivo imagen o PDF]
```

---

### Usuarios (`/api/users`)

#### Listar usuarios
```http
GET /api/users
Authorization: Bearer {token}
X-Tenant-ID: 1
```

**Filtros:**
- `search`: Búsqueda en nombre/email
- `role`: Filtrar por rol (1-7)
- `is_active`: true/false

#### Crear usuario manualmente
```http
POST /api/users
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "email": "coordinador@example.com",
  "name": "Nuevo Coordinador",
  "phone": "+52 443 111 2222",
  "is_tenant_admin": false
}
```

#### Obtener estadísticas de usuario
```http
GET /api/users/2/stats
Authorization: Bearer {token}
X-Tenant-ID: 1
```

**Respuesta:**
```json
{
  "user_id": 2,
  "user_name": "Coordinador Regional",
  "user_email": "coordinador@example.com",
  "assignments_count": 2,
  "committees_created": 5,
  "committees_in_hierarchy": 25,
  "members_in_hierarchy": 180,
  "assignments": [
    {
      "unit_id": 2,
      "unit_name": "Región 1 - Morelia",
      "role": 2
    }
  ]
}
```

#### Asignar rol a usuario
```http
POST /api/users/2/assignments
Authorization: Bearer {token}
X-Tenant-ID: 1
Content-Type: application/json

{
  "user_id": 2,
  "administrative_unit_id": 3,
  "role": 3
}
```

---

## Flujo Completo de Prueba

### 1. Setup Inicial

```powershell
# Inicializar base de datos
python scripts\create_database.py

# Iniciar servidor
uvicorn app.main:app --reload
```

### 2. Crear Estructura Jerárquica

1. Crear Estado (unit_type: "STATE")
2. Crear Regiones (unit_type: "REGION", parent_id: estado_id)
3. Crear Distritos (unit_type: "DISTRICT", parent_id: region_id)
4. Crear Municipios (unit_type: "MUNICIPALITY", parent_id: distrito_id)
5. Crear Secciones (unit_type: "SECTION", parent_id: municipio_id)

### 3. Crear Tipos de Comité

1. Comité General
2. Comité de Maestros
3. Comité de Transportistas
4. Etc.

### 4. Asignar Coordinadores

1. Crear usuarios (o login con OAuth)
2. Asignar a unidades administrativas con roles
3. Verificar estadísticas con `/users/{id}/stats`

### 5. Crear Comités

1. Crear comité en una sección
2. Agregar hasta 10 integrantes
3. Subir documentos/actas
4. Listar y filtrar comités

### 6. Verificar Árbol

```http
GET /api/administrative-units/tree
```

Esto debe retornar toda la jerarquía con contadores recursivos de comités y miembros.

---

## Errores Comunes

### 403: Tenant no identificado
- Asegúrate de incluir header `X-Tenant-ID: 1`
- En producción, usar subdomain correcto

### 401: No autenticado
- Token JWT expirado o inválido
- Hacer login nuevamente para obtener nuevo token

### 400: Límite alcanzado
- Has excedido el límite de usuarios o comités del plan
- Actualizar plan de suscripción o eliminar registros

### 404: No encontrado
- Verificar que el recurso pertenezca al tenant correcto
- IDs correctos en URLs

---

## Testing Avanzado

### Con Postman

1. Importar colección (crear archivo de colección con estos endpoints)
2. Configurar variables de entorno:
   - `base_url`: http://localhost:8000
   - `tenant_id`: 1
   - `token`: JWT del login

### Con curl

```powershell
# Login (simulado - en producción usar OAuth real)
# Para testing, crear usuario directamente en DB y generar JWT manualmente

# Listar comités
curl -X GET "http://localhost:8000/api/committees" `
  -H "Authorization: Bearer TOKEN" `
  -H "X-Tenant-ID: 1"

# Crear comité
curl -X POST "http://localhost:8000/api/committees" `
  -H "Authorization: Bearer TOKEN" `
  -H "X-Tenant-ID: 1" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Comité Test",
    "section_number": "001",
    "committee_type_id": 1,
    "administrative_unit_id": 1,
    "president_name": "Test User"
  }'
```

---

## Próximos Pasos

Una vez verificado que el backend funciona:

1. **Frontend "comites"**: Interfaz React + MUI
2. **AdminDashboard**: Gestión visual de coordinadores
3. **Módulos adicionales**: Eventos, Asistencia, Encuestas
4. **Integración PayPal**: Sistema de pagos completo
5. **Testing automatizado**: Pytest + coverage
6. **Deployment**: Configuración en servidor de producción

---

## Soporte

Si encuentras errores:
1. Verificar logs del servidor (terminal donde corre uvicorn)
2. Revisar respuesta JSON del error
3. Verificar configuración en `.env`
4. Asegurar que la base de datos esté corriendo
