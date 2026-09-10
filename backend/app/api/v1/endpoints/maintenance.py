from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse
from app.services.maintenance import MaintenanceService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "MAINTENANCE_MANAGER", "PRODUCTION_MANAGER"])

@router.get("", response_model=List[MaintenanceResponse], summary="List and filter maintenance records")
def list_maintenance(
    machine_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)"),
    maintenance_type: Optional[str] = Query(None, description="Filter by type (PREVENTIVE, PREDICTIVE, CORRECTIVE, EMERGENCY)"),
    priority: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return MaintenanceService.get_records(db, machine_id, status, maintenance_type, priority, skip, limit)

@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED, summary="Create maintenance work order")
def create_maintenance(
    record_in: MaintenanceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return MaintenanceService.create_record(db, record_in)

@router.patch("/{record_id}", response_model=MaintenanceResponse, summary="Update maintenance record or complete work order")
def update_maintenance(
    record_id: str,
    record_in: MaintenanceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return MaintenanceService.update_record(db, record_id, record_in)
