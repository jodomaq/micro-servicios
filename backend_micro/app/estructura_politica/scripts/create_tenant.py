"""
Script para crear un nuevo tenant desde línea de comandos
Uso: python scripts/create_tenant.py --name "Partido..." --subdomain "partido-x" --email admin@email.com --admin-name "Admin"
"""
import argparse
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.database import engine
from app.models import Tenant, User, SubscriptionPlan, CommitteeType, AdministrativeUnit


def create_tenant(args):
    """Crear un nuevo tenant con usuario admin y estructura básica"""
    with Session(engine) as session:
        # Verificar que el subdominio no exista
        existing = session.exec(
            select(Tenant).where(Tenant.subdomain == args.subdomain)
        ).first()
        if existing:
            print(f"❌ Error: El subdominio '{args.subdomain}' ya está en uso.")
            sys.exit(1)
        
        # Obtener plan de suscripción
        plan = session.get(SubscriptionPlan, args.plan_id)
        if not plan:
            print(f"❌ Error: Plan con ID {args.plan_id} no encontrado.")
            print("Planes disponibles:")
            plans = session.exec(select(SubscriptionPlan)).all()
            for p in plans:
                print(f"  ID {p.id}: {p.name} (${p.price_monthly}/mes)")
            sys.exit(1)
        
        # Crear tenant
        tenant = Tenant(
            name=args.name,
            subdomain=args.subdomain,
            contact_email=args.email,
            contact_phone=args.phone,
            subscription_plan_id=args.plan_id,
            primary_color=args.primary_color,
            secondary_color=args.secondary_color,
            max_users=plan.max_users,
            max_committees=plan.max_committees,
            max_storage_mb=plan.max_storage_mb,
            subscription_status="trial" if args.trial else "active",
            is_active=True,
            trial_ends_at=datetime.utcnow() + timedelta(days=7) if args.trial else None,
            created_at=datetime.utcnow()
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        print(f"✅ Tenant creado: ID={tenant.id}, nombre='{tenant.name}', subdominio='{tenant.subdomain}'")
        
        # Crear usuario administrador
        admin_user = User(
            tenant_id=tenant.id,
            email=args.email,
            name=args.admin_name,
            phone=args.phone,
            is_tenant_admin=True,
            is_super_admin=False,
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        print(f"✅ Usuario admin creado: ID={admin_user.id}, email='{admin_user.email}'")
        
        # Crear tipos de comité por defecto
        default_types = [
            ("Comité Seccional", "Comité a nivel de sección electoral"),
            ("Comité Municipal", "Comité a nivel municipal"),
            ("Comité Distrital", "Comité a nivel de distrito"),
        ]
        for type_name, type_desc in default_types:
            ct = CommitteeType(
                tenant_id=tenant.id,
                name=type_name,
                description=type_desc,
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(ct)
        session.commit()
        print(f"✅ {len(default_types)} tipos de comité creados")
        
        # Crear unidad administrativa raíz (Estado)
        state_unit = AdministrativeUnit(
            tenant_id=tenant.id,
            name=args.state_name if args.state_name else f"Estado - {args.name}",
            code="STATE-1",
            unit_type="STATE",
            parent_id=None,
            created_at=datetime.utcnow()
        )
        session.add(state_unit)
        session.commit()
        session.refresh(state_unit)
        print(f"✅ Unidad administrativa raíz creada: '{state_unit.name}'")
        
        print("\n" + "=" * 60)
        print(f"🎉 Tenant '{tenant.name}' creado exitosamente!")
        print(f"   Subdominio: {tenant.subdomain}")
        print(f"   Admin: {admin_user.email}")
        print(f"   Plan: {plan.name}")
        if args.trial:
            print(f"   Trial: 7 días (hasta {tenant.trial_ends_at})")
        print(f"   Token dev: dev_token_{admin_user.id}_{tenant.id}")
        print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear un nuevo tenant")
    parser.add_argument("--name", required=True, help="Nombre de la organización")
    parser.add_argument("--subdomain", required=True, help="Subdominio único")
    parser.add_argument("--email", required=True, help="Email del administrador")
    parser.add_argument("--admin-name", required=True, help="Nombre del administrador")
    parser.add_argument("--phone", default=None, help="Teléfono de contacto")
    parser.add_argument("--plan-id", type=int, default=1, help="ID del plan de suscripción (default: 1)")
    parser.add_argument("--primary-color", default="#1976d2", help="Color primario hex")
    parser.add_argument("--secondary-color", default="#dc004e", help="Color secundario hex")
    parser.add_argument("--state-name", default=None, help="Nombre del estado raíz")
    parser.add_argument("--trial", action="store_true", default=True, help="Crear en modo trial (7 días)")
    
    args = parser.parse_args()
    create_tenant(args)
