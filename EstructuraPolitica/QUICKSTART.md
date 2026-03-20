# Guía de Inicio Rápido

## ⚡ Configuración Inicial (5 minutos)

### 1. Configurar Base de Datos

Edita `backend\.env`:

```env
# Base de datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=estructura_politica

# JWT (genera una clave segura)
SECRET_KEY=cambiar_por_clave_segura_de_32_caracteres_minimo

# OAuth (usar tus credenciales reales o dejar vacío para testing)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Resto puedes dejarlo como está para desarrollo local
```

### 2. Instalar y Ejecutar

```powershell
# Navegar al backend
cd d:\DEV\EstructuraPolitica\backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos (crea tablas y datos demo)
python scripts\create_database.py

# Iniciar servidor
uvicorn app.main:app --reload
```

### 3. Verificar Instalación

Abre en tu navegador:
- **Docs interactivos**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

Deberías ver:
```json
{"status": "healthy"}
```

---

## 🧪 Primeras Pruebas

### Usando Swagger UI (http://localhost:8000/docs)

1. **Listar Tipos de Comité**
   - Endpoint: `GET /api/committee-types`
   - Click "Try it out"
   - Headers: `X-Tenant-ID: 1`
   - Click "Execute"

2. **Crear Unidad Administrativa (Estado)**
   - Endpoint: `POST /api/administrative-units`
   - Headers: `X-Tenant-ID: 1`
   - Body:
   ```json
   {
     "name": "Michoacán",
     "code": "MIC",
     "unit_type": "STATE",
     "parent_id": null
   }
   ```

3. **Ver Árbol Jerárquico**
   - Endpoint: `GET /api/administrative-units/tree`
   - Headers: `X-Tenant-ID: 1`

---

## 📊 Datos Demo Creados

El script `create_database.py` creó:

### Tenant Demo
- **Subdomain**: demo
- **ID**: 1
- **Plan**: Básico (7 días de prueba)

### Usuarios
- **Admin Demo**: admin@demo.com (is_tenant_admin=true)
- **Super Admin**: superadmin@micro-servicios.com.mx (is_super_admin=true)

### Planes de Suscripción
1. Básico - $499 MXN/mes
2. Intermedio - $999 MXN/mes
3. Premium - $1,999 MXN/mes
4. Enterprise - Contactar

---

## 🔑 Notas Importantes

### Headers Requeridos

Todos los endpoints requieren:
```http
X-Tenant-ID: 1
```

Endpoints protegidos también requieren:
```http
Authorization: Bearer {jwt_token}
```

### Obtener JWT Token

**Opción 1**: Login con OAuth (requiere configurar credenciales)
```http
POST /api/auth/google
{
  "token": "google_id_token",
  "consent_privacy_policy": true,
  "consent_terms": true
}
```

**Opción 2**: Para testing rápido sin OAuth
- Crear usuario directamente en la base de datos
- Usar el ID del usuario para generar un JWT manualmente
- O temporalmente hacer endpoints sin autenticación para testing

### Multi-Tenancy

- En desarrollo (localhost), usa header `X-Tenant-ID`
- En producción, se detecta por subdomain automáticamente
  - Ejemplo: `demo.micro-servicios.com.mx` → tenant_id=1

---

## 🎯 Flujo de Trabajo Recomendado

### Setup de Estructura (Hazlo en orden):

1. **Crear Tipos de Comité**
   ```json
   POST /api/committee-types
   {"name": "Comité General"}
   {"name": "Comité de Maestros"}
   {"name": "Comité de Transportistas"}
   ```

2. **Crear Jerarquía Administrativa**
   ```
   Estado → Regiones → Distritos → Municipios → Secciones
   ```

3. **Crear Usuarios/Coordinadores**
   ```json
   POST /api/users
   {
     "email": "coordinador@example.com",
     "name": "Juan Coordinador",
     "phone": "+52 443 123 4567"
   }
   ```

4. **Asignar Coordinadores a Jerarquía**
   ```json
   POST /api/users/{user_id}/assignments
   {
     "user_id": 2,
     "administrative_unit_id": 1,
     "role": 1
   }
   ```

5. **Crear Comités**
   ```json
   POST /api/committees
   {
     "name": "Comité Sección 001",
     "committee_type_id": 1,
     "administrative_unit_id": 5,
     "president_name": "María Presidente"
   }
   ```

6. **Agregar Integrantes**
   ```json
   POST /api/committees/{id}/members
   {
     "full_name": "Pedro García",
     "ine_key": "GAPR850315HMCRRD02",
     "phone": "+52 443 987 6543"
   }
   ```

---

## 🐛 Troubleshooting

### Error: "Tenant no identificado"
✅ Agregar header `X-Tenant-ID: 1`

### Error: "No autenticado"
✅ Temporalmente comentar la dependencia `get_current_user` en los routers para testing
✅ O configurar OAuth y hacer login

### Error: Conexión a base de datos
✅ Verificar que MariaDB/MySQL esté corriendo
✅ Verificar credenciales en `.env`
✅ Crear base de datos manualmente: `CREATE DATABASE estructura_politica;`

### Error: Módulo no encontrado
✅ Asegurarte de estar en el entorno virtual activado
✅ Reinstalar: `pip install -r requirements.txt`

---

## 📚 Documentación Adicional

- **README.md** - Documentación completa
- **TESTING_GUIDE.md** - Ejemplos de todas las APIs
- **PROGRESS_SUMMARY.md** - Estado del proyecto

---

## ✨ Siguientes Pasos

Una vez que hayas probado el backend:

1. **Frontend React** - Interfaz de usuario
2. **AdminDashboard** - Gestión visual de coordinadores
3. **Más módulos** - Eventos, Asistencia, Encuestas
4. **PayPal** - Sistema de pagos
5. **Testing** - Automatizado con Pytest
6. **Deployment** - Servidor de producción

---

¡Listo para empezar! 🚀
