"""
Middleware para identificación automática de tenant
Extrae el tenant por subdominio o header X-Tenant-ID
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlmodel import Session, select
from ..database import engine
from ..models import Tenant
from ..config import settings


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que identifica el tenant en cada request y lo inyecta en request.state
    """
    
    async def dispatch(self, request: Request, call_next):
        # Rutas que no requieren tenant (públicas, health checks, etc.)
        public_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/public/",
        ]
        
        # Verificar si es una ruta pública
        is_public = any(request.url.path.startswith(path) for path in public_paths)
        
        if is_public:
            # No requerir tenant para rutas públicas
            request.state.tenant_id = None
            request.state.tenant = None
            response = await call_next(request)
            return response
        
        tenant_id = None
        tenant = None
        
        try:
            with Session(engine) as session:
                # Método 1: Extraer por subdominio
                host = request.headers.get("host", "")
                
                if settings.ALLOW_LOCALHOST and ("localhost" in host or "127.0.0.1" in host):
                    # En desarrollo, usar header o primer tenant disponible
                    tenant_header = request.headers.get("X-Tenant-ID")
                    if tenant_header:
                        tenant_id = int(tenant_header)
                    else:
                        # Usar primer tenant activo (solo para desarrollo)
                        first_tenant = session.exec(
                            select(Tenant).where(Tenant.is_active == True).limit(1)
                        ).first()
                        if first_tenant:
                            tenant = first_tenant
                            tenant_id = first_tenant.id
                else:
                    # Producción: extraer subdomain
                    parts = host.split(".")
                    if len(parts) >= 3:  # ej: accion.micro-servicios.com.mx
                        subdomain = parts[0]
                        tenant = session.exec(
                            select(Tenant).where(
                                Tenant.subdomain == subdomain,
                                Tenant.is_active == True
                            )
                        ).first()
                        
                        if tenant:
                            tenant_id = tenant.id
                
                # Método 2: Header X-Tenant-ID (fallback)
                if not tenant_id:
                    tenant_header = request.headers.get("X-Tenant-ID")
                    if tenant_header:
                        tenant_id = int(tenant_header)
                
                # Cargar tenant si solo tenemos el ID
                if tenant_id and not tenant:
                    tenant = session.get(Tenant, tenant_id)
                    
                    if not tenant or not tenant.is_active:
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "Tenant inactivo o no encontrado"}
                        )
                
                # Verificar suscripción expirada
                if tenant:
                    from datetime import datetime
                    if tenant.subscription_status == "suspended":
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "Suscripción suspendida. Por favor, actualice su método de pago."}
                        )
                    
                    # Verificar trial expirado
                    if (tenant.subscription_status == "trial" and 
                        tenant.trial_ends_at and 
                        tenant.trial_ends_at < datetime.utcnow()):
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "Período de prueba expirado. Por favor, suscríbase a un plan."}
                        )
        
        except Exception as e:
            print(f"Error en TenantMiddleware: {e}")
            # En caso de error, continuar sin tenant (fallará en dependencias si es necesario)
            pass
        
        # Inyectar en request.state
        request.state.tenant_id = tenant_id
        request.state.tenant = tenant
        
        # Continuar con el request
        response = await call_next(request)
        
        # Agregar header informativo
        if tenant:
            response.headers["X-Tenant-Name"] = tenant.name
        
        return response
