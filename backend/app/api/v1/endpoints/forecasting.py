from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.forecasting import ForecastGenerateRequest, DemandForecastResponse
from app.services.forecasting import DemandForecastingService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
manager_or_admin = RoleChecker(["ADMIN", "PRODUCTION_MANAGER"])

@router.post("/generate", response_model=DemandForecastResponse, summary="Generate demand forecast for production and inventory planning")
def generate_forecast(
    req: ForecastGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin)
):
    return DemandForecastingService.generate_forecast(db, req)
