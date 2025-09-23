# Configuración SMTP para Micro-Servicios

Esta guía documenta la configuración del sistema de envío de correos electrónicos usando SMTP en lugar de Gmail OAuth.

## 📧 Configuración Actual

El sistema utiliza un servidor SMTP personalizado configurado mediante variables de entorno:

- **Servidor SMTP**: smtp.ionos.mx
- **Puerto**: 465 (SSL/TLS)
- **Cuenta**: contacto@micro-servicios.com.mx
- **Autenticación**: Contraseña normal

## ⚙️ Variables de Entorno

Crea un archivo `.env` en el directorio del backend con las siguientes variables:

```bash
# Configuración SMTP - IONOS
SMTP_SERVER=smtp.ionos.mx
SMTP_PORT=465
SMTP_USERNAME=contacto@micro-servicios.com.mx
SMTP_PASSWORD=tu_contraseña_aquí

# Email de destinatario
RECIPIENT_EMAIL=contacto@micro-servicios.com.mx
```

### Variables Disponibles

| Variable | Descripción | Valor por Defecto | Requerida |
|----------|-------------|-------------------|-----------|
| `SMTP_SERVER` | Servidor SMTP | smtp.ionos.mx | No |
| `SMTP_PORT` | Puerto SMTP | 465 | No |
| `SMTP_USERNAME` | Usuario de email | contacto@micro-servicios.com.mx | No |
| `SMTP_PASSWORD` | Contraseña del email | - | ✅ Sí |
| `RECIPIENT_EMAIL` | Email destinatario | contacto@micro-servicios.com.mx | No |

## 🔧 Archivos Principales

### `smtp_email.py`
Clase principal que maneja el envío de correos electrónicos vía SMTP:
- `SMTPEmailSender`: Clase principal para envío de emails
- `send_email()`: Envío de emails de texto plano
- `send_html_email()`: Envío de emails con formato HTML

### `main.py`
API FastAPI que maneja los endpoints:
- `POST /send-email`: Endpoint principal para envío de correos desde el formulario de contacto
- Utiliza la clase `SMTPEmailSender` para el envío real

## 🚀 Instalación y Uso

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar el Servidor

```bash
python main.py
```

O usando uvicorn directamente:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Probar el Endpoint

```bash
curl -X POST "http://localhost:8000/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "from_name": "Juan Pérez",
    "from_email": "juan@example.com",
    "service": "Desarrollo Web",
    "message": "Me interesa conocer más sobre sus servicios"
  }'
```

## 📦 Dependencias

Las dependencias actuales son mínimas y no requieren configuración OAuth:

- `fastapi==0.104.1`
- `uvicorn==0.24.0`
- `python-multipart==0.0.6`
- `python-dotenv==1.0.0`
- `pydantic[email]==2.5.0`

## 🔒 Seguridad

✅ **Configuración Actual**: Las credenciales están almacenadas en variables de entorno (archivo `.env`)

### Recomendaciones de Seguridad:

- ✅ **Variables de entorno**: Las credenciales están en el archivo `.env`
- ⚠️ **Archivo .env**: Asegúrate de que `.env` esté en `.gitignore`
- 🔄 **Rotación de contraseñas**: Considera cambiar las contraseñas periódicamente
- 🔐 **Producción**: Para entornos de producción, usa un sistema de gestión de secretos (AWS Secrets Manager, Azure Key Vault, etc.)

### Archivo .gitignore

Asegúrate de que tu `.gitignore` incluya:
```
.env
.env.local
.env.production
*.env
```

## 📋 Endpoints Disponibles

### `GET /`
Información básica de la API y endpoints disponibles.

### `GET /health`
Endpoint de salud para verificar que el servicio está funcionando.

### `POST /send-email`
Envío de correos electrónicos desde el formulario de contacto.

**Parámetros:**
- `from_name`: Nombre del remitente
- `from_email`: Email del remitente
- `service`: Servicio de interés
- `message`: Mensaje del formulario

## 🔄 Migración desde Gmail OAuth

Los siguientes archivos han sido renombrados como respaldo:
- `gmail_oauth.py` → `gmail_oauth_backup.py`
- `generate_token.py` → `generate_token_backup.py`
- `credentials.json` → `credentials_backup.json`
- `token.pickle` → `token_backup.pickle`

## 🚨 Solución de Problemas

### Error de Conexión SMTP
- Verificar que el servidor SMTP esté accesible
- Confirmar credenciales de email
- Verificar configuración de firewall

### Error de Autenticación
- Verificar usuario y contraseña
- Confirmar que la cuenta permite acceso SMTP

### Error de SSL/TLS
- Verificar que el puerto 465 esté disponible
- Confirmar configuración SSL en el servidor