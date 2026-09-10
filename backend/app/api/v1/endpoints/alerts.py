from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.alert import AlertResponse, AlertCreate
from app.services.alert import AlertService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER"])

@router.get("", response_model=List[AlertResponse], summary="List and filter alerts")
def get_alerts(
    machine_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, HIGH, CRITICAL)"),
    alert_type: Optional[str] = Query(None, description="Filter by type (FAILURE_RISK, ANOMALY, etc.)"),
    is_resolved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return AlertService.get_alerts(db, machine_id, severity, alert_type, is_resolved, skip, limit)

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED, summary="Create manual alert")
def create_alert(
    alert_in: AlertCreate,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return AlertService.create_alert(db, alert_in)

@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse, summary="Acknowledge alert")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_or_above)
):
    alert = AlertService.acknowledge_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/{alert_id}/resolve", response_model=AlertResponse, summary="Resolve alert")
def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_or_above)
):
    alert = AlertService.resolve_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
