# ⚡ Guía de Configuración Rápida

Esta guía te ayudará a configurar el sistema en menos de 10 minutos.

## 📝 Checklist de Configuración

### ✅ 1. Requisitos del Sistema

- [ ] Python 3.8+ instalado
- [ ] Node.js 18+ instalado
- [ ] npm instalado
- [ ] Cuenta Google Cloud Platform
- [ ] Cuenta PayPal Developer
- [ ] API Key de OpenAI

### ✅ 2. Setup Automático

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### ✅ 3. Configuración de Google OAuth

#### Paso a Paso:

1. **Crear Proyecto**
   - Ir a https://console.cloud.google.com/
   - Clic en "Nuevo Proyecto"
   - Nombre: "Excel Converter"
   - Crear

2. **Habilitar APIs**
   - Menú → "APIs y servicios" → "Biblioteca"
   - Buscar "Google+ API"
   - Habilitar

3. **Crear Credenciales**
   - "APIs y servicios" → "Credenciales"
   - "Crear credenciales" → "ID de cliente de OAuth"
   - Tipo: Aplicación web
   - Nombre: "Excel Converter Web"

4. **Configurar Orígenes**
   - Orígenes autorizados de JavaScript:
     ```
     http://localhost:5173
     https://tu-dominio.com
     ```
   - URIs de redirección autorizadas:
     ```
     http://localhost:5173
     https://tu-dominio.com
     ```

5. **Copiar Credenciales**
   - Copiar el **Client ID** (termina en .apps.googleusercontent.com)
   - Pegar en:
     - `backend_micro/.env` → línea `GOOGLE_CLIENT_ID=`
     - `ExcelConverter/.env` → línea `VITE_GOOGLE_CLIENT_ID=`

### ✅ 4. Configuración de PayPal

#### Paso a Paso:

1. **Crear Cuenta**
   - Ir a https://developer.paypal.com/
   - Registrarse o iniciar sesión

2. **Crear Aplicación**
   - Dashboard → "My Apps & Credentials"
   - Pestaña "Sandbox" (para pruebas)
   - "Create App"
   - Nombre: "Excel Converter"
   - Tipo: Merchant

3. **Obtener Credenciales**
   - Copiar **Client ID**
   - Copiar **Secret** (clic en "Show")

4. **Configurar en Backend**
   - Editar `backend_micro/.env`:
   ```env
   PAYPAL_CLIENT_ID=tu-client-id-aqui
   PAYPAL_CLIENT_SECRET=tu-secret-aqui
   PAYPAL_ENV=sandbox
   ```

5. **Para Producción**
   - Cambiar a pestaña "Live"
   - Obtener credenciales Live
   - Cambiar `PAYPAL_ENV=live`

### ✅ 5. Configuración de OpenAI

#### Paso a Paso:

1. **Crear Cuenta**
   - Ir a https://platform.openai.com/
   - Registrarse o iniciar sesión

2. **Obtener API Key**
   - Menú → "API keys"
   - "Create new secret key"
   - Nombre: "Excel Converter"
   - Copiar la key (solo se muestra una vez)

3. **Configurar**
   - Editar `backend_micro/.env`:
   ```env
   OPENAI_API_KEY=sk-...tu-key-aqui
   ```

### ✅ 6. Variables de Entorno

#### Backend (`backend_micro/.env`)

```env
# Google OAuth
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com

# PayPal
PAYPAL_CLIENT_ID=tu-paypal-client-id
PAYPAL_CLIENT_SECRET=tu-paypal-secret
PAYPAL_ENV=sandbox
PAYPAL_CURRENCY=MXN
PAYPAL_AMOUNT=20.00
PAYPAL_RETURN_URL=http://localhost:5173/return
PAYPAL_CANCEL_URL=http://localhost:5173/cancel

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
JWT_SECRET=cambia-esto-por-un-secret-aleatorio-largo

# Database
DATABASE_URL=sqlite:///./excel_converter.db

# SMTP (opcional)
SMTP_SERVER=smtp.ionos.mx
SMTP_PORT=465
SMTP_USERNAME=contacto@micro-servicios.com.mx
SMTP_PASSWORD=tu-password
RECIPIENT_EMAIL=contacto@micro-servicios.com.mx
```

#### Frontend (`ExcelConverter/.env`)

```env
VITE_API_BASE=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
```

### ✅ 7. Inicializar Base de Datos

```bash
cd backend_micro
source venv/bin/activate  # Windows: venv\Scripts\activate
python init_db.py
```

Deberías ver:
```
INFO:__main__:Creating database tables...
INFO:__main__:Database tables created successfully!
INFO:__main__:Tables created:
INFO:__main__:  - users
INFO:__main__:  - subscriptions
INFO:__main__:  - payments
INFO:__main__:  - conversions
```

### ✅ 8. Ejecutar el Sistema

#### Terminal 1 - Backend:
```bash
cd backend_micro
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

#### Terminal 2 - Frontend:
```bash
cd ExcelConverter
npm run dev
```

Deberías ver:
```
VITE v5.4.2  ready in 342 ms

➜  Local:   http://localhost:5173/
```

### ✅ 9. Verificación

Abre http://localhost:5173 y verifica:

1. **Sin Login:**
   - [ ] Puedes subir un PDF
   - [ ] Aparece el botón de "Iniciar sesión con Google"
   - [ ] Puedes ver las opciones de pago

2. **Con Login:**
   - [ ] Botón de Google funciona
   - [ ] Te autenticas correctamente
   - [ ] Aparece tu nombre y foto
   - [ ] Puedes ver el dashboard

3. **Funcionalidad:**
   - [ ] Subir PDF funciona
   - [ ] Crear orden de PayPal funciona
   - [ ] Ver planes de suscripción funciona

### ✅ 10. Testing con PayPal Sandbox

Para probar pagos:

1. **Obtener Cuenta de Prueba**
   - PayPal Developer → "Sandbox" → "Accounts"
   - Usar credenciales de "Personal" account

2. **Realizar Pago de Prueba**
   - Crear orden en la app
   - Abrir PayPal
   - Login con cuenta sandbox
   - Completar pago
   - Verificar conversión

### 🚨 Troubleshooting Rápido

#### Error: "Google OAuth no configurado"
- Verifica que `GOOGLE_CLIENT_ID` esté en `backend_micro/.env`
- Reinicia el backend

#### Error: "PayPal credentials not found"
- Verifica `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET`
- Reinicia el backend

#### Error: CORS
- Verifica que el frontend esté en puerto 5173
- O actualiza `allow_origins` en `backend_micro/main.py`

#### Backend no inicia
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

#### Frontend no inicia
```bash
# Limpiar e instalar
rm -rf node_modules package-lock.json
npm install
```

## 🎉 ¡Listo!

Si todo funciona, deberías poder:
- ✅ Iniciar sesión con Google
- ✅ Ver tu dashboard
- ✅ Subir PDFs
- ✅ Crear órdenes de pago
- ✅ Ver planes de suscripción

## 📞 Necesitas Ayuda?

1. Revisa los logs del backend (terminal donde corre uvicorn)
2. Revisa la consola del navegador (F12)
3. Verifica que todas las variables de entorno estén configuradas
4. Consulta README_PAYMENT_SYSTEM.md para más detalles

---

**¡Felicitaciones! Sistema listo para usar** 🎊
