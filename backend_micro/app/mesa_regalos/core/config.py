from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración central de la aplicación, cargada desde variables de entorno."""

    # Base de datos
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/mesa_de_regalos"

    # Mercado Libre — Afiliados
    ML_CAMP_ID: str = ""

    # PayPal — Suscripciones
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_SECRET: str = ""
    PAYPAL_MODE: str = "sandbox"  # "sandbox" o "live"
    PAYPAL_PLAN_ID: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Aplicación
    FRONTEND_URL: str = "https://micro-servicios.com.mx"
    SECRET_KEY: str = "clave-secreta-cambiar-en-produccion"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    @property
    def paypal_base_url(self) -> str:
        """Devuelve la URL base de PayPal según el modo configurado."""
        if self.PAYPAL_MODE == "live":
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    model_config = {"env_prefix": "MR_", "env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
