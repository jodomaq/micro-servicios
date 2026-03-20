"""
Script para crear la base de datos y poblar datos iniciales
"""
import sys
import os

# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import create_db_and_tables, engine
from app.models import SubscriptionPlan, Tenant, User
from sqlmodel import Session
from datetime import datetime, timedelta


def create_subscription_plans():
    """Crear planes de suscripción iniciales"""
    with Session(engine) as session:
        # Verificar si ya existen planes
        existing = session.query(SubscriptionPlan).first()
        if existing:
            print("✅ Planes de suscripción ya existen")
            return
        
        plans = [
            SubscriptionPlan(
                name="Básico",
                max_users=5,
                max_committees=50,
                max_storage_mb=1024,  # 1 GB
                price_monthly=499.0,
                features='{"dashboard": true, "attendance": false, "surveys": false}',
                is_active=True
            ),
            SubscriptionPlan(
                name="Intermedio",
                max_users=20,
                max_committees=200,
                max_storage_mb=5120,  # 5 GB
                price_monthly=999.0,
                features='{"dashboard": true, "attendance": true, "surveys": false}',
                is_active=True
            ),
            SubscriptionPlan(
                name="Premium",
                max_users=50,
                max_committees=1000,
                max_storage_mb=20480,  # 20 GB
                price_monthly=1999.0,
                features='{"dashboard": true, "attendance": true, "surveys": true, "api": true}',
                is_active=True
            ),
            SubscriptionPlan(
                name="Enterprise",
                max_users=999999,
                max_committees=999999,
                max_storage_mb=999999,
                price_monthly=0.0,  # Contactar
                features='{"dashboard": true, "attendance": true, "surveys": true, "api": true, "custom": true}',
                is_active=True
            ),
        ]
        
        for plan in plans:
            session.add(plan)
        
        session.commit()
        print(f"✅ Creados {len(plans)} planes de suscripción")


def create_demo_tenant():
    """Crear tenant de demostración"""
    with Session(engine) as session:
        # Verificar si ya existe
        existing = session.query(Tenant).filter(Tenant.subdomain == "demo").first()
        if existing:
            print("✅ Tenant demo ya existe")
            return existing
        
        # Obtener plan básico
        basic_plan = session.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == "Básico"
        ).first()
        
        if not basic_plan:
            print("❌ No se encontró el plan Básico")
            return None
        
        # Crear tenant
        tenant = Tenant(
            name="Organización Demo",
            subdomain="demo",
            logo_url=None,
            primary_color="#1976d2",
            secondary_color="#dc004e",
            is_active=True,
            subscription_plan_id=basic_plan.id,
            subscription_status="trial",
            trial_ends_at=datetime.utcnow() + timedelta(days=7),
            max_users=basic_plan.max_users,
            max_committees=basic_plan.max_committees,
            max_storage_mb=basic_plan.max_storage_mb,
            contact_email="demo@micro-servicios.com.mx",
            contact_phone="+52 123 456 7890",
            created_at=datetime.utcnow()
        )
        
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        
        print(f"✅ Tenant demo creado: {tenant.name} ({tenant.subdomain})")
        return tenant


def create_demo_admin(tenant: Tenant):
    """Crear usuario administrador demo"""
    with Session(engine) as session:
        # Verificar si ya existe
        existing = session.query(User).filter(
            User.tenant_id == tenant.id,
            User.email == "admin@demo.com"
        ).first()
        
        if existing:
            print("✅ Usuario admin demo ya existe")
            return
        
        # Crear admin
        admin = User(
            tenant_id=tenant.id,
            email="admin@demo.com",
            name="Administrador Demo",
            phone="+52 123 456 7890",
            picture_url=None,
            is_tenant_admin=True,
            is_super_admin=False,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        session.add(admin)
        session.commit()
        
        print(f"✅ Usuario admin demo creado: {admin.email}")


def create_super_admin():
    """Crear super administrador del sistema"""
    with Session (engine) as session:
        # Verificar si ya existe
        existing = session.query(User).filter(User.is_super_admin == True).first()
        
        if existing:
            print("✅ Super admin ya existe")
            return
        
        # Obtener primer tenant para asociar (aunque super admin no está limitado a un tenant)
        first_tenant = session.query(Tenant).first()
        if not first_tenant:
            print("❌ No hay tenants creados. Crea uno primero.")
            return
        
        # Crear super admin
        super_admin = User(
            tenant_id=first_tenant.id,  # Se asocia a un tenant pero tiene acceso global
            email="superadmin@micro-servicios.com.mx",
            name="Super Administrador",
            phone="+52 999 999 9999",
            is_tenant_admin=False,
            is_super_admin=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        session.add(super_admin)
        session.commit()
        
        print(f"✅ Super Admin creado: {super_admin.email}")


def main():
    """Función principal"""
    print("=" * 60)
    print("🗄️  CREACIÓN DE BASE DE DATOS Y DATOS INICIALES")
    print("=" * 60)
    
    # Crear tablas
    print("\n📝 Creando tablas...")
    create_db_and_tables()
    print("✅ Tablas creadas exitosamente")
    
    # Crear planes de suscripción
    print("\n💳 Creando planes de suscripción...")
    create_subscription_plans()
    
    # Crear tenant demo
    print("\n🏢 Creando tenant demo...")
    demo_tenant = create_demo_tenant()
    
    if demo_tenant:
        # Crear admin demo
        print("\n👤 Creando usuario admin demo...")
        create_demo_admin(demo_tenant)
    
    # Crear super admin
    print("\n🦸 Creando super administrador...")
    create_super_admin()
    
    print("\n" + "=" * 60)
    print("✅ ¡BASE DE DATOS INICIALIZADA EXITOSAMENTE!")
    print("=" * 60)
    print("\n📋 Resumen:")
    print("   - Tablas creadas")
    print("   - 4 planes de suscripción")
    print("   - 1 tenant demo (subdomain: demo)")
    print("   - 1 admin demo (demo@demo.com)")
    print("   - 1 super admin (superadmin@micro-servicios.com.mx)")
    print("\n🚀 Puedes iniciar el servidor con: uvicorn app.main:app --reload")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
