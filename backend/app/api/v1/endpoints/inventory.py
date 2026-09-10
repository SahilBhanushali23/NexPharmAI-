from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.inventory import (
    InventoryMaterialCreate,
    InventoryMaterialUpdate,
    InventoryMaterialResponse,
    StockAdjustmentRequest
)
from app.services.inventory import InventoryService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER"])

@router.get("", response_model=List[InventoryMaterialResponse], summary="List and filter inventory materials")
def list_materials(
    category: Optional[str] = Query(None, description="API, EXCIPIENT, PACKAGING, SOLVENT"),
    search: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return InventoryService.get_materials(db, category, search, low_stock_only)

@router.post("", response_model=InventoryMaterialResponse, status_code=status.HTTP_201_CREATED, summary="Register a new inventory raw material")
def create_material(
    mat_in: InventoryMaterialCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    mat = InventoryService.create_material(db, mat_in)
    return {
        "id": mat.id,
        "material_code": mat.material_code,
        "material_name": mat.material_name,
        "category": mat.category,
        "quantity": mat.quantity,
        "unit": mat.unit,
        "reorder_level": mat.reorder_level,
        "supplier": mat.supplier,
        "expiry_date": mat.expiry_date,
        "batch_number": mat.batch_number,
        "created_at": mat.created_at,
        "updated_at": mat.updated_at,
        "stock_status": InventoryService.get_stock_status(mat)
    }

@router.post("/{material_id}/adjust", summary="Record inventory adjustment (receive, consume, adjust)")
def adjust_inventory_stock(
    material_id: str,
    adj: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return InventoryService.adjust_stock(db, material_id, adj)
