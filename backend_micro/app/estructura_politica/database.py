"""
Configuración de base de datos y sesiones
"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import settings


# Crear engine de base de datos
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # Log de SQL queries en desarrollo
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_recycle=3600,  # Reciclar conexiones cada hora
)


def create_db_and_tables():
    """Crear todas las tablas en la base de datos"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI para obtener sesión de base de datos
    
    Yields:
        Session de SQLModel
    """
    with Session(engine) as session:
        yield session
