from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.production import ProductionOrder, ProductionBatch
from app.models.product import Product
from app.schemas.production import (
    ProductionOrderCreate,
    ProductionOrderResponse,
    ProductionBatchResponse
)
from app.services.inventory import InventoryService
from app.schemas.inventory import StockAdjustmentRequest

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER"])

@router.get("/orders", response_model=List[ProductionOrderResponse], summary="List and filter production orders")
def list_orders(
    status: Optional[str] = Query(None, description="PLANNED, SCHEDULED, RUNNING, COMPLETED, ON_HOLD, CANCELLED"),
    priority: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    query = db.query(ProductionOrder)
    if status:
        query = query.filter(ProductionOrder.status == status.upper())
    if priority:
        query = query.filter(ProductionOrder.priority == priority.upper())
    return query.order_by(ProductionOrder.due_date.asc()).offset(skip).limit(limit).all()

@router.post("/orders", response_model=ProductionOrderResponse, status_code=status.HTTP_201_CREATED, summary="Create a new production order")
def create_order(
    order_in: ProductionOrderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    product = db.query(Product).filter(Product.id == order_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(ProductionOrder).filter(ProductionOrder.order_code == order_in.order_code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Order code already exists")

    order = ProductionOrder(
        order_code=order_in.order_code.upper(),
        product_id=product.id,
        quantity=order_in.quantity,
        priority=order_in.priority.upper(),
        due_date=order_in.due_date,
        status="PLANNED",
        notes=order_in.notes,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/batches", response_model=List[ProductionBatchResponse], summary="List all manufacturing batches")
def list_batches(
    order_id: Optional[str] = Query(None),
    machine_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    query = db.query(ProductionBatch)
    if order_id:
        query = query.filter(ProductionBatch.order_id == order_id)
    if machine_id:
        query = query.filter(ProductionBatch.machine_id == machine_id)
    if status:
        query = query.filter(ProductionBatch.status == status.upper())
    return query.order_by(ProductionBatch.created_at.desc()).offset(skip).limit(limit).all()

@router.patch("/batches/{batch_id}/status", response_model=ProductionBatchResponse, summary="Progress batch lifecycle (IN_PROGRESS, COMPLETED)")
def update_batch_status(
    batch_id: str,
    status_str: str = Query(..., description="PLANNED, IN_PROGRESS, COMPLETED, QUARANTINED, REJECTED"),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    old_status = batch.status
    batch.status = status_str.upper()

    now = datetime.now(timezone.utc)
    if batch.status == "IN_PROGRESS" and not batch.start_time:
        batch.start_time = now
        # Consume raw materials from inventory!
        product = db.query(Product).filter(Product.id == batch.product_id).first()
        if product and product.required_materials:
            for mat_code, req_qty in product.required_materials.items():
                try:
                    InventoryService.adjust_stock(db, mat_code, StockAdjustmentRequest(
                        quantity_delta=-float(req_qty),
                        transaction_type="CONSUME",
                        reference_type="BATCH",
                        reference_id=batch.batch_number,
                        notes=f"Raw material consumption for Batch {batch.batch_number}"
                    ))
                except Exception as e:
                    pass

    elif batch.status == "COMPLETED" and not batch.end_time:
        batch.end_time = now

    batch.updated_at = now
    db.commit()
    db.refresh(batch)
    return batch
