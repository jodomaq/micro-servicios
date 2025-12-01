# Micro Servicios - Excel Converter con Sistema de Pagos

Sistema completo de conversión de PDFs (estados de cuenta) a Excel con:
- ✅ **Autenticación Google OAuth 2.0**
- ✅ **Pagos únicos con PayPal** ($20 MXN)
- ✅ **Suscripciones mensuales** (200/400/600 conversiones)
- ✅ **Dashboard de usuario**
- ✅ **Gestión completa de suscripciones**

## 🚀 Inicio Rápido

### Opción 1: Script Automático (Recomendado)

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Opción 2: Manual

#### Backend
```bash
cd backend_micro
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales
python init_db.py
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
cd ExcelConverter
npm install
cp .env.example .env
# Editar .env con credenciales
npm run dev
```

Abrir: http://localhost:5173

## 📋 Planes y Precios

### Pago Único
- **$20 MXN** por conversión
- Sin registro requerido
- Pago con PayPal

### Suscripciones Mensuales

| Plan | Conversiones | Precio | Por conversión |
|------|-------------|--------|----------------|
| 💼 Básico | 200 | $200 MXN | $1.00 |
| ⭐ Estándar | 400 | $300 MXN | $0.75 |
| 🏆 Premium | 600 | $350 MXN | $0.58 |

## 🔧 Configuración de Servicios

### 1. Google OAuth 2.0

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto nuevo
3. Habilitar "Google+ API"
4. Crear credenciales OAuth 2.0:
   - Tipo: Aplicación web
   - Orígenes autorizados:
     - `http://localhost:5173`
     - Tu dominio de producción
5. Copiar **Client ID** a:
   - `backend_micro/.env` → `GOOGLE_CLIENT_ID`
   - `ExcelConverter/.env` → `VITE_GOOGLE_CLIENT_ID`

### 2. PayPal

1. Ir a [PayPal Developer](https://developer.paypal.com/)
2. Crear aplicación en "My Apps & Credentials"
3. Obtener credenciales:
   - **Sandbox** (pruebas): Client ID y Secret
   - **Live** (producción): Client ID y Secret
4. Configurar en `backend_micro/.env`:
   ```env
   PAYPAL_CLIENT_ID=tu-client-id
   PAYPAL_CLIENT_SECRET=tu-secret
   PAYPAL_ENV=sandbox  # o 'live'
   ```

### 3. OpenAI (para conversión)

1. Ir a [OpenAI Platform](https://platform.openai.com/)
2. Crear API key
3. Configurar en `backend_micro/.env`:
   ```env
   OPENAI_API_KEY=sk-...
   ```

## 📁 Estructura del Proyecto

```
micro-servicios/
├── backend_micro/           # Backend FastAPI
│   ├── app/
│   │   ├── models.py        # Modelos BD (User, Subscription, Payment, Conversion)
│   │   ├── schemas.py       # Schemas Pydantic
│   │   ├── database.py      # Config BD
│   │   ├── auth.py          # Google OAuth + JWT
│   │   ├── subscription_manager.py  # Lógica suscripciones
│   │   ├── routes.py        # Endpoints conversión
│   │   ├── auth_routes.py   # Endpoints auth
│   │   ├── subscription_routes.py  # Endpoints suscripciones
│   │   └── paypal_client.py # Cliente PayPal
│   ├── main.py              # App principal
│   ├── init_db.py           # Script init BD
│   ├── requirements.txt     # Dependencias Python
│   ├── .env.example         # Template variables
│   └── README_PAYMENT_SYSTEM.md  # Docs detalladas
│
├── ExcelConverter/          # Frontend React
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx         # Panel usuario
│   │   │   ├── GoogleLogin.jsx       # Login Google
│   │   │   └── SubscriptionPlans.jsx # Planes
│   │   ├── context/
│   │   │   └── AuthContext.jsx       # Auth global
│   │   ├── pages/
│   │   │   ├── App.jsx               # App principal
│   │   │   ├── Upload.jsx            # Carga archivos
│   │   │   ├── Pay.jsx               # Pagos
│   │   │   └── PayPalReturn.jsx      # Retorno PayPal
│   │   ├── main.jsx         # Entry point
│   │   └── style.css        # Estilos
│   ├── package.json
│   ├── .env.example
│   └── README.md
│
├── setup.sh                 # Script setup Linux/Mac
├── setup.bat                # Script setup Windows
└── README.md                # Este archivo
```

## 🔐 Seguridad

- ✅ Autenticación OAuth 2.0 con Google
- ✅ Tokens JWT con expiración (30 días)
- ✅ Validación de pagos con PayPal
- ✅ CORS configurado correctamente
- ✅ Variables sensibles en `.env` (no commiteadas)
- ✅ Registro completo de transacciones

## 🎯 Flujos de Usuario

### Usuario Anónimo
1. Subir PDF
2. Pagar $20 MXN con PayPal
3. Descargar Excel convertido

### Usuario Registrado (Sin Suscripción)
1. Login con Google
2. Ver dashboard y estadísticas
3. Elegir:
   - Pago único ($20 MXN)
   - Suscripción mensual

### Usuario con Suscripción Activa
1. Login automático
2. Ver conversiones restantes
3. Subir PDF
4. **Conversión automática** (sin pago adicional)
5. Contador actualizado

## 📊 Base de Datos

### Modelos

- **User**: Usuarios autenticados (Google ID, email, nombre)
- **Subscription**: Suscripciones activas con límites y contador
- **Payment**: Historial completo de pagos
- **Conversion**: Registro de todas las conversiones (éxito/fallo)

Por defecto usa **SQLite**. Para producción, cambiar a PostgreSQL/MySQL en `DATABASE_URL`.

## 🚢 Deployment

### Backend (Producción)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno
# Configurar en plataforma (Heroku, Railway, etc.)

# Inicializar BD
python init_db.py

# Ejecutar con Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend (Producción)

```bash
# Build
npm run build

# Desplegar carpeta dist/
# Plataformas sugeridas:
# - Vercel
# - Netlify  
# - AWS S3 + CloudFront
# - GitHub Pages
```

### Variables de Entorno en Producción

**Backend:**
- `PAYPAL_ENV=live`
- `DATABASE_URL=postgresql://...`
- Todas las API keys de producción

**Frontend:**
- `VITE_API_BASE=https://tu-api.com`
- `VITE_GOOGLE_CLIENT_ID=...` (producción)

## 🐛 Troubleshooting

### Backend no inicia
- Verificar que todas las dependencias estén instaladas
- Revisar variables de entorno en `.env`
- Verificar puerto 8000 disponible

### Google Login no funciona
- Verificar `GOOGLE_CLIENT_ID` configurado
- Verificar origen autorizado en Google Console
- Revisar consola del navegador

### PayPal no redirige
- Verificar credenciales de PayPal
- Asegurar que `PAYPAL_ENV` sea correcto
- Revisar logs del backend

### Error de CORS
- Verificar `allow_origins` en `main.py`
- Incluir origen del frontend

## 📚 Documentación Adicional

- **[README_PAYMENT_SYSTEM.md](backend_micro/README_PAYMENT_SYSTEM.md)** - Documentación completa del sistema
- **[ExcelConverter/README.md](ExcelConverter/README.md)** - Documentación del frontend
- `.env.example` - Plantillas de configuración

## 🛠️ Stack Tecnológico

**Backend:**
- FastAPI
- SQLAlchemy
- Google Auth Library
- PyJWT
- PayPal SDK
- OpenAI

**Frontend:**
- React 18
- Vite
- Google Sign-In
- Fetch API

## 📝 Licencia

Propietario - Micro Servicios

## 👥 Soporte

Para problemas o consultas:
1. Revisar logs del backend
2. Revisar consola del navegador
3. Verificar configuración de `.env`
4. Consultar documentación de servicios externos

---

**Desarrollado para Micro Servicios** 🚀
