import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal, init_db
from app.models.user import User, Role
from app.models.machine import ProductionLine, Machine, MachineReading, MachineHealthHistory
from app.models.product import Product
from app.models.inventory import InventoryMaterial, InventoryTransaction
from app.models.production import ProductionOrder, ProductionBatch
from app.models.maintenance import MaintenanceRecord
from app.models.alert import Alert
from app.services.auth import AuthService
from app.services.reading import ReadingPipelineService
from app.schemas.reading import MachineReadingCreate
from app.services.scheduler import ProductionSchedulerService
from app.utils.logger import logger

def seed_database():
    logger.info("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Roles & Default Admin / Managers / Operators
        logger.info("Seeding roles and users...")
        AuthService.initialize_default_roles(db)

        users_to_seed = [
            ("admin@nexpharm.ai", "Dr. Alexander Vance", "ADMIN", "NexPharmAdmin2026!"),
            ("prod.manager@nexpharm.ai", "Elena Rostova", "PRODUCTION_MANAGER", "ProdManager2026!"),
            ("maint.lead@nexpharm.ai", "Marcus Thorne", "MAINTENANCE_MANAGER", "MaintLead2026!"),
            ("quality.head@nexpharm.ai", "Dr. Meera Patel", "QUALITY_MANAGER", "QualityHead2026!"),
            ("operator1@nexpharm.ai", "David Chen", "OPERATOR", "Operator2026!")
        ]
        for email, name, role, pwd in users_to_seed:
            existing = db.query(User).filter(User.email == email.lower()).first()
            if not existing:
                from app.schemas.user import UserCreate
                AuthService.register_user(db, UserCreate(
                    email=email,
                    full_name=name,
                    role=role,
                    password=pwd
                ))

        # 2. Production Lines
        logger.info("Seeding production lines...")
        lines_data = [
            ("LINE-1", "Solid Dosage Tableting Line 1", "High-speed rotary tablet compression and coating line"),
            ("LINE-2", "Sterile Injectable Fill-Finish Line", "Aseptic vial filling and lyophilization line"),
            ("LINE-3", "Liquid Oral Suspension Line", "Automated compounding, suspension homogenization, and bottling")
        ]
        line_objs = {}
        for code, name, desc in lines_data:
            line = db.query(ProductionLine).filter(ProductionLine.line_code == code).first()
            if not line:
                line = ProductionLine(line_code=code, name=name, description=desc)
                db.add(line)
                db.commit()
                db.refresh(line)
            line_objs[code] = line

        # 3. Machines
        logger.info("Seeding machines across cleanrooms...")
        machines_data = [
            ("M-101", "Fette Rotary Press 2090", "M", "LINE-1", "Cleanroom Suite 101", "RUNNING"),
            ("M-102", "Glatt Fluid Bed Granulator FB-500", "H", "LINE-1", "Granulation Bay 102", "RUNNING"),
            ("M-103", "Bohle High-Shear Mixer B-600", "L", "LINE-1", "Compounding Room 103", "IDLE"),
            ("M-201", "Bosch Aseptic Vial Filler ARX", "M", "LINE-2", "Grade A Cleanroom 201", "RUNNING"),
            ("M-202", "Telstar Industrial Lyophilizer L-120", "H", "LINE-2", "Freeze-Drying Suite 202", "MAINTENANCE"),
            ("M-301", "FrymaKoruma Homogenizer V-800", "L", "LINE-3", "Liquid Processing Bay 301", "RUNNING")
        ]
        mach_objs = {}
        for mid, name, mtype, lcode, loc, status in machines_data:
            m = db.query(Machine).filter(Machine.machine_id == mid).first()
            if not m:
                m = Machine(
                    machine_id=mid,
                    machine_name=name,
                    machine_type=mtype,
                    production_line=lcode,
                    production_line_id=line_objs[lcode].id,
                    location=loc,
                    status=status,
                    installation_date=datetime.now(timezone.utc) - timedelta(days=365)
                )
                db.add(m)
                db.commit()
                db.refresh(m)
            mach_objs[mid] = m

        # 4. Raw Material Inventory
        logger.info("Seeding pharmaceutical raw materials...")
        materials_data = [
            ("MAT-API-PARA", "Paracetamol Active Pharmaceutical Ingredient (Micronized)", "API", 2500.0, "kg", 300.0, "Lonza Pharma", 180),
            ("MAT-API-AMOX", "Amoxicillin Trihydrate Powder (Sterile Grade)", "API", 850.0, "kg", 150.0, "DSM Sinochem", 240),
            ("MAT-EXC-MCC", "Microcrystalline Cellulose (Avicel PH-102)", "EXCIPIENT", 4000.0, "kg", 500.0, "FMC BioPolymer", 365),
            ("MAT-EXC-MAG", "Magnesium Stearate (Vegetable Grade Lubricant)", "EXCIPIENT", 450.0, "kg", 80.0, "Mallinckrodt", 400),
            ("MAT-SOL-WFI", "Water for Injection (USP Sterile)", "SOLVENT", 15000.0, "liters", 2000.0, "In-House WFI Generation", 7),
            ("MAT-PKG-BLIST", "PVDC Barrier Blister Foil 250mc", "PACKAGING", 120.0, "kg", 200.0, "Klöckner Pentaplast", 700) # Intentionally Low Stock!
        ]
        for mcode, mname, cat, qty, unit, reorder, supplier, exp_days in materials_data:
            mat = db.query(InventoryMaterial).filter(InventoryMaterial.material_code == mcode).first()
            if not mat:
                mat = InventoryMaterial(
                    material_code=mcode,
                    material_name=mname,
                    category=cat,
                    quantity=qty,
                    unit=unit,
                    reorder_level=reorder,
                    supplier=supplier,
                    expiry_date=datetime.now(timezone.utc) + timedelta(days=exp_days),
                    batch_number=f"LOT-{mcode[-4:]}-2026"
                )
                db.add(mat)
                db.commit()

        # 5. Products
        logger.info("Seeding pharmaceutical products & BOMs...")
        products_data = [
            ("PROD-PARA-500", "Paracetamol 500mg Film-Coated Tablets", "Analgesic and antipyretic oral tablets", 20000, 3.5, {
                "MAT-API-PARA": 10.0,
                "MAT-EXC-MCC": 4.0,
                "MAT-EXC-MAG": 0.5
            }),
            ("PROD-AMOX-250", "Amoxicillin 250mg/5ml Oral Suspension", "Broad-spectrum beta-lactam antibacterial suspension", 5000, 4.0, {
                "MAT-API-AMOX": 1.25,
                "MAT-SOL-WFI": 500.0
            }),
            ("PROD-STER-INJ", "Sterile Hydration Solution 100ml Infusion", "Electrolyte sterile parenteral infusion", 8000, 5.0, {
                "MAT-SOL-WFI": 800.0
            })
        ]
        prod_objs = {}
        for pcode, pname, pdesc, bsize, ptime, bom in products_data:
            p = db.query(Product).filter(Product.product_code == pcode).first()
            if not p:
                p = Product(
                    product_code=pcode,
                    product_name=pname,
                    description=pdesc,
                    batch_size=bsize,
                    standard_production_time=ptime,
                    required_materials=bom,
                    status="ACTIVE"
                )
                db.add(p)
                db.commit()
                db.refresh(p)
            prod_objs[pcode] = p

        # 6. Production Orders
        logger.info("Seeding production orders...")
        orders_data = [
            ("ORD-2026-001", prod_objs["PROD-PARA-500"].id, 40000, "HIGH", 3),
            ("ORD-2026-002", prod_objs["PROD-AMOX-250"].id, 10000, "URGENT", 2),
            ("ORD-2026-003", prod_objs["PROD-STER-INJ"].id, 16000, "MEDIUM", 5)
        ]
        for ocode, pid, qty, prio, due_days in orders_data:
            order = db.query(ProductionOrder).filter(ProductionOrder.order_code == ocode).first()
            if not order:
                order = ProductionOrder(
                    order_code=ocode,
                    product_id=pid,
                    quantity=qty,
                    priority=prio,
                    due_date=datetime.now(timezone.utc) + timedelta(days=due_days),
                    status="PLANNED"
                )
                db.add(order)
                db.commit()

        # 7. Ingest Realistic Telemetry Readings through the Pipeline
        logger.info("Ingesting initial machine telemetry through ML pipeline...")
        readings_to_ingest = [
            # Normal Healthy Machine M-101
            ("M-101", "M", 298.2, 308.7, 1551.0, 42.8, 12.0),
            # Normal Healthy Machine M-102
            ("M-102", "H", 298.4, 308.9, 1500.0, 40.5, 45.0),
            # Normal Healthy Machine M-103
            ("M-103", "L", 297.9, 308.1, 1530.0, 38.0, 20.0),
            # Stressed Machine M-201 (Moderate wear)
            ("M-201", "M", 301.2, 310.8, 1420.0, 52.3, 160.0),
            # Degraded Machine M-301 (Approaching wear threshold)
            ("M-301", "L", 303.5, 312.4, 1310.0, 58.2, 195.0)
        ]
        for mid, mtype, atemp, ptemp, rpm, trq, wear in readings_to_ingest:
            ReadingPipelineService.ingest_reading(db, MachineReadingCreate(
                machine_id=mid,
                machine_type=mtype,
                air_temperature=atemp,
                process_temperature=ptemp,
                rotational_speed=rpm,
                torque=trq,
                tool_wear=wear
            ))

        # 8. Generate Initial AI Production Schedule (Google OR-Tools)
        logger.info("Generating baseline production schedule with Google OR-Tools...")
        ProductionSchedulerService.generate_schedule(db, horizon_days=7)

        # 9. Maintenance Records
        logger.info("Seeding maintenance record for Lyophilizer M-202...")
        m202 = mach_objs["M-202"]
        existing_maint = db.query(MaintenanceRecord).filter(MaintenanceRecord.machine_id == m202.id).first()
        if not existing_maint:
            db.add(MaintenanceRecord(
                machine_id=m202.id,
                maintenance_type="PREVENTIVE",
                reason="Semiannual vacuum pump seal replacement and condenser calibration",
                priority="HIGH",
                scheduled_date=datetime.now(timezone.utc) + timedelta(days=1),
                status="IN_PROGRESS",
                notes="Grade A sterile barrier maintenance protocol active."
            ))
            db.commit()

        logger.info("Database successfully seeded with realistic, internally consistent pharmaceutical plant data!")
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
