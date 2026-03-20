"""
Script para poblar unidades administrativas desde CSV
Crea automáticamente la jerarquía: STATE → REGION → DISTRICT → MUNICIPALITY → SECTION

Uso: python scripts/populate_administrative_units.py --tenant-id 1 --csv-file secciones.csv

El CSV debe tener columnas:
  seccion_numero, municipio_id, nombre_municipio, distrito_id, nombre_distrito, distrito_federal
"""
import argparse
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlmodel import Session, select
from app.database import engine
from app.models import Tenant, AdministrativeUnit, Seccion


def populate(args):
    """Poblar jerarquía desde CSV"""
    with Session(engine) as session:
        # Verificar tenant
        tenant = session.get(Tenant, args.tenant_id)
        if not tenant:
            print(f"❌ Error: Tenant con ID {args.tenant_id} no encontrado.")
            sys.exit(1)
        
        print(f"📁 Procesando CSV: {args.csv_file}")
        print(f"🏢 Tenant: {tenant.name} (ID: {tenant.id})")
        
        # Leer CSV
        with open(args.csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"📊 {len(rows)} filas encontradas en CSV")
        
        # Obtener o crear nodo raíz (STATE)
        state_unit = session.exec(
            select(AdministrativeUnit).where(
                AdministrativeUnit.tenant_id == args.tenant_id,
                AdministrativeUnit.unit_type == "STATE",
                AdministrativeUnit.parent_id == None
            )
        ).first()
        
        if not state_unit:
            state_unit = AdministrativeUnit(
                tenant_id=args.tenant_id,
                name=args.state_name or f"Estado - {tenant.name}",
                code="STATE-1",
                unit_type="STATE",
                parent_id=None,
                created_at=datetime.utcnow()
            )
            session.add(state_unit)
            session.commit()
            session.refresh(state_unit)
            print(f"  ✅ Estado creado: {state_unit.name}")
        else:
            print(f"  ℹ️ Estado existente: {state_unit.name}")
        
        # Cachés para evitar duplicados
        districts = {}   # distrito_id -> AdministrativeUnit
        municipalities = {}  # municipio_id -> AdministrativeUnit
        sections_created = 0
        secciones_created = 0
        
        # Extraer distritos y municipios únicos
        unique_districts = {}
        unique_municipalities = {}
        
        for row in rows:
            dist_id = row.get('distrito_id', '').strip()
            dist_name = row.get('nombre_distrito', '').strip()
            mun_id = row.get('municipio_id', '').strip()
            mun_name = row.get('nombre_municipio', '').strip()
            
            if dist_id and dist_id not in unique_districts:
                unique_districts[dist_id] = dist_name or f"Distrito {dist_id}"
            
            if mun_id and mun_id not in unique_municipalities:
                unique_municipalities[mun_id] = {
                    "name": mun_name or f"Municipio {mun_id}",
                    "distrito_id": dist_id
                }
        
        # Crear distritos
        for dist_id, dist_name in unique_districts.items():
            existing = session.exec(
                select(AdministrativeUnit).where(
                    AdministrativeUnit.tenant_id == args.tenant_id,
                    AdministrativeUnit.unit_type == "DISTRICT",
                    AdministrativeUnit.code == f"DIST-{dist_id}"
                )
            ).first()
            
            if existing:
                districts[dist_id] = existing
            else:
                unit = AdministrativeUnit(
                    tenant_id=args.tenant_id,
                    name=dist_name,
                    code=f"DIST-{dist_id}",
                    unit_type="DISTRICT",
                    parent_id=state_unit.id,
                    seccion_distrito_id=int(dist_id) if dist_id.isdigit() else None,
                    created_at=datetime.utcnow()
                )
                session.add(unit)
                session.commit()
                session.refresh(unit)
                districts[dist_id] = unit
        
        print(f"  ✅ {len(unique_districts)} distritos procesados")
        
        # Crear municipios (hijos de distritos)
        for mun_id, mun_info in unique_municipalities.items():
            existing = session.exec(
                select(AdministrativeUnit).where(
                    AdministrativeUnit.tenant_id == args.tenant_id,
                    AdministrativeUnit.unit_type == "MUNICIPALITY",
                    AdministrativeUnit.code == f"MUN-{mun_id}"
                )
            ).first()
            
            if existing:
                municipalities[mun_id] = existing
            else:
                parent_id = state_unit.id
                if mun_info["distrito_id"] in districts:
                    parent_id = districts[mun_info["distrito_id"]].id
                
                unit = AdministrativeUnit(
                    tenant_id=args.tenant_id,
                    name=mun_info["name"],
                    code=f"MUN-{mun_id}",
                    unit_type="MUNICIPALITY",
                    parent_id=parent_id,
                    seccion_municipio_id=int(mun_id) if mun_id.isdigit() else None,
                    created_at=datetime.utcnow()
                )
                session.add(unit)
                session.commit()
                session.refresh(unit)
                municipalities[mun_id] = unit
        
        print(f"  ✅ {len(unique_municipalities)} municipios procesados")
        
        # Crear secciones y registros en tabla Seccion
        for row in rows:
            sec_num = row.get('seccion_numero', '').strip()
            mun_id = row.get('municipio_id', '').strip()
            dist_id = row.get('distrito_id', '').strip()
            
            if not sec_num:
                continue
            
            # Crear unidad administrativa de tipo SECTION
            existing_unit = session.exec(
                select(AdministrativeUnit).where(
                    AdministrativeUnit.tenant_id == args.tenant_id,
                    AdministrativeUnit.unit_type == "SECTION",
                    AdministrativeUnit.code == f"SEC-{sec_num}"
                )
            ).first()
            
            if not existing_unit:
                parent_id = state_unit.id
                if mun_id in municipalities:
                    parent_id = municipalities[mun_id].id
                elif dist_id in districts:
                    parent_id = districts[dist_id].id
                
                section_unit = AdministrativeUnit(
                    tenant_id=args.tenant_id,
                    name=f"Sección {sec_num}",
                    code=f"SEC-{sec_num}",
                    unit_type="SECTION",
                    parent_id=parent_id,
                    created_at=datetime.utcnow()
                )
                session.add(section_unit)
                sections_created += 1
            
            # Crear registro en tabla Seccion
            existing_seccion = session.exec(
                select(Seccion).where(
                    Seccion.tenant_id == args.tenant_id,
                    Seccion.seccion_numero == sec_num
                )
            ).first()
            
            if not existing_seccion:
                seccion = Seccion(
                    tenant_id=args.tenant_id,
                    seccion_numero=sec_num,
                    municipio_id=int(mun_id) if mun_id and mun_id.isdigit() else None,
                    nombre_municipio=row.get('nombre_municipio', '').strip() or None,
                    distrito_id=int(dist_id) if dist_id and dist_id.isdigit() else None,
                    nombre_distrito=row.get('nombre_distrito', '').strip() or None,
                    distrito_federal=int(row.get('distrito_federal', '0') or '0') if row.get('distrito_federal', '').strip().isdigit() else None
                )
                session.add(seccion)
                secciones_created += 1
        
        session.commit()
        
        print(f"  ✅ {sections_created} secciones (unidades administrativas) creadas")
        print(f"  ✅ {secciones_created} registros en catálogo de secciones creados")
        print(f"\n🎉 Jerarquía poblada exitosamente para tenant '{tenant.name}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poblar unidades administrativas desde CSV")
    parser.add_argument("--tenant-id", type=int, required=True, help="ID del tenant")
    parser.add_argument("--csv-file", required=True, help="Ruta al archivo CSV")
    parser.add_argument("--state-name", default=None, help="Nombre del estado raíz")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: Archivo '{args.csv_file}' no encontrado.")
        sys.exit(1)
    
    populate(args)
