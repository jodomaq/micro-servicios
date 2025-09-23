from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging

logger = logging.getLogger("app.database")

# Estrategia de selección de base de datos:
# 1. Si existe DATABASE_URL usarlo tal cual.
# 2. Si se está ejecutando bajo pytest y no hay DATABASE_URL => usar SQLite local.
# 3. Por defecto (entorno normal) usar MySQL.

def _choose_default_url():
    # Fuerza SQLite en entorno de pruebas aunque exista DATABASE_URL
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "sqlite+aiosqlite:///./test.db"
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    return "mysql+aiomysql://iqtest_user:patzcuaro@localhost/iqtest"

DATABASE_URL = _choose_default_url()

try:
    engine = create_async_engine(DATABASE_URL, echo=False)
except Exception as e:
    # Fallback silencioso a SQLite solo si fallo al crear engine inicial
    logger.warning("Fallo creando engine %s, usando SQLite fallback: %s", DATABASE_URL, e)
    DATABASE_URL = "sqlite+aiosqlite:///./fallback.db"
    engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
