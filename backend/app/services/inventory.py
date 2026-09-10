from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.inventory import InventoryMaterial, InventoryTransaction
from app.models.alert import Alert
from app.schemas.inventory import InventoryMaterialCreate, InventoryMaterialUpdate, StockAdjustmentRequest
from app.schemas.alert import AlertCreate
from app.services.alert import AlertService
from app.utils.logger import logger

class InventoryService:
    @staticmethod
    def get_stock_status(material: InventoryMaterial) -> str:
        now = datetime.now(timezone.utc)
        if material.expiry_date:
            # Normalize timezone if necessary
            exp = material.expiry_date
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                return "EXPIRED"
            elif exp < now + timedelta(days=30):
                return "EXPIRING"

        if material.quantity <= 0:
            return "OUT_OF_STOCK"
        elif material.quantity <= material.reorder_level:
            return "LOW_STOCK"
        return "IN_STOCK"

    @staticmethod
    def create_material(db: Session, mat_in: InventoryMaterialCreate) -> InventoryMaterial:
        existing = db.query(InventoryMaterial).filter(
            InventoryMaterial.material_code == mat_in.material_code.upper()
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Material code already exists")

        mat = InventoryMaterial(
            material_code=mat_in.material_code.upper(),
            material_name=mat_in.material_name,
            category=mat_in.category.upper(),
            quantity=float(mat_in.quantity),
            unit=mat_in.unit,
            reorder_level=float(mat_in.reorder_level),
            supplier=mat_in.supplier,
            expiry_date=mat_in.expiry_date,
            batch_number=mat_in.batch_number,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(mat)
        db.commit()
        db.refresh(mat)

        # Record opening balance transaction
        tx = InventoryTransaction(
            material_id=mat.id,
            transaction_type="RECEIVE",
            quantity=mat.quantity,
            balance_after=mat.quantity,
            reference_type="INITIAL",
            notes="Opening balance record"
        )
        db.add(tx)
        db.commit()
        return mat

    @staticmethod
    def get_materials(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        low_stock_only: bool = False
    ) -> List[dict]:
        query = db.query(InventoryMaterial)
        if category:
            query = query.filter(InventoryMaterial.category == category.upper())
        if search:
            fmt = f"%{search}%"
            query = query.filter(
                (InventoryMaterial.material_code.ilike(fmt)) | (InventoryMaterial.material_name.ilike(fmt))
            )

        materials = query.order_by(InventoryMaterial.material_code).all()
        results = []
        for m in materials:
            status_str = InventoryService.get_stock_status(m)
            if low_stock_only and status_str not in ["LOW_STOCK", "OUT_OF_STOCK"]:
                continue
            item_dict = {
                "id": m.id,
                "material_code": m.material_code,
                "material_name": m.material_name,
                "category": m.category,
                "quantity": m.quantity,
                "unit": m.unit,
                "reorder_level": m.reorder_level,
                "supplier": m.supplier,
                "expiry_date": m.expiry_date,
                "batch_number": m.batch_number,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
                "stock_status": status_str
            }
            results.append(item_dict)
        return results

    @staticmethod
    def adjust_stock(db: Session, material_id: str, adj: StockAdjustmentRequest) -> dict:
        mat = db.query(InventoryMaterial).filter(
            (InventoryMaterial.id == material_id) | (InventoryMaterial.material_code == material_id)
        ).first()
        if not mat:
            raise HTTPException(status_code=404, detail="Material not found")

        old_qty = mat.quantity
        new_qty = old_qty + adj.quantity_delta
        if new_qty < 0:
            raise HTTPException(status_code=400, detail=f"Insufficient inventory. Available: {old_qty} {mat.unit}")

        mat.quantity = round(new_qty, 3)
        mat.updated_at = datetime.now(timezone.utc)

        tx = InventoryTransaction(
            material_id=mat.id,
            transaction_type=adj.transaction_type.upper(),
            quantity=adj.quantity_delta,
            balance_after=mat.quantity,
            reference_type=adj.reference_type,
            reference_id=adj.reference_id,
            notes=adj.notes,
            created_at=datetime.now(timezone.utc)
        )
        db.add(tx)
        db.commit()

        # Low stock alert check
        if mat.quantity <= mat.reorder_level:
            AlertService.create_alert(db, AlertCreate(
                alert_type="INVENTORY_SHORTAGE",
                severity="HIGH" if mat.quantity == 0 else "WARNING",
                title=f"Low Stock Alert: {mat.material_code}",
                message=f"Current stock for {mat.material_name} ({mat.material_code}) is {mat.quantity} {mat.unit}, below reorder threshold of {mat.reorder_level} {mat.unit}."
            ))

        return {
            "material_id": mat.id,
            "material_code": mat.material_code,
            "previous_quantity": old_qty,
            "new_quantity": mat.quantity,
            "unit": mat.unit,
            "stock_status": InventoryService.get_stock_status(mat)
        }

    @staticmethod
    def verify_materials_for_batches(db: Session, product_required_materials: dict, batch_count: int) -> Tuple[bool, List[str]]:
        """
        Verifies if all required ingredients are in stock for the requested batch count.
        """
        is_sufficient = True
        shortages = []

        for mat_code, qty_per_batch in (product_required_materials or {}).items():
            total_required = qty_per_batch * batch_count
            mat = db.query(InventoryMaterial).filter(InventoryMaterial.material_code == mat_code).first()
            if not mat:
                is_sufficient = False
                shortages.append(f"Material {mat_code} is not registered in inventory (Required: {total_required}).")
            elif mat.quantity < total_required:
                is_sufficient = False
                shortages.append(f"Material {mat.material_name} ({mat_code}) insufficient: Required {total_required} {mat.unit}, Available {mat.quantity} {mat.unit}.")

        return is_sufficient, shortages
