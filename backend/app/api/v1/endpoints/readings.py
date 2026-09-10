from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.models.machine import MachineReading, Machine
from app.schemas.reading import MachineReadingCreate, MachineReadingResponse
from app.services.reading import ReadingPipelineService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])

@router.post("/ingest", status_code=status.HTTP_201_CREATED, summary="Ingest real-time machine telemetry reading")
def ingest_reading(
    reading_in: MachineReadingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    """
    Ingests machine sensor reading, triggers Predictive Maintenance ML, Anomaly Isolation Forest,
    calculates Health Score, updates Machine status, and fires alerts.
    """
    return ReadingPipelineService.ingest_reading(db, reading_in)

@router.get("/{machine_id}", response_model=List[MachineReadingResponse], summary="Get historical readings for a machine")
def get_machine_readings(
    machine_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    machine = db.query(Machine).filter(
        (Machine.id == machine_id) | (Machine.machine_id == machine_id)
    ).first()
    if not machine:
        return []
    return db.query(MachineReading).filter(
        MachineReading.machine_id == machine.id
    ).order_by(MachineReading.timestamp.desc()).limit(limit).all()
