# Configuración OAuth 2.0 para Gmail API

Esta guía te ayudará a configurar OAuth 2.0 para enviar correos electrónicos usando Gmail API en tu backend.

## 📋 Requisitos Previos

- Una cuenta de Google
- Acceso a Google Cloud Console
- Python 3.7 o superior

## 🚀 Configuración en Google Cloud Console

### Paso 1: Crear un Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Haz clic en "Seleccionar proyecto" en la parte superior
3. Haz clic en "NUEVO PROYECTO"
4. Asigna un nombre (ej: "micro-servicios-email")
5. Haz clic en "CREAR"

### Paso 2: Habilitar Gmail API

1. Con tu proyecto seleccionado, ve a **APIs y servicios** > **Biblioteca**
2. Busca "Gmail API"
3. Haz clic en "Gmail API"
4. Haz clic en **HABILITAR**

### Paso 3: Configurar Pantalla de Consentimiento OAuth

1. Ve a **APIs y servicios** > **Pantalla de consentimiento de OAuth**
2. Selecciona **Externo** como tipo de usuario
3. Haz clic en **CREAR**
4. Completa la información requerida:
   - **Nombre de la aplicación**: "Micro-Servicios Contact Form"
   - **Correo de asistencia del usuario**: tu email
   - **Correo de contacto del desarrollador**: tu email
5. Haz clic en **GUARDAR Y CONTINUAR**
6. En **Alcances**, haz clic en **AGREGAR O QUITAR ALCANCES**
7. Busca y selecciona:
   - `https://www.googleapis.com/auth/gmail.send`
8. Haz clic en **ACTUALIZAR** y luego **GUARDAR Y CONTINUAR**
9. En **Usuarios de prueba**, agrega tu email
10. Haz clic en **GUARDAR Y CONTINUAR**

### Paso 4: Crear Credenciales OAuth 2.0

1. Ve a **APIs y servicios** > **Credenciales**
2. Haz clic en **+ CREAR CREDENCIALES** > **ID de cliente de OAuth 2.0**
3. Selecciona **Aplicación de escritorio** como tipo
4. Asigna un nombre (ej: "Micro-Servicios Backend")
5. Haz clic en **CREAR**
6. **¡IMPORTANTE!** Descarga el archivo JSON haciendo clic en **DESCARGAR JSON**
7. Renombra el archivo descargado a `credentials.json`

## 🔧 Configuración del Backend

### Paso 1: Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### Paso 2: Colocar el Archivo de Credenciales

1. Coloca el archivo `credentials.json` descargado en la carpeta `backend/`
2. **NUNCA** subas este archivo a tu repositorio Git
3. Agrega `credentials.json` a tu `.gitignore`

### Paso 3: Configurar Variables de Entorno

Edita el archivo `.env` en la carpeta `backend/`:

```env
# Gmail OAuth Configuration
GOOGLE_CREDENTIALS_PATH=credentials.json
RECIPIENT_EMAIL=contacto@micro-servicios.com.mx
```

### Paso 4: Primera Ejecución y Autorización

1. Ejecuta tu servidor por primera vez:
```bash
python start.py
```

2. La primera vez que se envíe un email, se abrirá automáticamente tu navegador
3. Inicia sesión con tu cuenta de Google
4. Autoriza la aplicación para enviar emails
5. Se creará automáticamente un archivo `token.pickle` que guardará tu autorización

## 📁 Estructura de Archivos

```
backend/
├── main.py                    # FastAPI application
├── gmail_oauth.py            # Gmail OAuth handler
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── credentials.json          # OAuth credentials (NO subir a Git)
├── token.pickle             # Authorization token (se crea automáticamente)
└── README_OAUTH_SETUP.md    # Esta guía
```

## ⚠️ Consideraciones de Seguridad

### Archivos a NO subir a Git:
- `credentials.json` - Contiene secretos de cliente OAuth
- `token.pickle` - Contiene tokens de acceso
- `.env` - Puede contener información sensible

### Agrega a tu `.gitignore`:
```gitignore
# OAuth files
credentials.json
token.pickle
*.pickle

# Environment files
.env
```

## 🧪 Probar la Configuración

1. Inicia el servidor:
```bash
python start.py
```

2. Haz una petición POST a `http://localhost:8000/send-email` con el siguiente JSON:
```json
{
  "from_name": "Test User",
  "from_email": "test@example.com",
  "service": "Desarrollo Web",
  "message": "Este es un mensaje de prueba"
}
```

3. Verifica que recibiste el email en la dirección configurada en `RECIPIENT_EMAIL`

## 🔄 Renovación de Tokens

- Los tokens se renuevan automáticamente
- Si hay problemas de autenticación, elimina `token.pickle` y vuelve a autorizar
- Los tokens tienen validez por largos períodos (meses/años)

## 🚨 Solución de Problemas

### Error: "Credentials file not found"
- Verifica que `credentials.json` esté en la carpeta `backend/`
- Verifica la ruta en `GOOGLE_CREDENTIALS_PATH` en `.env`

### Error: "Access blocked: This app's request is invalid"
- Verifica que hayas configurado correctamente la pantalla de consentimiento
- Asegúrate de haber agregado los alcances correctos
- Verifica que tu email esté en la lista de usuarios de prueba

### Error: "Token has been expired or revoked"
- Elimina el archivo `token.pickle`
- Vuelve a ejecutar la aplicación para re-autorizar

## 📊 Límites de Gmail API

- **Cuota diaria**: 1,000,000,000 unidades/día
- **Envío de mensajes**: ~100 unidades por mensaje
- **Límite práctico**: ~10,000,000 emails/día

Para aplicaciones de alto volumen, considera usar servicios como SendGrid o Mailgun.

## 📚 Referencias

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)