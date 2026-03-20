"""
Aplicación principal FastAPI
Sistema Multi-Tenant de Gestión Político-Electoral
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .database import create_db_and_tables
from .middleware.tenant_middleware import TenantMiddleware

# Routers
from .routers import (
    committees, auth, administrative_units, committee_types, users,
    admin, events, attendance, surveys, dashboard, secciones, public
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Eventos de inicio y cierre de la aplicación
    """
    # Startup
    print("🚀 Iniciando aplicación...")
    print(f"📊 Base de datos: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    # Crear tablas si no existen
    create_db_and_tables()
    print("✅ Tablas de base de datos verificadas")
    
    yield
    
    # Shutdown
    print("👋 Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema SaaS multi-tenant para gestión político-electoral",
    lifespan=lifespan
)


# ====================================
# MIDDLEWARE
# ====================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant Middleware
app.add_middleware(TenantMiddleware)


# ====================================
# EXCEPTION HANDLERS
# ====================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de excepciones"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc) if settings.ALLOW_LOCALHOST else "Internal server error"
        }
    )


# ====================================
# ROUTES
# ====================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema Multi-Tenant Electoral API",
        "version": settings.APP_VERSION,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ====================================
# INCLUDE ROUTERS
# ====================================

# Autenticación
app.include_router(auth.router, prefix="/api")

# Comités (Módulo Prioritario)
app.include_router(committees.router, prefix="/api")

# Unidades Administrativas
app.include_router(administrative_units.router, prefix="/api")

# Tipos de Comité
app.include_router(committee_types.router, prefix="/api")

# Usuarios y Coordinadores
app.include_router(users.router, prefix="/api")

# Super Administrador
app.include_router(admin.router, prefix="/api")

# Eventos
app.include_router(events.router, prefix="/api")

# Asistencia
app.include_router(attendance.router, prefix="/api")

# Encuestas
app.include_router(surveys.router, prefix="/api")

# Dashboard Estadístico
app.include_router(dashboard.router, prefix="/api")

# Secciones Electorales
app.include_router(secciones.router, prefix="/api")

# Endpoints Públicos (sin auth)
app.include_router(public.router, prefix="/api")


# ====================================
# RUN
# ====================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
