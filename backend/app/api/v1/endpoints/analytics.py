from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.services.analytics import AnalyticsService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])

@router.get("/dashboard", summary="Real-time plant dashboard KPI summary and metrics")
def get_dashboard_kpis(
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return AnalyticsService.get_dashboard_summary(db)

@router.get("/oee/machines/{machine_id}", summary="Get machine-specific OEE breakdown")
def get_machine_oee(
    machine_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return AnalyticsService.get_machine_oee(db, machine_id)
