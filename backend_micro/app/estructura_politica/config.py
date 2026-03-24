"""
Configuración centralizada de la aplicación
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno"""
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "estructura_user"
    DB_PASSWORD: str = "uk96/*BRR"
    DB_NAME: str = "estructura"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    # JWT
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Microsoft OAuth
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"
    
    # PayPal
    PAYPAL_MODE: str = "sandbox"  # 'sandbox' o 'live'
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_CURRENCY: str = "MXN"
    PAYPAL_AMOUNT: str = "20.00"
    PAYPAL_RETURN_URL: str = "https://micro-servicios.com.mx/registro/exito"
    PAYPAL_CANCEL_URL: str = "https://micro-servicios.com.mx/registro/cancelado"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@micro-servicios.com.mx"
    SMTP_FROM_NAME: str = "Sistema Electoral"
    
    # Application
    APP_NAME: str = "Sistema Multi-Tenant Electoral"
    APP_VERSION: str = "1.0.0"
    API_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Domain
    BASE_DOMAIN: str = "micro-servicios.com.mx"
    ALLOW_LOCALHOST: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175"
    
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    ALLOWED_HOSTS: str = "*"
    
    # Encryption
    ENCRYPTION_KEY: str = "change-this-encryption-key-32-chars-min"
    
    class Config:
        env_prefix = "EP_"
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Obtener configuración singleton"""
    return Settings()


# Instancia global de configuración
settings = get_settings()


def get_tenant_upload_dir(tenant_id: int) -> str:
    """
    Obtener directorio de uploads para un tenant específico
    
    Args:
        tenant_id: ID del tenant
        
    Returns:
        Ruta del directorio de uploads
    """
    path = os.path.join(settings.UPLOAD_DIR, str(tenant_id))
    os.makedirs(path, exist_ok=True)
    return path


def get_committee_upload_dir(tenant_id: int, committee_id: int) -> str:
    """
    Obtener directorio de uploads para un comité específico
    
    Args:
        tenant_id: ID del tenant
        committee_id: ID del comité
        
    Returns:
        Ruta del directorio de uploads
    """
    path = os.path.join(settings.UPLOAD_DIR, str(tenant_id), "committees", str(committee_id))
    os.makedirs(path, exist_ok=True)
    return path
