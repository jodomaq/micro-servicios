from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os
import logging
from html import escape as _html_escape
from dotenv import load_dotenv
from smtp_email import SMTPEmailSender

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Micro-Servicios API",
    description="API unificada: Excel Converter, Estructura Política, Mesa de Regalos e IQ Test",
    version="2.1.0"
)

# ====================================
# CORS
# Orígenes base + extras desde EP_CORS_ORIGINS o CORS_ORIGINS
# ====================================
_base_origins = [
    "https://micro-servicios.com.mx",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
]
_extra = os.getenv("CORS_ORIGINS") or os.getenv("EP_CORS_ORIGINS", "")
_extra_list = [o.strip() for o in _extra.split(",") if o.strip()]
_allowed_origins = list(dict.fromkeys(_base_origins + _extra_list))  # dedup preservando orden

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Tenant-ID"],
)

# ====================================
# MIDDLEWARE — Estructura Política (multi-tenant)
# ====================================
try:
    from app.estructura_politica.middleware.tenant_middleware import TenantMiddleware
    app.add_middleware(TenantMiddleware)
    logger.info("TenantMiddleware de Estructura Política cargado")
except Exception as e:
    logger.warning(f"TenantMiddleware no cargado: {e}")

# ====================================
# INICIALIZACIÓN DE BASES DE DATOS
# ====================================

# Excel Converter — SQLite
try:
    from app.database import engine, Base
    Base.metadata.create_all(bind=engine)
    logger.info("DB Excel Converter inicializada")
except Exception as e:
    logger.warning(f"DB Excel Converter no inicializada: {e}")

# Estructura Política — MySQL/MariaDB
try:
    from app.estructura_politica.database import create_db_and_tables as ep_create_tables
    ep_create_tables()
    logger.info("DB Estructura Política inicializada")
except Exception as e:
    logger.warning(f"DB Estructura Política no inicializada: {e}")

# Mesa de Regalos — MySQL/MariaDB
try:
    from app.mesa_regalos.core.database import engine as mr_engine, Base as mr_Base
    from app.mesa_regalos.models.models import User, GiftTable, Gift  # registrar modelos
    mr_Base.metadata.create_all(bind=mr_engine)
    logger.info("DB Mesa de Regalos inicializada")
except Exception as e:
    logger.warning(f"DB Mesa de Regalos no inicializada: {e}")

# ====================================
# ROUTERS — Excel Converter
# ====================================
try:
    from app.routes import router as converter_router
    app.include_router(converter_router)
    logger.info("Rutas Excel Converter cargadas")
except Exception as e:
    logger.warning(f"Rutas Excel Converter no cargadas: {e}")

try:
    from app.auth_routes import router as auth_router
    app.include_router(auth_router)
    logger.info("Rutas Auth (Converter) cargadas")
except Exception as e:
    logger.warning(f"Rutas Auth (Converter) no cargadas: {e}")

try:
    from app.subscription_routes import router as subscription_router
    app.include_router(subscription_router)
    logger.info("Rutas Suscripciones cargadas")
except Exception as e:
    logger.warning(f"Rutas Suscripciones no cargadas: {e}")

# ====================================
# ROUTERS — Estructura Política
# ====================================
try:
    from app.estructura_politica.routers import (
        auth as ep_auth,
        committees,
        administrative_units,
        committee_types,
        users as ep_users,
        admin as ep_admin,
        events,
        attendance,
        surveys,
        dashboard as ep_dashboard,
        secciones,
        public as ep_public,
    )
    app.include_router(ep_auth.router, prefix="/api")
    app.include_router(committees.router, prefix="/api")
    app.include_router(administrative_units.router, prefix="/api")
    app.include_router(committee_types.router, prefix="/api")
    app.include_router(ep_users.router, prefix="/api")
    app.include_router(ep_admin.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(attendance.router, prefix="/api")
    app.include_router(surveys.router, prefix="/api")
    app.include_router(ep_dashboard.router, prefix="/api")
    app.include_router(secciones.router, prefix="/api")
    app.include_router(ep_public.router, prefix="/api")
    logger.info("Rutas Estructura Política cargadas (12 routers)")
except Exception as e:
    logger.warning(f"Rutas Estructura Política no cargadas: {e}")

# ====================================
# SUB-APP — IQ Test (montada en /iqtest/api)
# ====================================
try:
    from app.iqtest.main import app as iqtest_app
    app.mount("/iqtest/api", iqtest_app)
    logger.info("IQ Test montado en /iqtest/api")
except Exception as e:
    logger.warning(f"IQ Test no montado: {e}")

# ====================================
# ROUTERS — Mesa de Regalos
# ====================================
try:
    from app.mesa_regalos.routers import auth as mr_auth
    app.include_router(mr_auth.router)
    logger.info("Rutas Mesa de Regalos cargadas")
except Exception as e:
    logger.warning(f"Rutas Mesa de Regalos no cargadas: {e}")

# ====================================
# ENDPOINTS GENERALES
# ====================================

class ContactForm(BaseModel):
    from_name: str
    from_email: EmailStr
    service: str
    message: str


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Received {request.method} request to {request.url.path}")
    if request.method == "POST":
        logger.info(f"Content-Type: {request.headers.get('content-type')}")
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    return {
        "message": "Micro-Servicios API",
        "version": "2.1.0",
        "status": "active",
        "services": [
            "Excel Converter (/auth, /converter, /subscriptions)",
            "Estructura Política (/api/auth, /api/committees, /api/...)",
            "Mesa de Regalos (/api/v1/auth, /api/v1/...)",
            "IQ Test (/iqtest/api/questions, /iqtest/api/evaluate, /iqtest/api/...)",
        ]
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "micro-servicios-api"}


@app.post("/")
async def root_post():
    raise HTTPException(
        status_code=400,
        detail={
            "error": "Invalid endpoint",
            "message": "Use POST /send-email for sending emails",
            "correct_endpoint": "/send-email"
        }
    )


@app.post("/send-email")
async def send_email(contact_form: ContactForm):
    logger.info(f"Processing email from {contact_form.from_email} for service: {contact_form.service}")

    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.ionos.mx")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_username = os.getenv("SMTP_USERNAME", "contacto@micro-servicios.com.mx")
        smtp_password = os.getenv("SMTP_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL", "contacto@micro-servicios.com.mx")

        if not smtp_password:
            raise ValueError("SMTP_PASSWORD environment variable is required")

        email_client = SMTPEmailSender(
            smtp_server=smtp_server,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password
        )

        subject = f"Nuevo contacto desde Micro-Servicios - {contact_form.service}"

        # Escapar HTML para prevenir inyección
        safe_name = _html_escape(contact_form.from_name)
        safe_email = _html_escape(str(contact_form.from_email))
        safe_service = _html_escape(contact_form.service)
        safe_message = _html_escape(contact_form.message).replace("\n", "<br>")

        html_body = f"""
        <html>
            <body>
                <h2>Nuevo mensaje de contacto desde el sitio web</h2>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Nombre:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{safe_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Email:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{safe_email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Servicio de interés:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{safe_service}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Mensaje:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{safe_message}</td>
                    </tr>
                </table>
                <p><small>Este mensaje fue enviado desde el formulario de contacto del sitio web Micro-Servicios.</small></p>
            </body>
        </html>
        """

        text_body = (
            f"Nuevo mensaje de contacto desde el sitio web:\n\n"
            f"Nombre: {contact_form.from_name}\n"
            f"Email: {contact_form.from_email}\n"
            f"Servicio de interés: {contact_form.service}\n\n"
            f"Mensaje:\n{contact_form.message}\n\n"
            "---\nEste mensaje fue enviado desde el formulario de contacto de Micro-Servicios."
        )

        result = email_client.send_html_email(
            to_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=smtp_username
        )

        return {"message": "Email enviado exitosamente", "status": "success"}

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al enviar el correo. Intenta más tarde.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
