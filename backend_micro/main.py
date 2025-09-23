from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os
import logging
from dotenv import load_dotenv
from smtp_email import SMTPEmailSender

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Micro-Servicios Contact API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://micro-servicios.com.mx", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class ContactForm(BaseModel):
    from_name: str
    from_email: EmailStr
    service: str
    message: str

# Add middleware to log all requests
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
        "message": "Micro-Servicios Contact API",
        "status": "active",
        "endpoints": {
            "send_email": "/send-email (POST)",
            "health": "/health (GET)"
        }
    }

# Add a health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "contact-api"}

# Handle POST requests to root (common misconfiguration)
@app.post("/")
async def root_post():
    logger.warning("POST request received at root path instead of /send-email")
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
        # SMTP configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.ionos.mx")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_username = os.getenv("SMTP_USERNAME", "contacto@micro-servicios.com.mx")
        smtp_password = os.getenv("SMTP_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL", "contacto@micro-servicios.com.mx")
        
        # Validate required environment variables
        if not smtp_password:
            raise ValueError("SMTP_PASSWORD environment variable is required")
        
        logger.info(f"Initializing SMTP client with server: {smtp_server}:{smtp_port}")
        
        # Initialize SMTP client
        email_client = SMTPEmailSender(
            smtp_server=smtp_server,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password
        )
        
        # Create email subject
        subject = f"Nuevo contacto desde Micro-Servicios - {contact_form.service}"
        
        # Create HTML email body
        html_body = f"""
        <html>
            <body>
                <h2>Nuevo mensaje de contacto desde el sitio web</h2>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Nombre:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{contact_form.from_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Email:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{contact_form.from_email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Servicio de interés:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{contact_form.service}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;"><strong>Mensaje:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{contact_form.message}</td>
                    </tr>
                </table>
                <p><small>Este mensaje fue enviado desde el formulario de contacto del sitio web Micro-Servicios.</small></p>
            </body>
        </html>
        """
        
        # Create plain text version as fallback
        text_body = f"""
        Nuevo mensaje de contacto desde el sitio web:
        
        Nombre: {contact_form.from_name}
        Email: {contact_form.from_email}
        Servicio de interés: {contact_form.service}
        
        Mensaje:
        {contact_form.message}
        
        ---
        Este mensaje fue enviado desde el formulario de contacto del sitio web Micro-Servicios.
        """
        
        logger.info(f"Sending email to {recipient_email}")
        
        # Send email using SMTP
        result = email_client.send_html_email(
            to_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=smtp_username
        )
        
        logger.info(f"Email sent successfully via SMTP")
        
        return {
            "message": "Email enviado exitosamente",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al enviar email: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
