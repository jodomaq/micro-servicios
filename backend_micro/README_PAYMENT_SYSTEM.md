# Sistema de Pagos y Suscripciones - Excel Converter

## Descripción General

Este sistema implementa pagos únicos y suscripciones mensuales para el conversor de PDFs a Excel, con autenticación Google OAuth 2.0 y gestión de usuarios.

## Características Principales

### 1. Autenticación con Google
- Login con Google OAuth 2.0
- Gestión de sesiones con JWT
- Almacenamiento local de tokens

### 2. Sistema de Pagos

#### Pago Único
- **Precio**: $20 MXN por conversión
- **Método**: PayPal
- **Beneficio**: Conversión única sin compromiso

#### Suscripciones Mensuales

| Plan | Conversiones | Precio | Precio por conversión |
|------|-------------|--------|----------------------|
| Básico | 200 | $200 MXN | ~$1.00 MXN |
| Estándar | 400 | $300 MXN | ~$0.75 MXN |
| Premium | 600 | $350 MXN | ~$0.58 MXN |

### 3. Gestión de Suscripciones
- Contador de conversiones usadas
- Renovación automática mensual
- Cancelación en cualquier momento
- Dashboard de usuario con estadísticas

## Estructura del Backend

### Modelos de Base de Datos

#### User
- Información del usuario de Google
- Relaciones con suscripciones, pagos y conversiones

#### Subscription
- Plan activo del usuario
- Límite y uso de conversiones
- Fechas de inicio y fin
- ID de suscripción de PayPal

#### Payment
- Registro de todos los pagos
- Tipo: one_time o subscription
- Estado y detalles de PayPal

#### Conversion
- Historial de conversiones
- Vinculación con usuario y pago
- Estado de éxito/fallo

### Endpoints Principales

#### Autenticación (`/auth`)
- `POST /auth/google` - Login con Google
- `GET /auth/me` - Información del usuario actual
- `POST /auth/logout` - Cerrar sesión

#### Conversión (`/converter`)
- `POST /converter/upload` - Subir PDF
- `POST /converter/paypal/create-order` - Crear orden de pago único
- `POST /converter/paypal/capture-and-convert` - Capturar pago y convertir
- `POST /converter/convert` - Convertir con suscripción
- `POST /converter/subscription/create` - Crear suscripción
- `POST /converter/subscription/approve` - Aprobar suscripción

#### Suscripciones (`/subscriptions`)
- `GET /subscriptions/plans` - Listar planes disponibles
- `GET /subscriptions/my-subscription` - Suscripción actual
- `GET /subscriptions/dashboard` - Dashboard completo del usuario
- `DELETE /subscriptions/{id}` - Cancelar suscripción

## Estructura del Frontend

### Componentes

#### `AuthContext`
Provider de contexto para autenticación global

#### `GoogleLogin`
Botón de login con Google OAuth

#### `Dashboard`
Panel de control del usuario con:
- Información del perfil
- Estado de suscripción
- Conversiones restantes
- Historial de conversiones

#### `SubscriptionPlans`
Visualización de planes con opción de suscripción

#### `Pay`
Flujo de pago con opciones:
- Pago único con PayPal
- Conversión con suscripción activa
- Selector de planes

### Flujo de Usuario

1. **Usuario Anónimo**
   - Subir PDF
   - Pagar $20 MXN con PayPal
   - Descargar Excel

2. **Usuario Registrado sin Suscripción**
   - Login con Google
   - Subir PDF
   - Elegir entre:
     - Pago único ($20 MXN)
     - Suscribirse a un plan

3. **Usuario con Suscripción Activa**
   - Login automático
   - Ver conversiones restantes
   - Subir PDF
   - Convertir automáticamente (sin pago)
   - Contador se actualiza

## Configuración

### Variables de Entorno - Backend

```env
# PayPal
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_CURRENCY=MXN
PAYPAL_AMOUNT=20.00
PAYPAL_ENV=sandbox  # o 'live' para producción

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# JWT
JWT_SECRET=your-super-secret-jwt-key

# Database
DATABASE_URL=sqlite:///./excel_converter.db
```

### Variables de Entorno - Frontend

```env
VITE_API_BASE=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

## Instalación y Ejecución

### Backend

```bash
cd backend_micro

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd ExcelConverter

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar servidor de desarrollo
npm run dev
```

## Configuración de Google OAuth

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un nuevo proyecto o seleccionar uno existente
3. Activar "Google+ API"
4. Ir a "Credenciales" → "Crear credenciales" → "ID de cliente de OAuth"
5. Tipo: Aplicación web
6. Orígenes autorizados:
   - `http://localhost:5173`
   - Tu dominio de producción
7. Copiar el Client ID a tus archivos `.env`

## Configuración de PayPal

1. Ir a [PayPal Developer](https://developer.paypal.com/)
2. Crear una aplicación en "My Apps & Credentials"
3. Obtener Client ID y Secret (Sandbox para pruebas)
4. Para producción, usar credenciales Live
5. Configurar webhooks (opcional) para renovaciones automáticas

## Base de Datos

La base de datos se crea automáticamente al iniciar el servidor por primera vez usando SQLite. Para usar PostgreSQL o MySQL en producción, cambiar `DATABASE_URL` en `.env`.

## Seguridad

- ✅ Autenticación OAuth 2.0 con Google
- ✅ Tokens JWT con expiración
- ✅ Validación de pagos con PayPal
- ✅ CORS configurado
- ✅ Variables sensibles en .env
- ✅ Registro de conversiones por usuario

## Próximos Pasos

1. Configurar webhooks de PayPal para renovaciones automáticas
2. Implementar sistema de notificaciones por email
3. Añadir panel de administración
4. Implementar analytics de uso
5. Agregar más métodos de pago (Stripe, etc.)

## Soporte

Para problemas o preguntas:
- Revisar logs del backend: `uvicorn` muestra logs en consola
- Revisar consola del navegador para errores del frontend
- Verificar que las credenciales estén correctamente configuradas
