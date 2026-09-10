from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.user import User
from app.schemas.quality import QualityPredictInput, QualityPredictResponse
from app.services.quality import BatchQualityService

router = APIRouter()
operator_or_above = RoleChecker(["ADMIN", "PRODUCTION_MANAGER", "MAINTENANCE_MANAGER", "QUALITY_MANAGER", "OPERATOR"])
quality_manager = RoleChecker(["ADMIN", "QUALITY_MANAGER", "PRODUCTION_MANAGER"])

@router.post("/predict", response_model=QualityPredictResponse, status_code=status.HTTP_201_CREATED, summary="Predict batch release quality and critical attributes")
def predict_quality(
    input_data: QualityPredictInput,
    db: Session = Depends(get_db),
    _: User = Depends(quality_manager)
):
    return BatchQualityService.predict_batch_quality(db, input_data)

@router.get("/history", response_model=List[QualityPredictResponse], summary="Retrieve quality predictions history")
def get_quality_history(
    batch_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(operator_or_above)
):
    return BatchQualityService.get_quality_predictions(db, batch_id)
