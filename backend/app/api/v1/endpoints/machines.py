from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.machine import (
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    MachineDetailResponse,
    ProductionLineCreate,
    ProductionLineResponse
)
from app.services.machine import MachineService

router = APIRouter()

# Role permissions: Operators and up can view machines. Maintenance & Production managers & Admin can edit.
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER"])

@router.get("/lines", response_model=List[ProductionLineResponse], summary="List all production lines")
def get_lines(
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return MachineService.get_lines(db)

@router.post("/lines", response_model=ProductionLineResponse, status_code=status.HTTP_201_CREATED, summary="Create a new production line")
def create_line(
    line_in: ProductionLineCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return MachineService.create_line(db, line_in)

@router.get("", response_model=List[MachineResponse], summary="List, filter and search machines")
def list_machines(
    status: Optional[str] = Query(None, description="Filter by status (RUNNING, IDLE, WARNING, CRITICAL, MAINTENANCE, OFFLINE)"),
    production_line: Optional[str] = Query(None, description="Filter by line code (e.g. LINE-1)"),
    machine_type: Optional[str] = Query(None, description="Filter by type (L, M, H)"),
    search: Optional[str] = Query(None, description="Search machine ID or name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return MachineService.get_machines(db, status, production_line, machine_type, search, skip, limit)

@router.post("", response_model=MachineResponse, status_code=status.HTTP_201_CREATED, summary="Register a new machine")
def create_machine(
    machine_in: MachineCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return MachineService.create_machine(db, machine_in)

@router.get("/{machine_id}", response_model=MachineResponse, summary="Get machine by machine_id or UUID")
def get_machine(
    machine_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return MachineService.get_machine_by_id(db, machine_id)

@router.patch("/{machine_id}", response_model=MachineResponse, summary="Update machine metadata or status")
def update_machine(
    machine_id: str,
    machine_in: MachineUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return MachineService.update_machine(db, machine_id, machine_in)

@router.delete("/{machine_id}", summary="Delete machine (Admin/Manager only)")
def delete_machine(
    machine_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return MachineService.delete_machine(db, machine_id)
