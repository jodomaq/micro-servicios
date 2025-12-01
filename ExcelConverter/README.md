# Excel Converter - Sistema Completo de Pagos y Suscripciones

Frontend en Vite + React y backend en FastAPI con sistema completo de:
- ✅ Autenticación con Google OAuth 2.0
- ✅ Pagos únicos con PayPal ($20 MXN)
- ✅ Suscripciones mensuales (200/400/600 conversiones)
- ✅ Dashboard de usuario
- ✅ Gestión de suscripciones

## Características

### Sistema de Pagos

#### Pago Único
- **Precio**: $20 MXN por conversión
- **Método**: PayPal
- **Sin registro requerido**

#### Suscripciones Mensuales

| Plan | Conversiones | Precio | Por conversión |
|------|-------------|--------|----------------|
| Básico | 200 | $200 MXN | ~$1.00 MXN |
| Estándar | 400 | $300 MXN | ~$0.75 MXN |
| Premium | 600 | $350 MXN | ~$0.58 MXN |

## Endpoints Backend

### Autenticación
- `POST /auth/google` - Login con Google
- `GET /auth/me` - Usuario actual
- `POST /auth/logout` - Cerrar sesión

### Conversión y Pagos
- `POST /converter/upload` - Subir PDF → `{ upload_id }`
- `POST /converter/paypal/create-order` - Crear orden PayPal ($20 MXN)
- `POST /converter/paypal/capture-and-convert` - Capturar pago y convertir
- `POST /converter/convert` - Convertir con suscripción activa
- `POST /converter/subscription/create` - Crear suscripción PayPal
- `POST /converter/subscription/approve` - Aprobar suscripción

### Suscripciones
- `GET /subscriptions/plans` - Listar planes
- `GET /subscriptions/my-subscription` - Suscripción actual
- `GET /subscriptions/dashboard` - Dashboard completo
- `DELETE /subscriptions/{id}` - Cancelar suscripción

## Variables de Entorno

### Backend (.env)

```env
# PayPal
PAYPAL_CLIENT_ID=tu-paypal-client-id
PAYPAL_CLIENT_SECRET=tu-paypal-secret
PAYPAL_ENV=sandbox  # o 'live' para producción
PAYPAL_CURRENCY=MXN
PAYPAL_AMOUNT=20.00

# Google OAuth
GOOGLE_CLIENT_ID=tu-google-client-id.apps.googleusercontent.com

# JWT
JWT_SECRET=tu-jwt-secret-key

# Database
DATABASE_URL=sqlite:///./excel_converter.db

# OpenAI (para conversión)
OPENAI_API_KEY=tu-openai-key
```

### Frontend (.env)

```env
VITE_API_BASE=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=tu-google-client-id.apps.googleusercontent.com
```

## Instalación y Ejecución

### Backend

```bash
cd backend_micro

# Instalar dependencias
pip install -r requirements.txt

# Copiar y configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# Inicializar base de datos
python init_db.py

# Iniciar servidor
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd ExcelConverter

# Instalar dependencias
npm install

# Copiar y configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor de desarrollo
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`

## Configuración de Servicios Externos

### Google OAuth 2.0

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto o seleccionar existente
3. Habilitar "Google+ API"
4. Crear credenciales OAuth 2.0
5. Configurar orígenes autorizados:
   - `http://localhost:5173`
   - Tu dominio de producción
6. Copiar Client ID a ambos archivos `.env`

### PayPal

1. Ir a [PayPal Developer](https://developer.paypal.com/)
2. Crear aplicación en "My Apps & Credentials"
3. Obtener Client ID y Secret (Sandbox para pruebas)
4. Configurar en backend `.env`
5. Para producción, cambiar a credenciales Live

## Estructura del Proyecto

### Backend (`backend_micro/`)

```
app/
├── models.py              # Modelos de BD (User, Subscription, Payment, Conversion)
├── schemas.py             # Schemas Pydantic
├── database.py            # Configuración de BD
├── auth.py                # Autenticación Google OAuth + JWT
├── subscription_manager.py # Lógica de suscripciones
├── routes.py              # Endpoints de conversión
├── auth_routes.py         # Endpoints de autenticación
├── subscription_routes.py # Endpoints de suscripciones
└── paypal_client.py       # Cliente PayPal (órdenes y suscripciones)
```

### Frontend (`ExcelConverter/src/`)

```
components/
├── Dashboard.jsx          # Panel de usuario
├── GoogleLogin.jsx        # Login con Google
└── SubscriptionPlans.jsx  # Planes de suscripción
context/
└── AuthContext.jsx        # Contexto de autenticación
pages/
├── App.jsx                # App principal
├── Upload.jsx             # Carga de archivos
├── Pay.jsx                # Sistema de pagos
└── PayPalReturn.jsx       # Retorno de PayPal
```

## Flujos de Usuario

### 1. Usuario Anónimo (Sin Login)
- Subir PDF
- Pagar $20 MXN con PayPal
- Descargar Excel

### 2. Usuario con Login (Sin Suscripción)
- Login con Google
- Ver dashboard
- Elegir: pago único o suscripción
- Si suscripción: elegir plan → PayPal → activación

### 3. Usuario con Suscripción Activa
- Login automático
- Ver conversiones restantes en dashboard
- Subir PDF
- Conversión automática (sin pago)
- Contador actualizado

## Base de Datos

### Modelos

- **User**: Usuarios autenticados con Google
- **Subscription**: Suscripciones activas con límites
- **Payment**: Historial de pagos (únicos y suscripciones)
- **Conversion**: Registro de todas las conversiones

Se crea automáticamente con SQLite. Para producción, cambiar a PostgreSQL/MySQL modificando `DATABASE_URL`.

## Documentación Adicional

- `README_PAYMENT_SYSTEM.md` - Documentación completa del sistema
- `.env.example` - Plantilla de variables de entorno
- Consultar logs del backend para debugging

## Seguridad

- ✅ OAuth 2.0 con Google
- ✅ JWT con expiración de 30 días
- ✅ Validación de pagos con PayPal
- ✅ CORS configurado
- ✅ Variables sensibles en .env (no commiteadas)

## Deployment

### Backend
- Uvicorn + Gunicorn en producción
- Variables de entorno en plataforma
- Base de datos PostgreSQL recomendada

### Frontend
- Build: `npm run build`
- Desplegar carpeta `dist/`
- Plataformas sugeridas: Vercel, Netlify, AWS S3

## Soporte

Para problemas:
1. Revisar logs del backend
2. Consola del navegador
3. Verificar credenciales en `.env`
4. Estado de servicios externos (Google, PayPal)

## Licencia

Propietario

